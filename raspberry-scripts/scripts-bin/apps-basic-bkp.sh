#!/bin/bash

# ===== CONFIG =====
BACKUP_DIR="/media/devmon/Case3.1_Externo/AP-HOME-201/Backups"
DATE=$(date +%Y-%m-%d_%H-%M)

# Carrega variáveis do Telegram
source /usr/local/bin/telegram.conf

send_telegram() {
  local MESSAGE="$1"
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
    -d chat_id="${TELEGRAM_CHAT_ID}" \
    -d text="$MESSAGE" > /dev/null
}

mkdir -p "$BACKUP_DIR"

echo "Iniciando backup dos apps críticos..."

FILES=(
  "/DATA/AppData/adguard-home"
  "/DATA/AppData/uptimekuma"
  "/DATA/AppData/nginxproxymanager"
)

LAST_FILE=""
ERROR=0

for APP_PATH in "${FILES[@]}"; do
  APP_NAME=$(basename "$APP_PATH")
  ARCHIVE="$BACKUP_DIR/${APP_NAME}_$DATE.tar.gz"

  tar -czf "$ARCHIVE" "$APP_PATH" 2>/tmp/backup_error.log
  STATUS=$?

  if [ $STATUS -ne 0 ]; then
    ERROR=1
    break
  fi

  LAST_FILE="$ARCHIVE"
done

if [ $ERROR -eq 0 ]; then
  SIZE=$(du -h "$LAST_FILE" | cut -f1)
  send_telegram "✅ Backup concluído com sucesso.\nÚltimo arquivo: $(basename "$LAST_FILE")\nTamanho: $SIZE"
else
  ERROR_MSG=$(cat /tmp/backup_error.log)
  send_telegram "❌ ERRO no backup.\n$ERROR_MSG"
fi

rm -f /tmp/backup_error.log
