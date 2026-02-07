"""Statistical analysis tools"""

import numpy as np
import pandas as pd
from langchain_core.tools import tool
from src.tools._shared import get_dataframe


@tool
def get_column_stats(column: str) -> str:
    """Get detailed statistics for a specific column.

    Args:
        column: Name of the column to analyze.

    Returns:
        Detailed statistics including nulls, unique values, and distribution.
    """
    df = get_dataframe()
    if df is None:
        return "Error: DataFrame not loaded"

    if column not in df.columns:
        return f"Error: Column '{column}' not found"

    try:
        col = df[column]
        lines = [
            f"Statistics for '{column}':",
            f"  Type: {col.dtype}",
            f"  Total: {len(col):,}",
            f"  Null: {col.isna().sum():,} ({col.isna().mean() * 100:.2f}%)",
            f"  Unique: {col.nunique():,}",
        ]

        if pd.api.types.is_numeric_dtype(col):
            lines.extend(
                [
                    f"  Min: {col.min():.4f}",
                    f"  Max: {col.max():.4f}",
                    f"  Mean: {col.mean():.4f}",
                    f"  Median: {col.median():.4f}",
                    f"  Std: {col.std():.4f}",
                ]
            )
        elif pd.api.types.is_datetime64_any_dtype(col):
            lines.extend(
                [
                    f"  Min: {col.min()}",
                    f"  Max: {col.max()}",
                ]
            )
        else:
            top_values = col.value_counts().head(10)
            lines.append("  Top 10 values:")
            for val, count in top_values.items():
                lines.append(f"    {val}: {count:,}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@tool
def find_correlations(columns: list[str] = None, method: str = "pearson") -> str:
    """Find correlations between numeric columns.

    Args:
        columns: List of column names to correlate. If None, uses all numeric columns.
        method: Correlation method - 'pearson', 'spearman', or 'kendall'.

    Returns:
        Top correlations sorted by absolute value.
    """
    df = get_dataframe()
    if df is None:
        return "Error: DataFrame not loaded"

    try:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        if columns:
            columns = [c for c in columns if c in numeric_cols]
        else:
            columns = numeric_cols

        if len(columns) < 2:
            return "Error: Need at least 2 numeric columns"

        corr_matrix = df[columns].corr(method=method)

        correlations = []
        for i, col1 in enumerate(columns):
            for j, col2 in enumerate(columns):
                if i < j:
                    val = corr_matrix.loc[col1, col2]
                    if not np.isnan(val):
                        correlations.append((col1, col2, val))

        correlations.sort(key=lambda x: abs(x[2]), reverse=True)

        lines = [f"Top correlations ({method}):"]
        for col1, col2, val in correlations[:15]:
            lines.append(f"  {col1} <-> {col2}: {val:.4f}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"
