"""Near-duplicate open-ends (fuzzy).

Complements `duplicate_text` (which catches *exact* copy-paste). Here we catch
answers that are highly similar but not identical — lightly reworded boilerplate.
Following standard practice, this is treated as a **review** signal (low
severity), not grounds for removal: short praise like "性价比高" legitimately
collides, so similarity alone should never auto-drop a respondent.

Uses RapidFuzz; bounded by `max_rows` to stay cheap on large datasets.
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
