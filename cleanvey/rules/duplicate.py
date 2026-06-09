"""Duplicate respondents: whole questionnaires that are identical.

Two (or more) submissions with the exact same answers across every objective
question (NPS + scale + categorical) are a strong fraud/bot signal. We build a
signature per row from those columns and flag any signature that appears more
than once. Rows with too few answered questions are ignored to avoid matching
on emptiness.
"""
from __future__ import annotations

import pandas as pd

from .base import register, empty_result


def _objective_cols(schema) -> list:
    cols = []
    if schema.nps_col:
        cols.append(schema.nps_col)
    cols += list(schema.scale_cols)
    cols += list(schema.categorical_cols)
    return cols


@register(
    key="duplicate_respondent",
    name_zh="整份雷同",
    name_en="Duplicate respondent",
    description="整份问卷答案与其他受访者完全相同（疑似刷单/机器人）",
    requires=[],
    default_weight=0.9,
    default_params={"min_answered": 5},
)
def check(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    cols = _objective_cols(schema)
    min_answered = int(params.get("min_answered", 5))
    if len(cols) < min_answered:
        return res

    sub = df[cols]
    answered = sub.notna().sum(axis=1)
    sig = sub.astype(str).apply(lambda r: "|".join(r.values), axis=1)

    valid = answered >= min_answered
    counts = sig[valid].value_counts()
    dup_values = set(counts[counts >= 2].index)

    flagged = valid & sig.isin(dup_values)
    res.loc[flagged, "flagged"] = True
    res.loc[flagged, "score"] = 0.9
    res.loc[flagged, "reason"] = "整份问卷答案与其他受访者完全雷同（疑似重复提交）"
    return res
