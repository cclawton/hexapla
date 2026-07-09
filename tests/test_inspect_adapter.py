import json
from pathlib import Path

from hexapla.inspect_adapter import build_inspect_task_source, export_inspect_jsonl, to_inspect_samples


def test_to_inspect_samples_maps_ozrock_items_to_input_target_metadata():
    items = [
        {
            "id": "ozrock-001",
            "category": "artist_lineage",
            "prompt": "Who?",
            "expected": "The Band",
            "acceptable_answers": ["The Band", "Band"],
            "source": {"title": "Source", "url": "https://example.com"},
            "scoring_notes": "Use expected answer.",
            "difficulty": "easy",
            "tags": ["tag"],
        }
    ]

    samples = to_inspect_samples(items)

    assert samples == [
        {
            "id": "ozrock-001",
            "input": "Who?",
            "target": "The Band",
            "metadata": {
                "category": "artist_lineage",
                "acceptable_answers": ["The Band", "Band"],
                "source": {"title": "Source", "url": "https://example.com"},
                "scoring_notes": "Use expected answer.",
                "difficulty": "easy",
                "tags": ["tag"],
            },
        }
    ]


def test_export_inspect_jsonl_writes_samples(tmp_path: Path):
    output_path = tmp_path / "inspect_samples.jsonl"
    samples = to_inspect_samples([{"id": "q1", "prompt": "Q?", "expected": "A"}])

    export_inspect_jsonl(samples, output_path)

    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert rows == samples


def test_build_inspect_task_source_contains_task_dataset_and_scorer_names():
    source = build_inspect_task_source(
        task_name="ozrock",
        dataset_path="benchmarks/ozrock/inspect_samples.jsonl",
        rubric_path="benchmarks/ozrock/rubric.md",
    )

    assert "from inspect_ai import Task, task" in source
    assert "json_dataset" in source
    assert "model_graded_qa" in source
    assert "benchmarks/ozrock/inspect_samples.jsonl" in source
    assert "benchmarks/ozrock/rubric.md" in source
