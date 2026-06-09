"""Composite risk scoring.

Each rule contributes a 0..1 severity per respondent. We combine them into a
single weighted risk figure, then bucket respondents into 高 / 中 / 低 risk and
attach a recommended action. Weights and thresholds are configurable.
"""
from __future__ import annotations

from typing import Dict

import pandas as pd

LEVEL_HIGH = "高"
LEVEL_MEDIUM = "中"
LEVEL_LOW = "低"

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

    risk_score is the weighted sum of rule severities, capped at 1.0 for a
    clean 0..100% display. Bucketing uses the *raw* (uncapped) sum so that
    stacking several issues pushes a respondent up the scale.
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
