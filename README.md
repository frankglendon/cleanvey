# 🧹 Cleanvey

[![CI](https://github.com/frankglendon/cleanvey/actions/workflows/ci.yml/badge.svg)](https://github.com/frankglendon/cleanvey/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

> **Catch the junk in survey data before it skews your numbers.**
> 在脏数据拉偏结论之前，先把它揪出来。

Upload a survey export → Cleanvey runs **15 transparent quality checks** and
returns a per-respondent **risk score with a plain-language reason for every
flag**. Seconds instead of hours, consistent instead of gut-feel, auditable
instead of a black box. Works fully offline; an optional AI layer adds semantic
checks when you want them.

---

## 💡 Why it matters / 为什么重要

A meaningful slice of raw survey responses is low quality — bots, speeders,
copy-paste boilerplate, careless straight-lining, contradictory answers. Ship
them into the analysis and **every downstream number (NPS, satisfaction,
segmentation) is quietly wrong** — and the client decisions built on top of it.

Today that cleanup is **manual**: analysts eyeball thousands of open-ends and
scale grids by hand. It's slow, inconsistent between people, and hard to defend
when a client asks *"why did you drop these respondents?"*

**Cleanvey turns that into a repeatable, explainable pass:** every flagged
respondent comes with the exact rule and reason, ready to show a client.

> 问卷原始数据里总有一部分是脏的（机器人、超速、复制粘贴、直线作答、自相矛盾），
> 混进分析就会**悄悄拉偏 NPS、满意度、人群细分**，进而影响客户决策。
> 而现在的清洗多半靠人工肉眼逐条看——慢、因人而异、还难向客户解释。
> Cleanvey 把它变成**可复现、可解释**的一步：每个被标记的样本都附规则与理由，可直接对客户交代。

---

## 📸 See it / 界面预览

| 上传 Upload | 自动识别列 Auto column mapping |
|:---:|:---:|
| ![upload](docs/screenshots/01_upload.png) | ![mapping](docs/screenshots/02_mapping.png) |

**结果与风险报告 / Result & risk report**

![result](docs/screenshots/03_result.png)

---

## 🎯 What this project demonstrates / 这个项目体现了什么

- **Spotting a real, costly problem — and automating it.** Data quality directly
  determines whether a research deliverable is valid. I took a painful manual
  process and made it fast, consistent, and defensible.
  *(发现真实且昂贵的业务痛点，并把人工流程自动化。)*
- **Domain expertise, codified.** 15 named, transparent checks plus a
  configurable logic-constraint engine — the actual methodology of survey QC,
  written down so anyone can audit it.
  *(把市场研究 QC 的实战方法论沉淀成可审计的规则。)*
- **AI used with judgment, not as a gimmick.** Rules do high-recall candidate
  generation; an **optional** LLM acts as the precise "judge" and writes the
  reason. No key? It degrades to pure rules — the tool never breaks.
  *(AI 用在刀刃上：规则高召回、LLM 当判官；没 key 也能跑，绝不崩。)*
- **Engineering that holds up.** Tested in CI across Python 3.10–3.12, compatible
  with pandas 2.x **and** 3.0, pip-installable, explainable by design.
  *(经得起检验的工程：CI、pandas 双版本兼容、可安装、可解释。)*
- **Judgment & integrity.** This public version is fully **desensitized** —
  generic methodology and synthetic data only, with **zero** client names, real
  data, or tuned parameters. I can build in the open *and* protect confidential,
  competitively-sensitive material.
  *(分寸感：完全脱敏，零客户信息/真实数据/调好的参数——既能开放分享，又守住机密。)*

---

## 🧭 How it works / 工作原理

Cleanvey layers its checks cheapest-and-most-certain first, so every flag is
explainable and any layer can be tuned independently:

1. **Structure & logic** — speeding, straight-lining, patterns, duplicates,
   missingness, out-of-range, configurable logic contradictions.
2. **Open-end text quality** — gibberish, low-effort, too-short, repeated-token
   spam, exact / fuzzy / self duplicates.
3. **Cross-question consistency** — NPS vs. satisfaction, declarative constraints.
4. **Semantic (optional, LLM)** — off-topic answers the rules can't settle.

Two principles: **rules generate candidates, the model judges**; and **raw data
is never overwritten — only QC columns are appended**, so the audit trail stays
intact. Full write-up: [docs/methodology.md](docs/methodology.md).

### The 15 checks / 规则一览

| Rule | Catches | How |
|---|---|---|
| 超速作答 Speeding | finished implausibly fast | duration < 34% of median |
| 直线作答 Straightlining | same answer down a scale block | spread of scale items ≈ 0 |
| 模式化作答 Pattern | mechanical 1-2-3-4 / 1-2-1-2 | diffs form a run or zig-zag |
| 矛盾作答 Contradiction | NPS vs. satisfaction conflict | large normalised gap |
| 开放题乱填 Gibberish | keyboard mashing / symbols | char heuristics + vowel ratio |
| 无信息作答 Low-effort | "don't know / none / whatever" | polarity-aware dictionary |
| 开放题过短 Too short | uninformative one-word answers | effective-character count |
| 重复刷屏 Repeated token | "推荐推荐推荐" style spam | multi-char repeat unit |
| 开放题雷同 Duplicate text | copy-pasted open-ends | normalised exact match |
| 近似雷同 Near-duplicate | reworded boilerplate | RapidFuzz similarity (review) |
| 自我重复 Self-duplicate | same text in all of one's open-ends | intra-respondent match |
| 整份雷同 Duplicate respondent | identical whole questionnaires | row signature collision |
| 逻辑矛盾 Logic check | age/income/exclusivity conflicts | configurable constraints |
| 作答缺失 Missing | too many blanks | missing ratio > 50% |
| 越界数值 Out-of-range | invalid values (e.g. NPS∉0–10) | domain check |
| *答非所问 Off-topic* (LLM) | answer ignores the question | semantic check (optional) |

Per-rule logic and thresholds: [docs/rules.md](docs/rules.md).

---

## 🚀 Try it in 30 seconds / 30 秒上手

```bash
pip install -r requirements.txt
python sample_data/generate_sample.py                 # synthetic demo (zero real data)
python app.py check sample_data/demo_survey.xlsx       # CLI: prints a summary, writes report.xlsx
python app.py                                          # or the web app at http://127.0.0.1:5000
```

Web flow: `上传 Upload → 确认列映射 Map columns → 运行 Run → 下载报告 Download`.
Prefer a real command? `pip install -e .` gives you `cleanvey check ...` / `cleanvey web`.

## 🤖 Optional AI layer / 可选 AI 层

Runs **fully without any API key**. To also flag *off-topic* open-ends:

```bash
pip install -r requirements-llm.txt
cp .env.example .env        # add your ANTHROPIC_API_KEY
```

No key → the LLM check is skipped and the report says so.

## 🔧 Under the hood / 工程细节

```
app.py                     # CLI + Flask web entry
cleanvey/                  # the library
  schema.py                #   data loading + auto column mapping
  engine.py / scoring.py   #   run rules -> composite risk -> 高/中/低
  rules/                   #   one small, readable file per rule
  report.py / llm.py       #   Excel+HTML reports / optional Claude client
config/default_rules.yaml  # toggle rules, weights, thresholds
tests/                     # pytest: per-rule + end-to-end
```

- **Tests:** `python -m pytest` — each rule individually + an end-to-end run that
  confirms every rule fires on the seeded demo. Green in CI on Python 3.10–3.12.
- **License & data:** MIT. All sample data is randomly generated by
  `sample_data/generate_sample.py` and bears no relation to any real respondent,
  client, or project.
