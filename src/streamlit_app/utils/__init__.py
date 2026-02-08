"""
Módulo de utilidades para la aplicación.
"""
from .database_utils import get_max_common_start_date, get_min_start_date

__all__ = [
    'get_max_common_start_date',
    'get_min_start_date',
]