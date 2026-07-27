#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import tempfile
import zipapp
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "project-continuity"
SOURCE = PLUGIN / "scripts"
TEMPLATES = PLUGIN / "assets" / "project-template"


def build(target: Path) -> Path:
    target = target.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="project-continuity-build-") as temporary:
        stage = Path(temporary)
        package = stage / "project_continuity"
        template_package = package / "templates"
        template_package.mkdir(parents=True)

        for name in ("__init__.py", "__main__.py", "continuity_core.py", "project_continuity.py"):
            shutil.copy2(SOURCE / name, package / name)
        shutil.copy2(TEMPLATES / "__init__.py", template_package / "__init__.py")
        for template in TEMPLATES.glob("*.md"):
            shutil.copy2(template, template_package / template.name)

        (stage / "__main__.py").write_text(
            "from project_continuity.project_continuity import main\n"
            "raise SystemExit(main())\n",
            encoding="utf-8",
        )
        zipapp.create_archive(stage, target, interpreter="/usr/bin/env python3", compressed=True)
    target.chmod(target.stat().st_mode | 0o111)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a standalone Project Continuity zipapp.")
    parser.add_argument("output", nargs="?", default="dist/project-continuity.pyz")
    args = parser.parse_args()
    print(build(Path(args.output)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
