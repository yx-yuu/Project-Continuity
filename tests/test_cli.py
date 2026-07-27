from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
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
        self.assertEqual(result["protocol_version"], "0.9.0")
        self.assertIn(
            "existing user content outside managed blocks in AGENTS.md and CLAUDE.md",
            result["preserves"],
        )
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
        self.assertIn("## 当前长期规则", project)
        self.assertIn("## 当前项目目标", project)
        self.assertIn("## 当前有效知识与约束", project)
        self.assertIn("| 目录或来源 | 职责 | 变化时检查 |", project)
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
        self.assertEqual(agents_text.count("project-continuity:protocol:start"), 1)
        self.assertIn("USER RULE", agents_text)
        self.assertIn("USER PROJECT FACT", project.read_text(encoding="utf-8"))

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

    def test_protocol_defines_scoped_lossless_mutations_and_paused_tasks(self) -> None:
        agents = (TEMPLATE_ROOT / "AGENTS.block.md").read_text(encoding="utf-8")
        rules = (TEMPLATE_ROOT / "project.rules.md").read_text(encoding="utf-8")
        structure = (TEMPLATE_ROOT / "project.structure.md").read_text(encoding="utf-8")
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
        self.assertIn("不保留旧值", rules)
        self.assertIn("Do not compress valid knowledge", skill)
        self.assertIn("Use a separate worktree", skill)
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

        self.assertIn("Do not invoke for ordinary coding", skill)
        self.assertIn("allow_implicit_invocation: false", openai)
        self.assertIn("使用 $project-continuity 接管当前项目", readme)
        self.assertNotIn("使用 project-continuity 接管当前项目", readme)
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

        self.assertEqual(version.stdout.strip(), "project-continuity 0.9.0")
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
        self.assertEqual(payload["protocol_version"], "0.9.0")
        self.assertEqual(payload["created"], ["agent-docs/project.md", "agent-docs/state.md"])

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
        plugin = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads(
            (REPOSITORY_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        skill_root = PLUGIN_ROOT / "skills" / "project-continuity"
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        openai = (skill_root / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertEqual(PROTOCOL_VERSION, "0.9.0")
        self.assertIn('name = "project-continuity"', pyproject)
        self.assertIn('version = "0.9.0"', pyproject)
        self.assertIn(
            'project-continuity = "project_continuity.project_continuity:main"',
            pyproject,
        )
        self.assertEqual(plugin["name"], "project-continuity")
        self.assertTrue(plugin["version"].startswith("0.9.0+codex."))
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
            [sys.executable, str(REPOSITORY_ROOT / "scripts" / "verify_release_tag.py"), "v0.9.0"],
            check=False,
            capture_output=True,
            text=True,
        )
        invalid = subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "scripts" / "verify_release_tag.py"), "v0.9.1"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertEqual(invalid.returncode, 2)
        self.assertIn("release tag 必须是 v0.9.0", invalid.stderr)

    def test_wheel_verifier_enforces_complete_current_package(self) -> None:
        package_files = {
            "project_continuity/__init__.py",
            "project_continuity/__main__.py",
            "project_continuity/continuity_core.py",
            "project_continuity/project_continuity.py",
            "project_continuity/templates/__init__.py",
            "project_continuity/templates/AGENTS.block.md",
            "project_continuity/templates/CLAUDE.block.md",
            "project_continuity/templates/project.md",
            "project_continuity/templates/project.rules.md",
            "project_continuity/templates/project.structure.md",
            "project_continuity/templates/state.md",
        }

        def build_fixture(
            path: Path,
            names: set[str],
            dist_info: str = "project_continuity-0.9.0.dist-info",
        ) -> None:
            with ZipFile(path, "w") as archive:
                for name in names:
                    archive.writestr(name, "fixture\n")
                archive.writestr(
                    f"{dist_info}/entry_points.txt",
                    "[console_scripts]\n"
                    "project-continuity = project_continuity.project_continuity:main\n",
                )

        verifier = str(REPOSITORY_ROOT / "scripts" / "verify_wheel.py")
        valid_wheel = self.root / "valid.whl"
        missing_wheel = self.root / "missing.whl"
        legacy_wheel = self.root / "legacy.whl"
        wrong_dist_info_wheel = self.root / "wrong-dist-info.whl"
        build_fixture(valid_wheel, package_files)
        build_fixture(missing_wheel, package_files - {"project_continuity/templates/state.md"})
        build_fixture(legacy_wheel, package_files | {"research_harness/legacy.py"})
        build_fixture(wrong_dist_info_wheel, package_files, "other_project-0.9.0.dist-info")

        valid = subprocess.run(
            [sys.executable, verifier, str(valid_wheel)],
            check=False,
            capture_output=True,
            text=True,
        )
        missing = subprocess.run(
            [sys.executable, verifier, str(missing_wheel)],
            check=False,
            capture_output=True,
            text=True,
        )
        legacy = subprocess.run(
            [sys.executable, verifier, str(legacy_wheel)],
            check=False,
            capture_output=True,
            text=True,
        )
        wrong_dist_info = subprocess.run(
            [sys.executable, verifier, str(wrong_dist_info_wheel)],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertEqual(missing.returncode, 2)
        self.assertIn("缺失", missing.stderr)
        self.assertEqual(legacy.returncode, 2)
        self.assertIn("旧包", legacy.stderr)
        self.assertEqual(wrong_dist_info.returncode, 2)
        self.assertIn("dist-info 不属于", wrong_dist_info.stderr)

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
        self.assertEqual(payload["protocol_version"], "0.9.0")
        self.assertTrue((target / "agent-docs" / "project.md").is_file())
        self.assertFalse((target / ".research-harness.json").exists())


if __name__ == "__main__":
    unittest.main()
