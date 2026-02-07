"""Outlier detection tools"""

import numpy as np
import pandas as pd
from langchain_core.tools import tool
from src.tools._shared import get_dataframe


@tool
def detect_outliers(column: str, method: str = "iqr") -> str:
    """Detect outliers in a numeric column.

    Args:
        column: Name of the numeric column to analyze.
        method: Detection method - 'iqr' (1.5*IQR rule) or 'zscore' (|z| > 3).

    Returns:
        Outlier statistics and sample of outlier values.
    """
    df = get_dataframe()
    if df is None:
        return "Error: DataFrame not loaded"

    if column not in df.columns:
        return f"Error: Column '{column}' not found"

    col = df[column]
    if not pd.api.types.is_numeric_dtype(col):
        return f"Error: Column '{column}' is not numeric"

    try:
        col_clean = col.dropna()

        if method == "iqr":
            Q1 = col_clean.quantile(0.25)
            Q3 = col_clean.quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            outliers = col[(col < lower) | (col > upper)]
        else:  # zscore
            mean = col_clean.mean()
            std = col_clean.std()
            z_scores = np.abs((col - mean) / std)
            outliers = col[z_scores > 3]
            lower = mean - 3 * std
            upper = mean + 3 * std

        pct = len(outliers) / len(col) * 100

        lines = [
            f"Outlier detection for '{column}' using {method.upper()}:",
            f"  Total values: {len(col):,}",
            f"  Outliers found: {len(outliers):,} ({pct:.2f}%)",
            f"  Bounds: [{lower:.2f}, {upper:.2f}]",
            f"  Column range: [{col.min():.2f}, {col.max():.2f}]",
        ]

        if len(outliers) > 0:
            lines.append(f"  Sample outlier values: {outliers.head(10).tolist()}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"
