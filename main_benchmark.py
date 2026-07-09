#!/usr/bin/env python3
"""CLI for the Hexapla Benchmark Harness."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hexapla.backend import Backend
from hexapla.benchmark_loop import BenchmarkConfig, load_eval_set, run_benchmark
from hexapla.config import Config
from hexapla.inspect_adapter import build_inspect_task_source, export_inspect_jsonl, to_inspect_samples
from hexapla.scoring import ScoreResult
from hexapla.sut_contract import load_sut_contract


def _load_contract(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "export-inspect":
        parser = argparse.ArgumentParser(description="Export Hexapla eval items for Inspect AI.")
        parser.add_argument("command", choices=["export-inspect"])
        parser.add_argument("--eval-set", required=True, type=Path, help="Canonical Hexapla eval set JSONL")
        parser.add_argument("--rubric", required=True, type=Path, help="Scoring rubric markdown")
        parser.add_argument("--task-name", required=True, help="Inspect task function name, e.g. ozrock")
        parser.add_argument("--output-dir", required=True, type=Path, help="Directory for Inspect artefacts")
        return parser.parse_args(argv)

    parser = argparse.ArgumentParser(description="Run a Hexapla Stage 4 benchmark.")
    parser.set_defaults(command="run")
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
    return parser.parse_args(argv)


def export_inspect(args: argparse.Namespace) -> tuple[Path, Path]:
    """Export canonical Hexapla eval items into Inspect-compatible artefacts."""

    items = load_eval_set(args.eval_set, strict=True)
    samples = to_inspect_samples(items)
    samples_path = args.output_dir / "inspect_samples.jsonl"
    task_path = args.output_dir / "inspect_task.py"
    export_inspect_jsonl(samples, samples_path)
    task_path.write_text(
        build_inspect_task_source(
            task_name=args.task_name,
            dataset_path=str(samples_path),
            rubric_path=str(args.rubric),
        ),
        encoding="utf-8",
    )
    return samples_path, task_path


def main() -> int:
    args = parse_args()
    if args.command == "export-inspect":
        samples_path, task_path = export_inspect(args)
        print(f"Wrote {samples_path}")
        print(f"Wrote {task_path}")
        return 0

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
