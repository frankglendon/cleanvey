# QC Methodology — a layered approach / 分层质检方法

Cleanvey organises checks into layers, cheapest and most certain first. This is
standard data-quality engineering, not a black box: you can see exactly why any
respondent was flagged, and tune any layer independently.

> Cleanvey 把检查按「越确定、越便宜越先跑」分层。每一条命中都有可读理由，每一层都能独立调参。

## The layers / 分层

**Layer 1 — Deterministic structure & logic（确定性结构与逻辑）**
Cheap, certain, no model needed: speeding, straightlining, patterned answers,
out-of-range values, missingness, duplicate respondents, and configurable logic
contradictions (`logic_check`). A hit here is hard evidence.

**Layer 2 — Open-end text quality（开放题文本质量）**
Character/string heuristics on free text: gibberish (incl. low-vowel keyboard
mashing), low-effort "don't know / none", too-short answers, exact duplicates,
and fuzzy near-duplicates. High recall, transparent rules.

**Layer 3 — Cross-question consistency（跨题一致性）**
Answers that conflict with each other — e.g. NPS vs. an overall-satisfaction
item (`contradiction`), or declarative numeric constraints across columns
(`logic_check`).

**Layer 4 — Semantic, optional (LLM)（语义层，可选）**
Only the genuinely ambiguous cases that rules can't settle — off-topic answers,
sentiment that contradicts a score. Activated only when an API key is present;
absent that, the tool runs fully on Layers 1–3.

## Two principles / 两条原则

1. **Rules generate candidates; the model judges.（规则负责高召回候选，模型负责精准判定）**
   Keyword/heuristic rules are tuned for recall — they cast a wide net. The
   optional LLM layer is the judge that adds precision and a written reason.
   Deterministic layers (1–3) may flag for removal on their own; the semantic
   layer only advises.

2. **Never overwrite raw data; only append.（绝不就地改数据，只追加标记）**
   Cleanvey adds QC columns — flag, risk score, risk level, recommendation,
   per-flag reasons — and leaves every original value untouched, so the audit
   trail is complete and reversible.

## Severity & action / 风险分级与处置

| Level | Meaning | Recommended action |
|---|---|---|
| 高 High | strong, usually deterministic evidence | 建议剔除 remove |
| 中 Medium | one or more softer signals | 建议复核 review |
| 低 Low | clean or negligible | 保留 keep |

## Calibration / 校准

Every threshold shipped here is a **neutral default**, chosen to be reasonable
across surveys — not tuned to any particular study. Real projects vary widely
(answer length, scale range, locale, incidence of fraud), so treat thresholds as
starting points and calibrate to each survey's own distribution. See
[`config/default_rules.yaml`](../config/default_rules.yaml) for every knob.

> 这里的每个阈值都是**中性默认值**，只为「跨项目大致合理」，并非针对某个项目调出。
> 请按你自己问卷的分布自行校准。
