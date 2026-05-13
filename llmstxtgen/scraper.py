"""HTTP fetcher with optional ScraperAPI fallback.

Aligned with the skillmind convention so the same env vars work across tools:

- ``SCRAPER_Vendor=scraperapi``  activates the fallback
- ``VPN_PROXY_API_KEY=<key>``    holds the credential

If the direct request fails with a block-pattern status (403/429/5xx/…) or a
network error, the request is retried through ScraperAPI in two flavours:

1. **Direct URL API**  — ``http://api.scraperapi.com/?api_key=KEY&url=ENC``
   Used inside :func:`fetch`.

2. **Proxy URL**       — ``http://scraperapi:KEY@proxy-server.scraperapi.com:8001``
   Exposed via :pyattr:`ScraperConfig.proxy_url` for callers like ``yt-dlp``
   or any tool that wants ``HTTP(S)_PROXY``-style usage.

Useful for affiliate links / Cloudflare walls / geo-blocked sitemaps.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from urllib.parse import quote_plus

import requests

from .fetcher import UA

SCRAPERAPI_DIRECT = "http://api.scraperapi.com/?api_key={key}&url={url}"
SCRAPERAPI_PROXY = "http://scraperapi:{key}@proxy-server.scraperapi.com:8001"

BLOCK_STATUSES = {
    401, 403, 405, 406, 408, 409, 425, 429,
    500, 502, 503, 504, 520, 521, 522, 523, 524,
}

# Concurrency hints per ScraperAPI plan (docs.scraperapi.com → Plans). Kept
# conservative so we don't burn through the user's quota in a single sitemap.
SCRAPER_DEFAULT_CONCURRENCY = 20
DIRECT_DEFAULT_CONCURRENCY = 16
RATE_LIMIT_BACKOFF_SEC = 1.0


@dataclass
class ScraperConfig:
    """Scraper credentials + provider switch.

    Use :meth:`from_env` to pick up the skillmind-style env vars, or pass
    ``api_key=`` / ``vendor=`` explicitly (e.g. from a CLI flag).
    """

    api_key: str | None = None
    vendor: str = "scraperapi"

    @classmethod
    def from_env(cls) -> "ScraperConfig":
        vendor = os.environ.get("SCRAPER_Vendor", "").lower()
        api_key = os.environ.get("VPN_PROXY_API_KEY") or ""
        if vendor == "scraperapi" and api_key:
            return cls(api_key=api_key, vendor="scraperapi")
        return cls(api_key=None)

    @property
    def enabled(self) -> bool:
        return bool(self.api_key) and self.vendor == "scraperapi"

    @property
    def proxy_url(self) -> str | None:
        """``HTTP(S)_PROXY``-compatible proxy URL (or ``None`` if disabled)."""
        if not self.enabled:
            return None
        return SCRAPERAPI_PROXY.format(key=self.api_key)

    def direct_url(self, target: str) -> str:
        if not self.enabled:
            raise RuntimeError("ScraperConfig not enabled — set SCRAPER_Vendor=scraperapi + VPN_PROXY_API_KEY")
        return SCRAPERAPI_DIRECT.format(key=self.api_key, url=quote_plus(target))

    def suggested_workers(self, requested: int | None = None) -> int:
        """Pick a sane default thread count.

        When ScraperAPI is enabled the origin's rate limit is bypassed via
        rotating proxies, so we can push higher concurrency (default 20).
        Without the fallback we stay conservative (16).
        """
        base = SCRAPER_DEFAULT_CONCURRENCY if self.enabled else DIRECT_DEFAULT_CONCURRENCY
        return requested if requested else base


def fetch(
    url: str,
    *,
    timeout: int = 15,
    cfg: ScraperConfig | None = None,
) -> requests.Response:
    """GET ``url`` with automatic ScraperAPI fallback on block patterns.

    Behaviour:
        - direct request first
        - on a block status (incl. 429), retry through ScraperAPI if enabled
        - on a block status without ScraperAPI, sleep
          :data:`RATE_LIMIT_BACKOFF_SEC` and retry once directly
        - on a connection / timeout error, retry through ScraperAPI if enabled,
          otherwise re-raise
    """
    cfg = cfg or ScraperConfig.from_env()
    headers = {"User-Agent": UA}

    try:
        r = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)
        if r.status_code not in BLOCK_STATUSES:
            return r
        if cfg.enabled:
            return requests.get(cfg.direct_url(url), timeout=timeout * 2)
        # No fallback configured — give the origin 1s breathing room and retry once.
        time.sleep(RATE_LIMIT_BACKOFF_SEC)
        return requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)
    except (requests.ConnectionError, requests.Timeout):
        if cfg.enabled:
            return requests.get(cfg.direct_url(url), timeout=timeout * 2)
        raise
