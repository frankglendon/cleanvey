# 🧹 Cleanvey

**An explainable quality-control toolkit for survey data.**
*问卷数据质量检查工具 —— 规则透明、开箱即用。*

Upload a survey export (Excel/CSV), and Cleanvey auto-detects each column's
role, runs a set of **transparent** quality rules (speeding, straightlining,
patterned answers, contradictions, gibberish, duplicates, missingness,
out-of-range), and produces a per-respondent **risk score + recommended
action**. Every flag comes with a human-readable reason — no black box.

> 上传问卷文件，自动识别列、运行一套**可解释**的质量规则，给出每位受访者的风险等级与处理建议。
> 纯规则模式无需任何 API Key；配置 Key 后可额外启用 LLM 语义检查（答非所问）。

---

## ✨ Features / 功能

- **9 built-in QC rules**, each a small, readable function — easy to audit and extend.
- **Auto column mapping** from names + value patterns; confirm/adjust in the UI.
- **Composite risk score** → 高 / 中 / 低 buckets with a 剔除 / 复核 / 保留 recommendation.
- **Two outputs**: a color-coded Excel detail workbook and a standalone HTML dashboard.
- **Web app *and* CLI** from a single entry point.
- **Optional LLM enhancement** (Anthropic Claude) — degrades gracefully to pure rules with no key.
- **Synthetic demo data** included — try it in 30 seconds, zero real data anywhere.

## 🧭 The rules / 规则一览

| Rule | Catches | How |
|---|---|---|
| 超速作答 Speeding | finished implausibly fast | duration < 34% of median |
| 直线作答 Straightlining | same answer down a scale block | spread of scale items ≈ 0 |
| 模式化作答 Pattern | mechanical 1-2-3-4 / 1-2-1-2 | diffs form a run or zig-zag |
| 矛盾作答 Contradiction | NPS vs. satisfaction conflict | large normalised gap |
| 开放题乱填 Gibberish | keyboard mashing / symbols | char-level heuristics |
| 开放题雷同 Duplicate text | copy-pasted open-ends | normalised exact match |
| 整份雷同 Duplicate respondent | identical whole questionnaires | row signature collision |
| 作答缺失 Missing | too many blanks | missing ratio > 50% |
| 越界数值 Out-of-range | invalid values (e.g. NPS∉0–10) | domain check |
| *答非所问 Off-topic* (LLM) | answer ignores the question | semantic check (optional) |

See [docs/rules.md](docs/rules.md) for the full methodology and thresholds.

---

## 🚀 Quickstart / 快速开始

```bash
# 1. install
pip install -r requirements.txt

# 2. generate the synthetic demo survey (300 rows with seeded issues)
python sample_data/generate_sample.py

# 3a. run from the command line
python app.py check sample_data/demo_survey.xlsx --out report.xlsx

# 3b. or launch the web app, then open http://127.0.0.1:5000
python app.py
```

### Web flow / 网页流程
`上传 Upload → 确认列映射 Map columns → 运行 Run → 查看结果并下载 Result & download`

### CLI
```bash
python app.py check data.xlsx \
  --config config/default_rules.yaml \   # optional: tweak thresholds/weights
  --out report.xlsx \
  --llm                                   # optional: enable semantic checks
```

---

## 🤖 Optional LLM checks / 可选的 LLM 增强

Cleanvey runs **fully without any API key**. To additionally flag *off-topic*
open-ends:

```bash
pip install -r requirements-llm.txt
cp .env.example .env        # then put your ANTHROPIC_API_KEY in .env
```

With no key, the LLM rule is simply skipped and the report says so.

## 🗂 Project structure / 项目结构

```
cleanvey/
├── app.py                  # CLI + Flask web entry point
├── cleanvey/
│   ├── schema.py           # data loading + column mapping
│   ├── engine.py           # run rules -> score respondents
│   ├── scoring.py          # composite risk + 高/中/低 buckets
│   ├── report.py           # Excel + HTML reports
│   ├── llm.py              # optional Claude client (fail-soft)
│   └── rules/              # one file per rule (self-contained)
├── config/default_rules.yaml  # toggle rules, weights, thresholds
├── sample_data/            # synthetic demo generator + xlsx
├── docs/rules.md           # methodology
└── tests/                  # pytest: per-rule + end-to-end
```

## 🧪 Tests / 测试

```bash
pip install pytest && python -m pytest
```
Covers each rule individually plus an end-to-end run that confirms every rule
fires on the seeded demo data.

## 📄 License & data / 许可与数据

MIT License. **All sample data is randomly generated** by
`sample_data/generate_sample.py` and bears no relation to any real respondent,
client, or project.
