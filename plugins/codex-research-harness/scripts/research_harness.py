#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from harness_core import (
    checks_ok,
    clear_checkpoint,
    doctor_project,
    initialize_project,
    read_checkpoint,
    resume_project,
    save_checkpoint,
    scan_project,
    sync_project,
)


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="research-harness",
        description="Maintain a lightweight project control plane for one research project.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Read-only project inventory")
    scan.add_argument("path", nargs="?", default=".")
    scan.add_argument("--project-name")
    scan.add_argument("--json", action="store_true")

    init = subparsers.add_parser("init", help="Initialize or migrate the project control plane")
    init.add_argument("path", nargs="?", default=".")
    init.add_argument("--project-name")
    init.add_argument("--dry-run", action="store_true")
    init.add_argument("--json", action="store_true")

    sync = subparsers.add_parser("sync", help="Detect external file changes without interpreting them")
    sync.add_argument("path", nargs="?", default=".")
    sync.add_argument("--accept", action="store_true", help="Accept the current filesystem as the new baseline")
    sync.add_argument("--json", action="store_true")

    doctor = subparsers.add_parser("doctor", help="Check context structure, lifecycle, and size budgets")
    doctor.add_argument("path", nargs="?", default=".")
    doctor.add_argument("--json", action="store_true")

    resume = subparsers.add_parser("resume", help="Build a compact recovery packet")
    resume.add_argument("path", nargs="?", default=".")
    resume.add_argument("--json", action="store_true")

    checkpoint = subparsers.add_parser("checkpoint", help="Maintain one replaceable task contract and checkpoint")
    checkpoint_subparsers = checkpoint.add_subparsers(dest="checkpoint_command", required=True)

    checkpoint_save = checkpoint_subparsers.add_parser("save", help="Replace the current checkpoint")
    checkpoint_save.add_argument("--path", default=".")
    checkpoint_save.add_argument("--goal", required=True)
    checkpoint_save.add_argument("--scope", required=True)
    checkpoint_save.add_argument("--done", required=True)
    checkpoint_save.add_argument("--validation", required=True)
    checkpoint_save.add_argument("--impact", action="append", default=[])
    checkpoint_save.add_argument("--current", required=True)
    checkpoint_save.add_argument("--next", dest="next_step", required=True)
    checkpoint_save.add_argument("--fact", action="append", default=[])
    checkpoint_save.add_argument("--decision", action="append", default=[])
    checkpoint_save.add_argument("--risk", action="append", default=[])
    checkpoint_save.add_argument("--ref", action="append", default=[])
    checkpoint_save.add_argument("--json", action="store_true")

    checkpoint_show = checkpoint_subparsers.add_parser("show", help="Show the current checkpoint")
    checkpoint_show.add_argument("--path", default=".")
    checkpoint_show.add_argument("--json", action="store_true")

    checkpoint_clear = checkpoint_subparsers.add_parser("clear", help="Move the checkpoint to trash")
    checkpoint_clear.add_argument("--path", default=".")
    checkpoint_clear.add_argument("--force", action="store_true", help="Clear an abandoned checkpoint despite pending file changes")
    checkpoint_clear.add_argument("--json", action="store_true")
    return parser


def _print_sync(result: dict) -> None:
    counts = result["counts"]
    status = "已接受为新基线" if result["accepted"] else "只读候选，尚未接受"
    print(f"文件变化: +{counts['added']} ~{counts['modified']} -{counts['removed']}；{status}。")
    for label, key in (("新增", "added"), ("修改", "modified"), ("移除", "removed")):
        for row in result[key][:30]:
            print(f"- {label}: {row['path']} [{row.get('category', 'unknown')}]")
    if result["display_truncated"]:
        print("变化清单过长，输出已截断；使用 --json 查看受限的机器清单。")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "scan":
            inventory = scan_project(Path(args.path), args.project_name)
            if args.json:
                _print_json({"ok": True, "inventory": asdict(inventory)})
            else:
                print(f"项目: {inventory.project_name}")
                print(f"扫描文件: {inventory.scanned_file_count}{'（已截断）' if inventory.scan_truncated else ''}")
                print(f"论文候选: {len(inventory.paper_files)}")
                print(f"上下文文档候选: {len(inventory.context_documents)}")
                print("扫描只发现候选，不移动文件，也不更新科研事实。")
            return 0

        if args.command == "init":
            result = initialize_project(Path(args.path), args.project_name, args.dry_run)
            if args.json:
                _print_json(result)
            elif args.dry_run:
                print(f"将初始化: {result['root']}")
                for item in result["planned"]:
                    print(f"- {item}")
            else:
                print(f"已初始化项目控制面: {result['root']}")
                print("自动发现没有写入长期事实；请只登记当前有效来源。")
                if result["legacy_cleanup_candidates"]:
                    print("发现 v0.1 遗留内容，请审查后清理：")
                    for item in result["legacy_cleanup_candidates"]:
                        print(f"- {item}")
            return 0

        if args.command == "sync":
            result = sync_project(Path(args.path), args.accept)
            _print_json(result) if args.json else _print_sync(result)
            return 0

        if args.command == "doctor":
            checks = doctor_project(Path(args.path))
            ok = checks_ok(checks)
            if args.json:
                _print_json({"ok": ok, "checks": [asdict(check) for check in checks]})
            else:
                for check in checks:
                    print(f"[{check.level.upper()}] {check.code}: {check.message}")
            return 0 if ok else 1

        if args.command == "resume":
            result = resume_project(Path(args.path))
            if args.json:
                _print_json(result)
            else:
                print("恢复顺序：")
                for item in result["read_first"]:
                    print(f"- {item}")
                if result["checkpoint"]:
                    print("\n当前 checkpoint：\n")
                    print(result["checkpoint"].rstrip())
                counts = result["pending_changes"]
                print(f"\n未确认文件变化: +{counts['added']} ~{counts['modified']} -{counts['removed']}")
            return 0

        if args.command == "checkpoint" and args.checkpoint_command == "save":
            path = save_checkpoint(
                Path(args.path), args.goal, args.current, args.next_step,
                args.fact, args.decision, args.risk, args.ref,
                scope=args.scope, done=args.done, validation=args.validation, impacts=args.impact,
            )
            result = {"ok": True, "checkpoint": str(path)}
            _print_json(result) if args.json else print(f"已替换 checkpoint: {path}")
            return 0

        if args.command == "checkpoint" and args.checkpoint_command == "show":
            content = read_checkpoint(Path(args.path))
            if content is None:
                raise ValueError("当前没有 checkpoint。")
            _print_json({"ok": True, "content": content}) if args.json else print(content.rstrip())
            return 0

        if args.command == "checkpoint" and args.checkpoint_command == "clear":
            path = clear_checkpoint(Path(args.path), force=args.force)
            result = {"ok": True, "trashed": str(path)}
            _print_json(result) if args.json else print(f"已移入 trash: {path}")
            return 0
    except (OSError, ValueError, FileNotFoundError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
