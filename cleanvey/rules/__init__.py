"""Importing this package registers every built-in rule.
导入本包即注册所有内置规则。

Each module calls `@register(...)` at import time, populating `REGISTRY`.
The import order below is also the default display order. `openend` registers
three rules at once: gibberish, duplicate_text and offtopic.
每个模块在导入时调用 `@register(...)` 填充 `REGISTRY`；下面的导入顺序也是默认展示顺序。
`openend` 一次注册三条规则：gibberish、duplicate_text、offtopic。
"""
from .base import REGISTRY, Rule, register, empty_result  # noqa: F401

from . import speeding          # noqa: F401,E402
from . import straightlining    # noqa: F401,E402
from . import pattern           # noqa: F401,E402
from . import contradiction     # noqa: F401,E402
from . import logic_check       # noqa: F401,E402
from . import openend           # noqa: F401,E402
from . import low_effort        # noqa: F401,E402
from . import too_short         # noqa: F401,E402
from . import repeated_token    # noqa: F401,E402
from . import near_duplicate    # noqa: F401,E402
from . import self_duplicate    # noqa: F401,E402
from . import duplicate         # noqa: F401,E402
from . import missing           # noqa: F401,E402
from . import out_of_range      # noqa: F401,E402

__all__ = ["REGISTRY", "Rule", "register", "empty_result"]
