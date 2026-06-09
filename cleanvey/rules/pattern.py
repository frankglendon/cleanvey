"""Pattern answering: mechanical sequences across scale questions.
模式化作答：量表答案呈机械的规律序列。

Beyond straightlining, careless respondents often produce tidy patterns:
除了直线作答，敷衍的受访者还常给出规整的模式：
  - arithmetic runs  (1,2,3,4,5 or 5,4,3,2,1)  / 等差序列
  - zig-zags         (1,2,1,2,1 or 5,1,5,1)    / 交替锯齿
We look at the differences between consecutive scale answers (in column order)
and flag rows that match one of these shapes.
我们看相邻量表答案（按列顺序）的差分，命中其中一种形态就标记。
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from .base import register, empty_result, REQUIRE_SCALE


def _classify(values: np.ndarray) -> Optional[str]:
    """Return a label if the sequence is a mechanical pattern, else None.
    若序列是机械模式则返回标签，否则返回 None。"""
    v = values[~np.isnan(values)]
    if len(v) < 4:
        return None
    diffs = np.diff(v)
    if np.all(diffs == 0):
        return None  # that's straightlining, handled elsewhere / 这是直线作答，另有规则处理

    # arithmetic run: every step identical and non-zero / 等差：每步相等且非零
    if np.all(diffs == diffs[0]) and diffs[0] != 0:
        return "递增/递减序列"

    # zig-zag: steps alternate in sign with (near) constant magnitude
    # 锯齿：差分符号交替，且幅度（近似）恒定
    signs = np.sign(diffs)
    if np.all(signs != 0) and np.all(signs[1:] == -signs[:-1]):
        if np.all(np.abs(np.abs(diffs) - abs(diffs[0])) < 1e-9):
            return "交替锯齿序列"

    return None


@register(
    key="pattern",
    name_zh="模式化作答",
    name_en="Pattern answering",
    description="量表答案呈递增、递减或交替等机械规律",
    requires=[REQUIRE_SCALE],
    default_weight=0.8,
    default_params={},
)
def check(df: pd.DataFrame, schema, params: dict) -> pd.DataFrame:
    res = empty_result(df.index)
    vals = df[schema.scale_cols].apply(pd.to_numeric, errors="coerce")

    for idx, row in vals.iterrows():
        label = _classify(row.to_numpy(dtype=float))
        if label:
            res.at[idx, "flagged"] = True
            res.at[idx, "score"] = 0.8
            res.at[idx, "reason"] = f"量表答案为{label}（机械作答）"
    return res
