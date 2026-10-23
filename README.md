# AiVikings.ai MCP Server (official)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/AIvikings/aivikings-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/AIvikings/aivikings-mcp/actions/workflows/ci.yml)

The official [Model Context Protocol](https://modelcontextprotocol.io) server for [AiVikings.ai](https://aivikings.ai), the domain registrar built for AI agents. It lets ChatGPT, Claude, Cursor and any agent that supports MCP check availability, register and renew domains, and manage DNS, contacts and transfers.

**No install needed.** AiVikings.ai runs this server at:

```
https://mcp.aivikings.ai/mcp
```

Setup guides, the full tool reference and pricing: **[aivikings.ai/docs/mcp](https://aivikings.ai/docs/mcp/)**

## Connect

You need an AiVikings.ai account. Create one at [app.aivikings.ai](https://app.aivikings.ai).

The server uses OAuth. On first use your client opens an AiVikings.ai page where you approve the connection. Today that page asks you to paste the API token from your dashboard.

### Claude Code

```bash
claude mcp add --transport http aivikings https://mcp.aivikings.ai/mcp
```

### Claude (web and desktop)

Add a custom connector with the URL `https://mcp.aivikings.ai/mcp`. Step by step: [Claude setup](https://aivikings.ai/docs/mcp/claude/).

### ChatGPT

Add a connector with the URL `https://mcp.aivikings.ai/mcp` and OAuth authentication. Step by step: [ChatGPT setup](https://aivikings.ai/docs/mcp/chatgpt/).

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "aivikings": {
      "url": "https://mcp.aivikings.ai/mcp"
    }
  }
}
```

### VS Code

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "aivikings": {
      "type": "http",
      "url": "https://mcp.aivikings.ai/mcp"
    }
  }
}
```

### Cline and other agents

Agents that install MCP servers for you can follow [llms-install.md](llms-install.md).

### Unattended agents (LangChain, CrewAI, scripts)

Agents without a browser can't complete OAuth. Send your AiVikings.ai API key as a bearer token instead:

```json
{
  "mcpServers": {
    "aivikings": {
      "type": "streamableHttp",
      "url": "https://mcp.aivikings.ai/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_AIVIKINGS_API_KEY"
      }
    }
  }
}
```

Optional `X-Agent-Id` and `X-Agent-Name` headers label your agent's actions in the domain audit log.

## Try it

Once connected, ask your assistant:

- "Is cartandcup.com available, and what would it cost to register and renew?"
- "Brainstorm 20 names for a weather analytics project and check which .com and .io domains are free."
- "Register nightowlanalytics.com for one year using my default contact."
- "Point the root of nightowlanalytics.com to 203.0.113.10 and add a www CNAME."
- "Show my domains with their status and expiry dates."

## Tools

| Group | Tools |
|---|---|
| Search and pricing | `check_domain_availability`, `check_single_domain_availability`, `get_domain_pricing` |
| Registration (spends prepaid balance) | `register_domain`, `renew_domain`, `domain_transfer` |
| Domain management | `get_domain_status`, `list_domains`, `update_nameservers`, `lock_domain`, `unlock_domain`, `get_transfer_auth_code`, `regenerate_transfer_auth_code`, `get_domain_audit_log` |
| DNS | `list_dns_records`, `add_dns_record`, `configure_dns_record`, `update_dns_record`, `delete_dns_record` |
| Contacts | `create_contact`, `get_contact`, `list_contacts`, `list_domain_registration_contacts`, `assign_domain_registration_contact_roles`, `remove_domain_registration_contact_roles`, `update_registrant_contact`, `list_contact_countries`, `list_contact_states` |
| Account | `get_current_user`, `get_prepaid_balance`, `get_customer` |

Full descriptions and parameters: [tool reference](https://aivikings.ai/docs/mcp/).

## Built for agents

- **Prepaid balance.** Registrations, renewals and transfers are paid from your prepaid USD or EUR balance. No card is charged by a tool call.
- **Premium domains need a yes.** A premium-priced domain is only registered when the agent passes `allow_premium=true` after the user accepted the quoted price.
- **Safety annotations.** Every tool is marked read-only or write, and destructive tools (such as `delete_dns_record`) are flagged, so clients can ask before running them.
- **Audit log.** Every change to a domain is recorded and can be read back with `get_domain_audit_log`.
- **Pure registrar.** No hosting or email upsells in the purchase flow.

## Privacy and security

This server is a thin adapter. Each request carries your own OAuth token or API key, which is verified by the AiVikings.ai backend and forwarded with each tool call. The adapter stores no credentials and has no privileged fallback token. Internal backend error details are never passed back to the client.

- Privacy policy: [aivikings.ai/legal/privacy](https://aivikings.ai/legal/privacy)
- Report a vulnerability: see [SECURITY.md](SECURITY.md)

## Support

- Questions and ideas: [GitHub Discussions](https://github.com/AIvikings/aivikings-mcp/discussions)
- Bugs: [GitHub Issues](https://github.com/AIvikings/aivikings-mcp/issues)
- Email: support@aivikings.ai

---

## Self-hosting the adapter

Most users should connect to the hosted server above. This section is for running the adapter yourself in front of an AiVikings.ai backend.

The adapter is a public Streamable HTTP MCP layer over the AiVikings.ai registrar REST API. The tools keep their parameter schemas, descriptions and safety annotations, and call the backend over HTTP. The backend owns business logic, authentication, customer isolation, scopes, provider access and audit persistence.

This repository contains no registrar backend, database models, provider adapters, frontend assets, internal runbooks or production environment files. It installs and builds without access to either private repository.

### Run locally

Requires Python 3.12+ and a running AiVikings.ai backend exposing `/v1/mcp`.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
# Configure AIVIKINGS_API_BASE_URL to reach the backend.
aivikings-mcp
```

The endpoint is `http://127.0.0.1:8081/mcp`. Clients send their own AiVikings.ai bearer API key or OAuth access token. The adapter verifies it through the backend and forwards it with each tool call. There is no privileged fallback token. Token revocation and customer/scope checks stay authoritative in the backend. Anonymous initialize, tools/list and ping discovery remain available.

`GET /healthz` is a local process health check, not an upstream readiness check. `/.well-known/oauth-protected-resource` advertises the public backend as the OAuth authorization server. `AIVIKINGS_API_BASE_URL` is an internal HTTP address; `AIVIKINGS_PUBLIC_API_BASE_URL` and `AIVIKINGS_MCP_URL` must be externally reachable for real OAuth clients. OAuth issuance and signing secrets remain in the backend.

### Docker

```bash
docker compose up --build
```

The standalone Compose default reaches the backend's published port 8080 using `host.docker.internal`. Set the upstream/public URLs for your deployment. If you copy `.env.example` first, replace its localhost upstream with an address reachable from inside the container. No private source checkout is mounted.

### Tests

```bash
pytest
```

Tests use a simulated HTTP backend and exercise discovery, bearer challenges, per-request identity, tool schemas and error sanitization without a database. Backend rejection is returned as an HTTP-status tool error; private upstream response bodies are not exposed to MCP clients. Review backend logs for details.

The optional Claude demonstration client is installed with `python -m pip install -e ".[demo]"`; configure its client-side `ANTHROPIC_API_KEY` and `AIVIKINGS_MCP_API_KEY` before `aivikings-demo-agent`. Its sample transcript in `examples/` is historical and illustrative.

## License

[MIT](LICENSE)
