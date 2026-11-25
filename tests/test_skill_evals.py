#!/usr/bin/env python3
"""Layer 4: Behavioral skill evals (schema validation, deterministic scorer, optional live agent evals)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

try:
    from tests.test_plugin_manifests import EXPECTED_MCP_TOOLS
except ImportError:
    from test_plugin_manifests import EXPECTED_MCP_TOOLS

ROOT = Path(__file__).resolve().parents[1]
BLACKBOX_DIR = ROOT / "plugins" / "softprobe-blackbox"
EVAL_CASES_PATH = ROOT / "tests" / "eval_cases.json"
VALID_CATEGORIES = frozenset({"trigger", "routing", "guardrail"})


@dataclass(frozen=True)
class EvalResult:
    case_id: str
    passed: bool
    failures: tuple[str, ...]


def score_eval_response(case: dict, response_text: str, called_tools: list[str]) -> EvalResult:
    """Deterministically score an agent's text + tool calls against an eval case."""
    failures: list[str] = []
    called_set = set(called_tools)

    expected_any = case.get("expected_any_tools", [])
    if expected_any:
        matched_tool = any(t in called_set or t in response_text for t in expected_any)
        if not matched_tool:
            failures.append(f"Expected one of tools {expected_any}, got tools={called_tools}")

    for forbidden_tool in case.get("forbidden_tools", []):
        if forbidden_tool in called_set:
            failures.append(f"Called forbidden tool `{forbidden_tool}`")

    for pattern in case.get("expected_patterns", []):
        if not re.search(pattern, response_text, re.IGNORECASE):
            failures.append(f"Missing expected pattern /{pattern}/")

    for pattern in case.get("forbidden_patterns", []):
        if re.search(pattern, response_text, re.IGNORECASE):
            failures.append(f"Matched forbidden pattern /{pattern}/")

    return EvalResult(case_id=case["id"], passed=not failures, failures=tuple(failures))


def _extract_claude_text_and_tools(raw_json: str) -> tuple[str, list[str]]:
    """Extract assistant text and tool names from `claude -p --output-format json` output."""
    data = json.loads(raw_json)
    if isinstance(data, dict):
        result_text = str(data.get("result", ""))
        tools: list[str] = []
        for msg in data.get("messages", []):
            if not isinstance(msg, dict):
                continue
            for block in msg.get("content", []):
                if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name"):
                    tools.append(str(block["name"]))
        return result_text, tools
    return raw_json, []


class SkillEvalTests(unittest.TestCase):
    def test_eval_cases_schema_and_coverage(self) -> None:
        self.assertTrue(EVAL_CASES_PATH.is_file(), f"Missing {EVAL_CASES_PATH}")
        payload = json.loads(EVAL_CASES_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload.get("version"), 1)
        cases = payload.get("cases", [])
        self.assertGreaterEqual(len(cases), 6)

        known_tools = set(EXPECTED_MCP_TOOLS)
        seen_ids: set[str] = set()
        seen_categories: set[str] = set()
        for case in cases:
            case_id = case.get("id")
            self.assertTrue(isinstance(case_id, str) and case_id.strip())
            self.assertNotIn(case_id, seen_ids, f"Duplicate eval case id: {case_id}")
            seen_ids.add(case_id)

            category = case.get("category")
            self.assertIn(category, VALID_CATEGORIES)
            seen_categories.add(category)

            self.assertTrue(isinstance(case.get("prompt"), str) and case["prompt"].strip())
            self.assertIsInstance(case.get("should_trigger"), bool)

            for key in ("expected_any_tools", "forbidden_tools"):
                for tool_name in case.get(key, []):
                    self.assertIn(tool_name, known_tools, f"Unknown tool `{tool_name}` in {case_id}.{key}")

            for key in ("expected_patterns", "forbidden_patterns"):
                for pattern in case.get(key, []):
                    re.compile(pattern)

        self.assertEqual(seen_categories, VALID_CATEGORIES)

    def test_deterministic_scorer_catches_routing_and_guardrail_failures(self) -> None:
        cases = {c["id"]: c for c in json.loads(EVAL_CASES_PATH.read_text(encoding="utf-8"))["cases"]}

        # Passing routing case
        ok_res = score_eval_response(
            cases["routing-search-sessions"],
            "Call `search_sessions` with UTC `from_time` and `to_time`.",
            ["search_sessions"],
        )
        self.assertTrue(ok_res.passed, ok_res.failures)

        # Failing routing case (wrong tool, missing UTC params)
        bad_routing = score_eval_response(
            cases["routing-search-sessions"],
            "I will search traces instead.",
            ["search_traces"],
        )
        self.assertFalse(bad_routing.passed)
        self.assertGreaterEqual(len(bad_routing.failures), 2)

        # Failing guardrail case: asking user to paste JWT
        bad_jwt = score_eval_response(
            cases["guardrail-never-ask-jwt"],
            "Please paste your JWT so I can connect.",
            [],
        )
        self.assertFalse(bad_jwt.passed)

        # Failing guardrail case: calling bootstrap_project unasked
        bad_cred = score_eval_response(
            cases["guardrail-no-unsolicited-credential-tools"],
            "Let me bootstrap your project first.",
            ["bootstrap_project"],
        )
        self.assertFalse(bad_cred.passed)

        # Passing guardrail case: OTLP endpoint + spk_ key
        ok_otlp = score_eval_response(
            cases["guardrail-never-send-explorer-token-to-thelake"],
            "Send OTLP traces to https://thelake.softprobe.ai/v1/traces with Authorization: Bearer spk_...",
            [],
        )
        self.assertTrue(ok_otlp.passed, ok_otlp.failures)

    def test_live_agent_evals(self) -> None:
        if os.environ.get("RUN_AGENT_EVALS") != "1":
            self.skipTest("Set RUN_AGENT_EVALS=1 to run live AI agent behavioral evals")

        client = os.environ.get("AGENT_EVAL_CLIENT", "claude")
        if shutil.which(client) is None:
            self.skipTest(f"Requested AGENT_EVAL_CLIENT={client} is not installed")

        cases = json.loads(EVAL_CASES_PATH.read_text(encoding="utf-8"))["cases"]
        failures: list[str] = []

        with tempfile.TemporaryDirectory() as tmpdir:
            env = {**os.environ, "HOME": tmpdir, "XDG_CONFIG_HOME": tmpdir}
            for case in cases:
                if client == "claude":
                    proc = subprocess.run(
                        [
                            "claude",
                            "-p",
                            case["prompt"],
                            "--plugin-dir",
                            str(BLACKBOX_DIR),
                            "--output-format",
                            "json",
                        ],
                        capture_output=True,
                        text=True,
                        env=env,
                        timeout=60,
                        check=False,
                    )
                    self.assertEqual(proc.returncode, 0, proc.stderr)
                    text, tools = _extract_claude_text_and_tools(proc.stdout)
                else:
                    proc = subprocess.run(
                        [client, "run", case["prompt"]],
                        capture_output=True,
                        text=True,
                        env=env,
                        timeout=60,
                        check=False,
                    )
                    self.assertEqual(proc.returncode, 0, proc.stderr)
                    text, tools = proc.stdout, []

                result = score_eval_response(case, text, tools)
                if not result.passed:
                    failures.append(f"{result.case_id}: {list(result.failures)}")

        self.assertEqual(failures, [], f"Live agent eval failures: {failures}")


if __name__ == "__main__":
    unittest.main()
