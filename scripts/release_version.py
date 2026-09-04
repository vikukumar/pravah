#!/usr/bin/env python3
"""
PRAVAH — Automated Semantic Versioning & Release Notes Generator
Parses Conventional Commits since the last release tag, calculates the next SemVer
version (major, minor, patch), synchronizes all repository version files,
and generates categorized release notes for GitHub Releases.

Usage:
    python scripts/release_version.py [--bump-type auto|patch|minor|major|custom]
                                      [--custom-version X.Y.Z]
                                      [--notes-file dist/RELEASE_NOTES.md]
                                      [--dry-run]
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Ensure UTF-8 output encoding across Windows and Linux runners
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))
from version import bump_semver, load_version_json, save_version_json, sync_files


def run_git(args: List[str]) -> str:
    """Execute a git command and return stripped stdout."""
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=str(ROOT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def get_latest_tag() -> Optional[str]:
    """Retrieve the most recent git tag matching v*.*.*, if any."""
    output = run_git(["tag", "-l", "v*", "--sort=-v:refname"])
    if output:
        tags = [t.strip() for t in output.splitlines() if t.strip()]
        for tag in tags:
            if re.match(r"^v\d+\.\d+\.\d+", tag):
                return tag
    return None


def get_commits_since_tag(tag: Optional[str]) -> List[Dict[str, str]]:
    """Retrieve commit hash, subject, and body since the given tag (or all if no tag)."""
    git_range = f"{tag}..HEAD" if tag else "HEAD"
    # Format: hash%x1fsubject%x1fbody%x1e
    raw = run_git(["log", git_range, "--format=%H%x1f%s%x1f%b%x1e"])
    if not raw:
        return []

    commits = []
    for entry in raw.split("\x1e"):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split("\x1f")
        commit_hash = parts[0].strip() if len(parts) > 0 else ""
        subject = parts[1].strip() if len(parts) > 1 else ""
        body = parts[2].strip() if len(parts) > 2 else ""
        if subject:
            commits.append({
                "hash": commit_hash[:7],
                "subject": subject,
                "body": body,
            })
    return commits


def analyze_commits_for_bump(commits: List[Dict[str, str]]) -> Tuple[str, Dict[str, List[str]]]:
    """
    Analyzes commit messages according to Conventional Commits:
    - Breaking Change ('!:' or 'BREAKING CHANGE:') -> 'major'
    - Feature ('feat:' or 'feat(...):') -> 'minor'
    - Fix / Perf / Refactor / Docs / Chore -> 'patch'

    Returns (bump_level, categorized_commits).
    """
    categories: Dict[str, List[str]] = {
        "breaking": [],
        "features": [],
        "fixes": [],
        "perf": [],
        "maintenance": [],
        "other": [],
    }

    has_breaking = False
    has_feature = False

    for c in commits:
        sub = c["subject"]
        body = c["body"]
        short_hash = c["hash"]
        entry = f"{sub} (`{short_hash}`)" if short_hash else sub

        # Detect breaking changes
        if "BREAKING CHANGE:" in body or "BREAKING-CHANGE:" in body or re.search(r"^[a-zA-Z]+(\([^\)]+\))?!:", sub):
            has_breaking = True
            categories["breaking"].append(entry)
            continue

        # Feat
        if re.match(r"^feat(\([^\)]+\))?:", sub, re.IGNORECASE):
            has_feature = True
            clean_sub = re.sub(r"^feat(\([^\)]+\))?:\s*", "", sub, flags=re.IGNORECASE)
            categories["features"].append(f"{clean_sub} (`{short_hash}`)")
            continue

        # Fix
        if re.match(r"^fix(\([^\)]+\))?:", sub, re.IGNORECASE):
            clean_sub = re.sub(r"^fix(\([^\)]+\))?:\s*", "", sub, flags=re.IGNORECASE)
            categories["fixes"].append(f"{clean_sub} (`{short_hash}`)")
            continue

        # Perf
        if re.match(r"^perf(\([^\)]+\))?:", sub, re.IGNORECASE):
            clean_sub = re.sub(r"^perf(\([^\)]+\))?:\s*", "", sub, flags=re.IGNORECASE)
            categories["perf"].append(f"{clean_sub} (`{short_hash}`)")
            continue

        # Maintenance / Chores / Tests / CI / Refactor / Docs
        if re.match(r"^(refactor|chore|test|ci|docs|build|style)(\([^\)]+\))?:", sub, re.IGNORECASE):
            clean_sub = re.sub(r"^(refactor|chore|test|ci|docs|build|style)(\([^\)]+\))?:\s*", "", sub, flags=re.IGNORECASE)
            categories["maintenance"].append(f"{clean_sub} (`{short_hash}`)")
            continue

        categories["other"].append(entry)

    if has_breaking:
        bump_level = "major"
    elif has_feature:
        bump_level = "minor"
    else:
        bump_level = "patch"

    return bump_level, categories


def generate_release_notes(
    version: str,
    tag_name: str,
    prev_tag: Optional[str],
    categories: Dict[str, List[str]],
    repo_name: str = "vikukumar/pravah",
) -> str:
    """Format markdown release notes."""
    today = datetime.date.today().isoformat()
    lines = [
        f"## 🚀 PRAVAH Release v{version} ({today})",
        "",
        "Enterprise-grade AI Workflow Automation & Social Media Management Platform.",
        "",
    ]

    # Breaking Changes
    if categories["breaking"]:
        lines.append("### 💥 Breaking Changes")
        for item in categories["breaking"]:
            lines.append(f"- {item}")
        lines.append("")

    # Features
    if categories["features"]:
        lines.append("### 🌟 New Features & Enhancements")
        for item in categories["features"]:
            lines.append(f"- {item}")
        lines.append("")

    # Fixes
    if categories["fixes"]:
        lines.append("### 🐛 Bug Fixes")
        for item in categories["fixes"]:
            lines.append(f"- {item}")
        lines.append("")

    # Performance
    if categories["perf"]:
        lines.append("### ⚡ Performance Improvements")
        for item in categories["perf"]:
            lines.append(f"- {item}")
        lines.append("")

    # Maintenance
    if categories["maintenance"]:
        lines.append("### 🔧 Maintenance & Refactoring")
        for item in categories["maintenance"]:
            lines.append(f"- {item}")
        lines.append("")

    # Fallback if no specific categories populated
    if not any([categories["breaking"], categories["features"], categories["fixes"], categories["perf"], categories["maintenance"]]):
        if categories["other"]:
            lines.append("### 📝 Changes")
            for item in categories["other"]:
                lines.append(f"- {item}")
            lines.append("")
        else:
            lines.append("### 📝 General Maintenance & Security Updates")
            lines.append(f"- Maintenance and performance enhancements for release v{version}.")
            lines.append("")

    # Docker instructions
    lines.extend([
        "---",
        "",
        "### 🐳 Docker Container Images",
        "Official pre-built production container images are available on GitHub Container Registry (GHCR):",
        "",
        "```bash",
        f"# Unified All-in-One Image (FastAPI + Next.js + Scheduler)",
        f"docker pull ghcr.io/{repo_name}:{version}",
        f"docker pull ghcr.io/{repo_name}:latest",
        "",
        f"# Modular Backend API",
        f"docker pull ghcr.io/{repo_name}-api:{version}",
        "",
        f"# Modular Web Frontend",
        f"docker pull ghcr.io/{repo_name}-web:{version}",
        "```",
        "",
        "### 📦 Standalone Release Artifacts",
        f"Download `pravah-v{version}.zip` below for full self-hosted source deployment with dedicated `api/`, `web/`, and `scripts/` directories.",
        "Verify archive integrity with `SHA256SUMS.txt`.",
        "",
    ])

    if prev_tag:
        lines.append(f"**Full Changelog**: https://github.com/{repo_name}/compare/{prev_tag}...{tag_name}")
    else:
        lines.append(f"**Initial Release**: https://github.com/{repo_name}/releases/tag/{tag_name}")

    lines.append("")
    return "\n".join(lines)


def write_github_output(key: str, value: str):
    """Write an output parameter to $GITHUB_OUTPUT if running inside GitHub Actions."""
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output and os.path.exists(gh_output):
        with open(gh_output, "a", encoding="utf-8") as f:
            if "\n" in value:
                delimiter = "EOF_" + os.urandom(8).hex()
                f.write(f"{key}<<{delimiter}\n{value}\n{delimiter}\n")
            else:
                f.write(f"{key}={value}\n")


def main():
    parser = argparse.ArgumentParser(description="PRAVAH Release Versioning & Notes CLI")
    parser.add_argument(
        "--bump-type",
        choices=["auto", "patch", "minor", "major", "custom"],
        default="auto",
        help="SemVer bump type (default: auto detect from commits)",
    )
    parser.add_argument("--custom-version", help="Explicit version string if bump-type is custom")
    parser.add_argument("--notes-file", default="dist/RELEASE_NOTES.md", help="Output path for release notes")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "vikukumar/pravah"), help="GitHub repository name (owner/repo)")
    parser.add_argument("--dry-run", action="store_true", help="Calculate version without modifying files")

    args = parser.parse_args()

    latest_tag = get_latest_tag()
    data = load_version_json()
    current_version = data.get("version", "1.0.0")

    print(f"📌 Latest Git Tag:       {latest_tag or 'None (initial release)'}")
    print(f"📌 Current version.json: v{current_version}")

    commits = get_commits_since_tag(latest_tag)
    print(f"📌 Found {len(commits)} commit(s) since last tag.")

    detected_bump, categories = analyze_commits_for_bump(commits)

    # Determine next version
    if args.bump_type == "custom":
        if not args.custom_version:
            print("❌ Error: --custom-version is required when --bump-type is custom", file=sys.stderr)
            sys.exit(1)
        next_version = args.custom_version.lstrip("v")
        effective_bump = "custom"
    elif args.bump_type == "auto":
        effective_bump = detected_bump
        # If no tag exists yet and version.json is already 1.0.0, keep current 1.0.0 for initial release
        if not latest_tag:
            next_version = current_version
        else:
            next_version = bump_semver(current_version, effective_bump)
    else:
        effective_bump = args.bump_type
        next_version = bump_semver(current_version, effective_bump)

    next_tag = f"v{next_version}"
    print(f"🚀 Next SemVer Bump:     {effective_bump.upper()}")
    print(f"🚀 Calculated Version:   {next_version} (Tag: {next_tag})")

    # Generate Release Notes
    release_notes = generate_release_notes(
        version=next_version,
        tag_name=next_tag,
        prev_tag=latest_tag,
        categories=categories,
        repo_name=args.repo,
    )

    notes_path = Path(args.notes_file)
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    with open(notes_path, "w", encoding="utf-8") as f:
        f.write(release_notes)
    print(f"📝 Release notes written to: {notes_path}")

    if not args.dry_run:
        # Update version.json
        data["version"] = next_version
        data["backend"] = next_version
        data["frontend"] = next_version
        data["shared_types"] = next_version
        save_version_json(data)
        sync_files(data)
        print("✓ All repository version files synchronized successfully.")
    else:
        print("🔍 Dry-run mode: no files modified.")

    # Export outputs for GitHub Actions
    write_github_output("version", next_version)
    write_github_output("tag_name", next_tag)
    write_github_output("previous_tag", latest_tag or "")
    write_github_output("bump_level", effective_bump)
    write_github_output("notes_file", str(notes_path))


if __name__ == "__main__":
    main()
