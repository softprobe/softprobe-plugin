---
name: arex-feature-test
description: >-
  Synthesize, fork, execute, and triage unified Arex test cases (arex.test-case/v1)
  with case-level dependency injection rules and Google CEL assertions using sp mcp
  or the sp case and sp test CLI commands. Use when testing new code changes,
  closing untested requirement coverage gaps, or diagnosing regressions in an
  Arex-instrumented service.
when_to_use: >-
  Softprobe Arex, sp mcp, sp case, sp test, arex.test-case/v1, dependency mocking,
  Google CEL assertions, CTRF, JUnit XML, requirement coverage, regression triage
---

# Softprobe Arex feature testing

Verify backend code changes against an Arex-instrumented service with unified `arex.test-case/v1` test cases. Use the `arex` stdio MCP server (`sp mcp`) when loaded, or fall back to deterministic `sp case` and `sp test` CLI commands.

## Connect MCP or CLI

Server command: `sp mcp` (plugin server name: `arex`).

If the `arex_*` MCP tools are not loaded in the current agent session, register the server in the workspace:

```bash
sp mcp setup --client cursor --dir .
# Or --client claude | antigravity | codex
```

Every MCP tool maps to an `sp` CLI command that writes a single-line `--json` envelope (`0` pass, `1` test or coverage gate failure, `2` usage or validation error, `3` authentication error).

## Tool routing

| Need | MCP tool | CLI equivalent |
|---|---|---|
| Check agent status, recorded operations, and existing cases | `arex_discover_context` | `sp app status`, `sp record operation list`, `sp case list` |
| List unified cases and requirement coverage gaps | `arex_list_cases_and_coverage` | `sp case list`, `sp test coverage` |
| Export a redacted baseline case from a recorded trace | `arex_export_baseline` | `sp case export --app <appId> --record-id <recordId>` |
| Create or update a unified `arex.test-case/v1` document | `arex_apply_test_case` | `sp case apply --file case.json` |
| Execute cases or a suite against `targetEnv` | `arex_run_test_case` | `sp case run --app <appId> --env <url>` |
| Import CTRF JSON or JUnit XML reports | `arex_import_external_results` | `sp test import-results --app <appId> --file <path>` |
| File or link a defect in GitHub, Jira, Linear, or GitLab | `arex_link_or_file_issue` | `sp test bug create` |
| Query correlated application logs around a trace | `arex_query_logs` | `sp logs --trace-id <id> --since <ts> --until <ts>` |

For complete input schemas, enum values, and return fields across all 8 tools, read [references/mcp-tools.md](references/mcp-tools.md).

## Follow the 5-step feature-testing loop

### 1. Discover diff, requirements, baselines, and coverage gaps

1. Inspect `git diff`, modified handlers, database queries, API schemas, and linked issue descriptions.
2. Call `arex_discover_context` and `arex_list_cases_and_coverage` for the target `appId`, or run:

```bash
sp record operation list --app <appId> --json
sp case list --app <appId> --json
sp test coverage --app <appId> --json
```

3. Identify which entry operations already have recorded traffic for baseline forking and which requirements report `coverageStatus == "UNTESTED"` or `"FAILING"`.

### 2. Draft the scenario matrix

Write a concise scenario table before generating case payloads. Pick one authoring origin per scenario:

- **`AI_FORKED` (baseline fork).** Use when recorded traffic exists for the endpoint. Export redacted dependency stubs from a recording with `arex_export_baseline` followed by `arex_apply_test_case`, or run `sp case fork --app <appId> --from <recordId> --out case.json --json`.
- **`AI_SYNTHETIC` (synthetic case).** Use for new routes or message consumers that have no prior recordings.

Cover happy paths, `4xx` input validation, authorization boundaries, and downstream `5xx` or empty-dataset cases. Attach requirement tickets in `requirementLinks` (`provider`, `externalId`, `url`).

### 3. Synthesize `arex.test-case/v1` cases

Build or edit the `TestCase` JSON with five parts inside `arexSpec`:

1. **`input`.** Entry request (`category`, `operationName`, `method`, `path`, `headers`, `body`, `attributes`).
2. **`expectedOutput`.** Optional reference output for unchanged structural fields, or `null` when CEL predicates own verification.
3. **`injectionRules`.** Case-level dependency mocking rules (`mockByDefault`, `operations.forceMock`, `operations.skipMock`, `matchTolerance`, and `fallback.strategy`). Never add external payment, email, or message-broker operations to `skipMock` without explicit user approval.
4. **`assertionRules`.** Case-level diff settings (`diffSpec`, such as `{"ignoreAllDependencies": true}`) combined with boolean Google CEL `assertions` over `response.status`, `response.headers`, `response.body`, and outbound `calls`.
5. **`dependencies`.** Case-scoped dependency stubs (`category`, `operationName`, `matchStrategy`, `request`, and `response`).

