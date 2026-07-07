import json
from pathlib import Path

from hexapla.benchmark_loop import BenchmarkConfig, load_eval_set, run_benchmark
from hexapla.scoring import ScoreResult
from hexapla.sut_contract import EchoSUT


class FakeVerifier:
    def chat(self, messages, temperature=0.0, max_tokens=None):
        class Result:
            text = '{"score": 0.5, "justification": "deterministic", "flags": []}'

        return Result()


def test_load_eval_set_reads_jsonl_and_requires_id_and_prompt(tmp_path: Path):
    eval_path = tmp_path / "eval.jsonl"
    eval_path.write_text('{"id": "q1", "prompt": "Question?"}\n\n{"id": "q2", "prompt": "Second?"}\n')

    assert load_eval_set(eval_path) == [
        {"id": "q1", "prompt": "Question?"},
        {"id": "q2", "prompt": "Second?"},
    ]


def test_load_eval_set_rejects_missing_prompt(tmp_path: Path):
    eval_path = tmp_path / "bad.jsonl"
    eval_path.write_text('{"id": "q1"}\n')

    try:
        load_eval_set(eval_path)
    except ValueError as exc:
        assert "prompt" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_run_benchmark_writes_matrix_for_all_candidates_and_items(tmp_path: Path):
    eval_path = tmp_path / "eval.jsonl"
    rubric_path = tmp_path / "rubric.md"
    output_dir = tmp_path / "results"
    eval_path.write_text('{"id": "q1", "prompt": "A?"}\n{"id": "q2", "prompt": "B?"}\n')
    rubric_path.write_text("score 0 to 1")

    matrix, paths = run_benchmark(
        config=BenchmarkConfig(
            concordance="smoke",
            eval_set_path=eval_path,
            rubric_path=rubric_path,
            output_dir=output_dir,
            matrix_version="vtest",
            contamination=False,
        ),
        suts=[EchoSUT("echo-a", prefix="A "), EchoSUT("echo-b", prefix="B ")],
        verifier=FakeVerifier(),
    )

    assert len(matrix.results) == 4
    assert matrix.aggregates()["echo-a"]["items_run"] == 2
    assert paths[0].exists()
    assert paths[1].exists()
    data = json.loads(paths[0].read_text())
    assert data["concordance"] == "smoke"
    assert data["aggregates"]["echo-b"]["mean_score"] == 0.5


def test_run_benchmark_can_use_custom_scorer_and_limit_items(tmp_path: Path):
    eval_path = tmp_path / "eval.jsonl"
    rubric_path = tmp_path / "rubric.md"
    eval_path.write_text('{"id": "q1", "prompt": "A?"}\n{"id": "q2", "prompt": "B?"}\n')
    rubric_path.write_text("score 0 to 1")

    matrix, _ = run_benchmark(
        config=BenchmarkConfig(
            concordance="smoke",
            eval_set_path=eval_path,
            rubric_path=rubric_path,
            output_dir=tmp_path,
            max_items=1,
            contamination=False,
        ),
        suts=[EchoSUT("echo")],
        verifier=FakeVerifier(),
        scorer=lambda item, response: ScoreResult(1.0, f"scored {item['id']}", []),
    )

    assert len(matrix.results) == 1
    assert matrix.results[0].score == 1.0
    assert matrix.results[0].item_id == "q1"
