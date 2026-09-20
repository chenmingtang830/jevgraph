"""JevGraph: evidence-backed knowledge graph construction."""

from .builder import GraphBuilder
from .ingest import load_document
from .models import (
    BuildResult,
    CandidateEdge,
    Decision,
    Document,
    Entity,
    EvidenceSourceSpan,
    Mention,
    PageSpan,
)
from .ontology import Ontology

__all__ = [
    "BuildResult",
    "CandidateEdge",
    "Decision",
    "Document",
    "Entity",
    "EvidenceSourceSpan",
    "GraphBuilder",
    "Mention",
    "Ontology",
    "PageSpan",
    "load_document",
]

__version__ = "0.5.0"
