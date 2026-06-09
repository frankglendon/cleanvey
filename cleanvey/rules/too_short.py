"""Open-ends that are too short to carry meaning.
开放题过短：短到没有信息量。

Counts *effective* characters (CJK + alphanumeric, ignoring spaces/punctuation)
and flags non-empty answers below a conservative threshold. Kept deliberately
low so genuine brief answers ("battery lasts long") survive — the goal is to
catch one-word filler, not to punish concise honesty. Calibrate per project.
统计“有效字符”（中文 + 字母数字，忽略空格与标点），非空但低于一个保守阈值就标记。
阈值刻意设得低，让真实的简短回答（如“续航久”）不被误伤——目标是抓一两字的敷衍，
而非惩罚言简意赅。请按项目自行校准。
"""
from __future__ import annotations

import re

import pandas as pd

from .base import register, empty_result, REQUIRE_OPENEND

_EFFECTIVE = re.compile(r"[0-9A-Za-z一-鿿]")  # effective chars: CJK + alphanumeric / 有效字符：中文+字母数字


def _eff_len(text) -> int:
    """Count effective characters; blank / NaN counts as 0. / 数有效字符；空与 NaN 记为 0。"""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return 0
    s = str(text).strip()
    if not s or s.lower() == "nan":  # blank == missing, not "short" / 空属于缺失，不算“过短”
        return 0
    return len(_EFFECTIVE.findall(s))


@register(
    key="too_short",
    name_zh="开放题过短",
    name_en="Too short",
    description="开放题有效字符数过少，信息量不足",
    requires=[REQUIRE_OPENEND],
    default_weight=0.3,
    default_params={"min_chars": 4},
)
def check(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    min_chars = int(params.get("min_chars", 4))
    cols = schema.openend_cols
    if not cols:
        return res

    def is_short(v: str) -> bool:
        n = _eff_len(v)
        return 0 < n < min_chars  # 0 == blank, that's "missing", not "short" / 0 是空缺，不算过短

    hit = pd.DataFrame({c: df[c].map(is_short) for c in cols}, index=df.index)
    n_hit = hit.sum(axis=1)
    flagged = n_hit > 0
    res.loc[flagged, "flagged"] = True
    res.loc[flagged, "score"] = 0.3
    res.loc[flagged, "reason"] = n_hit[flagged].map(
        lambda k: f"{int(k)} 道开放题有效字数少于 {min_chars}（信息量不足）"
    )
    return res
