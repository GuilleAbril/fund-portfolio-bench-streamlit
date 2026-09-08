"""
Streamlit application for comparing investment funds and portfolios.
"""

import sys
from pathlib import Path

# Add the src directory to PYTHONPATH
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

import streamlit as st

# Application modules
from streamlit_app.styles import apply_custom_styles
from streamlit_app.tabs.tab_funds import render_tab_funds
from streamlit_app.tabs.tab_portfolios import render_tab_portfolios
from streamlit_app.tabs.tab_available_funds import render_tab_available_funds

def main():
    """Main application entry point."""
    # Page configuration
    st.set_page_config(
        page_title="Fund Comparator",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Apply custom styles
    apply_custom_styles()

    # Main title
    st.markdown("""
        <div style="text-align:center; padding: 30px 0 10px 0;">
            <h1 style="color:#e2e8f0; font-size:28px; font-weight:700; margin:0; letter-spacing:1px;">
                📈 Comparador de Fondos
            </h1>
            <p style="color:#7a85a8; font-size:14px; margin-top:4px;">
                Compara fondos y carteras de fondos de inversión
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Main tabs
    tab_funds, tab_portfolios, tab_available = st.tabs(["Comparar Fondos", "Comparar Carteras", "Fondos Disponibles"])

    with tab_funds:
        render_tab_funds()

    with tab_portfolios:
        render_tab_portfolios()

    with tab_available:
        render_tab_available_funds()


if __name__ == "__main__":
    main()