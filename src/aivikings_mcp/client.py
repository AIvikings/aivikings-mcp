from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

import httpx
from mcp.server.fastmcp import Context
from mcp.server.fastmcp.exceptions import ToolError
from pydantic_core import to_jsonable_python

from .config import Settings


class BackendClient:
    def __init__(
        self, settings: Settings, *, http_client: httpx.AsyncClient | None = None
    ):
        self.settings = settings
        self.http_client = http_client

    @asynccontextmanager
    async def connection(self):
        if self.http_client is not None:
            yield self.http_client
        else:
            async with httpx.AsyncClient(
                timeout=self.settings.mcp_request_timeout_seconds
            ) as client:
                yield client

    async def request(
        self, method: str, path: str, *, headers: dict[str, str], **kwargs
    ) -> httpx.Response:
        # Never follow upstream redirects with a caller's bearer token.
        async with self.connection() as client:
            return await client.request(
                method,
                self.settings.api_base_url + "/v1/mcp/" + path,
                headers=headers,
                follow_redirects=False,
                **kwargs,
            )

    async def authenticate(self, headers: dict[str, str]) -> httpx.Response:
        return await self.request("GET", "auth", headers=headers)

    async def call(self, name: str, ctx: Context, arguments: dict[str, Any]) -> Any:
        request = ctx.request_context.request
        headers = {
            key: request.headers[key]
            for key in ("authorization", "x-agent-id", "x-agent-name", "user-agent")
            if key in request.headers
        }
        try:
            response = await self.request(
                "POST",
                "tools/" + name,
                headers=headers,
                json={"arguments": to_jsonable_python(arguments)},
            )
        except httpx.HTTPError:
            raise ToolError("AIvikings backend is temporarily unavailable.") from None
        if response.status_code >= 300:
            # Backend diagnostics can contain private provider information.
            raise ToolError(
                f"AIvikings rejected the operation (HTTP {response.status_code})."
            )
        try:
            return response.json()
        except ValueError:
            raise ToolError("AIvikings backend returned an invalid response.") from None
