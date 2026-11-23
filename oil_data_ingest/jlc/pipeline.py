"""Config-driven JLC crack fetch → cracks.parquet."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from oil_data_ingest.jlc.bloomberg import fetch_px_last_hist
from oil_data_ingest.jlc.store import load_cracks, save_cracks, upsert_cracks
from oil_data_ingest.paths import CONFIG_DIR, resolve_under_repo


def load_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or (CONFIG_DIR / "jlc_cracks.yaml")
    with cfg_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_jlc_cracks_fetch(
    *,
    config_path: Path | None = None,
    backfill_days: int | None = None,
    lookback_days: int | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    source = config.get("source", "jlc")
    via = config.get("via", "bloomberg")
    field = config.get("field", "PX_LAST")
    unit = config.get("unit", "USD/bbl")
    landing = config.get("landing") or {}
    cracks_path = resolve_under_repo(
        landing.get("cracks", "data/processed/jlc/cracks.parquet")
    )
    prefer_bpipe = bool((config.get("bloomberg") or {}).get("prefer_bpipe", True))

    registry: dict[str, dict[str, Any]] = config.get("tickers") or {}
    selected = {k: v for k, v in registry.items() if v.get("enabled", True)}
    if not selected:
        raise SystemExit("No JLC tickers enabled in config/jlc_cracks.yaml")

    ticker_to_meta = {
        meta["bloomberg"]: {"product": key, "label": meta.get("label", key)}
        for key, meta in selected.items()
    }
    tickers = list(ticker_to_meta)

    existing = load_cracks(cracks_path)
    end = pd.Timestamp.today().normalize()
    bf = int(backfill_days if backfill_days is not None else config.get("backfill_days", 365))
    lb = int(
        lookback_days
        if lookback_days is not None
        else config.get("refresh_lookback_days", 90)
    )
    if existing.empty:
        start = end - pd.Timedelta(days=bf)
        window = "backfill"
    else:
        start = end - pd.Timedelta(days=lb)
        window = "refresh"

    hist, session = fetch_px_last_hist(
        tickers, start, end, prefer_bpipe=prefer_bpipe
    )
    fetched_at = datetime.now(timezone.utc)

    rows = []
    for _, r in hist.iterrows():
        meta = ticker_to_meta.get(str(r["ticker"]))
        if meta is None:
            continue
        rows.append(
            {
                "date": r["date"],
                "product": meta["product"],
                "ticker": r["ticker"],
                "label": meta["label"],
                "value": float(r["value"]),
                "unit": unit,
                "source": source,
                "via": via,
                "field": field,
                "fetched_at": fetched_at,
                "session": session,
            }
        )
    new = pd.DataFrame(rows)
    combined, stats = upsert_cracks(existing, new)
    save_cracks(combined, cracks_path)

    per_product = (
        new.groupby("product").size().astype(int).to_dict() if not new.empty else {}
    )
    return {
        "cracks_path": str(cracks_path),
        "window": window,
        "start": str(start.date()),
        "end": str(end.date()),
        "session": session,
        "products": per_product,
        "rows_total": len(combined),
        "upsert": stats,
    }
