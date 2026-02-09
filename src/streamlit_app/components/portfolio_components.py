"""
Componentes de interfaz de usuario para la gestión de carteras.
"""
import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

import streamlit as st
from datetime import datetime, timedelta
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


def _calculate_date_from_period(period: str, min_start_date: str) -> str:
    """
    Calcula la fecha de inicio basada en el período seleccionado.

    Args:
        period: Período seleccionado (YTD, 1A, 3A, 5A)
        min_start_date: Fecha mínima disponible

    Returns:
        Fecha en formato 'YYYY-MM-DD'
    """
    today = datetime.now().date()

    if period == "YTD":
        start_date = datetime(today.year, 1, 1).date()
    elif period == "1A":
        start_date = today - timedelta(days=365)
    elif period == "3A":
        start_date = today - timedelta(days=365 * 3)
    elif period == "5A":
        start_date = today - timedelta(days=365 * 5)
    else:
        start_date = today

    if min_start_date:
        min_date = datetime.strptime(min_start_date, '%Y-%m-%d').date()
        if start_date < min_date:
            start_date = min_date

    return start_date.strftime('%Y-%m-%d')


def render_portfolios_date_selector(prefix: str, portfolios_start_dates: Optional[List[str]], portfolios_structure: List[Dict]) -> Optional[str]:
    """
    Renderiza selector de fecha y tipo de alineamiento para carteras.

    Args:
        prefix: Prefijo para las keys de los componentes
        portfolios_start_dates: Lista de fechas de inicio de las carteras
        portfolios_structure: Estructura actual de las carteras para detectar cambios

    Returns:
        Fecha de inicio seleccionada en formato 'YYYY-MM-DD' o None
    """
    # Calcular fecha mínima global (la fecha más antigua posible entre todas las carteras)
    # y fecha común global (la fecha más reciente entre los inicios de todas las carteras)
    min_start_date = None
    common_start_date_str = None

    if portfolios_start_dates:
        # La fecha común válida para todos es el MAX de los inicios
        common_start_date_str = max(portfolios_start_dates)
        
        # Para el "Histórico completo", queremos ver desde el principio de los tiempos de la cartera más antigua
        # o al menos dar la opción de retroceder.
        min_start_date = min(portfolios_start_dates)

    # Inicializar session_state
    session_key_mode = f"{prefix}_date_selection"
    session_key_range = f"{prefix}_date_range"
    session_key_counter = f"{prefix}_date_counter"
    session_key_last_structure = f"{prefix}_last_structure"

    # Detectar cambios en la estructura de las carteras
    # Usamos una representación string o hashable de la estructura relevante (funds + weights)
    current_structure_repr = str([{p['name']: p['funds']} for p in portfolios_structure])
    
    structure_changed = False
    if session_key_last_structure not in st.session_state:
        st.session_state[session_key_last_structure] = ""
        structure_changed = True
    elif st.session_state[session_key_last_structure] != current_structure_repr:
        structure_changed = True

    # Si cambió la estructura, resetear a fecha común
    if structure_changed:
        st.session_state[session_key_last_structure] = current_structure_repr
        st.session_state[session_key_mode] = "Usar fecha de inicio común"
        
        common_date = datetime.strptime(common_start_date_str, '%Y-%m-%d').date() if common_start_date_str else datetime.now().date()
        st.session_state[session_key_range] = (common_date, datetime.now().date())
        
        if session_key_counter not in st.session_state:
            st.session_state[session_key_counter] = 0
        else:
            st.session_state[session_key_counter] += 1

    if session_key_mode not in st.session_state:
        st.session_state[session_key_mode] = "Usar fecha de inicio común"
    if session_key_range not in st.session_state:
        # Default a fecha común si existen datos
        start_d = common_start_date_str if common_start_date_str else (min_start_date if min_start_date else None)
        common_date = datetime.strptime(start_d, '%Y-%m-%d').date() if start_d else datetime.now().date()
        st.session_state[session_key_range] = (common_date, datetime.now().date())
    if session_key_counter not in st.session_state:
        st.session_state[session_key_counter] = 0

    st.markdown("**Fecha de inicio de comparación:**")

    cols = st.columns([2, 2.5, 0.8, 0.8, 0.8, 0.8, 4])

    # Botón "Histórico completo": permite ver desde el inicio de la cartera más antigua
    if cols[0].button("Histórico completo", key=f"{prefix}_btn_historico", use_container_width=True):
        st.session_state[session_key_mode] = "Histórico completo"
        min_date = (datetime.strptime(min_start_date, '%Y-%m-%d').date()
                    if min_start_date else datetime(1990, 1, 1).date())
        st.session_state[session_key_range] = (min_date, datetime.now().date())
        st.session_state[session_key_counter] += 1
        st.rerun()

    # Botón "Usar fecha de inicio común"
    if cols[1].button("Usar fecha de inicio común", key=f"{prefix}_btn_comun", use_container_width=True):
        st.session_state[session_key_mode] = "Usar fecha de inicio común"
        common_date = datetime.strptime(common_start_date_str, '%Y-%m-%d').date() if common_start_date_str else datetime.now().date()
        st.session_state[session_key_range] = (common_date, datetime.now().date())
        st.session_state[session_key_counter] += 1
        st.rerun()

    # Botones de período
    period_buttons = ["YTD", "1A", "3A", "5A"]
    for i, period in enumerate(period_buttons):
        if cols[i + 2].button(period, key=f"{prefix}_btn_{period}", use_container_width=True):
            st.session_state[session_key_mode] = period
            calculated_start = _calculate_date_from_period(period, min_start_date)
            st.session_state[session_key_range] = (
                datetime.strptime(calculated_start, '%Y-%m-%d').date(),
                datetime.now().date()
            )
            st.session_state[session_key_counter] += 1
            st.rerun()

    # Indicador
    current_mode = st.session_state[session_key_mode]
    if current_mode in ["Histórico completo", "Usar fecha de inicio común"]:
        st.info(f"📅 Seleccionado: **{current_mode}**")
    else:
        st.info(f"📅 Período seleccionado: **{current_mode}**")

    # Selectores de fecha manuales
    # La fecha mínima permitida en el selector debe ser la mínima global (para permitir retroceder)
    min_date_obj = (datetime.strptime(min_start_date, '%Y-%m-%d').date()
                if min_start_date else datetime(1990, 1, 1).date())
    today = datetime.now().date()

    col1, col2 = st.columns(2)
    counter = st.session_state[session_key_counter]

    with col1:
        start_date_input = st.date_input(
            "Fecha desde",
            value=st.session_state[session_key_range][0],
            min_value=min_date_obj,
            max_value=today,
            key=f"{prefix}_custom_start_date_{counter}"
        )

    with col2:
        end_date_input = st.date_input(
            "Fecha hasta",
            value=st.session_state[session_key_range][1],
            min_value=min_date_obj,
            max_value=today,
            key=f"{prefix}_custom_end_date_{counter}"
        )

    st.session_state[session_key_range] = (start_date_input, end_date_input)
    
    return start_date_input.strftime('%Y-%m-%d')