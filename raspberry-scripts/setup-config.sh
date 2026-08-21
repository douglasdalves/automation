#!/bin/bash
# Script para configurar o arquivo telegram.conf centralizado

echo "Configurando arquivo telegram.conf centralizado..."

# Lê o arquivo local
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/scripts-bin" && pwd)"
LOCAL_CONF="$SCRIPT_DIR/telegram.conf"
CONTAINERS_CONF="$SCRIPT_DIR/docker-containers.conf"
DOCKER_MORNING_START="$SCRIPT_DIR/docker_morning_start.sh"
DOCKER_NIGHT_STOP="$SCRIPT_DIR/docker_night_stop.sh"

if [ ! -f "$LOCAL_CONF" ]; then
    echo "❌ Erro: $LOCAL_CONF não encontrado"
    exit 1
fi

if [ ! -f "$CONTAINERS_CONF" ]; then
    echo "❌ Erro: $CONTAINERS_CONF não encontrado"
    exit 1
fi

echo "Copiando $LOCAL_CONF para /usr/local/bin/..."
#sudo cp "$LOCAL_CONF" /usr/local/bin/telegram.conf
sudo cp "$CONTAINERS_CONF" /usr/local/bin/docker-containers.conf
sudo cp "$DOCKER_MORNING_START" /usr/local/bin/docker_morning_start.sh
sudo cp "$DOCKER_NIGHT_STOP" /usr/local/bin/docker_night_stop.sh

# Define permissões apropriadas
#sudo chmod 644 /usr/local/bin/telegram.conf
sudo chmod 644 /usr/local/bin/docker-containers.conf

# Verifica se foi criado com sucesso
if [ -f /usr/local/bin/telegram.conf ] && [ -f /usr/local/bin/docker-containers.conf ]; then
    #echo "✅ Arquivo criado com sucesso em /usr/local/bin/telegram.conf"
    echo "✅ Arquivo criado com sucesso em /usr/local/bin/docker-containers.conf"
    echo ""
    echo "📝 Próximos passos:"
    #echo "1. Edite o arquivo: sudo nano /usr/local/bin/telegram.conf"
    #echo "2. Adicione seus valores reais:"
    #echo "   - BOT_TOKEN: seu token do Telegram Bot"
    #echo "   - CHAT_ID: seu ID de chat"
    echo "3. Para alterar os containers, edite: sudo nano /usr/local/bin/docker-containers.conf"
else
    echo "❌ Erro ao criar o arquivo"
    exit 1
fi
