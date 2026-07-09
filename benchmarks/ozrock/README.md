# OzRock Benchmark Bundle

First real Hexapla Stage 4 benchmark bundle for a low-stakes Australian music knowledge use case.

Purpose:

- Validate the benchmark harness on source-linked, manually curated items.
- Test Australian music context where generic models may over-index on US/UK music history.
- Keep scope small enough for cheap smoke runs before heavier Concordances.

Files:

- `eval_set.jsonl` — source-linked OzRock/APRA-style eval items.
- `rubric.md` — verifier scoring rules and JSON output contract.
- `sut_contract.example.json` — no-network echo candidate contract for smoke tests.
- `gate_template.md` — Stage 5 decision-record template.

This bundle is a harness validation set, not a public benchmark claim.
