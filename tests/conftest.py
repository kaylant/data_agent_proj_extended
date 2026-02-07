"""Pytest fixtures for tests"""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_df():
    """Create a small sample dataframe for testing"""
    return pd.DataFrame(
        {
            "pipeline_name": ["Pipeline A", "Pipeline A", "Pipeline B", "Pipeline B", "Pipeline C"],
            "location_state_ab": ["TX", "TX", "CA", "CA", "OK"],
            "total_scheduled_quantity": [100.0, 200.0, 150.0, None, 300.0],
            "design_capacity": [500.0, 500.0, 400.0, 400.0, 600.0],
            "operating_capacity": [450.0, 450.0, 380.0, 380.0, 550.0],
            "gas_day": pd.to_datetime(
                ["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02", "2024-01-01"]
            ),
        }
    )


@pytest.fixture
def sample_df_with_issues():
    """Dataframe with data quality issues for testing (placeholders, negatives, invalid coords)."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame(
        {
            "pipeline_name": np.random.choice(
                ["Pipeline A", "Pipeline B", "Pipeline C", "Pipeline D"], n
            ),
            "region": np.random.choice(["East", "West", "South"], n),
            "total_scheduled_quantity": np.concatenate(
                [
                    np.random.normal(1000, 200, n - 5),
                    [999999999, -100, 0, 0, 0],
                ]
            ),
            "design_capacity": np.concatenate(
                [
                    np.random.normal(5000, 500, n - 3),
                    [999999999, 3000, 4000],
                ]
            ),
            "operating_capacity": np.concatenate(
                [
                    np.random.normal(4500, 400, n - 2),
                    [6000, 5500],
                ]
            ),
            "location_latitude": np.concatenate(
                [
                    np.random.uniform(30, 45, n - 2),
                    [-100, 95],
                ]
            ),
            "gas_day": pd.date_range("2024-01-01", periods=n, freq="D"),
        }
    )
