"""
Fetch SunSirs prices (multi-product landing table).

Usage
-----
  python scripts/fetch_sunsirs.py
  python scripts/fetch_sunsirs.py --product gasoline
  python scripts/fetch_sunsirs.py --product gasoline --product diesel
  python scripts/fetch_sunsirs.py --all
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from oil_data_ingest.cli import main_sunsirs  # noqa: E402

if __name__ == "__main__":
    main_sunsirs()
