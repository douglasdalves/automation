import os
from pathlib import Path

from dotenv import load_dotenv

# Carregar configurações compartilhadas e o token separado.
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
token_path = Path(__file__).parent.parent / ".env.token"
load_dotenv(token_path, override=True)

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN", ""
)  # nao completar com valor default, para forçar a configuração no .env
MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:5080/mcp")
TELEGRAM_ALLOWED_USER_ID = int(
    os.getenv("TELEGRAM_ALLOWED_USER_ID", "")
)  # nao completar com valor default, para forçar a configuração no .env
AI_API_URL = os.getenv("AI_API_URL", "https://api.groq.com/openai/v1")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-oss-120b")
