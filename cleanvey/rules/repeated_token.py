"""Repeated-token spam: an open-end that is one short token piled up.

Examples: "推荐推荐推荐推荐", "好的好的好的好的". The existing gibberish rule
only catches *single-character* repeats ("好好好"); this catches multi-character
units repeated N times. Kept distinct by requiring a repeating unit of length
>= 2, so it never double-counts with gibberish.
"""
from __future__ import annotations

import re

import pandas as pd

from .base import register, empty_result, REQUIRE_OPENEND


def _is_repeated_token(text: str, min_repeats: int = 3) -> bool:
    t = re.sub(r"\s+", "", str(text).strip())
    n = len(t)
    if n < 4:
        return False
    # unit length >= 2 (single-char repeats are gibberish's job)
    for unit in range(2, n // min_repeats + 1):
        if n % unit == 0 and t[:unit] * (n // unit) == t:
            return True
    return False


@register(
    key="repeated_token",
    name_zh="重复刷屏",
    name_en="Repeated token",
    description="开放题为同一词语反复堆砌（如“推荐推荐推荐”）",
    requires=[REQUIRE_OPENEND],
    default_weight=0.7,
    default_params={"min_repeats": 3},
)
def check(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    cols = schema.openend_cols
    if not cols:
        return res
    min_repeats = int(params.get("min_repeats", 3))

    def is_rep(v):
        return _is_repeated_token(v, min_repeats)

    hit = pd.DataFrame(
        {c: df[c].fillna("").astype(str).map(is_rep) for c in cols}, index=df.index
    )
    n_hit = hit.sum(axis=1)
    flagged = n_hit > 0
    res.loc[flagged, "flagged"] = True
    res.loc[flagged, "score"] = 0.7
    res.loc[flagged, "reason"] = n_hit[flagged].map(
        lambda k: f"{int(k)} 道开放题为同一词语反复堆砌（重复刷屏）"
    )
    return res
