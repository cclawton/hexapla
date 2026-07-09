# OzRock Rubric

## Scoring Scale

- 1.0: Fully correct. Matches `expected` or an `acceptable_answers` variant. No material error.
- 0.75: Mostly correct, with a minor naming/detail issue that does not change the answer.
- 0.5: Partially correct but incomplete, ambiguous, or includes one non-fatal error.
- 0.25: Related Australian music knowledge but wrong answer.
- 0.0: Wrong, hallucinated, non-answer, refusal without cause, or answer contradicts the source/scoring notes.

## General Rules

1. Use `expected`, `acceptable_answers`, and `scoring_notes` from the eval item as the authority.
2. Do not reward confident but unsupported extra detail.
3. Penalize American or UK substitution when the prompt asks for Australian context.
4. Penalize answers that ignore the requested answer format.
5. If the response includes multiple answers and one is wrong, cap at 0.5 unless `scoring_notes` says otherwise.
6. If the response gives the correct answer plus irrelevant detail, score the answer but flag `overbroad_answer` when the prompt requested a short answer.

## Recommended Flags

- `format_violation`
- `wrong_country_context`
- `hallucinated_detail`
- `overbroad_answer`
- `ambiguous_answer`
- `source_conflict`
- `contamination_suspected`

## JSON Output

Return only JSON with this shape:

```json
{
  "score": 0.0,
  "justification": "brief reason",
  "flags": ["optional_flag"]
}
```
