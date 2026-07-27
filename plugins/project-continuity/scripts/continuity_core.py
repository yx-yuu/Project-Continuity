from __future__ import annotations

import os
import secrets
import stat
from collections.abc import Iterator
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from string import Template


PROTOCOL_VERSION = "0.10.0"
CURRENT_MARKER_NAMESPACE = "project-continuity"
LEGACY_MARKER_NAMESPACES = ("research-harness",)
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = PLUGIN_ROOT / "assets" / "project-template"
MAX_CONCURRENT_RETRIES = 3


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return stream.read()


class ConcurrentModificationError(OSError):
    """Raised when a control file changes while an initialization plan is being committed."""

    def __init__(self, message: str, committed: tuple[Path, ...] = ()) -> None:
        super().__init__(message)
        self.committed = committed


def _current_control_text(path: Path) -> str | None:
    if path.parent.is_symlink():
        raise ConcurrentModificationError(f"控制文档目录在写入期间变成符号链接: {path.parent}")
    if path.is_symlink():
        raise ConcurrentModificationError(f"控制文档在写入期间变成符号链接: {path}")
    if not path.exists():
        return None
    if not path.is_file():
        raise ConcurrentModificationError(f"控制文档在写入期间不再是文件: {path}")
    return _read_text(path)


def _verify_expected_contents(expected: dict[Path, str | None]) -> None:
    changed = [path for path, original in expected.items() if _current_control_text(path) != original]
    if changed:
        paths = ", ".join(str(path) for path in changed)
        raise ConcurrentModificationError(f"控制文档在写入期间发生变化，请重新读取后重试: {paths}")


def _preferred_newline(text: str) -> str:
    for index, character in enumerate(text):
        if character == "\r":
            return "\r\n" if text[index : index + 2] == "\r\n" else "\r"
        if character == "\n":
            return "\n"
    return "\n"


