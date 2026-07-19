"""Inspect AI adapter helpers.

This module is intentionally dependency-light: it exports Hexapla eval items into
Inspect-style JSONL and can write a starter Inspect task file, but importing this
module does not require `inspect_ai` to be installed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def to_inspect_samples(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Hexapla eval items into Inspect JSON dataset samples."""

    samples: list[dict[str, Any]] = []
    for item in items:
        metadata = {
            "category": item.get("category"),
            "acceptable_answers": item.get("acceptable_answers", []),
            "source": item.get("source", {}),
            "scoring_notes": item.get("scoring_notes", ""),
            "difficulty": item.get("difficulty"),
            "tags": item.get("tags", []),
        }
        samples.append(
            {
                "id": str(item["id"]),
                "input": str(item["prompt"]),
                "target": item.get("expected", ""),
                "metadata": metadata,
            }
        )
    return samples


def export_inspect_jsonl(samples: list[dict[str, Any]], output_path: str | Path) -> Path:
    """Write Inspect-style samples as JSONL."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(sample, ensure_ascii=False, sort_keys=True) for sample in samples]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return path


def build_inspect_task_source(task_name: str, dataset_path: str, rubric_path: str) -> str:
    """Return a starter Inspect AI task module for this benchmark.

    The generated file is a spike artefact. It is not imported by Hexapla tests,
    so the main harness remains usable without Inspect installed.
    """

    return f'''"""Inspect AI task spike for the {task_name} Hexapla benchmark.

Run after installing Inspect AI, for example:
    inspect eval benchmarks/{task_name}/inspect_task.py --model openrouter/openai/gpt-4o-mini
"""

from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import json_dataset
from inspect_ai.scorer import model_graded_qa
from inspect_ai.solver import generate

_TASK_DIR = Path(__file__).resolve().parent


@task
def {task_name}():
    rubric = (_TASK_DIR / "{Path(rubric_path).name}").read_text(encoding="utf-8")
    dataset_path = _TASK_DIR / "{Path(dataset_path).name}"
    return Task(
        dataset=json_dataset(str(dataset_path)),
        solver=generate(),
        scorer=model_graded_qa(
            instructions=rubric,
            partial_credit=True,
        ),
    )
'''
