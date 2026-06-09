"""Rule interface and registry.

Every QC rule is a small function with a uniform signature:

    func(df, schema, params) -> pandas.DataFrame

The returned frame shares the input's index and has exactly three columns:

    flagged : bool   did this respondent trip the rule?
    reason  : str    human-readable explanation (empty when not flagged)
    score   : float  0..1 severity of the issue (0 when not flagged)

Rules register themselves with `@register(...)`, so the engine can discover
them, check whether the current data supports them, and run the enabled ones.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

import pandas as pd

# Schema field names a rule may require (the engine skips a rule when the
# mapped data lacks what it needs).
REQUIRE_ID = "id_col"
REQUIRE_NPS = "nps_col"
REQUIRE_SCALE = "scale_cols"
REQUIRE_OPENEND = "openend_cols"
REQUIRE_DURATION = "duration_col"


@dataclass
class Rule:
    key: str                       # stable id, e.g. "speeding"
    name_zh: str                   # display name (Chinese UI)
    name_en: str                   # display name (English)
    description: str               # one-line explanation of what it catches
    func: Callable                 # func(df, schema, params) -> DataFrame
    requires: List[str] = field(default_factory=list)
    default_weight: float = 1.0    # contribution to the composite risk score
    default_params: Dict = field(default_factory=dict)
    is_llm: bool = False           # needs an LLM (skipped without an API key)


REGISTRY: Dict[str, Rule] = {}


def register(key, name_zh, name_en, description,
             requires=None, default_weight=1.0,
             default_params=None, is_llm=False):
    """Decorator that adds a rule function to the global registry."""
    def deco(func: Callable) -> Callable:
        REGISTRY[key] = Rule(
            key=key, name_zh=name_zh, name_en=name_en,
            description=description, func=func,
            requires=requires or [], default_weight=default_weight,
            default_params=default_params or {}, is_llm=is_llm,
        )
        return func
    return deco


def empty_result(index) -> pd.DataFrame:
    """A 'nothing flagged' result frame aligned to `index`."""
    return pd.DataFrame(
        {"flagged": False, "reason": "", "score": 0.0},
        index=index,
    )
