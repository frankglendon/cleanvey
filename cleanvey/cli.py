"""Command-line interface — `cleanvey check ...` and `cleanvey web`.
命令行入口 —— `cleanvey check ...` 与 `cleanvey web`。

`check` runs purely on the library (no Flask, no templates), so it works
anywhere the package is installed. `web` serves the Flask UI and therefore must
be run from a clone of the repo (the HTML templates live there).
`check` 纯靠库运行（不依赖 Flask 与模板），装了包就能在任何目录用；`web` 启动 Flask 网页，
需在仓库克隆目录下运行（HTML 模板在那里）。
"""
from __future__ import annotations

import argparse
import sys

from .config import load_config
from .engine import run_qc
from .llm import llm_available
from .report import write_excel
from .schema import guess_schema, load_data


def build_parser() -> argparse.ArgumentParser:
    """Define the `check` / `web` subcommands. / 定义 check / web 两个子命令。"""
    parser = argparse.ArgumentParser(prog="cleanvey", description="Survey data QC toolkit")
    sub = parser.add_subparsers(dest="cmd")

    c = sub.add_parser("check", help="run QC on a file and write a report (no server)")
    c.add_argument("file", help="survey export (.csv / .xlsx / .xls)")
    c.add_argument("--config", default=None, help="rules YAML (optional)")
    c.add_argument("--out", default="cleanvey_report.xlsx", help="output .xlsx path")
    c.add_argument("--llm", action="store_true", help="enable LLM semantic checks")

    w = sub.add_parser("web", help="start the web app (run from a cloned repo)")
    w.add_argument("--port", type=int, default=5000)
    w.add_argument("--host", default="127.0.0.1")
    return parser


def run_check(args) -> int:
    """Headless QC: load -> map -> run -> write Excel + print summary.
    无界面跑 QC：加载 -> 列映射 -> 运行 -> 写 Excel 并打印汇总。"""
    df = load_data(args.file)
    schema = guess_schema(df)
    config = load_config(args.config)
    use_llm = args.llm and llm_available()
    if args.llm and not use_llm:
        print("提示：未检测到 ANTHROPIC_API_KEY，已跳过 LLM 语义检查。")

    result = run_qc(df, schema, config, use_llm=use_llm)
    write_excel(result.detail, result.summary, args.out)

    s = result.summary
    print(f"\n样本总数：{s['total']}")
    print(f"高风险 {s['level_counts']['高']} · 中风险 {s['level_counts']['中']} "
          f"· 低风险 {s['level_counts']['低']}")
    print("各规则命中：")
    for name, hits in s["rule_hits"].items():
        print(f"  - {name}: {hits}")
    if s["skipped_rules"]:
        print("未运行的规则：")
        for sk in s["skipped_rules"]:
            print(f"  - {sk['rule']}（{sk['reason']}）")
    print(f"\n报告已写出：{args.out}")
    return 0


def run_web(args, flask_app=None) -> int:
    """Start the Flask server. / 启动 Flask 服务。"""
    if flask_app is None:
        try:
            from app import app as flask_app  # served from a clone (needs templates/) / 需克隆目录的 templates/
        except Exception:
            print("无法启动网页：请在项目克隆目录下运行 `cleanvey web`（网页依赖 templates/）。")
            return 1
    print(f"Cleanvey running at http://{args.host}:{args.port}  (Ctrl+C to stop)")
    flask_app.run(host=args.host, port=args.port, debug=False)
    return 0


def main(argv=None) -> int:
    raw = sys.argv[1:] if argv is None else argv
    args = build_parser().parse_args(raw or ["web"])  # default to web / 不带参数默认启动网页
    if args.cmd == "check":
        return run_check(args)
    return run_web(args)


if __name__ == "__main__":
    raise SystemExit(main())
