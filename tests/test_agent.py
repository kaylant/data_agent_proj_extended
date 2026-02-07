"""Integration tests for the agent"""

import pytest
from src.agent import build_graph


@pytest.fixture
def app():
    """Build the agent graph"""
    return build_graph()


@pytest.mark.integration
def test_agent_responds_to_simple_question(app):
    """Test that the agent can answer a basic question"""
    result = app.invoke(
        {"messages": [("user", "How many columns are in the dataset?")]},
        config={"configurable": {"thread_id": "test-1"}},
    )

    # Should have at least one response message
    assert len(result["messages"]) >= 1

    # Last message should have content
    last_message = result["messages"][-1]
    assert last_message.content


@pytest.mark.integration
def test_agent_uses_tools(app):
    """Test that the agent uses tools for data questions"""
    result = app.invoke(
        {"messages": [("user", "How many unique pipelines are there?")]},
        config={"configurable": {"thread_id": "test-2"}},
    )

    # Should mention a number in the response
    last_message = result["messages"][-1]
    assert any(char.isdigit() for char in last_message.content)
