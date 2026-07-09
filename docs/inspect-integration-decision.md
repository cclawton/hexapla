# Inspect AI Integration Decision

Date: 2026-07-09
Status: Accepted for next implementation slice

## Decision

Hexapla will use Inspect AI as an **optional execution backend**, not as the core framework and not as a hard dependency.

The integration depth is:

1. **Hexapla remains the source of truth** for:
   - Concordance folder structure
   - eval item schema
   - SUT/rung vocabulary
   - normalized evaluation matrix
   - cost/latency/candidate comparison
   - Gate decision artefacts

2. **Inspect AI becomes an optional runner** for:
   - standard eval execution
   - dataset/task/scorer conventions
   - Inspect logs and traces
   - comparison with the broader eval ecosystem

3. **The native Hexapla runner remains supported** for:
   - no-network smoke tests
   - simple deterministic CI checks
   - quick local harness validation
   - cases where Inspect is not installed

## Why not replace the native runner now?

The current native runner is small and already validates the Hexapla-specific shape:

```text
Concordance eval set → SUT response → separate scoring → matrix → Gate evidence
```

Inspect is valuable, but it does not own Hexapla's domain-specific decision layer:

```text
matrix → cheapest adequate rung → Gate decision
```

Replacing the runner immediately would add dependency and integration risk before the OzRock use case has enough real signal. The better next step is to support both modes on the same eval set and compare.

## Current state

Implemented already:

- `src/hexapla/inspect_adapter.py`
  - converts Hexapla eval items into Inspect-style JSONL samples
  - exports JSONL
  - generates starter Inspect task source
  - does not require `inspect_ai` at import time

Not installed locally yet:

- `inspect_ai`

Latest visible PyPI package from `pip index versions inspect-ai`:

- `inspect-ai 0.3.245`

## Next implementation slice

Add an optional Inspect extra and CLI export command.

Target shape:

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0.0"]
inspect = ["inspect-ai>=0.3.245"]
```

Add CLI support:

```bash
PYTHONPATH=src python main_benchmark.py export-inspect \
  --eval-set benchmarks/ozrock/eval_set.jsonl \
  --rubric benchmarks/ozrock/rubric.md \
  --task-name ozrock \
  --output-dir benchmarks/ozrock
```

Expected outputs:

```text
benchmarks/ozrock/inspect_samples.jsonl
benchmarks/ozrock/inspect_task.py
```

Then run a separate manual Inspect smoke only when the optional dependency is installed:

```bash
python -m pip install -e '.[inspect]'
inspect eval benchmarks/ozrock/inspect_task.py --model openai/gpt-4o-mini
```

## Acceptance criteria for adopting Inspect as a real runner

Inspect should become a first-class optional runner only if it passes all of these:

- Uses the same Hexapla OzRock eval items without losing metadata.
- Produces inspect logs/traces that are more useful than the native matrix alone.
- Can be normalized back into the Hexapla matrix shape.
- Does not force Inspect as a dependency for no-network tests.
- Does not weaken the separate verifier/scorer principle.
- Does not obscure cost/latency accounting.

## Rejected options

### Make Inspect mandatory now

Rejected. It would add dependency weight before the native Hexapla contracts are stable.

### Keep only the native runner forever

Rejected. It risks reinventing too much benchmark infrastructure if Hexapla grows beyond small smoke runs.

### Maintain two unrelated eval formats

Rejected. Hexapla JSONL remains canonical; Inspect samples are generated from it.

## Practical summary

Use this layering:

```text
Hexapla schema and Gate logic
        ↓
Runner interface
        ↓
Native runner       Inspect runner/export
        ↓            ↓
Hexapla matrix      Inspect logs → Hexapla matrix
```

So: **optional Inspect execution backend, canonical Hexapla schema, canonical Hexapla matrix and Gate.**
