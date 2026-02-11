"""
Helper functions for database queries.
"""
import sqlite3
from typing import Optional, List
from pathlib import Path

from streamlit_app.config import METADATA_DB_PATH


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