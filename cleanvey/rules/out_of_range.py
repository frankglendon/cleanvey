"""Out-of-range: values that fall outside a question's valid domain.
越界数值：取值超出该题合法范围。

The clearest universal case is the NPS score, which must be an integer in
0..10. Anything else is a data error (bad export, coding mistake, tampering).
Optional `extra_ranges` lets users declare {column: [min, max]} for other
numeric fields.
最通用、最明确的例子是 NPS：必须是 0..10 的整数，越界即数据错误（导出问题、编码错误或篡改）。
可选参数 `extra_ranges` 允许为其他数值列声明 {列名: [最小, 最大]}。
"""
from __future__ import annotations

import pandas as pd

from .base import register, empty_result, REQUIRE_NPS


@register(
    key="out_of_range",
    name_zh="越界数值",
    name_en="Out-of-range value",
    description="数值超出合法取值范围（如 NPS 不在 0–10）",
    requires=[REQUIRE_NPS],
    default_weight=0.7,
    default_params={"nps_min": 0, "nps_max": 10, "extra_ranges": {}},
)
def check(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    lo = params.get("nps_min", 0)
    hi = params.get("nps_max", 10)

    nps = pd.to_numeric(df[schema.nps_col], errors="coerce")
    bad = nps.notna() & ((nps < lo) | (nps > hi))

    # optional extra numeric ranges declared by the user / 用户声明的额外数值范围
    for col, (cmin, cmax) in (params.get("extra_ranges") or {}).items():
        if col in df.columns:
            v = pd.to_numeric(df[col], errors="coerce")
            bad = bad | (v.notna() & ((v < cmin) | (v > cmax)))

    res.loc[bad, "flagged"] = True
    res.loc[bad, "score"] = 1.0
    res.loc[bad, "reason"] = f"存在超出合法范围的数值（NPS 应为 {lo}–{hi}）"
    return res
