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
# Rutas del proyecto
PROJECT_ROOT_PATH = Path(__file__).parent.parent.parent  # Sube desde src/streamlit_app/

def load_config():
    """Carga la configuración según el entorno especificado en los argumentos."""
    import sys
    import json
    import argparse

    # Valor por defecto
    env = "local"

    # Intentar parsear argumentos sin interferir con Streamlit
    # Streamlit usa sys.argv, así que buscamos --env manualmente o usamos argparse con parse_known_args
    parser = argparse.ArgumentParser(description="Fund Comparator App")
    parser.add_argument("--env", type=str, default="local", help="Entorno de ejecución (local, dev, pre, pro)")
    
    # parse_known_args devuelve (args, unknown) donde unknown son los args de streamlit
    args, _ = parser.parse_known_args()
    if args.env:
        env = args.env

    config_path = PROJECT_ROOT_PATH / "conf" / f"{env}.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    return config

# Cargar configuración
config_data = load_config()

DATA_DIR_PATH = PROJECT_ROOT_PATH / config_data["data_dir_relative_path"]
METADATA_DB_PATH = PROJECT_ROOT_PATH / config_data["metadata_db_relative_path"]