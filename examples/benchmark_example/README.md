# Benchmark Example

No-network smoke test for the Hexapla Benchmark Harness.

```bash
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

This writes:
- `benchmarks/results/evaluation_matrix_vsmoke.json`
- `benchmarks/results/evaluation_matrix_vsmoke.csv`
