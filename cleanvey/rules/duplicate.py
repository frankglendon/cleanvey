"""Duplicate respondents: whole questionnaires that are identical.
整份雷同：整份问卷完全相同的受访者。

Two (or more) submissions with the exact same answers across every objective
question (NPS + scale + categorical) are a strong fraud/bot signal. We build a
signature per row from those columns and flag any signature that appears more
than once. Rows with too few answered questions are ignored to avoid matching
on emptiness.
两份（或更多）在每道客观题（NPS + 量表 + 分类）上答案完全一样，是很强的造假/机器人信号。
我们用这些列为每行生成一个“签名”，签名出现不止一次就标记。作答太少的行会被忽略，
以免靠“都为空”而误判。
"""
from __future__ import annotations

import pandas as pd

from .base import register, empty_result


def _objective_cols(schema) -> list:
    """Objective (choice/numeric) columns used for the signature. / 用于签名的客观题列。"""
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
    sig = sub.fillna("").astype(str).apply(lambda r: "|".join(r.values), axis=1)  # row signature / 行签名

    valid = answered >= min_answered  # enough answered to compare / 作答足够多才参与比较
    counts = sig[valid].value_counts()
    dup_values = set(counts[counts >= 2].index)

    flagged = valid & sig.isin(dup_values)
    res.loc[flagged, "flagged"] = True
    res.loc[flagged, "score"] = 0.9
    res.loc[flagged, "reason"] = "整份问卷答案与其他受访者完全雷同（疑似重复提交）"
    return res
