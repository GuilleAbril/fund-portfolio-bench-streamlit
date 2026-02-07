"""
Módulo para generar gráficas de comparación de fondos y carteras con Plotly.
"""

import plotly.graph_objects as go
import pyarrow as pa
import  pyarrow.compute as pc
from typing import List, Dict, Optional


# ─────────────────────────────────────────────
# CONSTANTES DE ESTILO
# ─────────────────────────────────────────────
FUND_COLORS = [
    "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
    "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16"
]

PORTFOLIO_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]


# ─────────────────────────────────────────────
# APLICAR LAYOUT COMÚN
# ─────────────────────────────────────────────

def _apply_chart_layout(fig: go.Figure, title: str):
    """Aplica estilo común a las gráficas"""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(color="#e2e8f0", size=22),
            y=0.98,  # Ajustar posición vertical del título
            x=0.5,   # Centrar el título
            xanchor='center',
            yanchor='top'
        ),
        xaxis=dict(
            title=dict(text="Fecha", font=dict(color="#7a85a8")),
            tickfont=dict(color="#7a85a8"),
            gridcolor="#1a1d2e",
            zeroline=False,
            showspikes=True,
            spikemode="across+toaxis+marker",
            spikesnap="cursor",
            spikecolor="#7a85a8",
            spikethickness=1,
            spikedash="dot"
        ),
        yaxis=dict(
            title=dict(text="Rentabilidad", font=dict(color="#7a85a8")),
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
            font=dict(color="#e2e8f0", size=15)
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#1a1d2e", font_size=13),
        height=550,
        margin=dict(l=60, r=30, t=120, b=60)
    )


# ─────────────────────────────────────────────
# GRÁFICA DE FONDOS
# ─────────────────────────────────────────────

def plot_funds(
        funds_info: List[Dict],
        start_date: Optional[str] = None
) -> go.Figure:
    """
    Crea gráfica de comparación de fondos.

    Args:
        funds_info: Lista de fondos con 'name': str, 'dates': str, 'funds_data': pa.Table
        start_date: Fecha de inicio (para el título)

    Returns:
        Figura de Plotly
    """
    fig = go.Figure()

    for idx, fund in enumerate(funds_info):
        label = fund.get('name', fund.get('isin', f'Fondo {idx+1}'))
        cagr_str = f"{fund.get('cagr'):.2%}"
        fund_data = fund.get('fund_data')
        profitability = pc.subtract(fund_data['total_return'], 100)

        fig.add_trace(go.Scatter(
            x=fund_data['date'].to_pylist(),
            y=profitability.to_pylist(),
            mode='lines',
            name=label + f" (CAGR: {cagr_str})",
            line=dict(
                width=2,
                color=FUND_COLORS[idx % len(FUND_COLORS)]
            ),
            hovertemplate=f"<b>{label}</b><br>"
                          f"Rentabilidad: %{{y:.2f}}%<br>"
                          f"Rentabilidad anualizada total: <b>{cagr_str}</b><extra></extra>"
        ))

    # Título dinámico (más corto y sin "Base 100")
    if start_date:
        title = f"Comparativa desde {start_date}"
    else:
        title = "Comparativa de fondos desde el histórico de cada uno"

    _apply_chart_layout(fig, title)

    # Configurar hover mode con spike para mostrar la fecha abajo
    fig.update_layout(
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1a1d2e",
            font_size=13,
            font_color="#e2e8f0"
        )
    )

    # Añadir spike line vertical y configuración para mostrar fecha en eje X
    fig.update_xaxes(
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikecolor="#7a85a8",
        spikethickness=1,
        spikedash="dot",
        showline=True,
        showgrid=True,
        hoverformat="%Y-%m-%d"
    )

    fig.update_yaxes(
        showspikes=False
    )

    return fig


# ─────────────────────────────────────────────
# GRÁFICA DE CARTERAS
# ─────────────────────────────────────────────

def plot_portfolios(
        portfolios_info:  list[dict[str, pa.Table]],
        start_date: Optional[str] = None
) -> go.Figure:
    """
    Crea gráfica de comparación de carteras.

    Args:
        portfolios_info: Lista de carteras con 'name', 'dates', 'values', 'common_start'
        start_date: Fecha de inicio (para el título)

    Returns:
        Figura de Plotly
    """
    fig = go.Figure()

    for idx, portfolio in enumerate(portfolios_info):
        cagr_str = f"{portfolio.get('cagr'):.2%}"
        print(portfolio['name'])
        print(portfolio.get("portfolio_total_return"))
        profitability = pc.subtract(portfolio.get("portfolio_total_return")['total_return'], 100)
        print("last values")
        print(profitability.to_pylist()[-100:])
        fig.add_trace(go.Scatter(
            x=portfolio.get("portfolio_total_return")['date'].to_pylist(),
            y=profitability.to_pylist(),
            mode='lines',
            name=portfolio['name']  + f" (CAGR: {cagr_str})",
            line=dict(
                width=2.5,
                color=PORTFOLIO_COLORS[idx % len(PORTFOLIO_COLORS)]
            ),
            hovertemplate=f"<b>{portfolio['name']}</b><br>"
                          f"Rentabilidad: %{{y:.2f}}%<br>"
                          f"Rentabilidad anualizada total: <b>{cagr_str}</b><extra></extra>"
        ))

    # Título dinámico
    if start_date:
        title = f"Comparativa de Carteras desde {start_date}"
    else:
        title = "Comparativa de Carteras desde el histórico de cada una"

    _apply_chart_layout(fig, title)

    # Configurar hover mode con spike para mostrar la fecha abajo
    fig.update_layout(
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1a1d2e",
            font_size=13,
            font_color="#e2e8f0"
        )
    )

    # Añadir spike line vertical y configuración para mostrar fecha en eje X
    fig.update_xaxes(
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikecolor="#7a85a8",
        spikethickness=1,
        spikedash="dot",
        showline=True,
        showgrid=True,
        hoverformat="%Y-%m-%d"
    )

    fig.update_yaxes(
        showspikes=False
    )

    return fig