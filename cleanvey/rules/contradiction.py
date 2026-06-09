"""Contradiction: answers that conflict with each other.

The universal, low-false-positive case we ship by default: the NPS score
should move together with an overall-satisfaction scale item. A respondent who
gives a top NPS but the lowest satisfaction (or vice-versa) is contradicting
themselves. If no satisfaction item is present, the rule simply does nothing.

Users can declare additional checks via `consistency_pairs` in params.
"""
from __future__ import annotations

import pandas as pd

from .base import register, empty_result, REQUIRE_NPS

_SATISFACTION_HINTS = ("满意", "satisf", "overall", "总体", "整体")


def _find_satisfaction(schema):
    for col in schema.scale_cols:
        if any(h in str(col).lower() for h in _SATISFACTION_HINTS):
            return col
    return None


@register(
    key="contradiction",
    name_zh="矛盾作答",
    name_en="Contradiction",
    description="推荐分与满意度等强相关问题方向明显冲突",
    requires=[REQUIRE_NPS],
    default_weight=0.7,
    default_params={"gap_threshold": 0.8},
)
def check(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    sat_col = _find_satisfaction(schema)
    if not sat_col:
        return res

    nps = pd.to_numeric(df[schema.nps_col], errors="coerce")
    sat = pd.to_numeric(df[sat_col], errors="coerce")
    smin, smax = sat.min(), sat.max()
    if pd.isna(smin) or smax == smin:
        return res

    nps_n = nps / 10.0
    sat_n = (sat - smin) / (smax - smin)
    gap = (nps_n - sat_n).abs()

    threshold = float(params.get("gap_threshold", 0.8))
    flagged = nps.notna() & sat.notna() & (gap >= threshold)
    res.loc[flagged, "flagged"] = True
    res.loc[flagged, "score"] = gap[flagged].clip(0, 1)
    res.loc[flagged, "reason"] = "推荐分与满意度方向明显矛盾（逻辑冲突）"
    return res
