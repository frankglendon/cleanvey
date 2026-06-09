"""Rule interface and registry. / 规则接口与注册表。

Every QC rule is a small function with a uniform signature:
每条 QC 规则都是一个签名统一的小函数：

    func(df, schema, params) -> pandas.DataFrame

The returned frame shares the input's index and has exactly three columns:
返回的 DataFrame 与输入同 index，固定三列：

    flagged : bool   did this respondent trip the rule? / 该受访者是否命中
    reason  : str    human-readable explanation / 人类可读的原因（未命中为空串）
    score   : float  0..1 severity of the issue / 0~1 的严重度（未命中为 0）

Rules register themselves with `@register(...)`, so the engine can discover
them, check whether the current data supports them, and run the enabled ones.
规则用 `@register(...)` 自注册，引擎据此发现规则、判断数据是否支持、并运行启用的规则。
This keeps each rule self-contained and easy to read — the whole point of the
project is that the checks are transparent, not a black box.
这样每条规则都自包含、易读——本项目的核心就是让检查透明、而非黑箱。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

import pandas as pd

# Schema field names a rule may require (the engine skips a rule when the
# mapped data lacks what it needs).
# 规则可能依赖的 schema 字段名（数据缺这些时，引擎会跳过该规则）。
REQUIRE_ID = "id_col"
REQUIRE_NPS = "nps_col"
REQUIRE_SCALE = "scale_cols"
REQUIRE_OPENEND = "openend_cols"
REQUIRE_DURATION = "duration_col"


@dataclass
class Rule:
    key: str                       # stable id, e.g. "speeding" / 稳定标识，如 "speeding"
    name_zh: str                   # display name (Chinese UI) / 中文界面显示名
    name_en: str                   # display name (English) / 英文显示名
    description: str               # one-line explanation / 一句话说明检测什么
    func: Callable                 # func(df, schema, params) -> DataFrame
    requires: List[str] = field(default_factory=list)
    default_weight: float = 1.0    # contribution to the risk score / 对风险分的权重
    default_params: Dict = field(default_factory=dict)
    is_llm: bool = False           # needs an LLM (skipped without a key) / 需要大模型（无 key 时跳过）


REGISTRY: Dict[str, Rule] = {}


def register(key, name_zh, name_en, description,
             requires=None, default_weight=1.0,
             default_params=None, is_llm=False):
    """Decorator that adds a rule function to the global registry.
    把一个规则函数登记到全局注册表的装饰器。"""
    def deco(func: Callable) -> Callable:
        REGISTRY[key] = Rule(
            key=key, name_zh=name_zh, name_en=name_en,
            description=description, func=func,
            requires=requires or [], default_weight=default_weight,
            default_params=default_params or {}, is_llm=is_llm,
        )
        return func
    return deco


def empty_result(index) -> pd.DataFrame:
    """A 'nothing flagged' result frame aligned to `index`.
    与 `index` 对齐的“全部未命中”结果表。"""
    return pd.DataFrame(
        {"flagged": False, "reason": "", "score": 0.0},
        index=index,
    )
