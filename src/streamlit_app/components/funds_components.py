"""
Componentes de interfaz de usuario para la gestión de fondos.
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


def render_funds_inputs(prefix: str, num_funds: int = MAX_FUNDS) -> List[str]:
    """
    Renderiza cajas de entrada de ISINs y retorna lista de ISINs válidos.

    Args:
        prefix: Prefijo para las keys de los componentes
        num_funds: Número máximo de fondos a mostrar

    Returns:
        Lista de ISINs válidos
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
                # Obtener nombre del fondo
                metadata = get_funds_metadata([isin])
                name = metadata.get(isin, {}).get('name', isin)
                col.markdown(
                    f'<div class="status-ok">✓ {name}</div>',
                    unsafe_allow_html=True
                )
                isins.append(isin)
            else:
                col.markdown(
                    f'<div class="status-error">✗ {isin} no encontrado</div>',
                    unsafe_allow_html=True
                )

    return isins


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
        # Desde el 1 de enero del año actual
        start_date = datetime(today.year, 1, 1).date()
    elif period == "1A":
        start_date = today - timedelta(days=365)
    elif period == "3A":
        start_date = today - timedelta(days=365 * 3)
    elif period == "5A":
        start_date = today - timedelta(days=365 * 5)
    else:
        start_date = today

    # Asegurar que no sea anterior a la fecha mínima disponible
    if min_start_date:
        min_date = datetime.strptime(min_start_date, '%Y-%m-%d').date()
        if start_date < min_date:
            start_date = min_date

    return start_date.strftime('%Y-%m-%d')


def render_funds_date_selector(prefix: str, isins: List[str]) -> Optional[str]:
    """
    Renderiza selector de fecha y tipo de alineamiento para fondos.

    Args:
        prefix: Prefijo para las keys de los componentes
        isins: Lista de ISINs

    Returns:
        Fecha de inicio seleccionada en formato 'YYYY-MM-DD' o None
    """
    min_start_date = get_min_start_date(isins)

    # Inicializar session_state
    session_key_mode = f"{prefix}_date_selection"
    session_key_range = f"{prefix}_date_range"
    session_key_counter = f"{prefix}_date_counter"
    session_key_last_isins = f"{prefix}_last_isins"

    # Detectar cambios en los fondos
    funds_changed = False
    if session_key_last_isins not in st.session_state:
        st.session_state[session_key_last_isins] = []
        funds_changed = True
    elif st.session_state[session_key_last_isins] != isins:
        funds_changed = True

    # Si cambiaron los fondos, resetear a fecha común
    if funds_changed:
        st.session_state[session_key_last_isins] = list(isins)
        st.session_state[session_key_mode] = "Usar fecha de inicio común"
        
        # Calcular fecha común
        common_date_str = get_max_common_start_date(isins)
        common_date = datetime.strptime(common_date_str, '%Y-%m-%d').date() if common_date_str else datetime.now().date()
        
        st.session_state[session_key_range] = (common_date, datetime.now().date())
        
        # Incrementar contador si existe, sino inicializar
        if session_key_counter not in st.session_state:
            st.session_state[session_key_counter] = 0
        else:
            st.session_state[session_key_counter] += 1

    # Asegurar que las keys existen (por si acaso no entró en el if anterior, aunque debería estar cubierto)
    if session_key_mode not in st.session_state:
        st.session_state[session_key_mode] = "Usar fecha de inicio común"
    if session_key_range not in st.session_state:
        # Fallback por seguridad
        common_date_str = get_max_common_start_date(isins)
        common_date = datetime.strptime(common_date_str, '%Y-%m-%d').date() if common_date_str else datetime.now().date()
        st.session_state[session_key_range] = (common_date, datetime.now().date())
    if session_key_counter not in st.session_state:
        st.session_state[session_key_counter] = 0

    # Una sola fila con todos los botones
    st.markdown("**Fecha de inicio de comparación:**")

    cols = st.columns([2, 2.5, 0.8, 0.8, 0.8, 0.8, 4])

    # Botón "Histórico completo"
    if cols[0].button("Histórico completo", key=f"{prefix}_btn_historico", use_container_width=True):
        st.session_state[session_key_mode] = "Histórico completo"
        # Establecer rango desde la fecha mínima hasta hoy
        min_date = (datetime.strptime(min_start_date, '%Y-%m-%d').date()
                    if min_start_date else datetime(1990, 1, 1).date())
        st.session_state[session_key_range] = (min_date, datetime.now().date())
        st.session_state[session_key_counter] += 1
        st.rerun()

    # Botón "Usar fecha de inicio común"
    if cols[1].button("Usar fecha de inicio común", key=f"{prefix}_btn_comun", use_container_width=True):
        st.session_state[session_key_mode] = "Usar fecha de inicio común"
        # Establecer rango desde la fecha común hasta hoy
        common_date_str = get_max_common_start_date(isins)
        common_date = datetime.strptime(common_date_str, '%Y-%m-%d').date() if common_date_str else datetime.now().date()
        st.session_state[session_key_range] = (common_date, datetime.now().date())
        st.session_state[session_key_counter] += 1
        st.rerun()

    # Botones de período rápido
    period_buttons = ["YTD", "1A", "3A", "5A"]
    for i, period in enumerate(period_buttons):
        if cols[i + 2].button(period, key=f"{prefix}_btn_{period}", use_container_width=True):
            st.session_state[session_key_mode] = period
            # Calcular y guardar las fechas automáticamente
            calculated_start = _calculate_date_from_period(period, min_start_date)
            st.session_state[session_key_range] = (
                datetime.strptime(calculated_start, '%Y-%m-%d').date(),
                datetime.now().date()
            )
            st.session_state[session_key_counter] += 1
            st.rerun()

    # Mostrar indicador visual de qué está seleccionado
    current_mode = st.session_state[session_key_mode]
    if current_mode in ["Histórico completo", "Usar fecha de inicio común"]:
        st.info(f"📅 Seleccionado: **{current_mode}**")
    else:
        st.info(f"📅 Período seleccionado: **{current_mode}**")

    # Selector de rango de fechas (SIEMPRE VISIBLE)
    min_date = (datetime.strptime(min_start_date, '%Y-%m-%d').date()
                if min_start_date else datetime(1990, 1, 1).date())
    today = datetime.now().date()

    col1, col2 = st.columns(2)

    # Usar el contador en las keys para forzar re-renderizado
    counter = st.session_state[session_key_counter]

    with col1:
        start_date_input = st.date_input(
            "Fecha desde",
            value=st.session_state[session_key_range][0],
            min_value=min_date,
            max_value=today,
            key=f"{prefix}_custom_start_date_{counter}"
        )

    with col2:
        end_date_input = st.date_input(
            "Fecha hasta",
            value=st.session_state[session_key_range][1],
            min_value=min_date,
            max_value=today,
            key=f"{prefix}_custom_end_date_{counter}"
        )

    # Actualizar el rango en session_state
    st.session_state[session_key_range] = (start_date_input, end_date_input)

    # Retornar la fecha de inicio
    start_date = start_date_input.strftime('%Y-%m-%d')

    return start_date
