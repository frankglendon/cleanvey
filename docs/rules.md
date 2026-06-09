# QC Rules — Methodology / 规则方法论

This document explains what each rule detects, how it decides, and the default
thresholds. Every threshold is configurable in
[`config/default_rules.yaml`](../config/default_rules.yaml). Each rule returns,
per respondent: `flagged` (bool), `reason` (text), and `score` (0–1 severity).

> 本文说明每条规则**检测什么、怎么判定、默认阈值**。所有阈值都可在
> `config/default_rules.yaml` 中调整。

The composite **risk score** is the weighted sum of rule severities. Buckets:
`>= 0.9 → 高 (剔除)`, `>= 0.4 → 中 (复核)`, else `低 (保留)`.

---

## 1. 超速作答 · Speeding
- **Signal**: a respondent who finishes far faster than the sample is likely clicking through without reading.
- **Method**: flag `duration < max(median × relative_ratio, min_seconds)`.
- **Defaults**: `relative_ratio = 0.34`, `min_seconds = 0`. Severity scales with how far below the threshold they are.
- **Needs**: a duration column.

## 2. 直线作答 · Straightlining
- **Signal**: identical answers down a block of matrix/Likert items → not reading.
- **Method**: compute the per-row standard deviation of the scale items; flag when `answered >= min_items` and `std <= std_threshold`.
- **Defaults**: `min_items = 3`, `std_threshold = 0.0` (exactly identical). Raise the threshold to tolerate tiny variation.
- **Needs**: scale columns.

## 3. 模式化作答 · Pattern
- **Signal**: tidy mechanical sequences (1-2-3-4-5, or zig-zag 1-2-1-2).
- **Method**: take differences between consecutive scale answers (column order). Flag an **arithmetic run** (all steps equal & non-zero) or a **zig-zag** (signs alternate, equal magnitude). All-equal is excluded (that's straightlining).
- **Needs**: ≥ 4 scale columns answered.

## 4. 矛盾作答 · Contradiction
- **Signal**: answers that conflict — shipped default is NPS vs. an overall-satisfaction item moving in opposite directions.
- **Method**: normalise both to 0–1; flag when `|nps_n − sat_n| >= gap_threshold`.
- **Defaults**: `gap_threshold = 0.8`. If no satisfaction item exists, the rule does nothing (no false positives).
- **Needs**: an NPS column (and a satisfaction scale item to activate).

## 5. 开放题乱填 · Gibberish
- **Signal**: keyboard mashing, repeated characters, or pure symbols in free text.
- **Method**: conservative char-level heuristics — repeated single char (`aaaa`), keyboard runs (`asdf`, `qwerty`), or symbol-only strings. Short-but-valid answers (`无`, `none`) are **not** flagged.
- **Needs**: open-ended columns.

## 6. 开放题雷同 · Duplicate text
- **Signal**: copy-pasted open-ends shared across respondents.
- **Method**: normalise text (strip/lower/whitespace); flag values of length `>= min_len` that appear ≥ 2 times.
- **Defaults**: `min_len = 8` — short generic phrases are ignored so only substantive copy-paste is caught.
- **Needs**: open-ended columns.

## 7. 整份雷同 · Duplicate respondent
- **Signal**: whole questionnaires with identical objective answers → bots / duplicate submissions.
- **Method**: build a signature from NPS + scale + categorical answers; flag signatures appearing ≥ 2 times. Rows with `< min_answered` answers are ignored (so emptiness doesn't match).
- **Defaults**: `min_answered = 5`.

## 8. 作答缺失 · Missing
- **Signal**: low completion.
- **Method**: blank ratio across key columns (NPS + scale + open-end + categorical); flag `ratio > max_missing_ratio`. Severity equals the ratio.
- **Defaults**: `max_missing_ratio = 0.5`.

## 9. 越界数值 · Out-of-range
- **Signal**: values outside a valid domain — the universal case is NPS ∉ 0–10.
- **Method**: range-check the NPS column; optional `extra_ranges: {column: [min, max]}` for other numeric fields.
- **Defaults**: `nps_min = 0`, `nps_max = 10`.

## 10. 无信息作答 · Low-effort
- **Signal**: a non-empty open-end that says nothing — "don't know", "none", "whatever".
- **Method**: match the normalised answer against a small, generic non-substantive dictionary. **Polarity-aware**: list a question's column in `negative_polarity_cols` to exempt it (where "none" is a valid reply to "what could be better?").
- **Note**: the dictionary is a generic starter — extend it and add other languages for your surveys.

## 11. 开放题过短 · Too short
- **Signal**: too few *effective* characters (CJK + alphanumeric) to carry meaning.
- **Method**: flag non-empty answers with effective length `< min_chars`. Blank = missing (handled elsewhere), not "short".
- **Defaults**: `min_chars = 4` (conservative, so genuine brief answers survive). Calibrate per project.

## 12. 近似雷同 · Near-duplicate *(fuzzy)*
- **Signal**: lightly reworded boilerplate shared across respondents (complements exact `duplicate_text`).
- **Method**: RapidFuzz similarity between substantial open-ends. **Review-only** (low severity) — short praise legitimately collides, so similarity alone never auto-drops.
- **Defaults**: `similarity = 0.9`, `min_len = 10`, bounded by `max_rows`.

## 13. 逻辑矛盾 · Logic check *(configurable)*
- **Signal**: common-sense contradictions across closed-ended answers — respondent younger than their child, tenure > working life, income mismatch, mutually exclusive options, "dead" contradictions (NPS=0 yet "will definitely recommend"), and skip-logic violations.
- **Method**: declare constraints in config; each fires only if its columns exist (safe across datasets). Constraint types:
  - `gte_diff` — flag when `a − b < min`
  - `le_cols` — flag when `a > b`
  - `not_both` — flag when more than one of `cols` is answered (mutual exclusivity)
  - `forbidden_combo` — flag when `a ∈ a_in` **and** `b ∈ b_in` (dead contradictions)
  - `requires_answered` — if `if_col ∈ if_in`, then `then_col` must be answered (else flag)
  - `requires_blank` — if `if_col ∈ if_in`, then `then_col` must be blank (else flag)
- **Note**: shipped constraints are *illustrative*; declare your own. No project-tuned thresholds.

## 14. 重复刷屏 · Repeated token
- **Signal**: an open-end that is one short token piled up — "推荐推荐推荐推荐", "好的好的好的好的".
- **Method**: detect a repeating unit of length ≥ 2 repeated `min_repeats`+ times. Single-character repeats ("好好好") are left to `gibberish`, so the two never double-count.
- **Defaults**: `min_repeats = 3`.

## 15. 自我重复 · Self-duplicate
- **Signal**: a respondent pastes the *same* text into several of their own open-ends (distinct from cross-respondent `duplicate_text`).
- **Method**: compare a respondent's open-ends against each other; flag when ≥ 2 substantial answers (length ≥ `min_len`) are identical.
- **Needs**: ≥ 2 open-ended columns. **Defaults**: `min_len = 4`.

## 16. 答非所问 · Off-topic *(optional, LLM)*
- **Signal**: an open-end that doesn't address the question.
- **Method**: batched semantic classification via Anthropic Claude. **Skipped entirely** without an API key; the report notes it was not run.
- **Needs**: open-ended columns + `ANTHROPIC_API_KEY`.

---

### Tuning tips / 调参建议
- Over-flagging? Raise the relevant threshold or lower the rule's `weight`.
- Want a rule off? Set `enabled: false`.
- Different scale range (e.g. 1–7)? The scale rules adapt automatically; only `out_of_range` hard-codes the NPS domain.
