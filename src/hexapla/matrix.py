"""Versioned evaluation matrix artefacts for Hexapla benchmarks."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MatrixResult:
    """One candidate's score for one eval item."""

    item_id: str
    candidate: str
    score: float
    justification: str
    cost_usd: float
    latency_ms: float
    trace_id: str
    contamination: dict[str, Any] = field(default_factory=dict)
    response: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "candidate": self.candidate,
            "score": self.score,
            "justification": self.justification,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "trace_id": self.trace_id,
            "contamination": self.contamination,
            "response": self.response,
        }


@dataclass
class EvaluationMatrix:
    """Container for all per-item benchmark results."""

    concordance: str
    eval_set: str
    rubric: str
    candidates: list[str]
    matrix_version: str
    results: list[MatrixResult] = field(default_factory=list)

    def add_result(self, result: MatrixResult) -> None:
        if result.candidate not in self.candidates:
            self.candidates.append(result.candidate)
        self.results.append(result)

    def aggregates(self) -> dict[str, dict[str, float | int]]:
        aggregates: dict[str, dict[str, float | int]] = {}
        for candidate in self.candidates:
            candidate_results = [r for r in self.results if r.candidate == candidate]
            if not candidate_results:
                aggregates[candidate] = {
                    "mean_score": 0.0,
                    "total_cost": 0.0,
                    "mean_latency_ms": 0.0,
                    "items_run": 0,
                }
                continue
            count = len(candidate_results)
            aggregates[candidate] = {
                "mean_score": round(sum(r.score for r in candidate_results) / count, 6),
                "total_cost": round(sum(r.cost_usd for r in candidate_results), 6),
                "mean_latency_ms": round(sum(r.latency_ms for r in candidate_results) / count, 3),
                "items_run": count,
            }
        return aggregates

    def to_dict(self) -> dict[str, Any]:
        return {
            "matrix_version": self.matrix_version,
            "concordance": self.concordance,
            "eval_set": self.eval_set,
            "rubric": self.rubric,
            "candidates": self.candidates,
            "results": [result.to_dict() for result in self.results],
            "aggregates": self.aggregates(),
        }

    def save(self, output_dir: str | Path) -> tuple[Path, Path]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        safe_version = self.matrix_version.replace(":", "-").replace("/", "-")
        json_path = output / f"evaluation_matrix_{safe_version}.json"
        csv_path = output / f"evaluation_matrix_{safe_version}.csv"

        json_path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "item_id",
                    "candidate",
                    "score",
                    "justification",
                    "cost_usd",
                    "latency_ms",
                    "trace_id",
                    "contamination_flagged",
                ],
            )
            writer.writeheader()
            for result in self.results:
                writer.writerow(
                    {
                        "item_id": result.item_id,
                        "candidate": result.candidate,
                        "score": result.score,
                        "justification": result.justification,
                        "cost_usd": result.cost_usd,
                        "latency_ms": result.latency_ms,
                        "trace_id": result.trace_id,
                        "contamination_flagged": result.contamination.get("flagged", False),
                    }
                )
        return json_path, csv_path
