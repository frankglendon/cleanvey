"""The QC engine: run every enabled rule, then score each respondent.
QC 引擎：运行每条启用的规则，再为每个受访者打分。

Flow / 流程:
  1. For each registered rule, skip it if disabled, if the data lacks the
     columns it needs, or if it's an LLM rule and LLM is off.
     遍历每条注册规则；若被禁用、数据缺所需列、或是 LLM 规则但未启用，则跳过。
  2. Run the rest; collect per-respondent flags / reasons / severities.
     运行其余规则，收集每位受访者的命中 / 原因 / 严重度。
  3. Combine severities into a risk score and bucket each respondent.
     把严重度合成风险分，并给每位受访者分档。
  4. Build a detail table (original data + QC columns) and a summary dict.
     生成明细表（原数据 + QC 列）与一个汇总字典。

The result is intentionally transparent: every flag carries a human-readable
reason, and the summary lists exactly which rules ran and which were skipped.
结果刻意做到透明：每个标记都附可读理由，汇总里明确列出哪些规则跑了、哪些被跳过。
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import scoring
from .config import default_config
from .rules import REGISTRY

# Prefix for the QC columns we append to the user's data. / 追加到用户数据上的 QC 列前缀。
QC = "[QC] "


@dataclass
class QCResult:
    detail: pd.DataFrame   # original columns + QC columns / 原始列 + QC 列
    summary: dict          # counts, hit rates, level distribution, meta / 计数、命中率、风险分布等
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
        except Exception as exc:  # one broken rule must not sink the whole run / 单条规则出错不拖垮整体
            skipped.append({"rule": rule.name_zh, "reason": f"运行出错：{exc}"})
            continue

        weights[key] = rcfg.get("weight", rule.default_weight)
        rule_scores[key] = out["score"]
        flags[key] = out["flagged"]
        reasons[key] = out["reason"]
        ran.append(key)

    # --- assemble the detail table / 组装明细表 ---------------------------- #
    detail = df.copy()
    for key in ran:
        detail[QC + REGISTRY[key].name_zh] = flags[key].map(lambda b: "✓" if b else "")

    if reasons:
        # join all per-rule reasons for each respondent / 把每位受访者命中的各条原因拼在一起
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

    # --- summary / 汇总 -------------------------------------------------- #
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
