"""Data loading and schema inference"""

from pathlib import Path

import pandas as pd


def load_dataset(path: str = "data/pipeline_dataset.parquet") -> pd.DataFrame:
    """Load the dataset."""
    filepath = Path(path)
    if not filepath.exists():
        raise FileNotFoundError(f"Dataset not found at {filepath}")

    df = pd.read_parquet(filepath)
    print(f"✓ Loaded {len(df):,} rows × {len(df.columns)} columns")
    return df


def get_schema_summary(df: pd.DataFrame) -> str:
    """Generate a concise schema summary for the LLM."""
    lines = [
        f"Dataset: {len(df):,} rows × {len(df.columns)} columns",
        "",
        "Columns:",
    ]

    for col in df.columns:
        dtype = df[col].dtype
        null_pct = df[col].isna().mean() * 100

        # Get type-specific info
        if pd.api.types.is_numeric_dtype(df[col]):
            info = f"range [{df[col].min():.2f}, {df[col].max():.2f}]"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            info = f"{df[col].min()} to {df[col].max()}"
        else:
            n_unique = df[col].nunique()
            info = f"{n_unique} unique values"

        lines.append(f"  - {col} ({dtype}): {info}, {null_pct:.1f}% null")

    return "\n".join(lines)


if __name__ == "__main__":
    # Quick test for data loading and schema summary
    df = load_dataset()
    print("\n" + get_schema_summary(df))
