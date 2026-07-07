#!/usr/bin/env python3
"""CLI for the Hexapla Benchmark Harness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hexapla.backend import Backend
from hexapla.benchmark_loop import BenchmarkConfig, run_benchmark
from hexapla.config import Config
from hexapla.scoring import ScoreResult
from hexapla.sut_contract import load_sut_contract


def _load_contract(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a Hexapla Stage 4 benchmark.")
    parser.add_argument("--eval-set", required=True, type=Path, help="Concordance eval set JSONL")
    parser.add_argument("--rubric", required=True, type=Path, help="Scoring rubric markdown")
    parser.add_argument("--sut-contract", required=True, type=Path, help="SUT contract JSON")
    parser.add_argument("--output", required=True, type=Path, help="Output directory for matrix artefacts")
    parser.add_argument("--concordance", required=True, help="Concordance name")
    parser.add_argument("--matrix-version", default=None, help="Optional matrix version, e.g. v20260707")
    parser.add_argument("--max-items", type=int, default=None, help="Optional item limit for smoke tests")
    parser.add_argument("--max-cost", type=float, default=None, help="Optional benchmark cost cap in USD")
    parser.add_argument("--verifier-model", default=None, help="Verifier model slug")
    parser.add_argument("--no-contamination", action="store_true", help="Disable perturbation screening")
    parser.add_argument(
        "--echo-scorer",
        action="store_true",
        help="Use deterministic score=1 scorer for no-network CLI smoke tests",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = Config()
    verifier_model = args.verifier_model or config.verifier_model
    contract = _load_contract(args.sut_contract)
    suts = load_sut_contract(contract, config)

    scorer = None
    if args.echo_scorer:
        verifier = None
        scorer = lambda item, response: ScoreResult(1.0, "echo scorer", [])
    else:
        verifier = Backend(model=verifier_model, config=config)

    matrix, (json_path, csv_path) = run_benchmark(
        config=BenchmarkConfig(
            concordance=args.concordance,
            eval_set_path=args.eval_set,
            rubric_path=args.rubric,
            output_dir=args.output,
            matrix_version=args.matrix_version,
            max_items=args.max_items,
            max_cost_usd=args.max_cost,
            contamination=not args.no_contamination,
        ),
        suts=suts,
        verifier=verifier,
        scorer=scorer,
    )

    print(f"Wrote {json_path}")
    print(f"Wrote {csv_path}")
    print(json.dumps(matrix.aggregates(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
