"""Repo-root resolution so landing paths in YAML stay portable."""

from __future__ import annotations

from pathlib import Path

# Package lives at <repo>/oil_data_ingest/; repo root is one level up.
REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"
DATA_DIR = REPO_ROOT / "data"


def resolve_under_repo(path: str | Path) -> Path:
    """Resolve a config-relative path against the repo root (not CWD)."""
    p = Path(path)
    if p.is_absolute():
        return p
    return REPO_ROOT / p
