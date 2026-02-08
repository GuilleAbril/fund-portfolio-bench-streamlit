"""
Lógica de la pestaña de comparación de fondos.
"""
import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

import streamlit as st

from compare_funds.compare_funds import get_funds_for_comparison
from plot_funds.plot_funds import plot_funds
from streamlit_app.components.funds_components import render_funds_inputs, render_funds_date_selector


def _initialize_session_state():
    """Inicializa los estados de sesión necesarios."""
    if 'last_compared_isins' not in st.session_state:
        st.session_state.last_compared_isins = []
    if 'last_start_date' not in st.session_state:
        st.session_state.last_start_date = None
    if 'last_date_mode' not in st.session_state:
        st.session_state.last_date_mode = None
    if 'should_show_comparison' not in st.session_state:
        st.session_state.should_show_comparison = False
    if 'last_fig' not in st.session_state:
        st.session_state.last_fig = None
    if 'last_html_bytes' not in st.session_state:
        st.session_state.last_html_bytes = None


def _should_execute_comparison(compare_button: bool, isins: list, start_date: str, date_mode: str) -> bool:
    """
    Determina si se debe ejecutar una nueva comparación.

    Args:
        compare_button: Si se presionó el botón de comparar
        isins: Lista de ISINs actuales
        start_date: Fecha de inicio actual
        date_mode: Modo de fecha actual

    Returns:
        True si se debe ejecutar la comparación
    """
    # Detectar cambios
    date_changed = st.session_state.last_start_date != start_date
    date_mode_changed = st.session_state.last_date_mode != date_mode
    isins_changed = st.session_state.last_compared_isins != isins

    # Detectar si cambió a un modo automático
    changed_to_auto_mode = (date_mode_changed and
                            date_mode in ["Histórico completo", "Usar fecha de inicio común"])

    # Ejecutar comparación si:
    if compare_button:
        return True
    elif st.session_state.should_show_comparison and date_changed and not date_mode_changed:
        # Solo si la fecha cambió dentro del mismo modo Y no cambiaron los ISINs
        return not isins_changed
    elif st.session_state.should_show_comparison and changed_to_auto_mode:
        # Solo si no cambiaron los ISINs
        return not isins_changed

    return False


def _execute_comparison(isins: list, start_date: str, date_mode: str):
    """
    Ejecuta la comparación de fondos y muestra los resultados.

    Args:
        isins: Lista de ISINs a comparar
        start_date: Fecha de inicio de la comparación
        date_mode: Modo de fecha seleccionado
    """
    # Guardar los valores actuales en session_state
    st.session_state.last_compared_isins = isins.copy()
    st.session_state.last_start_date = start_date
    st.session_state.last_date_mode = date_mode

    st.markdown("<br>", unsafe_allow_html=True)

    # Obtener datos de fondos
    funds_info = get_funds_for_comparison(isins, start_date)

    if not funds_info:
        st.warning("No se pudieron cargar datos de ningún fondo o no hay fechas comunes.")
        st.session_state.last_fig = None
        st.session_state.last_html_bytes = None
    else:
        # Generar gráfico
        fig = plot_funds(funds_info, start_date)
        html_bytes = fig.to_html(include_plotlyjs='cdn')

        # Guardar en session_state
        st.session_state.last_fig = fig
        st.session_state.last_html_bytes = html_bytes

        # Mostrar gráfico y botón de descarga
        st.plotly_chart(fig, width='stretch')
        st.download_button(
            label="Descargar gráfico como HTML",
            data=html_bytes,
            file_name="comparador_fondos.html",
            mime="text/html"
        )


def _show_cached_comparison(date_mode: str):
    """
    Muestra la última gráfica guardada sin recalcular.

    Args:
        date_mode: Modo de fecha actual
    """
    if st.session_state.last_date_mode != date_mode:
        st.session_state.last_date_mode = date_mode

    st.markdown("<br>", unsafe_allow_html=True)

    # Mostrar la gráfica guardada
    st.plotly_chart(st.session_state.last_fig, width='stretch')
    st.download_button(
        label="Descargar gráfico como HTML",
        data=st.session_state.last_html_bytes,
        file_name="comparador_fondos.html",
        mime="text/html",
        key="download_cached"
    )


def render_tab_funds():
    """Renderiza la pestaña de comparación de fondos."""
    st.markdown("<br>", unsafe_allow_html=True)

    # Inicializar estados de sesión
    _initialize_session_state()

    # Renderizar inputs de fondos
    isins = render_funds_inputs("funds")

    st.markdown("<br>", unsafe_allow_html=True)

    # Mostrar mensajes informativos ANTES del botón
    if not isins or len(isins) == 0:
        st.info("Añade al menos un fondo para ver la comparación.")
    elif not st.session_state.should_show_comparison:
        st.info("Pulsa 'Comparar fondos' para ver la comparación.")

    # Botón de comparar
    compare_button = st.button(
        "Comparar fondos",
        key="fund_compare_btn",
        type="primary",
        disabled=not isins or len(isins) == 0,
        use_container_width=True
    )

    # Si hay ISINs y ya se ha hecho una comparación, mostrar selector de fecha
    if isins and len(isins) > 0 and st.session_state.should_show_comparison:
        start_date = render_funds_date_selector("funds", isins)
        current_date_mode = st.session_state.get("funds_date_mode", "Usar fecha de inicio común")

        # Determinar si ejecutar comparación
        should_compare = _should_execute_comparison(
            compare_button, isins, start_date, current_date_mode
        )

        if should_compare:
            _execute_comparison(isins, start_date, current_date_mode)
        elif st.session_state.last_fig is not None:
            _show_cached_comparison(current_date_mode)

    # Primera comparación (cuando se pulsa el botón por primera vez)
    elif compare_button and isins and len(isins) > 0:
        st.session_state.should_show_comparison = True
        # Obtener la fecha por defecto para la primera comparación
        start_date = render_funds_date_selector("funds", isins)
        current_date_mode = st.session_state.get("funds_date_mode", "Usar fecha de inicio común")
        _execute_comparison(isins, start_date, current_date_mode)