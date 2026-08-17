import json
import shutil
import subprocess
from typing import Any, Dict, List


def _run_docker_command(args: List[str]) -> Dict[str, Any]:
    command = ["docker", *args]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        return {
            "success": False,
            "error": "Docker CLI not found on the system.",
            "details": str(exc),
        }

    if result.returncode == 0:
        return {
            "success": True,
            "stdout": result.stdout,
        }

    error_output = (result.stderr or result.stdout or "Unknown Docker error").strip()
    if not _is_docker_permission_error(error_output):
        return {
            "success": False,
            "error": error_output,
        }

    sudo_path = shutil.which("sudo")
    if not sudo_path:
        return {
            "success": False,
            "error": "Docker access denied. Check Docker permissions or run with sufficient privileges.",
            "details": error_output,
        }

    elevated_result = subprocess.run(
        ["sudo", "-n", *command],
        capture_output=True,
        text=True,
        check=False,
    )
    if elevated_result.returncode == 0:
        return {
            "success": True,
            "stdout": elevated_result.stdout,
        }

    fallback_error = (elevated_result.stderr or elevated_result.stdout or "Unknown Docker error").strip()
    return {
        "success": False,
        "error": "Docker access denied. Check Docker permissions or run with sufficient privileges.",
        "details": f"{error_output}; {fallback_error}".strip("; "),
    }


def _is_docker_permission_error(error_output: str) -> bool:
    lowered = error_output.lower()
    return "permission denied" in lowered or "/var/run/docker.sock" in lowered


def list_containers(all_containers: bool = False) -> Dict[str, Any]:
    args = ["ps", "--format", "{{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}"]
    if all_containers:
        args.append("--all")

    result = _run_docker_command(args)
    if not result["success"]:
        return result

    lines = [line for line in result["stdout"].splitlines() if line.strip()]
    if not lines:
        return {"success": True, "containers": []}

    containers: List[Dict[str, Any]] = []
    for line in lines:
        parts = line.split("\t")
        if len(parts) < 4:
            continue

        container_id, image, status, name = parts[:4]
        containers.append(
            {
                "id": container_id.strip(),
                "image": image.strip(),
                "status": status.strip(),
                "name": name.strip(),
            }
        )

    return {"success": True, "containers": containers}


def inspect_container(container_id: str) -> Dict[str, Any]:
    result = _run_docker_command(["inspect", container_id])
    if not result["success"]:
        return result

    try:
        payload = json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        return {"success": False, "error": f"Unable to parse Docker inspect output: {exc}"}

    if not payload:
        return {"success": False, "error": "Container not found."}

    data = payload[0]
    return {
        "success": True,
        "container": {
            "name": data.get("Name", "").lstrip("/"),
            "image": data.get("Config", {}).get("Image", ""),
            "status": data.get("State", {}).get("Status", "")
        },
    }


def manage_container(container_id: str, action: str) -> Dict[str, Any]:
    allowed_actions = {"start", "stop", "restart", "kill", "remove"}
    if action not in allowed_actions:
        return {"success": False, "error": f"Unsupported action '{action}'. Allowed actions: {', '.join(sorted(allowed_actions))}"}

    result = _run_docker_command([action, container_id])
    if not result["success"]:
        return result

    return {
        "success": True,
        "action": action,
        "container": container_id,
        "message": f"Container '{container_id}' {action}ed successfully.",
    }
