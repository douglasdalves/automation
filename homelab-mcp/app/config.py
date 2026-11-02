from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Carregar configuracoes compartilhadas e segredos privados.
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")
load_dotenv(project_root / ".env.token", override=True)


def _positive_int_env(name: str, default: str, maximum: Optional[int] = None) -> int:
    value = os.getenv(name, default)
    try:
        parsed_value = int(value)
    except ValueError as exc:
        raise ValueError(
            f"Configuração inválida: {name} deve ser um número inteiro."
        ) from exc

    if parsed_value < 1 or (maximum is not None and parsed_value > maximum):
        requirement = (
            f"um número inteiro entre 1 e {maximum}"
            if maximum is not None
            else "um número inteiro positivo"
        )
        raise ValueError(f"Configuração inválida: {name} deve ser {requirement}.")

    return parsed_value


class Config:
    MCP_NAME = os.getenv("MCP_NAME", "Health Check")
    MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
    MCP_PORT = _positive_int_env("MCP_PORT", "5080", maximum=65535)
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEPLOY_COMMAND_TIMEOUT = _positive_int_env("DEPLOY_COMMAND_TIMEOUT", "300")
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
    FINANCE_BACKUP_COMMAND_TIMEOUT = _positive_int_env(
        "FINANCE_BACKUP_COMMAND_TIMEOUT", "900"
    )
