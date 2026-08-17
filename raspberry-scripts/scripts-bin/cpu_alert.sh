#!/bin/bash

# Carrega variáveis do Telegram
if [ -f /usr/local/bin/telegram.conf ]; then
  source /usr/local/bin/telegram.conf
else
  echo "❌ Erro: /usr/local/bin/telegram.conf não encontrado"
  exit 1
fi

# Verifica se as variáveis foram carregadas
if [ -z "$BOT_TOKEN" ] || [ -z "$CHAT_ID" ]; then
  echo "❌ Erro: BOT_TOKEN ou CHAT_ID não definidos"
  exit 1
fi

WARNING=60
CRITICAL=75

STATE_FILE="/tmp/pi_temp_state"

TEMP_RAW=$(vcgencmd measure_temp | grep -oP '[0-9.]+')
TEMP=${TEMP_RAW%.*}

if [ "$TEMP" -ge "$CRITICAL" ]; then
  CURRENT_STATE="CRITICAL"
elif [ "$TEMP" -ge "$WARNING" ]; then
  CURRENT_STATE="WARNING"
else
  CURRENT_STATE="NORMAL"
fi

LAST_STATE="NONE"
[ -f "$STATE_FILE" ] && LAST_STATE=$(cat "$STATE_FILE")

send_msg() {
  local RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
    -d chat_id="$CHAT_ID" \
    -d parse_mode="Markdown" \
    -d text="$1")
  
  if echo "$RESPONSE" | grep -q '"ok":false'; then
    echo "❌ Erro ao enviar mensagem Telegram: $RESPONSE" >&2
    return 1
  fi
  return 0
}

if [ "$CURRENT_STATE" != "$LAST_STATE" ]; then
  case "$CURRENT_STATE" in
    WARNING)
      send_msg "🟡 *WARNING*\n🌡️ Temperatura: ${TEMP_RAW}°C\n⚠️ Acima do normal"
      ;;
    CRITICAL)
      send_msg "🔴 *CRITICAL*\n🌡️ Temperatura: ${TEMP_RAW}°C\n🔥 Risco de throttling"
      ;;
    NORMAL)
      send_msg "🟢 *NORMAL*\n🌡️ Temperatura: ${TEMP_RAW}°C\n✅ Temperatura estabilizada"
      ;;
  esac

  echo "$CURRENT_STATE" > "$STATE_FILE"
fi
