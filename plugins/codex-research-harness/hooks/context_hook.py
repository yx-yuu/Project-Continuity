#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


PLUGIN_ROOT = Path(os.environ.get("PLUGIN_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from harness_core import find_project_root, sync_project  # noqa: E402


def emit(value: dict) -> None:
    print(json.dumps(value, ensure_ascii=False))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    root = find_project_root(Path(payload.get("cwd", ".")))
    if root is None:
        return 0

    event = payload.get("hook_event_name")
    if event == "PreCompact":
        checkpoint = root / "agent-docs" / "checkpoint.md"
        message = (
            "Research Harness: compact 前请确认 checkpoint.md 已保存任务范围、完成条件、验证边界、当前进展和下一步。"
            if checkpoint.is_file()
            else "Research Harness: 当前没有 checkpoint.md；若这是关键、长程或跨阶段任务，请先保存任务契约。"
        )
        emit({"continue": True, "systemMessage": message})
        return 0

    if event == "SessionStart":
        try:
            counts = sync_project(root)["counts"]
            change_note = f"检测到未确认文件变化 +{counts['added']} ~{counts['modified']} -{counts['removed']}。" if counts["total"] else "未检测到未确认文件变化。"
        except (OSError, ValueError):
            change_note = "文件增量状态暂时无法读取，请运行 research-harness doctor。"
        context = (
            "Research Harness 已启用。先读取 AGENTS.md、agent-docs/index.md、project.md、state.md，"
            "存在 checkpoint.md 时再读取任务契约。只恢复当前有效信息；具体任务步骤必须服从项目约束、证据门禁和完成条件。"
            + change_note
        )
        emit({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
