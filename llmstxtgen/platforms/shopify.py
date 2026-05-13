"""Shopify bucket strategy with locale-aware path handling.

Default behavior changed in v0.9:
- `include_locales=None` (CLI: omit `--locales`) → only ROOT URLs are kept.
- `include_locales=['root']` → same as None.
- `include_locales=['de','en-us']` → keep just those locale subtrees.
- `include_locales=['all']` → keep every URL, locale collapsed via clean_path.

In every case `clean_path` is the locale-stripped path so bucket rules match.
"""
from __future__ import annotations

import pandas as pd

from ..locales import locale_of_path, strip_locale


class ShopifyPlatform:
    name = "shopify"
    bucket_order = ["Pages", "Blogs", "Collections", "PDPs"]

    _trans = {
        "de": {
            "Pages": "Seiten",
            "Blogs": "Blogs",
            "Collections": "Kollektionen",
            "PDPs": "Produkte",
        },
        "en": {
            "Pages": "Pages",
            "Blogs": "Blogs",
            "Collections": "Collections",
            "PDPs": "Products",
        },
    }

    _rules = {
        "Pages": lambda p: p.startswith("/pages/"),
        "Blogs": lambda p: p.startswith("/blogs/"),
        "Collections": lambda p: p.startswith("/collections/"),
        "PDPs": lambda p: p.startswith("/products/"),
    }

    def annotate(self, df: pd.DataFrame, *, include_locales=None) -> pd.DataFrame:
        df = df.copy()
        df["locale"] = df["path"].apply(locale_of_path)
        df["clean_path"] = df.apply(
            lambda r: strip_locale(r["path"]) if r["locale"] else r["path"], axis=1
        )

        df = self._filter_locales(df, include_locales)
        df["bucket"] = df["clean_path"].apply(self._sh_bucket)
        return df

    @staticmethod
    def _filter_locales(df: pd.DataFrame, include_locales) -> pd.DataFrame:
        if not include_locales:
            # Default = root only.
            return df[df["locale"].isna()]
        wanted = {l.lower() for l in include_locales}
        if "all" in wanted:
            return df
        keep_root = "root" in wanted
        wanted = wanted - {"root", "all"}
        mask = df["locale"].isin(wanted)
        if keep_root:
            mask = mask | df["locale"].isna()
        return df[mask]

    def translate_buckets(self, bucket_lang: str) -> dict[str, str]:
        if bucket_lang not in self._trans:
            raise ValueError("bucket_lang must be 'de' or 'en'")
        return self._trans[bucket_lang]

    @classmethod
    def _sh_bucket(cls, clean_path: str) -> str:
        for name, rule in cls._rules.items():
            if rule(clean_path):
                return name
        return "Other"
