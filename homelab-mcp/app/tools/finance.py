from app.services.finance import (
    get_current_month_accounts,
    get_current_month_investments,
    get_current_month_summary,
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
    def start_finance_backup() -> dict:
        """Executa o backup financeiro configurado, usando o mesmo script do cron."""
        return run_finance_backup()
