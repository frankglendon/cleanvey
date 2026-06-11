<div align="center">

# 🧹 Cleanvey

**在脏数据拉偏结论之前，先把它揪出来。**

[![CI](https://github.com/frankglendon/cleanvey/actions/workflows/ci.yml/badge.svg)](https://github.com/frankglendon/cleanvey/actions/workflows/ci.yml)
&nbsp;[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
&nbsp;[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

[English](README.md) · **中文**

</div>

---

上传问卷导出文件 → Cleanvey 跑 **15 条透明的质量规则**，给出每位受访者的
**风险分，并为每个标记附上一句大白话理由**。几秒钟而非几小时、统一标准而非凭感觉、
可审计而非黑箱。确定性规则负责高召回初筛，**大模型“判官”**负责规则判不了的语义判断。

---

## 💡 为什么重要

问卷原始数据里总有一部分是脏的——机器人、超速作答、复制粘贴的套话、敷衍的直线作答、
自相矛盾的回答。混进分析，就会**悄悄拉偏 NPS、满意度、人群细分等每一个核心数字**，
连带影响建立在这些数字之上的客户决策。

而现在的清洗多半靠**人工**：分析师肉眼逐条看成千上万条开放题和量表。慢、因人而异，
客户一问“你凭什么剔除这些样本”时还很难解释清楚。

**Cleanvey 把它变成一个可复现、可解释的步骤：** 每个被标记的样本都附上命中的规则和理由，
可以直接拿给客户看。

---

## 📸 界面预览

| 上传 | 自动识别列 |
|:---:|:---:|
| ![upload](docs/screenshots/01_upload.png) | ![mapping](docs/screenshots/02_mapping.png) |

**结果与风险报告**

![result](docs/screenshots/03_result.png)

---

## 🎯 这个项目体现了什么

- **发现真实且昂贵的业务痛点，并把它自动化。** 数据质量直接决定研究交付是否站得住脚——
  我把一个痛苦的人工流程，做成了快速、一致、可向客户交代的自动化方案。

- **把领域经验沉淀成方法论。** 15 条命名清晰、逻辑透明的规则，外加一个可配置的逻辑约束引擎——
  这就是市场研究 QC 的实战方法，写下来让任何人都能审查。

- **AI 用在刀刃上，不是噱头。** 规则负责高召回地“捞候选”，**大模型“判官”**负责精准判定并写出理由——
  这是有意设计的分工，而不是硬塞一个聊天机器人。

- **经得起检验的工程。** CI 在 Python 3.10–3.12 上自动测试，兼容 pandas 2.x **和** 3.0，
  可 pip 安装，设计上就可解释。

- **分寸感与职业操守。** 这个公开版本做了**完全脱敏**——只有通用方法论和合成数据，
  **不含任何**客户名称、真实数据或调校过的参数。我既能开放地分享，也守得住机密与竞争性信息。

---

## 🧭 工作原理

Cleanvey 把检查按“越确定、越便宜越先跑”分层，因此每个标记都可解释，每一层都能独立调参：

1. **结构与逻辑** —— 超速、直线、模式化、雷同、缺失、越界、可配置的逻辑矛盾。
2. **开放题文本质量** —— 乱码、无信息、过短、重复刷屏，精确／近似／自我重复。
3. **跨题一致性** —— 推荐分与满意度背离、声明式约束。
4. **语义层 · 大模型判官** —— 规则判不了的“答非所问”，交给大模型判官。

两条原则：**规则负责高召回候选，模型负责精准判定**；以及**绝不就地改原始数据，只追加 QC 标记列**，
保证审计链路完整。完整说明见 [docs/methodology.md](docs/methodology.md)。

### 15 条规则 + 大模型判官一览

| 规则 | 检测什么 | 怎么判 |
|---|---|---|
| 超速作答 | 答题快得不合理 | 时长 < 中位数的 34% |
| 直线作答 | 一组量表全选同一值 | 量表答案离散度 ≈ 0 |
| 模式化作答 | 机械的 1-2-3-4 / 1-2-1-2 | 差分呈等差或锯齿 |
| 矛盾作答 | 推荐分与满意度冲突 | 归一化后差距过大 |
| 开放题乱填 | 键盘乱敲 / 纯符号 | 字符启发式 + 元音率 |
| 无信息作答 | “不知道/没有/随便” | 极性感知词典 |
| 开放题过短 | 一两字的无信息回答 | 有效字符数 |
| 重复刷屏 | “推荐推荐推荐”式堆砌 | 多字词重复单元 |
| 开放题雷同 | 跨人复制粘贴的开放题 | 归一化后逐字相同 |
| 近似雷同 | 改写过的套话 | RapidFuzz 相似度（仅复核） |
| 自我重复 | 一人所有开放题填同样内容 | 同受访者内部比对 |
| 整份雷同 | 整份问卷完全相同 | 客观题签名碰撞 |
| 逻辑矛盾 | 年龄/收入/互斥等冲突 | 可配置约束 |
| 作答缺失 | 留空过多 | 缺失率 > 50% |
| 越界数值 | 非法值（如 NPS∉0–10） | 取值域校验 |
| 答非所问（LLM 判官） | 答案与问题无关 | 大模型语义判断 |

每条规则的判定逻辑与阈值见 [docs/rules.md](docs/rules.md)。

---

## 🚀 30 秒上手

```bash
pip install -r requirements.txt
cp .env.example .env                                   # 填入 ANTHROPIC_API_KEY（LLM 判官需要）
python sample_data/generate_sample.py                 # 生成合成示例数据（零真实数据）
python app.py check sample_data/demo_survey.xlsx       # 命令行：打印汇总并写出 report.xlsx
python app.py                                          # 或启动网页 http://127.0.0.1:5000
```

网页流程：`上传 → 确认列映射 → 运行 → 下载报告`。想要一个真正的命令？
`pip install -e .` 之后即可用 `cleanvey check ...` / `cleanvey web`。

## 🤖 大模型判官（核心层）

语义层（判断开放题是否答非所问）由大模型判官（Anthropic Claude）完成。配置 Key 即可运行完整流程：

```bash
cp .env.example .env        # 填入你的 ANTHROPIC_API_KEY
```

`anthropic` 已是核心依赖。进阶用户可在 `config/default_rules.yaml` 里关掉判官
（`offtopic.enabled: false`）；未配置 Key 时规则引擎照常运行，报告会注明判官未配置。

## 🔧 工程细节

```
app.py                     # 网页入口（Flask）
cleanvey/                  # 核心库
  cli.py                   #   `cleanvey check` / `cleanvey web` 命令行
  schema.py                #   加载数据 + 自动列映射
  engine.py / scoring.py   #   跑规则 -> 综合风险 -> 高/中/低
  rules/                   #   一条规则一个小文件
  report.py / llm.py       #   Excel+HTML 报告 / 大模型判官客户端
config/default_rules.yaml  # 规则开关、权重、阈值
tests/                     # pytest：逐规则 + 端到端
```

- **测试：** `python -m pytest` —— 逐条规则 + 端到端跑通（确认每条规则都在合成数据上命中）。
  CI 在 Python 3.10–3.12 上保持绿色。
- **许可与数据：** MIT © Xiangyu (Frank) Bai。所有示例数据均由
  `sample_data/generate_sample.py` 随机生成，与任何真实受访者、客户或项目无关。

---

## 👤 关于作者

**白翔宇（Frank）** —— 市场研究 / 数据分析方向，且能用 AI 自己造工具解决真实业务问题。
Cleanvey 最初是我参加公司内部 AI 黑客松的**获奖作品**；这个公开版本已
**完全脱敏**（只含合成数据与通用方法论）。求职方向：**市场研究、数据分析、咨询**，欢迎联系。

- **LinkedIn:** https://www.linkedin.com/in/frank-bai-411173260
- **GitHub:** https://github.com/frankglendon
