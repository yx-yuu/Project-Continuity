from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPOSITORY_ROOT / "plugins" / "codex-research-harness"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from harness_core import (  # noqa: E402
    clear_checkpoint,
    doctor_project,
    initialize_project,
    read_checkpoint,
    resume_project,
    save_checkpoint,
    scan_project,
    sync_project,
)


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

    def test_scan_is_read_only_and_filters_generated_paper_files(self) -> None:
        self.write("README.md", "# Existing project\n")
        self.write("paper/main.tex", "\\documentclass{article}\n")
        self.write("paper/main.aux", "generated\n")
        self.write("src/model.py", "VALUE = 1\n")
        self.write("dataset/artifacts/run.json", "{}\n")

        inventory = scan_project(self.root)

        self.assertIn("paper/main.tex", inventory.paper_files)
        self.assertNotIn("paper/main.aux", inventory.paper_files)
        self.assertEqual(inventory.source_directories, ["src"])
        self.assertIn("dataset/artifacts", inventory.artifact_directories)
        self.assertIn("README.md", inventory.context_documents)
        self.assertFalse((self.root / ".research-harness.json").exists())

    def test_scan_does_not_treat_an_empty_git_directory_as_a_repository(self) -> None:
        (self.root / ".git").mkdir()

        inventory = scan_project(self.root)

        self.assertFalse(inventory.git_repository)

    def test_init_is_idempotent_and_preserves_user_content(self) -> None:
        self.write("AGENTS.md", "# Existing instructions\n\nKeep this sentence.\n")
        self.write("CLAUDE.md", "# Existing Claude instructions\n\nKeep this Claude sentence.\n")
        first = initialize_project(self.root, "Example Project")
        project = self.root / "agent-docs" / "project.md"
        project.write_text(project.read_text(encoding="utf-8") + "\nUSER EDIT\n", encoding="utf-8")

        second = initialize_project(self.root, "Example Project")

        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        claude = (self.root / "CLAUDE.md").read_text(encoding="utf-8")
        index = (self.root / "agent-docs" / "index.md").read_text(encoding="utf-8")
        manifest = json.loads((self.root / ".research-harness.json").read_text(encoding="utf-8"))
        self.assertIn("Keep this sentence.", agents)
        self.assertIn("Keep this Claude sentence.", claude)
        self.assertEqual(agents.count("research-harness:protocol:start"), 1)
        self.assertEqual(claude.count("research-harness:claude-adapter:start"), 1)
        self.assertEqual(claude.count("@AGENTS.md"), 1)
        self.assertEqual(index.count("research-harness:index:start"), 1)
        self.assertIn("USER EDIT", project.read_text(encoding="utf-8"))
        self.assertIn("agent-docs/project.md", first["created"])
        self.assertNotIn("agent-docs/project.md", second["created"])
        self.assertEqual(manifest["context_model"], "project-control-plane")
        self.assertEqual(manifest["protocol_version"], "0.4.0")
        self.assertFalse((self.root / "agent-docs" / "claims.md").exists())
        self.assertFalse((self.root / "agent-docs" / "tasks").exists())
        self.assertFalse((self.root / "agent-docs" / "checkpoint.md").exists())

    def test_sync_detects_external_changes_and_accepts_a_new_baseline(self) -> None:
        existing = self.write("README.md", "one\n")
        initialize_project(self.root)
        existing.write_text("two\n", encoding="utf-8")
        self.write("imported/new.txt", "new\n")

        pending = sync_project(self.root)

        self.assertEqual(pending["counts"]["added"], 1)
        self.assertEqual(pending["counts"]["modified"], 1)
        self.assertFalse(pending["accepted"])
        self.assertTrue(any(row["path"] == "imported/new.txt" for row in pending["added"]))

        sync_project(self.root, accept=True)
        clean = sync_project(self.root)
        self.assertEqual(clean["counts"]["total"], 0)

    def test_init_keeps_an_existing_claude_agents_import_without_duplication(self) -> None:
        self.write("CLAUDE.md", "# Existing Claude instructions\n\n@AGENTS.md\n")

        initialize_project(self.root)
        initialize_project(self.root)

        claude = (self.root / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(claude.count("@AGENTS.md"), 1)
        self.assertNotIn("research-harness:claude-adapter:start", claude)
        self.assertNotIn("claude-adapter-missing", {check.code for check in doctor_project(self.root)})

    def test_checkpoint_is_single_replaceable_state_and_uses_trash(self) -> None:
        initialize_project(self.root)
        with self.assertRaisesRegex(ValueError, "任务契约缺少必填字段"):
            save_checkpoint(self.root, "incomplete", "state", "next")
        save_checkpoint(
            self.root, "first goal", "first state", "first next", facts=["fact one"],
            scope="src only", done="behavior verified", validation="targeted tests",
        )
        save_checkpoint(
            self.root, "second goal", "second state", "second next", decisions=["user chose B"],
            scope="paper and results", done="claims trace to artifacts", validation="doctor and link checks",
            impacts=["paper/main.tex"],
        )

        content = read_checkpoint(self.root)
        self.assertIsNotNone(content)
        self.assertIn("second goal", content)
        self.assertIn("user chose B", content)
        self.assertIn("paper and results", content)
        self.assertIn("claims trace to artifacts", content)
        self.assertIn("paper/main.tex", content)
        self.assertNotIn("first goal", content)

        trashed = clear_checkpoint(self.root)
        self.assertFalse(trashed.exists())

    def test_checkpoint_clear_refuses_pending_changes_until_sync_accept(self) -> None:
        initialize_project(self.root)
        save_checkpoint(
            self.root, "goal", "progress", "next", scope="src", done="done",
            validation="targeted", impacts=["paper"],
        )
        self.write("new-source.md", "candidate\n")

        with self.assertRaisesRegex(ValueError, "未确认文件变化"):
            clear_checkpoint(self.root)

        sync_project(self.root, accept=True)
        clear_checkpoint(self.root)
        self.assertIsNone(read_checkpoint(self.root))

    def test_resume_reports_checkpoint_and_pending_file_changes(self) -> None:
        initialize_project(self.root)
        save_checkpoint(
            self.root, "resume goal", "verified", "continue", scope="current task",
            done="recovery works", validation="resume", impacts=["state"],
        )
        self.write("new-source.md", "candidate\n")

        result = resume_project(self.root)

        self.assertIn("resume goal", result["checkpoint"])
        self.assertEqual(result["pending_changes"]["added"], 1)
        self.assertEqual(result["agent_entrypoints"]["claude_code"], "CLAUDE.md")
        self.assertIn("agent-docs/state.md", result["read_first"])

    def test_doctor_checks_budgets_links_sync_and_legacy_context(self) -> None:
        initialize_project(self.root)
        state = self.root / "agent-docs" / "state.md"
        state.write_text(state.read_text(encoding="utf-8") + "\n".join(["extra"] * 140), encoding="utf-8")
        self.write("agent-docs/bootstrap.md", "# old bootstrap\n")
        self.write("agent-docs/project.md", "# Project\n\n[missing](missing.md)\n")
        self.write("outside.txt", "new\n")

        checks = doctor_project(self.root)
        codes = {check.code for check in checks}

        self.assertIn("context-budget", codes)
        self.assertIn("legacy-context", codes)
        self.assertIn("broken-link", codes)
        self.assertIn("pending-sync", codes)
        self.assertIn("project-unconfirmed", codes)

    def test_doctor_checks_total_restore_budget_and_task_contract(self) -> None:
        initialize_project(self.root)
        manifest_path = self.root / ".research-harness.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["context_budgets"]["restore_context_bytes"] = 100
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.write("agent-docs/checkpoint.md", "# old checkpoint\n")

        codes = {check.code for check in doctor_project(self.root)}

        self.assertIn("restore-budget", codes)
        self.assertIn("task-contract-incomplete", codes)

    def test_hook_injects_recovery_context_only_for_initialized_projects(self) -> None:
        initialize_project(self.root)
        payload = json.dumps({"hook_event_name": "SessionStart", "cwd": str(self.root), "source": "startup"})
        env = dict(os.environ, PLUGIN_ROOT=str(PLUGIN_ROOT))
        completed = subprocess.run(
            [sys.executable, str(PLUGIN_ROOT / "hooks" / "context_hook.py")],
            input=payload,
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        output = json.loads(completed.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Research Harness 已启用", context)
        self.assertIn("服从项目约束", context)

    def test_cli_emits_machine_readable_resume(self) -> None:
        initialize_project(self.root)
        completed = subprocess.run(
            [str(REPOSITORY_ROOT / "bin" / "research-harness"), "resume", str(self.root), "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["root"], str(self.root))


if __name__ == "__main__":
    unittest.main()
