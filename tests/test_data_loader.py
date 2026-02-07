"""Tests for data loader"""

from src.data_loader import get_schema_summary


def test_get_schema_summary(sample_df):
    """Test schema summary generation"""
    summary = get_schema_summary(sample_df)

    assert "5 rows" in summary
    assert "6 columns" in summary
    assert "pipeline_name" in summary
    assert "total_scheduled_quantity" in summary


def test_get_schema_summary_shows_null_percentage(sample_df):
    """Test that schema summary includes null info"""
    summary = get_schema_summary(sample_df)

    # total_scheduled_quantity has 1 null out of 5 = 20%
    assert "20.0% null" in summary or "20%" in summary
