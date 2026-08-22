from app.services.deploy import deploy, restart_service


def register_deploy_tools(mcp):
    @mcp.tool()
    def deploy_homelab() -> dict:
        """Atualiza o repositório do homelab com git pull."""
        return deploy()

    @mcp.tool()
    def restart_homelab_service(service: str) -> dict:
        """Reinicia um serviço permitido do homelab."""
        return restart_service(service)