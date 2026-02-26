"""
Helper functions for database queries.
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
from streamlit import cache_data

from streamlit_app.config import METADATA_DB_PATH


@cache_data
def get_all_funds_to_display() -> List[Dict]:
    """
    Retrieves all funds from the metadata database.

    Returns:
        Pyarrow Table with all rows from the funds table, or empty Table on error.
    """
    metadata_path = Path(METADATA_DB_PATH)

    if not metadata_path.exists():
        return []

    try:
        with sqlite3.connect(metadata_path) as conn:
            cursor = conn.cursor()
            query_cursor = cursor.execute("SELECT name, isin, start_date FROM funds")
            colname = ['Nombre', 'ISIN', 'Fecha de inicio']
            result_list = [ dict(zip(colname, r)) for r in query_cursor.fetchall() ]

            return result_list

    except Exception:
        return []

@cache_data
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
            return {f"{row[1]} - {row[0]}": row[0] for row in cursor.fetchall()}
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