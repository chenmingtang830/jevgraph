from __future__ import annotations

import hashlib
import re
from time import perf_counter

from ..models import (
    CandidateEdge,
    Decision,
    Document,
    EvaluationResult,
    RequestReceipt,
)
from ..ontology import Ontology


class KeywordProvider:
    """A transparent local baseline for the synthetic demo, not an ML model."""

    name = "local"
    model = "keyword-baseline-v1"

    def evaluate(
        self,
        document: Document,
        candidates: list[CandidateEdge],
        ontology: Ontology,
    ) -> EvaluationResult:
        started = perf_counter()
        request_id = "local_" + hashlib.sha256(document.text.encode()).hexdigest()[:16]
        decisions: list[Decision] = []
        for candidate in candidates:
            selected = "none"
            evidence = candidate.evidence_text.lower()
            if not re.search(r"\b(?:not|never|no evidence)\b", evidence):
                source_at = evidence.find(candidate.source_label.lower())
                target_at = evidence.find(candidate.target_label.lower())
                for relation_id in candidate.allowed_relations:
                    relation = ontology.relations[relation_id]
                    for pattern in relation.patterns:
                        pattern_at = evidence.find(pattern.lower())
                        if pattern_at < 0:
                            continue
                        if relation.symmetric or (
                            source_at >= 0 and source_at < pattern_at < target_at
                        ):
                            selected = relation_id
                            break
                    if selected != "none":
                        break
            options = [*candidate.allowed_relations, "none", "insufficient_evidence"]
            probabilities = {option: 0.0 for option in options}
            probabilities[selected] = 1.0
            decisions.append(
                Decision(
                    candidate_id=candidate.id,
                    selected=selected,
                    selected_probability=1.0,
                    probabilities=probabilities,
                    confidence=1.0,
                    provider=self.name,
                    model=self.model,
                    request_id=request_id,
                )
            )
        latency_ms = round((perf_counter() - started) * 1000)
        receipt = RequestReceipt(
            request_id=request_id,
            provider=self.name,
            requested_model=self.model,
            resolved_model=self.model,
            request_sha256=hashlib.sha256(document.text.encode()).hexdigest(),
            question_count=len(candidates),
            input_tokens=None,
            output_tokens=None,
            latency_ms=latency_ms,
            cost_usd=0.0,
            cost_basis="local",
            status="success",
        )
        return EvaluationResult(decisions=decisions, receipts=[receipt])
