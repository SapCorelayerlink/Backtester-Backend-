import os
from typing import Dict, Any

# Polygon.io Configuration
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "EuDdzXAGRUOBnAPs4e_efsvNQOhYFtzX")
POLYGON_BASE_URL = "https://api.polygon.io"

# Paper Trading Configuration
PAPER_MODE = os.getenv("PAPER_MODE", "True").lower() == "true"
PAPER_STARTING_CASH = float(os.getenv("PAPER_STARTING_CASH", "100000"))

# Database Configuration
DB_CONFIG = {
    "host": os.getenv("PG_HOST"),
    "port": os.getenv("PG_PORT", "5432"),
    "database": os.getenv("PG_DB"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
    "sslmode": os.getenv("PG_SSLMODE", "prefer")
}

# WebSocket Configuration
WEBSOCKET_HOST = os.getenv("WEBSOCKET_HOST", "localhost")
WEBSOCKET_PORT = int(os.getenv("WEBSOCKET_PORT", "8765"))

# Trading Configuration
DEFAULT_COMMISSION = float(os.getenv("DEFAULT_COMMISSION", "0.0"))
DEFAULT_SLIPPAGE = float(os.getenv("DEFAULT_SLIPPAGE", "0.0"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "paper_trader.log")

def get_config() -> Dict[str, Any]:
    """Get all configuration as a dictionary."""
    return {
        "polygon_api_key": POLYGON_API_KEY,
        "polygon_base_url": POLYGON_BASE_URL,
        "paper_mode": PAPER_MODE,
        "paper_starting_cash": PAPER_STARTING_CASH,
        "db_config": DB_CONFIG,
        "websocket_host": WEBSOCKET_HOST,
        "websocket_port": WEBSOCKET_PORT,
        "default_commission": DEFAULT_COMMISSION,
        "default_slippage": DEFAULT_SLIPPAGE,
        "log_level": LOG_LEVEL,
        "log_file": LOG_FILE
    }
