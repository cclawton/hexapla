import json
from pathlib import Path

from hexapla.matrix import EvaluationMatrix, MatrixResult


def test_matrix_result_serializes_expected_shape():
    result = MatrixResult(
        item_id="q1",
        candidate="glm",
        score=0.8,
        justification="good",
        cost_usd=0.01,
        latency_ms=120.0,
        trace_id="t1",
        contamination={"variance": 0.0, "flagged": False},
    )

    assert result.to_dict()["item_id"] == "q1"
    assert result.to_dict()["candidate"] == "glm"
    assert result.to_dict()["score"] == 0.8


def test_evaluation_matrix_adds_results_and_aggregates():
    matrix = EvaluationMatrix(
        concordance="oz_rock",
        eval_set="eval.jsonl",
        rubric="rubric.md",
        candidates=["glm", "opus"],
        matrix_version="2026-07-07",
    )
    matrix.add_result(MatrixResult("q1", "glm", 0.5, "ok", 0.10, 100, "t1"))
    matrix.add_result(MatrixResult("q2", "glm", 1.0, "great", 0.20, 200, "t2"))
    matrix.add_result(MatrixResult("q1", "opus", 0.25, "weak", 0.50, 300, "t3"))

    data = matrix.to_dict()

    assert data["aggregates"]["glm"] == {
        "mean_score": 0.75,
        "total_cost": 0.3,
        "mean_latency_ms": 150.0,
        "items_run": 2,
    }
    assert data["aggregates"]["opus"]["items_run"] == 1


def test_matrix_writes_json_and_csv(tmp_path: Path):
    matrix = EvaluationMatrix("oz_rock", "eval.jsonl", "rubric.md", ["glm"], "v1")
    matrix.add_result(MatrixResult("q1", "glm", 0.5, "ok", 0.1, 12.0, "trace"))

    json_path, csv_path = matrix.save(tmp_path)

    assert json_path.name == "evaluation_matrix_v1.json"
    assert csv_path.name == "evaluation_matrix_v1.csv"
    assert json.loads(json_path.read_text())["concordance"] == "oz_rock"
    assert "item_id,candidate,score" in csv_path.read_text()
    assert "q1,glm,0.5" in csv_path.read_text()
