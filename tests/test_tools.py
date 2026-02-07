"""Tests for analysis tools"""

import pytest
from src.tools import set_dataframe
from src.tools.clustering import cluster_analysis, find_segments
from src.tools.data_quality import compare_with_without_issues, data_quality_report
from src.tools.outliers import detect_outliers
from src.tools.pandas_tool import execute_pandas_code
from src.tools.patterns import find_patterns
from src.tools.stats import find_correlations, get_column_stats
from src.tools.time_series import analyze_time_series
from src.tools.validation import check_confounders, robustness_check

# --- Fixtures ---


@pytest.fixture
def use_sample_df(sample_df):
    """Set the shared dataframe to the small sample (5 rows, 3 pipelines)."""
    set_dataframe(sample_df)
    yield


@pytest.fixture
def use_sample_df_with_issues(sample_df_with_issues):
    """Set the shared dataframe to the sample with quality issues (100 rows)."""
    set_dataframe(sample_df_with_issues)
    yield


# --- execute_pandas_code ---


@pytest.mark.usefixtures("use_sample_df")
class TestExecutePandasCode:
    def test_simple_count(self):
        result = execute_pandas_code.invoke({"code": "result = len(df)"})
        assert "5" in result

    def test_unique_count(self):
        result = execute_pandas_code.invoke({"code": "result = df['pipeline_name'].nunique()"})
        assert "3" in result

    def test_invalid_code_returns_error(self):
        result = execute_pandas_code.invoke({"code": "result = invalid_variable"})
        assert "Error" in result


# --- stats (get_column_stats, find_correlations) ---


@pytest.mark.usefixtures("use_sample_df")
class TestGetColumnStats:
    def test_numeric_column(self):
        result = get_column_stats.invoke({"column": "total_scheduled_quantity"})
        assert "total_scheduled_quantity" in result
        assert "Mean" in result
        assert "Null" in result

    def test_string_column(self):
        result = get_column_stats.invoke({"column": "pipeline_name"})
        assert "pipeline_name" in result
        assert "Unique" in result

    def test_invalid_column(self):
        result = get_column_stats.invoke({"column": "nonexistent"})
        assert "Error" in result


@pytest.mark.usefixtures("use_sample_df")
class TestFindCorrelations:
    def test_finds_correlations(self):
        result = find_correlations.invoke({"columns": ["design_capacity", "operating_capacity"]})
        assert "correlation" in result.lower()

    def test_default_all_numeric(self):
        result = find_correlations.invoke({})
        assert "correlation" in result.lower()


# --- outliers ---


@pytest.mark.usefixtures("use_sample_df")
class TestDetectOutliers:
    def test_iqr_method(self):
        result = detect_outliers.invoke({"column": "total_scheduled_quantity", "method": "iqr"})
        assert "Outlier" in result
        assert "IQR" in result

    def test_zscore_method(self):
        result = detect_outliers.invoke({"column": "total_scheduled_quantity", "method": "zscore"})
        assert "Outlier" in result
        assert "ZSCORE" in result

    def test_invalid_column(self):
        result = detect_outliers.invoke({"column": "nonexistent"})
        assert "Error" in result


# --- patterns ---


@pytest.mark.usefixtures("use_sample_df")
class TestFindPatterns:
    def test_group_by_single_column(self):
        result = find_patterns.invoke(
            {
                "group_by": ["pipeline_name"],
                "agg_column": "total_scheduled_quantity",
                "agg_func": "sum",
            }
        )
        assert "Pipeline" in result

    def test_group_by_multiple_columns(self):
        result = find_patterns.invoke(
            {
                "group_by": ["pipeline_name", "location_state_ab"],
                "agg_column": "total_scheduled_quantity",
                "agg_func": "mean",
            }
        )
        assert "Pattern" in result


# --- clustering ---


