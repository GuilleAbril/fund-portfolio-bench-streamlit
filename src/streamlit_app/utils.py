import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional
import sqlite3

# Importar módulos propios
from compare_funds.compare_funds import (
    get_funds_metadata,
    fund_exists,
    get_funds_for_comparison,
    get_portfolios_for_comparison
)

from plot_funds.plot_funds import (
    plot_funds,
    plot_portfolios
)

# ─────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────

MAX_FUNDS = 10
MAX_PORTFOLIOS = 5
PORTFOLIO_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]
PROJECT_ROOT_PATH = Path(__file__).parent.parent.parent  # Sube desde src/compare_funds/
DATA_DIR_PATH = PROJECT_ROOT_PATH / "src" / "download_data" / "data"
METADATA_DB_PATH = DATA_DIR_PATH / "metadata_funds.db"

# ─────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ─────────────────────────────────────────────

def get_max_common_start_date(isins: list[str]) -> Optional[str]:
    """Obtiene la fecha más antigua disponible en metadata"""
    metadata_path = Path(METADATA_DB_PATH)
    if not metadata_path.exists():
        return None

    try:
        conn = sqlite3.connect(metadata_path)
        placeholders = ','.join('?' * len(isins))
        cursor = conn.execute(f'SELECT MAX(start_date) FROM funds WHERE isin IN ({placeholders})', isins)
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except:
        return None

def get_min_start_date(isins: list[str]) -> Optional[str]:

    metadata_path = Path(METADATA_DB_PATH)
    if not metadata_path.exists():
        return None
    try:
        conn = sqlite3.connect(metadata_path)
        placeholders = ','.join('?' * len(isins))
        cursor = conn.execute(f'SELECT min(start_date) FROM funds WHERE isin IN ({placeholders})', isins)
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except:
        return None


# ─────────────────────────────────────────────
# COMPONENTES DE UI - FONDOS
# ─────────────────────────────────────────────

def render_funds_inputs(prefix: str, num_funds: int = MAX_FUNDS) -> List[str]:
    """Renderiza cajas de entrada de ISINs y retorna lista de ISINs válidos"""
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
                col.markdown(f'<div class="status-ok">✓ {name}</div>', unsafe_allow_html=True)
                isins.append(isin)
            else:
                col.markdown(f'<div class="status-error">✗ {isin} no encontrado</div>', unsafe_allow_html=True)

    return isins


def render_funds_date_selector(prefix: str, isins: list[str]) -> Optional[str]:
    """
    Renderiza selector de fecha y tipo de alineamiento.

    Returns:
        start_date
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
        min_date = datetime.strptime(min_start_date, '%Y-%m-%d').date() if min_start_date else datetime(1990, 1, 1).date()
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

    if start_date:
        st.session_state[session_key] = start_date
    else:
        st.session_state[session_key] = min_start_date

    return start_date

# ─────────────────────────────────────────────
# COMPONENTES DE UI - CARTERAS
# ─────────────────────────────────────────────
def render_portfolios_inputs() -> List[Dict]:
    """
    Renderiza cajas de carteras y retorna lista de carteras válidas

    Returns:

        List of
         {
         'name': f'Cartera {p_idx + 1}',

         'funds': funds,

         'portfolio_start_date': portfolio_start_date,

         'color': PORTFOLIO_COLORS[p_idx]
         }

         Where funds is: List of {'isin': isin, 'weight': weight}
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
            f'Cartera {p_idx + 1}</div>',
            unsafe_allow_html=True       )

        funds = []
        num_funds = st.session_state.portfolio_fund_counts[p_idx]
        total_weight = 0.0

        portfolio_isins = []
        for f_idx in range(num_funds):
            input_cols = col.columns([2, 1])

            isin = input_cols[0].text_input(
                f"ISIN",
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
                    col.markdown(f'<div class="status-ok">✓ {name}</div>', unsafe_allow_html=True)
                    funds.append({'isin': isin, 'weight': weight, 'name': name})
                    portfolio_isins.append(isin)
                    total_weight += weight
                else:
                    col.markdown(f'<div class="status-error">✗ {isin}</div>', unsafe_allow_html=True)

        # Indicador de peso total
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
                f'<div class="weight-indicator {css_class}">{symbol} Peso total: {total_weight:.1f}%</div>',
                unsafe_allow_html=True
            )

        # Botón añadir fondo
        if num_funds < MAX_FUNDS:
            if col.button("+ Añadir fondo", key=f"add_fund_{p_idx}"):
                st.session_state.portfolio_fund_counts[p_idx] += 1
                st.rerun()

        col.markdown('</div>', unsafe_allow_html=True)

        if funds and abs(total_weight - 100.0) < 0.01:
            portfolio_start_date = get_max_common_start_date(portfolio_isins)
            portfolios.append({
                'name': portfolio_name,
                'funds': funds,
                'portfolio_start_date': portfolio_start_date,
                'color': PORTFOLIO_COLORS[p_idx]
            })

    return portfolios


def render_portfolios_date_selector(prefix: str, portfolios_start_dates: Optional[list[str]]) -> Optional[str]:
    """
    Renderiza selector de fecha y tipo de alineamiento.

    Returns:
        start_date
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
        min_date = datetime.strptime(min_start_date, '%Y-%m-%d').date() if min_start_date else datetime(1990, 1, 1).date()
        today = datetime.now().date()
        default_value = st.session_state[session_key]
        start_date = st.date_input(
            "Fecha desde",
            value=default_value,
            min_value=min_date,
            max_value=today,
            key=f"{prefix}_start_date"
        ).strftime('%Y-%m-%d')
    else:  # "Usar fecha de inicio común" TODO: repasar esta lógica y ponerla bien
        if portfolios_start_dates:
            start_date = max(portfolios_start_dates)
        else:
            start_date = None

    if start_date:
        st.session_state[session_key] = start_date
    else:
        st.session_state[session_key] = min_start_date

    return start_date
