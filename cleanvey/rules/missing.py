"""Missingness: respondents who left too many key questions blank.

Low completion is a basic quality signal. We count blanks across the mapped
question columns (NPS + scale + open-ended + categorical) and flag rows whose
missing ratio exceeds a threshold. Severity equals the missing ratio.
"""
from __future__ import annotations

import pandas as pd

from .base import register, empty_result


def _question_columns(schema) -> list:
    cols = []
    if schema.nps_col:
        cols.append(schema.nps_col)
    cols += list(schema.scale_cols)
    cols += list(schema.openend_cols)
    cols += list(schema.categorical_cols)
    return cols


@register(
    key="missing",
    name_zh="作答缺失",
    name_en="Missing answers",
    description="关键问题留空过多，完成度低",
    requires=[],
    default_weight=0.6,
    default_params={"max_missing_ratio": 0.5},
)
def check(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    cols = _question_columns(schema)
    if not cols:
        return res

    threshold = float(params.get("max_missing_ratio", 0.5))
    sub = df[cols]
    blank = sub.isna() | (sub.astype(str).apply(lambda s: s.str.strip()) == "")
    ratio = blank.sum(axis=1) / len(cols)

    flagged = ratio > threshold
    res.loc[flagged, "flagged"] = True
    res.loc[flagged, "score"] = ratio[flagged].clip(0, 1)
    res.loc[flagged, "reason"] = ratio[flagged].map(
        lambda r: f"{r:.0%} 的关键问题未作答（完成度低）"
    )
    return res
