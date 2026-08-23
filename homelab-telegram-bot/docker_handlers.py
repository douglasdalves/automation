import html
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from mcp_client import call_mcp_tool, is_authorized


logger = logging.getLogger(__name__)


async def restart_docker_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_docker_containers(update, "restart")


async def start_docker_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_docker_containers(update, "start")


async def stop_docker_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_docker_containers(update, "stop")


async def show_docker_containers(update: Update, action: str):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    try:
        data = await call_mcp_tool(
            "list_docker_containers",
            {"all_containers": action != "restart"},
        )
        if not data.get("success"):
            await update.message.reply_text(
                f"❌ Erro ao listar containers: <code>{html.escape(str(data.get('error', 'Erro desconhecido')))}</code>",
                parse_mode="HTML",
            )
            return

        containers = data.get("containers", [])
        if not containers:
            await update.message.reply_text("❌ Nenhum container encontrado.")
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    container.get("name", container.get("id", "desconhecido")),
                    callback_data=f"docker-{action}:{container['id']}",
                )
            ]
            for container in containers
            if container.get("id")
        ]
        await update.message.reply_text(
            f"Qual container deseja {action}?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception as exc:
        logger.exception("Erro ao listar containers Docker")
        await update.message.reply_text(
            f"❌ Erro ao listar containers: <code>{html.escape(str(exc))}</code>",
            parse_mode="HTML",
        )


async def manage_docker_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    if not is_authorized(update):
        await query.answer("Acesso nao autorizado.", show_alert=True)
        return

    action, container_id = query.data.removeprefix("docker-").split(":", 1)
    labels = {"restart": "reiniciando", "start": "iniciando", "stop": "parando"}
    await query.answer()
    await query.edit_message_text(
        f"🔄 {labels[action].capitalize()} container <code>{html.escape(container_id)}</code>...",
        parse_mode="HTML",
    )

    try:
        data = await call_mcp_tool(
            "manage_docker_container",
            {"container_id": container_id, "action": action},
        )
        if data.get("success"):
            message = f"✅ Container <code>{html.escape(container_id)}</code>: {action} concluido."
        else:
            message = f"❌ Falha ao executar {action}: <code>{html.escape(str(data.get('error', 'Erro desconhecido')))}</code>"
        await query.edit_message_text(message, parse_mode="HTML")
    except Exception as exc:
        logger.exception("Erro ao gerenciar container Docker")
        await query.edit_message_text(
            f"❌ Erro ao executar {action}: <code>{html.escape(str(exc))}</code>",
            parse_mode="HTML",
        )
