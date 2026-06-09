"""Data loading and column mapping. / 数据加载与列映射。

A survey export is just a table, but QC rules need to know the *role* of each
column: which one is the NPS score, which are matrix scale items, which are
open-ended text, which is the interview duration, etc.

`Schema` holds that mapping. `guess_schema()` proposes one automatically from
column names and value patterns; the user can then confirm/adjust it (in the
web UI or by passing a mapping file to the CLI).

中文：问卷导出本质上只是一张表，但 QC 规则需要知道每一列的“角色”——哪列是 NPS 推荐分、
哪些是量表题、哪些是开放题、哪列是答题时长等。`Schema` 保存这个映射；`guess_schema()`
会按列名与取值规律自动猜测，用户再在网页界面确认/调整（或给 CLI 传一个映射文件）。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional

import pandas as pd


class ColumnRole(str, Enum):
    """The role a column plays in QC analysis. / 列在 QC 分析中的角色。"""
    ID = "id"                  # respondent identifier / 受访者标识
    NPS = "nps"                # 0-10 recommend score / 0-10 推荐分
    SCALE = "scale"            # matrix / Likert item / 量表题（如 1-5、1-7）
    OPENEND = "openend"        # free-text answer / 开放题文本
    DURATION = "duration"      # time spent answering (seconds) / 答题时长（秒）
    CATEGORICAL = "categorical"  # single-choice / demographic / 单选 / 人口属性
    OTHER = "other"            # ignored by rules / 规则忽略


# Keyword hints for auto-detection. Lower-cased substring match on column names.
# Kept intentionally bilingual (EN + ZH) so it works on real-world exports.
# 自动识别用的关键词（对列名做小写子串匹配）；中英双语以适配真实导出文件。
_KEYWORDS = {
    ColumnRole.ID: ["id", "respondent", "编号", "受访者", "样本", "serial", "rid", "uuid"],
    ColumnRole.NPS: ["nps", "推荐", "recommend", "likelihood", "净推荐", "推荐度"],
    ColumnRole.DURATION: ["duration", "time", "时长", "用时", "答题时间", "loi", "interview length", "耗时"],
    ColumnRole.OPENEND: ["原因", "为什么", "open", "comment", "评价", "建议", "反馈",
                          "请说明", "具体", "feedback", "verbatim", "remarks", "说明"],
}


def load_data(path: str) -> pd.DataFrame:
    """Read a survey export (.csv / .xlsx / .xls) into a DataFrame.
    读取问卷导出文件（.csv / .xlsx / .xls）为 DataFrame。"""
    lower = str(path).lower()
    if lower.endswith(".csv"):
        return pd.read_csv(path)
    return pd.read_excel(path)


@dataclass
class Schema:
    """Column-role mapping for one survey dataset. / 一份问卷数据的列角色映射。"""
    id_col: Optional[str] = None
    nps_col: Optional[str] = None
    duration_col: Optional[str] = None
    scale_cols: List[str] = field(default_factory=list)
    openend_cols: List[str] = field(default_factory=list)
    categorical_cols: List[str] = field(default_factory=list)

    def has(self, require: str) -> bool:
        """True if the schema field named `require` is populated.
        若名为 `require` 的字段已填充则返回 True。

        Used by the engine to decide whether a rule can run on this data,
        e.g. a speeding rule requires a non-empty `duration_col`.
        引擎据此判断某规则能否在当前数据上运行（如超速规则需要 `duration_col`）。
        """
        return bool(getattr(self, require, None))

    def role_of(self, col: str) -> ColumnRole:
        """Return the role assigned to a given column. / 返回某列被指派的角色。"""
        if col == self.id_col:
            return ColumnRole.ID
        if col == self.nps_col:
            return ColumnRole.NPS
        if col == self.duration_col:
            return ColumnRole.DURATION
        if col in self.scale_cols:
            return ColumnRole.SCALE
        if col in self.openend_cols:
            return ColumnRole.OPENEND
        if col in self.categorical_cols:
            return ColumnRole.CATEGORICAL
        return ColumnRole.OTHER

    def roles_map(self, columns: List[str]) -> Dict[str, str]:
        """col -> role string, for display in the mapping UI.
        列名 -> 角色字符串，供映射界面展示。"""
        return {c: self.role_of(c).value for c in columns}

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Schema":
        known = {f: d.get(f) for f in (
            "id_col", "nps_col", "duration_col",
            "scale_cols", "openend_cols", "categorical_cols")}
        # normalise None lists / 把 None 的列表字段规整为空列表
        for k in ("scale_cols", "openend_cols", "categorical_cols"):
            known[k] = known.get(k) or []
        return cls(**known)


def _matches(col: str, role: ColumnRole) -> bool:
    """True if the column name contains any keyword for `role`.
    若列名包含 `role` 的任一关键词则为 True。"""
    name = str(col).lower()
    return any(kw in name for kw in _KEYWORDS.get(role, []))


def _looks_like_scale(series: pd.Series) -> bool:
    """A small-integer scale item: numeric, few distinct values, low range.
    像量表题：数值型、取值种类少、范围小（0-10 内）。"""
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) == 0:
        return False
    nunique = s.nunique()
    if nunique < 2 or nunique > 11:
        return False
    return s.min() >= 0 and s.max() <= 10


def _looks_like_text(series: pd.Series) -> bool:
    """Mostly free text: object dtype with non-trivial average length.
    像开放题：object 类型且平均长度不算太短。"""
    if series.dtype != object:
        return False
    text = series.dropna().astype(str)
    if len(text) == 0:
        return False
    avg_len = text.str.len().mean()
    return avg_len >= 4


def guess_schema(df: pd.DataFrame) -> Schema:
    """Propose a column mapping from names + value patterns.
    根据列名与取值规律，自动给出一个列角色映射。

    Heuristics, in priority order per column / 每列按以下优先级判断：
      1. name keyword for ID / NPS / DURATION / 先按列名命中 ID / NPS / 时长
      2. text content        -> open-ended       / 文本内容 -> 开放题
      3. small numeric scale -> scale item        / 小范围数值 -> 量表题
      4. everything else     -> categorical       / 其余 -> 分类
    """
    schema = Schema()
    used: set = set()

    # Pass 1: strong name-based hints (id / nps / duration are single columns).
    # 第一遍：按列名强信号识别（id / nps / 时长 各为单列）。
    for col in df.columns:
        if col in used:
            continue
        if schema.id_col is None and _matches(col, ColumnRole.ID):
            # only accept as ID if values are (near) unique / 取值（近乎）唯一才认作 ID
            if df[col].nunique(dropna=True) >= max(1, int(0.9 * len(df))):
                schema.id_col = col
                used.add(col)
                continue
        if schema.nps_col is None and _matches(col, ColumnRole.NPS):
            schema.nps_col = col
            used.add(col)
            continue
        if schema.duration_col is None and _matches(col, ColumnRole.DURATION):
            schema.duration_col = col
            used.add(col)
            continue

    # Pass 2: content-based classification for the rest.
    # 第二遍：剩余列按内容归类。
    for col in df.columns:
        if col in used:
            continue
        if _matches(col, ColumnRole.OPENEND) or _looks_like_text(df[col]):
            schema.openend_cols.append(col)
        elif _looks_like_scale(df[col]):
            schema.scale_cols.append(col)
        else:
            schema.categorical_cols.append(col)

    return schema
