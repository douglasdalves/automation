#!/usr/bin/env bash
# Conservative maintenance for a Raspberry Pi / CasaOS host.
# Default is a preview. Use --apply only after reviewing its output.

set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${HOMELAB_CLEANUP_CONFIG:-/etc/homelab-cleanup.conf}"
[[ -r "$SCRIPT_DIR/homelab-cleanup.conf" ]] && CONFIG_FILE="$SCRIPT_DIR/homelab-cleanup.conf"
[[ -r "$CONFIG_FILE" ]] && # shellcheck disable=SC1090
  source "$CONFIG_FILE"

MODE="preview"
PRUNE_STOPPED_CONTAINERS="false"
ROOT_MOUNT="${ROOT_MOUNT:-/}"
ROOT_USAGE_THRESHOLD="${ROOT_USAGE_THRESHOLD:-70}"
VSCODE_USER="${VSCODE_USER:-${SUDO_USER:-}}"
ALERT_COMMAND="${ALERT_COMMAND:-}"

usage() {
  cat <<'EOF'
Usage: sudo ./homelab-cleanup.sh [--dry-run|--apply] [--prune-stopped-containers] [--threshold PERCENT] [--vscode-user USER]

--dry-run             Show eligible cleanup actions without changing anything (default).
--apply               Perform only the conservative cleanup actions listed in the report.
--prune-stopped-containers
                      Also remove stopped containers. This deletes container metadata and
                      its writable layer, but does not remove volumes or bind mounts.
--threshold PERCENT   Alert when / is at or above this percentage (default: 70).
--vscode-user USER    Owner of ~/.vscode-server; needed for the VS Code Server cleanup.
EOF
}

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
note() { printf '%s\n' "$*"; }

while (($#)); do
  case "$1" in
    --dry-run) MODE="preview" ;;
    --apply) MODE="apply" ;;
    --prune-stopped-containers) PRUNE_STOPPED_CONTAINERS="true" ;;
    --threshold) shift; ROOT_USAGE_THRESHOLD="${1:-}" ;;
    --vscode-user) shift; VSCODE_USER="${1:-}" ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
  shift
done

[[ $EUID -eq 0 ]] || die "Run this script with sudo (it needs APT, Docker, and journald access)."
[[ "$ROOT_USAGE_THRESHOLD" =~ ^[0-9]{1,3}$ ]] && ((ROOT_USAGE_THRESHOLD >= 1 && ROOT_USAGE_THRESHOLD <= 100)) || die "Threshold must be an integer from 1 to 100."

root_usage() {
  df -P "$ROOT_MOUNT" | awk 'NR == 2 { gsub(/%/, "", $5); print $5 }'
}

root_line() {
  df -hP "$ROOT_MOUNT" | awk 'NR == 2 { print }'
}

section() { printf '\n== %s ==\n' "$*"; }

run_or_preview() {
  local label=$1
  shift
  if [[ "$MODE" == "apply" ]]; then
    note "Running: $label"
    "$@"
  else
    note "Would run: $label"
  fi
}

cleanup_vscode_servers() {
  local home servers_dir log_file active_commit candidate base real_servers real_candidate

  if [[ -z "$VSCODE_USER" ]]; then
    note "VS Code Server: skipped (set VSCODE_USER in the config for cron runs)."
    return
  fi
  home="$(getent passwd "$VSCODE_USER" | awk -F: '{print $6}' || true)"
  if [[ -z "$home" || ! -d "$home" ]]; then
    note "VS Code Server: skipped (user '$VSCODE_USER' has no usable home directory)."
    return
  fi

  servers_dir="$home/.vscode-server/cli/servers"
  log_file="$home/.vscode-server/cli/agent-host-stable.log"
  [[ -d "$servers_dir" ]] || { note "VS Code Server: no servers directory for $VSCODE_USER."; return; }
  [[ -r "$log_file" ]] || { note "VS Code Server: skipped (cannot identify active version: $log_file is missing)."; return; }

  active_commit="$(grep -E 'Resolved quality Stable to [0-9a-f]{40}' "$log_file" | tail -n 1 | sed -E 's/.* to ([0-9a-f]{40}).*/\1/' || true)"
  if [[ ! "$active_commit" =~ ^[0-9a-f]{40}$ ]]; then
    note "VS Code Server: skipped (active Stable commit was not found in the log)."
    return
  fi

  real_servers="$(readlink -f -- "$servers_dir")"
  note "VS Code Server: preserving Stable-$active_commit"
  while IFS= read -r -d '' candidate; do
    base="$(basename -- "$candidate")"
    [[ "$base" =~ ^Stable-[0-9a-f]{40}$ ]] || continue
    [[ "$base" == "Stable-$active_commit" ]] && continue
    real_candidate="$(readlink -f -- "$candidate")"
    [[ "$(dirname -- "$real_candidate")" == "$real_servers" ]] || { note "VS Code Server: refusing unexpected path $candidate"; continue; }
    if [[ "$MODE" == "apply" ]]; then
      note "Removing inactive VS Code Server: $base"
      rm -rf -- "$real_candidate"
    else
      note "Would remove inactive VS Code Server: $base"
    fi
  done < <(find "$servers_dir" -mindepth 1 -maxdepth 1 -type d -print0)
}

send_alert_if_needed() {
  local usage=$1 message
  ((usage >= ROOT_USAGE_THRESHOLD)) || return 0
  message="Homelab alert: root filesystem ($ROOT_MOUNT) is ${usage}% full (threshold: ${ROOT_USAGE_THRESHOLD}%)."
  note "ALERT: $message"
  if [[ -n "$ALERT_COMMAND" ]]; then
    if [[ "$MODE" == "apply" ]]; then
      ROOT_USAGE_PERCENT="$usage" ROOT_USAGE_THRESHOLD="$ROOT_USAGE_THRESHOLD" ROOT_MOUNT="$ROOT_MOUNT" ALERT_MESSAGE="$message" bash -c "$ALERT_COMMAND"
    else
      note "Would invoke ALERT_COMMAND with ALERT_MESSAGE and ROOT_USAGE_PERCENT exported."
    fi
  else
    note "Telegram hook not configured; the alert remains in this report."
  fi
}

section "Homelab conservative maintenance ($MODE)"
note "Started: $(date --iso-8601=seconds)"
note "Root before: $(root_line)"

section "APT cache"
run_or_preview "apt-get clean" apt-get clean

section "Docker"
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  run_or_preview "remove dangling Docker images only" docker image prune --filter dangling=true -f
  if [[ "$PRUNE_STOPPED_CONTAINERS" == "true" ]]; then
    run_or_preview "remove stopped Docker containers" docker container prune -f
  else
    note "Stopped Docker containers: preserved (use --prune-stopped-containers to remove them explicitly)."
    note "Stopped containers currently present: $(docker ps -aq --filter status=exited | wc -l)"
  fi
else
  note "Docker: skipped (Docker is unavailable or not running)."
fi

section "systemd journal"
if command -v journalctl >/dev/null 2>&1; then
  note "Journal before: $(journalctl --disk-usage 2>&1 || true)"
  run_or_preview "vacuum archived journal files older than 7 days" journalctl --vacuum-time=7d
else
  note "journald: skipped (journalctl not found)."
fi

section "VS Code Server"
cleanup_vscode_servers

section "Report"
note "Root after:  $(root_line)"
if command -v journalctl >/dev/null 2>&1; then
  note "Journal after:  $(journalctl --disk-usage 2>&1 || true)"
fi
send_alert_if_needed "$(root_usage)"
note "Finished: $(date --iso-8601=seconds)"
