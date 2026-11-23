"""Parse SunSirs UK product-detail HTML into tidy price rows."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
from bs4 import BeautifulSoup

# Stable landing schema — one row per product × observation date.
PRICE_COLUMNS = [
    "date",
    "product",
    "product_label",
    "sector",
    "price",
    "unit",
    "source",
    "source_product_id",
    "source_url",
    "fetched_at",
]


def parse_product_page(
    html: str,
    *,
    product: str,
    source_product_id: int | str,
    source_url: str,
    unit: str,
    source: str = "sunsirs",
    fetched_at: datetime | None = None,
) -> pd.DataFrame:
    """
    Extract the spot table (Commodity / Sectors / Price / Date).

    Pages typically expose ~6 recent daily prints; we keep all of them so the
    first run backfills a short history and later runs refresh overlapping dates.
    """
    soup = BeautifulSoup(html, "lxml")
    fetched_at = fetched_at or datetime.now(timezone.utc)

    table = _find_price_table(soup)
    if table is None:
        raise ValueError(f"No price table found on {source_url}")

    rows: list[dict] = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) != 4:
            continue
        commodity, sector, price_raw, date_raw = cells
        # Skip header row.
        if commodity.lower() == "commodity" or date_raw.lower() == "date":
            continue
        try:
            price = float(price_raw.replace(",", ""))
        except ValueError as exc:
            raise ValueError(f"Bad price {price_raw!r} on {source_url}") from exc
        date = pd.to_datetime(date_raw, format="%Y-%m-%d", errors="raise").date()
        rows.append(
            {
                "date": date,
                "product": product,
                "product_label": commodity,
                "sector": sector,
                "price": price,
                "unit": unit,
                "source": source,
                "source_product_id": str(source_product_id),
                "source_url": source_url,
                "fetched_at": fetched_at,
            }
        )

    if not rows:
        raise ValueError(f"Price table empty on {source_url}")

    out = pd.DataFrame(rows, columns=PRICE_COLUMNS)
    # One print per calendar date per product (page should already be unique).
    return out.drop_duplicates(subset=["product", "date"], keep="first")


def _find_price_table(soup: BeautifulSoup):
    for table in soup.find_all("table"):
        header = table.find("tr")
        if header is None:
            continue
        labels = [td.get_text(strip=True).lower() for td in header.find_all("td")]
        if labels == ["commodity", "sectors", "price", "date"]:
            return table
    return None
