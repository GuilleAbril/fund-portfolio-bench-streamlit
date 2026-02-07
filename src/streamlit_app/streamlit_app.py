"""
Aplicación Streamlit para comparar fondos y carteras de inversión.
"""
# Añadir el directorio src al PYTHONPATH

# TODO: Poner que se muestre igual el hovertemplate en carteras que fondos
#  comprobar el final date que no añada datos (en carteras por los pesos)
#  poner opción 1 año y 3 años con el botón y seleccionar fecha incio y fecha fin

import sys
from pathlib import Path


src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

import streamlit as st

# Importar módulos propios
from compare_funds.compare_funds import get_portfolios_for_comparison
from plot_funds.plot_funds import plot_portfolios
from utils import render_portfolios_date_selector, render_portfolios_inputs
from tab_funds import render_tab_funds

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE STREAMLIT
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Fund Comparator",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ─────────────────────────────────────────────
# ESTILOS CSS
# ─────────────────────────────────────────────

st.markdown("""
<style>
    .stApp {
        background-color: #0f1117;
        color: #e2e8f0;
        font-family: 'Segoe UI', sans-serif;
    }

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
        box-shadow: none;
    }
    .stTabs [role="tab"]:hover {
        border-color: #3b82f6;
        color: #fff;
    }

    .stTextInput input, .stNumberInput input, .stDateInput input {
        background: #1a1d2e;
        border: 1px solid #2a2f4a;
        color: #e2e8f0;
        border-radius: 6px;
        padding: 8px 12px;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
    }
    .stTextInput label, .stNumberInput label {
        color: #7a85a8;
        font-size: 13px;
        font-weight: 600;
    }
    
    /* Ocultar instrucciones de ayuda en inputs */
    .stTextInput [data-testid="InputInstructions"],
    .stTextInput .st-emotion-cache-1wmy9hl {
        display: none !important;
    }

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

    /* Estilos para checkboxes */
    .stCheckbox {
        color: #e2e8f0;
    }
    .stCheckbox label {
        color: #e2e8f0 !important;
    }
    .stCheckbox input[type="checkbox"]:checked + div {
        background-color: #7a85a8 !important;
    }
    .stCheckbox input[type="checkbox"]:checked + div svg {
        color: #fff !important;
    }

    .weight-indicator {
        font-size: 13px;
        font-weight: 600;
        text-align: right;
        padding: 4px 0;
    }
    .weight-ok { color: #22c55e; }
    .weight-warning { color: #f59e0b; }
    .weight-error { color: #ef4444; }

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

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

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
        render_tab_funds()

    # ── PESTAÑA: COMPARAR CARTERAS ──
    with tab_portfolios:
        st.markdown("<br>", unsafe_allow_html=True)

        # Inputs de carteras
        portfolios = render_portfolios_inputs()
        portfolios_start_dates = [p["portfolio_start_date"] for p in portfolios]

        st.markdown("<br>", unsafe_allow_html=True)

        # Selector de fecha y alineamiento
        start_date_portfolios = render_portfolios_date_selector("portfolios", portfolios_start_dates)

        st.markdown("<br>", unsafe_allow_html=True)

        # Generar gráfica
        if not portfolios:
            st.info("Añade al menos una cartera con fondos y pesos (que sumen 100%) para ver la gráfica.")
        else:
            # Obtener datos de carteras
            portfolios_info = get_portfolios_for_comparison(
                portfolios, # lista de dicts con isins, pesos y fecha de comienzo de cada portfolio (el min de su fondo más reciente)
                start_date_portfolios # fecha de comienzo común de todos los portfolios (historico, max comun (default) y selected)
            )

            if not portfolios_info:
                st.warning("No se pudieron cargar datos de ninguna cartera.")
            else:
                # Generar y mostrar gráfica
                fig = plot_portfolios(portfolios_info, start_date_portfolios)
                st.plotly_chart(fig, width='stretch')
                # 3. Convertir el gráfico a HTML
                # include_plotlyjs='cdn' hace que el archivo sea mucho más ligero
                html_bytes = fig.to_html(include_plotlyjs='cdn')
                # 4. Botón de descarga
                st.download_button(
                    label="Descargar gráfico",
                    data=html_bytes,
                    file_name="comparador_cartera_fondos.html",
                    mime="text/html"
                )


if __name__ == "__main__":
    main()