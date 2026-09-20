"""Document ingestion with an optional, pinned DocJev adapter."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .models import Document, PageSpan

TEXT_SUFFIXES = {".md", ".txt"}
DOCJEV_SUFFIXES = {".docx", ".pdf", ".pptx"}
DOCJEV_REVISION = "9ed0fe05984ce1906af9272b8b400c8d46520f98"


def load_document(
    path: str | Path,
    *,
    cache_dir: str | Path | None = None,
    use_cache: bool = True,
) -> Document:
    """Load text directly or use DocJev's local LiteParse document pipeline.

    Cloud OCR and DocJev's hosted classification/splitting are intentionally not
    invoked here. The graph builder's live provider remains separately budgeted.
    """

    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise ValueError("Input document does not exist or is not a file.")
    suffix = source.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        raw = source.read_bytes()
        return Document(
            id=source.stem,
            text=raw.decode("utf-8"),
            source_name=source.name,
            source_sha256=hashlib.sha256(raw).hexdigest(),
            parser={"name": "utf-8", "version": "1"},
        )
    if suffix not in DOCJEV_SUFFIXES:
        supported = ", ".join(sorted(TEXT_SUFFIXES | DOCJEV_SUFFIXES))
        raise ValueError(f"Unsupported input format {suffix!r}; expected one of: {supported}.")

    try:
        from jev_docs import parse_document
    except ImportError as exc:
        raise ValueError(
            "PDF, DOCX, and PPTX ingestion requires the documents extra: "
            "uv sync --extra documents"
        ) from exc

    parsed = parse_document(
        source,
        ocr="liteparse",
        cache_dir=cache_dir,
        use_cache=use_cache,
    )
    text, page_spans = _flatten_pages(parsed.pages)
    parser = _model_dump(parsed.parser)
    canonical_sha256 = str(parsed.canonical_sha256)
    return Document(
        id=f"{source.stem}-{canonical_sha256[:12]}",
        text=text,
        source_name=str(parsed.source_name),
        source_sha256=str(parsed.source_sha256),
        canonical_sha256=canonical_sha256,
        parser={**parser, "adapter": "docjev", "adapter_revision": DOCJEV_REVISION},
        page_spans=page_spans,
    )


def _flatten_pages(pages: list[Any]) -> tuple[str, tuple[PageSpan, ...]]:
    chunks: list[str] = []
    spans: list[PageSpan] = []
    cursor = 0
    for index, page in enumerate(pages):
        if index:
            chunks.append("\n\n")
            cursor += 2
        text = str(page.text)
        start = cursor
        chunks.append(text)
        cursor += len(text)
        spans.append(
            PageSpan(
                page=int(page.number),
                text_start=start,
                text_end=cursor,
                blank=bool(page.blank),
            )
        )
    return "".join(chunks), tuple(spans)


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        result = value.model_dump()
        if isinstance(result, dict):
            return result
    if isinstance(value, dict):
        return value
    raise ValueError("DocJev returned invalid parser metadata.")
