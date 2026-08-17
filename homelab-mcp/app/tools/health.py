from app.services.health import health_check


def register_health_tools(mcp):

    @mcp.tool()
    def get_health() -> dict:
        """Retorna informações de saúde do Raspberry Pi."""
        return health_check()