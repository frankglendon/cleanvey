"""Cleanvey web app (Flask).

Run it directly:
    python app.py            # then open http://127.0.0.1:5000
    python app.py web --port 8000
    python app.py check sample_data/demo_survey.xlsx   # delegates to the CLI

If the package is installed (`pip install -e .`), the same commands are
available as `cleanvey web` / `cleanvey check ...`. The argument parsing and
the headless `check` command live in `cleanvey/cli.py`.

Per-upload state is kept in an in-memory dict — fine for local, single-user use
(this is a demo/portfolio tool, not a multi-tenant service).
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
UPLOAD_DIR = os.path.join(BASE, "uploads")
OUTPUT_DIR = os.path.join(BASE, "outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

ALLOWED = (".csv", ".xlsx", ".xls")
SESSIONS: dict = {}  # token -> {"path", "df", "schema", "result", "excel", "html"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB


def schema_from_form(columns, form) -> Schema:
    """Rebuild a Schema from the mapping form (role_<col> -> role)."""
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
    return render_template("index.html", llm=llm_available())


@app.route("/upload", methods=["POST"])
def upload():
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
    sess = SESSIONS.get(token) or abort(404)
    path = sess.get("excel" if kind == "excel" else "html") or abort(404)
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    import sys

    from cleanvey.cli import build_parser, run_check, run_web

    _args = build_parser().parse_args(sys.argv[1:] or ["web"])
    if _args.cmd == "check":
        raise SystemExit(run_check(_args))
    raise SystemExit(run_web(_args, flask_app=app))
