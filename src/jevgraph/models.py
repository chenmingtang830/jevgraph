from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

EdgeStatus = Literal["proposed", "review", "rejected"]


@dataclass(frozen=True)
class Document:
    id: str
    text: str


@dataclass(frozen=True)
class Entity:
    id: str
    label: str
    type: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Mention:
    entity_id: str
    entity_label: str
    entity_type: str
    text: str
    start: int
    end: int
    sentence_index: int


@dataclass(frozen=True)
class CandidateEdge:
    id: str
    document_id: str
    source_id: str
    source_label: str
    source_type: str
    target_id: str
    target_label: str
    target_type: str
    evidence_text: str
    evidence_start: int
    evidence_end: int
    allowed_relations: tuple[str, ...]


@dataclass(frozen=True)
class Decision:
    candidate_id: str
    selected: str
    selected_probability: float
    probabilities: dict[str, float]
    confidence: float | None
    provider: str
    model: str
    request_id: str


@dataclass(frozen=True)
class RequestReceipt:
    request_id: str
    provider: str
    requested_model: str
    resolved_model: str | None
    request_sha256: str
    question_count: int
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int
    cost_usd: float | None
    cost_basis: str
    status: Literal["success", "failed"]
    error: str | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class EdgeRecord:
    candidate: CandidateEdge
    decision: Decision
    status: EdgeStatus
    reason: str


@dataclass
class EvaluationResult:
    decisions: list[Decision] = field(default_factory=list)
    receipts: list[RequestReceipt] = field(default_factory=list)


@dataclass
class BuildResult:
    schema_version: int
    created_at: str
    document: Document
    ontology_name: str
    ontology_version: int
    provider: str
    model: str
    config: dict[str, Any]
    entities: list[Entity]
    mentions: list[Mention]
    candidates: list[CandidateEdge]
    edges: list[EdgeRecord]
    receipts: list[RequestReceipt]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
