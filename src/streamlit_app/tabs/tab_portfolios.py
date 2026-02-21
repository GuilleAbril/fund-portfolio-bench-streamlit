"""
Logic for the portfolio comparison tab.
"""
import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

import streamlit as st

from compare_funds.compare_funds import get_portfolios_for_comparison
from plot_funds.plot_funds import plot_portfolios
from streamlit_app.components.portfolio_components import render_portfolios_inputs, render_portfolios_date_selector



def _initialize_session_state():
    """Initializes session state keys required for the portfolios tab."""
    if 'last_compared_portfolios' not in st.session_state:
        st.session_state.last_compared_portfolios = []
    if 'last_portfolios_start_date' not in st.session_state:
        st.session_state.last_portfolios_start_date = None
    if 'last_portfolios_end_date' not in st.session_state:
        st.session_state.last_portfolios_end_date = None
    if 'last_portfolios_date_mode' not in st.session_state:
        st.session_state.last_portfolios_date_mode = None
    if 'should_show_portfolios_comparison' not in st.session_state:
        st.session_state.should_show_portfolios_comparison = False
    if 'last_portfolios_fig' not in st.session_state:
        st.session_state.last_portfolios_fig = None
    if 'last_portfolios_html_bytes' not in st.session_state:
        st.session_state.last_portfolios_html_bytes = None


def _should_execute_comparison(compare_button: bool, portfolios: list, start_date: str, end_date: str, date_mode: str) -> bool:
    """
    Determines whether a new portfolio comparison should be executed.

    Args:
        compare_button: Whether the compare button was pressed.
        portfolios: Current list of portfolio dicts.
        start_date: Current start date.
        end_date: Current end date.
        date_mode: Current date selection mode.

    Returns:
        True if comparison should be executed.
    """
    current_structure_repr = str([{p['name']: p['funds']} for p in portfolios])
    
    last_structure_repr = ""
    if st.session_state.last_compared_portfolios:
         last_structure_repr = str([{p['name']: p['funds']} for p in st.session_state.last_compared_portfolios])

    date_changed = st.session_state.last_portfolios_start_date != start_date or st.session_state.last_portfolios_end_date != end_date
    date_mode_changed = st.session_state.last_portfolios_date_mode != date_mode
    structure_changed = current_structure_repr != last_structure_repr

    if compare_button:
        return True
    
    # Re-execute if the comparison is already shown and dates changed without structure change
    elif st.session_state.should_show_portfolios_comparison:
        if (date_changed or date_mode_changed) and not structure_changed:
            return True

    return False


def _execute_comparison(portfolios: list, start_date: str, end_date: str, date_mode: str):
    """
    Executes the portfolio comparison and displays results.

    Args:
        portfolios: List of portfolio dicts to compare.
        start_date: Start date for comparison.
        end_date: End date for comparison.
        date_mode: Selected date mode.
    """
    st.session_state.last_compared_portfolios = portfolios
    st.session_state.last_portfolios_start_date = start_date
    st.session_state.last_portfolios_end_date = end_date
    st.session_state.last_portfolios_date_mode = date_mode

    st.markdown("<br>", unsafe_allow_html=True)

    portfolios_info = get_portfolios_for_comparison(
        portfolios, 
        start_date,
        end_date
    )

    if not portfolios_info:
        st.warning("No se pudieron cargar datos de ninguna cartera.")
        st.session_state.last_portfolios_fig = None
        st.session_state.last_portfolios_html_bytes = None
    else:
        fig = plot_portfolios(portfolios_info, start_date)
        html_bytes = fig.to_html(include_plotlyjs='cdn')

        st.session_state.last_portfolios_fig = fig
        st.session_state.last_portfolios_html_bytes = html_bytes

        st.plotly_chart(fig, width='stretch')
        st.download_button(
            label="Descargar gráfico como HTML",
            data=html_bytes,
            file_name="comparador_carteras.html",
            mime="text/html",
            key="download_portfolios_new"
        )


def _show_cached_comparison(date_mode: str):
    """
    Displays the last saved portfolio chart without recalculating.

    Args:
        date_mode: Current date mode.
    """
    if st.session_state.last_portfolios_date_mode != date_mode:
        st.session_state.last_portfolios_date_mode = date_mode

    st.markdown("<br>", unsafe_allow_html=True)

    st.plotly_chart(st.session_state.last_portfolios_fig, width='stretch')
    st.download_button(
        label="Descargar gráfico como HTML",
        data=st.session_state.last_portfolios_html_bytes,
        file_name="comparador_carteras.html",
        mime="text/html",
        key="download_portfolios_cached"
    )


def render_tab_portfolios():
    """Renders the portfolio comparison tab."""
    st.markdown("<br>", unsafe_allow_html=True)

    _initialize_session_state()

    # Render portfolio inputs
    portfolios = render_portfolios_inputs()

    st.markdown("<br>", unsafe_allow_html=True)

    if not portfolios:
        st.info("Añade al menos una cartera con fondos y pesos (que sumen 100%) para continuar.")
    
    # Compare button (always visible)
    compare_button = st.button(
        "Comparar carteras",
        key="portfolio_compare_btn",
        type="primary",
        disabled=not portfolios,
        use_container_width=True
    )
    
    if not portfolios and not st.session_state.should_show_portfolios_comparison:
         pass
    elif portfolios and not st.session_state.should_show_portfolios_comparison and not compare_button:
         st.info("Pulsa 'Comparar carteras' para ver el análisis.")


    # Comparison display logic
    if portfolios:
        portfolios_start_dates = [p["portfolio_start_date"] for p in portfolios]
        
        if st.session_state.should_show_portfolios_comparison or compare_button:
            if compare_button:
                st.session_state.should_show_portfolios_comparison = True

            start_date, end_date = render_portfolios_date_selector("portfolios", portfolios_start_dates, portfolios)
            current_date_mode = st.session_state.get("portfolios_date_selection", "Usar fecha de inicio común")

            # When "Histórico completo" is selected and start equals the min portfolio date,
            # pass None to let each portfolio use its own start date
            comparison_start_date = start_date
            if current_date_mode == "Histórico completo" and portfolios_start_dates:
                min_date_str = min(portfolios_start_dates)
                if start_date == min_date_str:
                    comparison_start_date = None

            should_compare = _should_execute_comparison(
                compare_button, portfolios, comparison_start_date, end_date, current_date_mode
            )

            if should_compare:
                _execute_comparison(portfolios, comparison_start_date, end_date, current_date_mode)
            elif st.session_state.last_portfolios_fig is not None:
                _show_cached_comparison(current_date_mode)