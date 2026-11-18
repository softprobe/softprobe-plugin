# Softprobe Plugin Marketplace

Official multi-product plugin marketplace from SoftProbe, Inc. (`softprobe/softprobe-plugin`).

## Plugins

| Plugin | Location | Status | Description |
|---|---|---|---|
| `softprobe-blackbox` | [`plugins/softprobe-blackbox/`](./plugins/softprobe-blackbox/) | Available | Hosted Explorer MCP server (`https://explorer.softprobe.ai/mcp`) and skills for session, trace, span, log, and Agent workflows. |
| `@softprobe/opencode-blackbox` | [softprobe/softprobe-js](https://github.com/softprobe/softprobe-js/tree/main/packages/opencode-blackbox) ([npm](https://www.npmjs.com/package/@softprobe/opencode-blackbox)) | Available | Compiled OpenCode npm plugin that registers the `blackbox` MCP server and skill. |
| `softprobe-arex` | [`plugins/softprobe-arex/`](./plugins/softprobe-arex/) | Coming soon | Record, replay, and diff verification. |
| `softprobe-lisa` | [`plugins/softprobe-lisa/`](./plugins/softprobe-lisa/) | Coming soon | Policy evaluation and activity monitoring. |

### Where plugins live (`softprobe-plugin` vs `softprobe-js`)

- **`softprobe/softprobe-plugin`** (this repo) holds static GitHub-hosted manifests and `SKILL.md` files for Claude Code, Cursor, Codex, VS Code / GitHub Copilot, Gemini CLI, Windsurf, and Antigravity.
- **[`softprobe/softprobe-js`](https://github.com/softprobe/softprobe-js)** holds compiled TypeScript/JavaScript runtime plugins distributed via npm, such as [`@softprobe/opencode-blackbox`](https://github.com/softprobe/softprobe-js/tree/main/packages/opencode-blackbox) and [`@softprobe/opencode-plugin`](https://github.com/softprobe/softprobe-js/tree/main/packages/opencode-plugin).

## Install Softprobe Blackbox

### Claude Code

Install the plugin from the marketplace:

```bash
claude plugin marketplace add softprobe/softprobe-plugin
claude plugin install softprobe-blackbox@softprobe
```

Or add the hosted MCP server directly:

```bash
claude mcp add --transport http blackbox https://explorer.softprobe.ai/mcp
```

### Cursor

Install from Cursor Settings under **Plugins** using `softprobe/softprobe-plugin`, or add the MCP server via CLI or `.cursor/mcp.json`:

```bash
cursor --add-mcp '{"name":"blackbox","url":"https://explorer.softprobe.ai/mcp"}'
```

### Codex CLI

Install the plugin from `.agents/plugins/marketplace.json`, or add the hosted MCP server:

```bash
codex mcp add blackbox --url https://explorer.softprobe.ai/mcp
```

### VS Code and GitHub Copilot

Add the hosted MCP server via CLI or `.vscode/mcp.json`:

```bash
code --add-mcp '{"name":"blackbox","type":"http","url":"https://explorer.softprobe.ai/mcp"}'
```

### Gemini CLI

Install the extension directly from GitHub:

```bash
gemini extensions install https://github.com/softprobe/softprobe-plugin --ref main --consent
```

### Antigravity

Add `plugins/softprobe-blackbox/mcp_config.json` to `~/.gemini/config/mcp_config.json` (global) or `.agents/mcp_config.json` (workspace), and install the skill:

```bash
npx skills add softprobe/softprobe-plugin -g -y -a antigravity -s blackbox
```

### OpenCode

Install the npm plugin from [`softprobe/softprobe-js`](https://github.com/softprobe/softprobe-js/tree/main/packages/opencode-blackbox) (also on [npm](https://www.npmjs.com/package/@softprobe/opencode-blackbox)):

```bash
opencode plugin @softprobe/opencode-blackbox -g
```

Or add the hosted MCP server and skill manually:

```bash
opencode mcp add blackbox --global --url https://explorer.softprobe.ai/mcp
npx skills add softprobe/softprobe-plugin -g -y -a opencode -s blackbox
```

### Windsurf

Add the `mcpServers.blackbox` entry from `plugins/softprobe-blackbox/mcp_config.json` to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "blackbox": {
      "url": "https://explorer.softprobe.ai/mcp"
    }
  }
}
```

## Authenticate and use

The first MCP tool call opens a browser window to sign in to [Softprobe Explorer](https://explorer.softprobe.ai) via OAuth. After you approve access, ask your agent to investigate telemetry or manage Agents.

> Use Blackbox: why did session `sess_...` fail? Check tool errors, spans, and correlated logs.

## Repository layout

```text
assets/softprobe-mark.svg                  # Marketplace brand mark
plugins/
  softprobe-blackbox/
    plugin.json                            # Agent Plugins manifest
    .mcp.json                              # Streamable HTTP MCP config
    mcp_config.json                        # Antigravity / Windsurf MCP config
    assets/softprobe-mark.svg              # Plugin logo
    skills/blackbox/SKILL.md               # Blackbox skill & tool reference
  softprobe-arex/                          # Coming soon: record, replay, and diff verification
  softprobe-lisa/                          # Coming soon: policy evaluation and activity monitoring
tests/                                     # Manifest and skill placement tests
```

## License

Apache License 2.0. See [LICENSE](./LICENSE) and [NOTICE](./NOTICE).

## Operator note

Hosted MCP runs on Explorer (`POST /mcp`, OAuth under `/oauth/*`, discovery under `/.well-known/`). The Supabase Auth redirect allowlist must include:

- `https://explorer.softprobe.ai/auth/cli**`
- `https://explorer.softprobe.ai/oauth/authorize**`
