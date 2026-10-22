# AIvikings MCP

Public Streamable HTTP MCP adapter for the AIvikings registrar REST API.
The 34 existing tools retain their parameter schemas, descriptions and safety
annotations, and call the backend over HTTP. The backend owns business logic,
authentication, customer isolation, scopes, provider access and audit persistence.

This repository contains no registrar backend, database models, provider adapters,
frontend assets, internal runbooks or production environment files. It installs
and builds without access to either private repository.

## Run locally

Requires Python 3.12+ and a running AIvikings backend exposing `/v1/mcp`.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
# Configure AIVIKINGS_API_BASE_URL to reach the backend.
aivikings-mcp
```

The endpoint is `http://127.0.0.1:8081/mcp`. Clients send their own AIvikings
bearer API key or OAuth access token. The adapter verifies it through the backend
and forwards it with each tool call. There is no privileged fallback token.
Token revocation and customer/scope checks stay authoritative in the backend.
Anonymous initialize, tools/list and ping discovery remain available.

`GET /healthz` is a local process health check, not an upstream readiness check.
`/.well-known/oauth-protected-resource` advertises the public backend as the
OAuth authorization server. `AIVIKINGS_API_BASE_URL` is an internal HTTP address;
`AIVIKINGS_PUBLIC_API_BASE_URL` and `AIVIKINGS_MCP_URL` must be externally reachable
for real OAuth clients. OAuth issuance and signing secrets remain in the backend.

## Docker

```bash
docker compose up --build
```

The standalone Compose default reaches the backend's published port 8080 using
`host.docker.internal`. Set the upstream/public URLs for your deployment.
If you copy `.env.example` first, replace its localhost upstream with an address
reachable from inside the container. No private source checkout is mounted.

## Tests

```bash
pytest
```

Tests use a simulated HTTP backend and exercise discovery, bearer challenges,
per-request identity, tool schemas and error sanitization without a database.
Backend rejection is returned as an HTTP-status tool error; private upstream
response bodies are not exposed to MCP clients. Review backend logs for details.

The optional Claude demonstration client is installed with
`python -m pip install -e ".[demo]"`; configure its client-side
`ANTHROPIC_API_KEY` and `AIVIKINGS_MCP_API_KEY` before `aivikings-demo-agent`.
Its sample transcript in `examples/` is historical and illustrative.
