---
name: blackbox
description: Investigate Softprobe Blackbox sessions, OpenTelemetry traces, spans, and logs in Explorer, generate UI tests from recorded sessions, and manage registered Agents via hosted MCP at https://explorer.softprobe.ai/mcp. Use when debugging agent runs, tool errors, LLM generations, trace latency, generating Playwright or E2E UI tests from recorded sessions, or provisioning Explorer projects, agents, and ingestion keys.
when_to_use: Softprobe Blackbox, Explorer sessions, traces, spans, logs, TraceQL, ingestion key, create agent, bootstrap project, UI testing, Playwright, semantic actions, blackbox MCP
---

# Softprobe Blackbox

Query recorded sessions, OpenTelemetry traces, spans, and correlated logs in [Softprobe Explorer](https://explorer.softprobe.ai), and manage registered Agents through the hosted Streamable HTTP MCP server.

## Hosted MCP connection

Endpoint: `https://explorer.softprobe.ai/mcp` (server name: `blackbox`).

If `blackbox` tools are unavailable, tell the user to add the server in their client and complete the browser OAuth flow on first use. Never ask the user to paste a JWT or bearer token.

## Tool routing

| Need | Tool | Notes |
|---|---|---|
| Check auth and workspaces | `whoami`, `list_workspaces` | Run when auth or workspace context is unclear |
| Switch active workspace | `select_workspace` | Call when the API returns `workspace_picker_required` |
| Search sessions in a window | `search_sessions` | Requires UTC `from_time` and `to_time` |
| Inspect one session | `get_session`, `get_session_spans` | Pass `session_id` |
| Read UI semantic action timeline | `get_session_semantic_actions` | Pass `session_id`; use for UI test generation |
| Search spans in a window | `search_spans` | Requires UTC `from_time` and `to_time` |
| Inspect one span | `get_span` | Pass `span_id`; optional `from`, `to`, `session_id` |
| Search traces with TraceQL | `search_traces` | Includes unassigned traces without `session_id` |
| Discover TraceQL tag names and values | `list_trace_tags`, `list_trace_tag_values` | Inspect span/resource attributes before `search_traces` |
| Inspect one trace | `get_trace` | Pass `trace_id`; optional `from`, `to`, `session_id` |
| Read correlated logs | `logs_by_session`, `logs_by_trace` | Bounded scan (`limit` 1 to 500, default 100) |
| List or create Agents | `list_agents`, `create_agent` | `create_agent` returns a new Ingestion Key |
| Fetch an Agent Ingestion Key | `get_ingestion_key` | Pass `agent_id` only when the user asks for it |
| Provision project telemetry setup | `bootstrap_project` | Reuses or creates workspace, Agent, and Ingestion Key |

For full parameter schemas, defaults, and enum values, read [references/mcp-tools.md](references/mcp-tools.md).

## Investigation workflow

1. If workspace selection is required, call `list_workspaces` then `select_workspace`.
2. Start from the narrowest identifier available (`session_id`, `trace_id`, or `span_id`). Otherwise bound the query with `search_sessions` or `search_traces` in a UTC ISO-8601 window.
3. For a failing session, call `get_session` and `get_session_spans`, then check `logs_by_session` or `get_trace` for root-cause errors.
4. Cite exact `session_id`, `trace_id`, and `span_id` values in findings, and link sessions as `https://explorer.softprobe.ai?session=<session_id>`.

## UI test generation workflow

1. Call `get_session_semantic_actions` with `session_id` (keep `include_passive: false` unless scroll/resize assertions are needed) to read the segmented timeline of `softprobe.ui.action` steps, rich CSS/ARIA locators, `[non-interactive]` tags, and caused `trace_id` summaries.
2. Prune stray `[non-interactive]` clicks and retried failed attempts that do not belong in the target user flow.
3. Call `get_trace(trace_id)` on selected caused traces to inspect full HTTP request and response bodies and downstream `CLIENT` calls.
4. Write a `@playwright/test` + `@softprobe/e2e` test (or `e2e` suite) using the locators from `get_session_semantic_actions`, binding any `{ kind: "secret", slot }` inputs to `process.env.SP_SECRET_<SLOT>`, and asserting backend side effects with `trace.outboundHttp` and `trace.expectNoOutboundHttp`.
5. Add cleanup in `afterEach` so repeated test runs stay idempotent.

## Guardrails

- Treat `create_agent`, `get_ingestion_key`, and `bootstrap_project` outputs as sensitive credentials. Only call them when the user asks to register an app, bootstrap telemetry setup, enable coding agent trajectory capture, or retrieve an Ingestion Key.
- Never call `https://thelake.softprobe.ai` directly with a user token, and never send `X-Softprobe-Assertion`.
- Blackbox MCP queries Explorer telemetry and manages Agents. It does not ingest OTLP spans directly.

## Coding agent trajectory capture setup

When the user asks to capture their coding agent's own trajectory (Codex, Cursor, Claude Code, or OpenCode) into Explorer:

1. Call `bootstrap_project` (e.g. `project_name` matching the client such as `codex`, `cursor`, `claude-code`, or `opencode`) to provision an Agent and obtain `ingestionKey` and `otlpEndpoint`.
2. Write the client's local telemetry config with `chmod 600` (never commit keys to git):
   - **Codex CLI (`~/.codex/config.toml`)**:
     ```toml
     [otel]
     environment = "production"
     log_user_prompt = true

     [otel.exporter.otlp-http]
     endpoint = "<otlpEndpoint without /v1/traces>/v1/logs"
     protocol = "binary"
     headers = { Authorization = "Bearer <ingestionKey>" }

     [otel.trace_exporter.otlp-http]
     endpoint = "<otlpEndpoint>"
     protocol = "binary"
     headers = { Authorization = "Bearer <ingestionKey>" }
     ```
   - **Cursor & Claude Code (`~/.config/softprobe/agent-telemetry.json`)**:
     ```json
     {
       "ingestionKey": "<ingestionKey>",
       "otlpEndpoint": "<otlpEndpoint>"
     }
     ```
     The `softprobe-blackbox` plugin hooks (`npx -y @softprobe/blackbox hook`) automatically read this file and remain a no-op until it exists.
   - **OpenCode (`~/.config/opencode/opencode-softprobe.json`)**:
     ```json
     {
       "ingestionKey": "<ingestionKey>",
       "otlp": {
         "tracesEndpoint": "<otlpEndpoint>",
         "protocol": "http/protobuf"
       }
     }
     ```
     `@softprobe/opencode-blackbox` automatically activates trajectory capture when this file exists.
