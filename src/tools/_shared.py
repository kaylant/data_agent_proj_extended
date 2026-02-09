"""Shared utilities for tools - avoids circular imports"""

import os

USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"
_cached_df = None


def get_dataframe():
    """Get the dataframe - either from memory or database"""
    global _cached_df

    if USE_DATABASE:
        # In database mode, cache the dataframe after first load
        if _cached_df is not None:
            return _cached_df

        from src.database import get_dataframe_from_db

        print("Loading data from database for tool execution...")
        _cached_df = get_dataframe_from_db()
        print(f"✓ Loaded {len(_cached_df):,} rows")
        return _cached_df
    else:
        from src.tools import _df

        return _df
