"""
Componentes de interfaz de usuario para la gestión de fondos.
"""
import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

import streamlit as st
from datetime import datetime
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

    # Inicializar session_state para guardar la última fecha personalizada
    session_key = f"{prefix}_last_custom_date"
    if session_key not in st.session_state:
        st.session_state[session_key] = min_start_date

    # Radio buttons horizontales
    date_mode = st.radio(
        "Fecha de inicio de comparación:",
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

        if isinstance(default_value, str):
            default_value = datetime.strptime(default_value, '%Y-%m-%d').date()

        start_date = st.date_input(
            "Fecha desde",
            value=default_value,
            min_value=min_date,
            max_value=today,
            key=f"{prefix}_start_date"
        ).strftime('%Y-%m-%d')

    else:  # "Usar fecha de inicio común"
        start_date = get_max_common_start_date(isins)

    # Actualizar session_state
    if start_date:
        st.session_state[session_key] = start_date
    else:
        st.session_state[session_key] = min_start_date

    return start_date