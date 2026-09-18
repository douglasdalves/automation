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
FAILED_CONTAINERS=()

for c in "${CONTAINERS[@]}"; do
  if ! docker ps -a --format '{{.Names}}' | grep -q "^${c}$"; then
    FAILED_CONTAINERS+=("$c")
    ((ERRORS++))
    continue
  fi

  # `docker start` succeeds even if the container is already running.
  if docker ps --format '{{.Names}}' | grep -q "^${c}$"; then
    continue
  fi

  if docker start "$c" >/dev/null 2>&1; then
    sleep 2
    if docker ps --format '{{.Names}}' | grep -q "^${c}$"; then
      continue
    else
      FAILED_CONTAINERS+=("$c")
      ((ERRORS++))
    fi
  else
    FAILED_CONTAINERS+=("$c")
    ((ERRORS++))
  fi
done

if [ $ERRORS -gt 0 ]; then
  send_telegram "⚠️ Falha ao iniciar os containers: ${FAILED_CONTAINERS[*]}"
else
  send_telegram "✅ Containers iniciados com sucesso"
fi
