"""
Common utility functions for the Streamlit application.
"""
from datetime import datetime, timedelta
from typing import Optional, Any

import streamlit as st


def calculate_date_from_period(period: str, min_start_date: Optional[str] = None) -> str:
    """
    Calculates the start date based on the selected period.

    Args:
        period: Selected period (YTD, 1A, 3A, 5A).
        min_start_date: Minimum available start date (optional).

    Returns:
        Date string in 'YYYY-MM-DD' format.
    """
    today = datetime.now().date()

    if period == "YTD":
        # From January 1st of the current year
        start_date = datetime(today.year, 1, 1).date()
    elif period == "1A":
        start_date = today - timedelta(days=365)
    elif period == "3A":
        start_date = today - timedelta(days=365 * 3)
    elif period == "5A":
        start_date = today - timedelta(days=365 * 5)
    else:
        start_date = today

    # Ensure it's not before the minimum available date
    if min_start_date:
        min_date = datetime.strptime(min_start_date, '%Y-%m-%d').date()
        if start_date < min_date:
            start_date = min_date

    return start_date.strftime('%Y-%m-%d')


def init_session_state(keys_defaults: dict[str, Any]) -> None:
    """
    Initializes session state keys with default values.

    Args:
        keys_defaults: Dictionary mapping session state keys to their default values.
    """
    for key, default_value in keys_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
