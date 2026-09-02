#!/usr/bin/env python3
"""
PRAVAH — Semantic Version Management CLI Tool
Manage, bump, and sync versions across Frontend, Backend, and Shared Packages.

Usage:
    python scripts/version.py show
    python scripts/version.py bump patch [--target all|backend|frontend|types]
    python scripts/version.py bump minor [--target all|backend|frontend|types]
    python scripts/version.py bump major [--target all|backend|frontend|types]
    python scripts/version.py sync
"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT_DIR / "version.json"
BACKEND_INIT_FILE = ROOT_DIR / "apps" / "api" / "app" / "__init__.py"
FRONTEND_PACKAGE_FILE = ROOT_DIR / "apps" / "web" / "package.json"
FRONTEND_VERSION_FILE = ROOT_DIR / "apps" / "web" / "lib" / "version.ts"
TYPES_PACKAGE_FILE = ROOT_DIR / "packages" / "shared-types" / "package.json"
CHANGELOG_FILE = ROOT_DIR / "CHANGELOG.md"


def load_version_json() -> dict:
    if not VERSION_FILE.exists():
        data = {
            "version": "1.0.0",
            "backend": "1.0.0",
            "frontend": "1.0.0",
            "shared_types": "1.0.0",
            "api_version": "v1",
            "schema_version": "c61b97841082",
            "min_compatible_backend": "1.0.0",
            "min_compatible_frontend": "1.0.0",
            "release_date": datetime.date.today().isoformat(),
            "codename": "StreamFlow",
        }
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data

    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_version_json(data: dict):
    data["release_date"] = datetime.date.today().isoformat()
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def bump_semver(current: str, part: str) -> str:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(.*)$", current.strip())
    if not match:
        raise ValueError(f"Invalid semver string: {current}")

    major, minor, patch, suffix = int(match.group(1)), int(match.group(2)), int(match.group(3)), match.group(4)

    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    elif part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump level '{part}', must be patch, minor, or major.")


def sync_files(data: dict):
    backend_v = data["backend"]
    frontend_v = data["frontend"]
    types_v = data["shared_types"]

    # 1. Update apps/api/app/__init__.py
    if BACKEND_INIT_FILE.exists():
        content = f'"""\nPRAVAH FastAPI Backend Application\n"""\n\n__version__ = "{backend_v}"\n__api_version__ = "{data.get("api_version", "v1")}"\n'
        with open(BACKEND_INIT_FILE, "w", encoding="utf-8") as f:
            f.write(content)

    # 2. Update apps/web/package.json
    if FRONTEND_PACKAGE_FILE.exists():
        with open(FRONTEND_PACKAGE_FILE, "r", encoding="utf-8") as f:
            pkg = json.load(f)
        pkg["version"] = frontend_v
        with open(FRONTEND_PACKAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(pkg, f, indent=2)

    # 3. Update apps/web/lib/version.ts
    if FRONTEND_VERSION_FILE.exists():
        content = f'export const FRONTEND_VERSION = "{frontend_v}";\n' \
                  f'export const MIN_COMPATIBLE_BACKEND_VERSION = "{data.get("min_compatible_backend", "1.0.0")}";\n' \
                  f'export const API_VERSION = "{data.get("api_version", "v1")}";\n' \
                  f'export const RELEASE_CODENAME = "{data.get("codename", "StreamFlow")}";\n\n' \
                  f'export interface SystemVersionInfo {{\n' \
                  f'  backend_version: string;\n' \
                  f'  frontend_version: string;\n' \
                  f'  shared_types_version: string;\n' \
                  f'  api_version: string;\n' \
                  f'  schema_version: string;\n' \
                  f'  codename: string;\n' \
                  f'  environment: string;\n' \
                  f'  status: string;\n' \
                  f'}}\n'
        with open(FRONTEND_VERSION_FILE, "w", encoding="utf-8") as f:
            f.write(content)

    # 4. Update packages/shared-types/package.json
    if TYPES_PACKAGE_FILE.exists():
        with open(TYPES_PACKAGE_FILE, "r", encoding="utf-8") as f:
            pkg = json.load(f)
        pkg["version"] = types_v
        with open(TYPES_PACKAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(pkg, f, indent=2)

    # 5. Append to CHANGELOG.md if needed
    if not CHANGELOG_FILE.exists():
        with open(CHANGELOG_FILE, "w", encoding="utf-8") as f:
            f.write("# PRAVAH Changelog\n\nAll notable changes to the PRAVAH platform are documented here.\n\n")


def main():
    parser = argparse.ArgumentParser(description="PRAVAH Version Management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # show
    subparsers.add_parser("show", help="Display current system versions")

    # sync
    subparsers.add_parser("sync", help="Synchronize versions across all repository files")

    # bump
    bump_parser = subparsers.add_parser("bump", help="Bump version (patch, minor, or major)")
    bump_parser.add_argument("level", choices=["patch", "minor", "major"], help="Semver increment level")
    bump_parser.add_argument(
        "--target",
        choices=["all", "backend", "frontend", "types"],
        default="all",
        help="Component to bump (default: all)",
    )

    args = parser.parse_args()
    data = load_version_json()

    if args.command == "show":
        print("\n========================================================")
        print("          PRAVAH Version Status Matrix")
        print("========================================================")
        print(f"  Platform Release:    v{data.get('version')}")
        print(f"  Backend API:         v{data.get('backend')}")
        print(f"  Frontend Web:        v{data.get('frontend')}")
        print(f"  Shared Types:        v{data.get('shared_types')}")
        print(f"  API Endpoint Prefix: {data.get('api_version')}")
        print(f"  DB Schema Revision:  {data.get('schema_version')}")
        print(f"  Codename:            {data.get('codename')}")
        print(f"  Release Date:        {data.get('release_date')}")
        print("========================================================\n")

    elif args.command == "sync":
        sync_files(data)
        print("✓ All project files successfully synchronized to version.json!")

    elif args.command == "bump":
        level = args.level
        target = args.target

        if target in ("all", "backend"):
            data["backend"] = bump_semver(data["backend"], level)
        if target in ("all", "frontend"):
            data["frontend"] = bump_semver(data["frontend"], level)
        if target in ("all", "types"):
            data["shared_types"] = bump_semver(data["shared_types"], level)

        if target == "all":
            data["version"] = bump_semver(data["version"], level)

        save_version_json(data)
        sync_files(data)

        print(f"\n✓ Successfully bumped {target} to {level} version!")
        print(f"  New Platform: v{data['version']} | Backend: v{data['backend']} | Frontend: v{data['frontend']} | Types: v{data['shared_types']}\n")


if __name__ == "__main__":
    main()
