# oil_data_ingest

Desk ingest jobs for public / API energy series. Apps (e.g. `sci_api`) should **read** the landing tables, not own the scrape.

First source: **SunSirs** China spot prices — one multi-product parquet from day one.

## Setup

```powershell
cd oil_data_ingest
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## SunSirs

Config: `config/sunsirs.yaml` (product registry + landing paths). Only `gasoline` is `enabled: true` initially; flip flags or pass CLI products to expand.

```powershell
python scripts/fetch_sunsirs.py
python scripts/fetch_sunsirs.py --product gasoline --product diesel
python scripts/fetch_sunsirs.py --all
```

Landing table (all products):

`data/processed/sunsirs/prices.parquet`

| column | meaning |
|--------|---------|
| `date` | observation date |
| `product` | stable key (`gasoline`, `diesel`, …) |
| `product_label` | label from the page |
| `sector` | e.g. Energy |
| `price` | spot print |
| `unit` | default `RMB/mt` (not shown on UK pages) |
| `source` | `sunsirs` |
| `source_product_id` | SunSirs numeric id |
| `source_url` | page scraped |
| `fetched_at` | UTC pull time |

Upsert key: `(source, product, date)` — re-runs update the same day instead of duplicating.

Raw HTML (optional, on by default): `data/raw/sunsirs/{product}/{timestamp}.html`

## Scheduling (later)

Point Windows Task Scheduler or Prefect at `python scripts/fetch_sunsirs.py` once per weekday. No orchestrator required for the first series.

## Sharing later

- **PM / OneDrive:** copy or sync `data/processed/` (or a CSV export) into a shared folder — avoid two writers on the same parquet.
- **Snowflake:** add a thin loader that upserts the same tidy schema; keep this repo as the scrape owner.

## Layout

```
config/sunsirs.yaml          # multi-product registry
oil_data_ingest/sunsirs/     # client, parse, store, pipeline
scripts/fetch_sunsirs.py
data/raw/sunsirs/
data/processed/sunsirs/prices.parquet
```
