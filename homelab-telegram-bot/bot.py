import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Carregar .env compartilhado em automation/.env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MCP_URL = os.getenv("MCP_URL")
TELEGRAM_ALLOWED_USER_ID = int(
    os.getenv("TELEGRAM_ALLOWED_USER_ID", "0")
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def call_mcp_tool(tool_name: str, arguments: dict | None = None):
    async with streamable_http_client(MCP_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments or {},
            )

            if result.isError:
                raise RuntimeError(str(result))

            if not result.content:
                return None

            text = result.content[0].text

            return json.loads(text)

#------ limitar uso a um usuário específico do Telegram ---#
def is_authorized(update: Update) -> bool:
    if not update.effective_user:
        return False

    return update.effective_user.id == TELEGRAM_ALLOWED_USER_ID
#----------------------------------------------------------#

def format_health(data: dict) -> str:
    cpu = data.get("cpu", {})
    memory = data.get("memory", {})
    disk = data.get("disk", {})
    uptime = data.get("uptime", {})
    docker = data.get("docker", {})

    temperature = cpu.get("temperature")
    cpu_usage = cpu.get("usage_percent")

    memory_percent = memory.get("percent")
    memory_used = memory.get("used_gb")
    memory_total = memory.get("total_gb")

    disk_percent = disk.get("percent")
    disk_used = disk.get("used_gb")
    disk_total = disk.get("total_gb")

    days = uptime.get("days", 0)
    hours = uptime.get("hours", 0)
    minutes = uptime.get("minutes", 0)

    containers = docker.get("running_containers", [])

    lines = [
        "🟢 <b>Raspberry Pi — Status</b>",
        "",
        "🌡️ <b>CPU</b>",
        f"• Uso: {cpu_usage}%",
        f"• Temperatura: {temperature}°C",
        "",
        "🧠 <b>Memória</b>",
        f"• Uso: {memory_percent}%",
        f"• Utilizada: {memory_used} / {memory_total} GB",
        "",
        "💾 <b>Disco</b>",
        f"• Uso: {disk_percent}%",
        f"• Utilizado: {disk_used} / {disk_total} GB",
        "",
        "⏱️ <b>Uptime</b>",
        f"• {days}d {hours}h {minutes}min",
        "",
        f"🐳 <b>Docker</b> — {len(containers)} containers ativos",
    ]

    for container in containers:
        name = container.get("name", "desconhecido")
        status = container.get("status", "")
        lines.append(f"• <code>{name}</code> — {status}")

    return "\n".join(lines)


async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await update.message.reply_text(
            "⛔ Acesso não autorizado."
        )
        return

    try:
        data = await call_mcp_tool("get_health")

        message = format_health(data)

        await update.message.reply_text(
            message,
            parse_mode="HTML",
        )

    except Exception as exc:
        logger.exception("Erro ao consultar MCP")

        await update.message.reply_text(
            f"❌ Erro ao consultar o MCP:\n<code>{exc}</code>",
            parse_mode="HTML",
        )


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN não configurado no arquivo .env"
        )

    application = Application.builder().token(
        TELEGRAM_BOT_TOKEN
    ).build()

    application.add_handler(
        CommandHandler("status", status_command)
    )

    logger.info("NotApHome iniciado")
    logger.info("MCP: %s", MCP_URL)

    application.run_polling()


if __name__ == "__main__":
    main()