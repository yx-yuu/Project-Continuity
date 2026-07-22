from __future__ import annotations

import re
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from string import Template


PROTOCOL_VERSION = "0.6.0"
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = PLUGIN_ROOT / "assets" / "project-template"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _template(name: str, **values: str) -> str:
    path = TEMPLATE_ROOT / name
    if path.is_file():
        text = path.read_text(encoding="utf-8")
    else:
        try:
            text = resources.files("research_harness.templates").joinpath(name).read_text(encoding="utf-8")
        except (ModuleNotFoundError, FileNotFoundError) as exc:
            raise FileNotFoundError(f"缺少模板: {name}") from exc
    return Template(text).safe_substitute(values).rstrip() + "\n"


def _marker(name: str, boundary: str) -> str:
    return f"<!-- research-harness:{name}:{boundary} -->"


def _has_managed_section(path: Path, name: str) -> bool:
    return path.is_file() and _marker(name, "start") in path.read_text(encoding="utf-8")


def upsert_managed_section(path: Path, name: str, body: str, heading: str | None = None) -> None:
    start = _marker(name, "start")
    end = _marker(name, "end")
    section = f"{start}\n{body.rstrip()}\n{end}"
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
        if pattern.search(existing):
            updated = pattern.sub(lambda _: section, existing, count=1)
        else:
            spacer = "" if not existing.strip() else "\n\n"
            updated = existing.rstrip() + spacer + section + "\n"
    else:
        prefix = f"# {heading}\n\n" if heading else ""
        updated = prefix + section + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated, encoding="utf-8")


def _has_active_claude_import(text: str) -> bool:
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            fence = None if fence == marker else marker if fence is None else fence
            continue
        if fence is None and stripped == "@AGENTS.md":
            return True
    return False


def ensure_claude_adapter(path: Path) -> None:
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        if _marker("claude-adapter", "start") not in text and _has_active_claude_import(text):
            return
    upsert_managed_section(path, "claude-adapter", _template("CLAUDE.block.md"), heading="Project Agent Instructions")


def _write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _append_structure_section_if_missing(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "## 项目结构与入口" not in text:
        path.write_text(text.rstrip() + "\n\n" + _template("project.structure.md"), encoding="utf-8")


def _legacy_review_candidates(root: Path) -> list[str]:
    candidates = (
        ".research-harness.json",
        ".research-harness",
        "agent-docs/index.md",
        "agent-docs/bootstrap.md",
        "agent-docs/claims.md",
        "agent-docs/tasks",
    )
    return [relative for relative in candidates if (root / relative).exists()]


def initialize_project(root: Path, project_name: str | None = None, dry_run: bool = False) -> dict:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"项目目录不存在或不是目录: {root}")

    docs = root / "agent-docs"
    existing_agent_docs = sorted(path.name for path in docs.glob("*.md")) if docs.is_dir() else []
    mode = "refresh" if _has_managed_section(root / "AGENTS.md", "protocol") else "initialize"
    planned = [
        "AGENTS.md managed protocol",
        "CLAUDE.md AGENTS import adapter",
        "agent-docs/project.md",
        "agent-docs/state.md",
    ]
    preserves = [
        "existing user content in AGENTS.md and CLAUDE.md",
        "existing project.md and state.md research content",
        "all project files, datasets, results, and Git state",
    ]
    legacy = _legacy_review_candidates(root)

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "mode": mode,
            "root": str(root),
            "protocol_version": PROTOCOL_VERSION,
            "planned": planned,
            "preserves": preserves,
            "existing_agent_docs": existing_agent_docs,
            "legacy_review_candidates": legacy,
        }

    docs.mkdir(parents=True, exist_ok=True)
    upsert_managed_section(root / "AGENTS.md", "protocol", _template("AGENTS.block.md"), heading="Project Agent Instructions")
    ensure_claude_adapter(root / "CLAUDE.md")

    created = []
    templates = {
        "project.md": _template(
            "project.md",
            PROJECT_NAME=project_name or root.name,
            DATE=utc_now(),
            STRUCTURE_SECTION=_template("project.structure.md").rstrip(),
        ),
        "state.md": _template("state.md", DATE=utc_now()),
    }
    for filename, content in templates.items():
        if _write_if_missing(docs / filename, content):
            created.append(f"agent-docs/{filename}")
    _append_structure_section_if_missing(docs / "project.md")

    return {
        "ok": True,
        "dry_run": False,
        "mode": mode,
        "root": str(root),
        "protocol_version": PROTOCOL_VERSION,
        "created": created,
        "refreshed": ["AGENTS.md", "CLAUDE.md"],
        "preserves": preserves,
        "existing_agent_docs": existing_agent_docs,
        "legacy_review_candidates": legacy,
    }
