# Installing the AiVikings.ai MCP server (for AI agents)

Instructions for an AI agent (such as Cline) setting up this server for a user.
The server is hosted, so there is nothing to install or build.

## Requirements

The user needs an AiVikings.ai account. If they don't have one, they can create
it at https://app.aivikings.ai. Do not invent or guess API keys or tokens.

## Option A: connect with OAuth (recommended)

If the client supports remote MCP servers over Streamable HTTP with OAuth, add:

```json
{
  "mcpServers": {
    "aivikings": {
      "type": "streamableHttp",
      "url": "https://mcp.aivikings.ai/mcp"
    }
  }
}
```

Some clients call the type `http` instead of `streamableHttp`.

On first use, the client opens an AiVikings.ai page in the browser. The user
pastes the API token from their AiVikings.ai dashboard and approves the
connection. Nothing else needs configuring.

## Option B: connect with an API key

For clients without OAuth, or agents that run unattended, ask the user for
their AiVikings.ai API key (from the dashboard at https://app.aivikings.ai)
and send it as a bearer token:

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

## Check that it works

Call the `get_current_user` tool. It should return the user's name and email.
Then try `check_domain_availability` with a domain such as `example-test-name.com`.

## Good to know

- Domain registrations are paid from the user's prepaid balance. Always show
  the user the price from `get_domain_pricing` and get their OK before calling
  `register_domain`.
- Docs: https://aivikings.ai/docs/mcp/
