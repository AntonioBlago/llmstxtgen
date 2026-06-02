# Shopify and Wordpress LLMs.txt Generator 

Modular `llms.txt` and free generator from XML sitemaps. Supports **WordPress**, **Shopify** (locale-aware), and a **generic** fallback. UTF-8 by default.

## Install

```powershell
# In repo root
.\install.ps1
```

The script:

1. Creates/uses `env_llmstxtgen` venv.
2. `pip install -e .` so the `llmstxtgen` command becomes available.
3. Verifies a smoke test against `https://antonioblago.de/sitemap_index.xml`.

Manual install:

```powershell
& .\env_llmstxtgen\Scripts\python.exe -m pip install -e .
```

## Use

CLI:

```powershell
llmstxtgen --sitemap https://antonioblago.de/sitemap_index.xml --platform wordpress --out out.txt --title "Antonio Blago" --bucket-lang de
llmstxtgen --sitemap https://www.x-bionic.com/sitemap.xml --platform shopify --out xb.txt --locales de --bucket-lang en
```

`--locales` accepts a comma-separated list with two special tokens:

| Value           | Meaning                                                                |
|-----------------|------------------------------------------------------------------------|
| _(omitted)_     | Shopify → only root URLs · WordPress → all URLs                        |
| `root`          | Only root (un-prefixed) URLs                                           |
| `all`           | Every detected locale                                                  |
| `de,en-us`      | Just these subtrees (add `root` to include root as well, e.g. `root,de`) |

The generated header always includes a **Locales** overview listing every
detected locale with language, country, root URL and URL count — even when
the `## URLs` section is scoped to a subset.

Python:

```python
from llmstxtgen import generate
res = generate(sitemap_url="https://...", platform="wordpress", output_path="llms.txt")
```

### ScraperAPI fallback (skillmind-compatible)

For affiliate links / Cloudflare walls / geo-blocked sitemaps, the fetcher
falls back to ScraperAPI. The same env vars as in **skillmind** activate it:

```powershell
$env:SCRAPER_Vendor = "scraperapi"
$env:VPN_PROXY_API_KEY = "<your key>"
```

Or pass them per call: `llmstxtgen ... --scraper-key <key> --scraper-vendor scraperapi`.

The proxy URL (for `yt-dlp` / `HTTP_PROXY`-style consumers) is
`http://scraperapi:<KEY>@proxy-server.scraperapi.com:8001` and exposed as
`ScraperConfig.proxy_url`.

## Claude Code skill

Skill `llms-txt` installed at `~/.claude/skills/llms-txt/SKILL.md`. Invoke via `/llms-txt` or just say *"llms.txt für <domain> generieren"*.

## Architecture

```
llmstxtgen/
├── core.py            # generate() orchestrator
├── fetcher.py         # sitemap → DataFrame (advertools)
├── meta.py            # parallel <title>/meta fetch
├── writer.py          # markdown writer (incl. Locales header)
├── locales.py         # locale detection + language/country names
├── scraper.py         # ScraperAPI fallback (skillmind env-var compat)
├── cli.py             # argparse entrypoint
└── platforms/
    ├── base.py        # Platform protocol
    ├── wordpress.py
    ├── shopify.py     # locale-aware
    └── generic.py
```

Register a custom platform:

```python
from llmstxtgen import register_platform
register_platform("woocommerce", WooCommercePlatform)
```

## Backwards compat

`llms_function.py` keeps the v0.7 signature `generate_llms_txt(...)` so the existing Apify Actor wrapper still works.
