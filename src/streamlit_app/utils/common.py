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


def get_default_end_date() -> datetime.date:
    """
    Returns the default end date for comparisons.
    Logic: The Friday of the week that ended 2 weeks ago.
    Example:
    - If today is Fri 13 Feb, 2 weeks ago was Fri 30 Jan.
    - If today is Sat 14 Feb, 2 weeks ago was Fri 30 Jan.
    - If today is Fri 20 Feb, 2 weeks ago was Fri 6 Feb.

    Basically: Go to last Friday, then subtract 14 days.
    """
    today = datetime.now().date()

    # Calculate days to subtract to get to the most recent Friday (including today)
    # Weekday: Mon=0, ..., Fri=4, ..., Sun=6
    # If today is Friday (4), subtract 0.
    # If today is Saturday (5), subtract 1.
    # If today is Thursday (3), subtract 6 (go back to previous week Friday).

    days_to_last_friday = (today.weekday() - 4) % 7
    last_friday = today - timedelta(days=days_to_last_friday)

    # Subtract 2 weeks (14 days)
    default_end_date = last_friday - timedelta(days=7)

    return default_end_date