import csv
import json
from pathlib import Path

from jevgraph.export import export_csv, export_neo4j


def test_exports_only_proposed_edges(tmp_path: Path) -> None:
    run = {
        "document": {
            "source_sha256": "source-hash",
            "canonical_sha256": "canonical-hash",
        },
        "entities": [
            {"id": "a", "label": "A", "type": "organization"},
            {"id": "b", "label": "B", "type": "organization"},
        ],
        "edges": [
            {
                "status": "proposed",
                "candidate": {
                    "source_id": "a",
                    "target_id": "b",
                    "document_id": "d",
                    "evidence_start": 0,
                    "evidence_end": 10,
                    "evidence_text": "A bought B",
                    "evidence_source_spans": [
                        {
                            "page": 2,
                            "document_start": 0,
                            "document_end": 10,
                            "page_start": 4,
                            "page_end": 14,
                        }
                    ],
                },
                "decision": {
                    "selected": "acquired",
                    "selected_probability": 0.95,
                    "confidence": 0.9,
                    "model": "jev",
                },
            },
            {
                "status": "review",
                "candidate": {"source_id": "b", "target_id": "a"},
                "decision": {"selected": "acquired"},
            },
        ],
    }
    nodes, edges = export_csv(run, tmp_path / "csv")
    with edges.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    cypher = export_neo4j(run, tmp_path / "graph.cypher")

    assert nodes.exists()
    assert len(rows) == 1
    assert rows[0]["relation"] == "acquired"
    assert rows[0]["canonical_sha256"] == "canonical-hash"
    assert json.loads(rows[0]["evidence_source_spans"])[0]["page"] == 2
    text = cypher.read_text(encoding="utf-8")
    assert ":ACQUIRED" in text
    assert "review" not in text
    assert json.dumps("A bought B") in text
    assert json.dumps("canonical-hash") in text
    assert "evidence_source_spans" in text
