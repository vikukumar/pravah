#!/usr/bin/env python3
"""
PRAVAH — Helm Chart Packager & Repository Index Generator
Packages the Helm chart at `deploy/helm/pravah` into `dist/pravah-<version>.tgz`
and generates or merges `index.yaml` for GitHub-hosted Helm repositories.

Works on all operating systems without requiring the Helm binary.
Usage:
    python scripts/package_helm.py [--version X.Y.Z] [--output-dir dist] [--repo-url https://raw.githubusercontent.com/<owner>/<repo>/gh-pages/]
"""

import argparse
import datetime
import hashlib
import json
import os
import shutil
import sys
import tarfile
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    print("Warning: PyYAML not found, using basic YAML formatting fallback.")
    yaml = None

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CHART_DIR = ROOT_DIR / "deploy" / "helm" / "pravah"


def compute_sha256(filepath: Path) -> str:
    """Compute cryptographic SHA256 hex digest of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def read_chart_yaml(chart_path: Path) -> Dict[str, Any]:
    """Parse Chart.yaml from chart directory."""
    chart_file = chart_path / "Chart.yaml"
    if not chart_file.exists():
        raise FileNotFoundError(f"Chart.yaml not found at {chart_file}")

    if yaml:
        with open(chart_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    else:
        # Simple manual parser fallback
        data: Dict[str, Any] = {}
        with open(chart_file, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line and not line.startswith(" ") and not line.startswith("#"):
                    k, v = line.split(":", 1)
                    data[k.strip()] = v.strip().strip('"').strip("'")
        return data


def update_chart_yaml_version(chart_path: Path, version: str):
    """Update version and appVersion in Chart.yaml."""
    chart_file = chart_path / "Chart.yaml"
    with open(chart_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith("version:"):
            new_lines.append(f"version: {version}\n")
        elif line.startswith("appVersion:"):
            new_lines.append(f'appVersion: "{version}"\n')
        else:
            new_lines.append(line)

    with open(chart_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def package_chart(chart_dir: Path, output_dir: Path, version: str) -> Path:
    """Package the Helm chart directory into a .tgz archive matching Helm CLI output."""
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_name = f"pravah-{version}.tgz"
    archive_path = output_dir / archive_name

    # Helm archives must have top-level directory named 'pravah'
    with tarfile.open(archive_path, "w:gz") as tar:
        for item in sorted(chart_dir.rglob("*")):
            # Ignore git, cache, or temporary files
            if any(part.startswith(".") and part != ".helmignore" for part in item.parts):
                continue
            if "__pycache__" in item.parts:
                continue

            rel_path = item.relative_to(chart_dir)
            arcname = Path("pravah") / rel_path
            tar.add(item, arcname=str(arcname).replace("\\", "/"))

    return archive_path


def generate_or_update_index(
    output_dir: Path,
    chart_metadata: Dict[str, Any],
    version: str,
    digest: str,
    repo_url: Optional[str] = None,
    archive_name: Optional[str] = None,
) -> Path:
    """Generate or merge index.yaml conforming to Helm repository specification."""
    index_file = output_dir / "index.yaml"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    chart_name = chart_metadata.get("name", "pravah")
    archive_filename = archive_name or f"{chart_name}-{version}.tgz"

    # URL list for the chart
    if repo_url:
        clean_repo_url = repo_url.rstrip("/")
        urls = [f"{clean_repo_url}/{archive_filename}"]
    else:
        urls = [archive_filename]

    entry = {
        "apiVersion": chart_metadata.get("apiVersion", "v2"),
        "appVersion": str(chart_metadata.get("appVersion", version)),
        "created": now_iso,
        "description": chart_metadata.get("description", "PRAVAH Helm Chart"),
        "digest": digest,
        "name": chart_name,
        "urls": urls,
        "version": version,
    }

    # Copy standard fields if present
    for key in ["home", "sources", "keywords", "maintainers", "icon", "annotations", "type"]:
        if key in chart_metadata:
            entry[key] = chart_metadata[key]

    existing_index: Dict[str, Any] = {}
    if index_file.exists() and yaml:
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                existing_index = yaml.safe_load(f) or {}
        except Exception:
            existing_index = {}

    entries = existing_index.get("entries", {})
    if chart_name not in entries:
        entries[chart_name] = []

    # Replace existing version entry or prepend new entry
    new_entries = [e for e in entries[chart_name] if e.get("version") != version]
    new_entries.insert(0, entry)
    entries[chart_name] = new_entries

    index_data = {
        "apiVersion": "v1",
        "entries": entries,
        "generated": now_iso,
    }

    if yaml:
        with open(index_file, "w", encoding="utf-8") as f:
            yaml.dump(index_data, f, default_flow_style=False, sort_keys=False)
    else:
        # Fallback dump
        with open(index_file, "w", encoding="utf-8") as f:
            f.write("apiVersion: v1\n")
            f.write(f"generated: \"{now_iso}\"\n")
            f.write("entries:\n")
            f.write(f"  {chart_name}:\n")
            f.write(f"  - apiVersion: {entry['apiVersion']}\n")
            f.write(f"    appVersion: \"{entry['appVersion']}\"\n")
            f.write(f"    created: \"{entry['created']}\"\n")
            f.write(f"    description: \"{entry['description']}\"\n")
            f.write(f"    digest: {entry['digest']}\n")
            f.write(f"    name: {chart_name}\n")
            f.write("    urls:\n")
            for u in entry['urls']:
                f.write(f"    - {u}\n")
            f.write(f"    version: {version}\n")

    return index_file


def main():
    parser = argparse.ArgumentParser(description="PRAVAH Helm Chart Packager")
    parser.add_argument("--version", help="Release version (e.g. 1.0.1)")
    parser.add_argument("--chart-dir", default=str(DEFAULT_CHART_DIR), help="Path to Helm chart directory")
    parser.add_argument("--output-dir", default="dist", help="Output directory for .tgz and index.yaml")
    parser.add_argument("--repo-url", help="Base URL prefix for URLs in index.yaml (e.g. raw GitHub or Pages URL)")

    args = parser.parse_args()

    chart_dir = Path(args.chart_dir)
    output_dir = ROOT_DIR / args.output_dir

    if args.version:
        version = args.version.lstrip("v")
    else:
        version_json_path = ROOT_DIR / "version.json"
        if version_json_path.exists():
            with open(version_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                version = data.get("version", "1.0.1")
        else:
            version = "1.0.1"

    print(f"📦 Packaging Helm Chart '{chart_dir.name}' v{version}...")
    update_chart_yaml_version(chart_dir, version)
    chart_meta = read_chart_yaml(chart_dir)

    tgz_path = package_chart(chart_dir, output_dir, version)
    digest = compute_sha256(tgz_path)

    # Update SHA256SUMS.txt in output directory
    sums_file = output_dir / "SHA256SUMS.txt"
    with open(sums_file, "a", encoding="utf-8") as f:
        f.write(f"{digest}  {tgz_path.name}\n")

    index_path = generate_or_update_index(
        output_dir=output_dir,
        chart_metadata=chart_meta,
        version=version,
        digest=digest,
        repo_url=args.repo_url,
        archive_name=tgz_path.name,
    )

    size_kb = tgz_path.stat().st_size / 1024
    print(f"✅ Chart Archive Created: {tgz_path} ({size_kb:.1f} KB)")
    print(f"   SHA256:               {digest}")
    print(f"✅ Helm Index Generated: {index_path}")


if __name__ == "__main__":
    main()
