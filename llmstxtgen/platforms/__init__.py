"""Platform registry — pluggable bucket strategies."""
from __future__ import annotations

from typing import Callable

from .base import Platform
from .generic import GenericPlatform
from .shopify import ShopifyPlatform
from .wordpress import WordPressPlatform

_REGISTRY: dict[str, Callable[[], Platform]] = {
    "wordpress": WordPressPlatform,
    "shopify": ShopifyPlatform,
    "generic": GenericPlatform,
}


def register_platform(name: str, factory: Callable[[], Platform]) -> None:
    _REGISTRY[name.lower().strip()] = factory


def get_platform(name: str) -> Platform:
    key = name.lower().strip()
    if key not in _REGISTRY:
        raise ValueError(f"Unknown platform {name!r}. Available: {sorted(_REGISTRY)}")
    return _REGISTRY[key]()


def available_platforms() -> list[str]:
    return sorted(_REGISTRY)


__all__ = [
    "Platform",
    "register_platform",
    "get_platform",
    "available_platforms",
]
