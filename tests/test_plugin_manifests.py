#!/usr/bin/env python3
"""Validation tests for plugins/softprobe-blackbox manifests, MCP configs, assets, and skill."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLACKBOX_DIR = ROOT / "plugins" / "softprobe-blackbox"
EXPLORER_MCP_URL = "https://explorer.softprobe.ai/mcp"

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
    "list_agents",
    "create_agent",
    "get_ingestion_key",
)


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

    def test_blackbox_skill_covers_all_17_tools(self) -> None:
        self.assertEqual(len(EXPECTED_MCP_TOOLS), 17)
        skill_path = BLACKBOX_DIR / "skills" / "blackbox" / "SKILL.md"
        self.assertTrue(skill_path.is_file(), f"Missing {skill_path}")
        skill_text = skill_path.read_text(encoding="utf-8")
        self.assertIn(EXPLORER_MCP_URL, skill_text)
        for tool_name in EXPECTED_MCP_TOOLS:
            self.assertIn(f"`{tool_name}`", skill_text, f"Tool missing from SKILL.md: {tool_name}")

        ref_path = BLACKBOX_DIR / "skills" / "blackbox" / "references" / "mcp-tools.md"
        self.assertTrue(ref_path.is_file(), f"Missing {ref_path}")
        ref_text = ref_path.read_text(encoding="utf-8")
        self.assertIn("All 17 tools", ref_text)
        for tool_name in EXPECTED_MCP_TOOLS:
            self.assertIn(
                f"`{tool_name}`",
                ref_text,
                f"Tool missing from mcp-tools.md: {tool_name}",
            )


if __name__ == "__main__":
    unittest.main()
