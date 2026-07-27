#!/usr/bin/env python3
from __future__ import annotations

import argparse
import configparser
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile


EXPECTED_PACKAGE_FILES = {
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
EXPECTED_ENTRY_POINT = "project_continuity.project_continuity:main"


def _single_default_wheel() -> Path:
    wheels = sorted(Path("dist").glob("project_continuity-*.whl"))
    if len(wheels) != 1:
        raise ValueError(f"预期 dist 中恰好有一个 project_continuity wheel，实际为 {len(wheels)}")
    return wheels[0]


def verify_wheel(path: Path) -> None:
    with ZipFile(path) as archive:
        names = set(archive.namelist())
        package_files = {
            name
            for name in names
            if name.startswith("project_continuity/") and not name.endswith("/")
        }
        if package_files != EXPECTED_PACKAGE_FILES:
            missing = sorted(EXPECTED_PACKAGE_FILES - package_files)
            unexpected = sorted(package_files - EXPECTED_PACKAGE_FILES)
            raise ValueError(f"wheel 包内容不匹配；缺失={missing}；多余={unexpected}")

        legacy = sorted(name for name in names if name.startswith("research_harness/"))
        if legacy:
            raise ValueError(f"wheel 仍包含旧包: {legacy}")

        dist_info_directories = {
            name.split("/", 1)[0]
            for name in names
            if "/" in name and name.split("/", 1)[0].endswith(".dist-info")
        }
        if len(dist_info_directories) != 1:
            raise ValueError(f"预期恰好一个 dist-info 目录，实际为 {sorted(dist_info_directories)}")
        dist_info = next(iter(dist_info_directories))
        if not dist_info.startswith("project_continuity-"):
            raise ValueError(f"wheel dist-info 不属于 project-continuity: {dist_info}")
        entry_points = f"{dist_info}/entry_points.txt"
        if entry_points not in names:
            raise ValueError(f"wheel 缺少 console entry point: {entry_points}")
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(archive.read(entry_points).decode("utf-8"))
        actual = parser.get("console_scripts", "project-continuity", fallback=None)
        if actual != EXPECTED_ENTRY_POINT:
            raise ValueError(
                "project-continuity console entry point 不匹配；"
                f"预期={EXPECTED_ENTRY_POINT}；实际={actual}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the built Project Continuity wheel.")
    parser.add_argument("wheel", nargs="?", type=Path)
    args = parser.parse_args()
    try:
        wheel = args.wheel or _single_default_wheel()
        verify_wheel(wheel)
    except (BadZipFile, OSError, ValueError, configparser.Error, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"wheel verified: {wheel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
