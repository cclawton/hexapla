"""Inspect AI task spike for the ozrock Hexapla benchmark.

Run after installing Inspect AI, for example:
    inspect eval benchmarks/ozrock/inspect_task.py --model openrouter/openai/gpt-4o-mini
"""

from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import json_dataset
from inspect_ai.scorer import model_graded_qa
from inspect_ai.solver import generate

_TASK_DIR = Path(__file__).resolve().parent


@task
def ozrock():
    rubric = (_TASK_DIR / "rubric.md").read_text(encoding="utf-8")
    dataset_path = _TASK_DIR / "inspect_samples.jsonl"
    return Task(
        dataset=json_dataset(str(dataset_path)),
        solver=generate(),
        scorer=model_graded_qa(
            instructions=rubric,
            partial_credit=True,
        ),
    )
