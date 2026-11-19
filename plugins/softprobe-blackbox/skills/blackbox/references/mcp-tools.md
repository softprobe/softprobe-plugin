# Blackbox MCP tool reference

All 18 tools exposed by `https://explorer.softprobe.ai/mcp` (`softprobe/explorer` `src/mcp/tools.ts`).

## Auth and workspaces

- `whoami`. No parameters. Checks Explorer login and lists workspaces.
- `list_workspaces`. No parameters. Lists workspaces for the signed-in user.
- `select_workspace`. Required `workspace_id` (string). Sets the active workspace when the API returns `workspace_picker_required`.

## Sessions

- `search_sessions`
  - Required: `from_time` (ISO-8601 UTC), `to_time` (ISO-8601 UTC)
  - Optional: `limit` (integer, default 50), `cursor` (string, supported when `order_by` is `start_time`), `agent_name` (string), `model_name` (string), `user_id` (string), `has_errors` (boolean), `order_by` (`start_time` | `error_count` | `duration` | `total_tokens` | `total_cost`), `order` (`asc` | `desc`)
- `get_session`
  - Required: `session_id` (string)
  - Optional: `limit` (integer, default 200)
- `get_session_spans`
  - Required: `session_id` (string)

## Spans

- `search_spans`
  - Required: `from_time` (ISO-8601 UTC), `to_time` (ISO-8601 UTC)
  - Optional: `session_id` (string), `trace_id` (string), `span_types` (comma-separated string), `model_name` (string), `user_id` (string), `limit` (integer), `cursor` (string)
- `get_span`
  - Required: `span_id` (string)
  - Optional: `from` (ISO-8601 UTC, defaults to 90-day lookback), `to` (ISO-8601 UTC, defaults to now), `session_id` (string)

## Traces

- `search_traces`
  - Optional: `query` (TraceQL selector, e.g. `{}` or `{ status = error && .sp.session.id !~ ".+" }`), `from_time` (ISO-8601 UTC), `to_time` (ISO-8601 UTC), `min_duration` (string, e.g. `100ms`), `max_duration` (string, e.g. `5s`), `limit` (integer, default 20)
- `list_trace_tags`
  - Lists available span and resource attribute tag names for TraceQL queries.
  - Optional: `from_time` (ISO-8601 UTC), `to_time` (ISO-8601 UTC)
- `list_trace_tag_values`
  - Lists observed values for a TraceQL attribute tag.
  - Required: `tag` (string)
  - Optional: `from_time` (ISO-8601 UTC), `to_time` (ISO-8601 UTC)
- `get_trace`
  - Required: `trace_id` (string)
  - Optional: `from` (ISO-8601 UTC, defaults to 90-day lookback), `to` (ISO-8601 UTC, defaults to now), `session_id` (string), `limit` (integer), `cursor` (string)

## Logs

- `logs_by_session`
  - Required: `session_id` (string)
  - Optional: `from` (ISO-8601 UTC), `to` (ISO-8601 UTC), `limit` (integer `1..500`, default 100)
- `logs_by_trace`
  - Required: `trace_id` (string)
  - Optional: `from` (ISO-8601 UTC), `to` (ISO-8601 UTC), `limit` (integer `1..500`, default 100)

## Agents and ingestion keys

- `bootstrap_project`
  - Optional: `project_name` (string), `framework` (string), `environment` (string)
  - Provisions or reuses a workspace, Agent, and Ingestion Key in one call. Returns `workspaceId`, `agentId`, `ingestionKey`, `envVar`, and `otlpEndpoint`.
- `list_agents`. No parameters. Lists registered Agents in the active workspace.
- `create_agent`
  - Required: `name` (non-empty string)
  - Optional: `agent_id` (string), `framework` (string), `environment` (string)
  - Returns the created Agent and its new Ingestion Key.
- `get_ingestion_key`
  - Required: `agent_id` (non-empty string)
  - Returns the Agent's Ingestion Key.
