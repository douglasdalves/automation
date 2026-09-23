import os
from pathlib import Path

from dotenv import load_dotenv

# Carregar .env compartilhado em automation/.env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


class Config:
    MCP_NAME = os.getenv("MCP_NAME", "Health Check")
    MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT = int(os.getenv("MCP_PORT", "5080"))
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    FINANCE_DASHBOARD_DATA_URL = os.getenv(
        "FINANCE_DASHBOARD_DATA_URL", "http://127.0.0.1:8085/api/data"
    )
    FINANCE_BACKUP_SCRIPT = os.getenv(
        "FINANCE_BACKUP_SCRIPT", "/usr/local/bin/finance_backup.sh"
    )
    FINANCE_BACKUP_COMMAND_TIMEOUT = int(
        os.getenv("FINANCE_BACKUP_COMMAND_TIMEOUT", "900")
    )
