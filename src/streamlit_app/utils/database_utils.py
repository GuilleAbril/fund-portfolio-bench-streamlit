"""
Helper functions for database queries.
"""
import sqlite3
from typing import Optional, List, Dict
from pathlib import Path

import pandas as pd

from streamlit_app.config import METADATA_DB_PATH, PROJECT_ROOT_PATH


def get_all_funds() -> pd.DataFrame:
    """
    Retrieves all funds from the metadata database.

    Returns:
        DataFrame with all rows from the funds table, or empty DataFrame on error.
    """
    metadata_path = Path(METADATA_DB_PATH)
    if not metadata_path.exists():
        return pd.DataFrame()

    try:
        with sqlite3.connect(metadata_path) as conn:
            return pd.read_sql_query("SELECT * FROM funds", conn)
    except Exception:
        return pd.DataFrame()


def search_funds_by_name(query: str) -> List[Dict[str, str]]:
    """
    Searches funds whose name contains the given query (case-insensitive).

    Args:
        query: Search string (should be at least 3 characters).

    Returns:
        List of dicts with 'isin' and 'name' keys for matching funds.
    """
    if len(query) < 3:
        return []

    metadata_path = Path(METADATA_DB_PATH)
    if not metadata_path.exists():
        return []

    try:
        with sqlite3.connect(metadata_path) as conn:
            cursor = conn.execute(
                "SELECT isin, name FROM funds WHERE name LIKE ? LIMIT 10",
                (f"%{query}%",)
            )
            return [{'isin': row[0], 'name': row[1]} for row in cursor.fetchall()]
    except Exception:
        return []


def get_fund_options() -> Dict[str, str]:
    """
    Returns a mapping of display labels to ISINs for all funds.
    Example: {"Santander Gestion Global (ES0175835000)": "ES0175835000"}
    """
    metadata_path = Path(METADATA_DB_PATH)
    if not metadata_path.exists():
        return {}
    try:
        with sqlite3.connect(metadata_path) as conn:
            cursor = conn.execute("SELECT isin, name FROM funds ORDER BY name")
            return {f"{row[1]} ({row[0]})": row[0] for row in cursor.fetchall()}
    except Exception:
        return {}


def get_max_common_start_date(isins: List[str]) -> Optional[str]:
    """
    Gets the most recent start date among the funds (latest common start date).

    Args:
        isins: List of fund ISINs.

    Returns:
        Date in 'YYYY-MM-DD' format or None if not found.
    """
    metadata_path = Path(METADATA_DB_PATH)

    if not metadata_path.exists():
        return None

    try:
        with sqlite3.connect(metadata_path) as conn:
            placeholders = ','.join('?' * len(isins))
            query = f'SELECT MAX(start_date) FROM funds WHERE isin IN ({placeholders})'
            cursor = conn.execute(query, isins)
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception:
        return None


def get_min_start_date(isins: List[str]) -> Optional[str]:
    """
    Gets the oldest start date among the funds.

    Args:
        isins: List of fund ISINs.

    Returns:
        Date in 'YYYY-MM-DD' format or None if not found.
    """
    metadata_path = Path(METADATA_DB_PATH)
    if not metadata_path.exists():
        return None

    try:
        with sqlite3.connect(metadata_path) as conn:
            placeholders = ','.join('?' * len(isins))
            query = f'SELECT MIN(start_date) FROM funds WHERE isin IN ({placeholders})'
            cursor = conn.execute(query, isins)
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception:
        return None