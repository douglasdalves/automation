"""Run the fixed finance backup script from the MCP service."""

from __future__ import annotations

import subprocess
import threading
from pathlib import Path
from typing import Any

from app.config import Config


_backup_lock = threading.Lock()
_MAX_OUTPUT_LENGTH = 2_000


def _output(result: subprocess.CompletedProcess[str]) -> str:
    output = (result.stdout or result.stderr or "").strip()
    return output if len(output) <= _MAX_OUTPUT_LENGTH else output[-_MAX_OUTPUT_LENGTH:]


def run_finance_backup() -> dict[str, Any]:
    """Execute only the administrator-configured finance backup script."""
    script_path = Path(Config.FINANCE_BACKUP_SCRIPT)
    if not script_path.is_absolute() or not script_path.is_file():
        return {
            "success": False,
            "error": f"Script de backup não encontrado ou inválido: {script_path}",
        }

    if not _backup_lock.acquire(blocking=False):
        return {"success": False, "error": "Já existe um backup financeiro em execução."}

    try:
        try:
            result = subprocess.run(
                ["sudo", "-n", str(script_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=Config.FINANCE_BACKUP_COMMAND_TIMEOUT,
            )
        except FileNotFoundError as exc:
            return {"success": False, "error": f"Não foi possível executar o backup: {exc}"}
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "O backup financeiro excedeu o tempo limite configurado.",
            }

        output = _output(result)
        if result.returncode != 0:
            return {
                "success": False,
                "error": output or f"O script terminou com código {result.returncode}.",
            }

        return {"success": True, "output": output}
    finally:
        _backup_lock.release()
