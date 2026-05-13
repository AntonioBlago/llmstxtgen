"""Backwards-compatible shim for v0.7 callers.

Re-exports `generate_llms_txt` with the legacy signature so existing scripts
(e.g. the Apify Actor wrapper) keep working. New code should use
`from llmstxtgen import generate`.
"""
from __future__ import annotations

from llmstxtgen import generate
from llmstxtgen.writer import de_ascii  # noqa: F401  (legacy public symbol)
from llmstxtgen.fetcher import is_valid_xml_sitemap as is_valid_xml  # noqa: F401


def generate_llms_txt(
    sitemap_url: str,
    platform: str,
    output_path: str = "llms.txt",
    title: str | None = None,
    meta_desc: str | None = None,
    include_locales: list[str] | None = None,
    fetch_meta: bool = False,
    bucket_lang: str = "de",
    req_timeout: int = 10,
) -> str:
    """Legacy entry point. Returns the generated content as a string."""
    res = generate(
        sitemap_url=sitemap_url,
        platform=platform,
        output_path=output_path,
        title=title,
        meta_desc=meta_desc,
        include_locales=include_locales,
        fetch_meta=fetch_meta,
        bucket_lang=bucket_lang,
        ascii_only=True,  # legacy behavior
        req_timeout=req_timeout,
    )
    return res.content


if __name__ == "__main__":
    generate_llms_txt(
        sitemap_url="https://www.x-bionic.com/sitemap.xml",
        platform="shopify",
        output_path="llms.txt",
        bucket_lang="en",
        title="X-BIONIC",
        meta_desc="Performance sportswear",
        fetch_meta=False,
    )
