import json
from pathlib import Path

from jevgraph.benchmark import benchmark_plan, merge_benchmark_runs, run_lexical_benchmark
from jevgraph.fewrel import sample_fewrel


def _dataset(path: Path) -> None:
    data = {
        "P1": [
            {"tokens": ["Ada", "created", "Engine"], "h": ["Ada"], "t": ["Engine"]},
            {"tokens": ["Lin", "made", "Tool"], "h": ["Lin"], "t": ["Tool"]},
        ],
        "P2": [
            {"tokens": ["Acme", "bought", "Beta"], "h": ["Acme"], "t": ["Beta"]},
            {"tokens": ["One", "acquired", "Two"], "h": ["One"], "t": ["Two"]},
        ],
        "P3": [
            {"tokens": ["A", "joined", "B"], "h": ["A"], "t": ["B"]},
            {"tokens": ["C", "met", "D"], "h": ["C"], "t": ["D"]},
        ],
    }
    names = {
        "P1": ["creator", "person who created a work"],
        "P2": ["acquired", "organization acquired another organization"],
        "P3": ["member", "person belongs to an organization"],
    }
    (path / "train_wiki.json").write_text(json.dumps(data), encoding="utf-8")
    (path / "pid2name.json").write_text(json.dumps(names), encoding="utf-8")


def test_fewrel_sampling_and_plan_are_deterministic(tmp_path: Path) -> None:
    _dataset(tmp_path)
    first = sample_fewrel(tmp_path, relation_count=2, examples_per_relation=2, seed=9)
    second = sample_fewrel(tmp_path, relation_count=2, examples_per_relation=2, seed=9)

    assert first == second
    plan = benchmark_plan(first, batch_size=3)
    assert plan["cases"] == 4
    assert plan["requests"] == 2
    assert plan["illustrative_input_cost_usd"] > 0


def test_lexical_baseline_reports_complete_coverage(tmp_path: Path) -> None:
    _dataset(tmp_path)
    sample = sample_fewrel(tmp_path, relation_count=2, examples_per_relation=1, seed=2)
    result = run_lexical_benchmark(sample)
    summary = result.summary()

    assert summary["coverage"] == 1.0
    assert summary["completed_cases"] == 2
    assert summary["total_cost_usd"] == 0.0


def test_merge_preserves_failed_receipts_and_deduplicates_predictions(tmp_path: Path) -> None:
    identity = {
        "provider": "gateway",
        "model": "jev",
        "source_revision": "abc",
        "seed": 7,
        "relation_ids": ["P1", "P2"],
    }
    prediction = {
        "case_id": "P1:0",
        "gold_relation": "P1",
        "predicted_relation": "P1",
        "selected_probability": 0.9,
        "confidence": 0.8,
        "request_id": "r1",
        "status": "success",
    }
    receipt = {
        "request_id": "r1",
        "provider": "gateway",
        "requested_model": "jev",
        "resolved_model": None,
        "request_sha256": "hash",
        "question_count": 1,
        "input_tokens": 10,
        "output_tokens": 2,
        "latency_ms": 20,
        "cost_usd": 0.0,
        "cost_basis": "provider",
        "status": "success",
        "error": None,
        "warnings": [],
    }
    failed = {
        **receipt,
        "request_id": "r2",
        "status": "failed",
        "cost_usd": None,
        "cost_basis": "unknown",
        "error": "HTTP 503",
    }
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(
        json.dumps({**identity, "predictions": [prediction], "receipts": [receipt, failed]}),
        encoding="utf-8",
    )
    second.write_text(
        json.dumps({**identity, "predictions": [prediction], "receipts": [receipt]}),
        encoding="utf-8",
    )

    merged = merge_benchmark_runs([first, second], expected_cases=2)
    assert len(merged.predictions) == 1
    assert len(merged.receipts) == 2
    assert merged.summary()["coverage"] == 0.5
    assert merged.summary()["unknown_cost_requests"] == 1
