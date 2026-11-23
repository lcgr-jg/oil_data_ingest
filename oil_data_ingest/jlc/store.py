"""Append-only JLC crack store (single parquet)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

CRACK_COLUMNS = [
    "date",
    "product",
    "ticker",
    "label",
    "value",
    "unit",
    "source",
    "via",
    "field",
    "fetched_at",
    "session",
]

_KEY = ["source", "ticker", "date"]


def load_cracks(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=CRACK_COLUMNS)
    df = pd.read_parquet(path)
    for col in CRACK_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    return df[CRACK_COLUMNS]


def upsert_cracks(existing: pd.DataFrame, new: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Newer fetches win on (source, ticker, date)."""
    if new.empty:
        return existing.copy(), {"added": 0, "updated": 0, "unchanged": 0}

    new = new[CRACK_COLUMNS].copy()
    if existing.empty:
        combined = new.sort_values(["product", "date"]).reset_index(drop=True)
        return combined, {"added": len(new), "updated": 0, "unchanged": 0}

    existing = existing[CRACK_COLUMNS].copy()
    for frame in (existing, new):
        frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()

    before_keys = set(map(tuple, existing[_KEY].itertuples(index=False, name=None)))
    new_keys = set(map(tuple, new[_KEY].itertuples(index=False, name=None)))
    overlap = before_keys & new_keys

    combined = pd.concat([existing, new], ignore_index=True)
    combined = combined.drop_duplicates(subset=_KEY, keep="last")
    combined = combined.sort_values(["product", "date"]).reset_index(drop=True)

    after_keys = set(map(tuple, combined[_KEY].itertuples(index=False, name=None)))
    added = len(after_keys - before_keys)
    updated = len(overlap)
    unchanged = max(0, len(new_keys) - added - updated)
    return combined, {"added": added, "updated": updated, "unchanged": unchanged}


def save_cracks(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df[CRACK_COLUMNS].copy()
    out["date"] = pd.to_datetime(out["date"])
    out.to_parquet(path, index=False)
    return path
