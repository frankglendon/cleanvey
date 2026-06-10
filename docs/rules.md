# QC Rules — Methodology / 规则方法论

This document explains what each rule detects, how it decides, and the default
thresholds. Every threshold is configurable in
[`config/default_rules.yaml`](../config/default_rules.yaml). Each rule returns,
per respondent: `flagged` (bool), `reason` (text), and `score` (0–1 severity).

本文说明每条规则**检测什么、怎么判定、默认阈值**。所有阈值都可在
[`config/default_rules.yaml`](../config/default_rules.yaml) 中调整。每条规则对每位受访者
返回 `flagged`（是否命中）、`reason`（原因）、`score`（0–1 严重度）。

The composite **risk score** is the weighted sum of rule severities. Buckets:
`>= 0.9 → 高 (剔除)`, `>= 0.4 → 中 (复核)`, else `低 (保留)`.
综合**风险分**是各规则严重度的加权和，分档：`≥ 0.9 → 高（剔除）`、`≥ 0.4 → 中（复核）`、
其余 `低（保留）`。

---

## 1. 超速作答 · Speeding
- **Signal / 信号**: a respondent who finishes far faster than the sample is likely clicking through without reading. 答得远快于样本的人，多半在不读题地点点点。
- **Method / 方法**: flag `duration < max(median × relative_ratio, min_seconds)`. 时长低于「中位数×比例」与「绝对下限」中较大者即标记。
- **Defaults / 默认**: `relative_ratio = 0.34`, `min_seconds = 0`. Severity scales with how far below the threshold they are. 越低于阈值越严重。
- **Needs / 需要**: a duration column. 一个答题时长列。

## 2. 直线作答 · Straightlining
- **Signal / 信号**: identical answers down a block of matrix/Likert items → not reading. 一整组量表都选同一个值 → 没在读题。
- **Method / 方法**: compute the per-row standard deviation of the scale items; flag when `answered >= min_items` and `std <= std_threshold`. 计算每行量表答案的标准差，作答数达标且离散度≤阈值即标记。
- **Defaults / 默认**: `min_items = 3`, `std_threshold = 0.0` (exactly identical). Raise it to tolerate tiny variation. 调高阈值可容忍微小差异。
- **Needs / 需要**: scale columns. 量表题列。

