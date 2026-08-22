# Homelab Telegram Bot

Bot Telegram para consultar a saude do homelab, executar deploy e reiniciar servicos por meio do Homelab MCP.

## Requisitos

- Python 3
- Um bot criado no Telegram pelo BotFather
- Homelab MCP ativo e acessivel

## Configuracao

Na raiz de `automation`, crie ou preencha `.env` com as configuracoes compartilhadas:

```env
MCP_URL=http://127.0.0.1:5080/mcp
TELEGRAM_ALLOWED_USER_ID=123456789
DEPLOY_SERVICES=homelab-telegram-bot,homelab-mcp
```

Crie `.env.token` dentro desta pasta com o token do bot:

```env
TELEGRAM_BOT_TOKEN=cole_o_token_do_bot_aqui
```

O `.env.token` deve permanecer privado e ja e ignorado pelo Git.

## Instalacao

```bash
cd /home/dalves/automation/homelab-telegram-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Execucao manual

```bash
cd /home/dalves/automation/homelab-telegram-bot
source .venv/bin/activate
python bot.py
```

## Comandos do bot

- `/status`: mostra CPU, temperatura, memoria, disco, uptime e containers ativos.
- `/deploy`: atualiza o repositorio e reinicia os servicos configurados.
- `/restart_service`: mostra botoes para escolher qual servico reiniciar.
- `/restart-docker`: lista os containers Docker ativos e mostra botoes para escolher qual reiniciar.

O `/deploy` executa o fluxo completo no MCP: faz `git pull --ff-only`, atualiza o sincronizador `app-config-sync`, recarrega o systemd, sincroniza os arquivos e reinicia os servicos definidos em `DEPLOY_SERVICES`. Se uma etapa falhar, o bot informa o erro retornado pelo MCP.

Somente o usuario cujo ID esta em `TELEGRAM_ALLOWED_USER_ID` pode usar os comandos.

## systemd

```bash
sudo cp scripts-services/homelab-telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable homelab-telegram-bot
sudo systemctl start homelab-telegram-bot
sudo systemctl status homelab-telegram-bot
```

Para acompanhar os logs:

```bash
journalctl -u homelab-telegram-bot -f
```

## Solucao de problemas

Verifique se o MCP responde em `MCP_URL`, se o token esta em `.env.token` e se o servico tem permissao para executar os comandos `sudo systemctl` necessarios.
