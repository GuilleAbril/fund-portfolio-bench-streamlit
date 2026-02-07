import streamlit as st
import pyarrow.parquet as pq
import pyarrow.compute as pc
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG & STYLING
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Fund Comparator",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Fondo general */
    .stApp {
        background-color: #0f1117;
        color: #e2e8f0;
        font-family: 'Segoe UI', sans-serif;
    }

    /* Pestañas principales */
    .stTabs [data-baseid="tablist"] {
        gap: 10px;
    }
    .stTabs [role="tab"] {
        background: #1a1d2e;
        border: 1px solid #2a2f4a;
        color: #7a85a8;
        border-radius: 8px;
        padding: 10px 24px;
        font-size: 15px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stTabs [role="tab"][aria-selected="true"] {
        background: #3b82f6;
        border-color: #3b82f6;
        color: #fff;
    }
    .stTabs [role="tab"]:hover {
        border-color: #3b82f6;
        color: #fff;
    }

    /* Cajas de entrada ISIN */
    .stTextInput input {
        background: #1a1d2e;
        border: 1px solid #2a2f4a;
        color: #e2e8f0;
        border-radius: 6px;
        padding: 8px 12px;
    }
    .stTextInput input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
    }
    .stTextInput label {
        color: #7a85a8;
        font-size: 13px;
        font-weight: 600;
    }

    /* Selector de fecha */
    .stDateInput input {
        background: #1a1d2e;
        border: 1px solid #2a2f4a;
        color: #e2e8f0;
        border-radius: 6px;
    }

    /* Cajas de peso % */
    .stNumberInput input {
        background: #1a1d2e;
        border: 1px solid #2a2f4a;
        color: #e2e8f0;
        border-radius: 6px;
    }

    /* Contenedor cartera */
    .portfolio-card {
        background: #1a1d2e;
        border: 1px solid #2a2f4a;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .portfolio-card-header {
        color: #3b82f6;
        font-weight: 700;
        font-size: 15px;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #2a2f4a;
    }

    /* Botón añadir fondo */
    .stButton button {
        background: transparent;
        border: 1px dashed #2a2f4a;
        color: #7a85a8;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s;
        width: 100%;
    }
    .stButton button:hover {
        border-color: #3b82f6;
        color: #3b82f6;
    }

    /* Indicador de peso total */
    .weight-indicator {
        font-size: 13px;
        font-weight: 600;
        text-align: right;
        padding: 4px 0;
    }
    .weight-ok { color: #22c55e; }
    .weight-warning { color: #f59e0b; }
    .weight-error { color: #ef4444; }

    /* Mensajes de estado */
    .status-ok {
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.3);
        color: #22c55e;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 12px;
    }
    .status-error {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #ef4444;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 12px;
    }

    /* Ocultar menu de Streamlit */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FUNCIONES DE DATOS (PyArrow)
# ─────────────────────────────────────────────
DATA_DIR = Path("/download_data/data")
MAX_FUNDS = 10
MAX_PORTFOLIOS = 5
PORTFOLIO_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]
FUND_COLORS = [
    "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
    "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16"
]


def fund_exists(isin: str) -> bool:
    """Comprueba si el parquet del fondo existe"""
    return (DATA_DIR / f"{isin}.parquet").exists()


def load_fund_raw(isin: str, start_date: str = None) -> dict | None:
    """
    Carga datos RAW del fondo desde parquet con PyArrow (sin normalizar).
    Retorna dict con 'dates' y 'values', o None si falla.
    """
    filepath = DATA_DIR / f"{isin}.parquet"
    if not filepath.exists():
        return None

    try:
        table = pq.read_table(filepath)

        # Filtrar por fecha si se proporciona
        if start_date:
            mask = pc.greater_equal(table['date'], start_date)
            table = table.filter(mask)

        if len(table) == 0:
            return None

        return {
            'dates': table['date'].to_pylist(),
            'values': table['totalReturn'].to_pylist()
        }
    except Exception as e:
        st.error(f"Error cargando {isin}: {e}")
        return None


def normalize_to_base_100(values: list[float]) -> list[float]:
    """Normaliza una lista de valores a base 100 desde el primer elemento"""
    if not values or values[0] == 0:
        return values
    first = values[0]
    return [(v / first) * 100.0 for v in values]


def align_funds(funds_data: list[dict]) -> list[dict]:
    """
    Alinea múltiples fondos a la fecha común más tardía.
    Entrada:  [{'dates': [...], 'values': [...], ...}, ...]
    Salida:   misma estructura pero todos desde la misma fecha común,
              con valores normalizados a base 100 desde esa fecha.
    """
    if not funds_data:
        return []

    # Encontrar la fecha más tardía entre todos los fondos (fecha común)
    common_start = max(fd['dates'][0] for fd in funds_data)

    aligned = []
    for fd in funds_data:
        # Buscar el índice de la fecha común en este fondo
        try:
            # Encontrar la primera fecha >= common_start
            start_idx = next(
                i for i, date in enumerate(fd['dates'])
                if date >= common_start
            )
        except StopIteration:
            # Este fondo no tiene datos desde la fecha común, se descarta
            continue

        # Recortar fechas y valores desde el índice encontrado
        dates_aligned = fd['dates'][start_idx:]
        values_aligned = fd['values'][start_idx:]

        # Normalizar a base 100 desde la fecha común
        values_normalized = normalize_to_base_100(values_aligned)

        aligned.append({
            **fd,  # Preserva campos extra como 'weight', 'isin', etc.
            'dates': dates_aligned,
            'values': values_normalized
        })

    return aligned


def get_earliest_date() -> str | None:
    """Obtiene la fecha más antigua disponible en metadata"""
    metadata_path = DATA_DIR / "metadata_funds.parquet"
    if not metadata_path.exists():
        return None
    try:
        table = pq.read_table(metadata_path)
        return pc.min(table['first_date']).as_py()
    except:
        return None


# ─────────────────────────────────────────────
# COMPONENTES DE UI
# ─────────────────────────────────────────────
def render_fund_inputs(prefix: str, num_funds: int = MAX_FUNDS) -> list[str]:
    """Renderiza las cajas de entrada de ISINs y retorna lista de ISINs válidos"""
    isins = []
    cols = st.columns(2)  # 2 columnas para compactar

    for i in range(num_funds):
        col = cols[i % 2]
        isin = col.text_input(
            f"Fondo {i + 1}",
            placeholder="Ej: ES0175835000",
            key=f"{prefix}_isin_{i}",
            max_chars=12
        ).strip().upper()

        if isin:
            if fund_exists(isin):
                col.markdown(f'<div class="status-ok">✓ {isin} encontrado</div>', unsafe_allow_html=True)
                isins.append(isin)
            else:
                col.markdown(f'<div class="status-error">✗ {isin} no encontrado</div>', unsafe_allow_html=True)

    return isins


def render_date_selector(prefix: str) -> str | None:
    """Renderiza el selector de fecha de inicio. Retorna fecha como string o None (histórico completo)"""
    earliest = get_earliest_date()

    col1, col2 = st.columns([1, 3])

    use_full_history = col1.checkbox(
        "Histórico completo",
        value=True,
        key=f"{prefix}_full_history"
    )

    if use_full_history:
        return None  # Sin filtro de fecha
    else:
        min_date = datetime.strptime(earliest, '%Y-%m-%d').date() if earliest else datetime(2000, 1, 1).date()
        today = datetime.now().date()
        selected_date = col2.date_input(
            "Fecha desde",
            value=min_date,
            min_value=min_date,
            max_value=today,
            key=f"{prefix}_start_date"
        )
        return selected_date.strftime('%Y-%m-%d')


def render_portfolio_inputs() -> list[dict]:
    """
    Renderiza las cajas de carteras.
    Retorna lista de dicts: [{'name': 'Cartera 1', 'funds': [{'isin': '...', 'weight': 50.0}, ...]}, ...]
    """
    portfolios = []

    # Estado para controlar cuántos fondos tiene cada cartera
    if "portfolio_fund_counts" not in st.session_state:
        st.session_state.portfolio_fund_counts = [1] * MAX_PORTFOLIOS

    cols = st.columns(MAX_PORTFOLIOS)

    for p_idx in range(MAX_PORTFOLIOS):
        col = cols[p_idx]

        col.markdown(
            f'<div class="portfolio-card">'
            f'<div class="portfolio-card-header" style="color:{PORTFOLIO_COLORS[p_idx]}">'
            f'Cartera {p_idx + 1}</div>',
            unsafe_allow_html=True
        )

        funds = []
        num_funds = st.session_state.portfolio_fund_counts[p_idx]
        total_weight = 0.0

        for f_idx in range(num_funds):
            # Fila con ISIN y peso
            input_cols = col.columns([2, 1])

            isin = input_cols[0].text_input(
                "ISIN" if f_idx == 0 else "",
                placeholder=f"ISIN fondo {f_idx + 1}",
                key=f"portfolio_{p_idx}_isin_{f_idx}",
                max_chars=12,
                label_visibility="visible" if f_idx == 0 else "hidden"
            ).strip().upper()

            weight = input_cols[1].number_input(
                "%" if f_idx == 0 else "",
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                value=0.0,
                key=f"portfolio_{p_idx}_weight_{f_idx}",
                label_visibility="visible" if f_idx == 0 else "hidden"
            )

            if isin:
                if fund_exists(isin):
                    funds.append({'isin': isin, 'weight': weight})
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

        if funds:
            portfolios.append({
                'name': f'Cartera {p_idx + 1}',
                'funds': funds,
                'color': PORTFOLIO_COLORS[p_idx]
            })

    return portfolios


# ─────────────────────────────────────────────
# GRÁFICAS (Plotly)
# ─────────────────────────────────────────────
def render_funds_chart(isins: list[str], start_date: str | None):
    """Renderiza gráfica de comparación de fondos individuales"""
    if not isins:
        st.info("Añade al menos un fondo para ver la gráfica.")
        return

    # Cargar datos raw de todos los fondos
    funds_raw = []
    for isin in isins:
        data = load_fund_raw(isin, start_date)
        if data:
            funds_raw.append({**data, 'isin': isin})

    if not funds_raw:
        st.warning("No se pudieron cargar datos de ningún fondo.")
        return

    # Alinear fechas y normalizar
    funds_aligned = align_funds(funds_raw)

    if not funds_aligned:
        st.warning("No hay fechas comunes entre los fondos seleccionados.")
        return

    # Mostrar info de la fecha común
    common_start = funds_aligned[0]['dates'][0]
    st.caption(f"📅 Datos alineados desde la fecha común: **{common_start}**")

    # Graficar
    fig = go.Figure()

    for idx, fd in enumerate(funds_aligned):
        fig.add_trace(go.Scatter(
            x=fd['dates'],
            y=fd['values'],
            mode='lines',
            name=fd['isin'],
            line=dict(
                width=2,
                color=FUND_COLORS[idx % len(FUND_COLORS)]
            ),
            hovertemplate=f"<b>{fd['isin']}</b><br>Fecha: %{{x}}<br>Valor: %{{y:.2f}}<extra></extra>"
        ))

    _apply_chart_layout(fig, start_date)
    st.plotly_chart(fig, width='stretch')


def render_portfolios_chart(portfolios: list[dict], start_date: str | None):
    """Renderiza gráfica de comparación de carteras"""
    if not portfolios:
        st.info("Añade al menos una cartera con fondos y pesos para ver la gráfica.")
        return

    # Validar que al menos una cartera tenga pesos = 100%
    valid_portfolios = []
    for p in portfolios:
        total = sum(f['weight'] for f in p['funds'])
        if abs(total - 100.0) < 0.01:
            valid_portfolios.append(p)

    if not valid_portfolios:
        st.warning("Los pesos de al menos una cartera deben sumar 100% para graficarla.")
        return

    fig = go.Figure()
    common_dates_info = []

    for portfolio in valid_portfolios:
        # Cargar datos raw de todos los fondos de la cartera
        funds_raw = []
        for fund in portfolio['funds']:
            data = load_fund_raw(fund['isin'], start_date)
            if data:
                funds_raw.append({
                    **data,
                    'isin': fund['isin'],
                    'weight': fund['weight'] / 100.0
                })

        if not funds_raw:
            continue

        # Alinear fechas dentro de la cartera (normaliza a base 100 desde fecha común)
        funds_aligned = align_funds(funds_raw)

        if not funds_aligned:
            st.warning(f"No hay fechas comunes en {portfolio['name']}.")
            continue

        # Encontrar la longitud mínima (por si hay pequeñas diferencias de trading days)
        min_len = min(len(fd['dates']) for fd in funds_aligned)
        reference_dates = funds_aligned[0]['dates'][:min_len]

        common_dates_info.append(f"{portfolio['name']}: desde **{reference_dates[0]}**")

        # Calcular valor ponderado de la cartera día a día
        portfolio_values = []
        for day_idx in range(min_len):
            weighted_value = sum(
                fd['values'][day_idx] * fd['weight']
                for fd in funds_aligned
            )
            portfolio_values.append(weighted_value)

        fig.add_trace(go.Scatter(
            x=reference_dates,
            y=portfolio_values,
            mode='lines',
            name=portfolio['name'],
            line=dict(
                width=2.5,
                color=portfolio['color']
            ),
            hovertemplate=f"<b>{portfolio['name']}</b><br>Fecha: %{{x}}<br>Valor: %{{y:.2f}}<extra></extra>"
        ))

    # Mostrar info de fechas comunes por cartera
    if common_dates_info:
        st.caption("📅 " + " | ".join(common_dates_info))

    _apply_chart_layout(fig, start_date)
    st.plotly_chart(fig, width='stretch')


def _apply_chart_layout(fig: go.Figure, start_date: str | None):
    """Aplica estilo común a las gráficas"""
    title = "Comparativa de Fondos (Base 100)" if not start_date else f"Comparativa desde {start_date} (Base 100)"

    fig.update_layout(
        title=dict(text=title, font=dict(color="#e2e8f0", size=18)),
        xaxis=dict(
            title=dict(text="Fecha", font=dict(color="#7a85a8")),
            tickfont=dict(color="#7a85a8"),
            gridcolor="#1a1d2e",
            zeroline=False
        ),
        yaxis=dict(
            title=dict(text="Valor (Base 100)", font=dict(color="#7a85a8")),
            tickfont=dict(color="#7a85a8"),
            gridcolor="#1a1d2e",
            zeroline=False
        ),
        plot_bgcolor="#0f1117",
        paper_bgcolor="#0f1117",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(color="#e2e8f0")
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#1a1d2e", font_size=13),
        height=550,
        margin=dict(l=60, r=30, t=80, b=60)
    )


# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
def main():
    # Título
    st.markdown("""
        <div style="text-align:center; padding: 30px 0 10px 0;">
            <h1 style="color:#e2e8f0; font-size:28px; font-weight:700; margin:0; letter-spacing:1px;">
                📈 FUND COMPARATOR
            </h1>
            <p style="color:#7a85a8; font-size:14px; margin-top:4px;">
                Compara fondos y carteras de inversión
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Pestañas principales
    tab_funds, tab_portfolios = st.tabs(["Comparar Fondos", "Comparar Carteras"])

    # ── PESTAÑA: COMPARAR FONDOS ──
    with tab_funds:
        st.markdown("<br>", unsafe_allow_html=True)

        # Cajas de entrada de ISINs
        isins = render_fund_inputs("funds")

        st.markdown("<br>", unsafe_allow_html=True)

        # Selector de fecha
        start_date = render_date_selector("funds")

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráfica
        render_funds_chart(isins, start_date)

    # ── PESTAÑA: COMPARAR CARTERAS ──
    with tab_portfolios:
        st.markdown("<br>", unsafe_allow_html=True)

        # Inputs de carteras
        portfolios = render_portfolio_inputs()

        st.markdown("<br>", unsafe_allow_html=True)

        # Selector de fecha
        start_date = render_date_selector("portfolios")

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráfica
        render_portfolios_chart(portfolios, start_date)


if __name__ == "__main__":
    main()