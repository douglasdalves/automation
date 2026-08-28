import html
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

import config
from ai_client import AIProviderError, answer_homelab_question
from docker_handlers import (
    manage_docker_callback,
    restart_docker_command,
    start_docker_command,
    stop_docker_command,
)
from restart_handlers import (
    restart_callback, 
    restart_command
)

from mcp_client import call_mcp_tool, is_authorized


TELEGRAM_BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
MCP_URL = config.MCP_URL
TELEGRAM_ALLOWED_USER_ID = config.TELEGRAM_ALLOWED_USER_ID


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


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


async def deploy_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    await update.message.reply_text("🔄 Atualizando a aplicação...")

    try:
        data = await call_mcp_tool("deploy_homelab")
        if data.get("success"):
            message = "✅ <b>Aplicação atualizada</b>"
        else:
            error = html.escape(str(data.get("error", "Erro desconhecido")))
            message = f"❌ <b>Falha ao atualizar a aplicação</b>\n<code>{error}</code>"

        await update.message.reply_text(message, parse_mode="HTML")
    except Exception as exc:
        logger.exception("Erro ao atualizar a aplicação")
        await update.message.reply_text(
            f"❌ Erro ao atualizar a aplicação:\n<code>{html.escape(str(exc))}</code>",
            parse_mode="HTML",
        )


async def natural_language_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update) or not update.message or not update.message.text:
        return

    try:
        await update.message.chat.send_action("typing")
        answer = await answer_homelab_question(update.message.text)
        await update.message.reply_text(answer)
    except Exception as exc:
        logger.exception("Erro ao consultar a IA")
        if isinstance(exc, AIProviderError) and exc.status_code == 429:
            message = (
                "❌ A IA recusou a requisição por limite ou quota excedida. "
                "Verifique créditos, faturamento e limites da conta no provedor "
                f"configurado. Detalhe: {exc}"
            )
        else:
            message = (
                "❌ Não foi possível consultar a IA. "
                "Verifique AI_API_URL, AI_API_KEY, AI_MODEL e o provedor configurado. "
                f"({exc})"
            )
        await update.message.reply_text(
            message
        )


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN não configurado no arquivo .env.token"
        )

    application = Application.builder().token(
        TELEGRAM_BOT_TOKEN
    ).build()

    application.add_handler(
        CommandHandler("status", status_command)
    )
    application.add_handler(
        CommandHandler("deploy", deploy_command)
    )
    application.add_handler(
        CommandHandler("restart_service", restart_command)
    )
    application.add_handler(
        CommandHandler("restart_docker", restart_docker_command)
    )
    application.add_handler(
        CommandHandler("start_docker", start_docker_command)
    )
    application.add_handler(
        CommandHandler("stop_docker", stop_docker_command)
    )
    application.add_handler(
        CallbackQueryHandler(restart_callback, pattern=r"^restart:")
    )
    application.add_handler(
        CallbackQueryHandler(manage_docker_callback, pattern=r"^docker-(restart|start|stop):")
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, natural_language_command)
    )

    logger.info("NotApHome iniciado")
    logger.info("MCP: %s", MCP_URL)

    application.run_polling()


if __name__ == "__main__":
    main()