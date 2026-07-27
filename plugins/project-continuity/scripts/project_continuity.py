from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from .continuity_core import PROTOCOL_VERSION, initialize_project
except ImportError:
    from continuity_core import PROTOCOL_VERSION, initialize_project


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _configure_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="strict")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="project-continuity",
        description="Install a lightweight, agent-maintained project continuity protocol.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {PROTOCOL_VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Install or refresh the project protocol")
    init.add_argument("path", nargs="?", default=".")
    init.add_argument("--project-name")
    init.add_argument("--dry-run", action="store_true")
    init.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_output()
    args = build_parser().parse_args(argv)
    try:
        result = initialize_project(Path(args.path), args.project_name, args.dry_run)
        if args.json:
            _print_json(result)
        elif args.dry_run:
            print(f"模式: {result['mode']}；协议版本: {result['protocol_version']}")
            print(f"将处理: {result['root']}")
            if result["planned"]:
                for item in result["planned"]:
                    action = "创建" if item in result["created"] else "更新"
                    print(f"- {action}: {item}")
            else:
                print("- 无文件变化")
        else:
            if result["created"]:
                print(f"已创建: {', '.join(result['created'])}")
            if result["updated"]:
                print(f"已更新: {', '.join(result['updated'])}")
            if not result["planned"]:
                print("协议已是当前版本，未写入文件")
            print(f"项目协议 {result['mode']} 完成: {result['root']}")
            print("下一步：在项目中告诉 agent 使用 $project-continuity 接管当前项目。")
        return 0
    except (OSError, ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
