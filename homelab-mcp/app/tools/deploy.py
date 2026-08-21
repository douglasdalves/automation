from app.services.deploy import deploy


def register_deploy_tools(mcp):
    @mcp.tool()
    def deploy_homelab() -> dict:
        """Atualiza o repositório do homelab com git pull."""
        return deploy()