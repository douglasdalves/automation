import os
import subprocess
import threading
from pathlib import Path
from typing import Any, Dict


_deploy_lock = threading.Lock()
_COMMAND_TIMEOUT = int(os.getenv("DEPLOY_COMMAND_TIMEOUT", "300"))
_MAX_OUTPUT_LENGTH = 2000


def _output(result: subprocess.CompletedProcess[str]) -> str:
    text = (result.stdout or result.stderr or "").strip()
    if len(text) <= _MAX_OUTPUT_LENGTH:
        return text
    return text[-_MAX_OUTPUT_LENGTH:]


def deploy() -> Dict[str, Any]:
    repository_dir = Path(
        os.getenv("DEPLOY_REPOSITORY_DIR", "/home/dalves/automation")
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

        return {
            "success": True,
            "step": "complete",
            "git_pull": _output(pull),
        }
    finally:
        _deploy_lock.release()