@pytest.mark.usefixtures("use_sample_df_with_issues")
class TestClusterAnalysis:
    def test_cluster_analysis_runs(self):
        result = cluster_analysis.invoke(
            {"columns": ["total_scheduled_quantity", "design_capacity"], "n_clusters": 3}
        )
        assert "Cluster" in result
        assert "Error" not in result

    def test_cluster_analysis_invalid_column(self):
        result = cluster_analysis.invoke({"columns": ["nonexistent_column"], "n_clusters": 3})
        assert "Error" in result


@pytest.mark.usefixtures("use_sample_df_with_issues")
class TestFindSegments:
    def test_find_segments_runs(self):
        result = find_segments.invoke(
            {
                "group_column": "pipeline_name",
                "metric_column": "total_scheduled_quantity",
            }
        )
        assert "Segment" in result
        assert "Error" not in result

    def test_find_segments_invalid_column(self):
        result = find_segments.invoke(
            {
                "group_column": "nonexistent",
                "metric_column": "total_scheduled_quantity",
            }
        )
        assert "Error" in result


# --- data_quality ---


@pytest.mark.usefixtures("use_sample_df_with_issues")
class TestDataQualityReport:
    def test_data_quality_report_runs(self):
        result = data_quality_report.invoke({"check_all": True})
        assert "Data Quality" in result
        assert "Error" not in result

    def test_detects_placeholder_values(self):
        result = data_quality_report.invoke({"check_all": True})
        assert "999999999" in result or "Placeholder" in result or "placeholder" in result


@pytest.mark.usefixtures("use_sample_df_with_issues")
class TestCompareWithWithoutIssues:
    def test_compare_runs(self):
        result = compare_with_without_issues.invoke(
            {
                "metric_column": "total_scheduled_quantity",
                "group_column": "pipeline_name",
            }
        )
        assert "Clean" in result or "clean" in result
        assert "Error" not in result


# --- time series ---


class TestAnalyzeTimeSeries:
    def test_analyze_time_series_runs(self):
        result = analyze_time_series.invoke(
            {"date_column": "gas_day", "value_column": "total_scheduled_quantity"}
        )
        assert "Time series" in result or "Trend" in result or "trend" in result
        assert "Error" not in result

    def test_analyze_time_series_with_weekly_frequency(self):
        result = analyze_time_series.invoke(
            {"date_column": "gas_day", "value_column": "total_scheduled_quantity", "freq": "W"}
        )
        assert "Error" not in result

    def test_analyze_time_series_with_daily_frequency(self):
        result = analyze_time_series.invoke(
            {"date_column": "gas_day", "value_column": "total_scheduled_quantity", "freq": "D"}
        )
        assert "Error" not in result

    def test_analyze_time_series_invalid_date_column(self):
        result = analyze_time_series.invoke(
            {"date_column": "nonexistent", "value_column": "total_scheduled_quantity"}
        )
        assert "Error" in result

    def test_analyze_time_series_invalid_value_column(self):
        result = analyze_time_series.invoke(
            {"date_column": "gas_day", "value_column": "nonexistent"}
        )
        assert "Error" in result


# --- validation ---


@pytest.mark.usefixtures("use_sample_df_with_issues")
class TestCheckConfounders:
    def test_check_confounders_runs(self):
        result = check_confounders.invoke(
            {
                "target_column": "total_scheduled_quantity",
                "feature_column": "design_capacity",
                "potential_confounders": ["region"],
            }
        )
        assert "Confounder" in result or "correlation" in result.lower()
        assert "Error" not in result


@pytest.mark.usefixtures("use_sample_df_with_issues")
class TestRobustnessCheck:
    def test_robustness_check_runs(self):
        result = robustness_check.invoke(
            {
                "metric_column": "total_scheduled_quantity",
                "group_column": "pipeline_name",
            }
        )
        assert "Robustness" in result or "robust" in result.lower()
        assert "Error" not in result

    def test_robustness_check_temporal(self):
        result = robustness_check.invoke(
            {
                "metric_column": "total_scheduled_quantity",
                "group_column": "pipeline_name",
                "test_type": "temporal",
            }
        )
        assert "Temporal" in result or "Error" not in result
