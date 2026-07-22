from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPOSITORY_ROOT / "plugins" / "codex-research-harness"
TEMPLATE_ROOT = PLUGIN_ROOT / "assets" / "project-template"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from harness_core import PROTOCOL_VERSION, initialize_project  # noqa: E402


class ResearchHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write(self, relative: str, content: str = "") -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_init_dry_run_is_read_only(self) -> None:
        self.write("README.md", "# Existing project\n")

        result = initialize_project(self.root, dry_run=True)

        self.assertEqual(result["mode"], "initialize")
        self.assertEqual(result["protocol_version"], "0.6.0")
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertFalse((self.root / "agent-docs").exists())

    def test_init_creates_only_the_minimal_protocol(self) -> None:
        result = initialize_project(self.root, "Example Project")

        self.assertTrue(result["ok"])
        self.assertTrue((self.root / "AGENTS.md").is_file())
        self.assertTrue((self.root / "CLAUDE.md").is_file())
        self.assertTrue((self.root / "agent-docs" / "project.md").is_file())
        self.assertTrue((self.root / "agent-docs" / "state.md").is_file())
        self.assertFalse((self.root / "agent-docs" / "index.md").exists())
        self.assertFalse((self.root / "agent-docs" / "decisions.md").exists())
        self.assertFalse((self.root / "agent-docs" / "checkpoint.md").exists())
        self.assertFalse((self.root / ".research-harness.json").exists())
        self.assertFalse((self.root / ".research-harness").exists())
        self.assertFalse((self.root / ".gitignore").exists())

        project = (self.root / "agent-docs" / "project.md").read_text(encoding="utf-8")
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Example Project", project)
        self.assertIn("| 目录 | 职责 | 变化时检查 |", project)
        self.assertIn("不维护文件清单", agents)
        self.assertIn("一个活动写任务", agents)

    def test_init_is_idempotent_and_preserves_user_content(self) -> None:
        initialize_project(self.root)
        agents = self.root / "AGENTS.md"
        project = self.root / "agent-docs" / "project.md"
        agents.write_text(agents.read_text(encoding="utf-8") + "\nUSER RULE\n", encoding="utf-8")
        project.write_text(project.read_text(encoding="utf-8") + "\nUSER PROJECT FACT\n", encoding="utf-8")

        result = initialize_project(self.root)

        agents_text = agents.read_text(encoding="utf-8")
        self.assertEqual(result["mode"], "refresh")
        self.assertEqual(agents_text.count("research-harness:protocol:start"), 1)
        self.assertIn("USER RULE", agents_text)
        self.assertIn("USER PROJECT FACT", project.read_text(encoding="utf-8"))

    def test_existing_claude_import_is_not_duplicated(self) -> None:
        self.write("CLAUDE.md", "# Existing instructions\n\n@AGENTS.md\n")

        initialize_project(self.root)
        initialize_project(self.root)

        claude = (self.root / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(claude.count("@AGENTS.md"), 1)
        self.assertNotIn("research-harness:claude-adapter:start", claude)

    def test_init_reports_legacy_state_without_deleting_it(self) -> None:
        self.write(".research-harness.json", "{}\n")
        self.write(".research-harness/snapshot.json", "{}\n")
        self.write("agent-docs/index.md", "# Old index\n")

        result = initialize_project(self.root, dry_run=True)

        self.assertIn(".research-harness.json", result["legacy_review_candidates"])
        self.assertIn(".research-harness", result["legacy_review_candidates"])
        self.assertIn("agent-docs/index.md", result["legacy_review_candidates"])
        self.assertTrue((self.root / ".research-harness" / "snapshot.json").is_file())

    def test_cli_only_exposes_init(self) -> None:
        version = subprocess.run(
            [str(REPOSITORY_ROOT / "bin" / "research-harness"), "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        removed = subprocess.run(
            [str(REPOSITORY_ROOT / "bin" / "research-harness"), "sync", str(self.root)],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(version.stdout.strip(), "research-harness 0.6.0")
        self.assertEqual(removed.returncode, 2)
        self.assertIn("invalid choice", removed.stderr)

    def test_cli_init_emits_json(self) -> None:
        completed = subprocess.run(
            [str(REPOSITORY_ROOT / "bin" / "research-harness"), "init", str(self.root), "--json"],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["protocol_version"], "0.6.0")
        self.assertEqual(payload["created"], ["agent-docs/project.md", "agent-docs/state.md"])

    def test_plugin_and_skill_contain_no_runtime_automation(self) -> None:
        self.assertTrue((PLUGIN_ROOT / "skills" / "research-harness" / "SKILL.md").is_file())
        self.assertFalse((PLUGIN_ROOT / "hooks").exists())
        self.assertFalse((PLUGIN_ROOT / "skills" / "research-harness" / "scripts").exists())
        self.assertFalse((TEMPLATE_ROOT / "index.block.md").exists())
        self.assertFalse((TEMPLATE_ROOT / "checkpoint.md").exists())

    def test_version_metadata_is_consistent(self) -> None:
        pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        plugin = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))

        self.assertEqual(PROTOCOL_VERSION, "0.6.0")
        self.assertIn('version = "0.6.0"', pyproject)
        self.assertTrue(plugin["version"].startswith("0.6.0+codex."))

    def test_standalone_zipapp_includes_minimal_templates(self) -> None:
        output = self.root / "research-harness.pyz"
        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "scripts" / "build_zipapp.py"), str(output)],
            check=True,
            capture_output=True,
            text=True,
        )
        target = self.root / "portable-project"
        target.mkdir()

        completed = subprocess.run(
            [sys.executable, str(output), "init", str(target), "--json"],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["protocol_version"], "0.6.0")
        self.assertTrue((target / "agent-docs" / "project.md").is_file())
        self.assertFalse((target / ".research-harness.json").exists())


if __name__ == "__main__":
    unittest.main()
