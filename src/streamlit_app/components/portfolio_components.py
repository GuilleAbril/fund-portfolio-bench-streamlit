"""
UI components for portfolio management.
"""
import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional

from compare_funds.compare_funds import get_funds_metadata
from streamlit_app.config import MAX_FUNDS, MAX_PORTFOLIOS, PORTFOLIO_COLORS
from streamlit_app.utils.database_utils import get_max_common_start_date
from streamlit_app.utils.common import calculate_date_from_period, get_default_end_date


def render_portfolios_inputs() -> List[Dict]:
    """
    Renders portfolio input boxes and returns a list of valid portfolios.

    Returns:
        List of dictionaries with portfolio information:
        {
            'name': str,
            'funds': List[{'isin': str, 'weight': float, 'name': str}],
            'portfolio_start_date': str,
            'color': str
        }
    """
    portfolios = []

    # State to control how many funds each portfolio has
    if "portfolio_fund_counts" not in st.session_state:
        st.session_state.portfolio_fund_counts = [1] * MAX_PORTFOLIOS

    cols = st.columns(MAX_PORTFOLIOS)

    for p_idx in range(MAX_PORTFOLIOS):
        col = cols[p_idx]

        # Input for portfolio name
        portfolio_name = col.text_input(
            "Portfolio Name",
            value=f"Portfolio {p_idx + 1}",
            key=f"portfolio_{p_idx}_name",
            placeholder="Custom Name"
        )

        col.markdown(
            f'<div class="portfolio-card">'
            f'<div class="portfolio-card-header" style="color:{PORTFOLIO_COLORS[p_idx]}">'
            f'{portfolio_name}</div>',
            unsafe_allow_html=True
        )

        funds = []
        num_funds = st.session_state.portfolio_fund_counts[p_idx]
        total_weight = 0.0
        portfolio_isins = []

        from streamlit_app.utils.database_utils import get_fund_options
        fund_options = get_fund_options()
        options_list = list(fund_options.keys())

        for f_idx in range(num_funds):
            session_key = f"portfolio_{p_idx}_selected_isin_{f_idx}"
            search_key = f"port_{p_idx}_search_{f_idx}"
            weight_key = f"portfolio_{p_idx}_weight_{f_idx}"
            
            # Internal layout with clear button
            input_cols = col.columns([0.4, 2, 1])
            
            with input_cols[0]:
                current_isin = st.session_state.get(session_key, "")
                if current_isin:
                    st.markdown('<div class="clear-fund-btn">', unsafe_allow_html=True)
                    if st.button("✕", key=f"port_{p_idx}_clear_{f_idx}", help="Quitar fondo"):
                        st.session_state[session_key] = ""
                        if search_key in st.session_state:
                            st.session_state[search_key] = None
                        if weight_key in st.session_state:
                            st.session_state[weight_key] = 0.0
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.write("")

            # Get current ISIN if already selected
            current_isin = st.session_state.get(session_key, "")
            
            # Find corresponding label for the selectbox value
            index = None
            if current_isin:
                for label, isin in fund_options.items():
                    if isin == current_isin:
                        index = options_list.index(label)
                        break

            selected_label = input_cols[1].selectbox(
                "Fondo",
                options=options_list,
                index=index,
                placeholder="ISIN o nombre del fondo",
                key=search_key,
                label_visibility="visible" if f_idx == 0 else "hidden"
            )

            weight = input_cols[2].number_input(
                "Weight %",
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                value=st.session_state.get(weight_key, 0.0),
                key=weight_key,
                label_visibility="visible" if f_idx == 0 else "hidden"
            )

            if selected_label:
                selected_isin = fund_options[selected_label]
                st.session_state[session_key] = selected_isin
                
                metadata = get_funds_metadata([selected_isin])
                name = metadata.get(selected_isin, {}).get('name', selected_isin)
                col.markdown(
                    f'<div class="status-ok">✓ {name} - {selected_isin}</div>',
                    unsafe_allow_html=True
                )
                funds.append({'isin': selected_isin, 'weight': weight, 'name': name})
                portfolio_isins.append(selected_isin)
                total_weight += weight
            else:
                st.session_state[session_key] = ""

        # Total weight indicator
        _render_weight_indicator(col, total_weight)

        # Button to add fund
        if num_funds < MAX_FUNDS:
            if col.button("+ Añadir fondo", key=f"add_fund_{p_idx}"):
                st.session_state.portfolio_fund_counts[p_idx] += 1
                st.rerun()

        col.markdown('</div>', unsafe_allow_html=True)

        # Add portfolio to list if valid
        if funds and abs(total_weight - 100.0) < 0.01:
            portfolio_start_date = get_max_common_start_date(portfolio_isins)
            portfolios.append({
                'name': portfolio_name,
                'funds': funds,
                'portfolio_start_date': portfolio_start_date,
                'color': PORTFOLIO_COLORS[p_idx]
            })

    return portfolios


def _render_weight_indicator(col, total_weight: float):
    """
    Renders the total weight indicator for a portfolio.

    Args:
        col: Streamlit column to render in.
        total_weight: Total weight of the portfolio.
    """
    if total_weight > 0:
        if abs(total_weight - 100.0) < 0.01:
            css_class = "weight-ok"
            symbol = "✓"
        elif total_weight > 100.0:
            css_class = "weight-error"
            symbol = "✗"
        else:
            css_class = "weight-warning"
            symbol = "⚠"

        col.markdown(
            f'<div class="weight-indicator {css_class}">'
            f'{symbol} Total weight: {total_weight:.1f}%</div>',
            unsafe_allow_html=True
        )


