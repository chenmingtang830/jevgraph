"""JevGraph: evidence-backed knowledge graph construction."""

from .builder import GraphBuilder
from .models import BuildResult, CandidateEdge, Decision, Document, Entity, Mention
from .ontology import Ontology

__all__ = [
    "BuildResult",
    "CandidateEdge",
    "Decision",
    "Document",
    "Entity",
    "GraphBuilder",
    "Mention",
    "Ontology",
]

__version__ = "0.1.1"
