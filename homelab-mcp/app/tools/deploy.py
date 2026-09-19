from app.services.deploy import (
    deploy,
    deploy_finance,
    restart_service,
    sync_app_configs,
)


def register_deploy_tools(mcp):
    @mcp.tool()
    def deploy_homelab() -> dict:
        """Atualiza o repositório do homelab com git pull."""
        return deploy()

    @mcp.tool()
    def deploy_finance_app() -> dict:
        """Atualiza o repositorio e reinicia os containers da aplicacao financeira."""
        return deploy_finance()

    @mcp.tool()
    def deploy_sync() -> dict:
        """Sincroniza os arquivos definidos no app-config-sync sem deploy completo."""
        return sync_app_configs()

    @mcp.tool()
    def restart_homelab_service(service: str) -> dict:
        """Reinicia um serviço permitido do homelab."""
        return restart_service(service)
