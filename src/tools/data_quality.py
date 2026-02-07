"""Data quality tools for detecting issues that affect conclusions"""

import numpy as np
import pandas as pd
from langchain_core.tools import tool
from src.tools._shared import get_dataframe


@tool
def data_quality_report(check_all: bool = True) -> str:
    """Comprehensive data quality report that identifies issues affecting analysis conclusions

    Args:
        check_all: Whether to run all checks (default: True)

    Returns:
        Detailed quality report with impact assessment
    """
    df = get_dataframe()
    if df is None:
        return "Error: DataFrame not loaded"

    try:
        issues = []
        warnings = []

        lines = [
            "## Data Quality Report",
            "",
            f"**Dataset:** {len(df):,} rows × {len(df.columns)} columns",
            "",
        ]

        # 1. Missing values analysis
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        high_missing = missing_pct[missing_pct > 5].sort_values(ascending=False)

        if len(high_missing) > 0:
            lines.append("### 1. Missing Data (>5%)")
            for col, pct in high_missing.items():
                lines.append(f"  - **{col}**: {pct:.1f}% missing ({missing[col]:,} rows)")
                if pct > 20:
                    issues.append(f"{col} has {pct:.1f}% missing - may bias results")
            lines.append("")

        # 2. Placeholder/sentinel values
        lines.append("### 2. Potential Placeholder Values")
        sentinel_values = [999999999, 999999, -999, -1, 0]
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        sentinel_found = False
        for col in numeric_cols:
            for sentinel in sentinel_values:
                count = (df[col] == sentinel).sum()
                if count > 100:  # Significant occurrence
                    pct = count / len(df) * 100
                    lines.append(
                        f"  - **{col}**: {count:,} rows ({pct:.2f}%) have value {sentinel}"
                    )
                    sentinel_found = True
                    if pct > 1:
                        warnings.append(
                            f"{col} contains {pct:.1f}% placeholder values ({sentinel})"
                        )

        if not sentinel_found:
            lines.append("  - No significant placeholder values detected")
        lines.append("")

        # 3. Logical inconsistencies
        lines.append("### 3. Logical Inconsistencies")
        inconsistencies = []

        # Check capacity relationships
        if all(c in df.columns for c in ["design_capacity", "operating_capacity"]):
            invalid = (df["operating_capacity"] > df["design_capacity"]) & (
                df["design_capacity"] > 0
            )
            count = invalid.sum()
            if count > 0:
                pct = count / len(df) * 100
                lines.append(f"  - **Operating > Design capacity**: {count:,} rows ({pct:.1f}%)")
                issues.append(
                    f"{pct:.1f}% of rows have operating capacity exceeding design capacity"
                )

        if all(c in df.columns for c in ["operating_capacity", "operationally_available_capacity"]):
            invalid = (df["operationally_available_capacity"] > df["operating_capacity"]) & (
                df["operating_capacity"] > 0
            )
            count = invalid.sum()
            if count > 0:
                pct = count / len(df) * 100
                lines.append(f"  - **Available > Operating capacity**: {count:,} rows ({pct:.1f}%)")

        # Check for negative values where they shouldn't exist
        for col in ["total_scheduled_quantity", "design_capacity", "operating_capacity"]:
            if col in df.columns:
                neg_count = (df[col] < 0).sum()
                if neg_count > 0:
                    pct = neg_count / len(df) * 100
                    lines.append(f"  - **Negative {col}**: {neg_count:,} rows ({pct:.2f}%)")
                    if pct > 0.1:
                        warnings.append(f"{col} has {neg_count:,} negative values")

        lines.append("")

        # 4. Coordinate validation
        if "location_latitude" in df.columns and "location_longitude" in df.columns:
            lines.append("### 4. Geographic Data Issues")

            lat = df["location_latitude"]
            lon = df["location_longitude"]

            invalid_lat = ((lat < -90) | (lat > 90)).sum()
            invalid_lon = ((lon < -180) | (lon > 180)).sum()

            # US-specific checks (most pipelines should be in continental US)
            outside_us_lat = ((lat < 24) | (lat > 50)).sum() - lat.isnull().sum()
            outside_us_lon = ((lon > -60) | (lon < -130)).sum() - lon.isnull().sum()

            if invalid_lat > 0:
                lines.append(f"  - **Invalid latitude** (outside -90 to 90): {invalid_lat:,} rows")
            if invalid_lon > 0:
                lines.append(
                    f"  - **Invalid longitude** (outside -180 to 180): {invalid_lon:,} rows"
                )
            if outside_us_lon > 1000:
                lines.append(
                    f"  - **Positive longitude values**: {outside_us_lon:,} rows (unusual for US data)"
                )
                warnings.append(
                    "Many positive longitude values - possible sign error or non-US data"
                )

            lines.append("")

        # 5. Temporal issues
        if "gas_day" in df.columns and "posting_dt" in df.columns:
            lines.append("### 5. Temporal Consistency")

            gas_day = pd.to_datetime(df["gas_day"], errors="coerce")
            posting = pd.to_datetime(df["posting_dt"], errors="coerce")

            future_posting = (posting > gas_day).sum()
            if future_posting > 0:
                pct = future_posting / len(df) * 100
                lines.append(f"  - **Posting after gas day**: {future_posting:,} rows ({pct:.1f}%)")

            lines.append("")

        # 6. Duplicate analysis
        lines.append("### 6. Duplicate Records")
        exact_dups = df.duplicated().sum()
        lines.append(f"  - **Exact duplicates**: {exact_dups:,} rows")

        key_cols = [c for c in ["smx_location_id", "gas_day", "cycle_desc"] if c in df.columns]
        if len(key_cols) >= 2:
            key_dups = df.duplicated(subset=key_cols).sum()
            if key_dups > 0:
                lines.append(f"  - **Key duplicates** ({', '.join(key_cols)}): {key_dups:,} rows")

        lines.append("")

        # Summary
        lines.append("---")
        lines.append("## Impact Assessment")
        lines.append("")

        if issues:
            lines.append("### ⚠️ High-Impact Issues (may change conclusions)")
            for issue in issues:
                lines.append(f"  - {issue}")
            lines.append("")

        if warnings:
            lines.append("### ⚡ Moderate Concerns")
            for warning in warnings:
                lines.append(f"  - {warning}")
            lines.append("")

        if not issues and not warnings:
            lines.append(
                "✅ No major data quality issues detected that would significantly impact analysis."
            )
        else:
            lines.append("### Recommendations")
            lines.append("  - Filter out rows with placeholder values before aggregations")
            lines.append(
                "  - Consider excluding records with logical inconsistencies for capacity analysis"
            )
            lines.append("  - Validate geographic data before spatial analysis")

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"


