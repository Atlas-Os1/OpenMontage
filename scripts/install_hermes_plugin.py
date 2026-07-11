#!/usr/bin/env python3
"""Install the OpenMontage Hermes plugin into a selected Hermes profile.

Usage:
  python scripts/install_hermes_plugin.py --hermes-home /opt/data/profiles/Atlas-Content/.hermes
  python scripts/install_hermes_plugin.py --hermes-home "$HERMES_HOME"

This copies only the plugin integration layer. It never copies .env files,
credentials, generated media, or the rest of the OpenMontage checkout.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


EXCLUDED = {"__pycache__", ".env", ".DS_Store"}


def copy_tree(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.name in EXCLUDED:
            continue
        destination = target / item.name
        if item.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(item, destination)
        else:
            shutil.copy2(item, destination)


def copy_openmontage_skills(source: Path, hermes_home: Path) -> Path:
    skills_source = source / ".agents" / "skills"
    skills_target = hermes_home / "skills" / "openmontage"
    if skills_target.exists():
        shutil.rmtree(skills_target)
    copy_tree(skills_source, skills_target)
    return skills_target


def copy_openmontage_core_skills(source: Path, hermes_home: Path) -> Path:
    skills_source = source / "skills"
    skills_target = hermes_home / "skills" / "openmontage-core"
    if skills_target.exists():
        shutil.rmtree(skills_target)
    copy_tree(skills_source, skills_target)
    return skills_target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hermes-home", required=True, help="Target profile Hermes home directory")
    parser.add_argument("--no-skills", action="store_true", help="Install only the plugin tools, not the OpenMontage skill pack")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "hermes_plugin"
    hermes_home = Path(args.hermes_home).expanduser().resolve()
    target = hermes_home / "plugins" / "openmontage"
    if not (source / "plugin.yaml").is_file():
        raise SystemExit(f"OpenMontage plugin source is incomplete: {source}")
    if not (repo_root / ".agents" / "skills").is_dir():
        raise SystemExit(f"OpenMontage skill pack is missing: {repo_root / '.agents' / 'skills'}")

    copy_tree(source, target)
    (target / "openmontage_root.txt").write_text(str(repo_root), encoding="utf-8")
    skills_target = None if args.no_skills else copy_openmontage_skills(repo_root, hermes_home)
    core_skills_target = None if args.no_skills else copy_openmontage_core_skills(repo_root, hermes_home)
    print(f"Installed OpenMontage Hermes plugin: {target}")
    print(f"OpenMontage engine root marker: {target / 'openmontage_root.txt'}")
    if skills_target:
        print(f"Installed OpenMontage Layer 3 skills: {skills_target}")
    if core_skills_target:
        print(f"Installed OpenMontage Layer 2 skills: {core_skills_target}")
    print("Enable it in the target profile with: hermes plugins enable openmontage")
    print("Restart the target Hermes process after installation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
