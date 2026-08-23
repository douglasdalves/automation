import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from telegram import Update

import config


async def call_mcp_tool(tool_name: str, arguments: dict | None = None):
    async with streamable_http_client(config.MCP_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments or {})

            if result.isError:
                raise RuntimeError(str(result))
            if not result.content:
                return None

            return json.loads(result.content[0].text)


def is_authorized(update: Update) -> bool:
    return bool(
        update.effective_user
        and update.effective_user.id == config.TELEGRAM_ALLOWED_USER_ID
    )
