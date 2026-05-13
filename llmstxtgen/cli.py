"""Command-line interface: python -m llmstxtgen ..."""
from __future__ import annotations

import argparse
import json
import sys

from .core import generate
from .platforms import available_platforms
from .scraper import ScraperConfig


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="llmstxtgen",
        description="Generate an llms.txt from a sitemap (WordPress, Shopify, generic).",
    )
    p.add_argument("--sitemap", required=True, help="URL of the XML sitemap or sitemap index.")
    p.add_argument("--platform", required=True, choices=available_platforms())
    p.add_argument("--out", default="llms.txt", help="Output path (default: llms.txt).")
    p.add_argument("--title", default=None)
    p.add_argument("--desc", dest="meta_desc", default=None)
    p.add_argument(
        "--locales",
        default=None,
        help=(
            "Comma-separated locales to include. Special tokens: "
            "'root' (only un-prefixed), 'all' (every locale). "
            "Examples: --locales de,en-us  |  --locales all  |  --locales root,de"
        ),
    )
    p.add_argument("--fetch-meta", action="store_true", help="Fetch page <title> and meta description.")
    p.add_argument("--bucket-lang", choices=["de", "en"], default="de")
    p.add_argument("--ascii", action="store_true", help="Strip Umlaute/accents to ASCII.")
    p.add_argument("--timeout", type=int, default=10)
    p.add_argument("--workers", type=int, default=16)
    p.add_argument(
        "--scraper-key",
        default=None,
        help="ScraperAPI key. Falls back to env VPN_PROXY_API_KEY (skillmind-compat).",
    )
    p.add_argument(
        "--scraper-vendor",
        default=None,
        help="Scraper vendor (currently only 'scraperapi'). Falls back to env SCRAPER_Vendor.",
    )
    p.add_argument("--json", action="store_true", help="Print result summary as JSON.")
    return p


def _scraper_from_args(args) -> ScraperConfig:
    env_cfg = ScraperConfig.from_env()
    api_key = args.scraper_key or env_cfg.api_key
    vendor = (args.scraper_vendor or env_cfg.vendor or "scraperapi").lower()
    if api_key and vendor == "scraperapi":
        return ScraperConfig(api_key=api_key, vendor="scraperapi")
    return ScraperConfig(api_key=None)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    locales = [s.strip() for s in args.locales.split(",")] if args.locales else None
    scraper_cfg = _scraper_from_args(args)

    res = generate(
        sitemap_url=args.sitemap,
        platform=args.platform,
        output_path=args.out,
        title=args.title,
        meta_desc=args.meta_desc,
        include_locales=locales,
        fetch_meta=args.fetch_meta,
        bucket_lang=args.bucket_lang,
        ascii_only=args.ascii,
        req_timeout=args.timeout,
        meta_workers=args.workers,
        scraper_cfg=scraper_cfg,
    )
    summary = {
        "platform": res.platform,
        "n_urls": res.n_urls,
        "n_buckets": res.n_buckets,
        "n_locales": len(res.locales),
        "locales": [li.display_code for li in res.locales],
        "scraper": "scraperapi" if scraper_cfg.enabled else "off",
        "output_path": str(res.output_path) if res.output_path else None,
        "bytes": len(res.content.encode("utf-8")),
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for k, v in summary.items():
            print(f"{k}: {v}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
