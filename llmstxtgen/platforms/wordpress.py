"""WordPress bucket strategy (Yoast/RankMath-style sitemap indexes + path heuristics)."""
from __future__ import annotations

from pathlib import PurePosixPath

import pandas as pd

from ..locales import locale_of_path


class WordPressPlatform:
    name = "wordpress"
    bucket_order = ["Beiträge", "Seiten", "Kategorien", "Tags", "Shop"]

    _trans = {
        "de": {
            "Beiträge": "Beiträge",
            "Seiten": "Seiten",
            "Kategorien": "Kategorien",
            "Tags": "Tags",
            "Shop": "Shop",
        },
        "en": {
            "Beiträge": "Posts",
            "Seiten": "Pages",
            "Kategorien": "Categories",
            "Tags": "Tags",
            "Shop": "Shop",
        },
    }

    def annotate(self, df: pd.DataFrame, *, include_locales=None) -> pd.DataFrame:
        df = df.copy()
        df["locale"] = df["path"].apply(locale_of_path)
        df["bucket"] = df.apply(self._wp_bucket, axis=1)
        if include_locales:
            wanted = {l.lower() for l in include_locales}
            if "all" not in wanted:
                keep_root = "root" in wanted
                wanted = wanted - {"root", "all"}
                mask = df["locale"].isin(wanted)
                if keep_root:
                    mask = mask | df["locale"].isna()
                df = df[mask]
        return df

    def translate_buckets(self, bucket_lang: str) -> dict[str, str]:
        if bucket_lang not in self._trans:
            raise ValueError("bucket_lang must be 'de' or 'en'")
        return self._trans[bucket_lang]

    @staticmethod
    def _wp_bucket(row) -> str:
        sm = (row.get("sitemap") or "").lower() if row.get("sitemap") is not None else ""
        if "post-sitemap" in sm:
            return "Beiträge"
        if "page-sitemap" in sm:
            return "Seiten"
        if "category-sitemap" in sm:
            return "Kategorien"
        if "tag-sitemap" in sm:
            return "Tags"
        if "product-sitemap" in sm:
            return "Shop"

        p = row["path"]
        if "/category/" in p:
            return "Kategorien"
        if "/tag/" in p:
            return "Tags"
        if "/shop/" in p or "/product/" in p:
            return "Shop"
        parts = PurePosixPath(p).parts
        if len(parts) >= 3 and parts[1].isdigit() and parts[2].isdigit():
            return "Beiträge"
        if p in {"/", ""} or p.count("/") <= 2:
            return "Seiten"
        return "Beiträge"
