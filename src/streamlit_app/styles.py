"""
Estilos CSS personalizados para la aplicación Streamlit.
"""
import streamlit as st


def apply_custom_styles():
    """Aplica los estilos CSS personalizados a la aplicación."""
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

        /* Estilos para botones normales */
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

        /* Estilos para botones primarios (como "Comparar fondos") */
        .stButton button[kind="primary"] {
            background: #1e3a8a;
            border: 1px solid #3b82f6;
            color: #60a5fa;
            border-radius: 6px;
            padding: 10px 16px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            width: 100%;
        }
        .stButton button[kind="primary"]:hover {
            background: #1e40af;
            border-color: #60a5fa;
            color: #93c5fd;
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
        }
        .stButton button[kind="primary"]:disabled {
            background: #1a1d2e;
            border-color: #2a2f4a;
            color: #4a5568;
            cursor: not-allowed;
            opacity: 0.5;
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