"""
UI components for fund management.
"""
import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

import streamlit as st
from datetime import datetime
from typing import List, Optional

from compare_funds.compare_funds import get_funds_metadata
from streamlit_app.config import MAX_FUNDS
from streamlit_app.utils.database_utils import get_max_common_start_date, get_min_start_date
from streamlit_app.utils.common import calculate_date_from_period, get_default_end_date


def render_funds_inputs(prefix: str, num_funds: int = MAX_FUNDS) -> List[str]:
    """
    Renders fund selection boxes using a searchable selectbox (dropdown).
    Users can type ISIN or name to filter the list.

    Args:
        prefix: Prefix for component keys.
        num_funds: Maximum number of funds to show.

    Returns:
        List of valid ISINs.
    """
    from streamlit_app.utils.database_utils import get_fund_options
    
    isins = []
    fund_options = get_fund_options() # Mapping of "Name (ISIN)" -> ISIN
    options_list = list(fund_options.keys())
    
    cols = st.columns(2)
    
    # Column configuration for internal layout (clear button + selectbox)
    SEARCH_COLS_RATIO = [1, 20]

    for i in range(num_funds):
        col = cols[i % 2]
        session_key = f"{prefix}_selected_isin_{i}"
        search_key = f"{prefix}_search_{i}"
        
        # Internal layout for each fund slot
        inner_cols = col.columns(SEARCH_COLS_RATIO)
        
        # Clear button (X)
        with inner_cols[0]:
            # Only show if a fund is selected
            current_isin = st.session_state.get(session_key, "")
            if current_isin:
                st.markdown('<div class="clear-fund-btn">', unsafe_allow_html=True)
                if st.button("✕", key=f"{prefix}_clear_{i}", help="Quitar fondo"):
                    st.session_state[session_key] = ""
                    # We need to handle the internal selectbox key if it exists
                    if search_key in st.session_state:
                        st.session_state[search_key] = None
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                # Use empty space to maintain layout alignment
                st.write("")

        with inner_cols[1]:
            # Get current ISIN if already selected
            current_isin = st.session_state.get(session_key, "")
            
            # Find corresponding label for the selectbox value
            index = None
            if current_isin:
                for label, isin in fund_options.items():
                    if isin == current_isin:
                        index = options_list.index(label)
                        break

            selected_label = st.selectbox(
                f"Fondo {i + 1}",
                options=options_list,
                index=index,
                placeholder="ISIN o nombre del fondo",
                key=search_key,
            )

            if selected_label:
                selected_isin = fund_options[selected_label]
                st.session_state[session_key] = selected_isin
                isins.append(selected_isin)
                
                # Extract name for confirmation display
                metadata = get_funds_metadata([selected_isin])
                name = metadata.get(selected_isin, {}).get('name', selected_isin)
                st.markdown(
                    f'<div class="status-ok">✓ {name} - {selected_isin}</div>',
                    unsafe_allow_html=True
                )
            else:
                # If nothing selected, clear the state for this index
                st.session_state[session_key] = ""

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
        common_date = datetime.strptime(common_date_str, '%Y-%m-%d').date()
        
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
        common_date = datetime.strptime(common_date_str, '%Y-%m-%d').date()
        st.session_state[session_key_range] = (common_date, default_end_date)
    if session_key_counter not in st.session_state:
        st.session_state[session_key_counter] = 0

    # Single row with all buttons
    st.markdown("**Periodo de comparación:**")

    cols = st.columns([2, 2.5, 0.8, 0.8, 0.8, 0.8, 4])

    # "Full History" button
    if cols[0].button("Histórico completo", key=f"{prefix}_btn_historico", width='stretch'):
        st.session_state[session_key_mode] = "Histórico completo"
        # Set range from minimum date to today
        min_date = (datetime.strptime(min_start_date, '%Y-%m-%d').date()
                    if min_start_date else datetime(1990, 1, 1).date())
        st.session_state[session_key_range] = (min_date, default_end_date)
        st.session_state[session_key_counter] += 1
        st.rerun()

    # "Common Start Date" button
    if cols[1].button("Usar fecha de inicio común", key=f"{prefix}_btn_comun", width='stretch'):
        st.session_state[session_key_mode] = "Usar fecha de inicio común"
        # Set range from common date to today
        common_date_str = get_max_common_start_date(isins)
        common_date = datetime.strptime(common_date_str, '%Y-%m-%d').date()
        st.session_state[session_key_range] = (common_date, default_end_date)
        st.session_state[session_key_counter] += 1
        st.rerun()

    # Period buttons
    period_buttons = ["YTD", "1A", "3A", "5A"]
    for i, period in enumerate(period_buttons):
        if cols[i + 2].button(period, key=f"{prefix}_btn_{period}", width='stretch'):
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
        st.info(f"📅 **{current_mode}**")
    else:
        st.info(f"📅 Periodo seleccionado: **{current_mode}**")

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
