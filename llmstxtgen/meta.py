"""Optional parallel page-meta fetcher (title + meta description).

Routes every request through :func:`llmstxtgen.scraper.fetch`, which falls back
to ScraperAPI when the direct request is blocked (Cloudflare, 403/429 walls,
affiliate-link gates). The fallback is auto-detected from the environment
unless an explicit ``ScraperConfig`` is passed in.
"""
from __future__ import annotations

import html
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable

from bs4 import BeautifulSoup

from .scraper import ScraperConfig, fetch

# U+00AD soft hyphen, U+200B zero-width space, U+200C/D ZWNJ/ZWJ, U+FEFF BOM
_INVISIBLE = re.compile(r"[­​-‍﻿]")
_WS = re.compile(r"\s+")


def _clean(s: str) -> str:
    """Strip soft hyphens, normalise NBSP/Unicode, decode entities, collapse whitespace."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)  # NBSP → regular space, fullwidth → ASCII
    s = _INVISIBLE.sub("", s)
    s = html.unescape(s)  # &#39; → '
    s = _WS.sub(" ", s)
    return s.strip()


def _fetch_one(url: str, timeout: int, cfg: ScraperConfig) -> tuple[str, tuple[str, str]]:
    try:
        r = fetch(url, timeout=timeout, cfg=cfg)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        title = _clean(soup.title.get_text()) if soup.title else ""
        md = soup.find("meta", attrs={"name": "description"})
        desc = _clean(md.get("content", "")) if md else ""
        return url, (title, desc)
    except Exception:
        return url, ("", "")


def fetch_meta_parallel(
    urls: Iterable[str],
    timeout: int = 10,
    max_workers: int | None = None,
    cfg: ScraperConfig | None = None,
) -> dict[str, tuple[str, str]]:
    """Fetch ``(title, description)`` for each URL in parallel.

    ``max_workers=None`` (the default) picks a sane concurrency level via
    :meth:`ScraperConfig.suggested_workers` — 20 when ScraperAPI is active
    (rotating proxies bypass origin rate limits), 16 otherwise. Pass an
    explicit integer to override.
    """
    cfg = cfg or ScraperConfig.from_env()
    workers = cfg.suggested_workers(max_workers)
    out: dict[str, tuple[str, str]] = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_fetch_one, u, timeout, cfg) for u in urls]
        for fut in as_completed(futures):
            url, pair = fut.result()
            out[url] = pair
    return out
