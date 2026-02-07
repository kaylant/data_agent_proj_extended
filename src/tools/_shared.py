"""Shared utilities for tools - avoids circular imports"""


def get_dataframe():
    """Get the shared dataframe."""
    from src.tools import _df

    return _df
