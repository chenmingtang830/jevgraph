from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

from .models import CandidateEdge, Document, Entity, Mention
from .ontology import Ontology


def load_entities(path: str | Path) -> list[Entity]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    values = raw.get("entities") if isinstance(raw, dict) else None
    if not isinstance(values, list):
        raise ValueError("Entity catalog must contain an entities list.")
    entities: list[Entity] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, dict):
            raise ValueError("Each entity must be an object.")
        entity_id = str(value.get("id", "")).strip()
        label = str(value.get("label", "")).strip()
        entity_type = str(value.get("type", "")).strip()
        aliases = value.get("aliases", [label])
        if not entity_id or not label or not entity_type or entity_id in seen:
            raise ValueError("Entities need unique IDs, labels, and types.")
        if not isinstance(aliases, list) or any(not isinstance(alias, str) for alias in aliases):
            raise ValueError(f"Entity {entity_id!r} aliases must be strings.")
        normalized_aliases = tuple(
            dict.fromkeys([label, *(a.strip() for a in aliases if a.strip())])
        )
        entities.append(Entity(entity_id, label, entity_type, normalized_aliases))
        seen.add(entity_id)
    return entities


def sentence_spans(text: str) -> list[tuple[int, int]]:
    spans = []
    for match in re.finditer(r"[^.!?\n]+(?:[.!?]+|(?=\n|$))", text, re.MULTILINE):
        start, end = match.span()
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if start < end:
            spans.append((start, end))
    return spans


def find_mentions(document: Document, entities: list[Entity]) -> list[Mention]:
    spans = sentence_spans(document.text)
    aliases = sorted(
        ((alias, entity) for entity in entities for alias in entity.aliases),
        key=lambda item: (-len(item[0]), item[0].lower()),
    )
    occupied: list[tuple[int, int]] = []
    mentions: list[Mention] = []
    for alias, entity in aliases:
        pattern = re.compile(rf"(?<!\w){re.escape(alias)}(?!\w)", re.IGNORECASE)
        for match in pattern.finditer(document.text):
            start, end = match.span()
            if any(start < used_end and end > used_start for used_start, used_end in occupied):
                continue
            sentence_index = next(
                (index for index, (a, b) in enumerate(spans) if a <= start and end <= b),
                -1,
            )
            if sentence_index < 0:
                continue
            mentions.append(
                Mention(
                    entity_id=entity.id,
                    entity_label=entity.label,
                    entity_type=entity.type,
                    text=match.group(0),
                    start=start,
                    end=end,
                    sentence_index=sentence_index,
                )
            )
            occupied.append((start, end))
    return sorted(mentions, key=lambda item: (item.start, item.end, item.entity_id))


def generate_candidates(
    document: Document,
    mentions: list[Mention],
    ontology: Ontology,
    *,
    max_neighbors: int = 20,
) -> list[CandidateEdge]:
    if max_neighbors < 1:
        raise ValueError("max_neighbors must be positive.")
    spans = sentence_spans(document.text)
    best: dict[tuple[str, str, int], tuple[int, Mention, Mention]] = {}
    for source in mentions:
        neighbors = sorted(
            (
                target
                for target in mentions
                if target.entity_id != source.entity_id
                and target.sentence_index == source.sentence_index
                and ontology.allowed(source.entity_type, target.entity_type)
            ),
            key=lambda target: (abs(target.start - source.start), target.start),
        )[:max_neighbors]
        for target in neighbors:
            key = (source.entity_id, target.entity_id, source.sentence_index)
            distance = abs(target.start - source.start)
            current = best.get(key)
            if current is None or distance < current[0]:
                best[key] = (distance, source, target)

    candidates: list[CandidateEdge] = []
    for (_, _, sentence_index), (_, source, target) in sorted(best.items()):
        evidence_start, evidence_end = spans[sentence_index]
        stable = "\0".join(
            [
                document.id,
                source.entity_id,
                target.entity_id,
                str(evidence_start),
                str(evidence_end),
            ]
        )
        candidate_id = "edge_" + hashlib.sha256(stable.encode()).hexdigest()[:16]
        candidates.append(
            CandidateEdge(
                id=candidate_id,
                document_id=document.id,
                source_id=source.entity_id,
                source_label=source.entity_label,
                source_type=source.entity_type,
                target_id=target.entity_id,
                target_label=target.entity_label,
                target_type=target.entity_type,
                evidence_text=document.text[evidence_start:evidence_end],
                evidence_start=evidence_start,
                evidence_end=evidence_end,
                allowed_relations=ontology.allowed(source.entity_type, target.entity_type),
            )
        )
    return candidates
