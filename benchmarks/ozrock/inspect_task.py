"""Inspect AI task spike for the ozrock Hexapla benchmark.

Run after installing Inspect AI, for example:
    inspect eval benchmarks/ozrock/inspect_task.py --model openai/gpt-4o-mini
"""

from inspect_ai import Task, task
from inspect_ai.dataset import json_dataset
from inspect_ai.scorer import model_graded_qa
from inspect_ai.solver import generate


@task
def ozrock():
    rubric = open("benchmarks/ozrock/rubric.md", encoding="utf-8").read()
    return Task(
        dataset=json_dataset("benchmarks/ozrock/inspect_samples.jsonl"),
        solver=generate(),
        scorer=model_graded_qa(template=rubric),
    )
