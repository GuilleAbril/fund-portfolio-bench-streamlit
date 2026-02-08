"""
Funciones auxiliares para consultas a la base de datos.
"""
import sqlite3
from typing import Optional
from pathlib import Path

from streamlit_app.config import METADATA_DB_PATH


def get_max_common_start_date(isins: list[str]) -> Optional[str]:
    """
    Obtiene la fecha más reciente de inicio entre los fondos (fecha común más tardía).

    Args:
        isins: Lista de ISINs de fondos

    Returns:
        Fecha en formato 'YYYY-MM-DD' o None si no se encuentra
    """
    metadata_path = Path(METADATA_DB_PATH)
    if not metadata_path.exists():
        return None

    try:
        conn = sqlite3.connect(metadata_path)
        placeholders = ','.join('?' * len(isins))
        cursor = conn.execute(
            f'SELECT MAX(start_date) FROM funds WHERE isin IN ({placeholders})',
            isins
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception:
        return None


def get_min_start_date(isins: list[str]) -> Optional[str]:
    """
    Obtiene la fecha más antigua de inicio entre los fondos.

    Args:
        isins: Lista de ISINs de fondos

    Returns:
        Fecha en formato 'YYYY-MM-DD' o None si no se encuentra
    """
    metadata_path = Path(METADATA_DB_PATH)
    if not metadata_path.exists():
        return None

    try:
        conn = sqlite3.connect(metadata_path)
        placeholders = ','.join('?' * len(isins))
        cursor = conn.execute(
            f'SELECT MIN(start_date) FROM funds WHERE isin IN ({placeholders})',
            isins
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception:
        return None