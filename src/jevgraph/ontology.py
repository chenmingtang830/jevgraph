from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Relation:
    id: str
    description: str
    source_types: tuple[str, ...]
    target_types: tuple[str, ...]
    symmetric: bool = False
    patterns: tuple[str, ...] = ()

    def allows(self, source_type: str, target_type: str) -> bool:
        source_ok = (
            not self.source_types or source_type in self.source_types or "*" in self.source_types
        )
        target_ok = (
            not self.target_types or target_type in self.target_types or "*" in self.target_types
        )
        return source_ok and target_ok


@dataclass(frozen=True)
class Ontology:
    name: str
    version: int
    relations: dict[str, Relation]

    @classmethod
    def load(cls, path: str | Path) -> Ontology:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Ontology must be a YAML object.")
        relations_raw = raw.get("relations")
        if not isinstance(relations_raw, dict) or not relations_raw:
            raise ValueError("Ontology must define at least one relation.")
        if len(relations_raw) > 253:
            raise ValueError(
                "Ontology supports at most 253 relations; two Jev choices are reserved."
            )

        relations: dict[str, Relation] = {}
        for relation_id, value in relations_raw.items():
            if not isinstance(relation_id, str) or not relation_id:
                raise ValueError("Relation IDs must be non-empty strings.")
            if not isinstance(value, dict):
                raise ValueError(f"Relation {relation_id!r} must be an object.")
            description = value.get("description")
            if not isinstance(description, str) or not description.strip():
                raise ValueError(f"Relation {relation_id!r} requires a description.")
            relation = Relation(
                id=relation_id,
                description=description.strip(),
                source_types=_strings(value.get("source_types", ["*"]), "source_types"),
                target_types=_strings(value.get("target_types", ["*"]), "target_types"),
                symmetric=bool(value.get("symmetric", False)),
                patterns=_strings(value.get("patterns", []), "patterns"),
            )
            relations[relation_id] = relation
        return cls(
            name=str(raw.get("name", Path(path).stem)),
            version=int(raw.get("version", 1)),
            relations=relations,
        )

    @classmethod
    def from_relations(cls, name: str, relations: dict[str, str], version: int = 1) -> Ontology:
        return cls(
            name=name,
            version=version,
            relations={
                relation_id: Relation(
                    id=relation_id,
                    description=description,
                    source_types=("*",),
                    target_types=("*",),
                )
                for relation_id, description in relations.items()
            },
        )

    def allowed(self, source_type: str, target_type: str) -> tuple[str, ...]:
        return tuple(
            relation.id
            for relation in self.relations.values()
            if relation.allows(source_type, target_type)
        )

    def criteria(self, relation_ids: tuple[str, ...] | None = None) -> dict[str, str]:
        selected = relation_ids or tuple(self.relations)
        criteria = {
            relation_id: self.relations[relation_id].description for relation_id in selected
        }
        criteria["none"] = "The evidence does not explicitly support any listed directed relation."
        criteria["insufficient_evidence"] = (
            "The evidence window is incomplete or too ambiguous to decide without more context."
        )
        return criteria


def _strings(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a list of strings.")
    return tuple(item.strip() for item in value if item.strip())
