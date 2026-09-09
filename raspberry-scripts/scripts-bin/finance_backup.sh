#!/bin/bash

set -Eeuo pipefail

CONFIG_FILE="${FINANCE_BACKUP_CONFIG:-/etc/finance-backup.conf}"
if [ -f "$CONFIG_FILE" ]; then
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
fi

CONTAINER_NAME="${CONTAINER_NAME:-dc-finance-api}"
CONTAINER_DATABASE="${CONTAINER_DATABASE:-/data/finance.db}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/finance}"
RCLONE_REMOTE="${RCLONE_REMOTE:-}"
RCLONE_PATH="${RCLONE_PATH:-homelab-backups/finance}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

if [ -z "$RCLONE_REMOTE" ]; then
  echo "Erro: RCLONE_REMOTE nao configurado em $CONFIG_FILE" >&2
  exit 1
fi

for command in docker gzip rclone; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "Erro: comando nao encontrado: $command" >&2
    exit 1
  fi
done

if ! docker inspect --format '{{.State.Running}}' "$CONTAINER_NAME" 2>/dev/null | grep -qx true; then
  echo "Erro: container nao esta em execucao: $CONTAINER_NAME" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
CONTAINER_SNAPSHOT="/tmp/finance-backup-${DATE}.db"
LOCAL_SNAPSHOT="$BACKUP_DIR/finance-${DATE}.db"
ARCHIVE="$LOCAL_SNAPSHOT.gz"
REMOTE_TARGET="${RCLONE_REMOTE}:${RCLONE_PATH}"

cleanup() {
  docker exec "$CONTAINER_NAME" rm -f "$CONTAINER_SNAPSHOT" >/dev/null 2>&1 || true
  rm -f "$LOCAL_SNAPSHOT" "$ARCHIVE"
}
trap cleanup EXIT

echo "Criando snapshot SQLite consistente..."
docker exec "$CONTAINER_NAME" python3 - "$CONTAINER_DATABASE" "$CONTAINER_SNAPSHOT" <<'PY'
import sqlite3
import sys

source_path, target_path = sys.argv[1:]
with sqlite3.connect(source_path) as source:
    with sqlite3.connect(target_path) as target:
        source.backup(target)
PY

echo "Copiando snapshot para o Raspberry..."
docker cp "${CONTAINER_NAME}:${CONTAINER_SNAPSHOT}" "$LOCAL_SNAPSHOT"

if command -v sqlite3 >/dev/null 2>&1; then
  if [ "$(sqlite3 "$LOCAL_SNAPSHOT" 'PRAGMA integrity_check;')" != "ok" ]; then
    echo "Erro: integrity_check falhou" >&2
    exit 1
  fi
else
  echo "Aviso: sqlite3 nao instalado; integrity_check local ignorado" >&2
fi

gzip -9 "$LOCAL_SNAPSHOT"
echo "Enviando backup para $REMOTE_TARGET..."
rclone copyto "$ARCHIVE" "$REMOTE_TARGET/$(basename "$ARCHIVE")" --no-traverse

if [[ "$RETENTION_DAYS" =~ ^[0-9]+$ ]]; then
  rclone delete "$REMOTE_TARGET" --min-age "${RETENTION_DAYS}d" --include 'finance-*.db.gz' --no-traverse
else
  echo "Aviso: RETENTION_DAYS invalido; limpeza remota ignorada" >&2
fi

echo "Backup financeiro concluido: $(basename "$ARCHIVE")"
