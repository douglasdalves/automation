import html
import logging
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from secrets import token_hex

import config
from mcp_client import call_mcp_tool, is_authorized
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)
_FIXED_ACCOUNT_PENDING_KEY = "pending_fixed_account"
_FIXED_AMOUNT_PATTERN = re.compile(
    r"^(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{1,2})?$|^\d+(?:\.\d{1,2})?$"
)
_FINANCE_MONTHS = (
    "jan",
    "fev",
    "mar",
    "abr",
    "mai",
    "jun",
    "jul",
    "ago",
    "set",
    "out",
    "nov",
    "dez",
)
_FINANCE_MONTH_PATTERN = re.compile(r"^([a-z]{3})/(\d{2}|\d{4})$", re.IGNORECASE)

# -------------------------------- DEPLOY-FINANCE -----------------------------


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


# -------------------------------- FINANCE ---------------------------------


def format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_finance_summary(data: dict) -> str:
    summary = data.get("summary", {})
    month = html.escape(str(data.get("month", "mês atual")))
    fallback = (
        ""
        if data.get("is_current_month")
        else "\n<i>O mês atual ainda não está cadastrado; exibindo o último registro até o mês atual.</i>"
    )
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
    lines.extend(
        f"• {label}: <b>{format_brl(float(summary.get(key, 0)))}</b>"
        for label, key in rows
    )
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


async def finance_invest_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    try:
        data = await call_mcp_tool("get_current_finance_investments")
        if not data.get("success"):
            raise RuntimeError(data.get("error", "Erro desconhecido"))

        month = html.escape(str(data.get("month", "mês atual")))
        fallback = (
            ""
            if data.get("is_current_month")
            else "\n<i>O mês atual ainda não está cadastrado; exibindo o último registro até o mês atual.</i>"
        )
        lines = [f"📈 <b>Investimentos por item — {month}</b>", ""]
        items = data.get("items", [])
        if items:
            lines.extend(
                f"• {html.escape(str(item.get('item', 'Investimento')))}: <b>{format_brl(float(item.get('valor') or 0))}</b>"
                for item in items
            )
        else:
            lines.append("Nenhum investimento detalhado cadastrado neste mês.")
        lines.extend(["", f"Total: <b>{format_brl(float(data.get('total') or 0))}</b>"])
        await update.message.reply_text("\n".join(lines) + fallback, parse_mode="HTML")
    except Exception as exc:
        logger.exception("Erro ao consultar investimentos financeiros")
        await update.message.reply_text(
            f"❌ Erro ao consultar investimentos financeiros:\n<code>{html.escape(str(exc))}</code>",
            parse_mode="HTML",
        )


async def finance_contas_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    try:
        data = await call_mcp_tool("get_current_finance_accounts")
        if not data.get("success"):
            raise RuntimeError(data.get("error", "Erro desconhecido"))

        month = html.escape(str(data.get("month", "mês atual")))
        fallback = (
            ""
            if data.get("is_current_month")
            else "\n<i>O mês atual ainda não está cadastrado; exibindo o último registro até o mês atual.</i>"
        )
        lines = [f"🧾 <b>Contas mensais — {month}</b>", ""]

        sections = (
            ("Contas fixas", "fixed_items", "fixed_total"),
            ("Contas extras", "extra_items", "extras_total"),
        )
        for title, items_key, total_key in sections:
            lines.append(f"<b>{title}</b>")
            items = data.get(items_key, [])
            if items:
                lines.extend(
                    f"• {html.escape(str(item.get('item', 'Conta')))}: <b>{format_brl(float(item.get('valor') or 0))}</b>"
                    for item in items
                )
            else:
                lines.append("Nenhum item cadastrado.")
            lines.append(
                f"Subtotal: <b>{format_brl(float(data.get(total_key) or 0))}</b>"
            )
            lines.append("")

        await update.message.reply_text(
            "\n".join(lines).rstrip() + fallback, parse_mode="HTML"
        )
    except Exception as exc:
        logger.exception("Erro ao consultar contas financeiras")
        await update.message.reply_text(
            f"❌ Erro ao consultar contas financeiras:\n<code>{html.escape(str(exc))}</code>",
            parse_mode="HTML",
        )


def parse_fixed_account_amount(value: str) -> Decimal:
    """Parse Brazilian or dot-decimal currency input with at most two decimals."""
    if not _FIXED_AMOUNT_PATTERN.fullmatch(value):
        raise ValueError("Use um valor com até duas casas decimais.")

    normalized = value.replace(".", "").replace(",", ".") if "," in value else value
    try:
        amount = Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError("O valor informado é inválido.") from exc

    if not amount.is_finite() or amount <= 0:
        raise ValueError("O valor deve ser maior que zero.")
    return amount


