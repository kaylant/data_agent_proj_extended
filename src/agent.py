"""LangGraph agent with analysis tools"""

import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from src.data_loader import load_dataset, get_schema_summary
from src.tools import set_dataframe, ALL_TOOLS

load_dotenv()

USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"

# Load data and configure tools
df = load_dataset()
set_dataframe(df)
SCHEMA_SUMMARY = get_schema_summary(df)

# Add database-specific instructions
if USE_DATABASE:
    DATABASE_INSTRUCTIONS = """
## IMPORTANT: Database Mode Active

You are connected to a PostgreSQL database with 16+ million rows. 
**Always prefer execute_sql_query over execute_pandas_code** for better performance.

The table is called `pipeline_data`. Example queries:
- Count: SELECT COUNT(*) FROM pipeline_data
- Unique values: SELECT COUNT(DISTINCT pipeline_name) FROM pipeline_data
- Aggregations: SELECT pipeline_name, SUM(total_scheduled_quantity) as total FROM pipeline_data GROUP BY pipeline_name ORDER BY total DESC LIMIT 10
- Filtering: SELECT * FROM pipeline_data WHERE region_nat_gas = 'Southeast' LIMIT 100

Only use execute_pandas_code when you need complex transformations that SQL cannot handle.
"""
else:
    DATABASE_INSTRUCTIONS = ""

SYSTEM_PROMPT = f"""You are an expert data analyst for natural gas pipeline data.

{SCHEMA_SUMMARY}

{DATABASE_INSTRUCTIONS}

## Guidelines

1. **Always show your work**: Include the methodology, columns used, and any filters applied.

2. **For deterministic queries** (counts, sums, specific values):
   - Use execute_sql_query for simple counts and aggregations (preferred in database mode)
   - Use execute_pandas_code for complex transformations
   - Show the exact numbers

3. **For pattern recognition**:
   - Use find_correlations, find_patterns, or analyze_time_series
   - Quantify the strength of patterns found
   - Note any caveats

4. **For anomaly detection**:
   - Use detect_outliers with appropriate method (iqr or zscore)
   - Report count and percentage of outliers
   - Distinguish true outliers from potential data quality issues

5. **For causal hypotheses**:
   - Present as hypotheses, NOT facts
   - Provide supporting evidence
   - Acknowledge confounders and limitations
   - Suggest what additional data would help

Be concise but thorough. Start with a direct answer, then show supporting evidence.
"""


def get_llm():
    """Get LLM with tools bound"""
    if os.getenv("ANTHROPIC_API_KEY"):
        llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    elif os.getenv("OPENAI_API_KEY"):
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
    else:
        raise ValueError("No API key found.")

    return llm.bind_tools(ALL_TOOLS)


def agent_node(state: MessagesState):
    """Call the LLM"""
    llm = get_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


def should_continue(state: MessagesState) -> str:
    """Check if we should continue to tools or end"""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


def build_graph():
    """Build the agent graph with memory"""
    graph = StateGraph(MessagesState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    # Add memory for conversation persistence
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({"messages": [("user", "How many unique pipelines are in the dataset?")]})
    print("\n" + result["messages"][-1].content)
