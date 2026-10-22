from __future__ import annotations

import uvicorn
from mcp.server.fastmcp import FastMCP

from .auth import BackendBearerAuthMiddleware
from .client import BackendClient
from .config import Settings, get_settings
from .instructions import INSTRUCTIONS
from .tools import register_tools


def build_mcp_server(
    *, settings: Settings | None = None, api: BackendClient | None = None
) -> FastMCP:
    settings = settings or get_settings()
    mcp = FastMCP(
        "AIvikings AI Agent Registrar",
        instructions=INSTRUCTIONS,
        json_response=True,
        stateless_http=True,
        host=settings.mcp_host,
        port=settings.mcp_port,
        streamable_http_path=settings.mcp_path,
    )
    register_tools(mcp, api or BackendClient(settings))
    return mcp


def create_app(settings: Settings | None = None, *, api: BackendClient | None = None):
    settings = settings or get_settings()
    api = api or BackendClient(settings)
    mcp = build_mcp_server(settings=settings, api=api)
    return BackendBearerAuthMiddleware(mcp.streamable_http_app(), api)


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        create_app(settings),
        host=settings.mcp_host,
        port=settings.mcp_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
