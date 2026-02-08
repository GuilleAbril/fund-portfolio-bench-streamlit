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


def render_tab_portfolios():
    """Renderiza la pestaña de comparación de carteras."""
    st.markdown("<br>", unsafe_allow_html=True)

    # Renderizar inputs de carteras
    portfolios = render_portfolios_inputs()

    if not portfolios:
        st.info("Añade al menos una cartera con fondos y pesos (que sumen 100%) para ver la gráfica.")
        return

    # Obtener fechas de inicio de las carteras
    portfolios_start_dates = [p["portfolio_start_date"] for p in portfolios]

    st.markdown("<br>", unsafe_allow_html=True)

    # Selector de fecha y alineamiento
    start_date_portfolios = render_portfolios_date_selector("portfolios", portfolios_start_dates)

    st.markdown("<br>", unsafe_allow_html=True)

    # Obtener datos de carteras
    portfolios_info = get_portfolios_for_comparison(
        portfolios,  # lista de dicts con isins, pesos y fecha de comienzo
        start_date_portfolios  # fecha de comienzo común
    )

    if not portfolios_info:
        st.warning("No se pudieron cargar datos de ninguna cartera.")
        return

    # Generar y mostrar gráfica
    fig = plot_portfolios(portfolios_info, start_date_portfolios)
    st.plotly_chart(fig, width='stretch')

    # Convertir el gráfico a HTML y ofrecer descarga
    html_bytes = fig.to_html(include_plotlyjs='cdn')
    st.download_button(
        label="Descargar gráfico",
        data=html_bytes,
        file_name="comparador_cartera_fondos.html",
        mime="text/html"
    )