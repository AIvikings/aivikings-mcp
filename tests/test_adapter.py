from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest
from mcp.server.fastmcp.exceptions import ToolError

from aivikings_mcp.client import BackendClient
from aivikings_mcp.config import Settings
from aivikings_mcp.server import build_mcp_server, create_app


def context(token="customer-token"):
    return SimpleNamespace(
        request_context=SimpleNamespace(
            request=SimpleNamespace(
                headers={
                    "authorization": f"Bearer {token}",
                    "x-agent-id": "agent-42",
                }
            )
        )
    )


async def test_tool_schemas_and_annotations_are_preserved():
    tools = {tool.name: tool for tool in await build_mcp_server().list_tools()}
    assert len(tools) == 34
    for name in ("check_domain_availability", "check_single_domain_availability"):
        tool = tools[name]
        assert tool.inputSchema["properties"]["depth"]["default"] == "confirm"
        assert (
            "Never tell the user a likely_available name is available"
            in tool.description
        )
        assert tool.annotations.readOnlyHint is True
        assert "ctx" not in tool.inputSchema["properties"]
    assert tools["register_domain"].annotations.readOnlyHint is False
    assert tools["get_domain_audit_log"].annotations.readOnlyHint is True
    assert tools["unlock_domain"].annotations.destructiveHint is True


async def test_bearer_and_agent_identity_forwarded_with_datetime_arguments():
    requests = []

    def backend(request):
        requests.append(request)
        return httpx.Response(200, json={"events": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(backend)) as client:
        api = BackendClient(Settings(_env_file=None), http_client=client)
        mcp = build_mcp_server(api=api)
        tool = mcp._tool_manager.get_tool("get_domain_audit_log")
        result = await tool.fn(
            ctx=context(), from_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc)
        )
    assert result == {"events": []}
    assert requests[0].headers["authorization"] == "Bearer customer-token"
    assert requests[0].headers["x-agent-id"] == "agent-42"
    assert requests[0].url.path == "/v1/mcp/tools/get_domain_audit_log"
    assert b"2026-01-01T00:00:00Z" in requests[0].content


@pytest.mark.parametrize("status", [302, 401, 403, 500])
async def test_errors_do_not_expose_private_backend_details(status):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                status, json={"message": "private upstream credentials"}
            )
        )
    ) as client:
        api = BackendClient(Settings(_env_file=None), http_client=client)
        with pytest.raises(ToolError) as error:
            await api.call("list_domains", context(), {})
    assert "private" not in str(error.value)
    assert str(status) in str(error.value)


async def test_discovery_challenge_and_authentication():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200 if request.headers.get("authorization") == "Bearer valid" else 401
            )
        )
    ) as backend:
        app = create_app(
            api=BackendClient(Settings(_env_file=None), http_client=backend)
        )
        async with app.app.router.lifespan_context(app.app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8081"
            ) as client:
                health = await client.get("/healthz")
                assert health.status_code == 200
                metadata = await client.get("/.well-known/oauth-protected-resource")
                assert metadata.json()["authorization_servers"] == [
                    "https://api.aivikings.ai"
                ]
                missing = await client.post(
                    "/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {"name": "list_domains"},
                    },
                )
                assert missing.status_code == 401
                assert "resource_metadata" in missing.headers["www-authenticate"]
                discovered = await client.post(
                    "/mcp",
                    headers={"Accept": "application/json, text/event-stream"},
                    json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                )
                assert discovered.status_code == 200
                assert len(discovered.json()["result"]["tools"]) == 34
                mixed_batch = await client.post(
                    "/mcp", json=[{"method": "tools/list"}, {"method": "tools/call"}]
                )
                assert mixed_batch.status_code == 401


async def test_tokens_remain_isolated_between_requests():
    tokens = []

    def backend(request):
        tokens.append(request.headers["authorization"])
        return httpx.Response(200, json={})

    async with httpx.AsyncClient(transport=httpx.MockTransport(backend)) as client:
        api = BackendClient(Settings(_env_file=None), http_client=client)
        await api.call("get_current_user", context("alice"), {})
        await api.call("get_current_user", context("bob"), {})
    assert tokens == ["Bearer alice", "Bearer bob"]
