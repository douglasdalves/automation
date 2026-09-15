from app.services.finance import get_current_month_summary


def register_finance_tools(mcp):
    @mcp.tool()
    def get_current_finance_summary() -> dict:
        """Consulta no dashboard financeiro o resumo mensal do mês atual."""
        return get_current_month_summary()
