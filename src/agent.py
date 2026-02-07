"""LangGraph agent with analysis tools"""

import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from src.data_loader import get_schema_summary, load_dataset
from src.tools import ALL_TOOLS, set_dataframe

load_dotenv()

# Load data and configure tools
df = load_dataset()
set_dataframe(df)
SCHEMA_SUMMARY = get_schema_summary(df)

SYSTEM_PROMPT = f"""You are an expert data analyst for natural gas pipeline data.

{SCHEMA_SUMMARY}

## Guidelines

1. **Always show your work**: Include the methodology, columns used, and any filters applied.

2. **For deterministic queries** (counts, sums, specific values):
   - Use execute_pandas_code for precise answers
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
