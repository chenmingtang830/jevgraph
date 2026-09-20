from __future__ import annotations

from datetime import UTC, datetime

from .extract import find_mentions, generate_candidates
from .models import BuildResult, Document, EdgeRecord, Entity
from .ontology import Ontology
from .providers.base import RelationProvider


class GraphBuilder:
    def __init__(
        self,
        *,
        ontology: Ontology,
        provider: RelationProvider,
        probability_threshold: float = 0.85,
        confidence_threshold: float = 0.80,
        max_neighbors: int = 20,
    ) -> None:
        for name, value in {
            "probability_threshold": probability_threshold,
            "confidence_threshold": confidence_threshold,
        }.items():
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between zero and one.")
        self.ontology = ontology
        self.provider = provider
        self.probability_threshold = probability_threshold
        self.confidence_threshold = confidence_threshold
        self.max_neighbors = max_neighbors

    def build(self, document: Document, entities: list[Entity]) -> BuildResult:
        mentions = find_mentions(document, entities)
        candidates = generate_candidates(
            document,
            mentions,
            self.ontology,
            max_neighbors=self.max_neighbors,
        )
        evaluation = self.provider.evaluate(document, candidates, self.ontology)
        decisions = {decision.candidate_id: decision for decision in evaluation.decisions}
        if set(decisions) != {candidate.id for candidate in candidates}:
            raise ValueError("Provider did not return exactly one decision per candidate.")

        edges: list[EdgeRecord] = []
        symmetric_seen: set[tuple[str, str, str, int, int]] = set()
        for candidate in candidates:
            decision = decisions[candidate.id]
            selected = decision.selected
            if selected == "none":
                status = "rejected"
                reason = "provider_selected_none"
            elif selected == "insufficient_evidence":
                status = "review"
                reason = "provider_requested_more_context"
            elif selected not in candidate.allowed_relations:
                status = "review"
                reason = "relation_failed_schema_check"
            elif decision.confidence is None:
                status = "review"
                reason = "missing_confidence"
            elif decision.selected_probability < self.probability_threshold:
                status = "review"
                reason = "below_probability_threshold"
            elif decision.confidence < self.confidence_threshold:
                status = "review"
                reason = "below_confidence_threshold"
            else:
                status = "proposed"
                reason = "passed_configured_gates"

            if status == "proposed" and self.ontology.relations[selected].symmetric:
                key = (
                    selected,
                    *sorted([candidate.source_id, candidate.target_id]),
                    candidate.evidence_start,
                    candidate.evidence_end,
                )
                if key in symmetric_seen:
                    status = "rejected"
                    reason = "duplicate_symmetric_edge"
                else:
                    symmetric_seen.add(key)
            edges.append(EdgeRecord(candidate, decision, status, reason))

        return BuildResult(
            schema_version=1,
            created_at=datetime.now(UTC).isoformat(),
            document=document,
            ontology_name=self.ontology.name,
            ontology_version=self.ontology.version,
            provider=self.provider.name,
            model=self.provider.model,
            config={
                "probability_threshold": self.probability_threshold,
                "confidence_threshold": self.confidence_threshold,
                "max_neighbors": self.max_neighbors,
            },
            entities=entities,
            mentions=mentions,
            candidates=candidates,
            edges=edges,
            receipts=evaluation.receipts,
        )
