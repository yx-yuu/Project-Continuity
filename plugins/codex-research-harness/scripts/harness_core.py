from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from string import Template
from typing import Iterable


PROTOCOL_VERSION = "0.4.0"
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = PLUGIN_ROOT / "assets" / "project-template"
MANIFEST_NAME = ".research-harness.json"
STATE_DIR_NAME = ".research-harness"
SNAPSHOT_NAME = "snapshot.json"

SCAN_MAX_DEPTH = 4
SCAN_MAX_FILES = 20_000
CHANGE_DISPLAY_LIMIT = 200

CONTEXT_BUDGETS = {
    "agents_managed_lines": 24,
    "claude_adapter_lines": 8,
    "index_lines": 120,
    "project_lines": 180,
    "state_lines": 120,
    "decisions_lines": 200,
    "checkpoint_lines": 120,
    "restore_context_bytes": 32_000,
}

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    STATE_DIR_NAME,
    "agent-docs",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "dist",
    "build",
    "vendor",
    "third_party",
    "external_repos",
    "repos",
    "temp",
    "tmp",
}

CODE_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".kt", ".go", ".rs",
    ".c", ".cc", ".cpp", ".h", ".hpp", ".r", ".R", ".jl", ".m", ".scala", ".sh",
}
PAPER_SUFFIXES = {".tex", ".bib", ".docx", ".md", ".sty", ".cls"}
PAPER_DIR_NAMES = {"paper", "papers", "manuscript", "manuscripts", "latex", "author-kit", "authorkit"}
CONTEXT_DIR_NAMES = {"doc", "docs", "documentation", "notes", "spec", "specs"}
SOURCE_DIR_NAMES = {"src", "source", "lib", "app", "pkg", "package", "packages"}
TEST_DIR_NAMES = {"test", "tests", "testing"}
EXPERIMENT_DIR_NAMES = {"experiment", "experiments", "evaluation", "evaluations", "benchmark", "benchmarks"}
DATA_DIR_NAMES = {"data", "dataset", "datasets", "corpus", "corpora"}
ARTIFACT_DIR_NAMES = {
    "artifact", "artifacts", "result", "results", "output", "outputs", "analysis-output", "runs", "figures",
}
BUILD_NAMES = {
    "pyproject.toml", "requirements.txt", "environment.yml", "environment.yaml", "package.json",
    "cargo.toml", "go.mod", "makefile", "justfile", "dockerfile",
}
GENERATED_SUFFIXES = {
    ".aux", ".bbl", ".blg", ".fdb_latexmk", ".fls", ".log", ".out", ".pyc", ".pyo",
}
CORE_CONTEXT_FILES = {"index.md", "project.md", "state.md", "decisions.md", "checkpoint.md"}


@dataclass(frozen=True)
class Inventory:
    project_name: str
    git_repository: bool
    scanned_file_count: int
    scan_truncated: bool
    top_level_directories: list[str]
    paper_files: list[str]
    source_directories: list[str]
    test_directories: list[str]
    experiment_directories: list[str]
    data_directories: list[str]
    artifact_directories: list[str]
    context_documents: list[str]
    build_files: list[str]


@dataclass(frozen=True)
class Check:
    level: str
    code: str
    message: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def find_project_root(start: Path) -> Path | None:
    current = start.expanduser().resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / MANIFEST_NAME).is_file():
            return candidate
    return None


