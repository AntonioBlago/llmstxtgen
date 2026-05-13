# Quick Guide

One-page cheat sheet for `llmstxtgen` v0.8.

## 30-second install

```powershell
git clone https://github.com/AntonioBlago/llmstxtgen.git
cd llmstxtgen
.\install.ps1
```

After install, the `llmstxtgen` command is on PATH inside the venv.

## Generate from a sitemap

```powershell
# WordPress (Yoast / RankMath sitemap index)
llmstxtgen --sitemap https://antonioblago.de/sitemap_index.xml `
           --platform wordpress `
           --out antonioblago_llms.txt `
           --title "Antonio Blago" `
           --bucket-lang de

# Shopify (locale-aware; defaults to root URLs only)
llmstxtgen --sitemap https://www.x-bionic.com/sitemap.xml `
           --platform shopify `
           --out xbionic_llms.txt `
           --title "X-BIONIC" `
           --bucket-lang en
```

## Add real `<title>` and meta-description per URL

```powershell
llmstxtgen --sitemap https://example.com/sitemap.xml `
           --platform wordpress `
           --out example_llms.txt `
           --fetch-meta `
           --timeout 30
```

Each URL gets parsed via BeautifulSoup; soft-hyphens, NBSPs and HTML entities
are cleaned automatically.

## `--locales` cheat sheet

| Flag                 | Effect                                                      |
|----------------------|-------------------------------------------------------------|
| _(omitted)_          | Shopify → root only · WordPress → all URLs                 |
| `--locales root`     | Only root (un-prefixed) URLs                                |
| `--locales all`      | Every detected locale                                       |
| `--locales de,en-us` | Only these subtrees                                         |
| `--locales root,de`  | Root + the `de` subtree                                     |

The output header always lists every detected locale with language, country,
root URL and URL count — even when the body is scoped to a subset.

## ScraperAPI fallback (Cloudflare / 429 / affiliate links)

Set once per shell:

```powershell
$env:SCRAPER_Vendor    = "scraperapi"
$env:VPN_PROXY_API_KEY = "<your key>"
```

Or pass per call:

```powershell
llmstxtgen --sitemap ... --scraper-key <key> --scraper-vendor scraperapi
```

With ScraperAPI enabled, `--fetch-meta` runs 20 concurrent workers (16 without).
On direct-mode 429 the worker sleeps 1 second and retries once.

## JSON output for scripting

```powershell
llmstxtgen --sitemap ... --json | ConvertFrom-Json
```

Returns: `platform`, `n_urls`, `n_buckets`, `n_locales`, `locales[]`,
`scraper`, `output_path`, `bytes`.

## Claude Code

Skill installed at `~/.claude/skills/llms-txt/SKILL.md`. Invoke with:

```
/llms-txt
```

…or just *"generate llms.txt for example.com"* in chat.

## Python API

```python
from llmstxtgen import generate

res = generate(
    sitemap_url="https://example.com/sitemap.xml",
    platform="shopify",
    output_path="example_llms.txt",
    title="Example",
    fetch_meta=True,
    locales=["root", "de"],
)
print(res.n_urls, res.locales)
```

## Troubleshooting

| Symptom                                  | Fix                                                              |
|------------------------------------------|------------------------------------------------------------------|
| `Sitemap returned no URLs`               | Verify URL in browser; check for redirects to a different host.  |
| `Provided sitemap_url is not a valid XML sitemap` | Site is blocking direct requests — set ScraperAPI env vars. |
| Empty titles/descriptions                | Same — origin is rate-limiting; enable ScraperAPI.               |
| Soft-hyphens / `&#39;` in output         | Already cleaned in v0.8. Re-generate if file is from v0.7.       |
| `/ki/` showing as a locale on a German site | Fixed in v0.8 (bare 2-letter segments must match ISO-639-1).  |
