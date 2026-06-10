"""Cleanvey — an explainable quality-control toolkit for survey data.
Cleanvey —— 面向问卷数据的可解释质量检查工具。

Upload a survey export, map the columns, run 15 transparent rule-based checks
plus an LLM "judge" for the semantic calls, and get a per-respondent risk
report. Set ANTHROPIC_API_KEY to run the judge; the rule engine runs regardless.
上传问卷导出 → 自动列映射 → 跑 15 条透明的规则检查，外加一个大模型“判官”处理语义判断，
得到每位受访者的风险报告。配置 ANTHROPIC_API_KEY 即可启用判官；规则引擎始终照常运行。
"""

__version__ = "0.1.0"
