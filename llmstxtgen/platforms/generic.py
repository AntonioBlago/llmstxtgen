"""Generic single-bucket fallback for unknown CMS."""
from __future__ import annotations

import pandas as pd


class GenericPlatform:
    name = "generic"
    bucket_order = ["Pages"]

    _trans = {
        "de": {"Pages": "Seiten"},
        "en": {"Pages": "Pages"},
    }

    def annotate(self, df: pd.DataFrame, *, include_locales=None) -> pd.DataFrame:
        from ..locales import locale_of_path

        df = df.copy()
        df["locale"] = df["path"].apply(locale_of_path)
        df["bucket"] = "Pages"
        return df

    def translate_buckets(self, bucket_lang: str) -> dict[str, str]:
        if bucket_lang not in self._trans:
            raise ValueError("bucket_lang must be 'de' or 'en'")
        return self._trans[bucket_lang]