def _is_git_repository(root: Path) -> bool:
    git = shutil.which("git")
    if git:
        completed = subprocess.run(
            [git, "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode == 0:
            return completed.stdout.strip().lower() == "true"
    git_marker = root / ".git"
    return (git_marker.is_dir() and (git_marker / "HEAD").is_file()) or git_marker.is_file()


def _walk_files(root: Path, max_depth: int = SCAN_MAX_DEPTH, max_files: int = SCAN_MAX_FILES) -> tuple[list[Path], bool]:
    files: list[Path] = []
    for current, dirnames, filenames in os.walk(root):
        current_path = Path(current)
        relative = current_path.relative_to(root)
        depth = 0 if relative == Path(".") else len(relative.parts)
        dirnames[:] = [name for name in dirnames if name not in IGNORED_DIRS and not name.startswith(".trash")]
        if depth >= max_depth:
            dirnames[:] = []
        for filename in filenames:
            files.append(current_path / filename)
            if len(files) >= max_files:
                return files, True
    return files, False


def _relative_strings(root: Path, paths: Iterable[Path], limit: int = 80) -> list[str]:
    return sorted({path.relative_to(root).as_posix() for path in paths})[:limit]


def _matching_directories(root: Path, names: set[str], directories: Iterable[Path]) -> list[str]:
    matched = []
    for path in directories:
        lowered = path.name.lower()
        if lowered in names or any(lowered.startswith(f"{name}-") or lowered.startswith(f"{name}_") for name in names):
            matched.append(path.relative_to(root).as_posix())
    return sorted(set(matched))


def _is_context_directory(name: str) -> bool:
    lowered = name.lower()
    return (
        lowered in CONTEXT_DIR_NAMES
        or lowered.endswith("-doc")
        or lowered.endswith("-docs")
        or lowered.endswith("_doc")
        or lowered.endswith("_docs")
    )


def classify_path(root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    parts = [part.lower() for part in relative.parts[:-1]]
    suffix = path.suffix.lower()
    lowered_name = path.name.lower()
    if suffix in GENERATED_SUFFIXES or lowered_name.endswith(".synctex.gz") or lowered_name == ".ds_store":
        return "generated"
    if suffix == ".md" and (
        path.parent == root
        or any(_is_context_directory(part) for part in parts)
        or any(token in lowered_name for token in ("readme", "constraint", "onboarding", "design", "spec", "plan", "report"))
    ):
        return "context"
    if suffix in {".tex", ".bib", ".docx"} or (suffix in PAPER_SUFFIXES and any(part in PAPER_DIR_NAMES for part in parts)):
        return "paper"
    if any(part in ARTIFACT_DIR_NAMES for part in parts):
        return "artifact"
    if any(part in DATA_DIR_NAMES for part in parts):
        return "data"
    if suffix in CODE_SUFFIXES:
        return "code"
    if lowered_name in BUILD_NAMES:
        return "environment"
    return "other"


def scan_project(root: Path, project_name: str | None = None) -> Inventory:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"项目目录不存在或不是目录: {root}")

    files, truncated = _walk_files(root)
    top_dirs = sorted(
        [path for path in root.iterdir() if path.is_dir() and path.name not in IGNORED_DIRS and not path.name.startswith(".")],
        key=lambda path: path.name.lower(),
    )
    directories = set(top_dirs)
    for path in files:
        parent = path.parent
        while parent != root:
            directories.add(parent)
            parent = parent.parent

    categories: dict[str, list[Path]] = {}
    for path in files:
        categories.setdefault(classify_path(root, path), []).append(path)
    source_dirs = _matching_directories(root, SOURCE_DIR_NAMES, directories)
    if not source_dirs and categories.get("code"):
        source_dirs = ["."]

    return Inventory(
        project_name=project_name or root.name,
        git_repository=_is_git_repository(root),
        scanned_file_count=len(files),
        scan_truncated=truncated,
        top_level_directories=[path.name for path in top_dirs],
        paper_files=_relative_strings(root, categories.get("paper", []), limit=60),
        source_directories=source_dirs,
        test_directories=_matching_directories(root, TEST_DIR_NAMES, directories),
        experiment_directories=_matching_directories(root, EXPERIMENT_DIR_NAMES, directories),
        data_directories=_matching_directories(root, DATA_DIR_NAMES, directories),
        artifact_directories=_matching_directories(root, ARTIFACT_DIR_NAMES, directories),
        context_documents=_relative_strings(root, categories.get("context", []), limit=80),
        build_files=_relative_strings(root, categories.get("environment", []), limit=30),
    )


def _snapshot_path(root: Path) -> Path:
    return root / STATE_DIR_NAME / SNAPSHOT_NAME


def build_snapshot(root: Path) -> dict:
    root = root.expanduser().resolve()
    files, truncated = _walk_files(root)
    entries: dict[str, dict[str, int | str]] = {}
    for path in files:
        if path.relative_to(root).as_posix() == MANIFEST_NAME:
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        entries[path.relative_to(root).as_posix()] = {
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "ctime_ns": stat.st_ctime_ns,
            "category": classify_path(root, path),
        }
    return {
        "snapshot_version": 2,
        "generated_at": utc_now(),
        "scan_max_depth": SCAN_MAX_DEPTH,
        "scan_max_files": SCAN_MAX_FILES,
        "truncated": truncated,
        "entries": entries,
    }


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法解析 {path}: {exc}") from exc
    return value if isinstance(value, dict) else {}


def sync_project(root: Path, accept: bool = False) -> dict:
    root = root.expanduser().resolve()
    if not (root / MANIFEST_NAME).is_file():
        raise ValueError("项目尚未初始化 research harness。")
    previous = _load_json(_snapshot_path(root))
    current = build_snapshot(root)
    old_entries = previous.get("entries", {}) if isinstance(previous.get("entries", {}), dict) else {}
    new_entries = current["entries"]

    if accept and current.get("truncated"):
        raise ValueError("扫描已截断，不能接受不完整文件集为新基线。")

    old_paths = set(old_entries)
    new_paths = set(new_entries)
    added_paths = sorted(new_paths - old_paths)
    removed_paths = sorted(old_paths - new_paths)
    modified_paths = sorted(
        path for path in old_paths & new_paths
        if old_entries[path].get("size") != new_entries[path].get("size")
        or old_entries[path].get("mtime_ns") != new_entries[path].get("mtime_ns")
        or ("ctime_ns" in old_entries[path] and old_entries[path].get("ctime_ns") != new_entries[path].get("ctime_ns"))
    )

    def rows(paths: list[str], entries: dict) -> list[dict]:
        return [{"path": path, **entries.get(path, {})} for path in paths[:CHANGE_DISPLAY_LIMIT]]

    if accept:
        _write_json(_snapshot_path(root), current)
        manifest_path = root / MANIFEST_NAME
        manifest = _load_json(manifest_path)
        manifest["last_sync_at"] = utc_now()
        manifest["updated_at"] = utc_now()
        _write_json(manifest_path, manifest)

    total = len(added_paths) + len(modified_paths) + len(removed_paths)
    return {
        "ok": True,
        "root": str(root),
        "baseline_exists": bool(previous),
        "accepted": accept,
        "counts": {"added": len(added_paths), "modified": len(modified_paths), "removed": len(removed_paths), "total": total},
        "added": rows(added_paths, new_entries),
        "modified": rows(modified_paths, new_entries),
        "removed": rows(removed_paths, old_entries),
        "display_truncated": total > CHANGE_DISPLAY_LIMIT,
        "scan_truncated": bool(current.get("truncated")),
    }


def _template(name: str, **values: str) -> str:
    path = TEMPLATE_ROOT / name
    if not path.is_file():
        raise FileNotFoundError(f"缺少模板: {path}")
    return Template(path.read_text(encoding="utf-8")).safe_substitute(values).rstrip() + "\n"


def _marker(name: str, boundary: str) -> str:
    return f"<!-- research-harness:{name}:{boundary} -->"


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


def _append_sources_section_if_missing(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "## 当前项目来源" not in text:
        path.write_text(text.rstrip() + "\n\n" + _template("index.sources.md"), encoding="utf-8")


def initialize_project(root: Path, project_name: str | None = None, dry_run: bool = False) -> dict:
    root = root.expanduser().resolve()
    inventory = scan_project(root, project_name)
    planned = [
        "AGENTS.md managed section",
        "CLAUDE.md managed adapter",
        MANIFEST_NAME,
        f"{STATE_DIR_NAME}/{SNAPSHOT_NAME}",
        "agent-docs/index.md",
        "agent-docs/project.md",
        "agent-docs/state.md",
        "agent-docs/decisions.md",
    ]
    if dry_run:
        return {"ok": True, "dry_run": True, "root": str(root), "planned": planned, "inventory": asdict(inventory)}

    docs = root / "agent-docs"
    docs.mkdir(parents=True, exist_ok=True)
    upsert_managed_section(root / "AGENTS.md", "protocol", _template("AGENTS.block.md"), heading="Project Agent Instructions")
    ensure_claude_adapter(root / "CLAUDE.md")
    index_path = docs / "index.md"
    upsert_managed_section(index_path, "index", _template("index.block.md"), heading="Agent Docs 索引")
    _append_sources_section_if_missing(index_path)

    created = []
    static_templates = {
        "project.md": _template("project.md", PROJECT_NAME=inventory.project_name, DATE=utc_now()),
        "state.md": _template("state.md", DATE=utc_now()),
        "decisions.md": _template("decisions.md"),
    }
    for filename, content in static_templates.items():
        if _write_if_missing(docs / filename, content):
            created.append(f"agent-docs/{filename}")

    manifest_path = root / MANIFEST_NAME
    existing = _load_json(manifest_path)
    previous_version = existing.get("protocol_version")
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "context_model": "project-control-plane",
        "project_name": inventory.project_name,
        "project_root": ".",
        "initialized_at": existing.get("initialized_at", utc_now()),
        "updated_at": utc_now(),
        "last_sync_at": utc_now(),
        "snapshot_path": f"{STATE_DIR_NAME}/{SNAPSHOT_NAME}",
        "context_budgets": CONTEXT_BUDGETS,
        "managed_files": planned,
    }
    if previous_version and previous_version != PROTOCOL_VERSION:
        manifest["migrated_from"] = previous_version
    _write_json(manifest_path, manifest)
    _write_json(_snapshot_path(root), build_snapshot(root))

    legacy = []
    for relative in ("agent-docs/bootstrap.md", "agent-docs/claims.md", "agent-docs/tasks"):
        if (root / relative).exists():
            legacy.append(relative)
    return {
        "ok": True,
        "dry_run": False,
        "root": str(root),
        "created": created,
        "refreshed": ["AGENTS.md", "CLAUDE.md", "agent-docs/index.md", MANIFEST_NAME, f"{STATE_DIR_NAME}/{SNAPSHOT_NAME}"],
        "legacy_cleanup_candidates": legacy,
        "inventory": asdict(inventory),
    }


def _bullets(values: list[str], empty: str = "无") -> str:
    return "\n".join(f"- {value}" for value in values) if values else f"- {empty}"


def save_checkpoint(
    root: Path,
    goal: str,
    current: str,
    next_step: str,
    facts: list[str] | None = None,
    decisions: list[str] | None = None,
    risks: list[str] | None = None,
    refs: list[str] | None = None,
    scope: str = "未指定",
    done: str = "未指定",
    validation: str = "未指定",
    impacts: list[str] | None = None,
) -> Path:
    root = root.expanduser().resolve()
    if not (root / MANIFEST_NAME).is_file():
        raise ValueError("项目尚未初始化 research harness。")
    contract = {"scope": scope, "done": done, "validation": validation}
    missing = [name for name, value in contract.items() if not value.strip() or value.strip() == "未指定"]
    if missing:
        raise ValueError("任务契约缺少必填字段: " + ", ".join(missing))
    path = root / "agent-docs" / "checkpoint.md"
    path.write_text(
        _template(
            "checkpoint.md",
            DATE=utc_now(),
            GOAL=goal,
            SCOPE=scope,
            DONE=done,
            VALIDATION=validation,
            IMPACTS=_bullets(impacts or []),
            CURRENT=current,
            NEXT_STEP=next_step,
            FACTS=_bullets(facts or []),
            DECISIONS=_bullets(decisions or []),
            RISKS=_bullets(risks or []),
            REFS=_bullets([f"`{value}`" for value in (refs or [])]),
        ),
        encoding="utf-8",
    )
    return path


def read_checkpoint(root: Path) -> str | None:
    path = root.expanduser().resolve() / "agent-docs" / "checkpoint.md"
    return path.read_text(encoding="utf-8") if path.is_file() else None


def clear_checkpoint(root: Path, force: bool = False) -> Path:
    path = root.expanduser().resolve() / "agent-docs" / "checkpoint.md"
    if not path.is_file():
        raise ValueError("当前没有 checkpoint。")
    if not force:
        changes = sync_project(root)
        if changes["scan_truncated"]:
            raise ValueError("项目扫描已截断，不能确认任务影响已经完整处理。")
        if changes["counts"]["total"]:
            counts = changes["counts"]
            raise ValueError(
                "仍有未确认文件变化，完成影响审查并执行 sync --accept 后再清理 checkpoint："
                f"+{counts['added']} ~{counts['modified']} -{counts['removed']}。"
            )
    trash = shutil.which("trash")
    if not trash:
        raise ValueError("未找到 trash 命令；为保证可恢复性，未删除 checkpoint。")
    subprocess.run([trash, str(path)], check=True)
    return path


LINK_PATTERN = re.compile(r"\[[^\]]*\]\((?:<)?([^)>]+)(?:>)?\)")


def _local_link_checks(root: Path, document: Path) -> list[Check]:
    checks = []
    try:
        text = document.read_text(encoding="utf-8")
    except OSError as exc:
        return [Check("error", "document-unreadable", f"无法读取 {document}: {exc}")]
    for target in LINK_PATTERN.findall(text):
        target = target.strip()
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        clean = target.split("#", 1)[0]
        if not (document.parent / clean).resolve().exists():
            checks.append(Check("error", "broken-link", f"{document.relative_to(root)} 指向不存在的路径: {target}"))
    return checks


def _managed_line_count(path: Path, name: str) -> int:
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8")
    match = re.search(re.escape(_marker(name, "start")) + r"(.*?)" + re.escape(_marker(name, "end")), text, re.DOTALL)
    return len(match.group(1).strip().splitlines()) if match else 0


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines()) if path.is_file() else 0


def _restore_context_bytes(root: Path) -> int:
    paths = [
        root / "AGENTS.md",
        root / "agent-docs" / "index.md",
        root / "agent-docs" / "project.md",
        root / "agent-docs" / "state.md",
        root / "agent-docs" / "decisions.md",
        root / "agent-docs" / "checkpoint.md",
    ]
    return sum(path.stat().st_size for path in paths if path.is_file())


def doctor_project(root: Path) -> list[Check]:
    root = root.expanduser().resolve()
    checks: list[Check] = []
    required = [
        root / "AGENTS.md",
        root / "CLAUDE.md",
        root / MANIFEST_NAME,
        _snapshot_path(root),
        root / "agent-docs" / "index.md",
        root / "agent-docs" / "project.md",
        root / "agent-docs" / "state.md",
        root / "agent-docs" / "decisions.md",
    ]
    for path in required:
        if path.exists():
            checks.append(Check("ok", "required-file", f"存在: {path.relative_to(root)}"))
        else:
            checks.append(Check("error", "missing-required-file", f"缺少: {path.relative_to(root)}"))

    agents = root / "AGENTS.md"
    if agents.exists() and _marker("protocol", "start") not in agents.read_text(encoding="utf-8"):
        checks.append(Check("error", "agents-block-missing", "AGENTS.md 缺少 research harness 受管理区块。"))

    claude = root / "CLAUDE.md"
    if claude.exists():
        claude_text = claude.read_text(encoding="utf-8")
        if not _has_active_claude_import(claude_text):
            checks.append(Check("error", "claude-adapter-missing", "CLAUDE.md 缺少 AGENTS.md 共享入口。"))

    manifest_path = root / MANIFEST_NAME
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = _load_json(manifest_path)
            version = manifest.get("protocol_version")
            level = "ok" if version == PROTOCOL_VERSION else "warning"
            checks.append(Check(level, "protocol-version", f"项目协议版本: {version}; 当前版本: {PROTOCOL_VERSION}"))
        except ValueError as exc:
            checks.append(Check("error", "manifest-invalid", str(exc)))

    budgets = manifest.get("context_budgets", CONTEXT_BUDGETS) if isinstance(manifest, dict) else CONTEXT_BUDGETS
    budget_paths = {
        "index_lines": root / "agent-docs" / "index.md",
        "project_lines": root / "agent-docs" / "project.md",
        "state_lines": root / "agent-docs" / "state.md",
        "decisions_lines": root / "agent-docs" / "decisions.md",
        "checkpoint_lines": root / "agent-docs" / "checkpoint.md",
    }
    agents_lines = _managed_line_count(agents, "protocol")
    if agents_lines > int(budgets.get("agents_managed_lines", CONTEXT_BUDGETS["agents_managed_lines"])):
        checks.append(Check("warning", "context-budget", f"AGENTS.md 受管理区块超过预算: {agents_lines} 行。"))
    claude_lines = _managed_line_count(claude, "claude-adapter")
    if claude_lines > int(budgets.get("claude_adapter_lines", CONTEXT_BUDGETS["claude_adapter_lines"])):
        checks.append(Check("warning", "context-budget", f"CLAUDE.md 受管理区块超过预算: {claude_lines} 行。"))
    for key, path in budget_paths.items():
        count = _line_count(path)
        limit = int(budgets.get(key, CONTEXT_BUDGETS[key]))
        if count > limit:
            checks.append(Check("warning", "context-budget", f"{path.relative_to(root)} 超过预算: {count}/{limit} 行。"))
    restore_bytes = _restore_context_bytes(root)
    restore_limit = int(budgets.get("restore_context_bytes", CONTEXT_BUDGETS["restore_context_bytes"]))
    if restore_bytes > restore_limit:
        checks.append(Check("warning", "restore-budget", f"默认恢复包超过预算: {restore_bytes}/{restore_limit} bytes。"))

    project_path = root / "agent-docs" / "project.md"
    state_path = root / "agent-docs" / "state.md"
    project_text = project_path.read_text(encoding="utf-8") if project_path.is_file() else ""
    state_text = state_path.read_text(encoding="utf-8") if state_path.is_file() else ""
    if "待确认" in project_text or re.search(r"(?im)^- 当前阶段：`?bootstrap`?", state_text):
        checks.append(Check("warning", "project-unconfirmed", "项目定义或当前阶段仍处于 bootstrap/待确认状态。"))

    checkpoint_path = root / "agent-docs" / "checkpoint.md"
    if checkpoint_path.is_file():
        checkpoint_text = checkpoint_path.read_text(encoding="utf-8")
        required_sections = ("## 任务范围", "## 完成条件", "## 验证边界", "## 预期影响")
        missing_sections = [section.removeprefix("## ") for section in required_sections if section not in checkpoint_text]
        if missing_sections:
            checks.append(Check("warning", "task-contract-incomplete", "checkpoint 缺少任务契约字段: " + ", ".join(missing_sections)))

    docs = root / "agent-docs"
    if docs.exists():
        for document in docs.rglob("*.md"):
            checks.extend(_local_link_checks(root, document))
        index_text = (docs / "index.md").read_text(encoding="utf-8") if (docs / "index.md").is_file() else ""
        for document in docs.glob("*.md"):
            if document.name in CORE_CONTEXT_FILES or document.name == "bootstrap.md":
                continue
            if f"({document.name})" not in index_text and f"(<{document.name}>)" not in index_text:
                checks.append(Check("warning", "unrouted-context", f"未在 index.md 登记: agent-docs/{document.name}"))

    legacy = []
    if (docs / "bootstrap.md").exists():
        legacy.append("agent-docs/bootstrap.md")
    task_files = list((docs / "tasks").rglob("*.md")) if (docs / "tasks").exists() else []
    if task_files:
        legacy.append(f"agent-docs/tasks/ ({len(task_files)} 个旧任务文档)")
    if legacy:
        checks.append(Check("warning", "legacy-context", "请审查并清理 v0.1 遗留内容: " + ", ".join(legacy)))

    for path in (docs / "project.md", docs / "state.md"):
        if path.is_file() and re.search(r"(?im)^\s*[-*]?\s*(?:状态|status)\s*[:：]\s*`?(candidate|stale|superseded)", path.read_text(encoding="utf-8")):
            checks.append(Check("warning", "noncurrent-context", f"{path.relative_to(root)} 含未清理的非当前状态。"))

    if _snapshot_path(root).is_file() and manifest_path.is_file():
        try:
            changes = sync_project(root)
            if changes["scan_truncated"]:
                checks.append(Check("warning", "scan-truncated", "项目扫描达到深度或文件数量上限，当前增量基线不完整。"))
            if changes["counts"]["total"]:
                counts = changes["counts"]
                checks.append(Check("warning", "pending-sync", f"项目文件存在未确认变化: +{counts['added']} ~{counts['modified']} -{counts['removed']}。"))
        except ValueError as exc:
            checks.append(Check("error", "snapshot-invalid", str(exc)))

    if not any(check.level == "error" for check in checks):
        warning_count = sum(check.level == "warning" for check in checks)
        if warning_count:
            checks.append(Check("warning", "control-readiness", f"项目控制面可恢复，但仍有 {warning_count} 项需要审查。"))
        else:
            checks.append(Check("ok", "control-readiness", "项目定义、约束入口、当前状态和恢复预算均已就绪。"))
    return checks


def resume_project(root: Path) -> dict:
    root = root.expanduser().resolve()
    if not (root / MANIFEST_NAME).is_file():
        raise ValueError("项目尚未初始化 research harness。")
    changes = sync_project(root)
    checkpoint = read_checkpoint(root)
    return {
        "ok": True,
        "root": str(root),
        "agent_entrypoints": {"codex": "AGENTS.md", "claude_code": "CLAUDE.md"},
        "read_first": ["AGENTS.md", "agent-docs/index.md", "agent-docs/project.md", "agent-docs/state.md"],
        "read_if_present": ["agent-docs/checkpoint.md"],
        "checkpoint": checkpoint,
        "pending_changes": changes["counts"],
        "instructions": [
            "从当前项目定义、约束、状态和已登记证据恢复，不从历史材料推断当前事实。",
            "任务执行方式可由按需 skill 提供，但不得绕过项目约束、完成条件和证据门禁。",
            "文件变化先作为影响候选；确认并传播到受影响对象后再接受新基线。",
        ],
    }


def checks_ok(checks: Iterable[Check]) -> bool:
    return not any(check.level == "error" for check in checks)
