<div align="center">

# 🧹 Cleanvey

**Catch the junk in survey data before it skews your numbers.**

[![CI](https://github.com/frankglendon/cleanvey/actions/workflows/ci.yml/badge.svg)](https://github.com/frankglendon/cleanvey/actions/workflows/ci.yml)
&nbsp;[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
&nbsp;[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

**English** · [中文](README.zh-CN.md)

</div>

---

Upload a survey export → Cleanvey runs **15 transparent quality checks** and
returns a per-respondent **risk score with a plain-language reason for every
flag**. Seconds instead of hours, consistent instead of gut-feel, auditable
instead of a black box. Deterministic rules do high-recall screening; an **LLM
judge** makes the semantic calls the rules can't.

---

## 💡 Why it matters

A meaningful slice of raw survey responses is low quality — bots, speeders,
copy-paste boilerplate, careless straight-lining, contradictory answers. Ship
them into the analysis and **every downstream number (NPS, satisfaction,
segmentation) is quietly wrong** — and so are the client decisions built on top.

Today that cleanup is **manual**: analysts eyeball thousands of open-ends and
scale grids by hand. It's slow, inconsistent between people, and hard to defend
when a client asks *"why did you drop these respondents?"*

**Cleanvey turns that into a repeatable, explainable pass:** every flagged
respondent comes with the exact rule and reason, ready to show a client.

---

## 📸 See it

| Upload | Auto column mapping |
|:---:|:---:|
| ![upload](docs/screenshots/01_upload.png) | ![mapping](docs/screenshots/02_mapping.png) |

**Result & risk report**

![result](docs/screenshots/03_result.png)

---

## 🎯 What this project demonstrates

- **Spotting a real, costly problem — and automating it.** Data quality directly
  determines whether a research deliverable is valid. I took a painful manual
  process and made it fast, consistent, and defensible.

- **Domain expertise, codified.** 15 named, transparent checks plus a
  configurable logic-constraint engine — the actual methodology of survey QC,
  written down so anyone can audit it.

- **AI used with judgment, not as a gimmick.** Rules do high-recall candidate
  generation; an **LLM "judge"** makes the precise call and writes the reason —
  a deliberate division of labour, not a chatbot bolted on.

- **Engineering that holds up.** Tested in CI across Python 3.10–3.12, compatible
  with pandas 2.x **and** 3.0, pip-installable, explainable by design.

- **Judgment & integrity.** This public version is fully **desensitized** —
  generic methodology and synthetic data only, with **zero** client names, real
  data, or tuned parameters. I can build in the open *and* protect confidential,
  competitively-sensitive material.

---

## 🧭 How it works

Cleanvey layers its checks cheapest-and-most-certain first, so every flag is
explainable and any layer can be tuned independently.

1. **Structure & logic** — speeding, straight-lining, patterns, duplicates,
   missingness, out-of-range, configurable logic contradictions.
2. **Open-end text quality** — gibberish, low-effort, too-short, repeated-token
   spam, exact / fuzzy / self duplicates.
3. **Cross-question consistency** — NPS vs. satisfaction, declarative constraints.
4. **Semantic — the LLM judge** — off-topic answers the rules can't settle.

Two principles: **rules generate candidates, the model judges**; and **raw data
is never overwritten — only QC columns are appended**, so the audit trail stays
intact. Full write-up in [docs/methodology.md](docs/methodology.md).

### The 15 rule-based checks + the LLM judge

| Rule | Catches | How |
|---|---|---|
| Speeding | Implausibly fast completion | Duration < 34% of the median |
| Straightlining | A whole scale grid set to one value | Answer dispersion ≈ 0 |
| Pattern | Mechanical 1-2-3-4 / 1-2-1-2 | Differences form an arithmetic or zigzag run |
| Contradiction | Recommendation vs. satisfaction conflict | Gap too large after normalization |
| Gibberish | Keyboard mashing / pure symbols | Character heuristics + vowel ratio |
| Low-effort | "don't know / none / whatever" | Polarity-aware lexicon |
| Too short | One- or two-character non-answers | Effective character count |
| Repeated token | "great great great" padding | Repeated multi-char unit |
| Duplicate text | Copy-pasted open-ends across people | Identical after normalization |
| Near-duplicate | Reworded boilerplate | RapidFuzz similarity (review only) |
| Self-duplicate | One person's open-ends all identical | Within-respondent comparison |
| Duplicate respondent | An entire response is identical | Closed-question signature collision |
| Logic check | Age / income / mutual-exclusion conflicts | Configurable constraints |
| Missing | Too much left blank | Missing rate > 50% |
| Out-of-range | Illegal values (e.g. NPS ∉ 0–10) | Value-domain validation |
| Off-topic (LLM judge) | Answer unrelated to the question | LLM semantic judgment |

Per-rule logic and thresholds in [docs/rules.md](docs/rules.md).

---

## 🚀 Try it in 30 seconds

```bash
pip install -r requirements.txt
cp .env.example .env                              # set ANTHROPIC_API_KEY (needed by the LLM judge)
python sample_data/generate_sample.py             # generate synthetic demo data (zero real data)
python app.py check sample_data/demo_survey.xlsx  # CLI: print a summary and write report.xlsx
python app.py                                     # or launch the web app at http://127.0.0.1:5000
```

Web flow: `Upload → Map columns → Run → Download report`. Want a real command?
After `pip install -e .` you get `cleanvey check ...` / `cleanvey web`.

## 🤖 The AI judge

The semantic layer — flagging open-ends that don't answer the question — is run
by an LLM judge (Anthropic Claude). Configure your key to run the full pipeline:

```bash
cp .env.example .env        # set your ANTHROPIC_API_KEY
```

`anthropic` ships as a core dependency. Advanced users can disable the judge in
`config/default_rules.yaml` (`offtopic.enabled: false`); without a key, the rule
engine still runs and the report notes the judge was not configured.

## 🔧 Under the hood

```
app.py                     # Flask web entry
cleanvey/                  # the library
  cli.py                   #   `cleanvey check` / `cleanvey web`
  schema.py                #   data loading + auto column mapping
  engine.py / scoring.py   #   run rules -> composite risk -> high/med/low
  rules/                   #   one small file per rule
  report.py / llm.py       #   Excel+HTML reports / the LLM judge client
config/default_rules.yaml  # toggle rules, weights, thresholds
tests/                     # pytest: per-rule + end-to-end
```

- **Tests:** `python -m pytest` — per-rule + end-to-end (every rule fires on the
  synthetic data). CI stays green on Python 3.10–3.12.
- **License & data:** MIT © Xiangyu (Frank) Bai. All sample data is randomly
  generated by `sample_data/generate_sample.py` and unrelated to any real
  respondent, client, or project.

---

## 👤 About the author

**Xiangyu (Frank) Bai** — a market researcher / analyst who builds AI-assisted
tools to solve real business problems. Cleanvey began as my **award-winning
entry** to an internal company AI hackathon; this public version is fully
desensitized (synthetic data and generic methodology only).

Open to opportunities in **market research, data analysis, and consulting**.

- **LinkedIn:** https://www.linkedin.com/in/frank-bai-411173260
- **GitHub:** https://github.com/frankglendon
