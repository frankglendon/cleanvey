"""Generate a synthetic demo survey with known quality problems baked in.

Everything here is randomly generated — no real respondents, clients, or
projects. Each QC issue type is injected into a disjoint block of rows so that
running Cleanvey on the output visibly catches every rule.

Usage:
    python sample_data/generate_sample.py
Produces: sample_data/demo_survey.xlsx
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N = 300

SCALE_COLS = [
    "Q1_产品质量", "Q2_客服服务", "Q3_物流速度",
    "Q4_价格合理", "Q5_使用体验", "Q6_总体满意度",
]
GENDERS = ["男", "女"]
REGIONS = ["华东", "华南", "华北", "华中", "西南", "东北"]

# Wide vocab so independent "normal" answers almost never collide by chance
# (keeps duplicate-text detection meaningful in the demo).
_ADJ = ["性价比", "质量", "服务态度", "物流速度", "包装", "使用体验", "口味", "外观设计",
        "做工", "续航", "性能", "客服响应", "售后", "界面", "音质", "拍照效果"]
_EVAL = ["很不错", "比较满意", "还算可以", "超出预期", "挺好的", "无可挑剔", "令人满意",
         "中规中矩", "略有惊喜", "基本达标", "相当出色", "符合预期", "有点惊艳", "稳定可靠"]
_VERB = ["会回购", "推荐给朋友", "继续支持", "下次还来", "值得购买", "会保持关注", "略有犹豫",
         "还会再观望", "打算长期用", "考虑入手第二件", "已分享给同事", "准备复购"]
_EXTRA = ["希望多搞活动", "期待新品上市", "客服点赞", "发货能再快点", "颜色再多些",
          "整体满意", "暂时没别的", "继续加油", "建议出小份装", "价格再优惠就好",
          "包装可更环保", "增加配件选项", "门店再多些", "保修期望更长"]


def _reason() -> str:
    return f"{RNG.choice(_ADJ)}{RNG.choice(_EVAL)}，{RNG.choice(_VERB)}，{RNG.choice(_EXTRA)}"


def build() -> pd.DataFrame:
    # baseline: everyone starts as a clean, normal respondent
    df = pd.DataFrame({
        "respondent_id": [f"R{1000 + i}" for i in range(N)],
        "duration_sec": np.clip(RNG.normal(200, 55, N), 60, None).round().astype(int),
        "age": RNG.integers(18, 66, N),
        "gender": RNG.choice(GENDERS, N),
        "region": RNG.choice(REGIONS, N),
    })
    for c in SCALE_COLS:
        df[c] = RNG.integers(1, 6, N)

    # Make NPS broadly consistent with overall satisfaction (realistic): a
    # satisfied respondent recommends more. Injected contradictions stand out.
    base = (df["Q6_总体满意度"] - 1) / 4 * 10            # 1..5 -> 0..10
    nps = base + RNG.normal(0, 1.2, N)
    df.insert(2, "nps_score", np.clip(nps, 0, 10).round().astype(int))
    df["open_reason"] = [_reason() for _ in range(N)]
    df["open_suggestion"] = ["" if RNG.random() < 0.3 else _reason() for _ in range(N)]

    obj_cols = ["nps_score", *SCALE_COLS, "age", "gender", "region"]

    # 0-14 speeding
    df.loc[0:14, "duration_sec"] = RNG.integers(5, 25, 15)
    # 15-29 straightlining (all scale items identical)
    for i in range(15, 30):
        df.loc[i, SCALE_COLS] = int(RNG.integers(1, 6))
    # 30-39 pattern (zig-zag)
    for i in range(30, 40):
        df.loc[i, SCALE_COLS] = [1, 3, 1, 3, 1, 3]
    # 40-49 contradiction (top NPS vs lowest satisfaction, and vice-versa)
    for k, i in enumerate(range(40, 50)):
        if k % 2 == 0:
            df.loc[i, "nps_score"] = 10
            df.loc[i, "Q6_总体满意度"] = 1
        else:
            df.loc[i, "nps_score"] = 0
            df.loc[i, "Q6_总体满意度"] = 5
    # 50-61 gibberish open-ends
    junk = ["asdfgh", "。。。。。", "aaaa", "qwerty", "zxcvbn", "！！！！"]
    for i in range(50, 62):
        df.loc[i, "open_reason"] = RNG.choice(junk)
    # 62-71 duplicated open-end text (copy-paste)
    df.loc[62:71, "open_reason"] = "这个产品我用了很久一直都很满意非常推荐大家购买真的很好"
    # 72-79 duplicate respondents (identical objective answers, in pairs)
    for a in range(72, 80, 2):
        df.loc[a + 1, obj_cols] = df.loc[a, obj_cols].values
    # 80-89 missing (blank out most key questions)
    blank_cols = ["nps_score", *SCALE_COLS, "open_reason"]
    for i in range(80, 90):
        df.loc[i, blank_cols] = np.nan
    # 90-94 out-of-range NPS
    df.loc[90:92, "nps_score"] = 99
    df.loc[93:94, "nps_score"] = -1

    return df


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "demo_survey.xlsx")
    df = build()
    df.to_excel(out, index=False)
    print(f"Wrote {len(df)} rows -> {out}")
    print("Injected: speeding(15) straightlining(15) pattern(10) contradiction(10) "
          "gibberish(12) duplicate_text(10) duplicate_respondent(8) missing(10) out_of_range(5)")


if __name__ == "__main__":
    main()
