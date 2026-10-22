from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import os
from contextlib import AsyncExitStack
from typing import Any

import httpx
from anthropic import Anthropic
from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client


SYSTEM_PROMPT = """You are the autonomous AIvikings domain registrar demo agent.

Use only the provided MCP tools to inspect, register, update, and confirm domains.
Prefer .com, .net, and .org candidates. Avoid a long-domain choice when a concise
available candidate fits the goal. Never claim registration or nameserver updates
succeeded until you have called get_domain_status after the change. Keep the final
answer short and human-readable."""


def _tool_schema(tool: Any) -> dict[str, Any]:
    schema = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None)
    if schema is None:
        schema = {"type": "object", "properties": {}}
    return {
        "name": tool.name,
        "description": tool.description or f"MCP tool {tool.name}",
        "input_schema": schema,
    }


def _content_block_to_message(block: Any) -> dict[str, Any]:
    if block.type == "text":
        return {"type": "text", "text": block.text}
    if block.type == "tool_use":
        return {
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input,
        }
    raise ValueError(f"Unsupported Claude content block type: {block.type}")


def _tool_result_payload(result: Any) -> Any:
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return structured
    if getattr(result, "content", None):
        first = result.content[0]
        if isinstance(first, types.TextContent):
            try:
                return json.loads(first.text)
            except json.JSONDecodeError:
                return first.text
    return {}


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, default=str))


async def run_agent(goal: str, *, max_turns: int) -> None:
    endpoint = os.environ.get("AIVIKINGS_MCP_ENDPOINT", "http://127.0.0.1:8081/mcp")
    mcp_api_key = os.environ.get("AIVIKINGS_MCP_API_KEY")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Set ANTHROPIC_API_KEY before running the Claude-driven demo agent.")
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    client = Anthropic(api_key=api_key)

    print("TRANSCRIPT")
    print(f"Goal: {goal}")
    print(f"MCP endpoint: {endpoint}")
    print()

    async with AsyncExitStack() as stack:
        client_kwargs: dict[str, Any] = {}
        if mcp_api_key:
            auth_headers = {"Authorization": f"Bearer {mcp_api_key}"}
            parameters = inspect.signature(streamable_http_client).parameters
            if "headers" in parameters:
                client_kwargs["headers"] = auth_headers
            elif "http_client" in parameters:
                http_client = await stack.enter_async_context(httpx.AsyncClient(headers=auth_headers))
                client_kwargs["http_client"] = http_client
            else:
                raise SystemExit(
                    "The installed MCP Python SDK cannot send Authorization headers. "
                    'Upgrade it with: python -m pip install --upgrade "mcp[cli]"'
                )

        async with streamable_http_client(endpoint, **client_kwargs) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                tools = [_tool_schema(tool) for tool in tools_response.tools]
                print("Discovered MCP tools:")
                for tool in tools:
                    print(f"- {tool['name']}: {tool['description']}")
                print()

                messages: list[dict[str, Any]] = [{"role": "user", "content": goal}]
                final_text = ""

                for turn in range(1, max_turns + 1):
                    print(f"Claude turn {turn}:")
                    message = client.messages.create(
                        model=model,
                        max_tokens=2048,
                        system=SYSTEM_PROMPT,
                        tools=tools,
                        messages=messages,
                    )
                    assistant_content = [_content_block_to_message(block) for block in message.content]
                    messages.append({"role": "assistant", "content": assistant_content})

                    tool_results: list[dict[str, Any]] = []
                    for block in message.content:
                        if block.type == "text":
                            final_text += block.text
                            print(block.text)
                        elif block.type == "tool_use":
                            print(f"Tool call: {block.name}")
                            print("Arguments:")
                            _print_json(block.input)
                            result = await session.call_tool(block.name, arguments=block.input)
                            payload = _tool_result_payload(result)
                            print("Result:")
                            _print_json(payload)
                            print()
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": json.dumps(payload, default=str),
                                }
                            )

                    if not tool_results:
                        print()
                        print("Final outcome:")
                        print(final_text.strip())
                        return

                    messages.append({"role": "user", "content": tool_results})

    raise SystemExit(f"Demo agent stopped after {max_turns} turns before a final answer.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Claude-driven MCP-only domain registrar demo agent.")
    parser.add_argument("goal", nargs="?", help="Natural-language goal for the autonomous agent.")
    parser.add_argument("--max-turns", type=int, default=8)
    args = parser.parse_args()
    goal = args.goal or (
        "Find an available domain for a project called 'nightowl analytics', "
        "register it for one year, and point it at ns1.example.net and ns2.example.net."
    )
    asyncio.run(run_agent(goal, max_turns=args.max_turns))