Validate CEL syntax and save the case with `arex_apply_test_case` or:

```bash
sp case apply --file case.json --json
```

Example `arex.test-case/v1` document:

```json
{
  "schemaVersion": "arex.test-case/v1",
  "id": "tc-baggage-vip-01",
  "appId": "travel-ota",
  "suitePath": "flights/baggage/vip-tier",
  "title": "Platinum member gets first checked bag free",
  "kind": "AREX",
  "origin": "AI_FORKED",
  "parentCaseId": "rec-9001",
  "status": "ACTIVE",
  "requirementLinks": [
    { "provider": "jira", "externalId": "OTA-892" }
  ],
  "arexSpec": {
    "input": {
      "category": "Servlet",
      "method": "POST",
      "path": "/api/flights/baggage/purchase",
      "headers": { "Content-Type": "application/json" },
      "body": { "orderId": "ORD-9001", "bagCount": 1 }
    },
    "injectionRules": {
      "mockByDefault": true,
      "operations": {
        "forceMock": ["HttpClient:/ndc/servicelist", "Database:loyalty_member*"]
      },
      "fallback": { "strategy": "FAIL" }
    },
    "assertionRules": {
      "diffSpec": { "ignoreAllDependencies": true },
      "assertions": [
        {
          "id": "status-200",
          "expression": "response.status == 200",
          "message": "Expected HTTP 200 OK"
        },
        {
          "id": "vip-zero-fee",
          "expression": "response.body.totalCharge == 0",
          "message": "Platinum tier waives the first checked bag fee"
        }
      ]
    },
    "dependencies": [
      {
        "category": "HttpClient",
        "operationName": "/ndc/servicelist",
        "request": {
          "attributes": { "HttpMethod": "POST", "ContentType": "application/json" },
          "body": "{\"orderId\":\"ORD-9001\"}"
        },
        "response": {
          "status": 200,
          "headers": { "Content-Type": "application/json" },
          "body": "{\"services\":[{\"serviceCode\":\"BAG1\",\"amount\":50}]}"
        }
      },
      {
        "category": "Database",
        "operationName": "loyalty_member@SELECT",
        "request": { "body": "SELECT tier FROM loyalty_member WHERE order_id = ?" },
        "response": { "body": "[{\"tier\":\"PLATINUM\"}]", "javaType": "java.util.ArrayList" }
      }
    ]
  }
}
```

### 4. Execute cases and import external suites

Run the case or suite against a running local or test service using `arex_run_test_case` or:

```bash
sp case run --app <appId> --env http://127.0.0.1:8081 --case <caseId> --json
```

`sp case run` prints an `ok: true` JSON envelope to stdout and exits with code `1` whenever `passed == false`. If the repository also runs Pytest, Playwright, JUnit, Vitest, or Go suites, import their reports into the unified catalog and verify the requirement gate with `arex_import_external_results` or:

```bash
sp test import-results --app <appId> --file report.xml --runner pytest --json
sp test coverage --app <appId> --gate --json
```

### 5. Triage 4-way failures without weakening assertions

Inspect `results[].failureCategory` on each failed verdict:

- **`MOCK_MISS_OR_DRIFT`.** Read `results[].unmockedCalls[].stubTemplate`. Populate realistic `response` payloads that match the service return type and scenario data, append those stubs to `arexSpec.dependencies`, re-apply with `arex_apply_test_case` or `sp case apply`, and rerun for at most 3 rounds. Never delete, comment out, or weaken `assertionRules` to make a failing run pass during mock healing.
- **`TEST_AUTHORING_ERROR`.** Fix request field names, HTTP paths, or CEL typos only after verifying them against source code, OpenAPI, or the requirement spec. Cite the source line or spec section for every assertion edit.
- **`ENV_OR_AGENT_ERROR`.** Check the target service URL, Java agent heartbeat (`arex_discover_context` or `sp app status <appId> --json`), and backend health (`sp doctor --json`) before retrying.
- **`REAL_APPLICATION_BUG`.** Query correlated logs around `results[].logWindow` with `arex_query_logs` or `sp logs --trace-id <traceId> --since <since> --until <until> --json`. Report the root cause with the entry response, failed CEL assertion or diff, and log lines. Call `arex_link_or_file_issue` or `sp test bug create` only when the user asks to file or link an issue.
