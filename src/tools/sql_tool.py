"""SQL query tool for database mode"""

import os
from langchain_core.tools import tool

USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"


@tool
def execute_sql_query(query: str) -> str:
    """Execute a SQL query against the pipeline_data table (database mode only)

    Args:
        query: SQL SELECT query to execute. Table name is 'pipeline_data'.
               Example: SELECT COUNT(*) FROM pipeline_data
               Example: SELECT pipeline_name, SUM(total_scheduled_quantity) FROM pipeline_data GROUP BY pipeline_name

    Returns:
        Query results as formatted string
    """
    if not USE_DATABASE:
        return (
            "Error: SQL queries only available in database mode. Use execute_pandas_code instead."
        )

    # Security: only allow SELECT queries
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        return "Error: Only SELECT queries are allowed"

    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"]
    for word in forbidden:
        if word in query_upper:
            return f"Error: {word} operations are not allowed"

    try:
        from src.database import execute_query

        df = execute_query(query)

        if len(df) == 0:
            return "Query returned no results"

        if len(df) > 50:
            result = df.head(50).to_string()
            return f"{result}\n\n... (showing 50 of {len(df)} rows)"

        return df.to_string()

    except Exception as e:
        return f"Error executing query: {e}"
