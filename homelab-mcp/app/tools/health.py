from app.services.diagnostics import homelab_diagnostics
from app.services.health import health_check


def register_health_tools(mcp):

    @mcp.tool()
    def get_health() -> dict:
        """Retorna informações de saúde do Raspberry Pi."""
        return health_check()

    @mcp.tool()
    def get_homelab_diagnostics() -> dict:
        """Verifica configurações, serviços, containers e o backup financeiro recente."""
        return homelab_diagnostics()
