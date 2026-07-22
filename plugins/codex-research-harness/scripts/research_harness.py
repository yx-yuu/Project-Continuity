from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from .harness_core import PROTOCOL_VERSION, initialize_project
except ImportError:
    from harness_core import PROTOCOL_VERSION, initialize_project


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="research-harness",
        description="Install a lightweight, agent-maintained research project protocol.",
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
    args = build_parser().parse_args(argv)
    try:
        result = initialize_project(Path(args.path), args.project_name, args.dry_run)
        if args.json:
            _print_json(result)
        elif args.dry_run:
            print(f"模式: {result['mode']}；协议版本: {result['protocol_version']}")
            print(f"将处理: {result['root']}")
            for item in result["planned"]:
                print(f"- {item}")
        else:
            print(f"已完成项目协议 {result['mode']}: {result['root']}")
            if result["legacy_review_candidates"]:
                print("发现旧版控制文件；请让 agent 提取仍有效信息后再决定是否清理：")
                for item in result["legacy_review_candidates"]:
                    print(f"- {item}")
            print('下一步：在项目中告诉 agent “使用 research-harness 接管当前项目”。')
        return 0
    except (OSError, ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
