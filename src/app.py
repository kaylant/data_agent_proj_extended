"""Streamlit GUI for the Data Analysis Agent"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import time
import uuid

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="Data Analysis Agent",
    page_icon="📊",
    layout="wide",
)


@st.cache_resource(show_spinner=False)
def load_agent():
    """Load agent and data once, cached across sessions"""
    from src.agent import build_graph, df
    from src.data_loader import get_schema_summary

    app = build_graph()
    schema = get_schema_summary(df)
    return app, df, schema


# Load cached resources
app, df, schema_summary = load_agent()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())


def clear_conversation():
    """Clear conversation history"""
    st.session_state.messages = []
    st.session_state.thread_id = str(uuid.uuid4())


# Sidebar
with st.sidebar:
    st.title("📊 Data Analysis Agent")
    st.markdown("---")

    # Dataset info
    st.subheader("Dataset Info")
    st.metric("Rows", f"{len(df):,}")
    st.metric("Columns", len(df.columns))

    # Schema expander
    with st.expander("View Schema"):
        st.code(schema_summary, language=None)

    st.markdown("---")

    # Clear conversation button
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        clear_conversation()
        st.rerun()

    st.markdown("---")

    # Example queries
    st.subheader("Example Queries")
    example_queries = [
        "How many unique pipelines are there?",
        "Find correlations between capacity columns",
        "Are there outliers in total_scheduled_quantity?",
        "Run a data quality report",
        "Find segments of pipelines by total_scheduled_quantity",
        "Run robustness checks on top pipelines",
    ]

    for query in example_queries:
        if st.button(query, key=query, use_container_width=True):
            st.session_state.pending_query = query
            st.rerun()

# Main chat area
st.title("💬 Chat")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "time" in message:
            st.caption(f"⏱️ {message['time']:.2f}s")

# Handle pending query from sidebar
if "pending_query" in st.session_state:
    query = st.session_state.pending_query
    del st.session_state.pending_query

    # Add user message
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            start_time = time.time()
            result = app.invoke(
                {"messages": [("user", query)]},
                config={"configurable": {"thread_id": st.session_state.thread_id}},
            )
            elapsed = time.time() - start_time

        response = result["messages"][-1].content
        st.markdown(response)
        st.caption(f"⏱️ {elapsed:.2f}s")

    st.session_state.messages.append({"role": "assistant", "content": response, "time": elapsed})
    st.rerun()

# Chat input
if prompt := st.chat_input("Ask a question about the data..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            start_time = time.time()
            result = app.invoke(
                {"messages": [("user", prompt)]},
                config={"configurable": {"thread_id": st.session_state.thread_id}},
            )
            elapsed = time.time() - start_time

        response = result["messages"][-1].content
        st.markdown(response)
        st.caption(f"⏱️ {elapsed:.2f}s")

    st.session_state.messages.append({"role": "assistant", "content": response, "time": elapsed})
