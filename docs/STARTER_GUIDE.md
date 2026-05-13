# Starter Guide — `llmstxtgen`

A practical, end-to-end walkthrough: from "I have a website" to "my llms.txt
is published and crawl-ready". Estimated time: 10 minutes for a small site,
~20 minutes for a multi-locale Shopify store with `--fetch-meta`.

---

## 1. What is `llms.txt` and why generate one?

`llms.txt` is a markdown index that tells LLM-based crawlers and search
engines what your site contains, structured for cheap consumption. Unlike
`sitemap.xml`, it carries:

- a human-readable title and description per page,
- bucketing by content type (Pages, Posts, Collections, Products…),
- per-locale grouping for international sites,
- a header section explaining the site as a whole.

Where `robots.txt` says *what crawlers may do*, `llms.txt` says *what the
site is and where to look first*.

`llmstxtgen` reads your existing XML sitemap, infers the platform, optionally
fetches each page's `<title>` and meta description, and writes one
`llms.txt` per project.

---

## 2. Prerequisites

| Requirement       | Version / Note                                         |
|-------------------|--------------------------------------------------------|
| Python            | 3.10 or newer                                          |
| PowerShell        | 5.1+ (Windows) — Bash also works on macOS / Linux      |
| Git               | for cloning the repo                                   |
| ScraperAPI key    | _optional_ — only needed for Cloudflare-walled sites   |

The package depends on `advertools`, `beautifulsoup4`, `lxml`, `pandas` and
`requests`. The installer pulls these into a local venv so they don't
pollute your global Python.

---

## 3. Installation

### Option A — automated installer (Windows)

```powershell
git clone https://github.com/AntonioBlago/llmstxtgen.git
cd llmstxtgen
.\install.ps1
```

The script:
1. Creates `env_llmstxtgen\` venv if missing.
2. Installs the package in editable mode (`pip install -e .`).
3. Runs a smoke test against `antonioblago.de` and prints a JSON summary.

### Option B — manual install (any OS)

```bash
git clone https://github.com/AntonioBlago/llmstxtgen.git
cd llmstxtgen
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -e .
```

Verify:

```bash
llmstxtgen --help
```

---

## 4. Your first run

The minimum useful invocation needs three flags: a sitemap, a platform, and
an output path.

```powershell
llmstxtgen --sitemap https://antonioblago.de/sitemap_index.xml `
           --platform wordpress `
           --out llms.txt `
           --title "Antonio Blago" `
           --desc  "Neuro-SEO Freelancer" `
           --bucket-lang de
```

After ~2 seconds you'll see a JSON summary if you add `--json`, plus a
written `llms.txt` in the current directory.

### Picking the right `--platform`

| Platform     | Use when…                                                    |
|--------------|--------------------------------------------------------------|
| `wordpress`  | URLs are categorised into Pages, Posts, Categories, etc.     |
| `shopify`    | URLs include `/products/`, `/collections/`, `/pages/`        |
| `generic`    | Anything else — buckets by path prefix                       |

You don't have to be precise; if the inferred buckets look thin, try the
other platform and rerun. The sitemap is fetched once and parsed locally,
so iteration is cheap.

### Picking `--bucket-lang`

Controls the bucket section headers (`## Pages` vs. `## Seiten`). It does
**not** affect URL filtering. Pick `de` for German sites, `en` for English;
default is `en`.

---

## 5. Adding real titles and descriptions

By default, `llmstxtgen` writes a clean URL list with each URL's last path
segment as the link label. To pull the actual `<title>` and
`<meta name="description">` from each page, add `--fetch-meta`:

```powershell
llmstxtgen --sitemap https://antonioblago.de/sitemap_index.xml `
           --platform wordpress `
           --out llms.txt `
           --title "Antonio Blago" `
           --fetch-meta `
           --timeout 30 `
           --bucket-lang de
```

What happens:
- A thread pool fetches every URL in parallel (default 16 workers, 20 if
  ScraperAPI is enabled).
- The HTML is parsed with BeautifulSoup; `<title>` text + meta description
  are extracted.
- Each string is cleaned: NBSP → space, soft-hyphens removed, HTML entities
  decoded, whitespace collapsed.
- Pages that fail to load yield empty title/desc — they still appear in the
  output, just without metadata.

For 100 URLs this typically completes in 10-20 seconds. For 1000 URLs,
plan for a few minutes — or enable ScraperAPI for higher concurrency.

---

## 6. Multi-locale sites (Shopify, hreflang)

International Shopify stores expose every locale (`/de/`, `/en-us/`,
`/fr/`, …) under one sitemap. By default `llmstxtgen` keeps your output
sane by writing **only the root (un-prefixed) URLs** for Shopify — the
locale header still lists everything so consumers know subtrees exist.

```powershell
llmstxtgen --sitemap https://www.x-bionic.com/sitemap.xml `
           --platform shopify `
           --out xbionic_llms.txt `
           --title "X-BIONIC" `
           --bucket-lang en
```

To include specific locales (e.g. only German variants):

```powershell
llmstxtgen ... --locales root,de,de-de,de-at,de-ch
```

To include every detected locale:

```powershell
llmstxtgen ... --locales all
```

The output's `## Locales` block always shows the full set, regardless of
what's rendered below:

