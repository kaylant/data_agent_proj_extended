"""Time series analysis tools"""

import numpy as np
import pandas as pd
from langchain_core.tools import tool
from src.tools._shared import get_dataframe

# Map old frequency aliases to new ones (pandas 2.2+)
FREQ_MAP = {
    "M": "ME",  # Month end
    "Q": "QE",  # Quarter end
    "Y": "YE",  # Year end
    "A": "YE",  # Annual (year end)
    "H": "h",  # Hour
    "T": "min",  # Minute
    "S": "s",  # Second
    "L": "ms",  # Millisecond
    "U": "us",  # Microsecond
    "N": "ns",  # Nanosecond
}


@tool
def analyze_time_series(date_column: str, value_column: str, freq: str = "ME") -> str:
    """Analyze trends over time

    Args:
        date_column: Name of the date/datetime column
        value_column: Name of the numeric column to analyze
        freq: Resampling frequency - 'D' (day), 'W' (week), 'ME' (month), 'QE' (quarter), 'YE' (year)

    Returns:
        Trend analysis with statistics
    """
    df = get_dataframe()
    if df is None:
        return "Error: DataFrame not loaded"

    if date_column not in df.columns:
        return f"Error: Column '{date_column}' not found"
    if value_column not in df.columns:
        return f"Error: Column '{value_column}' not found"

    try:
        # Map old frequency aliases to new ones
        freq = FREQ_MAP.get(freq, freq)

        df_ts = df[[date_column, value_column]].copy()
        df_ts[date_column] = pd.to_datetime(df_ts[date_column], errors="coerce")
        df_ts = df_ts.dropna().set_index(date_column)

        resampled = df_ts.resample(freq).agg(["mean", "sum", "count"])
        resampled.columns = ["mean", "sum", "count"]

        values = resampled["mean"].dropna()
        if len(values) > 1:
            x = np.arange(len(values))
            slope, _ = np.polyfit(x, values.values, 1)
            trend = "increasing" if slope > 0 else "decreasing"
            pct_change = (values.iloc[-1] - values.iloc[0]) / values.iloc[0] * 100
        else:
            trend = "insufficient data"
            pct_change = 0

        lines = [
            f"Time series analysis: {value_column} by {date_column}",
            f"  Frequency: {freq}",
            f"  Periods: {len(resampled)}",
            f"  Date range: {values.index[0]} to {values.index[-1]}",
            f"  Trend: {trend}",
            f"  Overall change: {pct_change:.2f}%",
            f"  Mean of means: {values.mean():.2f}",
            "",
            "First 5 periods:",
            resampled.head().to_string(),
            "",
            "Last 5 periods:",
            resampled.tail().to_string(),
        ]

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"
