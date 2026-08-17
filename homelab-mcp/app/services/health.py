import os
import shutil
import subprocess
import time

try:
    import psutil
except ImportError:  # pragma: no cover - depends on environment
    psutil = None

from app.services.docker import list_containers


def cpu_usage():
    if psutil is not None:
        return psutil.cpu_percent(interval=1)

    try:
        with open("/proc/loadavg", "r", encoding="utf-8") as handle:
            return round(float(handle.read().split()[0]) * 100, 2)
    except Exception:
        return None


def cpu_temperature():
    try:
        result = subprocess.run(
            ["vcgencmd", "measure_temp"],
            capture_output=True,
            text=True,
            check=True,
        )

        temp = result.stdout.strip()
        return float(temp.replace("temp=", "").replace("'C", ""))

    except Exception:
        return None


def memory():
    if psutil is not None:
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "percent": mem.percent,
        }

    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as handle:
            meminfo = {}
            for line in handle:
                key, value = line.split(":", 1)
                meminfo[key.strip()] = int(value.split()[0])

        total_kb = meminfo.get("MemTotal", 0)
        available_kb = meminfo.get("MemAvailable", 0)
        used_kb = max(total_kb - available_kb, 0)
        percent = round((used_kb / total_kb * 100) if total_kb else 0, 2)

        return {
            "total_gb": round(total_kb / (1024**2), 2),
            "used_gb": round(used_kb / (1024**2), 2),
            "percent": percent,
        }
    except Exception:
        return {"total_gb": None, "used_gb": None, "percent": None}


def disk():
    if psutil is not None:
        disk_usage = psutil.disk_usage("/")
        return {
            "total_gb": round(disk_usage.total / (1024**3), 2),
            "used_gb": round(disk_usage.used / (1024**3), 2),
            "percent": disk_usage.percent,
        }

    disk_usage = shutil.disk_usage("/")
    total = disk_usage.total
    used = disk_usage.used
    percent = round((used / total * 100) if total else 0, 2)

    return {
        "total_gb": round(total / (1024**3), 2),
        "used_gb": round(used / (1024**3), 2),
        "percent": percent,
    }


def uptime():
    if psutil is not None:
        seconds = int(time.time() - psutil.boot_time())
    else:
        try:
            with open("/proc/uptime", "r", encoding="utf-8") as handle:
                seconds = int(float(handle.read().split()[0]))
        except Exception:
            return {"days": None, "hours": None, "minutes": None}

    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, _ = divmod(seconds, 60)

    return {
        "days": days,
        "hours": hours,
        "minutes": minutes,
    }


def health_check():
    docker_state = list_containers(all_containers=False)
    running_containers = []

    if docker_state.get("success"):
        running_containers = [
            container for container in docker_state.get("containers", []) if container.get("status", "").lower().startswith("up")
        ]

    return {
        "cpu": {
            "usage_percent": cpu_usage(),
            "temperature": cpu_temperature(),
        },
        "memory": memory(),
        "disk": disk(),
        "uptime": uptime(),
        "docker": {
            "running_containers": running_containers,
        },
    }