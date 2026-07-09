import json
from pathlib import Path


OZROCK_DIR = Path("benchmarks/ozrock")


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_ozrock_benchmark_bundle_files_exist():
    assert (OZROCK_DIR / "README.md").exists()
    assert (OZROCK_DIR / "eval_set.jsonl").exists()
    assert (OZROCK_DIR / "rubric.md").exists()
    assert (OZROCK_DIR / "sut_contract.example.json").exists()
    assert (OZROCK_DIR / "gate_template.md").exists()


def test_ozrock_eval_set_has_five_source_linked_items_with_unique_ids():
    items = _load_jsonl(OZROCK_DIR / "eval_set.jsonl")

    assert len(items) >= 5
    ids = [item["id"] for item in items]
    assert len(ids) == len(set(ids))

    for item in items:
        assert item["id"].startswith("ozrock-")
        assert item["category"] in {
            "artist_lineage",
            "song_catalogue",
            "venue_scene",
            "label_history",
            "chart_context",
            "licensing_context",
            "disambiguation",
        }
        assert item["prompt"]
        assert item["expected"]
        assert isinstance(item["acceptable_answers"], list)
        assert item["acceptable_answers"]
        assert item["source"]["title"]
        assert item["source"]["url"].startswith("https://")
        assert item["scoring_notes"]
        assert item["difficulty"] in {"easy", "medium", "hard"}
        assert isinstance(item["tags"], list)
        assert item["tags"]


def test_ozrock_rubric_declares_scoring_scale_and_json_contract():
    rubric = (OZROCK_DIR / "rubric.md").read_text(encoding="utf-8")

    assert "## Scoring Scale" in rubric
    assert "## JSON Output" in rubric
    assert '"score"' in rubric
    assert '"justification"' in rubric
    assert '"flags"' in rubric


def test_ozrock_example_sut_contract_is_no_network_echo_by_default():
    contract = json.loads((OZROCK_DIR / "sut_contract.example.json").read_text(encoding="utf-8"))

    assert contract["candidates"]
    assert all(candidate["type"] == "echo" for candidate in contract["candidates"])
