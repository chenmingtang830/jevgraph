from pathlib import Path

from jevgraph.builder import GraphBuilder
from jevgraph.extract import find_mentions, generate_candidates, load_entities
from jevgraph.models import Document
from jevgraph.ontology import Ontology
from jevgraph.providers.keyword import KeywordProvider

ROOT = Path(__file__).parents[1]


def test_ontology_and_candidates_preserve_evidence() -> None:
    ontology = Ontology.load(ROOT / "examples/ontology.yml")
    entities = load_entities(ROOT / "examples/entities.yml")
    document = Document(
        id="demo",
        text=(ROOT / "examples/company_events.txt").read_text(encoding="utf-8"),
    )
    mentions = find_mentions(document, entities)
    candidates = generate_candidates(document, mentions, ontology, max_neighbors=20)

    assert len(mentions) >= 8
    assert candidates
    assert len({candidate.id for candidate in candidates}) == len(candidates)
    for candidate in candidates:
        assert (
            document.text[candidate.evidence_start : candidate.evidence_end]
            == candidate.evidence_text
        )
        assert candidate.source_id != candidate.target_id
        assert candidate.allowed_relations


def test_keyword_demo_builds_expected_proposals() -> None:
    ontology = Ontology.load(ROOT / "examples/ontology.yml")
    entities = load_entities(ROOT / "examples/entities.yml")
    document = Document(
        id="demo",
        text=(ROOT / "examples/company_events.txt").read_text(encoding="utf-8"),
    )
    result = GraphBuilder(ontology=ontology, provider=KeywordProvider()).build(document, entities)
    proposed = {
        (
            edge.candidate.source_id,
            edge.decision.selected,
            edge.candidate.target_id,
        )
        for edge in result.edges
        if edge.status == "proposed"
    }

    assert ("mira_chen", "founded", "northstar_labs") in proposed
    assert ("northstar_labs", "released", "orbit_db") in proposed
    assert ("northstar_labs", "acquired", "atlas_systems") in proposed
    assert any(relation == "partnered_with" for _, relation, _ in proposed)
    assert all(edge.reason for edge in result.edges)


def test_entity_alias_overlap_prefers_longest_alias() -> None:
    entities = load_entities(ROOT / "examples/entities.yml")
    document = Document(id="overlap", text="Northstar Labs released OrbitDB.")
    mentions = find_mentions(document, entities)

    assert [mention.text for mention in mentions] == ["Northstar Labs", "OrbitDB"]
