#!/usr/bin/env python3
from __future__ import annotations

import argparse
import configparser
import re
import sys
from collections import Counter
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "plugins" / "project-continuity"
SCRIPT_ROOT = SOURCE_ROOT / "scripts"
TEMPLATE_ROOT = SOURCE_ROOT / "assets" / "project-template"
EXPECTED_SOURCE_FILES = {
    "project_continuity/__init__.py": SCRIPT_ROOT / "__init__.py",
    "project_continuity/__main__.py": SCRIPT_ROOT / "__main__.py",
    "project_continuity/continuity_core.py": SCRIPT_ROOT / "continuity_core.py",
    "project_continuity/project_continuity.py": SCRIPT_ROOT / "project_continuity.py",
    "project_continuity/templates/__init__.py": TEMPLATE_ROOT / "__init__.py",
    "project_continuity/templates/AGENTS.block.md": TEMPLATE_ROOT / "AGENTS.block.md",
    "project_continuity/templates/CLAUDE.block.md": TEMPLATE_ROOT / "CLAUDE.block.md",
    "project_continuity/templates/project.md": TEMPLATE_ROOT / "project.md",
    "project_continuity/templates/project.rules.md": TEMPLATE_ROOT / "project.rules.md",
    "project_continuity/templates/project.structure.md": TEMPLATE_ROOT / "project.structure.md",
    "project_continuity/templates/state.md": TEMPLATE_ROOT / "state.md",
}
EXPECTED_PACKAGE_FILES = set(EXPECTED_SOURCE_FILES)
EXPECTED_ENTRY_POINT = "project_continuity.project_continuity:main"
EXPECTED_NAME = "project-continuity"


def _configure_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="strict")


def _project_version() -> str:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    project_section = re.search(r"(?ms)^\[project\]\s*(.*?)(?=^\[|\Z)", pyproject)
    if project_section is None:
        raise ValueError("pyproject.toml 缺少 [project] 区块")
    version = re.search(r'^version\s*=\s*["\']([^"\']+)["\']\s*$', project_section.group(1), re.MULTILINE)
    if version is None:
        raise ValueError("pyproject.toml 缺少有效的 project.version")
    return version.group(1)


EXPECTED_VERSION = _project_version()
EXPECTED_DIST_INFO = f"project_continuity-{EXPECTED_VERSION}.dist-info"


def _single_default_wheel() -> Path:
    wheels = sorted(Path("dist").glob("project_continuity-*.whl"))
    if len(wheels) != 1:
        raise ValueError(f"预期 dist 中恰好有一个 project_continuity wheel，实际为 {len(wheels)}")
    return wheels[0]


def verify_wheel(path: Path) -> None:
    with ZipFile(path) as archive:
        members = archive.namelist()
        duplicates = sorted(name for name, count in Counter(members).items() if count > 1)
        if duplicates:
            raise ValueError(f"wheel 包含重复成员: {duplicates}")
        corrupt = archive.testzip()
        if corrupt is not None:
            raise ValueError(f"wheel 成员 CRC 校验失败: {corrupt}")
        names = set(members)
        package_files = {
            name
            for name in names
            if name.startswith("project_continuity/") and not name.endswith("/")
        }
        if package_files != EXPECTED_PACKAGE_FILES:
            missing = sorted(EXPECTED_PACKAGE_FILES - package_files)
            unexpected = sorted(package_files - EXPECTED_PACKAGE_FILES)
            raise ValueError(f"wheel 包内容不匹配；缺失={missing}；多余={unexpected}")
        for name, source in EXPECTED_SOURCE_FILES.items():
            actual = archive.read(name)
            expected = source.read_bytes()
            if actual != expected:
                raise ValueError(f"wheel 文件内容与源码不一致: {name}")

        dist_info_directories = {
            name.split("/", 1)[0]
            for name in names
            if "/" in name and name.split("/", 1)[0].endswith(".dist-info")
        }
        if len(dist_info_directories) != 1:
            raise ValueError(f"预期恰好一个 dist-info 目录，实际为 {sorted(dist_info_directories)}")
        dist_info = next(iter(dist_info_directories))
        if dist_info != EXPECTED_DIST_INFO:
            raise ValueError(f"wheel dist-info 版本不匹配；预期={EXPECTED_DIST_INFO}；实际={dist_info}")
        unexpected_top_level = sorted(
            name
            for name in names
            if not name.endswith("/")
            and not name.startswith("project_continuity/")
            and not name.startswith(f"{dist_info}/")
        )
        if unexpected_top_level:
            raise ValueError(f"wheel 包含非预期顶层内容: {unexpected_top_level}")
        metadata_path = f"{dist_info}/METADATA"
        if metadata_path not in names:
            raise ValueError(f"wheel 缺少 METADATA: {metadata_path}")
        metadata = BytesParser(policy=default).parsebytes(archive.read(metadata_path))
        if metadata.get("Name") != EXPECTED_NAME or metadata.get("Version") != EXPECTED_VERSION:
            raise ValueError(
                "wheel METADATA 不匹配；"
                f"预期={EXPECTED_NAME} {EXPECTED_VERSION}；"
                f"实际={metadata.get('Name')} {metadata.get('Version')}"
            )
        for required in ("WHEEL", "RECORD"):
            required_path = f"{dist_info}/{required}"
            if required_path not in names:
                raise ValueError(f"wheel 缺少必需元数据文件: {required_path}")
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
    _configure_utf8_output()
    parser = argparse.ArgumentParser(description="Verify the built Project Continuity wheel.")
    parser.add_argument("wheel", nargs="?", type=Path)
    args = parser.parse_args()
    try:
        wheel = args.wheel or _single_default_wheel()
        verify_wheel(wheel)
    except (BadZipFile, KeyError, OSError, ValueError, configparser.Error, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"wheel verified: {wheel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
