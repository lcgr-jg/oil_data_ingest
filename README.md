# oil_data_ingest

Desk ingest jobs for public / API energy series. Apps (e.g. `sci_api`) should **read** the landing tables, not own the scrape.

Sources so far:
- **SunSirs** China spot prices — multi-product parquet
- **JLC** independent-refinery gasoline/diesel cracks via Bloomberg (`CHPZIRGC` / `CHPZIRDC`)

## Setup

```powershell
cd oil_data_ingest
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## SunSirs

Config: `config/sunsirs.yaml` (product registry + landing paths). Enabled by default: `gasoline`, `diesel`, `fuel_oil`, `lpg`. Flip flags or pass CLI products to expand.

```powershell
python scripts/fetch_sunsirs.py
python scripts/fetch_sunsirs.py --product gasoline --product diesel
python scripts/fetch_sunsirs.py --all
python scripts/fetch_sunsirs.py --raw   # optional: keep HTML under data/raw/ (debug)
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

Raw HTML (off by default; `--raw` only): `data/raw/sunsirs/{product}/{timestamp}.html`

## JLC indie cracks (Bloomberg)

Config: `config/jlc_cracks.yaml`. Uses `desk_core.bloomberg` — **B-PIPE first**, falls back to desktop Terminal.

```powershell
python scripts/fetch_jlc_cracks.py
python scripts/fetch_jlc_cracks.py --backfill-days 365
```

Landing table: `data/processed/jlc/cracks.parquet`  
Upsert key: `(source, ticker, date)`. Empty store → 365d backfill; later runs → 90d refresh.

Requires sibling `desk_core` on `PYTHONPATH` or `pip install -e ../desk_core` (and Bloomberg entitlement).

## Scheduling

Morning runner (SunSirs + JLC):

```text
scripts\run_morning.bat
```

**Windows Task Scheduler** (example **09:20** weekdays, before `desk_reports` @ 09:30):

| Field | Value |
|-------|--------|
| Program/script | `...\oil_data_ingest\scripts\run_morning.bat` |
| Start in | `...\oil_data_ingest` |
| Trigger | Weekly — Mon–Fri |

```powershell
$bat = (Resolve-Path .\scripts\run_morning.bat).Path
schtasks /Create /F /TN "oil_data_ingest\morning_weekdays" `
  /TR "`"$bat`"" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 09:20 `
  /RL LIMITED
```

Prefer pointing your existing 09:20 task at `run_morning.bat` so cracks refresh with spots.

## Sharing later

- **PM / OneDrive:** copy or sync `data/processed/` (or a CSV export) into a shared folder — avoid two writers on the same parquet.
- **Snowflake:** add a thin loader that upserts the same tidy schema; keep this repo as the scrape owner.

## Layout

```
config/sunsirs.yaml
config/jlc_cracks.yaml
oil_data_ingest/sunsirs/
oil_data_ingest/jlc/
scripts/fetch_sunsirs.py
scripts/fetch_jlc_cracks.py
scripts/run_morning.bat
data/processed/sunsirs/prices.parquet
data/processed/jlc/cracks.parquet
```
