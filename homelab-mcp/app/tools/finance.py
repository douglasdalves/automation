import secrets

from app.config import Config
from app.services.finance import (
    get_current_month_accounts,
    get_current_month_investments,
    get_current_month_summary,
    set_month_fixed_account,
)
from app.services.finance_backup import run_finance_backup


def register_finance_tools(mcp):
    @mcp.tool()
    def get_current_finance_summary() -> dict:
        """Consulta no dashboard financeiro o resumo mensal do mês atual."""
        return get_current_month_summary()

    @mcp.tool()
    def get_current_finance_investments() -> dict:
        """Consulta no dashboard financeiro os investimentos do mês atual."""
        return get_current_month_investments()

    @mcp.tool()
    def get_current_finance_accounts() -> dict:
        """Consulta no dashboard as contas fixas e extras do mês atual."""
        return get_current_month_accounts()

    @mcp.tool()
    def set_current_finance_fixed_account(
        item: str,
        amount: float,
        write_token: str,
        month: str = "",
    ) -> dict:
        """Define o valor de uma conta fixa no mês indicado, mediante token."""
        if not Config.FINANCE_WRITE_TOKEN:
            return {
                "success": False,
                "error": "FINANCE_WRITE_TOKEN não está configurado no servidor MCP.",
            }
        if not isinstance(write_token, str) or not secrets.compare_digest(
            write_token.encode("utf-8"),
            Config.FINANCE_WRITE_TOKEN.encode("utf-8"),
        ):
            return {"success": False, "error": "Não autorizado."}
        return set_month_fixed_account(item, amount, month)

    @mcp.tool()
    def start_finance_backup() -> dict:
        """Executa o backup financeiro configurado, usando o mesmo script do cron."""
        return run_finance_backup()
