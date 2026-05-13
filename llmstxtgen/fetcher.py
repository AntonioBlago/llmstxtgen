"""Sitemap loading and basic validation.

Validation goes through :func:`llmstxtgen.scraper.fetch` so a sitemap behind a
Cloudflare/rate-limit wall still gets through ScraperAPI when configured.
"""
from __future__ import annotations

import warnings
from urllib.parse import urlparse

import advertools as adv
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

UA = "Mozilla/5.0 (compatible; llmstxtgen/0.8; +https://antonioblago.de)"


def is_valid_xml_sitemap(url: str, timeout: int = 10) -> bool:
    # Local import to break the scraper ↔ fetcher cycle at import time.
    from .scraper import fetch

    try:
        r = fetch(url, timeout=timeout)
        r.raise_for_status()
        ct = r.headers.get("Content-Type", "").lower()
        if "xml" not in ct and not r.text.lstrip().startswith("<?xml"):
            return False
        BeautifulSoup(r.content, "xml")
        return True
    except Exception:
        return False


def load_sitemap(url: str):
    """Return a pandas DataFrame of URLs from a sitemap or sitemap index."""
    df = adv.sitemap_to_df(url)
    if df.empty:
        raise ValueError(f"Sitemap returned no URLs: {url}")
    df = df.copy()
    df["loc"] = df["loc"].astype(str).str.strip()
    df["path"] = df["loc"].apply(lambda x: urlparse(x).path.lower())
    if "sitemap" not in df.columns:
        df["sitemap"] = None
    return df
