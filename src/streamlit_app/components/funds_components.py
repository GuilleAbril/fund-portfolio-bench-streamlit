"""
UI components for fund management.
"""
import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Optional

from compare_funds.compare_funds import get_funds_metadata, fund_exists
from streamlit_app.config import MAX_FUNDS
from streamlit_app.utils.database_utils import get_max_common_start_date, get_min_start_date
from streamlit_app.utils.common import calculate_date_from_period, get_default_end_date


def render_funds_inputs(prefix: str, num_funds: int = MAX_FUNDS) -> List[str]:
    """
    Renders ISIN input boxes and returns a list of valid ISINs.

    Args:
        prefix: Prefix for component keys.
        num_funds: Maximum number of funds to show.

    Returns:
        List of valid ISINs.
    """
    isins = []
    cols = st.columns(2)

    for i in range(num_funds):
        col = cols[i % 2]
        isin = col.text_input(
            f"Fondo {i + 1}",
            placeholder="ISIN",
            key=f"{prefix}_isin_{i}",
            max_chars=12
        ).strip().upper()

        if isin:
            if fund_exists(isin):
                # Get fund name
                metadata = get_funds_metadata([isin])
                name = metadata.get(isin, {}).get('name', isin)
                col.markdown(
                    f'<div class="status-ok">✓ {name}</div>',
                    unsafe_allow_html=True
                )
                isins.append(isin)
            else:
                col.markdown(
                    f'<div class="status-error">✗ {isin} not found</div>',
                    unsafe_allow_html=True
                )

    return isins


def render_funds_date_selector(prefix: str, isins: List[str]) -> Optional[tuple[str, str]]:
    """
    Renders date selector and alignment type for funds.

    Args:
        prefix: Prefix for component keys.
        isins: List of ISINs.

    Returns:
        Tuple of (start_date, end_date) in 'YYYY-MM-DD' format.
    """
    min_start_date = get_min_start_date(isins)
    default_end_date = get_default_end_date()

    # Initialize session_state
    session_key_mode = f"{prefix}_date_selection"
    session_key_range = f"{prefix}_date_range"
    session_key_counter = f"{prefix}_date_counter"
    session_key_last_isins = f"{prefix}_last_isins"

    # Detect changes in funds
    funds_changed = False
    if session_key_last_isins not in st.session_state:
        st.session_state[session_key_last_isins] = []
        funds_changed = True
    elif st.session_state[session_key_last_isins] != isins:
        funds_changed = True

    # If funds changed, reset to common date
    if funds_changed:
        st.session_state[session_key_last_isins] = list(isins)
        st.session_state[session_key_mode] = "Usar fecha de inicio común"
        
        # Calculate common date
        common_date_str = get_max_common_start_date(isins)
        common_date = datetime.strptime(common_date_str, '%Y-%m-%d').date() if common_date_str else datetime.now().date()
        
        st.session_state[session_key_range] = (common_date, default_end_date)
        
        # Increment counter if exists, else initialize
        if session_key_counter not in st.session_state:
            st.session_state[session_key_counter] = 0
        else:
            st.session_state[session_key_counter] += 1

    # Ensure keys exist
    if session_key_mode not in st.session_state:
        st.session_state[session_key_mode] = "Usar fecha de inicio común"
    if session_key_range not in st.session_state:
        # Fallback for safety
        common_date_str = get_max_common_start_date(isins)
        common_date = datetime.strptime(common_date_str, '%Y-%m-%d').date() if common_date_str else datetime.now().date()
        st.session_state[session_key_range] = (common_date, default_end_date)
    if session_key_counter not in st.session_state:
        st.session_state[session_key_counter] = 0

    # Single row with all buttons
    st.markdown("**Start date for comparison:**")

    cols = st.columns([2, 2.5, 0.8, 0.8, 0.8, 0.8, 4])

    # "Full History" button
    if cols[0].button("Histórico completo", key=f"{prefix}_btn_historico", use_container_width=True):
        st.session_state[session_key_mode] = "Histórico completo"
        # Set range from minimum date to today
        min_date = (datetime.strptime(min_start_date, '%Y-%m-%d').date()
                    if min_start_date else datetime(1990, 1, 1).date())
        st.session_state[session_key_range] = (min_date, default_end_date)
        st.session_state[session_key_counter] += 1
        st.rerun()

    # "Common Start Date" button
    if cols[1].button("Usar fecha de inicio común", key=f"{prefix}_btn_comun", use_container_width=True):
        st.session_state[session_key_mode] = "Usar fecha de inicio común"
        # Set range from common date to today
        common_date_str = get_max_common_start_date(isins)
        common_date = datetime.strptime(common_date_str, '%Y-%m-%d').date() if common_date_str else datetime.now().date()
        st.session_state[session_key_range] = (common_date, default_end_date)
        st.session_state[session_key_counter] += 1
        st.rerun()

    # Period buttons
    period_buttons = ["YTD", "1A", "3A", "5A"]
    for i, period in enumerate(period_buttons):
        if cols[i + 2].button(period, key=f"{prefix}_btn_{period}", use_container_width=True):
            st.session_state[session_key_mode] = period
            # Calculate and save dates automatically
            calculated_start = calculate_date_from_period(period, min_start_date)
            st.session_state[session_key_range] = (
                datetime.strptime(calculated_start, '%Y-%m-%d').date(),
                default_end_date
            )
            st.session_state[session_key_counter] += 1
            st.rerun()

    # Show visual indicator of what is selected
    current_mode = st.session_state[session_key_mode]
    if current_mode in ["Histórico completo", "Usar fecha de inicio común"]:
        st.info(f"📅 Selected: **{current_mode}**")
    else:
        st.info(f"📅 Selected period: **{current_mode}**")

    # Date range selector (ALWAYS VISIBLE)
    min_date = (datetime.strptime(min_start_date, '%Y-%m-%d').date()
                if min_start_date else datetime(1990, 1, 1).date())
    # Max selectable date is the default end date (2 weeks ago friday)
    max_selectable_date = default_end_date

    col1, col2 = st.columns(2)

    # Use counter in keys to force re-render
    counter = st.session_state[session_key_counter]

    with col1:
        start_date_input = st.date_input(
            "Fecha desde",
            value=st.session_state[session_key_range][0],
            min_value=min_date,
            max_value=max_selectable_date,
            key=f"{prefix}_custom_start_date_{counter}"
        )

    with col2:
        end_date_input = st.date_input(
            "Fecha hasta",
            value=st.session_state[session_key_range][1],
            min_value=min_date,
            max_value=max_selectable_date,
            key=f"{prefix}_custom_end_date_{counter}"
        )

    # Update range in session_state
    st.session_state[session_key_range] = (start_date_input, end_date_input)

    # Return start and end date
    start_date = start_date_input.strftime('%Y-%m-%d')
    end_date = end_date_input.strftime('%Y-%m-%d')

    return start_date, end_date
