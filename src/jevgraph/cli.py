from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from .benchmark import (
    benchmark_plan,
    merge_benchmark_runs,
    run_chat_benchmark,
    run_jev_benchmark,
    run_lexical_benchmark,
)
from .builder import GraphBuilder
from .export import export_csv, export_neo4j
from .extract import load_entities
from .fewrel import fetch_fewrel, sample_fewrel
from .models import Document
from .ontology import Ontology
from .providers import GatewayChatClient, GatewayJevClient, JevProvider, KeywordProvider


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="jevgraph",
        description="Build evidence-backed candidate knowledge graphs with typed decisions.",
    )
    root.add_argument("--version", action="version", version="jevgraph 0.2.0")
    commands = root.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="Build a candidate graph from one text document.")
    build.add_argument("input", type=Path)
    build.add_argument("--ontology", type=Path, required=True)
    build.add_argument("--entities", type=Path, required=True)
    build.add_argument("--provider", choices=["keyword", "jev"], default="keyword")
    build.add_argument("--out", type=Path, required=True)
    build.add_argument("--probability-threshold", type=float, default=0.85)
    build.add_argument("--confidence-threshold", type=float, default=0.80)
    build.add_argument("--max-neighbors", type=int, default=20)
    _live_arguments(build, include_batch_size=True)

    fetch = commands.add_parser("fetch-fewrel", help="Fetch pinned FewRel inputs.")
    fetch.add_argument("--data-dir", type=Path, default=Path("data/fewrel"))

    benchmark = commands.add_parser("benchmark", help="Plan or run the FewRel closed-set track.")
    benchmark.add_argument("--data-dir", type=Path, default=Path("data/fewrel"))
    benchmark.add_argument(
        "--provider",
        choices=["plan", "lexical", "jev", "gpt-5.6-luna", "deepseek-v4.1-flash"],
        default="plan",
    )
    benchmark.add_argument("--relations", type=int, default=8)
    benchmark.add_argument("--examples-per-relation", type=int, default=4)
    benchmark.add_argument("--seed", type=int, default=7)
    benchmark.add_argument("--batch-size", type=int, default=8)
    benchmark.add_argument("--case-offset", type=int, default=0)
    benchmark.add_argument("--case-limit", type=int)
    benchmark.add_argument("--out", type=Path)
    _live_arguments(benchmark, include_batch_size=False)

    export = commands.add_parser("export", help="Export proposed edges from a graph run.")
    export.add_argument("run", type=Path)
    export.add_argument("--format", choices=["csv", "neo4j"], required=True)
    export.add_argument("--out", type=Path, required=True)

    merge = commands.add_parser(
        "merge-benchmarks", help="Merge non-overlapping benchmark shards and failed receipts."
    )
    merge.add_argument("runs", nargs="+", type=Path)
    merge.add_argument("--expected-cases", type=int, required=True)
    merge.add_argument("--out", type=Path, required=True)
    return root


def _live_arguments(command: argparse.ArgumentParser, *, include_batch_size: bool) -> None:
    command.add_argument("--approved-budget-usd", type=float)
    command.add_argument("--call-ceiling", type=int, default=100)
    if include_batch_size:
        command.add_argument("--batch-size", type=int, default=8)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "fetch-fewrel":
            paths = fetch_fewrel(args.data_dir)
            _print({"downloaded": [str(path) for path in paths]})
            return 0
        if args.command == "build":
            return _build(args)
        if args.command == "benchmark":
            return _benchmark(args)
        if args.command == "export":
            return _export(args)
        if args.command == "merge-benchmarks":
            result = merge_benchmark_runs(args.runs, expected_cases=args.expected_cases)
            payload = result.to_dict()
            _write_json(args.out, payload)
            _print(payload["summary"])
            return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 2


