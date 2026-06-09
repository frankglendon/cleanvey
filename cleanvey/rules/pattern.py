"""Pattern answering: mechanical sequences across scale questions.

Beyond straightlining, careless respondents often produce tidy patterns:
  - arithmetic runs  (1,2,3,4,5 or 5,4,3,2,1)
  - zig-zags         (1,2,1,2,1 or 5,1,5,1)
We look at the differences between consecutive scale answers (in column order)
and flag rows that match one of these shapes.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from .base import register, empty_result, REQUIRE_SCALE


def _classify(values: np.ndarray) -> Optional[str]:
    """Return a label if the sequence is a mechanical pattern, else None."""
    v = values[~np.isnan(values)]
    if len(v) < 4:
        return None
    diffs = np.diff(v)
    if np.all(diffs == 0):
        return None  # that's straightlining, handled elsewhere

    # arithmetic run: every step identical and non-zero
    if np.all(diffs == diffs[0]) and diffs[0] != 0:
        return "递增/递减序列"

    # zig-zag: steps alternate in sign with (near) constant magnitude
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
