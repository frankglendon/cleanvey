"""Straightlining: the same answer down a whole block of scale questions.

When a respondent gives an (almost) identical value to every matrix/Likert
item, they are likely not reading the questions. We measure the spread of the
scale answers per respondent and flag rows whose spread is at or below a
threshold (0 = literally all identical).
"""
from __future__ import annotations

import pandas as pd

from .base import register, empty_result, REQUIRE_SCALE


@register(
    key="straightlining",
    name_zh="直线作答",
    name_en="Straightlining",
    description="一整组量表题几乎都选同一个答案",
    requires=[REQUIRE_SCALE],
    default_weight=1.0,
    default_params={"min_items": 3, "std_threshold": 0.0},
)
def check(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    min_items = int(params.get("min_items", 3))
    std_threshold = float(params.get("std_threshold", 0.0))

    vals = df[schema.scale_cols].apply(pd.to_numeric, errors="coerce")
    answered = vals.notna().sum(axis=1)
    spread = vals.std(axis=1)

    flagged = (answered >= min_items) & (spread <= std_threshold)
    res.loc[flagged, "flagged"] = True
    res.loc[flagged, "score"] = 1.0
    res.loc[flagged, "reason"] = answered[flagged].map(
        lambda n: f"{int(n)} 道量表题选了几乎相同的答案（直线作答）"
    )
    return res
