"""Platform protocol — what each bucket strategy must provide."""
from __future__ import annotations

from typing import Protocol

import pandas as pd


class Platform(Protocol):
    name: str
    bucket_order: list[str]

    def annotate(
        self,
        df: pd.DataFrame,
        *,
        include_locales: list[str] | None = None,
    ) -> pd.DataFrame:
        """Return df with at least 'bucket' (str) and optionally 'locale' (str|None) columns added."""
        ...

    def translate_buckets(self, bucket_lang: str) -> dict[str, str]:
        """Return {internal_name: localized_name} mapping for bucket_lang in {'de','en'}."""
        ...
