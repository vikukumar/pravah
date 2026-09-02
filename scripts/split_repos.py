#!/usr/bin/env python3
"""
PRAVAH — Monorepo to Multi-Repo Split Automation Tool
Exports apps/api, apps/web, and packages/shared-types into standalone, isolated Git repositories.

Usage:
    python scripts/split_repos.py [--out-dir ./dist-repos]
"""

import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def copy_directory(src: Path, dst: Path, ignore_patterns: list):
    """Copies directory recursively while excluding specified ignore patterns."""
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        if item.name in ignore_patterns or any(item.match(p) for p in ignore_patterns):
            continue
        if item.is_dir():
            shutil.copytree(
                item,
                dst / item.name,
                ignore=shutil.ignore_patterns(*ignore_patterns),
            )
        else:
            shutil.copy2(item, dst / item.name)


def init_git_repo(repo_dir: Path, repo_name: str, desc: str):
    """Initializes a fresh standalone git repository with an initial commit."""
    try:
        subprocess.run(["git", "init", "-b", "main"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"chore: initial standalone repository setup for {repo_name} v1.0.0"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        print(f"  ✓ Initialized Git repo for {repo_name} (main branch)")
    except Exception as e:
        print(f"  ⚠ Git init notice for {repo_name}: {e}")


def split_repositories(out_dir_path: str):
    out_dir = Path(out_dir_path).resolve()
    print("\n========================================================")
    print("      PRAVAH Monorepo -> Multi-Repo Splitter")
    print("========================================================")
    print(f"Target Output Directory: {out_dir}\n")

    common_ignore = [
        "node_modules",
        ".next",
        "__pycache__",
        ".venv",
        "venv",
        ".pytest_cache",
        "*.pyc",
        ".git",
        "*.db",
        "*.sqlite",
        "uploads",
        "storage",
        "dist",
        "build",
    ]

    # 1. Export Backend API
    backend_dst = out_dir / "pravah-backend"
    print(f"📦 Exporting Backend API to {backend_dst.name}...")
    copy_directory(ROOT_DIR / "apps" / "api", backend_dst, common_ignore)
    init_git_repo(backend_dst, "pravah-backend", "PRAVAH FastAPI Backend")

    # 2. Export Frontend Web
    frontend_dst = out_dir / "pravah-frontend"
    print(f"\n📦 Exporting Frontend Web to {frontend_dst.name}...")
    copy_directory(ROOT_DIR / "apps" / "web", frontend_dst, common_ignore)
    init_git_repo(frontend_dst, "pravah-frontend", "PRAVAH Next.js 16 Web")

    # 3. Export Shared Types
    types_dst = out_dir / "pravah-shared-types"
    print(f"\n📦 Exporting Shared Types to {types_dst.name}...")
    copy_directory(ROOT_DIR / "packages" / "shared-types", types_dst, common_ignore)
    init_git_repo(types_dst, "pravah-shared-types", "PRAVAH Shared TypeScript Types")

    print("\n========================================================")
    print("               Multi-Repo Split Complete!")
    print("========================================================")
    print("Generated 3 standalone repositories ready for GitHub/GitLab:")
    print(f"  1. Backend Repository:      {backend_dst}")
    print(f"  2. Frontend Repository:     {frontend_dst}")
    print(f"  3. Shared Types Package:    {types_dst}")
    print("\nTo push each standalone repository to its remote:")
    print("  cd <repo_directory>")
    print("  git remote add origin git@github.com:<your-org>/<repo-name>.git")
    print("  git push -u origin main\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split Pravah Monorepo into Multi-Repo Structure")
    parser.add_argument(
        "--out-dir",
        default="./dist-repos",
        help="Output directory where standalone repositories will be created",
    )
    args = parser.parse_args()
    split_repositories(args.out_dir)
