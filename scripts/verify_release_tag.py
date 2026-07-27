#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def expected_tag(pyproject: Path = ROOT / "pyproject.toml") -> str:
    with pyproject.open("rb") as stream:
        metadata = tomllib.load(stream)
    version = metadata.get("project", {}).get("version")
    if not isinstance(version, str) or not version:
        raise ValueError(f"缺少有效的 project.version: {pyproject}")
    return f"v{version}"


def verify_release_tag(tag: str, pyproject: Path = ROOT / "pyproject.toml") -> None:
    expected = expected_tag(pyproject)
    if tag != expected:
        raise ValueError(f"release tag 必须是 {expected}，实际为 {tag}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a release tag against pyproject.toml.")
    parser.add_argument("tag")
    args = parser.parse_args()
    try:
        verify_release_tag(args.tag)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"release tag verified: {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
