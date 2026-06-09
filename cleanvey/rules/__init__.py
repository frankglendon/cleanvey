"""Importing this package registers every built-in rule.

Each module calls `@register(...)` at import time, populating `REGISTRY`.
The import order below is also the default display order. `openend` registers
three rules at once: gibberish, duplicate_text and offtopic.
"""
from .base import REGISTRY, Rule, register, empty_result  # noqa: F401

from . import speeding          # noqa: F401,E402
from . import straightlining    # noqa: F401,E402
from . import pattern           # noqa: F401,E402
from . import contradiction     # noqa: F401,E402
from . import openend           # noqa: F401,E402
from . import duplicate         # noqa: F401,E402
from . import missing           # noqa: F401,E402
from . import out_of_range      # noqa: F401,E402

__all__ = ["REGISTRY", "Rule", "register", "empty_result"]