```markdown
## Locales
- **root**  — Default / Root      — [https://example.com/](…) — 764 URLs
- **de**    — Deutsch             — [https://example.com/de/](…) — 761 URLs
- **en-us** — English, United States — [https://example.com/en-us/](…) — 761 URLs
…

_Scope of URLs below:_ `root` (default; use --locales all to include every locale)
```

---

## 7. Sites behind Cloudflare or rate limits

If a site rejects direct `requests` with 403/429/503, route through
ScraperAPI. The same env vars used in **skillmind** are honoured:

```powershell
$env:SCRAPER_Vendor    = "scraperapi"
$env:VPN_PROXY_API_KEY = "your-scraperapi-key"
```

Once set, every fetch (sitemap validation, `--fetch-meta` per-URL) falls
back to ScraperAPI automatically when the direct request would be blocked.
You can confirm activation in the JSON summary:

```json
{ ..., "scraper": "scraperapi" }
```

Without env vars set the same JSON shows `"scraper": null`.

### How the fallback decides

1. Direct GET first.
2. If status ∈ `{401, 403, 405, 406, 408, 409, 425, 429, 5xx, 520-524}`,
   retry via `http://api.scraperapi.com/?api_key=...&url=...`.
3. If no key is configured and we got a block status, sleep 1 second and
   retry once directly — this is enough for most rate-limit windows.
4. On a connection / timeout error, fall back to ScraperAPI if enabled;
   otherwise re-raise.

### Plan-specific concurrency

ScraperAPI plans have concurrency limits (Hobby 25 / Startup 50 /
Business 100). `llmstxtgen` defaults to **20 concurrent workers** when
ScraperAPI is active — comfortably under Hobby — and **16** otherwise.
Override with `--workers N` if you've got a bigger plan.

### Proxy URL for other tools

`ScraperConfig.proxy_url` returns
`http://scraperapi:<KEY>@proxy-server.scraperapi.com:8001`, which works
as an `HTTP_PROXY` for `yt-dlp`, `curl`, or any HTTP client that accepts a
proxy URL.

---

## 8. JSON output for scripting / CI

Add `--json` and a single-line JSON summary is appended to stdout after
the file is written:

```json
{
  "platform": "shopify",
  "n_urls": 764,
  "n_buckets": 5,
  "n_locales": 40,
  "locales": ["root", "de", "de-at", …, "en-us"],
  "scraper": "scraperapi",
  "output_path": "C:\\…\\xbionic_llms.txt",
  "bytes": 217701
}
```

Pipe into anything: GitHub Actions step output, n8n workflow node,
make-job downstream.

---

## 9. Python API

For embedding into a larger workflow or an Apify Actor:

```python
from llmstxtgen import generate

res = generate(
    sitemap_url="https://example.com/sitemap.xml",
    platform="shopify",
    output_path="llms.txt",
    title="Example",
    description="Example storefront",
    fetch_meta=True,
    timeout=30,
    locales=["root", "de"],
    bucket_lang="en",
)

print(f"{res.n_urls} URLs across {res.n_buckets} buckets")
print(f"Locales: {res.locales}")
print(f"Wrote {res.bytes_written} bytes to {res.output_path}")
```

The legacy v0.7 entry point `generate_llms_txt(...)` remains in
`llms_function.py` so existing Apify wrappers still work without changes.

---

## 10. Custom platforms

Each platform is a tiny class — register a new one without forking:

```python
from llmstxtgen import register_platform
from llmstxtgen.platforms.base import Platform

class WooCommercePlatform(Platform):
    def bucketize(self, df):
        ...

register_platform("woocommerce", WooCommercePlatform)
```

After that, `--platform woocommerce` (CLI) and `platform="woocommerce"`
(API) both work.

---

## 11. Operating tips

- **Re-run is idempotent.** Sitemaps are fetched fresh each time; outputs
  are overwritten in place. Safe to wire into a nightly cron.
- **Output size scales linearly with `--fetch-meta`.** A 100-URL site
  yields ~30 KB; a 1000-URL site, ~250 KB.
- **Soft-hyphens used to leak through.** Anything generated before v0.8
  may contain `­`, `&nbsp;`, or `&#39;`. Re-generate or run
  `python -c "import html, re, unicodedata; ..."`-style cleanup over the
  file — or simply regenerate.
- **Sitemap of sitemaps?** Pass the index URL; `advertools` follows the
  index transparently.

---

## 12. Next step — Claude Code integration

The repo ships with a Claude Code skill:

```
~/.claude/skills/llms-txt/SKILL.md
```

Invoke with `/llms-txt` or say:

> "Generate an llms.txt for x-bionic.com with meta descriptions for the German locales."

Claude picks the right platform, sets the locale filter, enables
`--fetch-meta`, and writes the file to your `OneDrive\…\Claude\llms\`
folder by default.

---

## 13. Going further

- **Pair with a crawler.** `llmstxtgen` is intentionally sitemap-driven;
  if your site has orphan pages, pair with `advertools.crawl()` and feed
  the discovered URLs into `generate(urls=[...])`.
- **Compare versions.** Diff two outputs to spot content additions or
  removals over time — clean text inputs diff beautifully.
- **Publish.** Drop `llms.txt` at the site root (`/llms.txt`). No special
  server config needed; it's plain text.

---

Questions, bugs, ideas → open an issue at
<https://github.com/AntonioBlago/llmstxtgen/issues>.
