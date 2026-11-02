import os
from pathlib import Path

from dotenv import load_dotenv

# Carregar configurações compartilhadas e o token separado.
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
token_path = Path(__file__).parent.parent / ".env.token"
load_dotenv(token_path, override=True)


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(
            f"Configuração obrigatória ausente: {name}. Configure-a no .env ou .env.token."
        )
    return value


def _required_positive_int_env(name: str) -> int:
    value = _required_env(name)
    try:
        parsed_value = int(value)
    except ValueError as exc:
        raise ValueError(
            f"Configuração inválida: {name} deve ser um número inteiro positivo."
        ) from exc

    if parsed_value < 1:
        raise ValueError(
            f"Configuração inválida: {name} deve ser um número inteiro positivo."
        )
    return parsed_value


TELEGRAM_BOT_TOKEN = _required_env("TELEGRAM_BOT_TOKEN")
MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:5080/mcp")
TELEGRAM_ALLOWED_USER_ID = _required_positive_int_env("TELEGRAM_ALLOWED_USER_ID")
FINANCE_WRITE_TOKEN = os.getenv("FINANCE_WRITE_TOKEN", "")
AI_API_URL = os.getenv("AI_API_URL", "https://api.groq.com/openai/v1")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-oss-120b")
