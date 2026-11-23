"""Bloomberg BDH for JLC crack indices — B-PIPE first, Terminal fallback."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def _ensure_desk_core_on_path() -> None:
    """Allow editable sibling desk_core when not installed into the active venv."""
    import sys
    from pathlib import Path

    # parents: jlc → package → repo → Coding
    coding = Path(__file__).resolve().parents[3]
    desk = coding / "desk_core"
    if desk.is_dir() and str(desk) not in sys.path:
        sys.path.insert(0, str(desk))


def _reset_bbg_session() -> None:
    from desk_core.bloomberg.session import BloombergSession

    inst = BloombergSession._instance
    if inst is not None:
        try:
            inst.close()
        except Exception:
            BloombergSession._instance = None


def fetch_px_last_hist(
    tickers: list[str],
    start: str | pd.Timestamp,
    end: str | pd.Timestamp,
    *,
    prefer_bpipe: bool = True,
) -> tuple[pd.DataFrame, str]:
    """
    BDH PX_LAST for tickers.

    Returns (long frame with ticker/date/value, session label 'bpipe'|'terminal').
    """
    _ensure_desk_core_on_path()
    from desk_core.bloomberg import refdata

    start_s = pd.Timestamp(start).strftime("%Y-%m-%d")
    end_s = pd.Timestamp(end).strftime("%Y-%m-%d")
    modes: list[tuple[bool, str]] = (
        [(True, "bpipe"), (False, "terminal")]
        if prefer_bpipe
        else [(False, "terminal"), (True, "bpipe")]
    )

    last_err: Exception | None = None
    for on_server, label in modes:
        try:
            _reset_bbg_session()
            logger.info(
                "Bloomberg hist %s -> %s via %s (%s tickers)",
                start_s,
                end_s,
                label,
                len(tickers),
            )
            raw = refdata.hist(
                tickers,
                "PX_LAST",
                start_s,
                end_s,
                periodicity="DAILY",
                on_server=on_server,
            )
            if raw is None or raw.empty:
                raise RuntimeError(f"Empty BDH response via {label}")
            out = _normalize(raw)
            if out.empty:
                raise RuntimeError(f"No PX_LAST rows via {label}")
            return out, label
        except Exception as exc:
            last_err = exc
            logger.warning("Bloomberg %s failed: %s", label, exc)
            _reset_bbg_session()

    raise RuntimeError(f"Bloomberg hist failed on B-PIPE and Terminal: {last_err}")


def _normalize(raw: pd.DataFrame) -> pd.DataFrame:
    """desk_core hist is long: ticker, field, date, value."""
    df = raw.copy()
    if "field" in df.columns:
        df = df[df["field"].astype(str).str.upper() == "PX_LAST"]
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date", "value"])
    return df[["ticker", "date", "value"]].reset_index(drop=True)
