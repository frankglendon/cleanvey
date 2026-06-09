"""Per-rule unit tests on small hand-built tables."""
import pandas as pd

from cleanvey.rules import REGISTRY
from cleanvey.schema import Schema


def run(key, df, schema, params=None):
    rule = REGISTRY[key]
    merged = {**rule.default_params, **(params or {})}
    return rule.func(df, schema, merged)


def test_speeding():
    df = pd.DataFrame({"t": [10, 200, 220, 210, 205]})
    r = run("speeding", df, Schema(duration_col="t"))
    assert bool(r.loc[0, "flagged"]) and not bool(r.loc[1, "flagged"])


def test_straightlining():
    df = pd.DataFrame({"a": [3, 1], "b": [3, 2], "c": [3, 5]})
    r = run("straightlining", df, Schema(scale_cols=["a", "b", "c"]))
    assert bool(r.loc[0, "flagged"]) and not bool(r.loc[1, "flagged"])


def test_pattern_zigzag():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 5], "c": [1, 1], "d": [3, 4]})
    r = run("pattern", df, Schema(scale_cols=["a", "b", "c", "d"]))
    assert bool(r.loc[0, "flagged"]) and not bool(r.loc[1, "flagged"])


def test_gibberish():
    df = pd.DataFrame({"o": ["asdfgh", "这是一个很正常的回答内容"]})
    r = run("gibberish", df, Schema(openend_cols=["o"]))
    assert bool(r.loc[0, "flagged"]) and not bool(r.loc[1, "flagged"])


def test_duplicate_text():
    df = pd.DataFrame({"o": ["这个产品非常好用推荐", "这个产品非常好用推荐", "完全不同的另一段内容"]})
    r = run("duplicate_text", df, Schema(openend_cols=["o"]))
    assert bool(r.loc[0, "flagged"]) and not bool(r.loc[2, "flagged"])


def test_duplicate_respondent():
    df = pd.DataFrame({"nps": [5, 5, 9], "q1": [3, 3, 1], "q2": [4, 4, 2]})
    r = run("duplicate_respondent", df,
            Schema(nps_col="nps", scale_cols=["q1", "q2"]),
            params={"min_answered": 2})
    assert bool(r.loc[0, "flagged"]) and not bool(r.loc[2, "flagged"])


def test_missing():
    df = pd.DataFrame({"nps": [5, None], "q1": [3, None], "o": ["good", None], "c": ["A", None]})
    r = run("missing", df, Schema(nps_col="nps", scale_cols=["q1"],
                                  openend_cols=["o"], categorical_cols=["c"]))
    assert bool(r.loc[1, "flagged"]) and not bool(r.loc[0, "flagged"])


def test_out_of_range():
    df = pd.DataFrame({"nps": [5, 99, -1]})
    r = run("out_of_range", df, Schema(nps_col="nps"))
    assert bool(r.loc[1, "flagged"]) and bool(r.loc[2, "flagged"]) and not bool(r.loc[0, "flagged"])


def test_contradiction():
    df = pd.DataFrame({"nps": [10, 5], "总体满意度": [1, 3]})
    r = run("contradiction", df, Schema(nps_col="nps", scale_cols=["总体满意度"]))
    assert bool(r.loc[0, "flagged"]) and not bool(r.loc[1, "flagged"])


def test_low_effort():
    df = pd.DataFrame({"o": ["不知道", "因为质量很好用着也省心"]})
    r = run("low_effort", df, Schema(openend_cols=["o"]))
    assert bool(r.loc[0, "flagged"]) and not bool(r.loc[1, "flagged"])


def test_too_short():
    df = pd.DataFrame({"o": ["好", "这是一段有实质内容的回答"]})
    r = run("too_short", df, Schema(openend_cols=["o"]))
    assert bool(r.loc[0, "flagged"]) and not bool(r.loc[1, "flagged"])


def test_gibberish_low_vowel():
    df = pd.DataFrame({"o": ["dhrjhryfgjkbvn", "this is a normal english sentence"]})
    r = run("gibberish", df, Schema(openend_cols=["o"]))
    assert bool(r.loc[0, "flagged"]) and not bool(r.loc[1, "flagged"])


def test_near_duplicate():
    df = pd.DataFrame({"o": [
        "这个产品我用了大半年总体非常满意会推荐朋友",
        "这个产品我用了大半年整体非常满意会推荐朋友",
        "完全不一样的另外一段独立内容的文字描述",
    ]})
    r = run("near_duplicate", df, Schema(openend_cols=["o"]))
    assert bool(r.loc[0, "flagged"]) and not bool(r.loc[2, "flagged"])


def test_logic_check():
    df = pd.DataFrame({"age": [40, 30], "child_age": [35, 5]})
    r = run("logic_check", df, Schema())  # default constraint: age - child_age >= 16
    assert bool(r.loc[0, "flagged"]) and not bool(r.loc[1, "flagged"])


def test_logic_forbidden_combo():
    df = pd.DataFrame({"nps": [0, 8], "intent": ["一定会推荐", "可能不会"]})
    cons = [{"type": "forbidden_combo", "a": "nps", "a_in": [0],
             "b": "intent", "b_in": ["一定会推荐"], "label": "死亡矛盾"}]
    r = run("logic_check", df, Schema(), params={"constraints": cons})
    assert bool(r.loc[0, "flagged"]) and not bool(r.loc[1, "flagged"])


def test_logic_requires_answered():
    df = pd.DataFrame({"used": ["是", "否"], "detail": ["", ""]})
    cons = [{"type": "requires_answered", "if_col": "used", "if_in": ["是"],
             "then_col": "detail", "label": "应答未答"}]
    r = run("logic_check", df, Schema(), params={"constraints": cons})
    assert bool(r.loc[0, "flagged"]) and not bool(r.loc[1, "flagged"])


def test_logic_requires_blank():
    df = pd.DataFrame({"used": ["否", "是"], "detail": ["填了内容", ""]})
    cons = [{"type": "requires_blank", "if_col": "used", "if_in": ["否"],
             "then_col": "detail", "label": "应跳过却作答"}]
    r = run("logic_check", df, Schema(), params={"constraints": cons})
    assert bool(r.loc[0, "flagged"]) and not bool(r.loc[1, "flagged"])
