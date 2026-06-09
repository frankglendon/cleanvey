"""Near-duplicate open-ends (fuzzy).
开放题近似雷同（模糊匹配）。

Complements `duplicate_text` (which catches *exact* copy-paste). Here we catch
answers that are highly similar but not identical — lightly reworded boilerplate.
Following standard practice, this is treated as a **review** signal (low
severity), not grounds for removal: short praise like "性价比高" legitimately
collides, so similarity alone should never auto-drop a respondent.
对 `duplicate_text`（抓“逐字相同”）的补充。这里抓高度相似但不完全相同的回答——
改写过的套话。按惯例只作为“**复核**”信号（低严重度），不作为剔除依据：短好评（“性价比高”）
天然会撞车，所以仅凭相似度绝不自动剔除。

Uses RapidFuzz; bounded by `max_rows` to stay cheap on large datasets.
用 RapidFuzz；以 `max_rows` 设界，保证在大数据上也不慢。
"""
from __future__ import annotations

import re

import pandas as pd
from rapidfuzz import fuzz

from .base import register, empty_result, REQUIRE_OPENEND


@register(
    key="near_duplicate",
    name_zh="近似雷同",
    name_en="Near-duplicate text",
    description="开放题与他人高度相似（非逐字相同）——建议复核",
    requires=[REQUIRE_OPENEND],
    default_weight=0.4,
    default_params={"similarity": 0.9, "min_len": 10, "max_rows": 2000},
)
def check(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    thr = float(params.get("similarity", 0.9)) * 100
    min_len = int(params.get("min_len", 10))
    max_rows = int(params.get("max_rows", 2000))
    flagged = set()

    for col in schema.openend_cols:
        norm = df[col].fillna("").astype(str).map(lambda s: re.sub(r"\s+", "", s.strip().lower()))
        # group identical texts; only compare *distinct* substantial texts
        # 把完全相同的文本归组；只对“不同的、够长的”文本两两比较
        groups: dict = {}
        for idx in df.index:
            t = norm[idx]
            if len(t) >= min_len:
                groups.setdefault(t, []).append(idx)
        uniq = list(groups.keys())
        if len(uniq) < 2 or sum(len(v) for v in groups.values()) > max_rows:
            continue
        for i in range(len(uniq)):
            for j in range(i + 1, len(uniq)):
                if fuzz.ratio(uniq[i], uniq[j]) >= thr:
                    flagged.update(groups[uniq[i]])
                    flagged.update(groups[uniq[j]])

    for idx in flagged:
        res.at[idx, "flagged"] = True
        res.at[idx, "score"] = 0.4
        res.at[idx, "reason"] = "开放题与他人高度相似（建议复核）"
    return res
