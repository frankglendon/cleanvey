"""Low-effort / non-substantive open-ends.
无信息作答：非空但毫无信息量的开放题。

Answers that are technically non-empty but carry no information — "don't know",
"none", "whatever", "good". Industry-standard QC; the only nuance worth keeping
is **polarity awareness**: on a negative/improvement question ("what could be
better?"), "none" is a perfectly valid answer, so such columns can be exempted.
形式上非空、却毫无信息——“不知道”“没有”“随便”“好”。这是行业标准做法；唯一值得保留的细节是
**极性感知**：在负向/改进类问题（“哪里可以更好？”）里，“没有”是完全合理的回答，可豁免这些列。

The dictionary below is a small, generic starter — extend it (and add other
languages) for your own surveys. No project-tuned content here.
下面的词典只是一个通用的起步集——请按你自己的问卷扩充（并补充其他语言）。这里不含任何项目调优内容。
"""
from __future__ import annotations

import re

import pandas as pd

from .base import register, empty_result, REQUIRE_OPENEND

# Generic, illustrative starter set — calibrate/extend per project & language.
# 通用示例起步集——请按项目与语言自行校准/扩充。
NON_SUBSTANTIVE = {
    "不知道", "不清楚", "没有", "无", "没什么", "随便", "都行", "还行", "还好",
    "一般", "好", "好的", "嗯", "没意见", "不想说", "保密", "略", "暂无",
    "说不上来", "无所谓", "记不住", "没了", "不晓得",
    "none", "not sure", "na", "n/a", "nothing", "good", "nice", "ok", "fine",
}


def _normalize(text: str) -> str:
    """Lower-case, strip, drop trailing punctuation. / 小写、去空白、去尾部标点。"""
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
    exempt = set(params.get("negative_polarity_cols") or [])  # columns where "none" is valid / “没有”合理的列
    cols = [c for c in schema.openend_cols if c not in exempt]
    if not cols:
        return res

    def is_empty_or_low(v: str) -> bool:
        return _normalize(v) in NON_SUBSTANTIVE

    hit = pd.DataFrame({c: df[c].map(is_empty_or_low) for c in cols}, index=df.index)
    # only count columns that actually had a (non-blank) answer / 只统计真正作答（非空）的列
    answered = pd.DataFrame(
        {c: df[c].fillna("").astype(str).str.strip().astype(bool) for c in cols},
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
