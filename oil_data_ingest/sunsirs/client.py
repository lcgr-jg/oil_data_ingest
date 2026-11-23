"""HTTP client for SunSirs UK product pages.

The site serves a short HW_CHECK cookie challenge before the real HTML.
We complete that in-process so the job stays dependency-light (no browser).
"""

from __future__ import annotations

import re
import time
from typing import Final

import requests

_USER_AGENT: Final = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
_TOKEN_RE = re.compile(r'var _0x2\s*=\s*"([^"]+)"')


class SunsirsClient:
    def __init__(self, *, timeout: float = 30.0, pause_s: float = 0.4) -> None:
        self.timeout = timeout
        # Brief pause mirrors the page's setTimeout before reload.
        self.pause_s = pause_s
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": _USER_AGENT})

    def get_html(self, url: str) -> str:
        first = self.session.get(url, timeout=self.timeout)
        first.raise_for_status()
        token = _TOKEN_RE.search(first.text)
        if token is None:
            # Already past the gate (cookie still valid) or page shape changed.
            return first.text

        self.session.cookies.set(
            "HW_CHECK",
            token.group(1),
            domain="www.sunsirs.com",
            path="/",
        )
        if self.pause_s > 0:
            time.sleep(self.pause_s)
        second = self.session.get(url, timeout=self.timeout)
        second.raise_for_status()
        return second.text
