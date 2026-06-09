"""Configuration: which rules run, their weights, params, and score cutoffs.
配置：哪些规则运行、各自的权重、参数，以及分档阈值。

`default_config()` is derived straight from the rule registry, so the tool
works with zero configuration. `load_config(path)` lets a user override any
piece via a YAML file (see config/default_rules.yaml).
`default_config()` 直接由规则注册表生成，因此零配置即可使用；`load_config(path)`
允许用户用一个 YAML 文件覆盖其中任意部分（见 config/default_rules.yaml）。
"""
from __future__ import annotations

import os
from typing import Optional

import yaml

from .rules import REGISTRY


def default_config() -> dict:
    """Build the default config from every registered rule. / 由所有注册规则生成默认配置。"""
    rules = {}
    for key, rule in REGISTRY.items():
        rules[key] = {
            "enabled": True,
            "weight": rule.default_weight,
            "params": dict(rule.default_params),
        }
    return {"rules": rules, "scoring": {"high": 0.9, "medium": 0.4}}


def load_config(path: Optional[str] = None) -> dict:
    """Start from defaults, then shallow-merge a user YAML on top (if given).
    以默认配置为底，再把用户 YAML（若提供）浅合并覆盖上去。"""
    cfg = default_config()
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            user = yaml.safe_load(f) or {}
        for key, rule_cfg in (user.get("rules") or {}).items():
            base = cfg["rules"].setdefault(key, {"enabled": True, "weight": 1.0, "params": {}})
            if "enabled" in rule_cfg:
                base["enabled"] = rule_cfg["enabled"]
            if "weight" in rule_cfg:
                base["weight"] = rule_cfg["weight"]
            if "params" in rule_cfg:
                base.setdefault("params", {}).update(rule_cfg["params"] or {})
        if user.get("scoring"):
            cfg["scoring"].update(user["scoring"])
    return cfg
