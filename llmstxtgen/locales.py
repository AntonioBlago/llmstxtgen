"""Locale detection + display naming.

Detects locale prefix at the first path segment. Format expected:
- `xx` (language only)        → e.g. /de/...
- `xx-yy` (language-country)  → e.g. /en-us/...
- root (no prefix)            → /...

Provides a compact registry so generated llms.txt headers can show
human-readable names alongside the canonical root URL per locale.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import urlparse

LOCALE_PAT = re.compile(r"^[a-z]{2}(?:-[a-z]{2})?$")

# Trimmed ISO maps — extend on demand.
LANG_NAMES = {
    "de": "Deutsch", "en": "English", "fr": "Français", "it": "Italiano",
    "es": "Español", "nl": "Nederlands", "pt": "Português", "pl": "Polski",
    "cs": "Čeština", "sk": "Slovenčina", "sv": "Svenska", "da": "Dansk",
    "no": "Norsk", "fi": "Suomi", "ja": "日本語", "zh": "中文",
    "ko": "한국어", "ru": "Русский", "tr": "Türkçe", "uk": "Українська",
    "ar": "العربية", "he": "עברית", "ro": "Română", "hu": "Magyar",
    "el": "Ελληνικά", "bg": "Български",
}

COUNTRY_NAMES = {
    "de": "Germany", "us": "United States", "gb": "United Kingdom", "uk": "United Kingdom",
    "fr": "France", "it": "Italy", "es": "Spain", "ch": "Switzerland",
    "at": "Austria", "nl": "Netherlands", "be": "Belgium", "pl": "Poland",
    "cz": "Czech Republic", "sk": "Slovakia", "se": "Sweden", "dk": "Denmark",
    "no": "Norway", "fi": "Finland", "jp": "Japan", "cn": "China",
    "kr": "South Korea", "ru": "Russia", "tr": "Turkey", "ua": "Ukraine",
    "ie": "Ireland", "pt": "Portugal", "br": "Brazil", "mx": "Mexico",
    "ca": "Canada", "au": "Australia", "nz": "New Zealand", "in": "India",
    "ae": "United Arab Emirates", "il": "Israel", "ro": "Romania", "hu": "Hungary",
    "gr": "Greece", "bg": "Bulgaria", "hr": "Croatia", "rs": "Serbia",
    "si": "Slovenia",
}


@dataclass(frozen=True)
class LocaleInfo:
    code: str | None         # None → root
    language: str | None     # ISO 639-1 or None for root
    country: str | None      # ISO 3166-1 alpha-2 or None
    root_url: str            # absolute prefix URL (e.g. https://x.com/de/)
    n_urls: int

    @property
    def display_code(self) -> str:
        return self.code if self.code else "root"

    @property
    def human_name(self) -> str:
        if self.code is None:
            return "Default / Root"
        lang = LANG_NAMES.get(self.language or "", self.language or "")
        if self.country:
            country = COUNTRY_NAMES.get(self.country, self.country.upper())
            return f"{lang}, {country}" if lang else country
        return lang or self.code


def _looks_like_locale(seg: str) -> bool:
    """True iff segment is plausibly an i18n prefix, not a content slug.

    Accept ``xx-yy`` unconditionally (always a locale-country pair).
    Accept bare ``xx`` only when the language code is known — that filters out
    coincidental two-letter content folders like ``/ki/`` or ``/ai/``.
    """
    if not LOCALE_PAT.match(seg):
        return False
    if "-" in seg:
        return True
    return seg in LANG_NAMES


def locale_of_path(path: str) -> str | None:
    parts = PurePosixPath(path).parts
    if len(parts) >= 2 and _looks_like_locale(parts[1]):
        return parts[1]
    return None


def strip_locale(path: str) -> str:
    parts = PurePosixPath(path).parts
    if len(parts) >= 2 and _looks_like_locale(parts[1]):
        rest = "/".join(parts[2:])
        return "/" + rest if rest else "/"
    return path


def _split_code(code: str) -> tuple[str, str | None]:
    if "-" in code:
        a, b = code.split("-", 1)
        return a, b
    return code, None


def summarize_locales(df, sitemap_url: str) -> list[LocaleInfo]:
    """Return one LocaleInfo per detected locale (incl. None=root if present)."""
    if "locale" not in df.columns:
        df = df.copy()
        df["locale"] = df["path"].apply(locale_of_path)

    parsed = urlparse(sitemap_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    out: list[LocaleInfo] = []
    for code, n in df["locale"].fillna("__root__").value_counts().items():
        if code == "__root__":
            out.append(LocaleInfo(None, None, None, base + "/", int(n)))
            continue
        lang, country = _split_code(code)
        out.append(LocaleInfo(code, lang, country, f"{base}/{code}/", int(n)))

    out.sort(key=lambda x: (x.code is not None, x.code or ""))
    return out
