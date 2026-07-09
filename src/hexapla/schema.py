"""Schema validation for Hexapla benchmark eval sets."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

VALID_CATEGORIES = {
    "artist_lineage",
    "song_catalogue",
    "venue_scene",
    "label_history",
    "chart_context",
    "licensing_context",
    "disambiguation",
}

VALID_DIFFICULTIES = {"easy", "medium", "hard"}

BASE_REQUIRED_FIELDS = ("id", "prompt")
STRICT_REQUIRED_FIELDS = (
    "id",
    "category",
    "prompt",
    "expected",
    "acceptable_answers",
    "source",
    "scoring_notes",
    "difficulty",
    "tags",
)


def _label(item: dict[str, Any], label: str | None = None) -> str:
    if label:
        return label
    item_id = item.get("id")
    return f"item {item_id}" if item_id else "eval item"


def _require_non_empty_string(item: dict[str, Any], field: str, *, label: str) -> None:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must include non-empty '{field}'")


def _require_non_empty_list(item: dict[str, Any], field: str, *, label: str) -> None:
    value = item.get(field)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must include non-empty '{field}' list")


def validate_eval_item(item: dict[str, Any], *, strict: bool = False, label: str | None = None) -> None:
    """Validate one benchmark eval item.

    Non-strict mode preserves the existing smoke-test contract: only `id` and
    `prompt` are mandatory. Strict mode is for real Concordance bundles like
    OzRock, where source-linked scoring metadata is required.
    """

    if not isinstance(item, dict):
        raise ValueError("eval item must be an object")

    item_label = _label(item, label)
    required = STRICT_REQUIRED_FIELDS if strict else BASE_REQUIRED_FIELDS
    for field in required:
        if field not in item:
            raise ValueError(f"{item_label} missing required field '{field}'")

    _require_non_empty_string(item, "id", label=item_label)
    _require_non_empty_string(item, "prompt", label=item_label)

    if not strict:
        return

    _require_non_empty_string(item, "category", label=item_label)
    if item["category"] not in VALID_CATEGORIES:
        raise ValueError(f"{item_label} has invalid category: {item['category']}")

    if not isinstance(item.get("expected"), (str, dict, list)) or item.get("expected") in ("", [], {}):
        raise ValueError(f"{item_label} must include non-empty 'expected'")

    _require_non_empty_list(item, "acceptable_answers", label=item_label)

    source = item.get("source")
    if not isinstance(source, dict):
        raise ValueError(f"{item_label} must include object 'source'")
    if not isinstance(source.get("title"), str) or not source["title"].strip():
        raise ValueError(f"{item_label} must include non-empty 'source.title'")
    if not isinstance(source.get("url"), str) or not source["url"].startswith("https://"):
        raise ValueError(f"{item_label} must include https 'source.url'")

    _require_non_empty_string(item, "scoring_notes", label=item_label)
    _require_non_empty_string(item, "difficulty", label=item_label)
    if item["difficulty"] not in VALID_DIFFICULTIES:
        raise ValueError(f"{item_label} has invalid difficulty: {item['difficulty']}")

    _require_non_empty_list(item, "tags", label=item_label)
    if not all(isinstance(tag, str) and tag.strip() for tag in item["tags"]):
        raise ValueError(f"{item_label} tags must be non-empty strings")


def validate_eval_set(items: Iterable[dict[str, Any]], *, strict: bool = False) -> None:
    """Validate a benchmark eval set and reject duplicate IDs."""

    seen: set[str] = set()
    for index, item in enumerate(items, start=1):
        validate_eval_item(item, strict=strict, label=f"item {index}")
        item_id = str(item["id"])
        if item_id in seen:
            raise ValueError(f"duplicate eval item id: {item_id}")
        seen.add(item_id)
