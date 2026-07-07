import json
import subprocess
import sys
from pathlib import Path


def test_main_benchmark_echo_smoke(tmp_path: Path):
    eval_path = tmp_path / "eval.jsonl"
    rubric_path = tmp_path / "rubric.md"
    contract_path = tmp_path / "sut_contract.json"
    output_dir = tmp_path / "results"

    eval_path.write_text('{"id": "q1", "prompt": "Question?"}\n')
    rubric_path.write_text("score 0 to 1")
    contract_path.write_text(json.dumps({"candidates": [{"name": "echo", "type": "echo", "prefix": "answer: "}]}))

    result = subprocess.run(
        [
            sys.executable,
            "main_benchmark.py",
            "--eval-set",
            str(eval_path),
            "--rubric",
            str(rubric_path),
            "--sut-contract",
            str(contract_path),
            "--output",
            str(output_dir),
            "--concordance",
            "smoke",
            "--matrix-version",
            "vcli",
            "--no-contamination",
            "--echo-scorer",
        ],
        cwd=Path(__file__).resolve().parents[1],
        env={"PYTHONPATH": "src"},
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "evaluation_matrix_vcli.json" in result.stdout
    matrix_path = output_dir / "evaluation_matrix_vcli.json"
    assert matrix_path.exists()
    data = json.loads(matrix_path.read_text())
    assert data["results"][0]["response"] == "answer: Question?"
    assert data["results"][0]["score"] == 1.0
