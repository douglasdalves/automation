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

send_telegram() {
  local MESSAGE="$1"
  local RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d chat_id="${CHAT_ID}" \
    -d text="${MESSAGE}")
  
  # Verifica se houve erro na requisição
  if echo "$RESPONSE" | grep -q '"ok":false'; then
    echo "❌ Erro ao enviar mensagem Telegram: $RESPONSE" >&2
    return 1
  fi
  return 0
}

# Carrega a lista centralizada de containers
if [ -f /usr/local/bin/docker-containers.conf ]; then
  source /usr/local/bin/docker-containers.conf
else
  echo "❌ Erro: /usr/local/bin/docker-containers.conf não encontrado"
  exit 1
fi

ERRORS=0
REPORT="🛑 Relatório de Stop Containers%0A"

for c in "${CONTAINERS[@]}"; do
  if ! docker ps -a --format '{{.Names}}' | grep -q "^${c}$"; then
    REPORT+="❌ ${c} não existe%0A"
    ((ERRORS++))
    continue
  fi

  OUTPUT=$(docker stop "$c" 2>&1)
  STATUS=$?

  if [ $STATUS -eq 0 ]; then
    sleep 2
    if ! docker ps --format '{{.Names}}' | grep -q "^${c}$"; then
      REPORT+="✅ ${c} parado com sucesso%0A"
    else
      REPORT+="⚠️ ${c} ainda está rodando%0A"
      ((ERRORS++))
    fi
  else
    REPORT+="❌ Erro ao parar ${c}%0A${OUTPUT}%0A"
    ((ERRORS++))
  fi
done

if [ $ERRORS -gt 0 ]; then
  send_telegram "$REPORT"
else
  REPORT+="🎉 Todos parados com sucesso"
  send_telegram "$REPORT"
fi

