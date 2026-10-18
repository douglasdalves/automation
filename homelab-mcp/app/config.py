import os
from pathlib import Path

from dotenv import load_dotenv

# Carregar configuracoes compartilhadas e segredos privados.
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")
load_dotenv(project_root / ".env.token", override=True)


class Config:
    MCP_NAME = os.getenv("MCP_NAME", "Health Check")
    MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT = int(os.getenv("MCP_PORT", "5080"))
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    FINANCE_DASHBOARD_DATA_URL = os.getenv(
        "FINANCE_DASHBOARD_DATA_URL", "http://127.0.0.1:8085/api/data"
    )
    FINANCE_DASHBOARD_SAVE_URL = os.getenv(
        "FINANCE_DASHBOARD_SAVE_URL", "http://127.0.0.1:8085/api/save"
    )
    FINANCE_WRITE_TOKEN = os.getenv("FINANCE_WRITE_TOKEN", "")
    FINANCE_BACKUP_SCRIPT = os.getenv(
        "FINANCE_BACKUP_SCRIPT", "/usr/local/bin/finance_backup.sh"
    )
    FINANCE_BACKUP_DIR = os.getenv("FINANCE_BACKUP_DIR", "/var/backups/finance")
    FINANCE_BACKUP_COMMAND_TIMEOUT = int(
        os.getenv("FINANCE_BACKUP_COMMAND_TIMEOUT", "900")
    )
