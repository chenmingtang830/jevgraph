import json
from pathlib import Path

import pytest

from jevgraph.benchmark import BenchmarkPrediction
from jevgraph.episodic import (
    EpisodicBenchmarkResult,
    episodic_plan,
    merge_episodic_runs,
    run_episodic_benchmark,
)
from jevgraph.fewrel import sample_fewrel_episodes
from jevgraph.models import RequestReceipt
from jevgraph.providers.chat import GatewayChatClient
from jevgraph.providers.gateway import ProviderFailure


def _validation_dataset(path: Path) -> None:
    data = {}
    for relation_index in range(10):
        relation_id = f"P{relation_index}"
        data[relation_id] = [
            {
                "tokens": [f"Head-{relation_index}-{example}", "links", f"Tail-{example}"],
                "h": [f"Head-{relation_index}-{example}", "QH", [[0]]],
                "t": [f"Tail-{example}", "QT", [[2]]],
            }
            for example in range(8)
        ]
    (path / "val_wiki.json").write_text(json.dumps(data), encoding="utf-8")


def test_official_episodes_are_deterministic_and_disjoint(tmp_path: Path) -> None:
    _validation_dataset(tmp_path)
    first = sample_fewrel_episodes(
        tmp_path,
        ways=5,
        shots=1,
        queries_per_relation=2,
        episode_count=3,
        seed=17,
    )
    second = sample_fewrel_episodes(
        tmp_path,
        ways=5,
        shots=1,
        queries_per_relation=2,
        episode_count=3,
        seed=17,
    )

    assert first == second
    assert len(first.episodes) == 3
    for episode in first.episodes:
        assert len(episode.relation_ids) == 5
        assert len(episode.support) == 5
        assert len(episode.queries) == 10
        assert {item.id for item in episode.support}.isdisjoint(
            item.id for item in episode.queries
        )
        grouped = tuple(
            relation_id
            for relation_id in episode.relation_ids
            for _ in range(first.queries_per_relation)
        )
        assert tuple(item.gold_relation for item in episode.queries) != grouped


def test_official_plan_has_one_request_per_episode(tmp_path: Path) -> None:
    _validation_dataset(tmp_path)
    sample = sample_fewrel_episodes(
        tmp_path,
        ways=5,
        shots=5,
        queries_per_relation=1,
        episode_count=2,
        seed=3,
    )

    plan = episodic_plan(sample, model="gpt-5.6-luna")

    assert plan["requests"] == 2
    assert plan["cases"] == 10
    assert plan["ways"] == 5
    assert plan["shots"] == 5
    assert plan["conservative_estimated_cost_usd"] > 0


def test_runner_hides_property_ids_behind_episode_labels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _validation_dataset(tmp_path)
    sample = sample_fewrel_episodes(
        tmp_path,
        ways=5,
        shots=1,
        queries_per_relation=1,
        episode_count=1,
        seed=11,
    )
    client = GatewayChatClient(
        api_key="secret-key-value",
        model="gpt-5.6-luna",
        approved_budget_usd=0.05,
        call_ceiling=1,
    )

    def classify_episode(**kwargs: object) -> tuple[dict[str, str], RequestReceipt]:
        payload = kwargs["episode"]
        assert isinstance(payload, dict)
        assert "allowed_relation_ids" not in payload
        assert payload["allowed_labels"] == [f"relation_{index}" for index in range(5)]
        assert all("relation_id" not in item for item in payload["support"])
        assert all(item["query_id"].startswith("query_") for item in payload["queries"])
        assert all("P" not in item["query_id"] for item in payload["queries"])
        assert all(item["source_token_positions"] == [0] for item in payload["support"])
        assert all(item["target_token_positions"] == [2] for item in payload["queries"])
        query_ids = kwargs["query_ids"]
        assert isinstance(query_ids, tuple)
        return (
            {query_id: "relation_0" for query_id in query_ids},
            RequestReceipt(
                request_id="local-test",
                provider="test",
                requested_model=client.model,
                resolved_model=None,
                request_sha256="test",
                question_count=len(query_ids),
                input_tokens=1,
                output_tokens=1,
                latency_ms=1,
                cost_usd=0.0,
                cost_basis="test",
                status="success",
            ),
        )

    monkeypatch.setattr(client, "classify_episode", classify_episode)
    result = run_episodic_benchmark(sample, client=client)

    assert {item.predicted_relation for item in result.predictions} == {
        sample.episodes[0].relation_ids[0]
    }


