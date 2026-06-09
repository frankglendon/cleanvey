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