def _build(args: argparse.Namespace) -> int:
    document = Document(id=args.input.stem, text=args.input.read_text(encoding="utf-8"))
    ontology = Ontology.load(args.ontology)
    entities = load_entities(args.entities)
    if args.provider == "jev":
        provider = JevProvider(_client(args), batch_size=args.batch_size)
    else:
        provider = KeywordProvider()
    result = GraphBuilder(
        ontology=ontology,
        provider=provider,
        probability_threshold=args.probability_threshold,
        confidence_threshold=args.confidence_threshold,
        max_neighbors=args.max_neighbors,
    ).build(document, entities)
    _write_json(args.out, result.to_dict())
    counts: dict[str, int] = {"proposed": 0, "review": 0, "rejected": 0}
    for edge in result.edges:
        counts[edge.status] += 1
    _print(
        {
            "out": str(args.out),
            "mentions": len(result.mentions),
            "candidates": len(result.candidates),
            "edges": counts,
            "requests": len(result.receipts),
            "cost_usd": sum(r.cost_usd or 0 for r in result.receipts),
        }
    )
    return 0


def _benchmark(args: argparse.Namespace) -> int:
    sample = sample_fewrel(
        args.data_dir,
        relation_count=args.relations,
        examples_per_relation=args.examples_per_relation,
        seed=args.seed,
    )
    if args.case_offset < 0:
        raise ValueError("--case-offset cannot be negative.")
    if args.case_limit is not None and args.case_limit < 1:
        raise ValueError("--case-limit must be positive.")
    end = None if args.case_limit is None else args.case_offset + args.case_limit
    sample = type(sample)(
        cases=sample.cases[args.case_offset : end],
        ontology=sample.ontology,
        relation_ids=sample.relation_ids,
        seed=sample.seed,
        source_revision=sample.source_revision,
    )
    if not sample.cases:
        raise ValueError("The requested FewRel case slice is empty.")
    if args.provider == "plan":
        _print(benchmark_plan(sample, batch_size=args.batch_size))
        return 0
    if args.provider == "lexical":
        result = run_lexical_benchmark(sample)
    elif args.provider == "jev":
        if args.out is None:
            raise ValueError("--out is required for a live benchmark.")
        result = run_jev_benchmark(
            sample,
            client=_client(args),
            batch_size=args.batch_size,
            progress_path=args.out,
        )
    else:
        if args.out is None:
            raise ValueError("--out is required for a live benchmark.")
        result = run_chat_benchmark(
            sample,
            client=_chat_client(args, args.provider),
            batch_size=args.batch_size,
            progress_path=args.out,
        )
    payload = result.to_dict()
    if args.out is not None:
        _write_json(args.out, payload)
    _print(payload["summary"])
    return 0


def _export(args: argparse.Namespace) -> int:
    run = json.loads(args.run.read_text(encoding="utf-8"))
    if args.format == "csv":
        paths = export_csv(run, args.out)
        _print({"files": [str(path) for path in paths]})
    else:
        path = export_neo4j(run, args.out)
        _print({"file": str(path)})
    return 0


def _client(args: argparse.Namespace) -> GatewayJevClient:
    if args.approved_budget_usd is None:
        raise ValueError("Live Jev runs require --approved-budget-usd.")
    api_key = os.environ.get("AI_GATEWAY_API_KEY")
    if not api_key:
        raise ValueError("AI_GATEWAY_API_KEY is not set.")
    return GatewayJevClient(
        api_key=api_key,
        approved_budget_usd=args.approved_budget_usd,
        call_ceiling=args.call_ceiling,
    )


def _chat_client(args: argparse.Namespace, model: str) -> GatewayChatClient:
    if args.approved_budget_usd is None:
        raise ValueError("Live chat-model runs require --approved-budget-usd.")
    api_key = os.environ.get("AI_GATEWAY_API_KEY")
    if not api_key:
        raise ValueError("AI_GATEWAY_API_KEY is not set.")
    return GatewayChatClient(
        api_key=api_key,
        model=model,
        approved_budget_usd=args.approved_budget_usd,
        call_ceiling=args.call_ceiling,
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def _print(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
