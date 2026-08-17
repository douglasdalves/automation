from app.services.docker import inspect_container, list_containers, manage_container


def register_docker_tools(mcp):

    @mcp.tool()
    def list_docker_containers(all_containers: bool = False) -> dict:
        """Lista containers Docker ativos ou todos, incluindo ID, imagem, status e nome."""
        return list_containers(all_containers=all_containers)

    @mcp.tool()
    def inspect_docker_container(container_id: str) -> dict:
        """Retorna detalhes de um container Docker pelo ID ou nome."""
        return inspect_container(container_id)

    @mcp.tool()
    def manage_docker_container(container_id: str, action: str) -> dict:
        """Executa ações de ciclo de vida em um container Docker: start, stop, restart, kill ou remove."""
        return manage_container(container_id, action)