def render_portfolios_date_selector(prefix: str, portfolios_start_dates: Optional[List[str]], portfolios_structure: List[Dict])\
        -> Optional[tuple[str, str]]:
    """
    Renders date selector and alignment type for portfolios.

    Args:
        prefix: Prefix for component keys.
        portfolios_start_dates: List of portfolio start dates.
        portfolios_structure: Current structure of portfolios to detect changes.

    Returns:
        Selected start date in 'YYYY-MM-DD' format or None.
    """
    # Calculate global minimum date (oldest possible date among all portfolios)
    # and global common date (most recent date among all portfolio starts)
    min_start_date = None
    common_start_date_str = None

    if portfolios_start_dates:
        # The common date valid for all is the MAX of the starts
        common_start_date_str = max(portfolios_start_dates)
        default_end_date = get_default_end_date()
        
        # For "Full History", we want to see from the beginning of time of the oldest portfolio
        # or at least give the option to go back.
        min_start_date = min(portfolios_start_dates)

    # Initialize session_state
    session_key_mode = f"{prefix}_date_selection"
    session_key_range = f"{prefix}_date_range"
    session_key_counter = f"{prefix}_date_counter"
    session_key_last_structure = f"{prefix}_last_structure"

    # Detect changes in portfolio structure
    # Use string representation or hashable of relevant structure (funds + weights)
    current_structure_repr = str([{p['name']: p['funds']} for p in portfolios_structure])
    
    structure_changed = False
    if session_key_last_structure not in st.session_state:
        st.session_state[session_key_last_structure] = ""
        structure_changed = True
    elif st.session_state[session_key_last_structure] != current_structure_repr:
        structure_changed = True

    # If structure changed, reset to common date
    if structure_changed:
        st.session_state[session_key_last_structure] = current_structure_repr
        st.session_state[session_key_mode] = "Usar fecha de inicio común"
        
        common_date = datetime.strptime(common_start_date_str, '%Y-%m-%d').date() if common_start_date_str else default_end_date
        st.session_state[session_key_range] = (common_date, default_end_date)
        
        if session_key_counter not in st.session_state:
            st.session_state[session_key_counter] = 0
        else:
            st.session_state[session_key_counter] += 1

    if session_key_mode not in st.session_state:
        st.session_state[session_key_mode] = "Usar fecha de inicio común"
    if session_key_range not in st.session_state:
        # Default to common date if data exists
        start_d = common_start_date_str if common_start_date_str else (min_start_date if min_start_date else None)
        common_date = datetime.strptime(start_d, '%Y-%m-%d').date() if start_d else default_end_date
        st.session_state[session_key_range] = (common_date, default_end_date)
    if session_key_counter not in st.session_state:
        st.session_state[session_key_counter] = 0

    st.markdown("**Periodo de comparación:**")

    cols = st.columns([2, 2.5, 0.8, 0.8, 0.8, 0.8, 4])

    # "Full History" button: allows viewing from the start of the oldest portfolio
    if cols[0].button("Histórico completo", key=f"{prefix}_btn_historico", width='stretch'):
        st.session_state[session_key_mode] = "Histórico completo"
        min_date = (datetime.strptime(min_start_date, '%Y-%m-%d').date()
                    if min_start_date else datetime(1990, 1, 1).date())
        st.session_state[session_key_range] = (min_date, default_end_date)
        st.session_state[session_key_counter] += 1
        st.rerun()

    # "Common Start Date" button
    if cols[1].button("Usar fecha de inicio común", key=f"{prefix}_btn_comun", width='stretch'):
        st.session_state[session_key_mode] = "Usar fecha de inicio común"
        common_date = datetime.strptime(common_start_date_str, '%Y-%m-%d').date() if common_start_date_str else default_end_date
        st.session_state[session_key_range] = (common_date, default_end_date)
        st.session_state[session_key_counter] += 1
        st.rerun()

    # Period buttons
    period_buttons = ["YTD", "1A", "3A", "5A"]
    for i, period in enumerate(period_buttons):
        if cols[i + 2].button(period, key=f"{prefix}_btn_{period}", width='stretch'):
            st.session_state[session_key_mode] = period
            calculated_start = calculate_date_from_period(period, min_start_date)
            st.session_state[session_key_range] = (
                datetime.strptime(calculated_start, '%Y-%m-%d').date(),
                default_end_date
            )
            st.session_state[session_key_counter] += 1
            st.rerun()

    # Indicator
    current_mode = st.session_state[session_key_mode]
    if current_mode in ["Histórico completo", "Usar fecha de inicio común"]:
        st.info(f"📅 Selected: **{current_mode}**")
    else:
        st.info(f"📅 Selected period: **{current_mode}**")

    # Manual date selectors
    # The minimum allowed date in the selector must be the global minimum (to allow backing up)
    min_date_obj = (datetime.strptime(min_start_date, '%Y-%m-%d').date()
                if min_start_date else datetime(1990, 1, 1).date())

    col1, col2 = st.columns(2)
    counter = st.session_state[session_key_counter]

    with col1:
        start_date_input = st.date_input(
            "Fecha desde",
            value=st.session_state[session_key_range][0],
            min_value=min_date_obj,
            max_value=default_end_date,
            key=f"{prefix}_custom_start_date_{counter}"
        )

    with col2:
        end_date_input = st.date_input(
            "Fecha hasta",
            value=st.session_state[session_key_range][1],
            min_value=min_date_obj,
            max_value=default_end_date,
            key=f"{prefix}_custom_end_date_{counter}"
        )

    st.session_state[session_key_range] = (start_date_input, end_date_input)
    # Return start and end date
    start_date = start_date_input.strftime('%Y-%m-%d')
    end_date = end_date_input.strftime('%Y-%m-%d')
    
    return start_date, end_date