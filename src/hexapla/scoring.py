"""Rubric scoring for Hexapla benchmark items."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class ScoreResult:
    """Verifier-applied score for one response."""

    score: float
    justification: str
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "justification": self.justification,
            "flags": self.flags,
        }


class VerifierBackend(Protocol):
    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> Any: ...


def _parse_first_json(text: str) -> dict[str, Any] | None:
    fenced = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    candidates = [fenced.group(1)] if fenced else []
    candidates.append(text)

    for candidate in candidates:
        start = candidate.find("{")
        if start < 0:
            continue
        depth = 0
        in_string = False
        escape = False
        for idx in range(start, len(candidate)):
            char = candidate[idx]
            if escape:
                escape = False
                continue
            if char == "\\" and in_string:
                escape = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(candidate[start : idx + 1])
                    except json.JSONDecodeError:
                        break
    return None


def parse_score_json(text: str) -> ScoreResult:
    """Parse verifier JSON into a ScoreResult."""

    data = _parse_first_json(text)
    if data is None:
        raise ValueError("Verifier response did not contain JSON")
    if "score" not in data:
        raise ValueError("Verifier JSON must include 'score'")

    try:
        raw_score = float(data["score"])
    except (TypeError, ValueError) as exc:
        raise ValueError("Verifier 'score' must be numeric") from exc

    score = max(0.0, min(1.0, raw_score))
    justification = str(data.get("justification", ""))
    flags_value = data.get("flags", [])
    flags = [str(flag) for flag in flags_value] if isinstance(flags_value, list) else [str(flags_value)]
    return ScoreResult(score=score, justification=justification, flags=flags)


def build_scoring_prompt(item: dict[str, Any], response: str, rubric: str) -> str:
    """Build the verifier prompt for one benchmark item."""

    item_json = json.dumps(item, indent=2, ensure_ascii=False, sort_keys=True)
    return f"""Apply the rubric to the model response for this benchmark item.

RUBRIC:
{rubric}

EVAL ITEM:
{item_json}

MODEL RESPONSE:
{response}

Return ONLY JSON with this shape:
{{"score": <number from 0 to 1>, "justification": "<brief reason>", "flags": ["<optional flags>"]}}
"""


def score_item(
    item: dict[str, Any],
    response: str,
    rubric_path: str | Path,
    verifier: VerifierBackend,
    max_tokens: int = 1024,
) -> ScoreResult:
    """Score one response by calling the separate verifier backend."""

    rubric = Path(rubric_path).read_text(encoding="utf-8")
    prompt = build_scoring_prompt(item=item, response=response, rubric=rubric)
    result = verifier.chat(
        [{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=max_tokens,
    )
    return parse_score_json(result.text)
