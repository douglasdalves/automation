import os
from pathlib import Path

from dotenv import load_dotenv

# Carregar .env compartilhado em automation/.env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


class Config:
    MCP_NAME = os.getenv("MCP_NAME") #nao completar com valor default, para forçar a configuração no .env
    MCP_HOST = os.getenv("MCP_HOST") #nao completar com valor default, para forçar a configuração no .env
    MCP_PORT = int(os.getenv("MCP_PORT")) #nao completar com valor default, para forçar a configuração no .env
    ENVIRONMENT = os.getenv("ENVIRONMENT") #nao completar com valor default, para forçar a configuração no .env