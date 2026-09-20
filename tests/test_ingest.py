from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from jevgraph.extract import evidence_source_spans
from jevgraph.ingest import DOCJEV_REVISION, load_document
from jevgraph.models import Document, EvidenceSourceSpan, PageSpan


def test_text_ingestion_records_digest_without_document_extra(tmp_path: Path) -> None:
    source = tmp_path / "note.txt"
    source.write_text("Northstar Labs acquired Atlas Systems.", encoding="utf-8")

    document = load_document(source)

    assert document.id == "note"
    assert document.source_name == "note.txt"
    assert document.source_sha256 == hashlib.sha256(source.read_bytes()).hexdigest()
    assert document.canonical_sha256 is None
    assert document.page_spans == ()


def test_docjev_ingestion_preserves_pages_hashes_and_parser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "packet.pdf"
    source.write_bytes(b"fake-pdf-for-adapter-test")
    calls: list[dict[str, object]] = []

    class Parser:
        def model_dump(self) -> dict[str, object]:
            return {"name": "liteparse", "version": "2.14.6", "options": {}}

    def parse_document(path: Path, **options: object) -> SimpleNamespace:
        calls.append({"path": path, **options})
        return SimpleNamespace(
            source_name="packet.pdf",
            source_sha256="a" * 64,
            canonical_sha256="b" * 64,
            parser=Parser(),
            pages=[
                SimpleNamespace(number=1, text="Ada founded Northstar.", blank=False),
                SimpleNamespace(number=2, text="Northstar acquired Atlas.", blank=False),
            ],
        )

    module = ModuleType("jev_docs")
    module.parse_document = parse_document  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "jev_docs", module)

    document = load_document(source, cache_dir=tmp_path / "cache", use_cache=False)

    assert calls == [
        {
            "path": source.resolve(),
            "ocr": "liteparse",
            "cache_dir": tmp_path / "cache",
            "use_cache": False,
        }
    ]
    assert document.id == f"packet-{'b' * 12}"
    assert document.text == "Ada founded Northstar.\n\nNorthstar acquired Atlas."
    assert document.page_spans == (
        PageSpan(page=1, text_start=0, text_end=22, blank=False),
        PageSpan(page=2, text_start=24, text_end=49, blank=False),
    )
    assert document.parser["adapter_revision"] == DOCJEV_REVISION
    assert document.parser["name"] == "liteparse"


def test_evidence_offsets_project_to_page_local_offsets() -> None:
    document = Document(
        id="packet",
        text="Alpha Beta.\n\nGamma Delta.",
        page_spans=(
            PageSpan(page=1, text_start=0, text_end=11),
            PageSpan(page=2, text_start=13, text_end=25),
        ),
    )

    assert evidence_source_spans(document, 6, 24) == (
        # The separator at document offsets 11:13 has no source-page claim.
        EvidenceSourceSpan(
            page=1,
            document_start=6,
            document_end=11,
            page_start=6,
            page_end=11,
        ),
        EvidenceSourceSpan(
            page=2,
            document_start=13,
            document_end=24,
            page_start=0,
            page_end=11,
        ),
    )


def test_unknown_input_type_fails_closed(tmp_path: Path) -> None:
    source = tmp_path / "data.csv"
    source.write_text("a,b", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported input format"):
        load_document(source)
