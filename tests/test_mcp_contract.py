#!/usr/bin/env python3
"""Layer 2: MCP contract & schema drift checks against explorer/src/mcp/tools.ts and live Explorer MCP."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unittest
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPLORER_TOOLS_TS = ROOT.parent / "explorer" / "src" / "mcp" / "tools.ts"
MCP_TOOLS_MD = ROOT / "plugins" / "softprobe-blackbox" / "skills" / "blackbox" / "references" / "mcp-tools.md"
EXPLORER_BASE_URL = "https://explorer.softprobe.ai"


@dataclass(frozen=True)
class ToolSchema:
    name: str
    required: frozenset[str]
    optional: frozenset[str]

    @property
    def all_params(self) -> frozenset[str]:
        return self.required | self.optional


def _extract_balanced_block(text: str, start_idx: int, open_ch: str, close_ch: str) -> tuple[str, int]:
    """Return substring inside balanced delimiters starting at start_idx, plus end index."""
    depth = 0
    in_str: str | None = None
    escaped = False
    for idx in range(start_idx, len(text)):
        ch = text[idx]
        if in_str is not None:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in ("'", '"', "`"):
            in_str = ch
            continue
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[start_idx + 1 : idx], idx
    raise ValueError(f"Unbalanced {open_ch}{close_ch} starting at {start_idx}")


def _split_top_level_entries(block: str) -> list[str]:
    """Split comma-separated top-level entries inside an object or array literal."""
    entries: list[str] = []
    depth_brace = 0
    depth_paren = 0
    depth_bracket = 0
    in_str: str | None = None
    escaped = False
    start = 0

    for idx, ch in enumerate(block):
        if in_str is not None:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in ("'", '"', "`"):
            in_str = ch
            continue
        if ch == "{":
            depth_brace += 1
        elif ch == "}":
            depth_brace -= 1
        elif ch == "(":
            depth_paren += 1
        elif ch == ")":
            depth_paren -= 1
        elif ch == "[":
            depth_bracket += 1
        elif ch == "]":
            depth_bracket -= 1
        elif ch == "," and depth_brace == 0 and depth_paren == 0 and depth_bracket == 0:
            chunk = block[start:idx].strip()
            if chunk:
                entries.append(chunk)
            start = idx + 1

    tail = block[start:].strip()
    if tail:
        entries.append(tail)
    return entries


def _parse_zod_object_schemas(ts_text: str) -> dict[str, tuple[frozenset[str], frozenset[str]]]:
    """Extract top-level const <name> = z.object({ ... }) definitions from tools.ts."""
    schemas: dict[str, tuple[frozenset[str], frozenset[str]]] = {}
    for match in re.finditer(r"const\s+(\w+)\s*=\s*z\.object\s*\(\s*\{", ts_text):
        schema_name = match.group(1)
        brace_idx = ts_text.find("{", match.start())
        body, _ = _extract_balanced_block(ts_text, brace_idx, "{", "}")
        required: set[str] = set()
        optional: set[str] = set()
        for entry in _split_top_level_entries(body):
            key_match = re.match(r"^(\w+)\s*:\s*(.*)$", entry, re.DOTALL)
            if not key_match:
                continue
            key, expr = key_match.group(1), key_match.group(2)
            if ".optional()" in expr:
                optional.add(key)
            else:
                required.add(key)
        schemas[schema_name] = (frozenset(required), frozenset(optional))
    return schemas


def parse_explorer_tools_ts(ts_text: str) -> dict[str, ToolSchema]:
    """Parse MCP_TOOLS from explorer/src/mcp/tools.ts into ToolSchema map."""
    zod_schemas = _parse_zod_object_schemas(ts_text)
    anchor = re.search(r"export\s+const\s+MCP_TOOLS\s*:\s*ToolDef\[\]\s*=\s*\[", ts_text)
    if not anchor:
        raise ValueError("Could not locate export const MCP_TOOLS in tools.ts")
    bracket_idx = anchor.end() - 1
    array_body, _ = _extract_balanced_block(ts_text, bracket_idx, "[", "]")

    tools: dict[str, ToolSchema] = {}
    for entry in _split_top_level_entries(array_body):
        name_match = re.search(r'\bname\s*:\s*["\']([^"\']+)["\']', entry)
        if not name_match:
            continue
        tool_name = name_match.group(1)

        zod_match = re.search(r"\binputSchema\s*:\s*z\.toJSONSchema\(\s*(\w+)\s*\)", entry)
        if zod_match:
            schema_name = zod_match.group(1)
            if schema_name not in zod_schemas:
                raise ValueError(f"Referenced Zod schema {schema_name} not found for {tool_name}")
            req, opt = zod_schemas[schema_name]
            tools[tool_name] = ToolSchema(name=tool_name, required=req, optional=opt)
            continue

        schema_match = re.search(r"\binputSchema\s*:\s*\{", entry)
        if not schema_match:
            raise ValueError(f"Missing inputSchema for tool {tool_name}")
        schema_brace = entry.find("{", schema_match.start())
        schema_body, _ = _extract_balanced_block(entry, schema_brace, "{", "}")

        all_props: set[str] = set()
        props_match = re.search(r"\bproperties\s*:\s*\{", schema_body)
        if props_match:
            props_brace = schema_body.find("{", props_match.start())
            props_body, _ = _extract_balanced_block(schema_body, props_brace, "{", "}")
            for prop_entry in _split_top_level_entries(props_body):
                prop_key_match = re.match(r"^(\w+)\s*:", prop_entry)
                if prop_key_match:
                    all_props.add(prop_key_match.group(1))

        req_props: set[str] = set()
        req_match = re.search(r"\brequired\s*:\s*\[", schema_body)
        if req_match:
            req_bracket = schema_body.find("[", req_match.start())
            req_body, _ = _extract_balanced_block(schema_body, req_bracket, "[", "]")
            req_props.update(re.findall(r'["\']([^"\']+)["\']', req_body))

        tools[tool_name] = ToolSchema(
            name=tool_name,
            required=frozenset(req_props),
            optional=frozenset(all_props - req_props),
        )
    return tools


def _extract_param_names_from_doc_segment(segment: str) -> set[str]:
    """Extract parameter names written as `param_name` (ignoring enum values after parens)."""
    # Strip parenthetical type/enum descriptions so enum values like `asc` | `desc` aren't treated as param names.
    without_parens = re.sub(r"\([^)]*\)", "", segment)
    return set(re.findall(r"`([a-z_][a-z0-9_]*)`", without_parens))


def parse_mcp_tools_doc(md_text: str) -> dict[str, ToolSchema]:
    """Parse tool names and required/optional parameter names from references/mcp-tools.md."""
    tools: dict[str, ToolSchema] = {}
    current_name: str | None = None
    required: set[str] = set()
    optional: set[str] = set()

    def flush() -> None:
        if current_name is not None:
            tools[current_name] = ToolSchema(
                name=current_name,
                required=frozenset(required),
                optional=frozenset(optional),
            )

    for line in md_text.splitlines():
        tool_match = re.match(r"^- `([a-z_][a-z0-9_]*)`(.*)$", line)
        if tool_match:
            flush()
            current_name = tool_match.group(1)
            required = set()
            optional = set()
            rest = tool_match.group(2)
            req_inline = re.search(r"\bRequired\b([^.]*)", rest)
            if req_inline:
                required.update(_extract_param_names_from_doc_segment(req_inline.group(1)))
            continue

        if current_name is None:
            continue

        req_line = re.match(r"^\s+-\s+Required:\s*(.+)$", line)
        if req_line:
            required.update(_extract_param_names_from_doc_segment(req_line.group(1)))
            continue

        opt_line = re.match(r"^\s+-\s+Optional:\s*(.+)$", line)
        if opt_line:
            optional.update(_extract_param_names_from_doc_segment(opt_line.group(1)))
            continue

    flush()
    return tools


class McpContractTests(unittest.TestCase):
    @unittest.skipUnless(
        EXPLORER_TOOLS_TS.is_file(),
        f"Skipping Explorer MCP contract check; {EXPLORER_TOOLS_TS} not checked out",
    )
    def test_mcp_tools_doc_matches_explorer_schema(self) -> None:
        source_tools = parse_explorer_tools_ts(EXPLORER_TOOLS_TS.read_text(encoding="utf-8"))
        doc_tools = parse_mcp_tools_doc(MCP_TOOLS_MD.read_text(encoding="utf-8"))

        self.assertEqual(
            set(doc_tools.keys()),
            set(source_tools.keys()),
            f"Tool drift: missing_in_doc={sorted(set(source_tools) - set(doc_tools))}, "
            f"extra_in_doc={sorted(set(doc_tools) - set(source_tools))}",
        )

        for name, src in source_tools.items():
            doc = doc_tools[name]
            self.assertEqual(
                doc.required,
                src.required,
                f"Required params mismatch for `{name}`: doc={sorted(doc.required)} src={sorted(src.required)}",
            )
            self.assertEqual(
                doc.optional,
                src.optional,
                f"Optional params mismatch for `{name}`: doc={sorted(doc.optional)} src={sorted(src.optional)}",
            )

    def test_live_explorer_mcp_discovery_and_auth_challenge(self) -> None:
        if os.environ.get("RUN_LIVE_MCP_CHECKS") != "1":
            self.skipTest("Set RUN_LIVE_MCP_CHECKS=1 (or pass --live) to run live Explorer MCP checks")
        well_known_url = f"{EXPLORER_BASE_URL}/.well-known/oauth-protected-resource"
        req = urllib.request.Request(
            well_known_url,
            headers={"User-Agent": "softprobe-skills-eval/1.0"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            self.assertEqual(resp.status, 200)
            metadata = json.loads(resp.read().decode("utf-8"))
        self.assertIsInstance(metadata, dict)
        self.assertTrue(
            "resource" in metadata or "authorization_servers" in metadata,
            f"Unexpected OAuth protected resource metadata keys: {sorted(metadata.keys())}",
        )

        mcp_url = f"{EXPLORER_BASE_URL}/mcp"
        payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "softprobe-skills-eval/1.0",
        }
        token = os.environ.get("BLACKBOX_MCP_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        mcp_req = urllib.request.Request(mcp_url, data=payload, headers=headers, method="POST")
        if token:
            with urllib.request.urlopen(mcp_req, timeout=15) as resp:
                self.assertEqual(resp.status, 200)
                body = json.loads(resp.read().decode("utf-8"))
            tools = {t["name"] for t in body.get("result", {}).get("tools", [])}
            doc_tools = set(parse_mcp_tools_doc(MCP_TOOLS_MD.read_text(encoding="utf-8")).keys())
            self.assertEqual(tools, doc_tools)
        else:
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(mcp_req, timeout=15)
            self.assertEqual(ctx.exception.code, 401)
            www_auth = ctx.exception.headers.get("www-authenticate", "")
            self.assertIn("Bearer", www_auth)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--live", action="store_true", help="Run live Explorer MCP checks")
    args, remaining = parser.parse_known_args()
    if args.live:
        os.environ["RUN_LIVE_MCP_CHECKS"] = "1"
    unittest.main(argv=[sys.argv[0], *remaining], verbosity=2)
