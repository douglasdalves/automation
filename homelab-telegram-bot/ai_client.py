import json
import logging
import httpx

from mcp_client import call_mcp_tool, list_mcp_tools
import config


logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Voce e o assistente do homelab. Responda em portugues, de forma curta e objetiva.
Use as ferramentas MCP quando a pergunta envolver o estado ou uma acao no homelab.
Nao invente resultados: depois de usar uma ferramenta, baseie a resposta no retorno dela.
Se uma ferramenta falhar, explique o erro claramente.
"""


def _tool_definition(tool) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "Ferramenta do homelab",
            "parameters": tool.inputSchema or {"type": "object", "properties": {}},
        },
    }


async def _chat(messages: list[dict], tools: list[dict]) -> dict:
    headers = {"Authorization": f"Bearer {config.AI_API_KEY}"}
    payload = {
        "model": config.AI_MODEL,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
    }
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            f"{config.AI_API_URL.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()


async def answer_homelab_question(question: str) -> str:
    mcp_tools = await list_mcp_tools()
    tools = [_tool_definition(tool) for tool in mcp_tools]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for _ in range(5):
        result = await _chat(messages, tools)
        message = result["choices"][0]["message"]
        tool_calls = message.get("tool_calls") or []
        messages.append(message)

        if not tool_calls:
            return message.get("content") or "Nao consegui gerar uma resposta."

        for tool_call in tool_calls:
            function = tool_call["function"]
            arguments = json.loads(function.get("arguments") or "{}")
            try:
                tool_result = await call_mcp_tool(function["name"], arguments)
            except Exception as exc:
                logger.exception("Erro ao chamar tool MCP pela IA")
                tool_result = {"success": False, "error": str(exc)}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            )

    return "A IA atingiu o limite de chamadas de ferramentas nesta pergunta."