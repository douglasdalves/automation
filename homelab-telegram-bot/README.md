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
# API compativel com OpenAI (OpenAI, Groq, OpenRouter etc.)
AI_API_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
```

Crie `.env.token` dentro desta pasta com o token do bot:

```env
TELEGRAM_BOT_TOKEN=cole_o_token_do_bot_aqui
AI_API_KEY=cole_a_chave_da_api_aqui
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
- `/restart_docker`: lista os containers Docker ativos e mostra botoes para escolher qual reiniciar.
- `/start_docker`: lista os containers Docker e mostra botoes para escolher qual iniciar.
- `/stop_docker`: lista os containers Docker e mostra botoes para escolher qual parar.

O `/deploy` executa o fluxo completo no MCP: faz `git pull --ff-only`, atualiza o sincronizador `app-config-sync`, recarrega o systemd, sincroniza os arquivos e reinicia os servicos definidos em `DEPLOY_SERVICES`. Se uma etapa falhar, o bot informa o erro retornado pelo MCP.

Somente o usuario cujo ID esta em `TELEGRAM_ALLOWED_USER_ID` pode usar os comandos.
Mensagens de texto sem comando sao enviadas para a API de IA configurada, que pode consultar e operar o homelab pelas ferramentas MCP.

Para usar um provedor compativel com a API da OpenAI, configure `AI_API_URL`, `AI_API_KEY` e `AI_MODEL`. Exemplos:

```bash
# OpenAI
AI_API_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini

# Groq
AI_API_URL=https://api.groq.com/openai/v1
AI_MODEL=llama-3.3-70b-versatile

# OpenRouter
AI_API_URL=https://openrouter.ai/api/v1
AI_MODEL=openai/gpt-4o-mini
```

O provedor precisa aceitar `POST /chat/completions` e tool calling. O MCP continua rodando localmente; somente o processamento da linguagem e a chave ficam no provedor externo.

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
