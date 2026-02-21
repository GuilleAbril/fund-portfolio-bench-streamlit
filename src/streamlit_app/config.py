"""
Application constants and configuration.
"""
from pathlib import Path

# Limits
MAX_FUNDS = 10
MAX_PORTFOLIOS = 5

# Portfolio colors
PORTFOLIO_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]

# Project paths
PROJECT_ROOT_PATH = Path(__file__).parent.parent.parent

def load_config():
    """Loads the configuration for the specified environment from a JSON file."""
    import json
    import argparse

    env = "local"

    # Parse --env argument without interfering with Streamlit's own argv usage
    parser = argparse.ArgumentParser(description="Fund Comparator App")
    parser.add_argument("--env", type=str, default="local", help="Execution environment (local, dev, pre, pro)")

    args, _ = parser.parse_known_args()
    if args.env:
        env = args.env

    config_path = PROJECT_ROOT_PATH / "conf" / f"{env}.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    return config

# Load configuration at module import time
config_data = load_config()

DATA_DIR_PATH = PROJECT_ROOT_PATH / config_data["data_dir_relative_path"]
METADATA_DB_PATH = PROJECT_ROOT_PATH / config_data["metadata_db_relative_path"]