"""CLI entrypoints for ingest jobs."""

from __future__ import annotations

import argparse
from pathlib import Path

from oil_data_ingest.sunsirs.pipeline import run_sunsirs_fetch


def main_sunsirs(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch SunSirs spot prices into data/processed/sunsirs/prices.parquet "
            "(multi-product table)."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to sunsirs.yaml (default: config/sunsirs.yaml)",
    )
    parser.add_argument(
        "--product",
        action="append",
        dest="products",
        default=None,
        help="Product key from config (repeatable). Default: enabled products only.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_configured",
        help="Fetch every product listed in config (ignores enabled flags).",
    )
    parser.add_argument(
        "--no-raw",
        action="store_true",
        help="Do not write raw HTML under data/raw/sunsirs/",
    )
    args = parser.parse_args(argv)

    summary = run_sunsirs_fetch(
        config_path=args.config,
        products=args.products,
        all_configured=args.all_configured,
        save_raw=not args.no_raw,
    )
    print(f"wrote {summary['prices_path']}")
    print(f"rows_total={summary['rows_total']} upsert={summary['upsert']}")
    for product, n in summary["products"].items():
        print(f"  {product}: {n} row(s) from page")


if __name__ == "__main__":
    main_sunsirs()
