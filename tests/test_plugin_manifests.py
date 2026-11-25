#!/usr/bin/env python3
"""Validation tests for plugins/softprobe-blackbox manifests, MCP configs, assets, and skill."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLACKBOX_DIR = ROOT / "plugins" / "softprobe-blackbox"
EXPLORER_MCP_URL = "https://explorer.softprobe.ai/mcp"
EXPECTED_VERSION = "0.2.6"

EXPECTED_MCP_TOOLS = (
    "whoami",
    "list_workspaces",
    "select_workspace",
    "search_sessions",
    "get_session",
    "get_session_spans",
    "search_spans",
    "get_span",
    "search_traces",
    "list_trace_tags",
    "list_trace_tag_values",
    "get_trace",
    "logs_by_session",
    "logs_by_trace",
    "bootstrap_project",
    "list_agents",
    "create_agent",
    "get_ingestion_key",
    "compile_session_test",
)


def parse_frontmatter(markdown_text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", markdown_text, re.DOTALL)
    if not match:
        return {}
    fields: dict[str, str] = {}
    current_key: str | None = None
    for raw_line in match.group(1).splitlines():
        if not raw_line.strip():
            continue
        if raw_line.startswith((" ", "\t")) and current_key is not None:
            fields[current_key] = f"{fields[current_key]} {raw_line.strip()}".strip()
            continue
        if ":" in raw_line:
            key, value = raw_line.split(":", 1)
            current_key = key.strip()
            fields[current_key] = value.strip().strip("\"'")
    return fields


def extract_relative_markdown_links(markdown_text: str) -> list[str]:
    links: list[str] = []
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown_text):
        cleaned = target.strip().split("#", 1)[0]
        if not cleaned:
            continue
        if cleaned.startswith(("http://", "https://", "mailto:", "#")):
            continue
        links.append(cleaned)
    return links


class BlackboxPluginManifestTests(unittest.TestCase):
    def test_plugin_json_contract(self) -> None:
        manifest_path = BLACKBOX_DIR / "plugin.json"
        self.assertTrue(manifest_path.is_file(), f"Missing {manifest_path}")
        data = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(
            data.get("$schema"),
            "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        )
        self.assertEqual(data.get("name"), "softprobe-blackbox")
        self.assertEqual(data.get("version"), "0.2.6")
        self.assertTrue(isinstance(data.get("description"), str) and data["description"].strip())
        self.assertEqual(
            data.get("author"),
            {
                "name": "SoftProbe, Inc.",
                "email": "support@softprobe.ai",
                "url": "https://softprobe.ai",
            },
        )
        self.assertEqual(data.get("homepage"), "https://explorer.softprobe.ai")
        self.assertEqual(data.get("repository"), "https://github.com/softprobe/softprobe-plugin")
        self.assertEqual(data.get("license"), "MIT")
        self.assertEqual(
            data.get("keywords"),
            ["softprobe", "blackbox", "mcp", "observability", "opentelemetry", "debugging"],
        )

        openai_ext = data.get("extensions", {}).get("com.openai", {})
        self.assertEqual(openai_ext.get("displayName"), "Softprobe Blackbox")
        self.assertEqual(openai_ext.get("category"), "Developer Tools")
        logo_rel = openai_ext.get("logo")
        self.assertEqual(logo_rel, "assets/softprobe-mark.svg")
        logo_path = BLACKBOX_DIR / logo_rel
        self.assertTrue(logo_path.is_file(), f"Logo asset missing: {logo_path}")

    def test_svg_assets_exist_and_are_svg(self) -> None:
        for asset in (
            ROOT / "assets" / "softprobe-mark.svg",
            BLACKBOX_DIR / "assets" / "softprobe-mark.svg",
        ):
            self.assertTrue(asset.is_file(), f"Missing SVG asset: {asset}")
            content = asset.read_text(encoding="utf-8")
            self.assertIn("<svg", content)
            self.assertIn("</svg>", content)

    def test_mcp_configs_point_to_explorer_mcp(self) -> None:
        dot_mcp = json.loads((BLACKBOX_DIR / ".mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(
            dot_mcp,
            {
                "mcpServers": {
                    "blackbox": {
                        "type": "http",
                        "url": EXPLORER_MCP_URL,
                    }
                }
            },
        )

        mcp_cfg = json.loads((BLACKBOX_DIR / "mcp_config.json").read_text(encoding="utf-8"))
        self.assertEqual(
            mcp_cfg,
            {
                "mcpServers": {
                    "blackbox": {
                        "url": EXPLORER_MCP_URL,
                    }
                }
            },
        )

    def test_blackbox_skill_covers_all_tools(self) -> None:
        self.assertEqual(len(EXPECTED_MCP_TOOLS), 19)
        skill_path = BLACKBOX_DIR / "skills" / "blackbox" / "SKILL.md"
        self.assertTrue(skill_path.is_file(), f"Missing {skill_path}")
        skill_text = skill_path.read_text(encoding="utf-8")
        self.assertIn(EXPLORER_MCP_URL, skill_text)
        for tool_name in EXPECTED_MCP_TOOLS:
            self.assertIn(f"`{tool_name}`", skill_text, f"Tool missing from SKILL.md: {tool_name}")

        ref_path = BLACKBOX_DIR / "skills" / "blackbox" / "references" / "mcp-tools.md"
        self.assertTrue(ref_path.is_file(), f"Missing {ref_path}")
        ref_text = ref_path.read_text(encoding="utf-8")
        self.assertIn("All 19 tools", ref_text)
        for tool_name in EXPECTED_MCP_TOOLS:
            self.assertIn(
                f"`{tool_name}`",
                ref_text,
                f"Tool missing from mcp-tools.md: {tool_name}",
            )

    def test_marketplace_manifests_and_paths(self) -> None:
        claude_mp = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(claude_mp.get("name"), "softprobe")
        self.assertEqual(claude_mp.get("metadata", {}).get("version"), EXPECTED_VERSION)
        claude_plugins = claude_mp.get("plugins", [])
        self.assertTrue(claude_plugins)
        bb_claude = next((p for p in claude_plugins if p.get("name") == "softprobe-blackbox"), None)
        self.assertIsNotNone(bb_claude)
        self.assertEqual(bb_claude.get("version"), EXPECTED_VERSION)
        self.assertTrue((ROOT / bb_claude["source"]).is_dir())

        cursor_mp = json.loads((ROOT / ".cursor-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(cursor_mp.get("name"), "softprobe")
        self.assertEqual(cursor_mp.get("metadata", {}).get("version"), EXPECTED_VERSION)
        bb_cursor = next((p for p in cursor_mp.get("plugins", []) if p.get("name") == "softprobe-blackbox"), None)
        self.assertIsNotNone(bb_cursor)
        self.assertTrue((ROOT / bb_cursor["source"]).is_dir())

        agents_mp = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(agents_mp.get("name"), "softprobe")
        bb_agents = next((p for p in agents_mp.get("plugins", []) if p.get("name") == "softprobe-blackbox"), None)
        self.assertIsNotNone(bb_agents)
        self.assertEqual(bb_agents.get("source", {}).get("source"), "local")
        self.assertTrue((ROOT / bb_agents["source"]["path"]).is_dir())

    def test_client_plugin_manifests_and_version_parity(self) -> None:
        claude_plugin = json.loads(
            (BLACKBOX_DIR / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(claude_plugin.get("name"), "softprobe-blackbox")
        self.assertEqual(claude_plugin.get("version"), EXPECTED_VERSION)
        self.assertEqual(claude_plugin.get("license"), "MIT")
        self.assertEqual(
            claude_plugin.get("mcpServers", {}).get("blackbox"),
            {"type": "http", "url": EXPLORER_MCP_URL},
        )
        for rel_skill in claude_plugin.get("skills", []):
            skill_dir = BLACKBOX_DIR / rel_skill
            self.assertTrue(skill_dir.is_dir(), f"Missing skill dir: {skill_dir}")
            self.assertTrue((skill_dir / "SKILL.md").is_file(), f"Missing SKILL.md in {skill_dir}")

        cursor_plugin = json.loads(
            (BLACKBOX_DIR / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(cursor_plugin.get("name"), "softprobe-blackbox")
        self.assertEqual(cursor_plugin.get("version"), EXPECTED_VERSION)
        self.assertEqual(cursor_plugin.get("license"), "MIT")

        gemini_ext = json.loads((ROOT / "gemini-extension.json").read_text(encoding="utf-8"))
        self.assertEqual(gemini_ext.get("name"), "softprobe")
        self.assertEqual(gemini_ext.get("version"), EXPECTED_VERSION)
        context_file = ROOT / gemini_ext["contextFileName"]
        self.assertTrue(context_file.is_file(), f"Missing contextFileName target: {context_file}")
        self.assertEqual(
            gemini_ext.get("mcpServers", {}).get("blackbox", {}).get("httpUrl"),
            EXPLORER_MCP_URL,
        )

        skills_sh = json.loads((ROOT / "skills.sh.json").read_text(encoding="utf-8"))
        skill_paths = skills_sh.get("skills", [])
        self.assertTrue(skill_paths)
        for rel_skill in skill_paths:
            skill_dir = ROOT / rel_skill
            self.assertTrue(skill_dir.is_dir(), f"Missing skills.sh.json dir: {skill_dir}")
            self.assertTrue((skill_dir / "SKILL.md").is_file(), f"Missing SKILL.md in {skill_dir}")

    def test_skill_frontmatter_and_relative_links(self) -> None:
        skill_path = BLACKBOX_DIR / "skills" / "blackbox" / "SKILL.md"
        skill_text = skill_path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(skill_text)
        self.assertEqual(frontmatter.get("name"), "blackbox")
        self.assertTrue(frontmatter.get("description"), "SKILL.md frontmatter missing description")
        self.assertTrue(frontmatter.get("when_to_use"), "SKILL.md frontmatter missing when_to_use")

        rel_links = extract_relative_markdown_links(skill_text)
        self.assertTrue(rel_links, "Expected relative links in SKILL.md")
        for target in rel_links:
            resolved = skill_path.parent / target
            self.assertTrue(resolved.exists(), f"Broken relative link in SKILL.md: {target}")


if __name__ == "__main__":
    unittest.main()
