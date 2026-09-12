import html
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from mcp_client import call_mcp_tool, is_authorized


logger = logging.getLogger(__name__)

async def restart_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    services = os.getenv("DEPLOY_SERVICES").split(",")# nao completar com valor default, para forçar a configuração no .env
    keyboard = [
        [InlineKeyboardButton(service.strip(), callback_data=f"restart:{service.strip()}")]
        for service in services
        if service.strip()
    ]
    await update.message.reply_text(
        "Qual serviço deseja reiniciar?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def restart_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    if not query:
        return

    if not is_authorized(update):
        await query.answer("Acesso não autorizado.", show_alert=True)
        return

    await query.answer()
    service = query.data.removeprefix("restart:")
    await query.edit_message_text(f"🔄 Reiniciando {html.escape(service)}...")

    try:
        data = await call_mcp_tool(
            "restart_homelab_service",
            {"service": service},
        )
        if data.get("success"):
            message = f"✅ Serviço <b>{html.escape(service)}</b> reiniciado."
        else:
            error = html.escape(str(data.get("error", "Erro desconhecido")))
            message = f"❌ Falha ao reiniciar <b>{html.escape(service)}</b>:\n<code>{error}</code>"
        await query.edit_message_text(message, parse_mode="HTML")
    except Exception as exc:
        logger.exception("Erro ao reiniciar serviço")
        await query.edit_message_text(
            f"❌ Erro ao reiniciar o serviço:\n<code>{html.escape(str(exc))}</code>",
            parse_mode="HTML",
        )
