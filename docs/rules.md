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

## 10. 答非所问 · Off-topic *(optional, LLM)*
- **Signal**: an open-end that doesn't address the question.
- **Method**: batched semantic classification via Anthropic Claude. **Skipped entirely** without an API key; the report notes it was not run.
- **Needs**: open-ended columns + `ANTHROPIC_API_KEY`.

---

### Tuning tips / 调参建议
- Over-flagging? Raise the relevant threshold or lower the rule's `weight`.
- Want a rule off? Set `enabled: false`.
- Different scale range (e.g. 1–7)? The scale rules adapt automatically; only `out_of_range` hard-codes the NPS domain.
