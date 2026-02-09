"""Data loading utilities"""

import os
import pandas as pd
from pathlib import Path

USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"

# Cache for schema - we only need to query this once
_schema_cache = None
_row_count_cache = None


def load_dataset() -> pd.DataFrame:
    """Load the dataset from file or return a lazy database wrapper"""
    if USE_DATABASE:
        from src.database import get_dataframe_from_db, get_table_info

        # For database mode, we return a small sample for schema inference
        # The actual queries will hit the database directly
        print("Connecting to PostgreSQL...")
        info = get_table_info()
        print(f"✓ Connected to database with {info['row_count']:,} rows")

        # Return small sample for schema inference only
        df = get_dataframe_from_db(limit=1000)
        df._is_sample = True  # Mark as sample
        df._total_rows = info["row_count"]
        return df
    else:
        data_dir = Path("data")
        parquet_files = list(data_dir.glob("*.parquet"))

        if not parquet_files:
            raise FileNotFoundError(f"No parquet files found in {data_dir}")

        df = pd.read_parquet(parquet_files[0])
        print(f"✓ Loaded {len(df):,} rows × {len(df.columns)} columns from file")
        return df


def get_schema_summary(df: pd.DataFrame) -> str:
    """Generate a schema summary for the LLM"""
    global _schema_cache, _row_count_cache

    if _schema_cache is not None:
        return _schema_cache

    # Get actual row count
    if hasattr(df, "_total_rows"):
        row_count = df._total_rows
    else:
        row_count = len(df)

    lines = [f"Dataset: {row_count:,} rows × {len(df.columns)} columns", "", "Columns:"]

    for col in df.columns:
        dtype = df[col].dtype
        null_pct = df[col].isnull().mean() * 100

        if pd.api.types.is_numeric_dtype(df[col]):
            min_val = df[col].min()
            max_val = df[col].max()
            lines.append(
                f"  - {col} ({dtype}): range [{min_val:.2f}, {max_val:.2f}], {null_pct:.1f}% null"
            )
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            min_val = df[col].min()
            max_val = df[col].max()
            lines.append(f"  - {col} ({dtype}): {min_val} to {max_val}, {null_pct:.1f}% null")
        else:
            unique_count = df[col].nunique()
            lines.append(f"  - {col} ({dtype}): {unique_count} unique values, {null_pct:.1f}% null")

    _schema_cache = "\n".join(lines)
    return _schema_cache
