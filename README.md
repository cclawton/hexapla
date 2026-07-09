# Hexapla

<p align="center">
  <img src="assets/hexapla-logo.png" alt="Hexapla logo" width="360">
</p>

Early-stage evaluation harness for repeatable benchmark runs and result matrices.

The current code focuses on a repeatable benchmark runner:

- load a JSONL evaluation set
- run one or more systems under test against each item
- score outputs with a separate verifier
- capture cost, latency, traces, and per-item justifications
- optionally run simple perturbation checks
- write versioned JSON and CSV result matrices

The project is intentionally small and experimental for now. Public positioning, domain framing, and contribution language are deliberately omitted until the work is ready to describe more openly.

## Smoke test

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python main_benchmark.py \
  --eval-set examples/benchmark_example/eval_set.jsonl \
  --rubric examples/benchmark_example/rubric.md \
  --sut-contract examples/benchmark_example/sut_contract.json \
  --output benchmarks/results \
  --concordance benchmark_smoke \
  --matrix-version vsmoke \
  --no-contamination \
  --echo-scorer
```

The smoke test uses a deterministic local echo system and scorer. It does not call any network API.
