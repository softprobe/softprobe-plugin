---
name: blackbox
description: Investigate Softprobe Blackbox sessions, OpenTelemetry traces, spans, and logs in Explorer, and manage registered Agents via hosted MCP at https://explorer.softprobe.ai/mcp. Use when debugging agent runs, tool errors, LLM generations, trace latency, or provisioning Explorer agents and ingestion keys.
when_to_use: Softprobe Blackbox, Explorer sessions, traces, spans, logs, TraceQL, ingestion key, create agent, blackbox MCP
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
| Search spans in a window | `search_spans` | Requires UTC `from_time` and `to_time` |
| Inspect one span | `get_span` | Pass `span_id`; optional `from`, `to`, `session_id` |
| Search traces with TraceQL | `search_traces` | Includes unassigned traces without `session_id` |
| Inspect one trace | `get_trace` | Pass `trace_id`; optional `from`, `to`, `session_id` |
| Read correlated logs | `logs_by_session`, `logs_by_trace` | Bounded scan (`limit` 1 to 500, default 100) |
| List or create Agents | `list_agents`, `create_agent` | `create_agent` returns a new Ingestion Key |
| Fetch an Agent Ingestion Key | `get_ingestion_key` | Pass `agent_id` only when the user asks for it |

For full parameter schemas, defaults, and enum values, read [references/mcp-tools.md](references/mcp-tools.md).

## Investigation workflow

1. If workspace selection is required, call `list_workspaces` then `select_workspace`.
2. Start from the narrowest identifier available (`session_id`, `trace_id`, or `span_id`). Otherwise bound the query with `search_sessions` or `search_traces` in a UTC ISO-8601 window.
3. For a failing session, call `get_session` and `get_session_spans`, then check `logs_by_session` or `get_trace` for root-cause errors.
4. Cite exact `session_id`, `trace_id`, and `span_id` values in findings, and link sessions as `https://explorer.softprobe.ai?session=<session_id>`.

## Guardrails

- Treat `create_agent` and `get_ingestion_key` outputs as sensitive credentials. Only call `get_ingestion_key` or `create_agent` when the user asks to register an app or retrieve its key.
- Never call `https://thelake.softprobe.ai` directly with a user token, and never send `X-Softprobe-Assertion`.
- Blackbox MCP queries Explorer telemetry and manages Agents. It does not ingest OTLP spans directly.
