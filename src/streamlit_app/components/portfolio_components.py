"""
Componentes de interfaz de usuario para la gestión de carteras.
"""
import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional

from compare_funds.compare_funds import get_funds_metadata, fund_exists
from streamlit_app.config import MAX_FUNDS, MAX_PORTFOLIOS, PORTFOLIO_COLORS
from streamlit_app.utils.database_utils import get_max_common_start_date


def render_portfolios_inputs() -> List[Dict]:
    """
    Renderiza cajas de carteras y retorna lista de carteras válidas.

    Returns:
        Lista de diccionarios con información de cada cartera:
        {
            'name': str,
            'funds': List[{'isin': str, 'weight': float, 'name': str}],
            'portfolio_start_date': str,
            'color': str
        }
    """
    portfolios = []

    # Estado para controlar cuántos fondos tiene cada cartera
    if "portfolio_fund_counts" not in st.session_state:
        st.session_state.portfolio_fund_counts = [1] * MAX_PORTFOLIOS

    cols = st.columns(MAX_PORTFOLIOS)

    for p_idx in range(MAX_PORTFOLIOS):
        col = cols[p_idx]

        # Input para el nombre de la cartera
        portfolio_name = col.text_input(
            "Nombre de la cartera",
            value=f"Cartera {p_idx + 1}",
            key=f"portfolio_{p_idx}_name",
            placeholder="Nombre personalizado"
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

        for f_idx in range(num_funds):
            input_cols = col.columns([2, 1])

            isin = input_cols[0].text_input(
                "ISIN",
                placeholder=f"ISIN fondo {f_idx + 1}",
                key=f"portfolio_{p_idx}_isin_{f_idx}",
                max_chars=12,
                label_visibility="visible" if f_idx == 0 else "hidden"
            ).strip().upper()

            weight = input_cols[1].number_input(
                "Peso %",
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                value=0.0,
                key=f"portfolio_{p_idx}_weight_{f_idx}",
                label_visibility="visible" if f_idx == 0 else "hidden"
            )

            if isin:
                if fund_exists(isin):
                    metadata = get_funds_metadata([isin])
                    name = metadata.get(isin, {}).get('name', isin)
                    col.markdown(
                        f'<div class="status-ok">✓ {name}</div>',
                        unsafe_allow_html=True
                    )
                    funds.append({'isin': isin, 'weight': weight, 'name': name})
                    portfolio_isins.append(isin)
                    total_weight += weight
                else:
                    col.markdown(
                        f'<div class="status-error">✗ {isin}</div>',
                        unsafe_allow_html=True
                    )

        # Indicador de peso total
        _render_weight_indicator(col, total_weight)

        # Botón añadir fondo
        if num_funds < MAX_FUNDS:
            if col.button("+ Añadir fondo", key=f"add_fund_{p_idx}"):
                st.session_state.portfolio_fund_counts[p_idx] += 1
                st.rerun()

        col.markdown('</div>', unsafe_allow_html=True)

        # Añadir cartera a la lista si es válida
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
    Renderiza el indicador de peso total de una cartera.

    Args:
        col: Columna de Streamlit donde renderizar
        total_weight: Peso total de la cartera
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
            f'{symbol} Peso total: {total_weight:.1f}%</div>',
            unsafe_allow_html=True
        )


def render_portfolios_date_selector(prefix: str, portfolios_start_dates: Optional[List[str]]) -> Optional[str]:
    """
    Renderiza selector de fecha y tipo de alineamiento para carteras.

    Args:
        prefix: Prefijo para las keys de los componentes
        portfolios_start_dates: Lista de fechas de inicio de las carteras

    Returns:
        Fecha de inicio seleccionada en formato 'YYYY-MM-DD' o None
    """
    min_start_date = ""
    if portfolios_start_dates:
        min_start_date = min(portfolios_start_dates)

    # Inicializar session_state para guardar la última fecha personalizada
    session_key = f"{prefix}_last_custom_date"
    if session_key not in st.session_state:
        st.session_state[session_key] = min_start_date

    # Radio buttons horizontales
    date_mode = st.radio(
        "Rango de fechas:",
        options=["Histórico completo", "Usar fecha de inicio común", "Fecha personalizada"],
        index=1,  # Por defecto "Usar fecha de inicio común"
        key=f"{prefix}_date_mode",
        horizontal=True
    )

    if date_mode == "Histórico completo":
        start_date = None

    elif date_mode == "Fecha personalizada":
        min_date = (datetime.strptime(min_start_date, '%Y-%m-%d').date()
                    if min_start_date else datetime(1990, 1, 1).date())
        today = datetime.now().date()
        default_value = st.session_state[session_key]

        start_date = st.date_input(
            "Fecha desde",
            value=default_value,
            min_value=min_date,
            max_value=today,
            key=f"{prefix}_start_date"
        ).strftime('%Y-%m-%d')

    else:  # "Usar fecha de inicio común"
        if portfolios_start_dates:
            start_date = max(portfolios_start_dates)
        else:
            start_date = None

    # Actualizar session_state
    if start_date:
        st.session_state[session_key] = start_date
    else:
        st.session_state[session_key] = min_start_date

    return start_date