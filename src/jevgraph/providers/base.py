from __future__ import annotations

from typing import Protocol

from ..models import CandidateEdge, Document, EvaluationResult
from ..ontology import Ontology


class RelationProvider(Protocol):
    name: str
    model: str

    def evaluate(
        self,
        document: Document,
        candidates: list[CandidateEdge],
        ontology: Ontology,
    ) -> EvaluationResult: ...
