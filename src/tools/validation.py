"""Validate findings"""

import numpy as np
import pandas as pd
from langchain_core.tools import tool
from src.tools._shared import get_dataframe


@tool
def check_confounders(
    target_column: str, feature_column: str, potential_confounders: list[str]
) -> str:
    """Check if a relationship between two variables might be explained by confounders

    Args:
        target_column: The outcome/dependent variable
        feature_column: The predictor/independent variable
        potential_confounders: List of columns that might confound the relationship

    Returns:
        Analysis of how the relationship changes when controlling for confounders
    """
    df = get_dataframe()
    if df is None:
        return "Error: DataFrame not loaded"

    try:
        for col in [target_column, feature_column] + potential_confounders:
            if col not in df.columns:
                return f"Error: Column '{col}' not found"

        lines = [
            "## Confounder Analysis",
            "",
            f"**Relationship:** {feature_column} → {target_column}",
            f"**Potential confounders:** {', '.join(potential_confounders)}",
            "",
        ]

        # Overall correlation
        if pd.api.types.is_numeric_dtype(df[feature_column]) and pd.api.types.is_numeric_dtype(
            df[target_column]
        ):
            overall_corr = df[[feature_column, target_column]].corr().iloc[0, 1]
            lines.append(f"### Overall Correlation: {overall_corr:.4f}")
            lines.append("")

        # Check each confounder
        lines.append("### Stratified Analysis")

        for confounder in potential_confounders:
            lines.append("")
            lines.append(f"#### Controlling for: {confounder}")

            if pd.api.types.is_numeric_dtype(df[confounder]):
                # Bin numeric confounders
                df_temp = df.copy()
                df_temp["_confounder_bin"] = pd.qcut(
                    df_temp[confounder], q=4, labels=["Q1", "Q2", "Q3", "Q4"], duplicates="drop"
                )
                strat_col = "_confounder_bin"
            else:
                strat_col = confounder
                df_temp = df.copy()

            correlations = []
            for group in df_temp[strat_col].dropna().unique():
                subset = df_temp[df_temp[strat_col] == group]
                if len(subset) > 30:  # Minimum sample size
                    if pd.api.types.is_numeric_dtype(
                        df[feature_column]
                    ) and pd.api.types.is_numeric_dtype(df[target_column]):
                        corr = subset[[feature_column, target_column]].corr().iloc[0, 1]
                        if not np.isnan(corr):
                            correlations.append((group, corr, len(subset)))
                            lines.append(f"  - {group}: r = {corr:.4f} (n={len(subset):,})")

            if correlations:
                corr_values = [c[1] for c in correlations]
                corr_range = max(corr_values) - min(corr_values)

                if corr_range > 0.2:
                    lines.append(
                        f"  ⚠️ **Correlation varies by {confounder}** (range: {corr_range:.2f})"
                    )
                    lines.append(f"     This suggests {confounder} may confound the relationship")
                else:
                    lines.append(f"  ✓ Correlation stable across {confounder} levels")

        lines.extend(
            [
                "",
                "### Interpretation Guide",
                "- If correlations vary significantly across confounder levels, the relationship may be spurious",
                "- If correlations remain stable, the relationship is more robust",
                "- Consider collecting additional data to rule out other confounders",
            ]
        )

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"


