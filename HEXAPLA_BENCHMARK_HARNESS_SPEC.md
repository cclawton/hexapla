# Hexapla Benchmark Harness — Concrete Spec

## Purpose
Reusable Stage 4 (Measure) component for any Hexapla Concordance. Runs candidate models / composed architectures against a JSONL eval set, produces versioned evaluation matrix + cost/latency data + contamination flags. Feeds directly into Stage 5 (Gate).

Built on the existing react-harness ReAct loop infrastructure. Backend-agnostic. Producer ≠ Verifier.

## High-Level Architecture
- **Goal spec**: Path to eval_set.jsonl + rubric.md + system-under-test contract
- **Loop driver**: Adapted ReAct harness (plan → act → observe → iterate → verify → done)
- **System-under-test (SUT) interface**: Simple contract — `call(prompt) -> (response, latency_ms, cost_usd, trace_id)`
- **Scoring**: Separate verifier model applies rubric per item
- **Contamination screening**: Perturbation sub-loop (paraphrase, reorder, synonym swap)
- **Output artefact**: `evaluation_matrix_v{date}.json` + CSV summary + full traces

## Repo Structure (extension of react-harness)
```
react-harness/
├── src/react_harness/
│   ├── loop.py                 # existing — will be generalized
│   ├── benchmark_loop.py       # NEW: benchmark-specific loop + goal handling
│   ├── sut_contract.py         # NEW: SUT interface + OpenRouter + local backends
│   ├── scoring.py              # NEW: rubric application + verifier
│   ├── contamination.py        # NEW: perturbation generators + screening loop
│   ├── matrix.py               # NEW: evaluation matrix assembly + versioning
│   ├── instrumentation.py      # extended for per-item cost/latency/trace
│   └── config.py               # extended for eval paths, rubric, limits
├── benchmarks/                 # NEW top-level
│   ├── eval_sets/              # JSONL files (one per Concordance)
│   │   └── apra_oz_rock.jsonl
│   ├── rubrics/                # markdown rubrics
│   │   └── apra_oz_rock_rubric.md
│   └── results/                # generated matrices
├── examples/
│   └── benchmark_example/      # goal.md + tiny eval set for smoke test
├── main_benchmark.py           # NEW CLI entry point
├── requirements.txt            # add any new deps (jsonschema, etc.)
└── HEXAPLA_BENCHMARK_HARNESS_SPEC.md
```

## File Layout & Responsibilities

### benchmark_loop.py
Core loop adapted from loop.py:
- Loads eval_set.jsonl into memory (list of items)
- For each candidate in SUT contract:
  - For each eval item:
    - Run contamination screening (optional, configurable)
    - Execute SUT call
    - Capture raw response + metadata
    - Score via verifier
    - Record to matrix
- Bounded: max_items, max_cost_per_candidate, max_wall_time
- Escalation on budget or persistent errors

Key difference from coding loop: actions are now "call_sut", "score_item", "record_result", "run_perturbation".

### sut_contract.py
Defines the interface every candidate must satisfy:

```python
from typing import Protocol, NamedTuple

class SUTResult(NamedTuple):
    response: str
    latency_ms: float
    cost_usd: float
    trace_id: str

class SystemUnderTest(Protocol):
    def call(self, prompt: str, **kwargs) -> SUTResult: ...
    @property
    def name(self) -> str: ...
    @property
    def metadata(self) -> dict: ...   # model, provider, version, params
```

Implementations:
- OpenRouterSUT (existing backend.py reused)
- LocalVLLMSUT (future)
- ComposedArchitectureSUT (API wrapper around multi-model pipeline)

### scoring.py
- Loads rubric.md
- Verifier prompt template: "Apply this rubric to the item and response. Output JSON: {score: 0-1, justification, flags}"
- Separate verifier model (configurable, default GLM-5.2 or Claude)
- Per-item score + justification stored

### contamination.py
- Perturbation operators: paraphrase, entity_swap, order_shuffle, synonym
- Sub-loop runs original + 3 perturbations per item
- Flags if score variance > threshold (e.g. 0.2)

### matrix.py
Output format (versioned JSON):

```json
{
  "matrix_version": "2026-07-07",
  "concordance": "apra_oz_rock",
  "eval_set": "apra_oz_rock.jsonl",
  "rubric": "apra_oz_rock_rubric.md",
  "candidates": ["glm-5.2", "claude-opus-4.8", ...],
  "results": [
    {
      "item_id": "q001",
      "candidate": "glm-5.2",
      "score": 0.85,
      "justification": "...",
      "cost_usd": 0.0032,
      "latency_ms": 1240,
      "trace_id": "trace_abc123",
      "contamination": {"variance": 0.05, "flagged": false}
    }
  ],
  "aggregates": {
    "glm-5.2": {"mean_score": 0.78, "total_cost": 1.24, "items_run": 47}
  }
}
```

Also emits `matrix_v{date}.csv` for quick Gate review.

## Loop Design (adapted ReAct)

```
GOAL: "Benchmark these candidates against apra_oz_rock.jsonl using the rubric. Capture scores, costs, contamination flags. Produce evaluation_matrix."
  ↓
PLAN (model decides: next candidate? next item? run perturbation?)
  ↓
ACT: call_sut | score_item | record_result | run_perturbation
  ↓
OBSERVE: SUT response + metadata OR verifier JSON OR matrix write confirmation
  ↓
ITERATE: feed observation, update internal state (current item index, scores so far)
  ↓
VERIFY: separate verifier checks scoring consistency across sample of items
  ↓
DONE: all candidates × all items complete → write matrix artefact
```

The benchmark driver itself is not a single long-running ReAct agent — it is a Python orchestrator that uses the ReAct pattern only where needed (e.g., complex scoring decisions). Most flow is deterministic Python for reliability and cost control.

## Tool Interface (new tools added to tools.py)

- `call_sut(candidate_name, prompt)` → returns SUTResult
- `apply_rubric(item, response, rubric_path)` → calls verifier, returns score JSON
- `record_to_matrix(item_id, candidate, score, metadata)`
- `generate_perturbation(item, operator)` → returns perturbed text
- `write_matrix(output_path)`

## CLI (main_benchmark.py)

```bash
python main_benchmark.py \
  --eval-set benchmarks/eval_sets/apra_oz_rock.jsonl \
  --rubric benchmarks/rubrics/apra_oz_rock_rubric.md \
  --candidates glm-5.2,claude-opus-4.8 \
  --sut-contract configs/sut_openrouter.yaml \
  --output benchmarks/results/ \
  --max-cost 50
```

## First Use Case
Once built: run the APRA / Oz-rock Concordance eval set through it. Low-stakes, identity-fit, tests frontier model knowledge gaps on Australian music history vs American-centric training data.

## Next Steps After Spec
1. Implement sut_contract.py + OpenRouter adapter
2. Port scoring + matrix modules
3. Wire benchmark_loop.py
4. Smoke test on tiny 5-item eval set
5. Run full APRA set on 2–3 candidates

This spec turns the existing Loop Architect work into the actual Hexapla Stage 4 engine. Reusable, measurable, artefact-producing.