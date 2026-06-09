"""Low-effort / non-substantive open-ends.

Answers that are technically non-empty but carry no information — "don't know",
"none", "whatever", "good". Industry-standard QC; the only nuance worth keeping
is **polarity awareness**: on a negative/improvement question ("what could be
better?"), "none" is a perfectly valid answer, so such columns can be exempted.

The dictionary below is a small, generic starter — extend it (and add other
languages) for your own surveys. No project-tuned content here.
"""
from __future__ import annotations

import re

import pandas as pd

from .base import register, empty_result, REQUIRE_OPENEND

# Generic, illustrative starter set — calibrate/extend per project & language.
NON_SUBSTANTIVE = {
    "不知道", "不清楚", "没有", "无", "没什么", "随便", "都行", "还行", "还好",
    "一般", "好", "好的", "嗯", "没意见", "不想说", "保密", "略", "暂无",
    "说不上来", "无所谓", "记不住", "没了", "不晓得",
    "none", "not sure", "na", "n/a", "nothing", "good", "nice", "ok", "fine",
}


def _normalize(text: str) -> str:
    t = str(text).strip().lower()
    return re.sub(r"[\s，。、！？.!?,]+$", "", t)


@register(
    key="low_effort",
    name_zh="无信息作答",
    name_en="Low-effort answer",
    description="开放题仅为“不知道/没有/随便”等无信息内容",
    requires=[REQUIRE_OPENEND],
    default_weight=0.5,
    default_params={"negative_polarity_cols": []},
)
def check(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    exempt = set(params.get("negative_polarity_cols") or [])
    cols = [c for c in schema.openend_cols if c not in exempt]
    if not cols:
        return res

    def is_empty_or_low(v: str) -> bool:
        t = _normalize(v)
        return t in NON_SUBSTANTIVE

    hit = pd.DataFrame({c: df[c].map(is_empty_or_low) for c in cols}, index=df.index)
    # only count columns that actually had a (non-blank) answer
    answered = pd.DataFrame(
        {c: df[c].astype(str).str.strip().replace("nan", "").astype(bool) for c in cols},
        index=df.index,
    )
    n_hit = (hit & answered).sum(axis=1)
    flagged = n_hit > 0
    res.loc[flagged, "flagged"] = True
    res.loc[flagged, "score"] = 0.5
    res.loc[flagged, "reason"] = n_hit[flagged].map(
        lambda k: f"{int(k)} 道开放题为无信息作答（不知道/没有/随便等）"
    )
    return res
