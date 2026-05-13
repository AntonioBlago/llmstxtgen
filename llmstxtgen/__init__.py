"""llmstxtgen — modular llms.txt generator for WordPress, Shopify, and generic sitemaps."""
from .core import generate, GenerateResult
from .platforms import register_platform, get_platform, available_platforms

__version__ = "0.8.0"
__all__ = [
    "generate",
    "GenerateResult",
    "register_platform",
    "get_platform",
    "available_platforms",
    "__version__",
]
