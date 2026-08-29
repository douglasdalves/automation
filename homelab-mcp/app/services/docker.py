import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List


def _get_compose_directory() -> Path:
    base_dir = Path(__file__).resolve()
    for parent in [*base_dir.parents, base_dir]:
        candidate = parent / "dc-local"
        if candidate.exists():
            return candidate
    return base_dir.parents[2] / "dc-local"


def _is_valid_compose_file_name(file_name: str) -> bool:
    if not file_name or file_name.strip() != file_name:
        return False
    if file_name.startswith("."):
        return False
    if "/" in file_name or "\\" in file_name:
        return False
    if not file_name.lower().endswith(".yaml") and not file_name.lower().endswith(".yml"):
        return False
    return True


def list_compose_files() -> Dict[str, Any]:
    compose_dir = _get_compose_directory()
    if not compose_dir.exists():
        return {"success": False, "error": f"Diretório de compose não encontrado: {compose_dir}"}

    files = []
    for path in sorted(compose_dir.iterdir(), key=lambda item: item.name.lower()):
        if path.is_file() and path.name.lower().endswith((".yaml", ".yml")):
            files.append(path.name)

    return {"success": True, "files": files}


def start_compose_file(file_name: str) -> Dict[str, Any]:
    if not _is_valid_compose_file_name(file_name):
        return {
            "success": False,
            "error": "Nome de arquivo inválido. Use apenas arquivos .yaml/.yml dentro da pasta dc-local.",
        }

    compose_dir = _get_compose_directory()
    compose_path = compose_dir / file_name
    if not compose_path.is_file():
        return {"success": False, "error": f"Arquivo não encontrado: {file_name}"}

    result = _run_docker_command(["compose", "-f", str(compose_path), "up", "-d"], cwd=str(compose_dir))
    if not result["success"]:
        return result

    return {
        "success": True,
        "file_name": file_name,
        "path": str(compose_path),
        "message": f"Compose '{file_name}' iniciado com sucesso.",
    }


def _run_docker_command(args: List[str], cwd: str | None = None) -> Dict[str, Any]:
    command = ["docker", *args]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            cwd=cwd,
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
        cwd=cwd,
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