## 3. 模式化作答 · Pattern
- **Signal / 信号**: tidy mechanical sequences (1-2-3-4-5, or zig-zag 1-2-1-2). 规整的机械序列（递增或交替锯齿）。
- **Method / 方法**: take differences between consecutive scale answers (column order); flag an **arithmetic run** (all steps equal & non-zero) or a **zig-zag** (signs alternate, equal magnitude). All-equal is excluded (that's straightlining). 看相邻量表答案的差分：等差或交替锯齿即标记；全相等排除（那是直线）。
- **Needs / 需要**: ≥ 4 scale columns answered. 至少作答 4 道量表题。

## 4. 矛盾作答 · Contradiction
- **Signal / 信号**: answers that conflict — default is NPS vs. an overall-satisfaction item moving in opposite directions. 相互冲突——默认看 NPS 与总体满意度是否反向。
- **Method / 方法**: normalise both to 0–1; flag when `|nps_n − sat_n| >= gap_threshold`. 都归一化到 0–1，差距≥阈值即标记。
- **Defaults / 默认**: `gap_threshold = 0.8`. If no satisfaction item exists, the rule does nothing (no false positives). 没有满意度题就不做（不误报）。
- **Needs / 需要**: an NPS column (and a satisfaction scale item to activate). NPS 列（且需有满意度题才触发）。

## 5. 开放题乱填 · Gibberish
- **Signal / 信号**: keyboard mashing, repeated characters, or pure symbols in free text. 键盘乱敲、单字符重复、纯符号。
- **Method / 方法**: conservative char-level heuristics — repeated single char (`aaaa`), keyboard runs (`asdf`), symbol-only strings, or long low-vowel Latin strings. Short-but-valid answers (`无`, `none`) are **not** flagged. 保守的字符级启发式（含「长串低元音」抓键盘乱敲）；短但有效的回答不标记。
- **Needs / 需要**: open-ended columns. 开放题列。

## 6. 开放题雷同 · Duplicate text
- **Signal / 信号**: copy-pasted open-ends shared across respondents. 跨受访者复制粘贴的开放题。
- **Method / 方法**: normalise text; flag values of length `>= min_len` that appear ≥ 2 times. 文本归一化后，长度达标且出现≥2次的标记。
- **Defaults / 默认**: `min_len = 8` — short generic phrases are ignored so only substantive copy-paste is caught. 忽略过短通用语，只抓实质性复制。
- **Needs / 需要**: open-ended columns. 开放题列。

## 7. 整份雷同 · Duplicate respondent
- **Signal / 信号**: whole questionnaires with identical objective answers → bots / duplicate submissions. 整份客观题完全相同 → 机器人/重复提交。
- **Method / 方法**: build a signature from NPS + scale + categorical answers; flag signatures appearing ≥ 2 times. Rows with `< min_answered` answers are ignored. 用客观题生成签名，重复签名标记；作答太少的行忽略。
- **Defaults / 默认**: `min_answered = 5`.

## 8. 作答缺失 · Missing
- **Signal / 信号**: low completion. 完成度低。
- **Method / 方法**: blank ratio across key columns (NPS + scale + open-end + categorical); flag `ratio > max_missing_ratio`. Severity equals the ratio. 关键题缺失率超阈值即标记；严重度即缺失率。
- **Defaults / 默认**: `max_missing_ratio = 0.5`.

## 9. 越界数值 · Out-of-range
- **Signal / 信号**: values outside a valid domain — the universal case is NPS ∉ 0–10. 取值越界——最通用的是 NPS 不在 0–10。
- **Method / 方法**: range-check the NPS column; optional `extra_ranges: {column: [min, max]}` for other numeric fields. 校验 NPS；可选 `extra_ranges` 校验其他数值列。
- **Defaults / 默认**: `nps_min = 0`, `nps_max = 10`.

## 10. 无信息作答 · Low-effort
- **Signal / 信号**: a non-empty open-end that says nothing — "don't know", "none", "whatever". 非空但毫无信息——“不知道”“没有”“随便”。
- **Method / 方法**: match the normalised answer against a small, generic non-substantive dictionary. **Polarity-aware**: list a column in `negative_polarity_cols` to exempt it (where "none" is a valid reply). 用通用词典匹配；**极性感知**：负向题可在 `negative_polarity_cols` 中豁免。
- **Note / 注**: the dictionary is a generic starter — extend it and add other languages. 词典只是起步集，请按需扩充并补语言。

## 11. 开放题过短 · Too short
- **Signal / 信号**: too few *effective* characters (CJK + alphanumeric) to carry meaning. 有效字符（中文+字母数字）太少，没信息量。
- **Method / 方法**: flag non-empty answers with effective length `< min_chars`. Blank = missing (handled elsewhere), not "short". 非空但有效字数低于阈值即标记；空属于缺失，不算过短。
- **Defaults / 默认**: `min_chars = 4` (conservative, so genuine brief answers survive). Calibrate per project. 保守默认，避免误伤真实简短回答；请按项目校准。

## 12. 近似雷同 · Near-duplicate *(fuzzy / 模糊)*
- **Signal / 信号**: lightly reworded boilerplate shared across respondents (complements exact `duplicate_text`). 改写过的套话（对“逐字相同”的补充）。
- **Method / 方法**: RapidFuzz similarity between substantial open-ends. **Review-only** (low severity) — short praise legitimately collides, so similarity alone never auto-drops. 用 RapidFuzz 算相似度；**仅复核**（低严重度），相似度本身绝不自动剔除。
- **Defaults / 默认**: `similarity = 0.9`, `min_len = 10`, bounded by `max_rows`.

## 13. 逻辑矛盾 · Logic check *(configurable / 可配置)*
- **Signal / 信号**: common-sense contradictions across closed-ended answers — respondent younger than their child, tenure > working life, income mismatch, mutually exclusive options, "dead" contradictions (NPS=0 yet "will definitely recommend"), and skip-logic violations. 封闭题间的常识矛盾——亲子年龄倒挂、工龄超工作年限、收入矛盾、互斥同选、死亡矛盾、跳转逻辑违规。
- **Method / 方法**: declare constraints in config; each fires only if its columns exist (safe across datasets). 在配置里声明约束；列不存在的约束自动跳过（跨数据安全）。Constraint types / 约束类型：
  - `gte_diff` — flag when `a − b < min` / `a − b < min` 即违反
  - `le_cols` — flag when `a > b` / `a > b` 即违反
  - `not_both` — more than one of `cols` answered (mutual exclusivity) / 互斥多选同答
  - `forbidden_combo` — `a ∈ a_in` **and** `b ∈ b_in` (dead contradictions) / 死亡矛盾
  - `requires_answered` — if `if_col ∈ if_in`, `then_col` must be answered / 应答未答
  - `requires_blank` — if `if_col ∈ if_in`, `then_col` must be blank / 应跳过却答
- **Note / 注**: shipped constraints are *illustrative*; declare your own. No project-tuned thresholds. 内置约束只是示例，请自行声明；不含项目调优阈值。

## 14. 重复刷屏 · Repeated token
- **Signal / 信号**: an open-end that is one short token piled up — "推荐推荐推荐推荐". 开放题就是一个短词反复堆砌。
- **Method / 方法**: detect a repeating unit of length ≥ 2 repeated `min_repeats`+ times. Single-character repeats ("好好好") are left to `gibberish`. 检测长度≥2 的单元重复≥N 次；单字符重复归乱码管，二者不重叠。
- **Defaults / 默认**: `min_repeats = 3`.

## 15. 自我重复 · Self-duplicate
- **Signal / 信号**: a respondent pastes the *same* text into several of their own open-ends (distinct from cross-respondent `duplicate_text`). 同一人把相同文本填进自己多个开放题（区别于跨人雷同）。
- **Method / 方法**: compare a respondent's open-ends against each other; flag when ≥ 2 substantial answers (length ≥ `min_len`) are identical. 把同一人的开放题互比，≥2 道够长且相同即标记。
- **Needs / 需要**: ≥ 2 open-ended columns. **Defaults / 默认**: `min_len = 4`. 至少两道开放题。

## 16. 答非所问 · Off-topic *(LLM judge / 大模型判官)*
- **Signal / 信号**: an open-end that doesn't address the question. 开放题没在回答这道题。
- **Method / 方法**: the semantic layer — batched classification by an LLM judge (Anthropic Claude) that returns a verdict + reason. Configure `ANTHROPIC_API_KEY` to run it; can be turned off via `offtopic.enabled: false`. 语义层——大模型判官批量分类并给出判定+理由；配 `ANTHROPIC_API_KEY` 启用，可用 `offtopic.enabled: false` 关闭。
- **Needs / 需要**: open-ended columns + `ANTHROPIC_API_KEY`. 开放题列 + API key。

---

### Tuning tips / 调参建议
- Over-flagging? Raise the relevant threshold or lower the rule's `weight`. 误报多？调高阈值或降低该规则 `weight`。
- Want a rule off? Set `enabled: false`. 想关掉某条规则？设 `enabled: false`。
- Different scale range (e.g. 1–7)? The scale rules adapt automatically; only `out_of_range` hard-codes the NPS domain. 量表是 1–7 等其他范围？量表规则自动适应；只有 `out_of_range` 写死了 NPS 范围。
