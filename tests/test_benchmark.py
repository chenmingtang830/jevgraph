import json
from pathlib import Path

import pytest

from jevgraph.benchmark import (
    benchmark_plan,
    merge_benchmark_runs,
    run_jev_benchmark,
    run_lexical_benchmark,
)
from jevgraph.fewrel import sample_fewrel
from jevgraph.models import RequestReceipt
from jevgraph.providers.gateway import GatewayAnswer, GatewayJevClient, ProviderFailure


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
    plan = benchmark_plan(
        first,
        batch_size=3,
        choice_set="relations-only",
        chat_max_output_tokens=4096,
        chat_reasoning_effort="none",
    )
    assert plan["cases"] == 4
    assert plan["requests"] == 2
    assert plan["illustrative_input_cost_usd"] > 0
    assert plan["choice_set"] == "relations-only"
    assert plan["chat_max_output_tokens"] == 4096
    assert plan["chat_reasoning_effort"] == "none"


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


def test_direct_relation_only_request_hides_gold_bearing_case_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _dataset(tmp_path)
    sample = sample_fewrel(tmp_path, relation_count=2, examples_per_relation=1, seed=9)
    client = GatewayJevClient(
        api_key="secret-key-value", approved_budget_usd=0.05, call_ceiling=2
    )
    seen_ids: list[str] = []

    def evaluate(*, state: dict, questions: dict) -> tuple[dict, RequestReceipt]:
        provider_ids = set(state["cases"])
        assert provider_ids == set(questions)
        assert len(provider_ids) == 1
        provider_id = next(iter(provider_ids))
        seen_ids.append(provider_id)
        assert provider_id.startswith("case_")
        assert "P" not in provider_id
        assert "none" not in questions[provider_id]["criteria"]
        assert "insufficient_evidence" not in questions[provider_id]["criteria"]
        assert all(case.id not in json.dumps(state) for case in sample.cases)
        return (
            {
                provider_id: GatewayAnswer(
                    selected="P1", probabilities={"P1": 1.0}, confidence=1.0
                )
            },
            RequestReceipt(
                request_id=f"request-{provider_id}",
                provider="test",
                requested_model=client.model,
                resolved_model=None,
                request_sha256="hash",
                question_count=1,
                input_tokens=10,
                output_tokens=1,
                latency_ms=1,
                cost_usd=0.0,
                cost_basis="provider",
                status="success",
            ),
        )

    monkeypatch.setattr(client, "evaluate", evaluate)
    result = run_jev_benchmark(
        sample, client=client, batch_size=1, choice_set="relations-only"
    )

    assert seen_ids == ["case_00000", "case_00001"]
    assert result.config["task_mode"] == "direct_closed_set_relation_only"
    assert result.config["provider_case_id_contains_gold_relation"] is False
    assert result.summary()["illustrative_jev_list_price_equivalent_usd"] == pytest.approx(
        0.00000084
    )


def test_direct_runner_continues_after_known_cost_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _dataset(tmp_path)
    sample = sample_fewrel(tmp_path, relation_count=2, examples_per_relation=1, seed=9)
    client = GatewayJevClient(
        api_key="secret-key-value", approved_budget_usd=0.05, call_ceiling=2
    )
    calls = 0

    def evaluate(*, state: dict, questions: dict) -> tuple[dict, RequestReceipt]:
        nonlocal calls
        calls += 1
        provider_id = next(iter(questions))
        if calls == 1:
            raise ProviderFailure(
                "known failure",
                RequestReceipt(
                    request_id="failed",
                    provider="test",
                    requested_model=client.model,
                    resolved_model=None,
                    request_sha256="failed-hash",
                    question_count=1,
                    input_tokens=1,
                    output_tokens=1,
                    latency_ms=1,
                    cost_usd=0.01,
                    cost_basis="provider",
                    status="failed",
                    error="incomplete_choice",
                ),
            )
        return (
            {
                provider_id: GatewayAnswer(
                    selected="P1", probabilities={"P1": 1.0}, confidence=1.0
                )
            },
            RequestReceipt(
                request_id="success",
                provider="test",
                requested_model=client.model,
                resolved_model=None,
                request_sha256="success-hash",
                question_count=1,
                input_tokens=1,
                output_tokens=1,
                latency_ms=1,
                cost_usd=0.01,
                cost_basis="provider",
                status="success",
            ),
        )

    monkeypatch.setattr(client, "evaluate", evaluate)
    result = run_jev_benchmark(
        sample,
        client=client,
        batch_size=1,
        choice_set="relations-only",
        continue_after_known_failure=True,
    )

    assert calls == 2
    assert [receipt.status for receipt in result.receipts] == ["failed", "success"]
    assert result.summary()["coverage"] == 0.5


def test_direct_runner_stops_after_unknown_cost_failure_without_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _dataset(tmp_path)
    sample = sample_fewrel(tmp_path, relation_count=2, examples_per_relation=1, seed=9)
    client = GatewayJevClient(
        api_key="secret-key-value", approved_budget_usd=0.05, call_ceiling=2
    )
    calls = 0

    def evaluate(*, state: dict, questions: dict) -> tuple[dict, RequestReceipt]:
        nonlocal calls
        calls += 1
        raise ProviderFailure(
            "billing status unknown",
            RequestReceipt(
                request_id="unknown-cost-failure",
                provider="test",
                requested_model=client.model,
                resolved_model=None,
                request_sha256="failed-hash",
                question_count=1,
                input_tokens=None,
                output_tokens=None,
                latency_ms=1,
                cost_usd=None,
                cost_basis="unknown",
                status="failed",
                error="HTTP 503",
            ),
        )

    monkeypatch.setattr(client, "evaluate", evaluate)

    with pytest.raises(ProviderFailure, match="billing status unknown"):
        run_jev_benchmark(
            sample,
            client=client,
            batch_size=1,
            choice_set="relations-only",
            continue_after_known_failure=True,
        )

    assert calls == 1