@tool
def compare_with_without_issues(
    metric_column: str, group_column: str = None, agg_func: str = "sum"
) -> str:
    """Compare analysis results with and without data quality issues to show impact

    Args:
        metric_column: The column to analyze
        group_column: Optional column to group by
        agg_func: Aggregation function (sum, mean, count)

    Returns:
        Comparison showing how data quality issues affect conclusions
    """
    df = get_dataframe()
    if df is None:
        return "Error: DataFrame not loaded"

    try:
        if metric_column not in df.columns:
            return f"Error: Column '{metric_column}' not found"

        lines = [
            "## Data Quality Impact Analysis",
            "",
            f"**Metric:** {metric_column}",
            f"**Aggregation:** {agg_func}",
            "",
        ]

        # Define clean data filters
        df_clean = df.copy()
        filters_applied = []

        # Remove nulls
        null_count = df_clean[metric_column].isnull().sum()
        if null_count > 0:
            df_clean = df_clean[df_clean[metric_column].notna()]
            filters_applied.append(f"Removed {null_count:,} null values")

        # Remove placeholder values
        for sentinel in [999999999, 999999]:
            sentinel_count = (df_clean[metric_column] == sentinel).sum()
            if sentinel_count > 0:
                df_clean = df_clean[df_clean[metric_column] != sentinel]
                filters_applied.append(
                    f"Removed {sentinel_count:,} placeholder values ({sentinel})"
                )

        # Remove negatives if unexpected
        neg_count = (df_clean[metric_column] < 0).sum()
        if neg_count > 0:
            df_clean = df_clean[df_clean[metric_column] >= 0]
            filters_applied.append(f"Removed {neg_count:,} negative values")

        lines.append("### Filters Applied")
        for f in filters_applied:
            lines.append(f"  - {f}")
        lines.append(
            f"  - **Rows removed:** {len(df) - len(df_clean):,} ({(len(df) - len(df_clean)) / len(df) * 100:.1f}%)"
        )
        lines.append("")

        # Compare results
        if group_column and group_column in df.columns:
            lines.append(f"### Comparison by {group_column}")

            raw_result = (
                df.groupby(group_column)[metric_column]
                .agg(agg_func)
                .sort_values(ascending=False)
                .head(10)
            )
            clean_result = (
                df_clean.groupby(group_column)[metric_column]
                .agg(agg_func)
                .sort_values(ascending=False)
                .head(10)
            )

            lines.append("")
            lines.append("**Top 10 - Raw Data:**")
            for name, val in raw_result.items():
                lines.append(f"  {name}: {val:,.2f}")

            lines.append("")
            lines.append("**Top 10 - Clean Data:**")
            for name, val in clean_result.items():
                lines.append(f"  {name}: {val:,.2f}")

            # Check if rankings changed
            raw_top5 = list(raw_result.head(5).index)
            clean_top5 = list(clean_result.head(5).index)

            if raw_top5 != clean_top5:
                lines.append("")
                lines.append("⚠️ **Rankings changed after cleaning!**")
                new_entries = set(clean_top5) - set(raw_top5)
                if new_entries:
                    lines.append(f"  New in top 5: {', '.join(str(x) for x in new_entries)}")
        else:
            lines.append("### Overall Comparison")

            raw_val = df[metric_column].agg(agg_func)
            clean_val = df_clean[metric_column].agg(agg_func)
            diff_pct = (clean_val - raw_val) / raw_val * 100 if raw_val != 0 else 0

            lines.append(f"  - Raw data {agg_func}: {raw_val:,.2f}")
            lines.append(f"  - Clean data {agg_func}: {clean_val:,.2f}")
            lines.append(f"  - Difference: {diff_pct:+.2f}%")

            if abs(diff_pct) > 5:
                lines.append("")
                lines.append(
                    f"⚠️ **Significant impact**: Cleaning data changes {agg_func} by {abs(diff_pct):.1f}%"
                )

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"
