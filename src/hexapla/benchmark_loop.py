"""Deterministic Hexapla benchmark loop.

The outer control flow is Python, not an unconstrained long-running agent:
every candidate × every item is executed exactly once, then scored by a separate
verifier. This keeps Stage 4 reliable while preserving the producer≠verifier
loop pattern.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from .contamination import screen_contamination
from .matrix import EvaluationMatrix, MatrixResult
from .scoring import ScoreResult, VerifierBackend, score_item
from .sut_contract import SystemUnderTest


@dataclass(frozen=True)
class BenchmarkConfig:
    concordance: str
    eval_set_path: Path
    rubric_path: Path
    output_dir: Path
    matrix_version: str | None = None
    max_items: int | None = None
    max_cost_usd: float | None = None
    contamination: bool = True
    contamination_threshold: float = 0.2


def load_eval_set(path: str | Path) -> list[dict]:
    """Load a Concordance eval set from JSONL."""

    eval_path = Path(path)
    items: list[dict] = []
    for line_number, line in enumerate(eval_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
        if "id" not in item:
            raise ValueError(f"Eval item on line {line_number} must include 'id'")
        if "prompt" not in item:
            raise ValueError(f"Eval item on line {line_number} must include 'prompt'")
        items.append(item)
    return items


def _default_version() -> str:
    return "v" + datetime.now().strftime("%Y%m%d-%H%M%S")


def run_benchmark(
    config: BenchmarkConfig,
    suts: list[SystemUnderTest],
    verifier: VerifierBackend,
    scorer: Callable[[dict, str], ScoreResult] | None = None,
) -> tuple[EvaluationMatrix, tuple[Path, Path]]:
    """Run every SUT over every eval item and write matrix artefacts."""

    if not suts:
        raise ValueError("At least one system under test is required")

    items = load_eval_set(config.eval_set_path)
    if config.max_items is not None:
        items = items[: config.max_items]

    matrix = EvaluationMatrix(
        concordance=config.concordance,
        eval_set=str(config.eval_set_path),
        rubric=str(config.rubric_path),
        candidates=[sut.name for sut in suts],
        matrix_version=config.matrix_version or _default_version(),
    )

    total_cost = 0.0

    def apply_score(item: dict, response: str) -> ScoreResult:
        if scorer is not None:
            return scorer(item, response)
        return score_item(item=item, response=response, rubric_path=config.rubric_path, verifier=verifier)

    for sut in suts:
        for item in items:
            if config.max_cost_usd is not None and total_cost >= config.max_cost_usd:
                raise RuntimeError(f"Benchmark cost limit reached: ${total_cost:.4f}")

            sut_result = sut.call(str(item["prompt"]))
            total_cost += sut_result.cost_usd
            score = apply_score(item, sut_result.response)

            contamination = {"variance": 0.0, "flagged": False, "scores": []}
            if config.contamination:
                contamination_result = screen_contamination(
                    item=item,
                    sut=sut,
                    scorer=apply_score,
                    threshold=config.contamination_threshold,
                )
                contamination = contamination_result.to_dict()

            matrix.add_result(
                MatrixResult(
                    item_id=str(item["id"]),
                    candidate=sut.name,
                    score=score.score,
                    justification=score.justification,
                    cost_usd=sut_result.cost_usd,
                    latency_ms=sut_result.latency_ms,
                    trace_id=sut_result.trace_id,
                    contamination=contamination,
                    response=sut_result.response,
                )
            )

    paths = matrix.save(config.output_dir)
    return matrix, paths
