"""Authenticate against the backend; no database or signing secret is needed here."""

from __future__ import annotations

import json
from urllib.parse import urlsplit

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse

from .client import BackendClient

PUBLIC_METHODS = {"initialize", "tools/list", "ping", "notifications/initialized"}


class BackendBearerAuthMiddleware:
    def __init__(self, app, api: BackendClient):
        self.app = app
        self.api = api

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope["path"]
        if path == "/healthz":
            await JSONResponse({"status": "ok"})(scope, receive, send)
            return
        if (
            path == "/.well-known/oauth-protected-resource"
            or path
            == "/.well-known/oauth-protected-resource" + self.api.settings.mcp_path
        ):
            await JSONResponse(
                {
                    "resource": self.api.settings.mcp_url,
                    "authorization_servers": [self.api.settings.public_api_base_url],
                    "scopes_supported": self.api.settings.oauth_scopes.split(),
                    "bearer_methods_supported": ["header"],
                }
            )(scope, receive, send)
            return

        request = Request(scope)
        authorization = request.headers.get("authorization", "")
        if authorization:
            try:
                response = await self.api.authenticate({"authorization": authorization})
            except httpx.HTTPError:
                response = None
            if response is not None and response.status_code == 200:
                await self.app(scope, receive, send)
                return
            if response is None or response.status_code not in {401, 403}:
                await JSONResponse({"error": "backend_unavailable"}, status_code=503)(
                    scope, receive, send
                )
                return

        # Only discovery and initialization may be anonymous, including JSON-RPC batches.
        messages = []
        body = bytearray()
        if scope["method"] == "POST":
            while True:
                message = await receive()
                messages.append(message)
                body.extend(message.get("body", b""))
                if len(body) > 1_048_576:
                    await JSONResponse({"error": "request_too_large"}, status_code=413)(
                        scope, receive, send
                    )
                    return
                if message["type"] != "http.request" or not message.get(
                    "more_body", False
                ):
                    break
            try:
                payload = json.loads(body)
                calls = payload if isinstance(payload, list) else [payload]
                discovery = bool(calls) and all(
                    isinstance(call, dict) and call.get("method") in PUBLIC_METHODS
                    for call in calls
                )
            except (ValueError, TypeError):
                discovery = False
            if discovery:

                async def replay():
                    return messages.pop(0) if messages else await receive()

                await self.app(scope, replay, send)
                return

        parsed = urlsplit(self.api.settings.mcp_url)
        metadata = (
            f"{parsed.scheme}://{parsed.netloc}/.well-known/oauth-protected-resource"
        )
        await JSONResponse(
            {
                "error": "unauthorized",
                "message": "MCP tools require a valid AIvikings bearer token.",
            },
            status_code=401,
            headers={
                "WWW-Authenticate": f'Bearer resource_metadata="{metadata}", scope="{self.api.settings.oauth_scopes}"'
            },
        )(scope, receive, send)
