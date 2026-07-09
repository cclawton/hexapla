import json
import subprocess
import sys
from pathlib import Path

import tomllib


def test_pyproject_declares_optional_inspect_extra():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    inspect_deps = pyproject["project"]["optional-dependencies"]["inspect"]

    assert any(dep.startswith("inspect-ai>=") for dep in inspect_deps)


def test_main_benchmark_export_inspect_writes_samples_and_task(tmp_path: Path):
    eval_path = tmp_path / "eval.jsonl"
    rubric_path = tmp_path / "rubric.md"
    output_dir = tmp_path / "inspect"
    eval_path.write_text(
        json.dumps(
            {
                "id": "ozrock-001",
                "category": "artist_lineage",
                "prompt": "Who?",
                "expected": "The Band",
                "acceptable_answers": ["The Band"],
                "source": {"title": "Source", "url": "https://example.com"},
                "scoring_notes": "Use expected answer.",
                "difficulty": "easy",
                "tags": ["tag"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    rubric_path.write_text("# Rubric\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "main_benchmark.py",
            "export-inspect",
            "--eval-set",
            str(eval_path),
            "--rubric",
            str(rubric_path),
            "--task-name",
            "ozrock",
            "--output-dir",
            str(output_dir),
        ],
        cwd=Path(__file__).resolve().parents[1],
        env={"PYTHONPATH": "src"},
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    samples_path = output_dir / "inspect_samples.jsonl"
    task_path = output_dir / "inspect_task.py"
    assert samples_path.exists()
    assert task_path.exists()
    rows = [json.loads(line) for line in samples_path.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["input"] == "Who?"
    assert rows[0]["target"] == "The Band"
    task_source = task_path.read_text(encoding="utf-8")
    assert "def ozrock" in task_source
    assert str(samples_path) in task_source
    assert str(rubric_path) in task_source
    assert "Wrote" in result.stdout
