import os
import subprocess
import threading
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

_deploy_lock = threading.Lock()
_COMMAND_TIMEOUT = int(os.getenv("DEPLOY_COMMAND_TIMEOUT"))
_MAX_OUTPUT_LENGTH = 2000
_DEFAULT_SERVICES = ("homelab-telegram-bot", "homelab-mcp")


def _output(result: subprocess.CompletedProcess[str]) -> str:
    text = (result.stdout or result.stderr or "").strip()
    if len(text) <= _MAX_OUTPUT_LENGTH:
        return text
    return text[-_MAX_OUTPUT_LENGTH:]


def deploy() -> Dict[str, Any]:
    repository_dir = Path(
        os.getenv("DEPLOY_REPOSITORY_DIR")
    ).expanduser()

    if not repository_dir.is_dir():
        return {"success": False, "error": f"Repository directory not found: {repository_dir}"}

    if not _deploy_lock.acquire(blocking=False):
        return {"success": False, "error": "A deploy is already running."}

    try:
        try:
            pull = subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=repository_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=_COMMAND_TIMEOUT,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            return {"success": False, "step": "git_pull", "error": str(exc)}

        if pull.returncode != 0:
            return {
                "success": False,
                "step": "git_pull",
                "error": _output(pull) or "git pull failed",
            }

        sync_dir = repository_dir / "configs-apps" / "app-config-sync"
        sync_commands = [
            ["sudo", "mkdir", "-p", "/etc/app-config-sync"],
            [
                "sudo",
                "cp",
                str(sync_dir / "sync.conf"),
                "/etc/app-config-sync/sync.conf",
            ],
            [
                "sudo",
                "cp",
                str(sync_dir / "sync-configs.sh"),
                "/usr/local/bin/sync-configs.sh",
            ],
            ["sudo", "chmod", "+x", "/usr/local/bin/sync-configs.sh"],
            [
                "sudo",
                "cp",
                str(sync_dir / "app-config-sync.service"),
                str(sync_dir / "app-config-sync.path"),
                "/etc/systemd/system/",
            ],
            ["sudo", "systemctl", "daemon-reload"],
            ["sudo", "systemctl", "enable", "--now", "app-config-sync.path"],
            ["sudo", "systemctl", "start", "app-config-sync.service"],
        ]
        for command in sync_commands:
            try:
                sync_setup = subprocess.run(
                    command,
                    cwd=repository_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=_COMMAND_TIMEOUT,
                )
            except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
                return {"success": False, "step": "sync_setup", "command": command, "error": str(exc)}

            if sync_setup.returncode != 0:
                return {
                    "success": False,
                    "step": "sync_setup",
                    "command": command,
                    "error": _output(sync_setup) or "app-config-sync setup failed",
                }

        services = tuple(
            service.strip()
            for service in os.getenv("DEPLOY_SERVICES", ",".join(_DEFAULT_SERVICES)).split(",")
            if service.strip()
        )
        restarted_services = []
        for service in services:
            try:
                restart = subprocess.run(
                    ["sudo", "systemctl", "restart", service],
                    cwd=repository_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=_COMMAND_TIMEOUT,
                )
            except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
                return {
                    "success": False,
                    "step": "restart_service",
                    "service": service,
                    "restarted_services": restarted_services,
                    "error": str(exc),
                }

            if restart.returncode != 0:
                return {
                    "success": False,
                    "step": "restart_service",
                    "service": service,
                    "restarted_services": restarted_services,
                    "error": _output(restart) or f"failed to restart {service}",
                }
            restarted_services.append(service)

        return {
            "success": True,
            "step": "complete",
            "git_pull": _output(pull),
            "restarted_services": restarted_services,
        }
    finally:
        _deploy_lock.release()