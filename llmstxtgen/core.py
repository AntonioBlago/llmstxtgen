"""High-level orchestrator: sitemap → DataFrame → buckets → llms.txt."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .fetcher import is_valid_xml_sitemap, load_sitemap
from .locales import LocaleInfo, summarize_locales
from .meta import fetch_meta_parallel
from .platforms import get_platform
from .scraper import ScraperConfig
from .writer import render


@dataclass
class GenerateResult:
    content: str
    output_path: Path | None
    platform: str
    n_urls: int
    n_buckets: int
    locales: list[LocaleInfo] = field(default_factory=list)


def generate(
    sitemap_url: str,
    platform: str,
    *,
    output_path: str | Path | None = "llms.txt",
    title: str | None = None,
    meta_desc: str | None = None,
    include_locales: list[str] | None = None,
    fetch_meta: bool = False,
    bucket_lang: str = "de",
    ascii_only: bool = False,
    req_timeout: int = 10,
    meta_workers: int = 16,
    scraper_cfg: ScraperConfig | None = None,
) -> GenerateResult:
    """Generate an llms.txt for the given sitemap.

    Parameters
    ----------
    include_locales : list[str] | None
        ``None`` → platform default (Shopify: root only; WordPress: all).
        ``["all"]``  → keep every locale, prefix kept on the URL.
        ``["root"]`` → only the un-prefixed URLs.
        ``["de", "en-us"]`` → keep just those subtrees (root excluded unless
        ``"root"`` is also passed).
    ascii_only : bool
        ``False`` (default) keeps full UTF-8 (Umlaute, accents). Set ``True``
        only if the consumer cannot handle non-ASCII.
    scraper_cfg : ScraperConfig | None
        Forwarded to :func:`fetch_meta_parallel`. Defaults to
        :meth:`ScraperConfig.from_env` so ``SCRAPER_Vendor=scraperapi`` +
        ``VPN_PROXY_API_KEY`` activate the fallback automatically.
    """
    from . import __version__

    if not is_valid_xml_sitemap(sitemap_url, timeout=req_timeout):
        raise ValueError(f"Provided sitemap_url is not a valid XML sitemap: {sitemap_url}")

    plat = get_platform(platform)
    df = load_sitemap(sitemap_url)
    locale_overview = summarize_locales(df, sitemap_url)
    df = plat.annotate(df, include_locales=include_locales)

    meta_map: dict[str, tuple[str, str]] | None = None
    if fetch_meta:
        meta_map = fetch_meta_parallel(
            df["loc"].tolist(),
            timeout=req_timeout,
            max_workers=meta_workers,
            cfg=scraper_cfg,
        )

    content = render(
        df=df,
        sitemap_url=sitemap_url,
        platform_name=plat.name,
        bucket_order=plat.bucket_order,
        bucket_translation=plat.translate_buckets(bucket_lang),
        title=title,
        meta_desc=meta_desc,
        include_locales=include_locales,
        ascii_only=ascii_only,
        meta_map=meta_map,
        version=__version__,
        locales=locale_overview,
    )

    out_path: Path | None = None
    if output_path:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")

    n_buckets = int(df["bucket"].nunique())
    return GenerateResult(
        content=content,
        output_path=out_path,
        platform=plat.name,
        n_urls=int(len(df)),
        n_buckets=n_buckets,
        locales=locale_overview,
    )
