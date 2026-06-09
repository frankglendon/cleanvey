"""The LLM judge (Anthropic Claude by default).

This module is the *only* place that talks to an LLM. It powers the semantic
layer (the off-topic check). Set `ANTHROPIC_API_KEY` (directly or via a .env
file) to run it.

It is also designed to fail soft for robustness: if the key or the `anthropic`
package is missing, `get_client()` returns None and the LLM rule is skipped with
a note in the report — the deterministic rule engine still runs either way.
"""
from __future__ import annotations

import json
import os
import re
from typing import List, Optional

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def _load_dotenv() -> None:
    """Minimal .env loader so users don't need python-dotenv."""
    path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass


def _extract_json(text: str) -> str:
    """Pull the first {...} block out of a model response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else "{}"


class LLMClient:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self.available = False
        self._client = None
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key)
            self.available = True
        except Exception:
            self.available = False

    def classify_offtopic(self, question: str, answers: List[str], batch_size: int = 20) -> List[bool]:
        """Return one bool per answer: True if it does not address `question`.

        Empty answers are treated as on-topic (missingness is a separate rule).
        Any error degrades gracefully to all-False.
        """
        results = [False] * len(answers)
        if not self.available:
            return results

        todo = [
            (i, str(a)) for i, a in enumerate(answers)
            if str(a).strip() and str(a).strip().lower() != "nan"
        ]
        for start in range(0, len(todo), batch_size):
            batch = todo[start:start + batch_size]
            verdicts = self._classify_batch(question, [a for _, a in batch])
            for (i, _), v in zip(batch, verdicts):
                results[i] = v
        return results

    def _classify_batch(self, question: str, answers: List[str]) -> List[bool]:
        listing = "\n".join(f"{i}. {a}" for i, a in enumerate(answers))
        prompt = (
            "你是问卷质量审核助手。下面是某道开放题及若干受访者的回答。\n"
            "请判断每条回答是否“答非所问”（与问题无关、无意义、答错题）。\n"
            f"\n【问题】{question}\n\n【回答】\n{listing}\n\n"
            "只返回 JSON 对象，键是回答编号(字符串)，值是 true(答非所问)/false(正常)。"
            "不要输出任何多余文字。"
        )
        try:
            msg = self._client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            data = json.loads(_extract_json(msg.content[0].text))
            return [bool(data.get(str(i), False)) for i in range(len(answers))]
        except Exception:
            return [False] * len(answers)


_client: Optional[LLMClient] = None
_initialized = False


def get_client() -> Optional[LLMClient]:
    """Return a ready LLM client, or None if LLM checks aren't available."""
    global _client, _initialized
    if _initialized:
        return _client
    _initialized = True

    _load_dotenv()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        _client = None
        return _client

    model = os.environ.get("CLEANVEY_LLM_MODEL", DEFAULT_MODEL)
    client = LLMClient(api_key, model)
    _client = client if client.available else None
    return _client


def llm_available() -> bool:
    return get_client() is not None
