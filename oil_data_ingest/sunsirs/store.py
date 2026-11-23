"""Append-only multi-product price store (single parquet file)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from oil_data_ingest.sunsirs.parse import PRICE_COLUMNS

# Natural key for idempotent daily upserts across products.
_KEY = ["source", "product", "date"]


def load_prices(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=PRICE_COLUMNS)
    df = pd.read_parquet(path)
    for col in PRICE_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    return df[PRICE_COLUMNS]


def upsert_prices(existing: pd.DataFrame, new: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Merge new rows into the multi-product series.

    Newer fetches win on the natural key so a same-day revision updates price
    without duplicating the date.
    """
    if new.empty:
        return existing.copy(), {"added": 0, "updated": 0, "unchanged": 0}

    new = new[PRICE_COLUMNS].copy()
    if existing.empty:
        combined = new.sort_values(["product", "date"]).reset_index(drop=True)
        return combined, {"added": len(new), "updated": 0, "unchanged": 0}

    existing = existing[PRICE_COLUMNS].copy()
    # Normalize date dtype before key merge (parquet may round-trip as datetime64).
    for frame in (existing, new):
        frame["date"] = pd.to_datetime(frame["date"]).dt.date
        frame["source_product_id"] = frame["source_product_id"].astype(str)

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


def save_prices(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df[PRICE_COLUMNS].copy()
    out["date"] = pd.to_datetime(out["date"])
    out.to_parquet(path, index=False)
    return path