def test_merge_episodic_runs_retains_failed_receipts(tmp_path: Path) -> None:
    base = dict(
        schema_version=1,
        created_at="2026-09-20T00:00:00+00:00",
        track="fewrel-1.0-official-compatible-validation",
        provider="gateway",
        model="model",
        source_revision="abc",
        split="val_wiki",
        seed=17,
        ways=5,
        shots=1,
        queries_per_relation=1,
        query_mode="batched_transductive",
        planned_episodes=1,
        planned_cases=5,
    )
    prediction = BenchmarkPrediction(
        case_id="episode-00000:P1:1",
        gold_relation="P1",
        predicted_relation="P1",
        selected_probability=None,
        confidence=None,
        request_id="ok",
        status="success",
    )
    success = RequestReceipt(
        request_id="ok",
        provider="gateway",
        requested_model="model",
        resolved_model=None,
        request_sha256="hash-ok",
        question_count=1,
        input_tokens=1,
        output_tokens=1,
        latency_ms=1,
        cost_usd=0.0,
        cost_basis="provider",
        status="success",
    )
    failed = RequestReceipt(
        request_id="failed",
        provider="gateway",
        requested_model="model",
        resolved_model=None,
        request_sha256="hash-failed",
        question_count=5,
        input_tokens=None,
        output_tokens=None,
        latency_ms=10,
        cost_usd=None,
        cost_basis="unknown",
        status="failed",
        error="HTTP 503",
    )
    first = EpisodicBenchmarkResult(
        **base, predictions=[prediction], receipts=[success, failed]
    )
    second = EpisodicBenchmarkResult(**base, predictions=[], receipts=[])
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    first_path.write_text(json.dumps(first.to_dict()), encoding="utf-8")
    second_path.write_text(json.dumps(second.to_dict()), encoding="utf-8")

    merged = merge_episodic_runs([first_path, second_path], expected_episodes=2)

    assert merged.planned_cases == 10
    assert len(merged.predictions) == 1
    assert len(merged.receipts) == 2
    assert merged.summary()["unknown_cost_requests"] == 1


def test_jev_summary_separates_free_billing_from_list_price_equivalent() -> None:
    result = EpisodicBenchmarkResult(
        schema_version=1,
        created_at="2026-09-20T00:00:00+00:00",
        track="fewrel-1.0-official-compatible-validation",
        provider="vercel-ai-gateway",
        model="typesafe-ai/jev",
        source_revision="abc",
        split="val_wiki",
        seed=17,
        ways=5,
        shots=1,
        queries_per_relation=1,
        query_mode="batched_transductive",
        planned_episodes=1,
        planned_cases=5,
        receipts=[
            RequestReceipt(
                request_id="free",
                provider="vercel-ai-gateway",
                requested_model="typesafe-ai/jev",
                resolved_model=None,
                request_sha256="hash",
                question_count=5,
                input_tokens=1_000_000,
                output_tokens=100,
                latency_ms=1,
                cost_usd=0.0,
                cost_basis="provider",
                status="success",
            )
        ],
    )

    summary = result.summary()

    assert summary["provider_reported_cost_usd"] == 0.0
    assert summary["provider_reported_cost_requests"] == 1
    assert summary["illustrative_jev_list_price_equivalent_usd"] == 0.042


def test_runner_can_continue_after_a_known_cost_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _validation_dataset(tmp_path)
    sample = sample_fewrel_episodes(
        tmp_path,
        ways=5,
        shots=1,
        queries_per_relation=1,
        episode_count=2,
        seed=11,
    )
    client = GatewayChatClient(
        api_key="secret-key-value",
        model="gpt-5.6-luna",
        approved_budget_usd=0.05,
        call_ceiling=2,
    )
    calls = 0

    def classify_episode(**kwargs: object) -> tuple[dict[str, str], RequestReceipt]:
        nonlocal calls
        calls += 1
        query_ids = kwargs["query_ids"]
        assert isinstance(query_ids, tuple)
        if calls == 1:
            raise ProviderFailure(
                "incomplete",
                RequestReceipt(
                    request_id="failed",
                    provider="gateway",
                    requested_model=client.model,
                    resolved_model=None,
                    request_sha256="failed-hash",
                    question_count=5,
                    input_tokens=10,
                    output_tokens=20,
                    latency_ms=30,
                    cost_usd=0.01,
                    cost_basis="provider",
                    status="failed",
                    error="incomplete_choice",
                ),
            )
        return (
            {query_id: "relation_0" for query_id in query_ids},
            RequestReceipt(
                request_id="success",
                provider="gateway",
                requested_model=client.model,
                resolved_model=None,
                request_sha256="success-hash",
                question_count=5,
                input_tokens=10,
                output_tokens=20,
                latency_ms=30,
                cost_usd=0.01,
                cost_basis="provider",
                status="success",
            ),
        )

    monkeypatch.setattr(client, "classify_episode", classify_episode)

    result = run_episodic_benchmark(
        sample, client=client, continue_after_known_failure=True
    )

    assert calls == 2
    assert len(result.receipts) == 2
    assert result.receipts[0].status == "failed"
    assert len(result.predictions) == 5
    assert result.summary()["coverage"] == 0.5
