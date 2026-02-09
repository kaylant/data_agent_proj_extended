"""Tools for data analysis agent"""

import os
import pandas as pd

USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"

# Shared dataframe reference (for file mode)
_df: pd.DataFrame = None


def set_dataframe(df: pd.DataFrame):
    """Set the dataframe for all tools to use"""
    global _df
    _df = df


# Import tools AFTER _df is defined
from src.tools.pandas_tool import execute_pandas_code
from src.tools.stats import get_column_stats, find_correlations
from src.tools.outliers import detect_outliers
from src.tools.time_series import analyze_time_series
from src.tools.patterns import find_patterns
from src.tools.clustering import cluster_analysis, find_segments
from src.tools.data_quality import data_quality_report, compare_with_without_issues
from src.tools.validation import check_confounders, robustness_check
from src.tools.sql_tool import execute_sql_query

ALL_TOOLS = [
    execute_pandas_code,
    execute_sql_query,  # Add SQL tool
    find_correlations,
    detect_outliers,
    analyze_time_series,
    get_column_stats,
    find_patterns,
    cluster_analysis,
    find_segments,
    data_quality_report,
    compare_with_without_issues,
    check_confounders,
    robustness_check,
]
