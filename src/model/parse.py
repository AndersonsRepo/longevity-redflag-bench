"""Answer extraction from raw model output, matching the LongevityBench answer
conventions (gold = option LETTER for classification/pairwise; number for regression;
comma/again list for generation). Robust by design — a 9B model formats poorly. Every
parse returns a structured result with a `failure_type`; it never raises.

`failure_type` is also the data behind the parse-success metric (grading-rubric-spec §4).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from schema.records import Format


@dataclass
class ParsedAnswer:
    answer: object                 # "A".. | float | list[str] | None
    failure_type: Optional[str]    # None=ok | "malformed" | "refusal" | "missing"
    raw: str
    path: Optional[str] = None     # how a letter was extracted: explicit|leading|fallback_last|none
                                   # ("fallback_last" = a low-confidence guess; audit it — verify_parsing.py)

    @property
    def ok(self) -> bool:
        return self.failure_type is None


_REFUSAL = re.compile(r"\b(i (cannot|can't|won't)|as an ai|unable to)\b", re.I)


def parse(raw: str, fmt: Format) -> ParsedAnswer:
    text = (raw or "").strip()
    if not text:
        return ParsedAnswer(None, "missing", raw)
    if _REFUSAL.search(text) and len(text) < 240:
        return ParsedAnswer(None, "refusal", raw)
    path = None
    try:
        if fmt == Format.regression:
            ans, path = _number(text), "numeric"
        elif fmt == Format.generation:
            ans, path = _set(text), "set"
        else:  # binary | multiclass | ternary | pairwise -> option letter
            ans, path = _letter(text)
    except Exception:
        return ParsedAnswer(None, "malformed", raw, path)
    return ParsedAnswer(ans, None if ans is not None else "malformed", raw, path)


def _letter(text: str):
    """Returns (letter|None, path). path records HOW it was found so a low-confidence
    fallback guess is never silent — verified 2026-05-24 (results/parse-audit.md): the
    fallback fires 0% across both models; Claude=explicit, Longevity-LLM=leading."""
    # The answer follows the thinking block; restrict to the region AFTER the last
    # </think> so stray "Patient A/B" mentions inside the reasoning can't be grabbed
    # (fixes the first-match mis-grade — vault ERR-20260523-002).
    region = text.rsplit("</think>", 1)[-1] if "</think>" in text else text
    # explicit "Answer: B" / "(B)" in the answer region
    m = re.search(r"\b(?:answer|option)\s*[:=]?\s*\(?([A-E])\)?", region, re.I)
    if m:
        return m.group(1).upper(), "explicit"
    # leading bare letter
    m = re.match(r"\(?([A-E])\)?[\.\):]?\b", region.strip(), re.I)
    if m:
        return m.group(1).upper(), "leading"
    # fallback: the LAST standalone A-E in the answer region (LOW CONFIDENCE — a guess)
    matches = re.findall(r"\b([A-E])\b", region)
    return (matches[-1].upper(), "fallback_last") if matches else (None, "none")


def _number(text: str) -> Optional[float]:
    m = re.search(r"-?\d+(\.\d+)?", text)
    return float(m.group(0)) if m else None


def _set(text: str) -> Optional[List[str]]:
    # strip a JSON-ish wrapper if present, then split on commas/newlines/semicolons
    body = re.sub(r"^.*?[:\[]", "", text, count=1) if (":" in text or "[" in text) else text
    items = [i.strip(" -*•\"'[]").lower() for i in re.split(r"[,\n;]", body)]
    items = [i for i in items if i]
    return items or None