def _with_newlines(text: str, newline: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", newline)


def _append_block(text: str, block: str, newline: str) -> str:
    block = _with_newlines(block, newline)
    if not text:
        return block + newline
    if text.endswith(("\r\n\r\n", "\n\n", "\r\r")):
        separator = ""
    elif text.endswith(("\r", "\n")):
        separator = newline
    else:
        separator = newline * 2
    return text + separator + block + newline


def _template(name: str, **values: str) -> str:
    path = TEMPLATE_ROOT / name
    if path.is_file():
        text = _read_text(path)
    else:
        try:
            text = resources.files("project_continuity.templates").joinpath(name).read_text(encoding="utf-8")
        except (ModuleNotFoundError, FileNotFoundError) as exc:
            raise FileNotFoundError(f"缺少模板: {name}") from exc
    return Template(text).safe_substitute(values).rstrip() + "\n"


def _marker(namespace: str, name: str, boundary: str) -> str:
    return f"<!-- {namespace}:{name}:{boundary} -->"


def _fence_token(line: str) -> tuple[str, int, str] | None:
    stripped = line.lstrip(" ")
    if len(line) - len(stripped) > 3 or not stripped or stripped[0] not in "`~":
        return None
    marker = stripped[0]
    length = len(stripped) - len(stripped.lstrip(marker))
    if length < 3:
        return None
    return marker, length, stripped[length:]


def _opening_fence_token(line: str) -> tuple[str, int, str] | None:
    token = _fence_token(line)
    if token is not None and token[0] == "`" and "`" in token[2]:
        return None
    return token


def _unfenced_lines(text: str) -> Iterator[tuple[int, str]]:
    fence_marker: str | None = None
    fence_length = 0
    offset = 0
    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        fence_line = line.removeprefix("\ufeff") if offset == 0 else line
        token = (
            _fence_token(fence_line)
            if fence_marker is not None
            else _opening_fence_token(fence_line)
        )
        if fence_marker is None:
            if token is not None:
                fence_marker, fence_length, _ = token
            else:
                leading_spaces = len(line) - len(line.lstrip(" "))
                if not line.startswith("\t") and leading_spaces <= 3:
                    yield offset, line
        elif (
            token is not None
            and token[0] == fence_marker
            and token[1] >= fence_length
            and not token[2].strip()
        ):
            fence_marker = None
            fence_length = 0
        offset += len(raw_line)


def _has_unclosed_fence(text: str) -> bool:
    fence_marker: str | None = None
    fence_length = 0
    for index, raw_line in enumerate(text.splitlines()):
        fence_line = raw_line.removeprefix("\ufeff") if index == 0 else raw_line
        token = (
            _fence_token(fence_line)
            if fence_marker is not None
            else _opening_fence_token(fence_line)
        )
        if fence_marker is None:
            if token is not None:
                fence_marker, fence_length, _ = token
        elif (
            token is not None
            and token[0] == fence_marker
            and token[1] >= fence_length
            and not token[2].strip()
        ):
            fence_marker = None
            fence_length = 0
    return fence_marker is not None


def _standalone_marker_spans(text: str, marker: str) -> list[tuple[int, int]]:
    spans = []
    for offset, line in _unfenced_lines(text):
        content = line
        marker_offset = offset
        if offset == 0 and content.startswith("\ufeff"):
            content = content[1:]
            marker_offset += 1
        if content.strip(" \t") == marker:
            spans.append((marker_offset, offset + len(line)))
    return spans


def _namespace_span(text: str, namespace: str, name: str) -> tuple[int, int] | None:
    start = _marker(namespace, name, "start")
    end = _marker(namespace, name, "end")
    starts = _standalone_marker_spans(text, start)
    ends = _standalone_marker_spans(text, end)
    if not starts and not ends:
        return None
    if len(starts) != 1 or len(ends) != 1:
        raise ValueError(f"{name} 受管理区块标记缺失或重复，请先人工检查")
    if ends[0][0] < starts[0][0]:
        raise ValueError(f"{name} 受管理区块结束标记位于开始标记之前，请先人工检查")
    return starts[0][0], ends[0][1]


def _managed_section_span(text: str, name: str) -> tuple[int, int] | None:
    spans = [
        span
        for namespace in (CURRENT_MARKER_NAMESPACE, *LEGACY_MARKER_NAMESPACES)
        if (span := _namespace_span(text, namespace, name)) is not None
    ]
    if len(spans) > 1:
        raise ValueError(f"{name} 同时存在新旧受管理区块，请先人工检查")
    return spans[0] if spans else None


def _validate_managed_file(path: Path, name: str) -> None:
    if path.is_file():
        text = _read_text(path)
        if _has_unclosed_fence(text):
            raise ValueError(f"{path.name} 存在未闭合的 Markdown 代码块，请先人工检查")
        _managed_section_span(text, name)


def _has_managed_section(path: Path, name: str) -> bool:
    if not path.is_file():
        return False
    return _managed_section_span(_read_text(path), name) is not None


def _upsert_managed_section_text(
    existing: str | None,
    name: str,
    body: str,
    heading: str | None = None,
) -> str:
    start = _marker(CURRENT_MARKER_NAMESPACE, name, "start")
    end = _marker(CURRENT_MARKER_NAMESPACE, name, "end")
    if existing is not None:
        newline = _preferred_newline(existing)
        section = _with_newlines(f"{start}\n{body.rstrip()}\n{end}", newline)
        span = _managed_section_span(existing, name)
        if span is not None:
            updated = existing[: span[0]] + section + existing[span[1] :]
        else:
            updated = _append_block(existing, section, newline)
    else:
        section = f"{start}\n{body.rstrip()}\n{end}"
        prefix = f"# {heading}\n\n" if heading else ""
        updated = prefix + section + "\n"
    return updated


def _has_active_claude_import(text: str) -> bool:
    for _, line in _unfenced_lines(text):
        if line.strip() == "@AGENTS.md":
            return True
    return False


def _claude_adapter_text(existing: str | None, body: str) -> str:
    text = existing or ""
    span = _managed_section_span(text, "claude-adapter")
    unmanaged_text = text if span is None else text[: span[0]] + text[span[1] :]
    if not _has_active_claude_import(unmanaged_text):
        newline = _preferred_newline(text)
        if not text.strip():
            text = _append_block(text, "# Project Agent Instructions", newline)
        text = _append_block(text, "@AGENTS.md", newline)
    return _upsert_managed_section_text(
        text,
        "claude-adapter",
        body,
        heading="Project Agent Instructions",
    )


def _has_markdown_heading(text: str, heading: str) -> bool:
    for _, line in _unfenced_lines(text):
        if line.strip() == heading:
            return True
    return False


def _project_with_missing_sections(text: str, rules: str, structure: str) -> str:
    additions = []
    if not _has_markdown_heading(text, "## 当前长期规则"):
        additions.append(rules.rstrip())
    if not _has_markdown_heading(text, "## 项目结构与入口"):
        additions.append(structure.rstrip())
    if additions:
        newline = _preferred_newline(text)
        addition = (newline * 2).join(_with_newlines(item, newline) for item in additions)
        return _append_block(text, addition, newline)
    return text


_WRITE_BITS = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
_EXECUTE_BITS = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH


def _require_writable_file(path: Path) -> None:
    mode = path.stat().st_mode
    if not os.access(path, os.W_OK) or (os.name != "nt" and not mode & _WRITE_BITS):
        raise PermissionError(f"控制文档不可写: {path}")


def _require_writable_directory(path: Path) -> None:
    mode = path.stat().st_mode
    mode_denies_write = os.name != "nt" and not mode & _WRITE_BITS
    mode_denies_search = os.name != "nt" and not mode & _EXECUTE_BITS
    if not os.access(path, os.W_OK | os.X_OK) or mode_denies_write or mode_denies_search:
        raise PermissionError(f"控制文档目录不可写: {path}")


def _nearest_existing_directory(path: Path) -> Path:
    candidate = path
    while True:
        if candidate.is_symlink():
            raise ValueError(f"控制文档目录不能是符号链接: {candidate}")
        if candidate.exists():
            break
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent
    if not candidate.is_dir():
        raise ValueError(f"控制文档父路径必须是目录: {candidate}")
    return candidate


def _preflight_writes(paths: list[Path]) -> None:
    for path in paths:
        if path.is_file():
            _require_writable_file(path)
        _require_writable_directory(_nearest_existing_directory(path.parent))


def _stage_text(path: Path, text: str, mode: int | None) -> Path:
    if path.parent.is_symlink():
        raise ConcurrentModificationError(f"控制文档目录在写入期间变成符号链接: {path.parent}")
    for _ in range(100):
        temporary = path.parent / f".{path.name}.{secrets.token_hex(8)}.tmp"
        try:
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
        except FileExistsError:
            continue
        try:
            stream = os.fdopen(descriptor, "w", encoding="utf-8", newline="")
        except BaseException:
            os.close(descriptor)
            temporary.unlink(missing_ok=True)
            raise
        try:
            with stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            if mode is not None:
                os.chmod(temporary, mode)
            return temporary
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    raise FileExistsError(f"无法为控制文档创建唯一临时文件: {path}")


def _remove_empty_directories(paths: list[Path]) -> None:
    for path in reversed(paths):
        try:
            path.rmdir()
        except OSError:
            pass


def _atomic_write_texts(
    writes: dict[Path, str],
    expected: dict[Path, str | None],
) -> tuple[Path, ...]:
    if not writes:
        return ()
    if set(writes) != set(expected):
        raise ValueError("原子写入的预期内容与写入目标不一致")

    paths = list(writes)
    _verify_expected_contents(expected)
    _preflight_writes(paths)
    originals: dict[Path, tuple[str | None, int | None]] = {}
    for path in paths:
        originals[path] = (
            _current_control_text(path),
            stat.S_IMODE(path.stat().st_mode) if path.is_file() else None,
        )
    _verify_expected_contents(expected)

    created_directories: list[Path] = []
    staged: dict[Path, Path] = {}
    try:
        for parent in sorted({path.parent for path in paths}, key=lambda item: len(item.parts)):
            missing = []
            candidate = parent
            while not candidate.exists():
                missing.append(candidate)
                candidate = candidate.parent
            for directory in reversed(missing):
                directory.mkdir()
                created_directories.append(directory)

        for path, text in writes.items():
            staged[path] = _stage_text(path, text, originals[path][1])
    except BaseException:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)
        _remove_empty_directories(created_directories)
        raise

    committed: list[Path] = []
    try:
        current_expected = expected.copy()
        for path, temporary in staged.items():
            _verify_expected_contents(current_expected)
            os.replace(temporary, path)
            committed.append(path)
            current_expected[path] = writes[path]
        _verify_expected_contents({path: writes[path] for path in committed})
    except ConcurrentModificationError as exc:
        # A retry will merge against the latest files. Rolling back here could overwrite
        # the concurrent change that this guard is specifically intended to preserve.
        raise ConcurrentModificationError(str(exc), tuple(committed)) from exc
    except BaseException as exc:
        rollback_errors = []
        for path in reversed(committed):
            original, mode = originals[path]
            try:
                if _current_control_text(path) != writes[path]:
                    rollback_errors.append(f"{path}: 内容在回滚前发生变化，已保留最新内容")
                    continue
                if original is None:
                    path.unlink(missing_ok=True)
                else:
                    rollback: Path | None = None
                    try:
                        rollback = _stage_text(path, original, mode)
                        os.replace(rollback, path)
                    finally:
                        if rollback is not None:
                            rollback.unlink(missing_ok=True)
            except BaseException as rollback_exc:
                rollback_errors.append(f"{path}: {rollback_exc}")
        if rollback_errors:
            details = "; ".join(rollback_errors)
            raise OSError(f"控制文档写入失败且回滚不完整: {details}") from exc
        raise
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)
        _remove_empty_directories(created_directories)
    return tuple(committed)


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


