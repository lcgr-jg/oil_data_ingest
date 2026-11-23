"""Unit tests that do not hit the network."""

from __future__ import annotations

from oil_data_ingest.sunsirs.parse import parse_product_page
from oil_data_ingest.sunsirs.store import upsert_prices
import pandas as pd

_SAMPLE = """
<html><body>
<table>
<tr><td>Commodity</td><td>Sectors</td><td>Price</td><td>Date</td></tr>
<tr><td>Gasoline</td><td>Energy</td><td>8795.14</td><td>2026-11-23</td></tr>
<tr><td>Gasoline</td><td>Energy</td><td>8875.57</td><td>2026-11-22</td></tr>
</table>
</body></html>
"""


def test_parse_product_page():
    df = parse_product_page(
        _SAMPLE,
        product="gasoline",
        source_product_id=437,
        source_url="https://www.sunsirs.com/uk/prodetail-437.html",
        unit="RMB/mt",
    )
    assert len(df) == 2
    assert list(df["product"].unique()) == ["gasoline"]
    assert float(df.loc[df["date"].astype(str) == "2026-11-23", "price"].iloc[0]) == 8795.14


def test_upsert_is_idempotent_and_multi_product():
    g = parse_product_page(
        _SAMPLE,
        product="gasoline",
        source_product_id=437,
        source_url="https://example/g",
        unit="RMB/mt",
    )
    d_html = _SAMPLE.replace("Gasoline", "Diesel").replace("8795.14", "7000.00")
    d = parse_product_page(
        d_html,
        product="diesel",
        source_product_id=490,
        source_url="https://example/d",
        unit="RMB/mt",
    )
    combined, stats = upsert_prices(pd.DataFrame(), pd.concat([g, d], ignore_index=True))
    assert stats["added"] == 4
    assert set(combined["product"]) == {"gasoline", "diesel"}

    again, stats2 = upsert_prices(combined, g)
    assert stats2["added"] == 0
    assert len(again) == 4
