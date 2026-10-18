import html
import logging

import config
from ai_client import AIProviderError, answer_homelab_question
from handlers.docker_handlers import (
    create_compose_callback,
    create_compose_command,
    manage_docker_callback,
    restart_docker_command,
    start_docker_command,
    stop_docker_command,
)
from handlers.finance_handlers import (
    deploy_finance_command,
    finance_backup_command,
    finance_command,
    finance_contas_command,
    finance_fixed_account_callback,
    finance_fixed_account_command,
    finance_invest_command,
)
from handlers.restart_handlers import restart_callback, restart_command
from mcp_client import call_mcp_tool, is_authorized
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# -------------------------------- CONFIG ---------------------------------

TELEGRAM_BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
MCP_URL = config.MCP_URL
TELEGRAM_ALLOWED_USER_ID = config.TELEGRAM_ALLOWED_USER_ID


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

BOT_COMMANDS = {
    "status": "status do sistema",
    "diagnostico": "diagnóstico de serviços, containers, configurações e backup",
    "deploy": "deploy da aplicação",
    "deploy_sync": "sincroniza arquivos configurados",
    "deploy_finance": "deploy do painel financeiro",
    "finance": "resumo financeiro do mês atual",
    "finance_invest": "investimentos do mês atual",
    "finance_contas": "contas fixas e extras do mês atual",
    "conta_fixa": "lança ou atualiza o valor mensal de uma conta fixa",
    "finance_bkp": "executa backup financeiro",
    "restart_service": "reinicia serviço do homelab",
    "restart_docker": "reinicia container Docker",
    "start_docker": "inicia container Docker",
    "stop_docker": "para container Docker",
    "create_docker": "cria container via compose",
    "options": "lista todos os comandos",
}


# -------------------------------- STATUS ---------------------------------


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
        await update.message.reply_text("⛔ Acesso não autorizado.")
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


async def diagnostic_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    await update.message.reply_text("🔎 Verificando o homelab...")
    try:
        data = await call_mcp_tool("get_homelab_diagnostics")
        status_icons = {"ok": "✅", "warning": "⚠️", "error": "❌", "unknown": "❔"}
        overall_status = data.get("status", "unknown")
        bot_config = [
            ("TELEGRAM_BOT_TOKEN", bool(config.TELEGRAM_BOT_TOKEN)),
            ("TELEGRAM_ALLOWED_USER_ID", config.TELEGRAM_ALLOWED_USER_ID > 0),
            ("MCP_URL", bool(config.MCP_URL)),
        ]
        if not all(configured for _, configured in bot_config):
            overall_status = "error"

        lines = [
            (
                f"{status_icons.get(overall_status, '❔')} "
                f"<b>Diagnóstico do homelab</b> — {html.escape(overall_status)}"
            ),
            "",
            "<b>Configurações MCP</b>",
        ]
        for item in data.get("configuration", []):
            status = item.get("status", "unknown")
            detail = html.escape(str(item.get("detail", "")))
            name = html.escape(str(item.get("name", "configuração")))
            lines.append(
                f"• {status_icons.get(status, '❔')} <code>{name}</code>: {detail}"
            )

        lines.extend(["", "<b>Serviços</b>"])
        services = data.get("services", [])
        if services:
            for item in services:
                status = item.get("status", "unknown")
                name = html.escape(str(item.get("name", "serviço")))
                detail = html.escape(str(item.get("detail", "")))
                lines.append(
                    f"• {status_icons.get(status, '❔')} <code>{name}</code>: {detail}"
                )
        else:
            lines.append("• ⚠️ Nenhum serviço configurado para deploy.")

        docker = data.get("docker", {})
        docker_status = docker.get("status", "unknown")
        lines.extend(
            [
                "",
                "<b>Containers Docker</b>",
                (
                    f"• {status_icons.get(docker_status, '❔')} "
                    f"{docker.get('running', 0)} ativos, "
                    f"{docker.get('stopped', 0)} parados"
                ),
            ]
        )
        if docker_status == "error":
            lines.append(
                "• "
                f"{html.escape(str(docker.get('detail', 'Falha ao consultar Docker.')))}"
            )
        for container in docker.get("containers", []):
            name = html.escape(str(container.get("name", "desconhecido")))
            state = html.escape(str(container.get("status", "desconhecido")))
            lines.append(f"  - <code>{name}</code>: {state}")

        backup = data.get("backup", {})
        backup_status = backup.get("status", "unknown")
        lines.extend(
            [
                "",
                "<b>Backup financeiro</b>",
                (
                    f"• {status_icons.get(backup_status, '❔')} "
                    f"{html.escape(str(backup.get('detail', 'Sem informação.')))}"
                ),
            ]
        )
        if backup.get("timestamp"):
            lines.append(
                f"• Último arquivo: <code>{html.escape(str(backup.get('last_file', '')))}</code>"
            )
            lines.append(
                f"• Data (UTC): {html.escape(str(backup['timestamp']))} "
                f"({backup.get('age_hours')} h)"
            )

        lines.extend(["", "<b>Configurações do bot</b>"])
        for name, configured in bot_config:
            icon = "✅" if configured else "❌"
            lines.append(
                f"• {icon} <code>{name}</code>: "
                f"{'configurada' if configured else 'ausente'}"
            )
        ai_configured = bool(
            config.AI_API_URL and config.AI_API_KEY and config.AI_MODEL
        )
        lines.append(
            f"• {'✅' if ai_configured else 'ℹ️'} <code>IA</code>: "
            f"{'configurada' if ai_configured else 'não configurada (opcional)'}"
        )

        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    except Exception as exc:
        logger.exception("Erro ao executar diagnóstico do homelab")
        await update.message.reply_text(
            "❌ Não foi possível concluir o diagnóstico:\n"
            f"<code>{html.escape(str(exc))}</code>",
            parse_mode="HTML",
        )


