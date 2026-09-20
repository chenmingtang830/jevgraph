import json
import shutil
from pathlib import Path

import pytest

from jevgraph.e2e_benchmark import run_e2e_benchmark
from jevgraph.providers.keyword import KeywordProvider

ROOT = Path(__file__).parents[1]


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
