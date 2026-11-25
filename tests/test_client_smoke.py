#!/usr/bin/env python3
"""Layer 3: Real CLI install/load smoke tests for Gemini CLI, Claude Code, and OpenCode."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLACKBOX_DIR = ROOT / "plugins" / "softprobe-blackbox"
OPENCODE_PLUGIN_DIST = ROOT.parent / "softprobe-js" / "packages" / "opencode-blackbox" / "dist" / "index.js"
EXPLORER_MCP_URL = "https://explorer.softprobe.ai/mcp"


class ClientSmokeTests(unittest.TestCase):
    @unittest.skipIf(shutil.which("gemini") is None, "gemini CLI is not installed")
    def test_gemini_extensions_validate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {**os.environ, "HOME": tmpdir, "XDG_CONFIG_HOME": tmpdir}
            proc = subprocess.run(
                ["gemini", "extensions", "validate", str(ROOT)],
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
                check=False,
            )
        self.assertEqual(
            proc.returncode,
            0,
            f"gemini extensions validate failed:\nstdout={proc.stdout}\nstderr={proc.stderr}",
        )
        self.assertIn("successfully validated", (proc.stdout + proc.stderr).lower())

    @unittest.skipIf(shutil.which("claude") is None, "claude CLI is not installed")
    def test_claude_plugin_validate_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {**os.environ, "HOME": tmpdir, "XDG_CONFIG_HOME": tmpdir}
            for target in (ROOT, BLACKBOX_DIR):
                proc = subprocess.run(
                    ["claude", "plugin", "validate", str(target)],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=30,
                    check=False,
                )
                self.assertEqual(
                    proc.returncode,
                    0,
                    f"claude plugin validate {target} failed:\nstdout={proc.stdout}\nstderr={proc.stderr}",
                )
                self.assertIn("Validation passed", proc.stdout + proc.stderr)

            load_proc = subprocess.run(
                ["claude", "--plugin-dir", str(BLACKBOX_DIR), "--version"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
                check=False,
            )
            self.assertEqual(
                load_proc.returncode,
                0,
                f"claude --plugin-dir --version failed:\nstdout={load_proc.stdout}\nstderr={load_proc.stderr}",
            )

    @unittest.skipIf(shutil.which("opencode") is None, "opencode CLI is not installed")
    @unittest.skipUnless(
        OPENCODE_PLUGIN_DIST.is_file(),
        f"Built opencode-blackbox plugin not found at {OPENCODE_PLUGIN_DIST}",
    )
    def test_opencode_loads_blackbox_plugin_and_registers_mcp(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_dir = tmp_path / "opencode"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "opencode.json").write_text(
                json.dumps(
                    {
                        "$schema": "https://opencode.ai/config.json",
                        "plugin": [OPENCODE_PLUGIN_DIST.as_uri()],
                    }
                ),
                encoding="utf-8",
            )
            env = {
                **os.environ,
                "HOME": tmpdir,
                "XDG_CONFIG_HOME": tmpdir,
                "OPENCODE_CONFIG_DIR": str(config_dir),
            }
            proc = subprocess.run(
                ["opencode", "debug", "config"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
                check=False,
            )
        self.assertEqual(
            proc.returncode,
            0,
            f"opencode debug config failed:\nstdout={proc.stdout}\nstderr={proc.stderr}",
        )
        config = json.loads(proc.stdout)
        blackbox_mcp = config.get("mcp", {}).get("blackbox")
        self.assertEqual(
            blackbox_mcp,
            {
                "type": "remote",
                "url": EXPLORER_MCP_URL,
                "enabled": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
