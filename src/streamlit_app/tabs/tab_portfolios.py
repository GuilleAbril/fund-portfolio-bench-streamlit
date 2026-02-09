"""
Lógica de la pestaña de comparación de carteras.
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
    """Inicializa los estados de sesión necesarios para carteras."""
    if 'last_compared_portfolios' not in st.session_state:
        st.session_state.last_compared_portfolios = []
    if 'last_portfolios_start_date' not in st.session_state:
        st.session_state.last_portfolios_start_date = None
    if 'last_portfolios_date_mode' not in st.session_state:
        st.session_state.last_portfolios_date_mode = None
    if 'should_show_portfolios_comparison' not in st.session_state:
        st.session_state.should_show_portfolios_comparison = False
    if 'last_portfolios_fig' not in st.session_state:
        st.session_state.last_portfolios_fig = None
    if 'last_portfolios_html_bytes' not in st.session_state:
        st.session_state.last_portfolios_html_bytes = None


def _should_execute_comparison(compare_button: bool, portfolios: list, start_date: str, date_mode: str) -> bool:
    """
    Determina si se debe ejecutar una nueva comparación de carteras.
    """
    # Representación simple para comparar cambios en estructura
    current_structure_repr = str([{p['name']: p['funds']} for p in portfolios])
    
    # Recuperar estructura anterior si existe
    last_structure_repr = ""
    if st.session_state.last_compared_portfolios:
         last_structure_repr = str([{p['name']: p['funds']} for p in st.session_state.last_compared_portfolios])

    date_changed = st.session_state.last_portfolios_start_date != start_date
    date_mode_changed = st.session_state.last_portfolios_date_mode != date_mode
    structure_changed = current_structure_repr != last_structure_repr

    # Detectar si cambió a un modo automático (YA NO ES NECESARIO RESTRINGIR)
    # changed_to_auto_mode = (date_mode_changed and
    #                         date_mode in ["Histórico completo", "Usar fecha de inicio común"])

    if compare_button:
        return True
    
    # Si ya se mostró la comparación anteriormente
    elif st.session_state.should_show_portfolios_comparison:
        # Si hubo cualquier cambio en la fecha (valor o modo) y NO hubo cambios en la estructura de carteras
        if (date_changed or date_mode_changed) and not structure_changed:
            return True

    return False


def _execute_comparison(portfolios: list, start_date: str, date_mode: str):
    """
    Ejecuta la comparación de carteras y muestra los resultados.
    """
    st.session_state.last_compared_portfolios = portfolios
    st.session_state.last_portfolios_start_date = start_date
    st.session_state.last_portfolios_date_mode = date_mode

    st.markdown("<br>", unsafe_allow_html=True)

    # Obtener datos de carteras (ya tienen sus fechas de inicio calculadas)
    portfolios_info = get_portfolios_for_comparison(
        portfolios, 
        start_date
    )

    if not portfolios_info:
        st.warning("No se pudieron cargar datos de ninguna cartera.")
        st.session_state.last_portfolios_fig = None
        st.session_state.last_portfolios_html_bytes = None
    else:
        # Generar gráfico
        fig = plot_portfolios(portfolios_info, start_date)
        html_bytes = fig.to_html(include_plotlyjs='cdn')

        # Guardar en session_state
        st.session_state.last_portfolios_fig = fig
        st.session_state.last_portfolios_html_bytes = html_bytes

        # Mostrar gráfico y botón de descarga
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
    Muestra la última gráfica guardada de carteras sin recalcular.
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
    """Renderiza la pestaña de comparación de carteras."""
    st.markdown("<br>", unsafe_allow_html=True)

    _initialize_session_state()

    # Renderizar inputs de carteras
    portfolios = render_portfolios_inputs()

    st.markdown("<br>", unsafe_allow_html=True)

    # Mensajes informativos y botón de comparar
    if not portfolios:
        st.info("Añade al menos una cartera con fondos y pesos (que sumen 100%) para continuar.")
    
    # Botón de comparar (siempre visible)
    compare_button = st.button(
        "Comparar carteras",
        key="portfolio_compare_btn",
        type="primary",
        disabled=not portfolios,
        use_container_width=True
    )
    
    if not portfolios and not st.session_state.should_show_portfolios_comparison:
         pass # Ya mostramos el info arriba
    elif portfolios and not st.session_state.should_show_portfolios_comparison and not compare_button:
         st.info("Pulsa 'Comparar carteras' para ver el análisis.")


    # Lógica de visualización
    if portfolios:
        portfolios_start_dates = [p["portfolio_start_date"] for p in portfolios]
        
        # Renderizar selector de fecha (si ya estamos mostrando comparación o si se pulsa el botón)
        if st.session_state.should_show_portfolios_comparison or compare_button:
            # Renderizamos el selector siempre para tener la fecha, aunque no mostremos la gráfica todavía si es la primera vez (antes del click)
            # Pero el click ya pone should_show a True.
            
            # Si es la primera vez que se pulsa, activamos flag
            if compare_button:
                st.session_state.should_show_portfolios_comparison = True

            start_date = render_portfolios_date_selector("portfolios", portfolios_start_dates, portfolios)
            current_date_mode = st.session_state.get("portfolios_date_selection", "Usar fecha de inicio común")

            # Lógica para determinar si enviamos una fecha específica o None (histórico completo real por cartera)
            comparison_start_date = start_date
            if current_date_mode == "Histórico completo" and portfolios_start_dates:
                min_date_str = min(portfolios_start_dates)
                if start_date == min_date_str:
                    comparison_start_date = None

            should_compare = _should_execute_comparison(
                compare_button, portfolios, comparison_start_date, current_date_mode
            )

            if should_compare:
                _execute_comparison(portfolios, comparison_start_date, current_date_mode)
            elif st.session_state.last_portfolios_fig is not None:
                _show_cached_comparison(current_date_mode)