def parse_fixed_account_month(value: str) -> str:
    match = _FINANCE_MONTH_PATTERN.fullmatch(value)
    if not match or match.group(1).lower() not in _FINANCE_MONTHS:
        raise ValueError("Use o mês no formato Mmm/aa, por exemplo Nov/26.")

    month_name, year_text = match.groups()
    year = int(year_text)
    if len(year_text) == 2:
        year += 2000
    if year < 2000 or year > 2099:
        raise ValueError("O ano deve estar entre 2000 e 2099.")
    return f"{month_name.lower().capitalize()}/{year % 100:02d}"


async def finance_fixed_account_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    if not config.FINANCE_WRITE_TOKEN:
        await update.message.reply_text(
            "❌ Lançamento indisponível: FINANCE_WRITE_TOKEN não está configurado."
        )
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Use /conta_fixa <nome> <valor> [mês/ano]\n"
            "Exemplos:\n"
            "• /conta_fixa luz 120,50\n"
            "• /conta_fixa luz 120,50 Nov/26"
        )
        return

    args = list(context.args)
    today = datetime.now().astimezone()
    month = f"{_FINANCE_MONTHS[today.month - 1].capitalize()}/{today:%y}"
    if "/" in args[-1]:
        try:
            month = parse_fixed_account_month(args.pop())
        except ValueError as exc:
            await update.message.reply_text(f"❌ {html.escape(str(exc))}")
            return
        if len(args) < 2:
            await update.message.reply_text(
                "Informe o nome da conta e o valor antes do mês."
            )
            return

    item = " ".join(args[:-1]).strip()
    if not item or len(item) > 100:
        await update.message.reply_text(
            "❌ Informe o nome da conta (até 100 caracteres) e o valor."
        )
        return

    try:
        amount = parse_fixed_account_amount(args[-1])
    except ValueError as exc:
        await update.message.reply_text(f"❌ {html.escape(str(exc))}")
        return

    confirmation_id = token_hex(8)
    context.user_data[_FIXED_ACCOUNT_PENDING_KEY] = {
        "id": confirmation_id,
        "item": item,
        "amount": float(amount),
        "month": month,
    }
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Confirmar",
                    callback_data=f"finance-fixed:confirm:{confirmation_id}",
                ),
                InlineKeyboardButton(
                    "Cancelar",
                    callback_data=f"finance-fixed:cancel:{confirmation_id}",
                ),
            ]
        ]
    )
    await update.message.reply_text(
        f"Confirma definir a conta fixa abaixo para <b>{html.escape(month)}</b>?\n"
        f"• Item: <b>{html.escape(item)}</b>\n"
        f"• Valor: <b>{format_brl(float(amount))}</b>\n\n"
        "<i>Se o item já existir, o valor atual do mês será substituído.</i>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def finance_fixed_account_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    if not query:
        return

    if not is_authorized(update):
        await query.answer("Acesso não autorizado.", show_alert=True)
        return

    _, action, confirmation_id = query.data.split(":", 2)
    pending = context.user_data.get(_FIXED_ACCOUNT_PENDING_KEY)
    if not pending or pending.get("id") != confirmation_id:
        await query.answer("Este lançamento não está mais pendente.", show_alert=True)
        return

    await query.answer()
    if action == "cancel":
        context.user_data.pop(_FIXED_ACCOUNT_PENDING_KEY, None)
        await query.edit_message_text("Lançamento cancelado.")
        return

    await query.edit_message_text("🔄 Registrando a conta fixa...")
    context.user_data.pop(_FIXED_ACCOUNT_PENDING_KEY, None)
    try:
        data = await call_mcp_tool(
            "set_current_finance_fixed_account",
            {
                "item": pending["item"],
                "amount": pending["amount"],
                "month": pending["month"],
                "write_token": config.FINANCE_WRITE_TOKEN,
            },
        )
        if not data.get("success"):
            raise RuntimeError(data.get("error", "Erro desconhecido"))

        month = html.escape(str(data.get("month", "mês atual")))
        item = html.escape(str(data.get("item", pending["item"])))
        amount = float(data.get("amount", pending["amount"]))
        await query.edit_message_text(
            f"✅ Conta fixa registrada para <b>{month}</b>\n"
            f"• {item}: <b>{format_brl(amount)}</b>",
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.exception("Erro ao registrar conta fixa")
        await query.edit_message_text(
            "❌ Não foi possível registrar a conta fixa:\n"
            f"<code>{html.escape(str(exc))}</code>",
            parse_mode="HTML",
        )


# -------------------------------- FINANCE BACKUP --------------------------


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
