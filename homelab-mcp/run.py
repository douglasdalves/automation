import uvicorn

from app.config import Config


if __name__ == "__main__":
    uvicorn.run(
        "app.server:app",
        host=Config.MCP_HOST,
        port=Config.MCP_PORT,
        reload=Config.ENVIRONMENT == "development",
    )