"""
Constantes y configuración de la aplicación.
"""
from pathlib import Path

# Configuración de límites
MAX_FUNDS = 10
MAX_PORTFOLIOS = 5

# Colores para las carteras
PORTFOLIO_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]

# Rutas del proyecto
PROJECT_ROOT_PATH = Path(__file__).parent.parent.parent  # Sube desde src/streamlit_app/
DATA_DIR_PATH = PROJECT_ROOT_PATH / "src" / "download_data" / "data"
METADATA_DB_PATH = DATA_DIR_PATH / "metadata_funds.db"