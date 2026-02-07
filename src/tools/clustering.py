"""Clustering tools for finding non-obvious segments"""

import pandas as pd
from langchain_core.tools import tool
from src.tools._shared import get_dataframe


@tool
def cluster_analysis(
    columns: list[str],
    n_clusters: int = 5,
    sample_size: int = 50000,
    include_interpretation: bool = True,
) -> str:
    """Find non-obvious segments/clusters in the data using K-means clustering

    Args:
        columns: Numeric columns to use for clustering
        n_clusters: Number of clusters to find (default: 5)
        sample_size: Number of rows to sample for performance (default: 50000)
        include_interpretation: Whether to include business interpretation hints

    Returns:
        Cluster profiles with statistics and interpretation
    """
    df = get_dataframe()
    if df is None:
        return "Error: DataFrame not loaded"

    try:
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler

        # Validate columns
        valid_cols = []
        for col in columns:
            if col not in df.columns:
                return f"Error: Column '{col}' not found"
            if not pd.api.types.is_numeric_dtype(df[col]):
                return f"Error: Column '{col}' is not numeric"
            valid_cols.append(col)

        # Prepare data - sample if large
        df_clean = df[valid_cols].dropna()
        if len(df_clean) > sample_size:
            df_sample = df_clean.sample(n=sample_size, random_state=42)
        else:
            df_sample = df_clean

        # Scale features
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(df_sample)

        # Cluster
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(scaled_data)
        df_sample = df_sample.copy()
        df_sample["cluster"] = clusters

        # Build cluster profiles
        lines = [
            "## Cluster Analysis Results",
            "",
            "**Configuration:**",
            f"- Features: {', '.join(valid_cols)}",
            f"- Clusters: {n_clusters}",
            f"- Sample size: {len(df_sample):,} rows",
            f"- Inertia (lower = tighter clusters): {kmeans.inertia_:,.2f}",
            "",
        ]

        # Profile each cluster
        for i in range(n_clusters):
            cluster_data = df_sample[df_sample["cluster"] == i]
            pct = len(cluster_data) / len(df_sample) * 100

            lines.append(f"### Cluster {i} ({len(cluster_data):,} rows, {pct:.1f}%)")

            # Stats for each feature
            for col in valid_cols:
                col_mean = cluster_data[col].mean()
                col_std = cluster_data[col].std()
                overall_mean = df_sample[col].mean()
                diff_pct = (
                    (col_mean - overall_mean) / overall_mean * 100 if overall_mean != 0 else 0
                )

                direction = "↑" if diff_pct > 10 else "↓" if diff_pct < -10 else "≈"
                lines.append(
                    f"  - {col}: {col_mean:,.2f} (σ={col_std:,.2f}) {direction} {diff_pct:+.1f}% vs avg"
                )

            lines.append("")

        if include_interpretation:
            lines.extend(
                [
                    "### Interpretation Guide",
                    "- ↑ indicates cluster is notably above average (>10%)",
                    "- ↓ indicates cluster is notably below average (<-10%)",
                    "- ≈ indicates cluster is near average",
                    "",
                    "**Business Questions to Explore:**",
                    "- Which clusters represent high-value segments?",
                    "- Are there clusters with unusual capacity utilization?",
                    "- Do clusters align with geographic or operational patterns?",
                ]
            )

        return "\n".join(lines)

    except ImportError:
        return "Error: scikit-learn required. Install with: pip install scikit-learn"
    except Exception as e:
        return f"Error: {e}"


@tool
def find_segments(
    group_column: str, metric_column: str, method: str = "quantile", n_segments: int = 4
) -> str:
    """Segment data into groups based on a metric and profile each segment

    Args:
        group_column: Column to analyze segments by (e.g., 'pipeline_name')
        metric_column: Numeric column to segment on (e.g., 'total_scheduled_quantity')
        method: 'quantile' (equal-sized groups) or 'kmeans' (natural breaks)
        n_segments: Number of segments (default: 4 for quartiles)

    Returns:
        Segment profiles with actionable insights
    """
    df = get_dataframe()
    if df is None:
        return "Error: DataFrame not loaded"

    try:
        if group_column not in df.columns:
            return f"Error: Column '{group_column}' not found"
        if metric_column not in df.columns:
            return f"Error: Column '{metric_column}' not found"

        # Aggregate by group
        grouped = df.groupby(group_column, dropna=False)[metric_column].agg(
            ["sum", "mean", "count"]
        )
        grouped = grouped.reset_index()

        # Create segments
        if method == "quantile":
            grouped["segment"] = pd.qcut(
                grouped["sum"], q=n_segments, labels=False, duplicates="drop"
            )
        else:
            from sklearn.cluster import KMeans

            scaler_vals = grouped[["sum"]].values
            kmeans = KMeans(n_clusters=n_segments, random_state=42, n_init=10)
            grouped["segment"] = kmeans.fit_predict(scaler_vals)
            # Reorder segments by mean value
            segment_means = grouped.groupby("segment")["sum"].mean().sort_values()
            segment_map = {old: new for new, old in enumerate(segment_means.index)}
            grouped["segment"] = grouped["segment"].map(segment_map)

        lines = [
            "## Segmentation Analysis",
            "",
            "**Configuration:**",
            f"- Grouped by: {group_column}",
            f"- Metric: {metric_column}",
            f"- Method: {method}",
            f"- Segments: {n_segments}",
            "",
        ]

        segment_names = ["Low", "Medium-Low", "Medium", "Medium-High", "High"][:n_segments]
        if n_segments == 4:
            segment_names = ["Bottom 25%", "Lower-Mid", "Upper-Mid", "Top 25%"]

        for seg in range(n_segments):
            seg_data = grouped[grouped["segment"] == seg]
            if len(seg_data) == 0:
                continue

            seg_name = segment_names[seg] if seg < len(segment_names) else f"Segment {seg}"
            total_sum = seg_data["sum"].sum()
            total_pct = total_sum / grouped["sum"].sum() * 100

            lines.append(f"### {seg_name} ({len(seg_data)} {group_column}s)")
            lines.append(f"- Total {metric_column}: {total_sum:,.0f} ({total_pct:.1f}% of total)")
            lines.append(f"- Avg per {group_column}: {seg_data['sum'].mean():,.0f}")

            # Top examples
            top_3 = seg_data.nlargest(3, "sum")
            lines.append(f"- Examples: {', '.join(top_3[group_column].astype(str).tolist())}")
            lines.append("")

        # Concentration insight
        top_segment = grouped[grouped["segment"] == n_segments - 1]
        top_pct = top_segment["sum"].sum() / grouped["sum"].sum() * 100
        top_count_pct = len(top_segment) / len(grouped) * 100

        lines.extend(
            [
                "### Key Insight",
                f"The top segment contains {top_count_pct:.1f}% of {group_column}s ",
                f"but accounts for {top_pct:.1f}% of total {metric_column}.",
            ]
        )

        if top_pct > 50 and top_count_pct < 25:
            lines.append("**High concentration detected**: A small group dominates the metric.")

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"
