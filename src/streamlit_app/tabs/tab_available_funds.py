"""
Logic for the available funds tab.
Displays all funds from the metadata database.
"""
import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

import streamlit as st

from streamlit_app.utils.database_utils import get_all_funds_to_display


def render_tab_available_funds():
    st.markdown("<br>", unsafe_allow_html=True)

    display_data = get_all_funds_to_display()

    if not display_data:
        st.warning("No se encontraron fondos en la base de datos.")
        return

    st.markdown(f"**Total de fondos disponibles: {len(display_data)}**")

    st.dataframe(
        display_data,
        width='stretch',
        hide_index=True,
        height=600
    )
