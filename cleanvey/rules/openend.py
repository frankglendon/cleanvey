"""Open-ended text rules: gibberish, duplicate text, and off-topic (LLM).
开放题文本规则：乱码、跨人雷同、答非所问（LLM）。

These target free-text answers, where careless or fraudulent respondents leave
the clearest fingerprints: keyboard mashing, copy-pasted boilerplate, or
answers that simply don't address the question.
这些针对开放题——敷衍或造假的受访者在这里留下的痕迹最明显：键盘乱敲、复制粘贴的套话，
或干脆答非所问。
"""
from __future__ import annotations

import re

import pandas as pd

from .base import register, empty_result, REQUIRE_OPENEND

# --- gibberish detection / 乱码检测 -----------------------------------------

_REPEAT = re.compile(r"^(.)\1{2,}$")            # "aaaa", "。。。" / 单字符重复
_SYMBOLS = re.compile(r"^[\W_]+$", re.UNICODE)  # only punctuation/symbols / 纯标点符号
_KEYBOARD = (
    "asdf", "sdfg", "dfgh", "fghj", "qwer", "wert", "erty", "rtyu",
    "zxcv", "xcvb", "1234", "2345", "3456", "qwerty", "asdfg", "qazwsx",
)


def _is_gibberish(text: str) -> bool:
    """True for clear nonsense; deliberately conservative to avoid false hits
    on short-but-valid answers like '无' / 'none'.
    明显是乱码才返回 True；故意保守，避免误伤“无”“none”这类短但有效的回答。"""
    t = str(text).strip().lower()
    if not t or t == "nan":
        return False  # empty is 'missing', handled by another rule / 空属于缺失，另有规则
    if _REPEAT.match(t):
        return True
    if _SYMBOLS.match(t):
        return True
    compact = re.sub(r"\s+", "", t)
    if any(k in compact for k in _KEYBOARD):
        return True
    # Long Latin string with implausibly few vowels = keyboard mashing
    # (catches things like "dhrjhry" that dodge the keyboard-run list).
    # 长串拉丁字母但元音异常少 = 键盘乱敲（抓“dhrjhry”这类漏过键位表的情形）。
    letters = re.sub(r"[^a-z]", "", t)
    if len(letters) >= 10:
        vowels = sum(c in "aeiou" for c in letters)
        if vowels / len(letters) < 0.25:
            return True
    return False


@register(
    key="gibberish",
    name_zh="开放题乱填",
    name_en="Gibberish",
    description="开放题为乱码、键盘连击或纯符号",
    requires=[REQUIRE_OPENEND],
    default_weight=0.9,
    default_params={},
)
def check_gibberish(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    cols = schema.openend_cols
    if not cols:
        return res
    hit = pd.DataFrame(
        {c: df[c].map(_is_gibberish) for c in cols}, index=df.index
    )
    n_hit = hit.sum(axis=1)
    flagged = n_hit > 0
    res.loc[flagged, "flagged"] = True
    res.loc[flagged, "score"] = (n_hit[flagged] / len(cols)).clip(0, 1)
    res.loc[flagged, "reason"] = n_hit[flagged].map(
        lambda k: f"{int(k)} 道开放题为乱码/键盘连击/纯符号"
    )
    return res


# --- duplicate open-end text / 跨人开放题雷同 -------------------------------

@register(
    key="duplicate_text",
    name_zh="开放题雷同",
    name_en="Duplicate open-end",
    description="开放题文本与其他受访者完全相同（疑似复制粘贴）",
    requires=[REQUIRE_OPENEND],
    default_weight=0.7,
    default_params={"min_len": 8},
)
def check_duplicate_text(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    min_len = int(params.get("min_len", 8))
    flagged = set()

    for col in schema.openend_cols:
        norm = df[col].fillna("").astype(str).map(lambda s: re.sub(r"\s+", "", s.strip().lower()))
        valid = norm.str.len() >= min_len  # ignore short generic answers ("无") / 忽略过短的通用答案
        counts = norm[valid].value_counts()
        dup_values = set(counts[counts >= 2].index)  # texts appearing ≥2 times / 出现≥2次的文本
        for idx in df.index:
            if valid.get(idx, False) and norm[idx] in dup_values:
                flagged.add(idx)

    for idx in flagged:
        res.at[idx, "flagged"] = True
        res.at[idx, "score"] = 0.7
        res.at[idx, "reason"] = "开放题文本与其他受访者完全雷同（疑似复制粘贴）"
    return res


# --- off-topic (LLM-powered) / 答非所问（大模型判官） -----------------------

@register(
    key="offtopic",
    name_zh="答非所问",
    name_en="Off-topic (LLM)",
    description="开放题答案与问题无关（语义判断，需 LLM）",
    requires=[REQUIRE_OPENEND],
    default_weight=0.8,
    default_params={"max_rows": 300},
    is_llm=True,
)
def check_offtopic(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    from ..llm import get_client  # lazy import: keeps the core import-light / 懒加载，避免核心依赖它

    client = get_client()
    if client is None or not client.available:
        return res  # engine also skips LLM rules without a key; double safety / 引擎也会跳过，双保险

    for col in schema.openend_cols:
        answers = df[col].fillna("").astype(str).tolist()
        verdicts = client.classify_offtopic(str(col), answers)
        for idx, off in zip(df.index, verdicts):
            if off:
                res.at[idx, "flagged"] = True
                res.at[idx, "score"] = max(float(res.at[idx, "score"]), 0.8)
                res.at[idx, "reason"] = "开放题答非所问（语义判断）"
    return res
