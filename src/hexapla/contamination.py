"""Contamination and robustness screening helpers.

This is deliberately simple in v1: perturbations are deterministic so tests and
benchmark reruns are reproducible. More sophisticated paraphrase generation can
be plugged in later behind the same operator interface.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from .scoring import ScoreResult
from .sut_contract import SystemUnderTest


@dataclass(frozen=True)
class ContaminationResult:
    """Score stability across perturbations for one item/candidate."""

    variance: float
    flagged: bool
    scores: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"variance": self.variance, "flagged": self.flagged, "scores": self.scores}


def _split_sentences(text: str) -> list[str]:
    parts = re.findall(r"[^.!?]+[.!?]?", text)
    return [part.strip() for part in parts if part.strip()]


def generate_perturbation(item: dict[str, Any], operator: str) -> dict[str, Any]:
    """Return a perturbed copy of an eval item.

    Supported operators:
    - identity: unchanged prompt
    - order_shuffle: reverse sentence order
    - whitespace: normalize excessive whitespace
    - synonym: small deterministic phrasing swaps
    """

    prompt = str(item.get("prompt", ""))
    perturbed = dict(item)
    perturbed["id"] = f"{item.get('id', 'item')}__{operator}"

    if operator == "identity":
        perturbed["prompt"] = prompt
    elif operator == "order_shuffle":
        sentences = _split_sentences(prompt)
        perturbed["prompt"] = " ".join(reversed(sentences)) if len(sentences) > 1 else prompt
    elif operator == "whitespace":
        perturbed["prompt"] = " ".join(prompt.split())
    elif operator == "synonym":
        replacements = {
            "Name": "List",
            "name": "list",
            "three": "3",
            "Which": "What",
            "which": "what",
        }
        value = prompt
        for old, new in replacements.items():
            value = value.replace(old, new)
        perturbed["prompt"] = value
    else:
        raise ValueError(f"Unsupported perturbation operator: {operator}")

    return perturbed


def screen_contamination(
    item: dict[str, Any],
    sut: SystemUnderTest,
    scorer: Callable[[dict[str, Any], str], ScoreResult],
    operators: list[str] | None = None,
    threshold: float = 0.2,
) -> ContaminationResult:
    """Run perturbation checks and flag large score swings."""

    if operators is None:
        operators = ["identity", "order_shuffle", "whitespace", "synonym"]
    if not operators:
        return ContaminationResult(variance=0.0, flagged=False, scores=[])

    scores: list[float] = []
    for operator in operators:
        perturbed = generate_perturbation(item, operator)
        result = sut.call(str(perturbed.get("prompt", "")))
        score = scorer(perturbed, result.response)
        scores.append(score.score)

    variance = round(max(scores) - min(scores), 6) if scores else 0.0
    return ContaminationResult(variance=variance, flagged=variance > threshold, scores=scores)
