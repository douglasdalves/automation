#!/bin/bash
# Script para configurar o arquivo telegram.conf centralizado

echo "Configurando arquivo telegram.conf centralizado..."

# Lê o arquivo local
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/scripts-bin" && pwd)"
LOCAL_CONF="$SCRIPT_DIR/telegram.conf"

if [ ! -f "$LOCAL_CONF" ]; then
    echo "❌ Erro: $LOCAL_CONF não encontrado"
    exit 1
fi

echo "Copiando $LOCAL_CONF para /usr/local/bin/telegram.conf..."
sudo cp "$LOCAL_CONF" /usr/local/bin/telegram.conf

# Define permissões apropriadas
sudo chmod 644 /usr/local/bin/telegram.conf

# Verifica se foi criado com sucesso
if [ -f /usr/local/bin/telegram.conf ]; then
    echo "✅ Arquivo criado com sucesso em /usr/local/bin/telegram.conf"
    echo ""
    echo "📝 Próximos passos:"
    echo "1. Edite o arquivo: sudo nano /usr/local/bin/telegram.conf"
    echo "2. Adicione seus valores reais:"
    echo "   - BOT_TOKEN: seu token do Telegram Bot"
    echo "   - CHAT_ID: seu ID de chat"
else
    echo "❌ Erro ao criar o arquivo"
    exit 1
fi
