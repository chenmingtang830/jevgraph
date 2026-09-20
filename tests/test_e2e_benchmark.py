import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from jevgraph.e2e_benchmark import run_e2e_benchmark
from jevgraph.providers.gateway import GatewayJevClient
from jevgraph.providers.keyword import KeywordProvider

ROOT = Path(__file__).parents[1]


class _CostedKeywordProvider:
    name = "test"
    model = GatewayJevClient.model

    def evaluate(self, document, candidates, ontology):
        result = KeywordProvider().evaluate(document, candidates, ontology)
        result.receipts = [
            replace(
                result.receipts[0],
                provider=self.name,
                requested_model=self.model,
                resolved_model=self.model,
                input_tokens=1_000,
                cost_usd=0.015,
                cost_basis="provider",
            )
        ]
        return result


def test_configured_e2e_smoke_benchmark_scores_full_graph() -> None:
    result = run_e2e_benchmark(
        ROOT / "benchmarks/company-events-v1.json",
        provider=KeywordProvider(),
    )

    assert result["benchmark"]["scope"] == "configured_e2e_from_canonical_text"
    assert result["benchmark"]["ontology"] == "company-events"
    assert result["metrics"]["candidate_recall"] == 1.0
    assert result["metrics"]["edge_precision"] == 1.0
    assert result["metrics"]["edge_recall"] == 1.0
    assert result["metrics"]["edge_f1"] == 1.0
    assert result["metrics"]["character_span_integrity"] == 1.0
    assert result["metrics"]["page_mapping_applicable"] is False
    assert result["metrics"]["page_mapping_coverage"] is None
    assert result["metrics"]["known_cost_usd"] == 0.0
    assert result["metrics"]["known_cost_per_candidate_usd"] == 0.0
    assert result["metrics"]["known_cost_per_proposed_edge_usd"] == 0.0
    assert result["metrics"]["known_cost_per_correct_edge_usd"] == 0.0
    assert result["metrics"]["provider_reported_cost_usd"] == 0
    assert result["metrics"]["illustrative_jev_list_price_equivalent_usd"] is None


def test_configured_e2e_manifest_rejects_fixture_drift(tmp_path: Path) -> None:
    source = ROOT / "benchmarks/company-events-v1.json"
    manifest = json.loads(source.read_text(encoding="utf-8"))
    fixture_root = tmp_path / "fixture"
    (fixture_root / "benchmarks").mkdir(parents=True)
    shutil.copytree(ROOT / "examples", fixture_root / "examples")
    manifest["files"]["input"]["sha256"] = "0" * 64
    target = fixture_root / "benchmarks" / "changed.json"
    target.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="Pinned digest mismatch"):
        run_e2e_benchmark(target, provider=KeywordProvider())


def test_configured_e2e_preserves_receipt_and_illustrative_cost_boundaries() -> None:
    result = run_e2e_benchmark(
        ROOT / "benchmarks/company-events-v1.json",
        provider=_CostedKeywordProvider(),
    )
    metrics = result["metrics"]

    assert metrics["provider_reported_cost_usd"] == 0.015
    assert metrics["list_price_estimated_cost_usd"] == 0
    assert metrics["known_cost_per_candidate_usd"] == pytest.approx(0.001)
    assert metrics["known_cost_per_correct_edge_usd"] == pytest.approx(0.00375)
    assert metrics["illustrative_jev_list_price_equivalent_usd"] == pytest.approx(
        0.000042
    )
