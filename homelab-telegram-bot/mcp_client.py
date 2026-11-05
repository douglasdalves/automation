from __future__ import annotations

import json

import config
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from telegram import Update


def _connection_error() -> RuntimeError:
    return RuntimeError(
        "Não foi possível conectar ao servidor MCP. Verifique se o serviço "
        "homelab-mcp está ativo e se MCP_URL aponta para o host e a porta "
        "corretos. O backup não foi iniciado."
    )


async def call_mcp_tool(tool_name: str, arguments: dict | None = None):
    try:
        async with streamable_http_client(config.MCP_URL) as (  # noqa: SIM117 - Parenthesized context managers require Python 3.9.
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments or {})

                if result.isError:
                    raise RuntimeError(str(result))
                if not result.content:
                    return None

                return json.loads(result.content[0].text)
    except httpx.ConnectError as exc:
        raise _connection_error() from exc


async def list_mcp_tools():
    try:
        async with streamable_http_client(config.MCP_URL) as (  # noqa: SIM117 - Parenthesized context managers require Python 3.9.
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                return result.tools
    except httpx.ConnectError as exc:
        raise _connection_error() from exc


def is_authorized(update: Update) -> bool:
    return bool(
        update.effective_user
        and update.effective_user.id == config.TELEGRAM_ALLOWED_USER_ID
    )
