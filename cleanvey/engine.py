"""The QC engine: run every enabled rule, then score each respondent.

Flow:
  1. For each registered rule, skip it if disabled, if the data lacks the
     columns it needs, or if it's an LLM rule and LLM is off.
  2. Run the rest; collect per-respondent flags / reasons / severities.
  3. Combine severities into a risk score and bucket each respondent.
  4. Build a detail table (original data + QC columns) and a summary dict.

The result is intentionally transparent: every flag carries a human-readable
reason, and the summary lists exactly which rules ran and which were skipped.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import scoring
from .config import default_config
from .rules import REGISTRY

# Prefix for the QC columns we append to the user's data.
QC = "[QC] "


@dataclass
class QCResult:
    detail: pd.DataFrame   # original columns + QC columns
    summary: dict          # counts, hit rates, level distribution, meta
    schema: object


def run_qc(df: pd.DataFrame, schema, config: dict = None, use_llm: bool = False) -> QCResult:
    config = config or default_config()
    rules_cfg = config.get("rules", {})

    weights, rule_scores, flags, reasons = {}, {}, {}, {}
    ran, skipped = [], []

    for key, rule in REGISTRY.items():
        rcfg = rules_cfg.get(key, {})
        if not rcfg.get("enabled", True):
            continue
        if not all(schema.has(req) for req in rule.requires):
            skipped.append({"rule": rule.name_zh, "reason": "数据缺少所需列"})
            continue
        if rule.is_llm and not use_llm:
            skipped.append({"rule": rule.name_zh, "reason": "未启用 LLM（无 API key）"})
            continue

        params = {**rule.default_params, **(rcfg.get("params") or {})}
        try:
            out = rule.func(df, schema, params)
        except Exception as exc:  # one broken rule must not sink the whole run
            skipped.append({"rule": rule.name_zh, "reason": f"运行出错：{exc}"})
            continue

        weights[key] = rcfg.get("weight", rule.default_weight)
        rule_scores[key] = out["score"]
        flags[key] = out["flagged"]
        reasons[key] = out["reason"]
        ran.append(key)

    # --- assemble the detail table -----------------------------------------
    detail = df.copy()
    for key in ran:
        detail[QC + REGISTRY[key].name_zh] = flags[key].map(lambda b: "✓" if b else "")

    if reasons:
        reasons_df = pd.DataFrame(reasons, index=df.index)
        combined = reasons_df.apply(
            lambda row: "；".join([r for r in row.tolist() if r]), axis=1
        )
    else:
        combined = pd.Series("", index=df.index)

    risk, level, rec = scoring.score_respondents(
        rule_scores, weights, config.get("scoring", {}), df.index
    )
    detail[QC + "命中问题"] = combined
    detail[QC + "风险分"] = risk
    detail[QC + "风险等级"] = level
    detail[QC + "处理建议"] = rec

    # --- summary ------------------------------------------------------------
    n = len(df)
    rule_hits = {REGISTRY[k].name_zh: int(flags[k].sum()) for k in ran}
    summary = {
        "total": n,
        "ran_rules": [REGISTRY[k].name_zh for k in ran],
        "skipped_rules": skipped,
        "rule_hits": rule_hits,
        "rule_hit_rates": {name: (hits / n if n else 0) for name, hits in rule_hits.items()},
        "level_counts": {
            scoring.LEVEL_HIGH: int((level == scoring.LEVEL_HIGH).sum()),
            scoring.LEVEL_MEDIUM: int((level == scoring.LEVEL_MEDIUM).sum()),
            scoring.LEVEL_LOW: int((level == scoring.LEVEL_LOW).sum()),
        },
        "flagged_total": int((level != scoring.LEVEL_LOW).sum()),
        "llm_used": use_llm,
    }
    return QCResult(detail=detail, summary=summary, schema=schema)
