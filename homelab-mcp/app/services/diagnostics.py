from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import Config
from app.services.deploy import configured_services
from app.services.docker import list_containers

_BACKUP_MAX_AGE_HOURS = 36


def _configuration_status() -> list[dict[str, Any]]:
    services = configured_services()
    backup_script = Path(Config.FINANCE_BACKUP_SCRIPT).expanduser()
    backup_dir = Path(Config.FINANCE_BACKUP_DIR).expanduser()

    return [
        {
            "name": "DEPLOY_SERVICES",
            "status": "ok" if services else "error",
            "required": True,
            "detail": ", ".join(services)
            if services
            else "Nenhum serviço configurado.",
        },
        {
            "name": "FINANCE_DASHBOARD_DATA_URL",
            "status": ("ok" if Config.FINANCE_DASHBOARD_DATA_URL.strip() else "error"),
            "required": True,
            "detail": (
                "Configurada"
                if Config.FINANCE_DASHBOARD_DATA_URL.strip()
                else "Não configurada."
            ),
        },
        {
            "name": "FINANCE_WRITE_TOKEN",
            "status": "ok" if Config.FINANCE_WRITE_TOKEN else "warning",
            "required": False,
            "detail": (
                "Configurado"
                if Config.FINANCE_WRITE_TOKEN
                else "Ausente; /conta_fixa não estará disponível."
            ),
        },
        {
            "name": "FINANCE_BACKUP_SCRIPT",
            "status": "ok" if backup_script.is_file() else "error",
            "required": True,
            "detail": (
                "Script encontrado"
                if backup_script.is_file()
                else "Script não encontrado ou inválido."
            ),
        },
        {
            "name": "FINANCE_BACKUP_DIR",
            "status": "ok" if backup_dir.is_absolute() else "error",
            "required": True,
            "detail": (
                "Configurado"
                if backup_dir.is_absolute()
                else "Configure um caminho absoluto."
            ),
        },
    ]


def _service_status(service: str) -> dict[str, str]:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except FileNotFoundError:
        return {
            "name": service,
            "status": "unknown",
            "detail": "systemctl não encontrado.",
        }
    except subprocess.TimeoutExpired:
        return {
            "name": service,
            "status": "unknown",
            "detail": "A consulta excedeu o tempo limite.",
        }

    state = (result.stdout or result.stderr).strip() or "unknown"
    return {
        "name": service,
        "status": "ok" if result.returncode == 0 and state == "active" else "warning",
        "detail": state,
    }


def _backup_status() -> dict[str, Any]:
    backup_dir = Path(Config.FINANCE_BACKUP_DIR).expanduser()
    if not backup_dir.is_absolute():
        return {
            "status": "error",
            "detail": "FINANCE_BACKUP_DIR precisa ser um caminho absoluto.",
            "last_file": None,
            "timestamp": None,
            "age_hours": None,
        }
    if not backup_dir.is_dir():
        return {
            "status": "warning",
            "detail": "Diretório de backups não encontrado.",
            "last_file": None,
            "timestamp": None,
            "age_hours": None,
        }

    try:
        backups = [
            path
            for path in backup_dir.iterdir()
            if path.is_file()
            and path.name.startswith("finance-")
            and path.name.endswith(".db.gz")
        ]
        latest = max(backups, key=lambda path: path.stat().st_mtime, default=None)
        if latest is None:
            return {
                "status": "warning",
                "detail": "Nenhum arquivo de backup financeiro encontrado.",
                "last_file": None,
                "timestamp": None,
                "age_hours": None,
            }

        modified_at = latest.stat().st_mtime
    except OSError as exc:
        return {
            "status": "error",
            "detail": f"Não foi possível consultar os backups: {exc}",
            "last_file": None,
            "timestamp": None,
            "age_hours": None,
        }

    age_hours = max(
        0,
        round((datetime.now(timezone.utc).timestamp() - modified_at) / 3600, 1),
    )
    is_fresh = age_hours <= _BACKUP_MAX_AGE_HOURS
    return {
        "status": "ok" if is_fresh else "warning",
        "detail": (
            "Backup recente"
            if is_fresh
            else f"Backup mais recente tem mais de {_BACKUP_MAX_AGE_HOURS} horas."
        ),
        "last_file": latest.name,
        "timestamp": datetime.fromtimestamp(modified_at, timezone.utc).isoformat(),
        "age_hours": age_hours,
    }


def homelab_diagnostics() -> dict[str, Any]:
    configuration = _configuration_status()
    services = [_service_status(service) for service in configured_services()]
    docker = list_containers(all_containers=True)
    backup = _backup_status()

    if docker.get("success"):
        containers = docker.get("containers", [])
        running_count = sum(
            container.get("status", "").lower().startswith("up")
            for container in containers
        )
        docker_status = {
            "status": ("warning" if running_count < len(containers) else "ok"),
            "containers": containers,
            "running": running_count,
            "stopped": len(containers) - running_count,
            "detail": "Docker consultado.",
        }
    else:
        docker_status = {
            "status": "error",
            "containers": [],
            "running": 0,
            "stopped": 0,
            "detail": str(docker.get("error", "Falha ao consultar Docker.")),
        }

    all_statuses = [item["status"] for item in configuration + services] + [
        docker_status["status"],
        backup["status"],
    ]
    overall_status = (
        "error"
        if "error" in all_statuses
        else "warning"
        if "warning" in all_statuses or "unknown" in all_statuses
        else "ok"
    )

    return {
        "success": True,
        "status": overall_status,
        "configuration": configuration,
        "services": services,
        "docker": docker_status,
        "backup": backup,
    }
