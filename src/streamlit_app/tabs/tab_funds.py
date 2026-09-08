"""
Logic for the funds comparison tab.
"""
import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

import streamlit as st

from compare_funds.compare_funds import get_funds_for_comparison
from plot_funds.plot_funds import plot_funds
from streamlit_app.components.funds_components import render_funds_inputs, render_funds_date_selector
from streamlit_app.utils.common import init_session_state


def _initialize_session_state():
    """Initializes necessary session states."""
    init_session_state({
        'last_compared_isins': [],
        'last_start_date': None,
        'last_end_date': None,
        'last_date_mode': None,
        'should_show_comparison': False,
        'last_fig': None,
        'last_html_bytes': None
    })


def _should_execute_comparison(compare_button: bool, isins: list, start_date: str, end_date: str, date_mode: str) -> bool:
    """
    Determines if a new comparison should be executed.

    Args:
        compare_button: Whether the compare button was pressed.
        isins: Current list of ISINs.
        start_date: Current start date.
        date_mode: Current date mode.

    Returns:
        True if comparison should be executed.
    """
    # Detect changes
    date_changed = st.session_state.last_start_date != start_date or st.session_state.last_end_date != end_date
    date_mode_changed = st.session_state.last_date_mode != date_mode
    isins_changed = st.session_state.last_compared_isins != isins

    # Detect if changed to an auto mode
    changed_to_auto_mode = (date_mode_changed and
                            date_mode in ["Histórico completo", "Usar fecha de inicio común"])

    # Execute comparison if:
    if compare_button:
        return True
    elif st.session_state.should_show_comparison and date_changed and not date_mode_changed:
        # Only if date changed within the same mode AND ISINs didn't change
        return not isins_changed
    elif st.session_state.should_show_comparison and changed_to_auto_mode:
        # Only if ISINs didn't change
        return not isins_changed

    return False


def _execute_comparison(isins: list, start_date: str, end_date: str, date_mode: str):
    """
    Executes the funds comparison and shows results.

    Args:
        isins: List of ISINs to compare.
        start_date: Start date of comparison.
        date_mode: Selected date mode.
    """
    # Save current values to session_state
    st.session_state.last_compared_isins = isins.copy()
    st.session_state.last_start_date = start_date
    st.session_state.last_end_date = end_date
    st.session_state.last_date_mode = date_mode

    st.markdown("<br>", unsafe_allow_html=True)

    # Get fund data
    funds_info = get_funds_for_comparison(isins, start_date, end_date)

    if not funds_info:
        st.warning("Could not load data for any fund or no common dates found.")
        st.session_state.last_fig = None
        st.session_state.last_html_bytes = None
    else:
        # Generate chart
        fig = plot_funds(funds_info, start_date)
        html_bytes = fig.to_html(include_plotlyjs='cdn')

        # Save to session_state
        st.session_state.last_fig = fig
        st.session_state.last_html_bytes = html_bytes

        # Show chart and download button
        st.plotly_chart(fig, width='stretch')
        st.download_button(
            label="Descargar gráfico como HTML",
            data=html_bytes,
            file_name="comparador_fondos.html",
            mime="text/html"
        )


def _show_cached_comparison(date_mode: str):
    """
    Shows the last saved chart without recalculating.

    Args:
        date_mode: Current date mode.
    """
    if st.session_state.last_date_mode != date_mode:
        st.session_state.last_date_mode = date_mode

    st.markdown("<br>", unsafe_allow_html=True)

    # Show saved chart
    st.plotly_chart(st.session_state.last_fig, width='stretch')
    st.download_button(
        label="Descargar gráfico como HTML",
        data=st.session_state.last_html_bytes,
        file_name="comparador_fondos.html",
        mime="text/html",
        key="download_cached"
    )


def render_tab_funds():
    """Renders the funds comparison tab."""
    st.markdown("<br>", unsafe_allow_html=True)

    # Initialize session states
    _initialize_session_state()

    # Render fund inputs
    isins = render_funds_inputs("funds")

    st.markdown("<br>", unsafe_allow_html=True)

    # Show info messages BEFORE button
    if not isins or len(isins) == 0:
        st.info("Añade al menos un fondo para ver la comparación")
    elif not st.session_state.should_show_comparison:
        st.info("Presiona 'Comparar fondos' para ver la comparación.")

    # Compare button
    compare_button = st.button(
        "Comparar fondos",
        key="fund_compare_btn",
        type="primary",
        disabled=not isins or len(isins) == 0,
        width='stretch'
    )

    # If there are ISINs and a comparison has been made, show date selector
    if isins and len(isins) > 0 and st.session_state.should_show_comparison:
        start_date, end_date = render_funds_date_selector("funds", isins)
        current_date_mode = st.session_state.get("funds_date_mode", "Usar fecha de inicio común")

        # Determine if comparison should be executed
        should_compare = _should_execute_comparison(
            compare_button, isins, start_date, end_date, current_date_mode
        )

        if should_compare:
            _execute_comparison(isins, start_date, end_date, current_date_mode)
        elif st.session_state.last_fig is not None:
            _show_cached_comparison(current_date_mode)

    # First comparison (when button is pressed for the first time)
    elif compare_button and isins and len(isins) > 0:
        st.session_state.should_show_comparison = True
        # Get default date for first comparison
        start_date, end_date = render_funds_date_selector("funds", isins)
        current_date_mode = st.session_state.get("funds_date_mode", "Usar fecha de inicio común")
        _execute_comparison(isins, start_date, end_date, current_date_mode)