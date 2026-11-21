# Softprobe Plugin Marketplace

Official multi-product plugin marketplace from SoftProbe, Inc. (`softprobe/softprobe-plugin`).

## Plugins

| Plugin | Location | Status | Description |
|---|---|---|---|
| `softprobe-blackbox` | [`plugins/softprobe-blackbox/`](./plugins/softprobe-blackbox/) | Available | Hosted Explorer MCP server (`https://explorer.softprobe.ai/mcp`) and skills for session, trace, span, log, and Agent workflows. |
| `@softprobe/opencode-blackbox` | [softprobe/softprobe-js](https://github.com/softprobe/softprobe-js/tree/main/packages/opencode-blackbox) ([npm](https://www.npmjs.com/package/@softprobe/opencode-blackbox)) | Available | Compiled OpenCode npm plugin that registers the `blackbox` MCP server and skill. |
| `softprobe-arex` | [`plugins/softprobe-arex/`](./plugins/softprobe-arex/) | Available | Stdio `sp mcp` server and `arex-feature-test` skill for unified `arex.test-case/v1` authoring, dependency mocking, Google CEL assertions, requirement coverage, and regression triage. |
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

## Install Softprobe Arex

Softprobe Arex runs a local stdio MCP server (`sp mcp`) backed by your configured `sp` CLI profile (`SP_API_URL` and `SP_TOKEN` or `sp auth login`).

### Quick setup with `sp mcp setup`

Generate or merge the MCP configuration file in your project root:

```bash
sp mcp setup --client cursor --dir .
# Supported clients: cursor | claude | antigravity | codex
```

### Claude Code and Cursor marketplace

```bash
claude plugin marketplace add softprobe/softprobe-plugin
claude plugin install softprobe-arex@softprobe
```

In Cursor, add `softprobe/softprobe-plugin` under **Plugins** and install `softprobe-arex`.

### Antigravity, Codex, and Windsurf

Merge [`plugins/softprobe-arex/mcp_config.json`](./plugins/softprobe-arex/mcp_config.json) into your MCP config, and install the feature-testing skill:

```bash
npx skills add softprobe/softprobe-plugin -g -y -a antigravity -s arex-feature-test
```

## Authenticate and use

For **Blackbox**, the first MCP tool call opens a browser window to sign in to [Softprobe Explorer](https://explorer.softprobe.ai) via OAuth. After you approve access, ask your agent to investigate telemetry or manage Agents.

> Use Blackbox: why did session `sess_...` fail? Check tool errors, spans, and correlated logs.

For **Arex**, configure `sp` with `sp setup` or `sp auth login`, then ask your agent to verify a feature branch with unified test cases.

> Use Arex: check untested requirements for `travel-ota`, fork a baseline case for the new baggage discount endpoint, and verify it against `http://127.0.0.1:8081`.

## Blackbox MCP tools (17)

The hosted server at `https://explorer.softprobe.ai/mcp` exposes 17 tools (see [`plugins/softprobe-blackbox/skills/blackbox/references/mcp-tools.md`](./plugins/softprobe-blackbox/skills/blackbox/references/mcp-tools.md) for full parameter schemas):

- **Auth & workspaces:** `whoami`, `list_workspaces`, `select_workspace`
- **Sessions:** `search_sessions`, `get_session`, `get_session_spans`
- **Spans:** `search_spans`, `get_span`
- **Traces:** `search_traces`, `list_trace_tags`, `list_trace_tag_values`, `get_trace`
- **Logs:** `logs_by_session`, `logs_by_trace`
- **Agents & ingestion keys:** `list_agents`, `create_agent`, `get_ingestion_key`

## Arex MCP tools (8)

The stdio server `sp mcp` exposes 8 tools (see [`plugins/softprobe-arex/skills/arex-feature-test/references/mcp-tools.md`](./plugins/softprobe-arex/skills/arex-feature-test/references/mcp-tools.md) for full parameter schemas):

- **Context & coverage:** `arex_discover_context`, `arex_list_cases_and_coverage`
- **Authoring & forking:** `arex_export_baseline`, `arex_apply_test_case`
- **Execution & external suites:** `arex_run_test_case`, `arex_import_external_results`
- **Defects & logs:** `arex_link_or_file_issue`, `arex_query_logs`

## Repository layout

```text
assets/softprobe-mark.svg                                     # Marketplace brand mark
plugins/
  softprobe-blackbox/
    plugin.json                                               # Agent Plugins manifest
    .mcp.json                                                 # Streamable HTTP MCP config
    mcp_config.json                                           # Antigravity / Windsurf MCP config
    assets/softprobe-mark.svg                                 # Plugin logo
    skills/blackbox/SKILL.md                                  # Blackbox skill & tool routing
    skills/blackbox/references/mcp-tools.md                   # Full 17-tool MCP reference
  softprobe-arex/
    plugin.json                                               # Agent Plugins manifest
    .claude-plugin/plugin.json                                # Claude Code plugin manifest
    .cursor-plugin/plugin.json                                # Cursor plugin manifest
    .mcp.json                                                 # Stdio sp mcp config
    mcp_config.json                                           # Antigravity / Windsurf MCP config
    assets/softprobe-mark.svg                                 # Plugin logo
    skills/arex-feature-test/SKILL.md                         # Feature-testing skill & 5-step loop
    skills/arex-feature-test/references/mcp-tools.md          # Full 8-tool MCP reference
  softprobe-lisa/                                             # Coming soon: policy evaluation and activity monitoring
tests/                                                        # Manifest and skill placement tests
```

## License

MIT License. See [LICENSE](./LICENSE).

## Operator note

Hosted MCP runs on Explorer (`POST /mcp`, OAuth under `/oauth/*`, discovery under `/.well-known/`). The Supabase Auth redirect allowlist must include:

- `https://explorer.softprobe.ai/auth/cli**`
- `https://explorer.softprobe.ai/oauth/authorize**`
