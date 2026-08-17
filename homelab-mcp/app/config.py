import os
from pathlib import Path

from dotenv import load_dotenv

# Carregar .env compartilhado em automation/.env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


class Config:
    MCP_NAME = os.getenv("MCP_NAME", "Health Check")
    MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT = int(os.getenv("MCP_PORT", "5080"))
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")