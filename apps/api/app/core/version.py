import json
import os
from pathlib import Path
from typing import Any, Dict

def get_version_info() -> Dict[str, Any]:
    """Returns backend and system version information."""
    version = "1.0.0"
    api_version = "v1"
    schema_version = "c61b97841082"
    codename = "StreamFlow"

    # Check root version.json if available
    try:
        root_version_file = Path(__file__).resolve().parent.parent.parent.parent / "version.json"
        if root_version_file.exists():
            with open(root_version_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "backend_version": data.get("backend", version),
                    "frontend_version": data.get("frontend", version),
                    "shared_types_version": data.get("shared_types", version),
                    "api_version": data.get("api_version", api_version),
                    "schema_version": data.get("schema_version", schema_version),
                    "codename": data.get("codename", codename),
                    "min_compatible_frontend": data.get("min_compatible_frontend", "1.0.0"),
                    "environment": os.getenv("ENVIRONMENT", "development"),
                    "status": "healthy",
                }
    except Exception:
        pass

    return {
        "backend_version": version,
        "api_version": api_version,
        "schema_version": schema_version,
        "codename": codename,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "status": "healthy",
    }
