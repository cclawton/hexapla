# Inspect AI Smoke Eval Findings

Date: 2026-07-19
Status: Spike complete, normalization path identified

## What we ran

```bash
inspect eval benchmarks/ozrock/inspect_task.py \
  --model openrouter/openai/gpt-4o-mini \
  --limit 2
```

Same model (`openai/gpt-4o-mini`) and same 2 OzRock eval items as the native Hexapla OpenRouter smoke run.

## Results comparison

| Item | Model response | Native Hexapla score | Inspect score |
|---|---|---:|---:|
| `ozrock-001` (Bon Scott / The Valentines) | `Fraternity` | 0.25 | NaN (grade parse failure) |
| `ozrock-002` (Easybeats / Friday on My Mind) | `The Easybeats` | 1.0 | NaN (grade parse failure) |

## Key finding

Inspect's `model_graded_qa` scorer returned `NaN` for both items. The verifier model produced valid JSON (`{"score": 0.0, "justification": ...}` and `{"score": 1.0, ...}`), but Inspect's default grade pattern expects a different format (letter grade or numeric in a specific position).

The native Hexapla scorer parsed the same JSON correctly because it uses a brace-depth JSON extractor that finds the first complete JSON object regardless of surrounding text.

## What works

- Inspect loaded the exported `inspect_samples.jsonl` dataset correctly.
- Inspect called the model via OpenRouter successfully.
- Inspect captured the model responses and traces.
- Inspect produced a structured eval log.

## What does not work yet

- The scorer format is mismatched. Inspect's `model_graded_qa` default grade pattern does not match our rubric's JSON output contract.
- Inspect accuracy shows `NaN` because no grades were parsed.

## Normalization path

Two options to fix the scorer mismatch:

### Option A: Custom Inspect scorer (recommended)

Write a custom Inspect scorer that uses Hexapla's JSON extraction logic. This would:

1. Call the verifier model with the Hexapla rubric prompt
2. Parse the JSON response using Hexapla's `_parse_first_json`
3. Return an Inspect `Score` object with the numeric value

This keeps Hexapla's scoring contract intact and makes Inspect produce comparable scores.

### Option B: Adapt the rubric to Inspect's grade format

Change the rubric to output a letter grade or simple numeric that Inspect's `model_graded_qa` default pattern can parse. This is simpler but loses the richer JSON justification/flags structure that Hexapla needs for the Gate.

## Decision

Proceed with Option A. The Hexapla scoring contract (JSON with score, justification, flags) is load-bearing for the Gate decision. Adapting it to Inspect's default format would lose information.

The custom scorer would live in `src/hexapla/inspect_scorer.py` and be referenced by the generated `inspect_task.py`. It would require `inspect_ai` to be installed, but only when actually running Inspect evals.

## Cost comparison

- Native Hexapla 2-item run: $0.000012 (SUT only, verifier cost not separately tracked yet)
- Inspect 2-item run: 993 tokens total (906 input, 87 output) for the SUT calls; verifier calls not separately tracked by Inspect in the summary

Both are effectively free at this scale.

## Trace quality comparison

- Native Hexapla: JSON matrix with per-item score, justification, cost, latency, trace ID, contamination flag, and raw response.
- Inspect: structured eval log with full message history, model output, scorer output, and token usage. Richer trace data for debugging, but score is NaN due to format mismatch.

## Next steps

1. Fix the Inspect scorer mismatch (Option A: custom scorer)
2. Re-run the 2-item Inspect smoke
3. Compare native and Inspect scores on the same items
4. If they match, Inspect becomes a viable optional execution backend
5. If they diverge, investigate whether the scoring prompt or verifier model behaves differently under Inspect

## Repo state after smoke

- Inspect AI 0.3.248 installed locally
- `openai` upgraded to 2.46.0 (was 2.24.0) to satisfy Inspect's OpenRouter provider requirement
- `benchmarks/ozrock/inspect_task.py` regenerated with `__file__`-relative paths and `instructions=` scorer
- `benchmarks/ozrock/inspect_samples.jsonl` unchanged
- Inspect eval log saved at `logs/2026-07-19T03-27-58-00-00_ozrock_aZooLwWiiV8stVH7iq84gk.eval` (local, not committed)
