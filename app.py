"""Cleanvey web app (Flask). / Cleanvey 网页应用（Flask）。

Run it directly / 直接运行:
    python app.py            # then open http://127.0.0.1:5000
    python app.py web --port 8000
    python app.py check sample_data/demo_survey.xlsx   # delegates to the CLI / 委托给 CLI

If the package is installed (`pip install -e .`), the same commands are
available as `cleanvey web` / `cleanvey check ...`. The argument parsing and
the headless `check` command live in `cleanvey/cli.py`.
若已安装包（`pip install -e .`），可直接用 `cleanvey web` / `cleanvey check ...`；
参数解析与无界面的 `check` 命令在 `cleanvey/cli.py`。

Per-upload state is kept in an in-memory dict — fine for local, single-user use
(this is a demo/portfolio tool, not a multi-tenant service).
每次上传的状态存在内存字典里——本地单用户够用（这是演示/作品集工具，不是多租户服务）。
"""
from __future__ import annotations

import os
import uuid

from flask import (Flask, abort, redirect, render_template, request,
                   send_file, url_for)

from cleanvey.config import load_config
from cleanvey.engine import run_qc
from cleanvey.llm import llm_available
from cleanvey.report import write_excel, write_html
from cleanvey.schema import ColumnRole, Schema, guess_schema, load_data

BASE = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE, "uploads")   # uploaded files / 上传的文件
OUTPUT_DIR = os.path.join(BASE, "outputs")   # generated reports / 生成的报告
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

ALLOWED = (".csv", ".xlsx", ".xls")
SESSIONS: dict = {}  # token -> {"path", "df", "schema", "result", "excel", "html"} / 每次上传的会话状态

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB upload cap / 上传大小上限 32MB


def schema_from_form(columns, form) -> Schema:
    """Rebuild a Schema from the mapping form (role_<col> -> role).
    根据映射表单（role_<列名> -> 角色）重建 Schema。"""
    schema = Schema()
    for col in columns:
        role = form.get(f"role_{col}", ColumnRole.OTHER.value)
        if role == ColumnRole.ID.value:
            schema.id_col = col
        elif role == ColumnRole.NPS.value:
            schema.nps_col = col
        elif role == ColumnRole.DURATION.value:
            schema.duration_col = col
        elif role == ColumnRole.SCALE.value:
            schema.scale_cols.append(col)
        elif role == ColumnRole.OPENEND.value:
            schema.openend_cols.append(col)
        elif role == ColumnRole.CATEGORICAL.value:
            schema.categorical_cols.append(col)
    return schema


@app.route("/")
def index():
    """Upload page. / 上传页。"""
    return render_template("index.html", llm=llm_available())


@app.route("/upload", methods=["POST"])
def upload():
    """Receive a file, auto-guess the schema, go to the mapping page.
    接收文件，自动猜测列映射，跳转到映射确认页。"""
    file = request.files.get("file")
    if not file or not file.filename:
        return redirect(url_for("index"))
    if not file.filename.lower().endswith(ALLOWED):
        abort(400, "仅支持 .csv / .xlsx / .xls 文件")

    token = uuid.uuid4().hex
    path = os.path.join(UPLOAD_DIR, f"{token}_{file.filename}")
    file.save(path)

    df = load_data(path)
    schema = guess_schema(df)
    SESSIONS[token] = {"path": path, "df": df, "schema": schema}
    return redirect(url_for("mapping", token=token))


@app.route("/mapping/<token>")
def mapping(token):
    """Show the auto-guessed column roles for the user to confirm/adjust.
    展示自动识别的列角色，供用户确认/调整。"""
    sess = SESSIONS.get(token) or abort(404)
    df, schema = sess["df"], sess["schema"]
    columns = [
        {"name": c, "role": schema.role_of(c).value,
         "sample": ", ".join(df[c].dropna().astype(str).head(3).tolist())}
        for c in df.columns
    ]
    roles = [(r.value, label) for r, label in [
        (ColumnRole.ID, "受访者ID"), (ColumnRole.NPS, "NPS推荐分"),
        (ColumnRole.SCALE, "量表题"), (ColumnRole.OPENEND, "开放题"),
        (ColumnRole.DURATION, "答题时长"), (ColumnRole.CATEGORICAL, "分类/单选"),
        (ColumnRole.OTHER, "忽略"),
    ]]
    return render_template("mapping.html", token=token, columns=columns,
                           roles=roles, rows=len(df))


@app.route("/run/<token>", methods=["POST"])
def run(token):
    """Run the engine with the confirmed schema, write reports, go to result.
    用确认后的映射跑引擎，写报告，跳到结果页。"""
    sess = SESSIONS.get(token) or abort(404)
    df = sess["df"]
    schema = schema_from_form(df.columns, request.form)

    config = load_config(os.path.join(BASE, "config", "default_rules.yaml"))
    use_llm = llm_available()
    result = run_qc(df, schema, config, use_llm=use_llm)

    excel_path = os.path.join(OUTPUT_DIR, f"{token}_report.xlsx")
    html_path = os.path.join(OUTPUT_DIR, f"{token}_report.html")
    write_excel(result.detail, result.summary, excel_path)
    write_html(result.summary, html_path)

    sess.update({"result": result, "excel": excel_path, "html": html_path})
    return redirect(url_for("result", token=token))


@app.route("/result/<token>")
def result(token):
    """Result dashboard + a 50-row preview of the detail table.
    结果看板 + 明细表前 50 行预览。"""
    sess = SESSIONS.get(token) or abort(404)
    res = sess.get("result") or abort(404)
    preview = res.detail.head(50)
    table_html = preview.to_html(
        classes="table table-sm table-striped", index=False, na_rep=""
    )
    return render_template("result.html", token=token, summary=res.summary,
                           table_html=table_html)


@app.route("/download/<token>/<kind>")
def download(token, kind):
    """Download the Excel detail or the HTML report. / 下载 Excel 明细或 HTML 报告。"""
    sess = SESSIONS.get(token) or abort(404)
    path = sess.get("excel" if kind == "excel" else "html") or abort(404)
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    import sys

    from cleanvey.cli import build_parser, run_check, run_web

    # `check` -> CLI; anything else (default) -> serve this module's app.
    # `check` 走 CLI；其余（默认）启动本模块的 app。
    _args = build_parser().parse_args(sys.argv[1:] or ["web"])
    if _args.cmd == "check":
        raise SystemExit(run_check(_args))
    raise SystemExit(run_web(_args, flask_app=app))
