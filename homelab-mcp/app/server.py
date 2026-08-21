from mcp.server.fastmcp import FastMCP

from app.config import Config
from app.tools.deploy import register_deploy_tools
from app.tools.docker import register_docker_tools
from app.tools.health import register_health_tools

mcp = FastMCP(
    Config.MCP_NAME,
    host=Config.MCP_HOST,
    port=Config.MCP_PORT,
    #transport_security=security,
)

register_health_tools(mcp)
register_docker_tools(mcp)
register_deploy_tools(mcp)

app = mcp.streamable_http_app()