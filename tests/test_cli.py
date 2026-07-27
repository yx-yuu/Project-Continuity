from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest import mock
from zipfile import ZipFile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPOSITORY_ROOT / "plugins" / "project-continuity"
TEMPLATE_ROOT = PLUGIN_ROOT / "assets" / "project-template"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import continuity_core  # noqa: E402
from continuity_core import PROTOCOL_VERSION, initialize_project  # noqa: E402


def cli_command(*arguments: str) -> list[str]:
    """Build a command that invokes the platform-native CLI wrapper."""
    if sys.platform == "win32":
        launcher = REPOSITORY_ROOT / "bin" / "project-continuity.cmd"
        return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(launcher), *arguments]
    launcher = REPOSITORY_ROOT / "bin" / "project-continuity"
    return [str(launcher), *arguments]


class ProjectContinuityTests(unittest.TestCase):
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
        self.assertEqual(result["protocol_version"], "0.10.0")
        self.assertEqual(
            result["created"],
            ["AGENTS.md", "CLAUDE.md", "agent-docs/project.md", "agent-docs/state.md"],
        )
        self.assertEqual(result["updated"], [])
        self.assertEqual(result["unchanged"], [])
        self.assertEqual(result["planned"], result["created"])
        self.assertIn(
            "existing user content outside managed blocks in AGENTS.md and CLAUDE.md",
            result["preserves"],
        )
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertFalse((self.root / "agent-docs").exists())

    def test_init_creates_only_the_minimal_protocol(self) -> None:
        result = initialize_project(self.root, "Example Project")

        self.assertTrue(result["ok"])
        self.assertEqual(
            result["created"],
            ["AGENTS.md", "CLAUDE.md", "agent-docs/project.md", "agent-docs/state.md"],
        )
        self.assertEqual(result["updated"], [])
        self.assertEqual(result["unchanged"], [])
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
        self.assertIn("## 当前长期规则", project)
        self.assertIn("## 当前项目目标", project)
        self.assertIn("## 当前有效知识与约束", project)
        self.assertIn("| 目录或来源 | 权威范围 | 读取或复核条件 |", project)
        self.assertIn("不维护文件清单", agents)
        self.assertIn("一个未完成写任务", agents)
        self.assertNotIn("## 当前研究问题", project)

    def test_init_is_idempotent_and_preserves_user_content(self) -> None:
        initialize_project(self.root)
        agents = self.root / "AGENTS.md"
        project = self.root / "agent-docs" / "project.md"
        agents.write_text(agents.read_text(encoding="utf-8") + "\nUSER RULE\n", encoding="utf-8")
        project.write_text(project.read_text(encoding="utf-8") + "\nUSER PROJECT FACT\n", encoding="utf-8")

        result = initialize_project(self.root)

        agents_text = agents.read_text(encoding="utf-8")
        self.assertEqual(result["mode"], "refresh")
        self.assertEqual(result["planned"], [])
        self.assertEqual(result["created"], [])
        self.assertEqual(result["updated"], [])
        self.assertEqual(
            result["unchanged"],
            ["AGENTS.md", "CLAUDE.md", "agent-docs/project.md", "agent-docs/state.md"],
        )
        self.assertEqual(agents_text.count("project-continuity:protocol:start"), 1)
        self.assertIn("USER RULE", agents_text)
        self.assertIn("USER PROJECT FACT", project.read_text(encoding="utf-8"))

    def test_init_retries_against_latest_content_after_a_concurrent_change(self) -> None:
        agents = self.write("AGENTS.md", "# Existing agents\n\nORIGINAL USER CONTENT\n")
        real_atomic_write = continuity_core._atomic_write_texts
        injected = False

        def inject_change(
            writes: dict[Path, str],
            expected: dict[Path, str | None],
        ) -> tuple[Path, ...]:
            nonlocal injected
            if not injected:
                injected = True
                agents.write_text(
                    agents.read_text(encoding="utf-8") + "\nCONCURRENT USER CONTENT\n",
                    encoding="utf-8",
                )
            return real_atomic_write(writes, expected)

        with mock.patch.object(continuity_core, "_atomic_write_texts", side_effect=inject_change):
            result = initialize_project(self.root)

        text = agents.read_text(encoding="utf-8")
        self.assertTrue(injected)
        self.assertIn("ORIGINAL USER CONTENT", text)
        self.assertIn("CONCURRENT USER CONTENT", text)
        self.assertEqual(text.count("project-continuity:protocol:start"), 1)
        self.assertEqual(result["updated"], ["AGENTS.md"])

    def test_init_stops_after_repeated_concurrent_changes(self) -> None:
        self.write("AGENTS.md", "# Existing agents\n")
        error = continuity_core.ConcurrentModificationError("simulated concurrent change")

        with mock.patch.object(continuity_core, "_atomic_write_texts", side_effect=error) as atomic:
            with self.assertRaisesRegex(continuity_core.ConcurrentModificationError, "simulated"):
                initialize_project(self.root)

        self.assertEqual(atomic.call_count, continuity_core.MAX_CONCURRENT_RETRIES)

    def test_init_discloses_partial_writes_after_concurrent_retries_are_exhausted(self) -> None:
        agents = self.write("AGENTS.md", "# Existing agents\n")
        error = continuity_core.ConcurrentModificationError(
            "simulated concurrent change",
            (agents,),
        )

        with mock.patch.object(continuity_core, "_atomic_write_texts", side_effect=error):
            with self.assertRaisesRegex(
                continuity_core.ConcurrentModificationError,
                r"已写入部分控制文档 \(AGENTS.md\).+重新运行 init",
            ):
                initialize_project(self.root)

    def test_init_retries_a_change_during_commit_and_reports_all_actual_writes(self) -> None:
        agents = self.write("AGENTS.md", "# Existing agents\n\nORIGINAL USER CONTENT\n")
        claude = self.write("CLAUDE.md", "# Existing Claude instructions\n")
        real_verify = continuity_core._verify_expected_contents
        verify_calls = 0
        injected = False

        def inject_during_commit(expected: dict[Path, str | None]) -> None:
            nonlocal verify_calls, injected
            verify_calls += 1
            if verify_calls == 4:
                injected = True
                claude.write_text(
                    claude.read_text(encoding="utf-8") + "\nCONCURRENT CLAUDE CONTENT\n",
                    encoding="utf-8",
                )
            real_verify(expected)

        with mock.patch.object(
            continuity_core,
            "_verify_expected_contents",
            side_effect=inject_during_commit,
        ):
            result = initialize_project(self.root)

        self.assertTrue(injected)
        self.assertIn("ORIGINAL USER CONTENT", agents.read_text(encoding="utf-8"))
        self.assertIn("CONCURRENT CLAUDE CONTENT", claude.read_text(encoding="utf-8"))
        self.assertEqual(result["mode"], "initialize")
        self.assertEqual(result["existing_agent_docs"], [])
        self.assertEqual(result["created"], ["agent-docs/project.md", "agent-docs/state.md"])
        self.assertEqual(result["updated"], ["AGENTS.md", "CLAUDE.md"])
        self.assertEqual(result["unchanged"], [])
        self.assertEqual(
            result["planned"],
            ["agent-docs/project.md", "agent-docs/state.md", "AGENTS.md", "CLAUDE.md"],
        )

    def test_init_preserves_existing_crlf_content_and_newlines(self) -> None:
        originals = {
            self.root / "AGENTS.md": b"# Existing instructions\r\n\r\nUSER RULE\r\n",
            self.root / "agent-docs" / "project.md": b"# Existing project\r\n\r\nPROJECT FACT\r\n",
        }
        for path, content in originals.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

        initialize_project(self.root)
        initialize_project(self.root)

        for path, original in originals.items():
            with self.subTest(path=path.name):
                updated = path.read_bytes()
                self.assertTrue(updated.startswith(original))
                self.assertNotIn(b"\n", updated.replace(b"\r\n", b""))
                self.assertNotIn(b"\r", updated.replace(b"\r\n", b""))

    def test_existing_claude_import_is_not_duplicated(self) -> None:
        self.write("CLAUDE.md", "# Existing instructions\n\n@AGENTS.md\n")

        initialize_project(self.root)
        initialize_project(self.root)

        claude = (self.root / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(claude.count("@AGENTS.md"), 1)
        self.assertIn("project-continuity:claude-adapter:start", claude)
        self.assertIn("auto memory", claude)

    def test_init_migrates_claude_import_out_of_legacy_managed_block(self) -> None:
        self.write(
            "CLAUDE.md",
            (
                "# Existing instructions\n\n"
                "<!-- research-harness:claude-adapter:start -->\n"
                "@AGENTS.md\n\n## Claude Code 适配\n\nOLD ADAPTER\n"
                "<!-- research-harness:claude-adapter:end -->\n"
            ),
        )

        initialize_project(self.root)
        initialize_project(self.root)

        claude = (self.root / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(claude.count("@AGENTS.md"), 1)
        self.assertNotIn("OLD ADAPTER", claude)
        self.assertNotIn("research-harness:claude-adapter", claude)
        self.assertIn("project-continuity:claude-adapter:start", claude)
        self.assertIn("auto memory", claude)

    def test_init_migrates_legacy_protocol_markers_in_place(self) -> None:
        agents = self.write(
            "AGENTS.md",
            (
                "# Existing instructions\n\nUSER PREFIX\n\n"
                "<!-- research-harness:protocol:start -->\nOLD PROTOCOL\n"
                "<!-- research-harness:protocol:end -->\n\nUSER SUFFIX\n"
            ),
        )

        result = initialize_project(self.root)
        initialize_project(self.root)

        text = agents.read_text(encoding="utf-8")
        self.assertEqual(result["mode"], "refresh")
        self.assertEqual(text.count("project-continuity:protocol:start"), 1)
        self.assertEqual(text.count("project-continuity:protocol:end"), 1)
        self.assertNotIn("research-harness:protocol", text)
        self.assertNotIn("OLD PROTOCOL", text)
        self.assertIn("USER PREFIX", text)
        self.assertIn("USER SUFFIX", text)

    def test_init_ignores_marker_examples_in_markdown_code(self) -> None:
        agents = self.write(
            "AGENTS.md",
            (
                "# Marker examples\n\n"
                "```markdown\n"
                "<!-- project-continuity:protocol:start -->\n"
                "FENCED EXAMPLE\n"
                "<!-- project-continuity:protocol:end -->\n"
                "```\n\n"
                "    <!-- research-harness:protocol:start -->\n"
                "    INDENTED EXAMPLE\n"
                "    <!-- research-harness:protocol:end -->\n"
            ),
        )

        result = initialize_project(self.root)

        text = agents.read_text(encoding="utf-8")
        self.assertEqual(result["mode"], "initialize")
        self.assertIn("FENCED EXAMPLE", text)
        self.assertIn("INDENTED EXAMPLE", text)
        self.assertGreater(
            text.rindex("<!-- project-continuity:protocol:start -->"),
            text.rindex("```"),
        )

    def test_real_markers_can_coexist_with_fenced_examples(self) -> None:
        initialize_project(self.root)
        agents = self.root / "AGENTS.md"
        example = (
            "```markdown\n"
            "<!-- project-continuity:protocol:start -->\n"
            "FENCED EXAMPLE\n"
            "<!-- project-continuity:protocol:end -->\n"
            "```\n\n"
        )
        agents.write_text(example + agents.read_text(encoding="utf-8"), encoding="utf-8")

        result = initialize_project(self.root)

        text = agents.read_text(encoding="utf-8")
        self.assertEqual(result["mode"], "refresh")
        self.assertIn("FENCED EXAMPLE", text)
        self.assertEqual(text.count("<!-- project-continuity:protocol:start -->"), 2)

    def test_init_ignores_fenced_markers_after_utf8_bom(self) -> None:
        agents = self.write(
            "AGENTS.md",
            (
                "\ufeff```markdown\n"
                "<!-- project-continuity:protocol:start -->\n"
                "FENCED EXAMPLE\n"
                "<!-- project-continuity:protocol:end -->\n"
                "```\n"
            ),
        )

        result = initialize_project(self.root)

        text = agents.read_text(encoding="utf-8")
        self.assertEqual(result["mode"], "initialize")
        self.assertTrue(text.startswith("\ufeff```markdown\n"))
        self.assertIn("FENCED EXAMPLE", text)
        self.assertEqual(text.count("<!-- project-continuity:protocol:start -->"), 2)

    def test_invalid_backtick_info_string_is_not_treated_as_a_fence(self) -> None:
        agents = self.write("AGENTS.md", "# Existing\n\n```language`option\n")

        result = initialize_project(self.root)

        self.assertEqual(result["mode"], "initialize")
        self.assertIn(
            "<!-- project-continuity:protocol:start -->",
            agents.read_text(encoding="utf-8"),
        )

    def test_init_rejects_unclosed_fences_before_writing(self) -> None:
        cases = {
            "agents": ("AGENTS.md", "```markdown\nunfinished\n"),
            "claude": ("CLAUDE.md", "~~~text\nunfinished\n"),
            "project": ("agent-docs/project.md", "# Project\n\n```\nunfinished\n"),
        }
        for name, (relative, content) in cases.items():
            with self.subTest(name=name):
                target = self.root / name
                target.mkdir()
                path = target / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

                with self.assertRaisesRegex(ValueError, "未闭合"):
                    initialize_project(target)

                self.assertFalse((target / "agent-docs" / "state.md").exists())
                if relative != "AGENTS.md":
                    self.assertFalse((target / "AGENTS.md").exists())
                if relative != "CLAUDE.md":
                    self.assertFalse((target / "CLAUDE.md").exists())

    def test_init_adds_missing_rule_section_without_rewriting_project_content(self) -> None:
        project = self.write(
            "agent-docs/project.md",
            "# Existing Project\n\nUSER PROJECT FACT\n\n## 项目结构与入口\n\nExisting structure.\n",
        )

        initialize_project(self.root)
        initialize_project(self.root)

        text = project.read_text(encoding="utf-8")
        self.assertIn("USER PROJECT FACT", text)
        self.assertEqual(text.count("## 当前长期规则"), 1)
        self.assertEqual(text.count("## 项目结构与入口"), 1)

    def test_init_rejects_corrupt_or_duplicate_managed_markers(self) -> None:
        cases = {
            "missing-end": "<!-- project-continuity:protocol:start -->\nOLD RULE\n",
            "duplicate": (
                "<!-- project-continuity:protocol:start -->\nOLD RULE\n"
                "<!-- project-continuity:protocol:end -->\n"
                "<!-- project-continuity:protocol:start -->\nOTHER RULE\n"
                "<!-- project-continuity:protocol:end -->\n"
            ),
            "mixed-generations": (
                "<!-- research-harness:protocol:start -->\nOLD RULE\n"
                "<!-- research-harness:protocol:end -->\n"
                "<!-- project-continuity:protocol:start -->\nOTHER RULE\n"
                "<!-- project-continuity:protocol:end -->\n"
            ),
        }
        for name, content in cases.items():
            with self.subTest(name=name):
                target = self.root / name
                target.mkdir()
                (target / "AGENTS.md").write_text(content, encoding="utf-8")

                with self.assertRaisesRegex(ValueError, "受管理区块"):
                    initialize_project(target)

                self.assertFalse((target / "CLAUDE.md").exists())
                self.assertFalse((target / "agent-docs").exists())

    def test_init_rejects_invalid_control_paths_before_writing(self) -> None:
        cases = ("agent-docs", "agent-docs/project.md", "agent-docs/state.md")
        for index, relative in enumerate(cases):
            with self.subTest(relative=relative):
                target = self.root / f"invalid-{index}"
                target.mkdir()
                path = target / relative
                if relative == "agent-docs":
                    path.write_text("not a directory\n", encoding="utf-8")
                else:
                    path.mkdir(parents=True)

                with self.assertRaisesRegex(ValueError, "控制文档"):
                    initialize_project(target)

                self.assertFalse((target / "AGENTS.md").exists())
                self.assertFalse((target / "CLAUDE.md").exists())

    @unittest.skipIf(os.name == "nt", "POSIX permission bits are required for this test")
    def test_init_preflights_readonly_claude_before_any_writes(self) -> None:
        agents = self.write("AGENTS.md", "# Existing agents\n\nUSER RULE\n")
        claude = self.write("CLAUDE.md", "# Existing Claude instructions\n")
        agents_before = agents.read_bytes()
        claude_before = claude.read_bytes()
        claude.chmod(0o444)

        try:
            with self.assertRaisesRegex(PermissionError, "不可写"):
                initialize_project(self.root)
        finally:
            claude.chmod(0o644)

        self.assertEqual(agents.read_bytes(), agents_before)
        self.assertEqual(claude.read_bytes(), claude_before)
        self.assertFalse((self.root / "agent-docs").exists())

    @unittest.skipIf(os.name == "nt", "POSIX permission bits are required for this test")
    def test_init_preflights_readonly_project_before_any_writes(self) -> None:
        agents = self.write("AGENTS.md", "# Existing agents\n\nUSER RULE\n")
        project = self.write("agent-docs/project.md", "# Existing project\n\nPROJECT FACT\n")
        agents_before = agents.read_bytes()
        project_before = project.read_bytes()
        project.chmod(0o444)

        try:
            with self.assertRaisesRegex(PermissionError, "不可写"):
                initialize_project(self.root)
        finally:
            project.chmod(0o644)

        self.assertEqual(agents.read_bytes(), agents_before)
        self.assertEqual(project.read_bytes(), project_before)
        self.assertFalse((self.root / "CLAUDE.md").exists())
        self.assertFalse((self.root / "agent-docs" / "state.md").exists())

    def test_init_rolls_back_if_an_atomic_replace_fails(self) -> None:
        agents = self.write("AGENTS.md", "# Existing agents\n\nUSER RULE\n")
        agents_before = agents.read_bytes()
        real_replace = os.replace
        replace_calls = 0

        def flaky_replace(source: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
            nonlocal replace_calls
            replace_calls += 1
            if replace_calls == 2:
                raise OSError("simulated replace failure")
            real_replace(source, target)

        with mock.patch.object(continuity_core.os, "replace", side_effect=flaky_replace):
            with self.assertRaisesRegex(OSError, "simulated replace failure"):
                initialize_project(self.root)

        self.assertEqual(agents.read_bytes(), agents_before)
        self.assertFalse((self.root / "CLAUDE.md").exists())
        self.assertFalse((self.root / "agent-docs").exists())
        self.assertEqual(list(self.root.rglob("*.tmp")), [])

    def test_failed_rollback_does_not_overwrite_a_new_concurrent_change(self) -> None:
        agents = self.write("AGENTS.md", "# Existing agents\n\nUSER RULE\n")
        real_replace = os.replace
        replace_calls = 0

        def fail_after_concurrent_change(
            source: str | os.PathLike[str],
            target: str | os.PathLike[str],
        ) -> None:
            nonlocal replace_calls
            replace_calls += 1
            if replace_calls == 2:
                agents.write_text(
                    agents.read_text(encoding="utf-8") + "\nCONCURRENT USER CONTENT\n",
                    encoding="utf-8",
                )
                raise OSError("simulated replace failure")
            real_replace(source, target)

        with mock.patch.object(
            continuity_core.os,
            "replace",
            side_effect=fail_after_concurrent_change,
        ):
            with self.assertRaisesRegex(OSError, "回滚不完整"):
                initialize_project(self.root)

        text = agents.read_text(encoding="utf-8")
        self.assertIn("USER RULE", text)
        self.assertIn("CONCURRENT USER CONTENT", text)
        self.assertEqual(text.count("project-continuity:protocol:start"), 1)
        self.assertFalse((self.root / "CLAUDE.md").exists())
        self.assertFalse((self.root / "agent-docs").exists())
        self.assertEqual(list(self.root.rglob("*.tmp")), [])

    @unittest.skipIf(os.name == "nt", "POSIX file modes are required for this test")
    def test_atomic_refresh_preserves_existing_file_mode(self) -> None:
        agents = self.write("AGENTS.md", "# Existing agents\n")
        agents.chmod(0o640)
        original_mode = agents.stat().st_mode & 0o777

        initialize_project(self.root)

        self.assertEqual(agents.stat().st_mode & 0o777, original_mode)

    @unittest.skipIf(os.name == "nt", "Creating symlinks is not reliably available on Windows CI")
    def test_init_rejects_symlinked_control_paths_before_writing(self) -> None:
        cases = (
            ("agent-docs", True),
            ("AGENTS.md", False),
            ("CLAUDE.md", False),
            ("agent-docs/project.md", False),
            ("agent-docs/state.md", False),
        )
        for index, (relative, is_directory) in enumerate(cases):
            with self.subTest(relative=relative):
                target = self.root / f"symlink-{index}"
                target.mkdir()
                link = target / relative
                link.parent.mkdir(parents=True, exist_ok=True)
                real = target / ("real-control-dir" if is_directory else "real-control.md")
                if is_directory:
                    real.mkdir()
                else:
                    real.write_text("ORIGINAL\n", encoding="utf-8")
                link.symlink_to(real, target_is_directory=is_directory)

                with self.assertRaisesRegex(ValueError, "符号链接"):
                    initialize_project(target)

                if not is_directory:
                    self.assertEqual(real.read_text(encoding="utf-8"), "ORIGINAL\n")
                if relative != "AGENTS.md":
                    self.assertFalse((target / "AGENTS.md").exists())
                if relative != "CLAUDE.md":
                    self.assertFalse((target / "CLAUDE.md").exists())

    @unittest.skipIf(os.name == "nt", "Creating symlinks is not reliably available on Windows CI")
    def test_init_does_not_follow_agent_docs_symlink_created_during_commit(self) -> None:
        external = self.root / "external-control-dir"
        external.mkdir()
        docs = self.root / "agent-docs"
        real_atomic_write = continuity_core._atomic_write_texts
        injected = False

        def inject_symlink(
            writes: dict[Path, str],
            expected: dict[Path, str | None],
        ) -> tuple[Path, ...]:
            nonlocal injected
            if not injected:
                injected = True
                docs.symlink_to(external, target_is_directory=True)
            return real_atomic_write(writes, expected)

        with mock.patch.object(
            continuity_core,
            "_atomic_write_texts",
            side_effect=inject_symlink,
        ):
            with self.assertRaisesRegex(ValueError, "符号链接"):
                initialize_project(self.root)

        self.assertTrue(injected)
        self.assertEqual(list(external.iterdir()), [])
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertFalse((self.root / "CLAUDE.md").exists())

    def test_protocol_defines_scoped_lossless_mutations_and_paused_tasks(self) -> None:
        agents = (TEMPLATE_ROOT / "AGENTS.block.md").read_text(encoding="utf-8")
        rules = (TEMPLATE_ROOT / "project.rules.md").read_text(encoding="utf-8")
        structure = (TEMPLATE_ROOT / "project.structure.md").read_text(encoding="utf-8")
        state = (TEMPLATE_ROOT / "state.md").read_text(encoding="utf-8")
        skill = (PLUGIN_ROOT / "skills" / "project-continuity" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("当前操作、当前任务、当前项目、项目子树还是用户所有项目", agents)
        self.assertIn("添加", agents)
        self.assertIn("替换", agents)
        self.assertIn("删除", agents)
        self.assertIn("不因文档较长而压缩", agents)
        self.assertIn("`active` 或 `paused`", agents)
        self.assertIn("另一写任务使用独立 worktree", agents)
        self.assertIn("不调用 Project Continuity skill", agents)
        self.assertIn("才重新判断是否持久化", agents)
        self.assertIn("会影响后续任务的稳定项目事实", agents)
        self.assertIn("需要跨会话恢复的项目阶段或未完成任务状态", agents)
        self.assertIn("普通讨论、分析、建议、搜索结果和任务输出本身不触发写入", agents)
        self.assertIn("目标状态与 agent 核验的项目当前事实是不同对象", agents)
        self.assertIn("核验一致后只保留统一的当前形式", agents)
        self.assertIn("真实项目状态决定事实表述", agents)
        self.assertIn("只应用作用域覆盖当前任务且会实质影响当前判断的信息", agents)
        self.assertIn("修改持久化内容前重新读取目标文件", agents)
        self.assertIn("写入并重新读取核验成功后", agents)
        self.assertIn("明确的持久化请求失败时必须说明", agents)
        self.assertIn("checkpoint 时，它是该跨会话未完成任务契约的唯一权威", agents)
        self.assertIn("`state.md` 不重复任务目标、进度、状态或任务级约束", agents)
        self.assertIn("checkpoint 可额外保存任务目标", agents)
        self.assertIn("`state.md` 可额外保存项目级阶段", agents)
        self.assertIn("一个项目级操作性下一步", agents)
        self.assertIn("一个任务级操作性下一步", agents)
        self.assertIn("无冲突的 checkpoint 创建/暂停/恢复/完成", agents)
        self.assertIn("不保留旧值", rules)
        self.assertIn("| 目录或来源 | 权威范围 | 读取或复核条件 |", structure)
        self.assertIn("只保存需要跨会话理解的项目阶段、焦点、阻塞和下一步", state)
        self.assertIn("当前焦点", state)
        self.assertNotIn("当前任务：", state)
        self.assertNotIn("当前状态：", state)
        self.assertIn("Do not compress valid knowledge", skill)
        self.assertIn("Use a separate worktree", skill)
        self.assertIn("Ordinary discussion, analysis, suggestions, search results", skill)
        self.assertIn("a stable project fact that affects later tasks", skill)
        self.assertIn("unfinished-task state needed across sessions", skill)
        self.assertIn("Keep a requested target state distinct from the verified current state", skill)
        self.assertIn("keep the unified current form and remove the transitional difference", skill)
        self.assertIn("verified real project state governs statements of current fact", skill)
        self.assertIn("Apply stored information only when its scope covers the task", skill)
        self.assertIn("re-read the target file", skill)
        self.assertIn("do not imply it was saved", skill)
        self.assertIn("sole authority for that unfinished task contract", skill)
        self.assertIn("Routine checkpoint lifecycle changes", skill)
        self.assertIn("one project-level operational next action", skill)
        self.assertIn("one task-level operational next action", skill)
        self.assertIn("`agent-docs/state.md`", agents)
        self.assertIn("`agent-docs/checkpoint.md`", agents)
        self.assertIn("`agent-docs/state.md`", skill)
        self.assertIn("`agent-docs/decisions.md`", skill)
        self.assertIn("`project.md` 登记的当前路由", agents)
        self.assertIn("创建时必须在 `project.md`", agents)
        self.assertIn("删除时同步删除该路由", agents)
        self.assertIn("创建 `agent-docs/decisions.md`", structure)
        self.assertIn("registers it as a current authority", skill)
        self.assertIn("without a project route as a legacy candidate", skill)
        self.assertIn("remove the file and its project route together", skill)

    def test_skill_is_explicit_and_excludes_ordinary_project_work(self) -> None:
        skill_root = PLUGIN_ROOT / "skills" / "project-continuity"
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        openai = (skill_root / "agents" / "openai.yaml").read_text(encoding="utf-8")
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        plugin = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))

        self.assertIn("Do not invoke for ordinary coding", skill)
        self.assertIn("routine checkpoint creation, pause, resume, and completion", skill)
        self.assertNotIn("pausing, resuming, switching, or completing", skill.split("---", 2)[1])
        self.assertIn("allow_implicit_invocation: false", openai)
        self.assertIn("使用 $project-continuity 接管当前项目", readme)
        self.assertNotIn("使用 project-continuity 接管当前项目", readme)
        self.assertIn(
            "Repair a checkpoint whose task contract no longer matches worktree state.",
            plugin["interface"]["defaultPrompt"],
        )
        self.assertFalse((skill_root / "references").exists())

    def test_existing_complete_knowledge_is_not_rewritten_or_truncated(self) -> None:
        knowledge = "\n".join(f"CURRENT KNOWLEDGE {index}" for index in range(500))
        project = self.write(
            "agent-docs/project.md",
            (
                "# Existing Project\n\n"
                "## 当前长期规则\n\nExisting rule.\n\n"
                "## 项目结构与入口\n\nExisting authority.\n\n"
                f"{knowledge}\n"
            ),
        )

        initialize_project(self.root)
        initialize_project(self.root)

        text = project.read_text(encoding="utf-8")
        self.assertIn("CURRENT KNOWLEDGE 0", text)
        self.assertIn("CURRENT KNOWLEDGE 499", text)
        self.assertEqual(text.count("CURRENT KNOWLEDGE"), 500)

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
            cli_command("--version"),
            check=True,
            capture_output=True,
            text=True,
        )
        removed = subprocess.run(
            cli_command("sync", str(self.root)),
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(version.stdout.strip(), "project-continuity 0.10.0")
        self.assertEqual(removed.returncode, 2)
        self.assertIn("invalid choice", removed.stderr)

    def test_cli_init_emits_json(self) -> None:
        completed = subprocess.run(
            cli_command("init", str(self.root), "--json"),
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["protocol_version"], "0.10.0")
        self.assertEqual(
            payload["created"],
            ["AGENTS.md", "CLAUDE.md", "agent-docs/project.md", "agent-docs/state.md"],
        )
        self.assertEqual(payload["updated"], [])
        self.assertEqual(payload["unchanged"], [])

    def test_cli_reports_an_idempotent_refresh_as_unchanged(self) -> None:
        initialize_project(self.root)

        completed = subprocess.run(
            cli_command("init", str(self.root)),
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("协议已是当前版本，未写入文件", completed.stdout)
        self.assertNotIn("已更新:", completed.stdout)

    def test_cli_init_prompts_with_explicit_skill_syntax(self) -> None:
        completed = subprocess.run(
            cli_command("init", str(self.root)),
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("使用 $project-continuity 接管当前项目", completed.stdout)

    def test_plugin_and_skill_contain_no_runtime_automation(self) -> None:
        self.assertTrue((PLUGIN_ROOT / "skills" / "project-continuity" / "SKILL.md").is_file())
        self.assertFalse((PLUGIN_ROOT / "hooks").exists())
        self.assertFalse((PLUGIN_ROOT / "skills" / "project-continuity" / "scripts").exists())
        self.assertFalse((PLUGIN_ROOT / "skills" / "project-continuity" / "references").exists())
        self.assertFalse((TEMPLATE_ROOT / "index.block.md").exists())
        self.assertFalse((TEMPLATE_ROOT / "checkpoint.md").exists())

    def test_version_metadata_is_consistent(self) -> None:
        pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        plugin = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads(
            (REPOSITORY_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        skill_root = PLUGIN_ROOT / "skills" / "project-continuity"
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        openai = (skill_root / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertEqual(PROTOCOL_VERSION, "0.10.0")
        self.assertIn('name = "project-continuity"', pyproject)
        self.assertIn('version = "0.10.0"', pyproject)
        self.assertIn("https://github.com/yx-yuu/Project-Continuity", pyproject)
        self.assertNotIn("github.com/yx-yuu/research-harness", pyproject)
        self.assertIn("github.com/yx-yuu/Project-Continuity.git", readme)
        self.assertNotIn("github.com/yx-yuu/research-harness", readme)
        self.assertIn(
            'project-continuity = "project_continuity.project_continuity:main"',
            pyproject,
        )
        self.assertEqual(plugin["name"], "project-continuity")
        self.assertTrue(plugin["version"].startswith("0.10.0+codex."))
        self.assertEqual(
            marketplace["plugins"],
            [
                {
                    "name": "project-continuity",
                    "source": {
                        "source": "local",
                        "path": "./plugins/project-continuity",
                    },
                    "policy": {
                        "installation": "AVAILABLE",
                        "authentication": "ON_INSTALL",
                    },
                    "category": "Productivity",
                }
            ],
        )
        self.assertIn("name: project-continuity", skill)
        self.assertIn("$project-continuity", openai)
        self.assertNotIn("$research-harness", openai)

    def test_workflows_use_current_commands_and_artifact_names(self) -> None:
        ci = (REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        release = (REPOSITORY_ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("project-continuity --version", ci)
        self.assertIn("dist/project-continuity.pyz --version", ci)
        self.assertIn("python scripts/verify_wheel.py", ci)
        self.assertIn("python -m venv", ci)
        self.assertIn('python-version: "3.13"', ci)
        self.assertIn('project-continuity" init "$target" --json', ci)
        self.assertNotIn("run: research-harness", ci)
        self.assertNotIn("dist/research-harness.pyz", ci)
        self.assertIn('python scripts/verify_release_tag.py "${{ github.ref_name }}"', release)
        self.assertIn("python scripts/verify_wheel.py", release)
        self.assertIn("python -m venv", release)
        self.assertIn('project-continuity" init "$target" --json', release)
        self.assertIn("project_continuity-* project-continuity.pyz", release)
        self.assertIn("dist/project_continuity-*", release)
        self.assertIn("dist/project-continuity.pyz", release)
        self.assertNotIn("dist/research_harness-*", release)
        self.assertNotIn("dist/research-harness.pyz", release)

    @unittest.skipIf(sys.version_info < (3, 11), "verify_release_tag uses stdlib tomllib")
    def test_release_tag_verifier_matches_project_version(self) -> None:
        valid = subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "scripts" / "verify_release_tag.py"), "v0.10.0"],
            check=False,
            capture_output=True,
            text=True,
        )
        invalid = subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "scripts" / "verify_release_tag.py"), "v0.10.1"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertEqual(invalid.returncode, 2)
        self.assertIn("release tag 必须是 v0.10.0", invalid.stderr)

    def test_wheel_verifier_enforces_complete_current_package(self) -> None:
        script_root = PLUGIN_ROOT / "scripts"
        template_root = PLUGIN_ROOT / "assets" / "project-template"
        package_sources = {
            "project_continuity/__init__.py": script_root / "__init__.py",
            "project_continuity/__main__.py": script_root / "__main__.py",
            "project_continuity/continuity_core.py": script_root / "continuity_core.py",
            "project_continuity/project_continuity.py": script_root / "project_continuity.py",
            "project_continuity/templates/__init__.py": template_root / "__init__.py",
            "project_continuity/templates/AGENTS.block.md": template_root / "AGENTS.block.md",
            "project_continuity/templates/CLAUDE.block.md": template_root / "CLAUDE.block.md",
            "project_continuity/templates/project.md": template_root / "project.md",
            "project_continuity/templates/project.rules.md": template_root / "project.rules.md",
            "project_continuity/templates/project.structure.md": template_root / "project.structure.md",
            "project_continuity/templates/state.md": template_root / "state.md",
        }
        package_files = set(package_sources)

        def build_fixture(
            path: Path,
            names: set[str] | None = None,
            dist_info: str = "project_continuity-0.10.0.dist-info",
            metadata: str | None = (
                "Metadata-Version: 2.4\n"
                "Name: project-continuity\n"
                "Version: 0.10.0\n"
            ),
            wheel_metadata: str | None = (
                "Wheel-Version: 1.0\n"
                "Generator: test fixture\n"
                "Root-Is-Purelib: true\n"
                "Tag: py3-none-any\n"
            ),
            record: str | None = "",
            overrides: dict[str, bytes] | None = None,
            duplicate_member: str | None = None,
        ) -> None:
            names = package_files if names is None else names
            overrides = overrides or {}
            with ZipFile(path, "w") as archive:
                for name in names:
                    source = package_sources.get(name)
                    content = source.read_bytes() if source is not None else b"fixture\n"
                    archive.writestr(name, overrides.get(name, content))
                if metadata is not None:
                    archive.writestr(f"{dist_info}/METADATA", metadata)
                if wheel_metadata is not None:
                    archive.writestr(f"{dist_info}/WHEEL", wheel_metadata)
                if record is not None:
                    archive.writestr(f"{dist_info}/RECORD", record)
                archive.writestr(
                    f"{dist_info}/entry_points.txt",
                    "[console_scripts]\n"
                    "project-continuity = project_continuity.project_continuity:main\n",
                )
                if duplicate_member is not None:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", UserWarning)
                        archive.writestr(duplicate_member, b"duplicate\n")

        verifier = str(REPOSITORY_ROOT / "scripts" / "verify_wheel.py")
        fixtures = {
            "valid": self.root / "valid.whl",
            "missing": self.root / "missing.whl",
            "legacy": self.root / "legacy.whl",
            "corrupt": self.root / "corrupt.whl",
            "wrong-version-dist-info": self.root / "wrong-version-dist-info.whl",
            "wrong-project-dist-info": self.root / "wrong-project-dist-info.whl",
            "missing-metadata": self.root / "missing-metadata.whl",
            "missing-wheel-metadata": self.root / "missing-wheel-metadata.whl",
            "missing-record": self.root / "missing-record.whl",
            "duplicate-member": self.root / "duplicate-member.whl",
            "wrong-metadata-name": self.root / "wrong-metadata-name.whl",
            "wrong-metadata-version": self.root / "wrong-metadata-version.whl",
        }
        valid_wheel = fixtures["valid"]
        build_fixture(valid_wheel, package_files)
        build_fixture(
            fixtures["missing"],
            package_files - {"project_continuity/templates/state.md"},
        )
        build_fixture(fixtures["legacy"], package_files | {"research_harness/legacy.py"})
        build_fixture(
            fixtures["corrupt"],
            overrides={"project_continuity/continuity_core.py": b"BROKEN CONTENT\n"},
        )
        build_fixture(
            fixtures["wrong-version-dist-info"],
            dist_info="project_continuity-9.9.9.dist-info",
        )
        build_fixture(
            fixtures["wrong-project-dist-info"],
            dist_info="other_project-0.10.0.dist-info",
        )
        build_fixture(fixtures["missing-metadata"], metadata=None)
        build_fixture(fixtures["missing-wheel-metadata"], wheel_metadata=None)
        build_fixture(fixtures["missing-record"], record=None)
        build_fixture(
            fixtures["duplicate-member"],
            duplicate_member="project_continuity/__init__.py",
        )
        build_fixture(
            fixtures["wrong-metadata-name"],
            metadata="Metadata-Version: 2.4\nName: other-project\nVersion: 0.10.0\n",
        )
        build_fixture(
            fixtures["wrong-metadata-version"],
            metadata="Metadata-Version: 2.4\nName: project-continuity\nVersion: 9.9.9\n",
        )

        valid = subprocess.run(
            [sys.executable, verifier, str(valid_wheel)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(valid.returncode, 0, valid.stderr)
        expected_errors = {
            "missing": "缺失",
            "legacy": "旧包",
            "corrupt": "文件内容与源码不一致",
            "wrong-version-dist-info": "dist-info 版本不匹配",
            "wrong-project-dist-info": "dist-info 版本不匹配",
            "missing-metadata": "缺少 METADATA",
            "missing-wheel-metadata": "缺少必需元数据文件",
            "missing-record": "缺少必需元数据文件",
            "duplicate-member": "重复成员",
            "wrong-metadata-name": "METADATA 不匹配",
            "wrong-metadata-version": "METADATA 不匹配",
        }
        for name, message in expected_errors.items():
            with self.subTest(name=name):
                completed = subprocess.run(
                    [sys.executable, verifier, str(fixtures[name])],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertIn(message, completed.stderr)

    def test_standalone_zipapp_includes_minimal_templates(self) -> None:
        output = self.root / "project-continuity.pyz"
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
        self.assertEqual(payload["protocol_version"], "0.10.0")
        self.assertTrue((target / "agent-docs" / "project.md").is_file())
        self.assertFalse((target / ".research-harness.json").exists())


if __name__ == "__main__":
    unittest.main()