# -------------------------------- DEPLOY ---------------------------------


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


async def deploy_sync_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    await update.message.reply_text("🔄 Sincronizando arquivos configurados...")

    try:
        data = await call_mcp_tool("deploy_sync")
        if data.get("success"):
            message = "✅ <b>Arquivos sincronizados</b>"
        else:
            error = html.escape(str(data.get("error", "Erro desconhecido")))
            message = (
                f"❌ <b>Falha ao sincronizar os arquivos</b>\n<code>{error}</code>"
            )

        await update.message.reply_text(message, parse_mode="HTML")
    except Exception as exc:
        logger.exception("Erro ao sincronizar os arquivos")
        await update.message.reply_text(
            f"❌ Erro ao sincronizar os arquivos:\n<code>{html.escape(str(exc))}</code>",
            parse_mode="HTML",
        )


# -------------------------------- OPTIONS ---------------------------------


async def options_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    commands = "\n".join(
        f"• /{command} — {description}" for command, description in BOT_COMMANDS.items()
    )
    await update.message.reply_text(
        "<b>Opções disponíveis</b>\n\n" + commands,
        parse_mode="HTML",
    )


# -------------------------------- IA ---------------------------------


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
        await update.message.reply_text(message)


# -------------------------------- BOT ---------------------------------


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado no arquivo .env.token")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    for command_name in BOT_COMMANDS:
        if command_name == "options":
            application.add_handler(CommandHandler("options", options_command))
            continue
        if command_name == "status":
            application.add_handler(CommandHandler("status", status_command))
        elif command_name == "diagnostico":
            application.add_handler(CommandHandler("diagnostico", diagnostic_command))
        elif command_name == "deploy":
            application.add_handler(CommandHandler("deploy", deploy_command))
        elif command_name == "deploy_sync":
            application.add_handler(CommandHandler("deploy_sync", deploy_sync_command))
        elif command_name == "deploy_finance":
            application.add_handler(
                CommandHandler("deploy_finance", deploy_finance_command)
            )
        elif command_name == "finance":
            application.add_handler(CommandHandler("finance", finance_command))
        elif command_name == "finance_invest":
            application.add_handler(
                CommandHandler("finance_invest", finance_invest_command)
            )
        elif command_name == "finance_contas":
            application.add_handler(
                CommandHandler("finance_contas", finance_contas_command)
            )
        elif command_name == "conta_fixa":
            application.add_handler(
                CommandHandler("conta_fixa", finance_fixed_account_command)
            )
        elif command_name == "finance_bkp":
            application.add_handler(
                CommandHandler("finance_bkp", finance_backup_command)
            )
        elif command_name == "restart_service":
            application.add_handler(CommandHandler("restart_service", restart_command))
        elif command_name == "restart_docker":
            application.add_handler(
                CommandHandler("restart_docker", restart_docker_command)
            )
        elif command_name == "start_docker":
            application.add_handler(
                CommandHandler("start_docker", start_docker_command)
            )
        elif command_name == "stop_docker":
            application.add_handler(CommandHandler("stop_docker", stop_docker_command))
        elif command_name == "create_docker":
            application.add_handler(
                CommandHandler("create_docker", create_compose_command)
            )

    application.add_handler(
        CallbackQueryHandler(restart_callback, pattern=r"^restart:")
    )
    application.add_handler(
        CallbackQueryHandler(
            manage_docker_callback, pattern=r"^docker-(restart|start|stop):"
        )
    )
    application.add_handler(
        CallbackQueryHandler(create_compose_callback, pattern=r"^compose:start:")
    )
    application.add_handler(
        CallbackQueryHandler(
            finance_fixed_account_callback,
            pattern=r"^finance-fixed:(confirm|cancel):[a-f0-9]{16}$",
        )
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, natural_language_command)
    )

    logger.info("NotApHome iniciado")
    logger.info("MCP: %s", MCP_URL)

    application.run_polling()


if __name__ == "__main__":
    main()
