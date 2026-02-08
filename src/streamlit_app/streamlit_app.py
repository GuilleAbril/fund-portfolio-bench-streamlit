"""
Aplicación Streamlit para comparar fondos y carteras de inversión.
"""
# TODO: Poner que se muestre igual el hovertemplate en carteras que fondos
#  poner opción 1 año y 3 años con el botón y seleccionar fecha incio y fecha fin
#  meterle como argumento el path a la data o un env para que lo coja del fichero de config.

import sys
from pathlib import Path

# Añadir el directorio src al PYTHONPATH
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

import streamlit as st

# Importar módulos propios
from streamlit_app.styles import apply_custom_styles
from streamlit_app.tabs.tab_funds import render_tab_funds
from streamlit_app.tabs.tab_portfolios import render_tab_portfolios

def main():
    """Función principal de la aplicación."""
    # Configuración de página
    st.set_page_config(
        page_title="Fund Comparator",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Aplicar estilos personalizados
    apply_custom_styles()

    # Título principal
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

    with tab_funds:
        render_tab_funds()

    with tab_portfolios:
        render_tab_portfolios()


if __name__ == "__main__":
    main()