
import html
import logging

from mcp_client import call_mcp_tool, is_authorized
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

#-------------------------------- DEPLOY-FINANCE -----------------------------

async def deploy_finance_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    await update.message.reply_text("🔄 Atualizando o painel financeiro...")

    try:
        data = await call_mcp_tool("deploy_finance_app")
        if data.get("success"):
            message = "✅ <b>Painel financeiro atualizado</b>"
        else:
            error = html.escape(str(data.get("error", "Erro desconhecido")))
            message = f"❌ <b>Falha ao atualizar o painel financeiro</b>\n<code>{error}</code>"

        await update.message.reply_text(message, parse_mode="HTML")
    except Exception as exc:
        logger.exception("Erro ao atualizar o painel financeiro")
        await update.message.reply_text(
            f"❌ Erro ao atualizar o painel financeiro:\n<code>{html.escape(str(exc))}</code>",
            parse_mode="HTML",
        )

#-------------------------------- FINANCE ---------------------------------

def format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_finance_summary(data: dict) -> str:
    summary = data.get("summary", {})
    month = html.escape(str(data.get("month", "mês atual")))
    fallback = "" if data.get("is_current_month") else "\n<i>O mês atual ainda não está cadastrado; exibindo o último registro.</i>"
    rows = (
        ("Saldo anterior", "saldo_anterior"),
        ("Receita", "receita"),
        ("Ganho extra", "ganho_extra"),
        ("Despesas", "despesas"),
        ("Despesa extra", "extras"),
        ("Investimentos", "investimentos"),
        ("Saldo geral", "saldo"),
    )
    lines = [f"📊 <b>Resumo financeiro — {month}</b>", ""]
    lines.extend(f"• {label}: <b>{format_brl(float(summary.get(key, 0)))}</b>" for label, key in rows)
    return "\n".join(lines) + fallback


async def finance_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    try:
        data = await call_mcp_tool("get_current_finance_summary")
        if not data.get("success"):
            raise RuntimeError(data.get("error", "Erro desconhecido"))
        await update.message.reply_text(format_finance_summary(data), parse_mode="HTML")
    except Exception as exc:
        logger.exception("Erro ao consultar resumo financeiro")
        await update.message.reply_text(
            f"❌ Erro ao consultar o resumo financeiro:\n<code>{html.escape(str(exc))}</code>",
            parse_mode="HTML",
        )


#-------------------------------- FINANCE BACKUP --------------------------

async def finance_backup_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    await update.message.reply_text("💾 Iniciando backup financeiro...")

    try:
        data = await call_mcp_tool("start_finance_backup")
        if data.get("success"):
            output = html.escape(str(data.get("output", "")))
            message = "✅ <b>Backup financeiro concluído</b>"
            if output:
                message += f"\n<code>{output}</code>"
        else:
            error = html.escape(str(data.get("error", "Erro desconhecido")))
            message = f"❌ <b>Falha no backup financeiro</b>\n<code>{error}</code>"

        await update.message.reply_text(message, parse_mode="HTML")
    except Exception as exc:
        logger.exception("Erro ao executar backup financeiro")
        await update.message.reply_text(
            f"❌ Erro ao executar backup financeiro:\n<code>{html.escape(str(exc))}</code>",
            parse_mode="HTML",
        )
