from pathlib import Path

from hexapla.scoring import ScoreResult, build_scoring_prompt, parse_score_json, score_item


class FakeVerifier:
    def __init__(self, text):
        self.text = text
        self.messages = None

    def chat(self, messages, temperature=0.0, max_tokens=None):
        self.messages = messages

        class Result:
            text = self.text

        return Result()


def test_parse_score_json_accepts_fenced_json():
    text = 'Here you go:\n```json\n{"score": 0.75, "justification": "mostly correct", "flags": ["minor"]}\n```'

    result = parse_score_json(text)

    assert result == ScoreResult(score=0.75, justification="mostly correct", flags=["minor"])


def test_parse_score_json_clamps_score_and_defaults_flags():
    result = parse_score_json('{"score": 2, "justification": "too high"}')

    assert result.score == 1.0
    assert result.justification == "too high"
    assert result.flags == []


def test_build_scoring_prompt_contains_item_response_and_rubric():
    prompt = build_scoring_prompt(
        item={"id": "q1", "prompt": "Who?", "expected": "A"},
        response="answer text",
        rubric="Score from 0 to 1",
    )

    assert "Score from 0 to 1" in prompt
    assert '"id": "q1"' in prompt
    assert "answer text" in prompt
    assert "JSON" in prompt


def test_score_item_calls_verifier_and_returns_score(tmp_path: Path):
    rubric_path = tmp_path / "rubric.md"
    rubric_path.write_text("0 to 1 rubric")
    verifier = FakeVerifier('{"score": 0.4, "justification": "weak", "flags": ["missing_evidence"]}')

    result = score_item(
        item={"id": "q1", "prompt": "Name an Australian band"},
        response="Nirvana",
        rubric_path=rubric_path,
        verifier=verifier,
    )

    assert result.score == 0.4
    assert result.flags == ["missing_evidence"]
    assert verifier.messages[0]["role"] == "user"
    assert "0 to 1 rubric" in verifier.messages[0]["content"]


def test_parse_score_json_rejects_missing_score():
    try:
        parse_score_json('{"justification": "no score"}')
    except ValueError as exc:
        assert "score" in str(exc)
    else:
        raise AssertionError("expected ValueError")
