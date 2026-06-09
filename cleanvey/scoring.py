"""Composite risk scoring. / 综合风险打分。

Each rule contributes a 0..1 severity per respondent. We combine them into a
single weighted risk figure, then bucket respondents into 高 / 中 / 低 risk and
attach a recommended action. Weights and thresholds are configurable.
每条规则对每位受访者给出 0~1 的严重度。把它们加权合成一个风险值，再把受访者分到
高 / 中 / 低三档，并给出处理建议。权重与阈值均可配置。
"""
from __future__ import annotations

from typing import Dict

import pandas as pd

LEVEL_HIGH = "高"
LEVEL_MEDIUM = "中"
LEVEL_LOW = "低"

# Recommended action per risk level. / 各风险档对应的处理建议。
_RECOMMENDATION = {
    LEVEL_HIGH: "建议剔除",
    LEVEL_MEDIUM: "建议复核",
    LEVEL_LOW: "保留",
}


def score_respondents(
    rule_scores: Dict[str, pd.Series],
    weights: Dict[str, float],
    thresholds: Dict[str, float],
    index: pd.Index,
):
    """Return (risk_score, level, recommendation), each a Series on `index`.
    返回 (风险分, 风险等级, 处理建议)，三者都是对齐 `index` 的 Series。

    risk_score is the weighted sum of rule severities, capped at 1.0 for a
    clean 0..100% display. Bucketing uses the *raw* (uncapped) sum so that
    stacking several issues pushes a respondent up the scale.
    风险分是各规则严重度的加权和，展示时封顶到 1.0（0~100%）；但分档用未封顶的原始和，
    这样命中的问题越多、档位越高。
    """
    raw = pd.Series(0.0, index=index)
    for key, severity in rule_scores.items():
        w = float(weights.get(key, 1.0))
        raw = raw.add(severity.reindex(index).fillna(0.0) * w, fill_value=0.0)

    high = float(thresholds.get("high", 0.9))
    medium = float(thresholds.get("medium", 0.4))

    level = pd.Series(LEVEL_LOW, index=index)
    level[raw >= medium] = LEVEL_MEDIUM
    level[raw >= high] = LEVEL_HIGH

    recommendation = level.map(_RECOMMENDATION)
    risk_score = raw.clip(upper=1.0).round(3)
    return risk_score, level, recommendation