@tool
def robustness_check(metric_column: str, group_column: str, test_type: str = "all") -> str:
    """Run robustness checks on a finding by testing different subsets and methods

    Args:
        metric_column: The metric being analyzed
        group_column: The grouping variable
        test_type: Type of robustness check - 'temporal', 'sample', 'outliers', or 'all'

    Returns:
        Robustness analysis showing if findings hold under different conditions
    """
    df = get_dataframe()
    if df is None:
        return "Error: DataFrame not loaded"

    try:
        if metric_column not in df.columns:
            return f"Error: Column '{metric_column}' not found"
        if group_column not in df.columns:
            return f"Error: Column '{group_column}' not found"

        lines = [
            "## Robustness Check",
            "",
            f"**Finding:** Top {group_column}s by {metric_column}",
            "",
        ]

        # Baseline result
        baseline = df.groupby(group_column)[metric_column].sum().sort_values(ascending=False)
        baseline_top5 = list(baseline.head(5).index)

        lines.append("### Baseline Top 5")
        for i, (name, val) in enumerate(baseline.head(5).items(), 1):
            lines.append(f"  {i}. {name}: {val:,.0f}")
        lines.append("")

        checks_passed = 0
        total_checks = 0

        # Temporal robustness
        if test_type in ["temporal", "all"] and "gas_day" in df.columns:
            lines.append("### Temporal Robustness")

            df_temp = df.copy()
            df_temp["gas_day"] = pd.to_datetime(df_temp["gas_day"], errors="coerce")

            # Split by time periods
            median_date = df_temp["gas_day"].median()

            early = df_temp[df_temp["gas_day"] <= median_date]
            late = df_temp[df_temp["gas_day"] > median_date]

            early_top5 = list(
                early.groupby(group_column)[metric_column]
                .sum()
                .sort_values(ascending=False)
                .head(5)
                .index
            )
            late_top5 = list(
                late.groupby(group_column)[metric_column]
                .sum()
                .sort_values(ascending=False)
                .head(5)
                .index
            )

            early_overlap = len(set(baseline_top5) & set(early_top5))
            late_overlap = len(set(baseline_top5) & set(late_top5))

            lines.append(
                f"  - Early period (before {median_date.date()}): {early_overlap}/5 match baseline"
            )
            lines.append(
                f"  - Late period (after {median_date.date()}): {late_overlap}/5 match baseline"
            )

            total_checks += 2
            if early_overlap >= 4:
                checks_passed += 1
            if late_overlap >= 4:
                checks_passed += 1

            if early_overlap >= 4 and late_overlap >= 4:
                lines.append("  ✓ **Temporally robust** - rankings consistent over time")
            else:
                lines.append("  ⚠️ Rankings shift over time - findings may be period-specific")
            lines.append("")

        # Sample robustness
        if test_type in ["sample", "all"]:
            lines.append("### Sample Robustness (Bootstrap)")

            n_samples = 5
            overlaps = []

            for i in range(n_samples):
                sample = df.sample(frac=0.5, random_state=i)
                sample_top5 = list(
                    sample.groupby(group_column)[metric_column]
                    .sum()
                    .sort_values(ascending=False)
                    .head(5)
                    .index
                )
                overlap = len(set(baseline_top5) & set(sample_top5))
                overlaps.append(overlap)

            avg_overlap = np.mean(overlaps)
            lines.append(f"  - Average overlap across {n_samples} 50% samples: {avg_overlap:.1f}/5")

            total_checks += 1
            if avg_overlap >= 4:
                checks_passed += 1
                lines.append("  ✓ **Sample robust** - findings stable across random samples")
            else:
                lines.append("  ⚠️ Findings sensitive to sample - may not generalize")
            lines.append("")

        # Outlier robustness
        if test_type in ["outliers", "all"]:
            lines.append("### Outlier Robustness")

            # Remove top/bottom 5% of metric
            lower = df[metric_column].quantile(0.05)
            upper = df[metric_column].quantile(0.95)
            df_trimmed = df[(df[metric_column] >= lower) & (df[metric_column] <= upper)]

            trimmed_top5 = list(
                df_trimmed.groupby(group_column)[metric_column]
                .sum()
                .sort_values(ascending=False)
                .head(5)
                .index
            )
            overlap = len(set(baseline_top5) & set(trimmed_top5))

            lines.append(
                f"  - After removing outliers (5th-95th percentile): {overlap}/5 match baseline"
            )

            total_checks += 1
            if overlap >= 4:
                checks_passed += 1
                lines.append("  ✓ **Outlier robust** - not driven by extreme values")
            else:
                lines.append("  ⚠️ Findings may be driven by outliers")
            lines.append("")

        # Summary
        lines.append("---")
        lines.append(f"### Summary: {checks_passed}/{total_checks} robustness checks passed")

        if checks_passed == total_checks:
            lines.append("✅ **Finding is robust** - holds under multiple conditions")
        elif checks_passed >= total_checks * 0.5:
            lines.append("⚡ **Finding is moderately robust** - some conditions affect results")
        else:
            lines.append("⚠️ **Finding is fragile** - sensitive to data conditions")

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"
