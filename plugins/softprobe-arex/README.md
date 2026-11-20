# Softprobe Arex Plugin

Official Softprobe Arex MCP plugin and `arex-feature-test` skill for authoring, forking, running, and triaging unified `arex.test-case/v1` test cases.

## Prerequisites

Install the `sp` CLI and authenticate against your Softprobe backend (`SP_API_URL` and `SP_TOKEN` or `sp auth login`). See the [Arex documentation](https://docs.softprobe.ai/en/arex/) for setup instructions.

## Install

### Quick setup with `sp mcp setup`

Write or merge the stdio MCP configuration directly into your project directory:

```bash
sp mcp setup --client cursor --dir .
# Supported clients: cursor | claude | antigravity | codex
```

### Claude Code

```bash
claude plugin marketplace add softprobe/softprobe-plugin
claude plugin install softprobe-arex@softprobe
```

### Cursor

Install `softprobe-arex` from `softprobe/softprobe-plugin` in Cursor **Plugins**, or run `sp mcp setup --client cursor --dir .`.

### Antigravity and Codex

Copy [`mcp_config.json`](./mcp_config.json) or run `sp mcp setup --client antigravity --dir .`, then install the skill:

```bash
npx skills add softprobe/softprobe-plugin -g -y -a antigravity -s arex-feature-test
```

## Included MCP tools (8)

`sp mcp` runs over stdio and exposes 8 tools documented in [`skills/arex-feature-test/references/mcp-tools.md`](./skills/arex-feature-test/references/mcp-tools.md):

- **Context & coverage:** `arex_discover_context`, `arex_list_cases_and_coverage`
- **Authoring & forking:** `arex_export_baseline`, `arex_apply_test_case`
- **Execution & external suites:** `arex_run_test_case`, `arex_import_external_results`
- **Defects & logs:** `arex_link_or_file_issue`, `arex_query_logs`
