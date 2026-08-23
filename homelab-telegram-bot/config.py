import os
from pathlib import Path

from dotenv import load_dotenv
# Carregar configurações compartilhadas e o token separado.
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
token_path = Path(__file__).parent.parent / ".env.token"
load_dotenv(token_path, override=True)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MCP_URL = os.getenv("MCP_URL")
TELEGRAM_ALLOWED_USER_ID = int(os.getenv("TELEGRAM_ALLOWED_USER_ID")) # nao completar com valor default, para forçar a configuração no .env