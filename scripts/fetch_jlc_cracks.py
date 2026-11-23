"""CLI wrapper: python scripts/fetch_jlc_cracks.py"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from oil_data_ingest.cli import main_jlc_cracks

if __name__ == "__main__":
    main_jlc_cracks()
