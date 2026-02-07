"""General pandas code execution tool"""

import numpy as np
import pandas as pd
from langchain_core.tools import tool
from src.tools._shared import get_dataframe


@tool
def execute_pandas_code(code: str) -> str:
    """Execute pandas code against the dataset.

    The dataframe is available as 'df'. Always assign your final result to 'result'.

    Examples:
        - result = df['pipeline_name'].nunique()
        - result = df.groupby('region_nat_gas')['total_scheduled_quantity'].sum()
        - result = df[df['location_state_ab'] == 'TX'].shape[0]

    Args:
        code: Python code to execute. Must assign output to 'result'.

    Returns:
        The result as a string, or an error message.
    """
    df = get_dataframe()
    if df is None:
        return "Error: DataFrame not loaded"

    try:
        namespace = {"df": df, "pd": pd, "np": np}
        exec(code, namespace)
        result = namespace.get("result", "No 'result' variable assigned")

        if isinstance(result, pd.DataFrame):
            if len(result) > 20:
                return f"DataFrame ({len(result)} rows):\n{result.head(20).to_string()}\n..."
            return result.to_string()
        elif isinstance(result, pd.Series):
            if len(result) > 20:
                return f"Series ({len(result)} items):\n{result.head(20).to_string()}\n..."
            return result.to_string()
        else:
            return str(result)
    except Exception as e:
        return f"Error: {e}"
