"""Logic / consistency checks across closed-ended answers.

A generic, declarative framework for the kind of common-sense contradictions any
QC analyst checks by hand — respondent younger than their child, tenure longer
than a working life, personal income above household income, mutually exclusive
options both selected. You declare constraints in config; a constraint whose
columns are absent is silently skipped, so the same config is safe across
datasets.

Supported constraint types:
  - gte_diff        : flag when (a - b) < min        e.g. age - child_age >= 16
  - le_cols         : flag when a > b                e.g. personal <= household income
  - not_both        : flag when >1 of `cols` is set  mutually exclusive options
  - forbidden_combo : flag when a∈a_in AND b∈b_in    "dead" contradictions
                      e.g. NPS=0 but intent="will definitely recommend"
  - requires_answered: if if_col∈if_in, then_col must be answered (skip-logic)
  - requires_blank   : if if_col∈if_in, then_col must be blank     (skip-logic)

The shipped defaults are *illustrative* and only fire if matching columns exist.
No project-specific thresholds.
"""
from __future__ import annotations

import pandas as pd

from .base import register, empty_result


def _in_set(series: pd.Series, values) -> pd.Series:
    """Membership test robust to numeric/string representation."""
    str_targets = {str(v).strip() for v in values}
    num_targets = set()
    for v in values:
        try:
            num_targets.add(float(v))
        except (TypeError, ValueError):
            pass
    by_str = series.astype(str).str.strip().isin(str_targets)
    by_num = pd.to_numeric(series, errors="coerce").isin(num_targets)
    return by_str | by_num


def _is_blank(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype(str).str.strip().replace("nan", "") == "")

_DEFAULT_CONSTRAINTS = [
    {"type": "gte_diff", "a": "age", "b": "child_age", "min": 16,
     "label": "受访者与子女年龄差不合常理"},
    {"type": "le_cols", "a": "personal_income", "b": "household_income",
     "label": "个人收入高于家庭总收入"},
]


def _violation(df: pd.DataFrame, c: dict):
    """Return a boolean Series (True = violates) or None if columns missing."""
    t = c.get("type")
    if t == "gte_diff":
        a, b = c["a"], c["b"]
        if a not in df or b not in df:
            return None
        va, vb = pd.to_numeric(df[a], errors="coerce"), pd.to_numeric(df[b], errors="coerce")
        return va.notna() & vb.notna() & ((va - vb) < c.get("min", 0))
    if t == "le_cols":
        a, b = c["a"], c["b"]
        if a not in df or b not in df:
            return None
        va, vb = pd.to_numeric(df[a], errors="coerce"), pd.to_numeric(df[b], errors="coerce")
        return va.notna() & vb.notna() & (va > vb)
    if t == "not_both":
        cols = [col for col in c.get("cols", []) if col in df]
        if len(cols) < 2:
            return None
        selected = sum((~_is_blank(df[col])).astype(int) for col in cols)
        return selected > 1
    if t == "forbidden_combo":
        a, b = c["a"], c["b"]
        if a not in df or b not in df:
            return None
        return _in_set(df[a], c.get("a_in", [])) & _in_set(df[b], c.get("b_in", []))
    if t == "requires_answered":
        ic, tc = c["if_col"], c["then_col"]
        if ic not in df or tc not in df:
            return None
        return _in_set(df[ic], c.get("if_in", [])) & _is_blank(df[tc])
    if t == "requires_blank":
        ic, tc = c["if_col"], c["then_col"]
        if ic not in df or tc not in df:
            return None
        return _in_set(df[ic], c.get("if_in", [])) & ~_is_blank(df[tc])
    return None


@register(
    key="logic_check",
    name_zh="逻辑矛盾",
    name_en="Logic check",
    description="封闭题之间或与人口属性的常识性矛盾（可配置）",
    requires=[],
    default_weight=0.8,
    default_params={"constraints": _DEFAULT_CONSTRAINTS},
)
def check(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    reasons = {i: [] for i in df.index}
    any_hit = pd.Series(False, index=df.index)

    for c in params.get("constraints", []):
        bad = _violation(df, c)
        if bad is None:
            continue
        any_hit = any_hit | bad
        label = c.get("label", c.get("type", "逻辑矛盾"))
        for i in df.index[bad]:
            reasons[i].append(label)

    res.loc[any_hit, "flagged"] = True
    res.loc[any_hit, "score"] = 0.8
    for i in df.index[any_hit]:
        res.at[i, "reason"] = "；".join(reasons[i])
    return res
