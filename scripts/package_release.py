#!/usr/bin/env python3
"""
PRAVAH — Secure Standalone Release Artifact Packager
Bundles the platform into a production-ready ZIP archive with distinct `api/`, `web/`,
`shared-types/`, and `scripts/` directories, alongside root startup runners.

Enforces strict security checks:
- Excludes sensitive credentials, local `.env` files, sqlite databases, bytecode, and caches.
- Computes SHA256 hashes for cryptographic integrity.

Usage:
    python scripts/package_release.py [--version X.Y.Z] [--output-dir dist]
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List, Set

# Ensure UTF-8 output encoding across Windows and Linux runners
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent

# Files & patterns that MUST NEVER be packaged in release artifacts
FORBIDDEN_PATTERNS = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "pravah.db",
    "pravah.db-journal",
    "pravah.db-wal",
    "pravah.db-shm",
    ".DS_Store",
    "Thumbs.db",
}

FORBIDDEN_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".key",
    ".pem",
}

FORBIDDEN_DIRS = {
    ".git",
    ".github",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".next",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage",
    "htmlcov",
    "dist",
    "build",
    ".turbo",
    ".vscode",
    ".idea",
    "uploads",
}


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hexadecimal digest of a file."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def copy_directory_secure(src: Path, dst: Path):
    """Recursively copy directory while strictly enforcing security exclusion filters."""
    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        name = item.name

        # Check directory exclusions
        if item.is_dir():
            if name in FORBIDDEN_DIRS or name.startswith("."):
                continue
            copy_directory_secure(item, dst / name)
            continue

        # Check file exclusions
        if name in FORBIDDEN_PATTERNS:
            continue
        if item.suffix in FORBIDDEN_EXTENSIONS:
            continue
        if name.startswith(".env") and name != ".env.example":
            continue

        shutil.copy2(item, dst / name)


def copy_file_secure(src: Path, dst: Path):
    """Safely copy a single file if it passes security criteria."""
    if not src.exists():
        return
    name = src.name
    if name in FORBIDDEN_PATTERNS or src.suffix in FORBIDDEN_EXTENSIONS:
        raise ValueError(f"Security Alert: Attempted to package forbidden file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def audit_staged_files(staged_root: Path):
    """Audit all files staged for packaging to guarantee zero leakage."""
    violations: List[str] = []
    total_files = 0

    for root, dirs, files in os.walk(staged_root):
        rel_root = Path(root).relative_to(staged_root)

        # Check forbidden directories
        for d in dirs:
            if d in FORBIDDEN_DIRS:
                violations.append(f"Forbidden directory staged: {rel_root / d}")

        for f in files:
            total_files += 1
            rel_file = rel_root / f
            ext = Path(f).suffix.lower()

            if f in FORBIDDEN_PATTERNS:
                violations.append(f"Forbidden file staged: {rel_file}")
            elif ext in FORBIDDEN_EXTENSIONS:
                violations.append(f"Forbidden extension staged ({ext}): {rel_file}")
            elif f.startswith(".env") and f != ".env.example":
                violations.append(f"Potential secret file staged: {rel_file}")

    if violations:
        print("❌ SECURITY AUDIT FAILED! The following forbidden files were detected in staged artifact:", file=sys.stderr)
        for v in violations:
            print(f"   - {v}", file=sys.stderr)
        raise RuntimeError("Release artifact packaging aborted due to security violation.")

    print(f"🔒 Security Audit Passed: {total_files} files verified clean. Zero sensitive files detected.")


def write_github_output(key: str, value: str):
    """Write an output parameter to $GITHUB_OUTPUT if running inside GitHub Actions."""
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output and os.path.exists(gh_output):
        with open(gh_output, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


def package_release(version: str, output_dir: Path) -> Path:
    """Create the distribution ZIP artifact containing separate web, api, and scripts folders."""
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_name = f"pravah-v{version}.zip"
    zip_output_path = output_dir / archive_name
    root_folder_name = f"pravah-v{version}"

    with tempfile.TemporaryDirectory(prefix="pravah_dist_") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        staged = tmp_dir / root_folder_name
        staged.mkdir(parents=True, exist_ok=True)

        print(f"📦 Staging PRAVAH v{version} components...")

        # 1. API Backend (apps/api -> api/)
        print("   -> Staging Backend API (api/)...")
        copy_directory_secure(ROOT_DIR / "apps" / "api", staged / "api")

        # 2. Web Frontend (apps/web -> web/)
        print("   -> Staging Frontend Web (web/)...")
        copy_directory_secure(ROOT_DIR / "apps" / "web", staged / "web")

        # 3. Shared Types (packages/shared-types -> shared-types/)
        if (ROOT_DIR / "packages" / "shared-types").exists():
            print("   -> Staging Shared Contracts (shared-types/)...")
            copy_directory_secure(ROOT_DIR / "packages" / "shared-types", staged / "shared-types")

        # 4. Scripts (scripts/ -> scripts/)
        print("   -> Staging Scripts (scripts/)...")
        copy_directory_secure(ROOT_DIR / "scripts", staged / "scripts")

        # 5. Infrastructure (infrastructure/ -> infrastructure/)
        if (ROOT_DIR / "infrastructure").exists():
            print("   -> Staging Infrastructure (infrastructure/)...")
            copy_directory_secure(ROOT_DIR / "infrastructure", staged / "infrastructure")

        # 6. Deploy & Helm Charts (deploy/ -> deploy/)
        if (ROOT_DIR / "deploy").exists():
            print("   -> Staging Helm & Kubernetes Manifests (deploy/)...")
            copy_directory_secure(ROOT_DIR / "deploy", staged / "deploy")

        # 7. Root Startup & Container Files
        print("   -> Staging Startup & Deployment Run scripts...")
        root_files_to_copy = [
            "start.sh",
            "start.ps1",
            "docker-run.sh",
            "docker-run.ps1",
            "docker-compose.yml",
            "docker-compose.app.yml",
            "docker-compose.prod.yml",
            "Dockerfile",
            ".env.example",
            "version.json",
            "README.md",
            "SECURITY.md",
            "ARCHITECTURE.md",
            "DEPLOYMENT.md",
        ]

        for rf in root_files_to_copy:
            copy_file_secure(ROOT_DIR / rf, staged / rf)

        # Ensure .env.example also copied to api/ and web/ for self-contained setup
        if (ROOT_DIR / ".env.example").exists():
            copy_file_secure(ROOT_DIR / ".env.example", staged / "api" / ".env.example")

        # Audit staged files
        audit_staged_files(staged)

        # Compress into ZIP
        print(f"📦 Compressing into {zip_output_path}...")
        if zip_output_path.exists():
            zip_output_path.unlink()

        with zipfile.ZipFile(zip_output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            for root, dirs, files in os.walk(staged):
                for file in files:
                    file_path = Path(root) / file
                    archive_arcname = file_path.relative_to(tmp_dir)
                    zipf.write(file_path, arcname=str(archive_arcname).replace("\\", "/"))

    # Compute SHA256 checksum
    zip_sha256 = compute_sha256(zip_output_path)
    sha_file = output_dir / f"{archive_name}.sha256"
    sums_file = output_dir / "SHA256SUMS.txt"

    with open(sha_file, "w", encoding="utf-8") as f:
        f.write(f"{zip_sha256}  {archive_name}\n")

    with open(sums_file, "w", encoding="utf-8") as f:
        f.write(f"{zip_sha256}  {archive_name}\n")

    size_mb = zip_output_path.stat().st_size / (1024 * 1024)
    print("\n========================================================")
    print("      🎉 Standalone Release Package Created Successfully!")
    print("========================================================")
    print(f"  Archive:       {zip_output_path}")
    print(f"  Size:          {size_mb:.2f} MB")
    print(f"  SHA256:        {zip_sha256}")
    print(f"  Checksum File: {sums_file}")
    print("========================================================\n")

    # Set GitHub Actions output
    write_github_output("zip_path", str(zip_output_path))
    write_github_output("zip_name", archive_name)
    write_github_output("zip_sha256", zip_sha256)
    write_github_output("sums_path", str(sums_file))

    return zip_output_path


def main():
    parser = argparse.ArgumentParser(description="PRAVAH Secure Standalone Packager")
    parser.add_argument("--version", help="Release version (e.g. 1.0.0). If omitted, read from version.json")
    parser.add_argument("--output-dir", default="dist", help="Target output directory (default: dist)")

    args = parser.parse_args()

    if args.version:
        version = args.version.lstrip("v")
    else:
        version_json_path = ROOT_DIR / "version.json"
        if version_json_path.exists():
            with open(version_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                version = data.get("version", "1.0.0")
        else:
            version = "1.0.0"

    output_dir = ROOT_DIR / args.output_dir
    package_release(version, output_dir)


if __name__ == "__main__":
    main()