def _validate_control_paths(root: Path) -> Path:
    docs = root / "agent-docs"
    if docs.is_symlink():
        raise ValueError(f"控制文档目录不能是符号链接: {docs}")
    if docs.exists() and not docs.is_dir():
        raise ValueError(f"控制文档路径必须是目录: {docs}")

    for path in (root / "AGENTS.md", root / "CLAUDE.md", docs / "project.md", docs / "state.md"):
        if path.is_symlink():
            raise ValueError(f"控制文档不能是符号链接: {path}")
        if path.exists() and not path.is_file():
            raise ValueError(f"控制文档路径必须是文件: {path}")

    project = docs / "project.md"
    if project.is_file():
        text = _read_text(project)
        if _has_unclosed_fence(text):
            raise ValueError(f"{project.name} 存在未闭合的 Markdown 代码块，请先人工检查")
    return docs


def initialize_project(root: Path, project_name: str | None = None, dry_run: bool = False) -> dict:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"项目目录不存在或不是目录: {root}")

    preserves = [
        "existing user content outside managed blocks in AGENTS.md and CLAUDE.md",
        "complete existing project.md and state.md knowledge",
        "all project files, datasets, results, and Git state",
    ]
    rules = _template("project.rules.md")
    structure = _template("project.structure.md")
    agent_protocol = _template("AGENTS.block.md")
    claude_adapter = _template("CLAUDE.block.md")
    project_template = _template(
        "project.md",
        PROJECT_NAME=project_name or root.name,
        DATE=utc_now(),
        RULES_SECTION=rules.rstrip(),
        STRUCTURE_SECTION=structure.rstrip(),
    )
    state_template = _template("state.md", DATE=utc_now())
    relative_paths = (
        ("AGENTS.md", root / "AGENTS.md"),
        ("CLAUDE.md", root / "CLAUDE.md"),
        ("agent-docs/project.md", root / "agent-docs" / "project.md"),
        ("agent-docs/state.md", root / "agent-docs" / "state.md"),
    )
    committed_actions: dict[Path, str] = {}
    initial_mode: str | None = None
    initial_agent_docs: list[str] | None = None
    initial_legacy_candidates: list[str] | None = None

    for attempt in range(MAX_CONCURRENT_RETRIES):
        docs = _validate_control_paths(root)
        _validate_managed_file(root / "AGENTS.md", "protocol")
        _validate_managed_file(root / "CLAUDE.md", "claude-adapter")
        existing_agent_docs = sorted(path.name for path in docs.glob("*.md")) if docs.is_dir() else []
        mode = "refresh" if _has_managed_section(root / "AGENTS.md", "protocol") else "initialize"
        if initial_mode is None:
            initial_mode = mode
            initial_agent_docs = existing_agent_docs
            initial_legacy_candidates = _legacy_review_candidates(root)

        agents_path = root / "AGENTS.md"
        claude_path = root / "CLAUDE.md"
        project_path = docs / "project.md"
        state_path = docs / "state.md"
        existing_contents = {
            path: _current_control_text(path)
            for _, path in relative_paths
        }
        final_contents = {
            agents_path: _upsert_managed_section_text(
                existing_contents[agents_path],
                "protocol",
                agent_protocol,
                heading="Project Agent Instructions",
            ),
            claude_path: _claude_adapter_text(existing_contents[claude_path], claude_adapter),
            project_path: (
                project_template
                if existing_contents[project_path] is None
                else _project_with_missing_sections(existing_contents[project_path], rules, structure)
            ),
            state_path: state_template if existing_contents[state_path] is None else existing_contents[state_path],
        }
        writes = {
            path: content
            for path, content in final_contents.items()
            if existing_contents[path] != content
        }
        planned_created = [
            relative
            for relative, path in relative_paths
            if path in writes and existing_contents[path] is None
        ]
        planned_updated = [
            relative
            for relative, path in relative_paths
            if path in writes and existing_contents[path] is not None
        ]
        planned_unchanged = [relative for relative, path in relative_paths if path not in writes]
        result = {
            "ok": True,
            "dry_run": dry_run,
            "mode": initial_mode,
            "root": str(root),
            "protocol_version": PROTOCOL_VERSION,
            "planned": [*planned_created, *planned_updated],
            "created": planned_created,
            "updated": planned_updated,
            "unchanged": planned_unchanged,
            "preserves": preserves,
            "existing_agent_docs": initial_agent_docs,
            "legacy_review_candidates": initial_legacy_candidates,
        }
        if dry_run:
            return result

        try:
            committed = _atomic_write_texts(
                writes,
                {path: existing_contents[path] for path in writes},
            )
        except ConcurrentModificationError as exc:
            for path in exc.committed:
                committed_actions.setdefault(
                    path,
                    "created" if existing_contents[path] is None else "updated",
                )
            if attempt + 1 == MAX_CONCURRENT_RETRIES:
                if committed_actions:
                    partial = ", ".join(
                        relative
                        for relative, path in relative_paths
                        if path in committed_actions
                    )
                    raise ConcurrentModificationError(
                        f"{exc}；初始化已写入部分控制文档 ({partial})，"
                        "请确认并发修改结束后重新运行 init",
                        tuple(committed_actions),
                    ) from exc
                raise
            continue
        for path in committed:
            committed_actions.setdefault(
                path,
                "created" if existing_contents[path] is None else "updated",
            )
        result["created"] = [
            relative
            for relative, path in relative_paths
            if committed_actions.get(path) == "created"
        ]
        result["updated"] = [
            relative
            for relative, path in relative_paths
            if committed_actions.get(path) == "updated"
        ]
        result["planned"] = [*result["created"], *result["updated"]]
        result["unchanged"] = [
            relative for relative, path in relative_paths if path not in committed_actions
        ]
        return result

    raise ConcurrentModificationError("控制文档持续发生变化，无法安全完成初始化")
