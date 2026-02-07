"""Pattern finding tools"""

from langchain_core.tools import tool
from src.tools._shared import get_dataframe


@tool
def find_patterns(
    group_by: list[str], agg_column: str, agg_func: str = "mean", top_n: int = 20
) -> str:
    """Find patterns by grouping and aggregating data.

    Args:
        group_by: Columns to group by.
        agg_column: Column to aggregate.
        agg_func: Aggregation function - 'mean', 'sum', 'count', 'min', 'max', 'std'.
        top_n: Number of top results to return.

    Returns:
        Top groups sorted by aggregated value.
    """
    df = get_dataframe()
    if df is None:
        return "Error: DataFrame not loaded"

    try:
        for col in group_by:
            if col not in df.columns:
                return f"Error: Column '{col}' not found"
        if agg_column not in df.columns:
            return f"Error: Column '{agg_column}' not found"

        result = df.groupby(group_by, dropna=False)[agg_column].agg(agg_func)
        result = result.sort_values(ascending=False).head(top_n)

        lines = [
            f"Pattern: {agg_func}({agg_column}) by {', '.join(group_by)}",
            f"Top {len(result)} results:",
            "",
            result.to_string(),
        ]

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"
