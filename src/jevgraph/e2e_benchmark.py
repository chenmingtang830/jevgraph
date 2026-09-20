from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from .builder import GraphBuilder
from .extract import load_entities
from .ingest import load_document
from .models import BuildResult
from .ontology import Ontology
from .providers.base import RelationProvider


def run_e2e_benchmark(
    manifest_path: str | Path,
    *,
    provider: RelationProvider,
    probability_threshold: float = 0.85,
    confidence_threshold: float = 0.80,
    max_neighbors: int = 20,
) -> dict[str, Any]:
    """Run a small, digest-pinned document-to-candidate-graph benchmark."""

    manifest_file = Path(manifest_path).resolve()
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("E2E benchmark manifest must use schema_version 1.")

    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ValueError("E2E benchmark manifest requires a files object.")
    root = manifest_file.parent.parent
    input_path = _pinned_path(root, files, "input")
    ontology_path = _pinned_path(root, files, "ontology")
    entities_path = _pinned_path(root, files, "entities")

    started = perf_counter()
    document = load_document(input_path)
    ontology = Ontology.load(ontology_path)
    entities = load_entities(entities_path)
    build = GraphBuilder(
        ontology=ontology,
        provider=provider,
        probability_threshold=probability_threshold,
        confidence_threshold=confidence_threshold,
        max_neighbors=max_neighbors,
    ).build(document, entities)
    pipeline_latency_ms = round((perf_counter() - started) * 1000, 3)

    gold = _gold_edges(manifest)
    metrics = _score(build, ontology, gold)
    receipts = [asdict(receipt) for receipt in build.receipts]
    known_costs = [receipt.cost_usd for receipt in build.receipts if receipt.cost_usd is not None]
    request_latencies = sorted(receipt.latency_ms for receipt in build.receipts)
    return {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "benchmark": {
            "name": str(manifest.get("name", manifest_file.stem)),
            "manifest": str(manifest_path),
            "manifest_sha256": _sha256(manifest_file),
            "ontology": ontology.name,
            "ontology_version": ontology.version,
            "ontology_sha256": files["ontology"]["sha256"],
            "entity_catalog_sha256": files["entities"]["sha256"],
            "input_sha256": files["input"]["sha256"],
            "gold_edges": len(gold),
            "scope": "configured_e2e_from_canonical_text",
        },
        "provider": provider.name,
        "model": provider.model,
        "config": {
            "probability_threshold": probability_threshold,
            "confidence_threshold": confidence_threshold,
            "max_neighbors": max_neighbors,
        },
        "metrics": {
            **metrics,
            "pipeline_latency_ms": pipeline_latency_ms,
            "request_latency_p50_ms": _percentile(request_latencies, 0.50),
            "request_latency_p95_ms": _percentile(request_latencies, 0.95),
            "known_cost_usd": sum(known_costs),
            "unknown_cost_requests": len(build.receipts) - len(known_costs),
        },
        "receipts": receipts,
    }


def _pinned_path(root: Path, files: dict[str, Any], key: str) -> Path:
    value = files.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"E2E benchmark manifest requires files.{key}.")
    relative = value.get("path")
    expected = value.get("sha256")
    if not isinstance(relative, str) or not isinstance(expected, str):
        raise ValueError(f"files.{key} requires path and sha256 strings.")
    path = (root / relative).resolve()
    if root not in path.parents:
        raise ValueError(f"files.{key}.path must stay inside the repository.")
    if _sha256(path) != expected:
        raise ValueError(f"Pinned digest mismatch for files.{key}: {relative}")
    return path


def _gold_edges(manifest: dict[str, Any]) -> set[tuple[str, str, str]]:
    values = manifest.get("gold_edges")
    if not isinstance(values, list) or not values:
        raise ValueError("E2E benchmark manifest requires non-empty gold_edges.")
    edges: set[tuple[str, str, str]] = set()
    for value in values:
        if not isinstance(value, dict):
            raise ValueError("Each gold edge must be an object.")
        edge = (value.get("source"), value.get("relation"), value.get("target"))
        if not all(isinstance(part, str) and part for part in edge):
            raise ValueError("Gold edges require source, relation, and target strings.")
        edges.add((str(edge[0]), str(edge[1]), str(edge[2])))
    return edges


def _score(
    build: BuildResult,
    ontology: Ontology,
    gold: set[tuple[str, str, str]],
) -> dict[str, Any]:
    normalized_gold = {_normalize(edge, ontology) for edge in gold}
    proposed = {
        _normalize(
            (
                edge.candidate.source_id,
                edge.decision.selected,
                edge.candidate.target_id,
            ),
            ontology,
        )
        for edge in build.edges
        if edge.status == "proposed"
    }
    candidate_edges = {
        _normalize((candidate.source_id, relation, candidate.target_id), ontology)
        for candidate in build.candidates
        for relation in candidate.allowed_relations
    }
    tp = len(normalized_gold & proposed)
    fp = len(proposed - normalized_gold)
    fn = len(normalized_gold - proposed)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else None
    )
    span_valid = sum(
        build.document.text[candidate.evidence_start : candidate.evidence_end]
        == candidate.evidence_text
        for candidate in build.candidates
    )
    page_mapped = sum(bool(candidate.evidence_source_spans) for candidate in build.candidates)
    status_counts = {status: 0 for status in ("proposed", "review", "rejected")}
    for edge in build.edges:
        status_counts[edge.status] += 1
    return {
        "mentions": len(build.mentions),
        "candidates": len(build.candidates),
        "edge_status": status_counts,
        "true_positive_edges": tp,
        "false_positive_edges": fp,
        "false_negative_edges": fn,
        "edge_precision": precision,
        "edge_recall": recall,
        "edge_f1": f1,
        "candidate_recall": len(normalized_gold & candidate_edges) / len(normalized_gold),
        "character_span_integrity": span_valid / len(build.candidates)
        if build.candidates
        else None,
        "page_mapping_coverage": (
            page_mapped / len(build.candidates)
            if build.document.page_spans and build.candidates
            else None
        ),
        "page_mapping_applicable": bool(build.document.page_spans),
    }


def _normalize(
    edge: tuple[str, str, str], ontology: Ontology
) -> tuple[str, str, str]:
    source, relation, target = edge
    if relation not in ontology.relations:
        raise ValueError(f"Edge refers to unknown relation {relation!r}.")
    if ontology.relations[relation].symmetric and target < source:
        source, target = target, source
    return source, relation, target


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _percentile(values: list[int], quantile: float) -> int | None:
    if not values:
        return None
    index = round((len(values) - 1) * quantile)
    return values[index]
