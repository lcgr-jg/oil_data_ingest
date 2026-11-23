"""Config-driven SunSirs fetch → multi-product prices.parquet."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from oil_data_ingest.paths import CONFIG_DIR, resolve_under_repo
from oil_data_ingest.sunsirs.client import SunsirsClient
from oil_data_ingest.sunsirs.parse import parse_product_page
from oil_data_ingest.sunsirs.store import load_prices, save_prices, upsert_prices


def load_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or (CONFIG_DIR / "sunsirs.yaml")
    with cfg_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def select_products(
    config: dict[str, Any],
    *,
    products: list[str] | None = None,
    all_configured: bool = False,
) -> dict[str, dict[str, Any]]:
    """
    Resolve which product keys to fetch.

    Default: enabled=true in YAML. --product overrides. --all ignores enabled.
    """
    registry: dict[str, dict[str, Any]] = config.get("products") or {}
    if products:
        missing = [p for p in products if p not in registry]
        if missing:
            known = ", ".join(sorted(registry))
            raise KeyError(f"Unknown product(s) {missing}; known: {known}")
        return {p: registry[p] for p in products}
    if all_configured:
        return dict(registry)
    return {k: v for k, v in registry.items() if v.get("enabled", False)}


def run_sunsirs_fetch(
    *,
    config_path: Path | None = None,
    products: list[str] | None = None,
    all_configured: bool = False,
    save_raw: bool = True,
) -> dict[str, Any]:
    """
    Fetch selected SunSirs product pages and upsert into one prices table.

    Returns a small summary dict for the CLI (paths, per-product row counts).
    """
    config = load_config(config_path)
    source = config.get("source", "sunsirs")
    unit_default = config.get("unit_default", "RMB/mt")
    landing = config.get("landing") or {}
    prices_path = resolve_under_repo(landing.get("prices", "data/processed/sunsirs/prices.parquet"))
    raw_dir = resolve_under_repo(landing.get("raw_dir", "data/raw/sunsirs"))

    selected = select_products(
        config, products=products, all_configured=all_configured
    )
    if not selected:
        raise SystemExit(
            "No products selected — enable entries in config/sunsirs.yaml "
            "or pass --product / --all"
        )

    client = SunsirsClient()
    fetched_at = datetime.now(timezone.utc)
    frames: list[pd.DataFrame] = []
    per_product: dict[str, int] = {}

    for key, meta in selected.items():
        url = meta["url"]
        html = client.get_html(url)
        if save_raw:
            # Keep raw HTML so we can re-parse if the tidy schema evolves.
            stamp = fetched_at.strftime("%Y%m%dT%H%M%SZ")
            out_raw = raw_dir / key / f"{stamp}.html"
            out_raw.parent.mkdir(parents=True, exist_ok=True)
            out_raw.write_text(html, encoding="utf-8")

        frame = parse_product_page(
            html,
            product=key,
            source_product_id=meta["id"],
            source_url=url,
            unit=meta.get("unit", unit_default),
            source=source,
            fetched_at=fetched_at,
        )
        per_product[key] = len(frame)
        frames.append(frame)

    new = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    existing = load_prices(prices_path)
    combined, stats = upsert_prices(existing, new)
    save_prices(combined, prices_path)

    return {
        "prices_path": str(prices_path),
        "products": per_product,
        "rows_total": len(combined),
        "upsert": stats,
    }
