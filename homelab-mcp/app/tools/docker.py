from app.services.docker import (
    inspect_container,
    list_compose_files,
    list_containers,
    manage_container,
    start_compose_file,
)


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

    @mcp.tool()
    def list_compose_files_in_dc_local() -> dict:
        """Lista os arquivos YAML válidos disponíveis na pasta dc-local para subir via docker compose."""
        return list_compose_files()

    @mcp.tool()
    def start_compose_file_in_dc_local(file_name: str) -> dict:
        """Inicia um compose YAML permitido dentro da pasta dc-local com sudo docker compose -f <arquivo> up -d."""
        return start_compose_file(file_name)
