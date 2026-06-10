# Working on Cleanvey / 在 Cleanvey 上协作

Context for humans and AI assistants working in this repo. Conventions only —
no secrets, no client data.
给在本仓库协作的人与 AI 助手的上下文。只讲约定，不含机密与客户数据。

## What this is / 这是什么

A transparent quality-control toolkit for survey data: upload an export, run 15
explainable rules (+ an LLM "judge"), get a per-respondent risk report. The
whole point is **explainability** — every flag carries a human-readable reason.
一个面向问卷数据的透明 QC 工具：上传导出文件，跑 15 条可解释规则（外加大模型“判官”），
得到每位受访者的风险报告。核心是**可解释**——每个标记都附人类可读的理由。

## Layout / 结构

```
app.py                     # CLI + Flask web entry / 命令行 + 网页入口
cleanvey/
  schema.py                # load data + auto column mapping / 加载数据 + 自动列映射
  engine.py / scoring.py   # run rules -> composite risk -> 高/中/低
  rules/                   # one small file per rule / 一条规则一个小文件
  report.py / llm.py       # Excel+HTML reports / the LLM judge client
config/default_rules.yaml  # toggle rules, weights, thresholds / 规则开关、权重、阈值
sample_data/               # synthetic demo generator (no real data) / 合成示例（无真实数据）
tests/                     # pytest: per-rule + end-to-end
docs/                      # rules.md (per-rule) + methodology.md (the layered approach)
```

## The rule contract / 规则约定

Every rule is one function with a uniform signature:
每条规则都是一个签名统一的函数：

```python
func(df, schema, params) -> pd.DataFrame   # columns: flagged(bool), reason(str), score(0..1)
```

To add a rule / 新增一条规则：
1. Create `cleanvey/rules/<name>.py`; decorate with `@register(...)`.
   新建 `cleanvey/rules/<name>.py`，用 `@register(...)` 装饰。
2. Import it in `cleanvey/rules/__init__.py` (import order = display order).
   在 `cleanvey/rules/__init__.py` 里导入（导入顺序=展示顺序）。
3. Add a config block in `config/default_rules.yaml`.
   在 `config/default_rules.yaml` 里加一段配置。
4. Add a unit test in `tests/test_rules.py`; if it should show in the demo,
   inject a case in `sample_data/generate_sample.py` and assert it in `test_engine.py`.
   在 `tests/test_rules.py` 加单测；若要在演示中体现，在示例生成器里注入样本并在端到端测试断言。

The engine skips a rule when its required columns are absent, or when it's an
LLM rule and no API key is set; one rule throwing never sinks the whole run.
当所需列缺失、或是 LLM 规则但未配 key 时，引擎会跳过该规则；单条规则报错也不会拖垮整体。

## Conventions / 约定

- **Explainable by design.** Every flag must set a clear `reason`.
  **设计上可解释。** 每个标记都要写清 `reason`。
- **Rules generate candidates; the LLM judges.** Keyword/heuristic rules favour
  recall; the LLM adds precision + a reason. The judge is core but fail-soft.
  **规则负责高召回候选，大模型当判官。** 规则求召回，判官求精准并给理由；判官是核心但会优雅降级。
- **Never overwrite raw data — only append `[QC] ...` columns.**
  **绝不就地改原始数据——只追加 `[QC] ...` 列。**
- **Neutral default thresholds.** Every threshold is a reasonable starting
  point, *not* tuned to any project. Calibrate per survey.
  **中性默认阈值。** 所有阈值只是合理起点，未针对任何项目调优；请按问卷自行校准。
- **Bilingual comments (EN + 中文).** Match the existing style.
  **注释中英双语。** 与现有风格一致。

## Gotchas / 注意事项

- **pandas 2.x and 3.0 both supported.** pandas 3.0 keeps `NaN` through
  `astype(str)`, so always `.fillna("").astype(str)` before `.str` / `.strip()`
  / element-wise string ops — otherwise string rules silently break.
  **同时兼容 pandas 2.x 与 3.0。** pandas 3.0 下 `astype(str)` 会保留 `NaN`，因此做
  `.str`/`.strip()`/逐元素字符串操作前务必先 `.fillna("").astype(str)`，否则文本规则会静默失效。
- The LLM judge needs `ANTHROPIC_API_KEY` (see `.env.example`); it can be turned
  off via `offtopic.enabled: false` in the config.
  判官需要 `ANTHROPIC_API_KEY`（见 `.env.example`）；可在配置里 `offtopic.enabled: false` 关闭。

## Safety / data hygiene / 数据安全与脱敏

This is a **public, demo-safe** project. Only synthetic data
(`sample_data/generate_sample.py`) — **no real respondents, clients, project
names, or tuned parameters**. Before committing, grep for any such terms.
这是一个**公开、可安全演示**的项目。只用合成数据——**不含任何真实受访者、客户、项目名或调好的参数**。
提交前请 grep 复核此类词。

## Verify / 验证

```bash
python -m pytest                                   # all tests / 全部测试
python app.py check sample_data/demo_survey.xlsx   # CLI smoke test / 命令行冒烟
```
CI runs the test suite on Python 3.10–3.12. / CI 会在 Python 3.10–3.12 上跑测试。
