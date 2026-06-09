"""Speeding: respondents who finished far faster than everyone else.
超速作答：答题速度远快于其他人的受访者。

A common sign of careless or fraudulent answering. We flag durations below a
threshold that is the larger of (a) a fraction of the sample's median duration
and (b) an absolute floor. Severity grows the faster they went.
这是敷衍或造假作答的常见信号。阈值取“样本中位时长的某个比例”与“绝对下限”中的较大者，
低于它就标记；答得越快、严重度越高。
"""
from __future__ import annotations

import pandas as pd

from .base import register, empty_result, REQUIRE_DURATION


@register(
    key="speeding",
    name_zh="超速作答",
    name_en="Speeding",
    description="答题时长远低于正常水平，疑似随意作答",
    requires=[REQUIRE_DURATION],
    default_weight=1.0,
    default_params={"relative_ratio": 0.34, "min_seconds": 0},
)
def check(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    dur = pd.to_numeric(df[schema.duration_col], errors="coerce")
    median = dur.median()

    ratio = params.get("relative_ratio", 0.34)
    floor = params.get("min_seconds", 0) or 0
    # threshold = max(median * ratio, floor) / 阈值取“中位数×比例”与“绝对下限”中较大者
    threshold = max(median * ratio, floor) if pd.notna(median) else floor
    if not threshold or threshold <= 0:
        return res

    flagged = dur.notna() & (dur < threshold)
    res.loc[flagged, "flagged"] = True
    # severity: the further below threshold, the higher / 越低于阈值，严重度越高
    res.loc[flagged, "score"] = (1 - dur[flagged] / threshold).clip(0, 1)
    res.loc[flagged, "reason"] = dur[flagged].map(
        lambda x: f"答题仅 {x:.0f} 秒，低于阈值 {threshold:.0f} 秒（疑似超速）"
    )
    return res
