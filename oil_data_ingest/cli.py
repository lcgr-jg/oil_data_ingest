"""CLI entrypoints for ingest jobs."""

from __future__ import annotations

import argparse
from pathlib import Path

from oil_data_ingest.jlc.pipeline import run_jlc_cracks_fetch
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
        "--raw",
        action="store_true",
        help="Also write raw HTML under data/raw/sunsirs/ (debug only; off by default).",
    )
    args = parser.parse_args(argv)

    summary = run_sunsirs_fetch(
        config_path=args.config,
        products=args.products,
        all_configured=args.all_configured,
        save_raw=args.raw,
    )
    print(f"wrote {summary['prices_path']}")
    print(f"rows_total={summary['rows_total']} upsert={summary['upsert']}")
    for product, n in summary["products"].items():
        print(f"  {product}: {n} row(s) from page")


def main_jlc_cracks(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch JLC China indie refinery cracks (Bloomberg) into "
            "data/processed/jlc/cracks.parquet"
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to jlc_cracks.yaml (default: config/jlc_cracks.yaml)",
    )
    parser.add_argument(
        "--backfill-days",
        type=int,
        default=None,
        help="Override first-fill lookback (default from config, usually 365)",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=None,
        help="Override refresh lookback when store already has rows",
    )
    args = parser.parse_args(argv)

    summary = run_jlc_cracks_fetch(
        config_path=args.config,
        backfill_days=args.backfill_days,
        lookback_days=args.lookback_days,
    )
    print(f"wrote {summary['cracks_path']}")
    print(
        f"window={summary['window']} {summary['start']}->{summary['end']} "
        f"session={summary['session']} rows_total={summary['rows_total']} "
        f"upsert={summary['upsert']}"
    )
    for product, n in summary["products"].items():
        print(f"  {product}: {n} row(s) from Bloomberg")


if __name__ == "__main__":
    main_sunsirs()
