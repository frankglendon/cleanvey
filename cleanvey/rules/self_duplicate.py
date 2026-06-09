"""Self-duplicate: one respondent pastes the same text into several of their
own open-ends.
自我重复：同一受访者把相同文本填进自己多个开放题。

A lazy or automated respondent often drops the identical answer into every
free-text box. This is distinct from `duplicate_text` (which compares *across*
respondents) — here we compare a respondent's open-ends against each other.
Needs at least two open-ended columns.
懒人或机器人常把同一段答案塞进每个开放题框。这与 `duplicate_text`（跨受访者比较）不同——
这里是把同一受访者的多个开放题互相比较。至少需要两道开放题。
"""
from __future__ import annotations

import re
from collections import Counter

import pandas as pd

from .base import register, empty_result, REQUIRE_OPENEND


@register(
    key="self_duplicate",
    name_zh="自我重复",
    name_en="Self-duplicate open-end",
    description="同一受访者把相同文本填进自己的多个开放题",
    requires=[REQUIRE_OPENEND],
    default_weight=0.6,
    default_params={"min_len": 4},
)
def check(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    cols = schema.openend_cols
    if len(cols) < 2:
        return res  # need at least two open-ends to compare / 至少两道开放题才能互比
    min_len = int(params.get("min_len", 4))

    norm = {
        c: df[c].fillna("").astype(str).map(lambda s: re.sub(r"\s+", "", s.strip().lower()))
        for c in cols
    }
    for idx in df.index:
        vals = [norm[c][idx] for c in cols]
        vals = [v for v in vals if len(v) >= min_len]  # ignore trivially short / 忽略过短文本
        counts = Counter(vals)
        repeats = max(counts.values()) if counts else 0
        if repeats >= 2:
            res.at[idx, "flagged"] = True
            res.at[idx, "score"] = 0.6
            res.at[idx, "reason"] = f"{repeats} 道开放题填写了完全相同的文本（自我复制）"
    return res
