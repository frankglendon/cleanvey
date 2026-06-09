"""End-to-end: auto-map the synthetic demo and confirm every rule fires.
端到端测试：自动映射合成示例，并确认每条规则都命中。"""
import importlib.util
import os

from cleanvey.config import default_config
from cleanvey.engine import run_qc
from cleanvey.schema import guess_schema

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _build_demo():
    path = os.path.join(ROOT, "sample_data", "generate_sample.py")
    spec = importlib.util.spec_from_file_location("gen_sample", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build()


def test_end_to_end_catches_each_issue():
    df = _build_demo()
    schema = guess_schema(df)

    # auto-mapping sanity / 自动列映射是否正确
    assert schema.nps_col == "nps_score"
    assert schema.duration_col == "duration_sec"
    assert "Q6_总体满意度" in schema.scale_cols
    assert "open_reason" in schema.openend_cols

    res = run_qc(df, schema, default_config(), use_llm=False)
    hits = res.summary["rule_hits"]
    for name in ["超速作答", "直线作答", "模式化作答", "矛盾作答", "逻辑矛盾",
                 "开放题乱填", "开放题雷同", "无信息作答", "开放题过短", "近似雷同",
                 "重复刷屏", "自我重复", "整份雷同", "作答缺失", "越界数值"]:
        assert hits.get(name, 0) > 0, f"{name} 未命中"

    # LLM rule must be skipped when no key is configured / 无 key 时 LLM 规则应被跳过
    assert any(s["rule"] == "答非所问" for s in res.summary["skipped_rules"])
    assert res.summary["total"] == len(df)
    assert "[QC] 风险等级" in res.detail.columns
