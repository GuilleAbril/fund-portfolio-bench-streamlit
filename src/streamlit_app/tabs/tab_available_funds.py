"""
Logic for the available funds tab.
Displays all funds from the metadata database.
"""
import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

import streamlit as st

from streamlit_app.utils.database_utils import get_all_funds


# Column display name mapping (DB column -> Spanish UI label)
_COLUMN_LABELS = {
    'isin': 'ISIN',
    'start_date': 'Fecha de inicio',
    'name': 'Nombre',
    'updated_at': 'Última actualización'
}


def render_tab_available_funds():
    """Renders the available funds tab showing all funds from the database."""
    st.markdown("<br>", unsafe_allow_html=True)

    funds_df = get_all_funds()

    if funds_df.empty:
        st.warning("No se encontraron fondos en la base de datos.")
        return

    # Rename columns to user-friendly Spanish names
    display_df = funds_df.rename(columns=_COLUMN_LABELS)

    # Reorder to show Name first, then ISIN, then dates
    desired_order = ['Nombre', 'ISIN', 'Fecha de inicio', 'Última actualización']
    existing_cols = [c for c in desired_order if c in display_df.columns]
    remaining_cols = [c for c in display_df.columns if c not in existing_cols]
    display_df = display_df[existing_cols + remaining_cols]

    st.markdown(f"**Total de fondos disponibles: {len(display_df)}**")

    st.dataframe(
        display_df,
        width='stretch',
        hide_index=True,
        height=600
    )
