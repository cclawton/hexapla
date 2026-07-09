import json
from pathlib import Path

import pytest

from hexapla.benchmark_loop import load_eval_set
from hexapla.schema import validate_eval_item, validate_eval_set


VALID_ITEM = {
    "id": "ozrock-001",
    "category": "artist_lineage",
    "prompt": "Question?",
    "expected": "Answer",
    "acceptable_answers": ["Answer"],
    "source": {"title": "Source", "url": "https://example.com/source"},
    "scoring_notes": "Score only the expected answer.",
    "difficulty": "easy",
    "tags": ["tag"],
}


def test_validate_eval_item_accepts_full_ozrock_shape():
    validate_eval_item(dict(VALID_ITEM), strict=True)


@pytest.mark.parametrize(
    "field",
    ["id", "prompt", "expected", "acceptable_answers", "source", "scoring_notes", "difficulty", "tags"],
)
def test_validate_eval_item_rejects_missing_required_strict_field(field):
    item = dict(VALID_ITEM)
    item.pop(field)

    with pytest.raises(ValueError, match=field):
        validate_eval_item(item, strict=True)


def test_validate_eval_item_rejects_invalid_difficulty():
    item = dict(VALID_ITEM, difficulty="tricky")

    with pytest.raises(ValueError, match="difficulty"):
        validate_eval_item(item, strict=True)


def test_validate_eval_item_rejects_missing_source_url():
    item = dict(VALID_ITEM, source={"title": "Source"})

    with pytest.raises(ValueError, match="source.url"):
        validate_eval_item(item, strict=True)


def test_validate_eval_set_rejects_duplicate_ids():
    first = dict(VALID_ITEM)
    second = dict(VALID_ITEM)

    with pytest.raises(ValueError, match="duplicate"):
        validate_eval_set([first, second], strict=True)


def test_validate_eval_item_non_strict_preserves_existing_smoke_shape():
    validate_eval_item({"id": "q1", "prompt": "Question?"})


def test_load_eval_set_reports_line_number_for_invalid_json(tmp_path: Path):
    eval_path = tmp_path / "bad.jsonl"
    eval_path.write_text('{"id": "q1", "prompt": "ok"}\n{nope}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="line 2"):
        load_eval_set(eval_path)


def test_load_eval_set_uses_schema_validation_for_required_prompt(tmp_path: Path):
    eval_path = tmp_path / "bad.jsonl"
    eval_path.write_text(json.dumps({"id": "q1"}) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="prompt"):
        load_eval_set(eval_path)
