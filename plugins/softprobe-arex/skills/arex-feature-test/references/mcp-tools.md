# Arex MCP tool reference

All 8 tools exposed by `sp mcp` (`softprobe-arex-mcp` stdio server, MCP protocol `2024-11-05` and `2025-03-26`).

## Context and coverage

- `arex_discover_context`
  - Required: `appId` (string, application identifier)
  - Returns `appId`, `agentStatus` (`online` | `degraded` | `offline` | `never` | `unknown`), `recordedOperations` (map of dependency category to operation names), and the first page of unified `cases`.
- `arex_list_cases_and_coverage`
  - Required: `appId` (string)
  - Optional: `suitePath` (string, suite path prefix), `kind` (`AREX` | `EXTERNAL_AUTOMATED` | `MANUAL`), `status` (`DRAFT` | `ACTIVE` | `FLAKY` | `DEPRECATED`), `tag` (string), `provider` (`github` | `jira` | `linear` | `local`), `scope` (string, milestone, epic, label, or cycle), `page` (integer, minimum `1`), `pageSize` (integer, `1` to `200`, default `50`)
  - Returns `appId`, paginated `cases` (`total`, `page`, `pageSize`, `items`), and `coverage` (`summary` counts plus per-requirement `coverageStatus`, linked `cases`, and `openBugs`).

## Test case authoring

- `arex_export_baseline`
  - Required: `appId` (string), `recordId` (string, recorded trace or record identifier)
  - Exports a sensitive-policy-redacted `arex.test-case/v1` baseline document from a Rolling or Pinned recording without persisting it.
- `arex_apply_test_case`
  - Required: `appId` (string), `kind` (`AREX` | `EXTERNAL_AUTOMATED` | `MANUAL`)
  - Optional: `schemaVersion` (string, defaults to `"arex.test-case/v1"`), `id` (string, generated when omitted), `suitePath` (string), `title` (string), `description` (string), `origin` (`CAPTURED` | `AI_FORKED` | `AI_SYNTHETIC` | `MANUAL`), `parentCaseId` (string), `status` (`DRAFT` | `ACTIVE` | `FLAKY` | `DEPRECATED`), `priority` (string), `tags` (string array), `requirementLinks` (object array with `provider`, `externalId`, `url`, `title`, `status`), `bugLinks` (object array), `arexSpec` (object with `input`, `expectedOutput`, `injectionRules`, `assertionRules`, and `dependencies`), `externalSpec` (object with `runner`, `canonicalName`, `fileRef`), `manualSpec` (object with `preconditions`, `steps`, `expectedOutcome`), `testCase` (optional nested `TestCase` wrapper object)
  - Validates the `arex.test-case/v1` payload and Google CEL expressions, upserts the case into the catalog, and returns the stored `TestCase` document.

## Execution and external result ingestion

- `arex_run_test_case`
  - Required: `appId` (string), `targetEnv` (string, target service base URL such as `http://127.0.0.1:8081`)
  - Optional: `caseIds` (string array), `caseId` (string, single case convenience field merged with `caseIds`), `suitePath` (string, suite prefix), `gitSha` (string, commit SHA recorded on the run)
  - Returns `runId`, `appId`, `passed`, `total`, `passedCount`, `failedCount`, and `results[]`. Each item in `results` contains `resultId`, `caseId`, `replayId`, `status`, `passed`, `failureCategory` (`NONE` | `MOCK_MISS_OR_DRIFT` | `TEST_AUTHORING_ERROR` | `ENV_OR_AGENT_ERROR` | `REAL_APPLICATION_BUG`), `durationMs`, `actualEntry`, `assertionResults`, `diffSummary`, `unmockedCalls[].stubTemplate`, and `logWindow` (`traceId`, `since`, `until`).
- `arex_import_external_results`
  - Required: `appId` (string)
  - Optional: `filePath` (string, path to `.xml` or `.json` report on disk), `content` (string, raw JUnit XML or CTRF JSON when `filePath` is omitted), `format` (`ctrf` | `junit`, auto-detected from extension or payload when omitted), `runner` (string, such as `playwright`, `pytest`, `junit`, `vitest`, or `go`), `suitePath` (string), `gitSha` (string)
  - Ingests external automated test results into the unified catalog, extracts requirement ticket references, and returns `runId`, `importedCases`, `passedCount`, `failedCount`, and `skippedCount`.

## Issue tracking and logs

- `arex_link_or_file_issue`
  - Required: `appId` (string), `caseId` (string), `provider` (`github` | `jira` | `linear` | `gitlab`)
  - Optional: `resultId` (string, failed run result identifier), `repositoryOrProject` (string, `owner/repo` for GitHub or project key for Jira; required when `externalUrl` is omitted), `title` (string), `notes` (string), `externalUrl` (string, existing issue URL to link without creating a new ticket)
  - Files a new defect or links an existing ticket onto the test case and returns `caseId`, `provider`, `externalId`, `url`, and `status`.
- `arex_query_logs`
  - Required: `traceId` (string), `since` (string, inclusive start timestamp in ISO-8601 UTC), `until` (string, exclusive end timestamp in ISO-8601 UTC)
  - Queries `/api/recorder/logs` for correlated application log records within the bounded UTC window.
