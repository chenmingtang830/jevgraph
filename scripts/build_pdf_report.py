"""Build the two-page JevGraph benchmark PDF from committed aggregate evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = ROOT / "docs/evidence/direct-reasoning-none-2026-09-20.json"
DEFAULT_OUTPUT = ROOT / "output/pdf/jevgraph-v0.5.1-direct-relation-report.pdf"

PAPER = HexColor("#FFFFFF")
WARM = HexColor("#F8F7F3")
INK = HexColor("#181A20")
INK_2 = HexColor("#555B66")
INK_3 = HexColor("#686F78")
LINE = HexColor("#D7DCD9")
ACCENT = HexColor("#0E6675")
ACCENT_SOFT = HexColor("#EFF7F7")


def _text(
    c: canvas.Canvas, text: str, x: float, y: float, size: float, *, color=INK, font="Helvetica"
) -> None:
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, y, text)


def _wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    size: float,
    *,
    color=INK_2,
    leading: float | None = None,
    font="Helvetica",
) -> float:
    leading = leading or size * 1.35
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if stringWidth(candidate, font, size) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    c.setFillColor(color)
    c.setFont(font, size)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def _header(
    c: canvas.Canvas, left: str, right: str, width: float, height: float, margin: float
) -> None:
    c.setStrokeColor(INK)
    c.setLineWidth(0.8)
    c.rect(margin, height - margin - 18, 18, 18, stroke=1, fill=0)
    c.setFillColor(HexColor("#2E8FA3"))
    c.circle(margin + 18, height - margin - 18, 4.5, stroke=0, fill=1)
    _text(c, left, margin + 30, height - margin - 14, 11, font="Helvetica-Bold")
    right_width = stringWidth(right, "Courier-Bold", 7)
    _text(
        c,
        right,
        width - margin - right_width,
        height - margin - 13,
        7,
        color=INK_3,
        font="Courier-Bold",
    )
    c.line(margin, height - margin - 28, width - margin, height - margin - 28)


def _bar_chart(
    c: canvas.Canvas,
    *,
    x: float,
    y: float,
    width: float,
    title: str,
    subtitle: str,
    values: list[tuple[str, float, str]],
    caption: str,
) -> None:
    height = 175
    c.setFillColor(WARM)
    c.setStrokeColor(LINE)
    c.rect(x, y - height, width, height, stroke=1, fill=1)
    _text(c, title, x + 14, y - 21, 10, font="Helvetica-Bold")
    _text(c, subtitle, x + 14, y - 35, 6.8, color=INK_3)
    max_value = max(value for _, value, _ in values)
    row_y = y - 65
    zero_x = x + 14
    for name, value, label in values:
        if name == "Jev":
            c.setFillColor(ACCENT_SOFT)
            c.rect(x + 8, row_y - 22, width - 16, 31, stroke=0, fill=1)
        _text(c, name, x + 14, row_y, 7.5, font="Helvetica-Bold")
        label_width = stringWidth(label, "Courier-Bold", 6.7)
        _text(c, label, x + width - 14 - label_width, row_y, 6.7, color=INK_2, font="Courier-Bold")
        c.setFillColor(LINE)
        c.rect(zero_x, row_y - 11, width - 28, 5, stroke=0, fill=1)
        c.setFillColor(ACCENT if name == "Jev" else HexColor("#747B84"))
        c.rect(zero_x, row_y - 11, (width - 28) * value / max_value, 5, stroke=0, fill=1)
        c.setStrokeColor(INK_3)
        c.line(zero_x, row_y - 12, zero_x, row_y - 5)
        row_y -= 35
    c.setStrokeColor(LINE)
    c.line(x + 14, y - height + 28, x + width - 14, y - height + 28)
    _text(c, caption, x + 14, y - height + 13, 6.6, color=INK_3)


def _page_one(c: canvas.Canvas, evidence: dict[str, object], width: float, height: float) -> None:
    margin = 42
    _header(
        c,
        "JevGraph / benchmark brief",
        "V0.5.1  |  160 CASES  |  REASONING NONE",
        width,
        height,
        margin,
    )
    _text(c, "Jev is the fastest option", margin, height - 120, 31, font="Helvetica-Bold")
    _text(c, "in this relation-selection run.", margin, height - 155, 31, font="Helvetica-Bold")
    _text(c, "431 ms p95", margin, height - 192, 22, color=ACCENT, font="Helvetica-Bold")
    _wrapped(
        c,
        (
            "It also has the lowest planning-cost signal. Accuracy is lower than both chat "
            "comparators, so this is an operational tradeoff - not a general model ranking."
        ),
        margin + 190,
        height - 181,
        width - margin * 2 - 190,
        9.3,
    )

    models = evidence["models"]
    jev = models["typesafe-ai/jev"]
    luna = models["openai/gpt-5.6-luna"]
    deep = models["deepseek/deepseek-v4.1-flash"]
    gap = 12
    chart_width = (width - margin * 2 - gap * 2) / 3
    chart_top = height - 225
    _bar_chart(
        c,
        x=margin,
        y=chart_top,
        width=chart_width,
        title="p95 latency",
        subtitle="Lower is better | milliseconds",
        values=[
            ("Jev", jev["request_latency_p95_ms"], "431 ms"),
            ("GPT-5.6 Luna", luna["request_latency_p95_ms"], "1,699 ms"),
            ("DeepSeek V4.1", deep["request_latency_p95_ms"], "1,242 ms"),
        ],
        caption="Measured request latency.",
    )
    _bar_chart(
        c,
        x=margin + chart_width + gap,
        y=chart_top,
        width=chart_width,
        title="Cost / 100 planned",
        subtitle="Lower is better | cents",
        values=[
            (
                "Jev",
                jev["illustrative_input_list_price_equivalent_per_100_planned_cases_cents"],
                "0.410c",
            ),
            ("GPT-5.6 Luna", luna["provider_reported_cost_per_100_planned_cases_cents"], "1.225c"),
            ("DeepSeek V4.1", deep["provider_reported_cost_per_100_planned_cases_cents"], "1.462c"),
        ],
        caption="Jev illustrative; chat values are receipts.",
    )
    _bar_chart(
        c,
        x=margin + (chart_width + gap) * 2,
        y=chart_top,
        width=chart_width,
        title="Planned-case accuracy",
        subtitle="Higher is better | percent",
        values=[
            ("Jev", jev["planned_case_accuracy"] * 100, "87.50%"),
            ("GPT-5.6 Luna", luna["planned_case_accuracy"] * 100, "89.375%"),
            ("DeepSeek V4.1", deep["planned_case_accuracy"] * 100, "93.125%"),
        ],
        caption="Same 160-case denominator.",
    )

    labels = [
        ("VS LUNA", "3.94x lower p95 latency"),
        ("VS DEEPSEEK", "2.88x lower p95 latency"),
        ("COST SIGNAL", "2.99-3.56x lower"),
        ("ACCURACY GAP", "-1.875 to -5.625 pp"),
    ]
    box_y = 86
    box_width = (width - margin * 2) / 4
    c.setStrokeColor(INK)
    c.line(margin, box_y + 50, width - margin, box_y + 50)
    c.line(margin, box_y, width - margin, box_y)
    for index, (label, value) in enumerate(labels):
        box_x = margin + index * box_width
        if index:
            c.setStrokeColor(LINE)
            c.line(box_x, box_y, box_x, box_y + 50)
        _text(c, label, box_x + 10, box_y + 35, 6.5, color=ACCENT, font="Courier-Bold")
        _text(c, value, box_x + 10, box_y + 14, 8.5, font="Helvetica-Bold")
    _text(
        c,
        (
            "Cost basis: Jev illustrative input list-price equivalent; Luna and DeepSeek "
            "provider receipts."
        ),
        margin,
        57,
        6.5,
        color=INK_3,
        font="Courier",
    )


def _page_two(c: canvas.Canvas, evidence: dict[str, object], width: float, height: float) -> None:
    margin = 42
    _header(
        c,
        "JevGraph / evidence record",
        "DIRECT CLOSED-SET RELATION SELECTION",
        width,
        height,
        margin,
    )
    _text(
        c,
        "Exactly what was measured - and what was not.",
        margin,
        height - 115,
        27,
        font="Helvetica-Bold",
    )
    _wrapped(
        c,
        (
            "Each provider saw the same one-case request, 16 relation descriptions, and an "
            "opaque case ID. Failed calls remain in the denominator and release evidence."
        ),
        margin,
        height - 145,
        width - margin * 2,
        8.5,
    )

    steps = [
        ("INPUT", "One positive case", "Sentence plus supplied source and target entities."),
        ("CHOICE", "16 relations", "No abstention in this positive-only sample."),
        ("EXECUTION", "160 requests / model", "Sequential, temperature 0, 55 s timeout, no retry."),
        ("SCORE", "Planned-case accuracy", "Uncovered cases count incorrect; gold IDs stay local."),
    ]
    top = height - 190
    step_width = (width - margin * 2) / 4
    c.setStrokeColor(INK)
    c.line(margin, top, width - margin, top)
    c.line(margin, top - 115, width - margin, top - 115)
    for index, (label, title, copy) in enumerate(steps):
        x = margin + index * step_width
        if index:
            c.setStrokeColor(LINE)
            c.line(x, top, x, top - 115)
        _text(c, label, x + 12, top - 20, 6.5, color=ACCENT, font="Courier-Bold")
        _text(c, title, x + 12, top - 54, 10, font="Helvetica-Bold")
        _wrapped(c, copy, x + 12, top - 73, step_width - 24, 7.2)

    col_gap = 32
    col_width = (width - margin * 2 - col_gap) / 2
    left = margin
    right = margin + col_width + col_gap
    audit_top = top - 150
    c.setStrokeColor(INK)
    c.line(left, audit_top, left + col_width, audit_top)
    _text(c, "Failure ledger", left, audit_top - 24, 12, font="Helvetica-Bold")
    failures = [
        ("Jev", "HTTP 503 at offset 98; unknown cost; no retry; continuation at 99."),
        ("DeepSeek", "prediction_outside_criteria; known cost; receipt retained; no retry."),
        ("Luna", "160 / 160 valid scored decisions."),
    ]
    row_y = audit_top - 50
    for name, copy in failures:
        c.setStrokeColor(LINE)
        c.line(left, row_y + 12, left + col_width, row_y + 12)
        _text(c, name, left, row_y, 8, font="Helvetica-Bold")
        _wrapped(c, copy, left + 75, row_y, col_width - 75, 7.2)
        row_y -= 36

    c.setFillColor(ACCENT_SOFT)
    c.rect(right, audit_top - 95, col_width, 95, stroke=0, fill=1)
    c.setStrokeColor(ACCENT)
    c.line(right, audit_top, right + col_width, audit_top)
    _text(
        c,
        "Ready to publish as a scoped benchmark.",
        right + 16,
        audit_top - 29,
        12,
        color=ACCENT,
        font="Helvetica-Bold",
    )
    _wrapped(
        c,
        (
            "The task, revision, seed, request controls, cost basis, failure receipts, and "
            "checksums are all preserved."
        ),
        right + 16,
        audit_top - 51,
        col_width - 32,
        7.5,
    )
    _text(c, "LIMITS", right, audit_top - 122, 6.5, color=ACCENT, font="Courier-Bold")
    limits = [
        "Relation identification only; not end-to-end graph construction.",
        "Positive-only public sample; possible training-data exposure.",
        "One seed; no confidence interval or statistical test.",
        "Jev cost is illustrative, not an invoice-to-invoice comparison.",
    ]
    limit_y = audit_top - 142
    for item in limits:
        _text(c, "-", right, limit_y, 7.2, color=INK_2)
        limit_y = _wrapped(c, item, right + 10, limit_y, col_width - 10, 7.2)
        limit_y -= 4

    c.setStrokeColor(INK)
    c.line(margin, 64, width - margin, 64)
    _text(
        c,
        "FewRel train_wiki | revision 278a2315... | seed 17 | no retries or fallback",
        margin,
        48,
        6.5,
        color=INK_3,
        font="Courier",
    )
    _text(c, evidence["release"], width - margin - 34, 48, 6.5, color=ACCENT, font="Courier-Bold")


def build(evidence_path: Path, output_path: Path) -> None:
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = landscape(A4)
    c = canvas.Canvas(str(output_path), pagesize=(width, height), pageCompression=1)
    c.setTitle("JevGraph v0.5.1 Direct Relation Selection Benchmark")
    c.setAuthor("JevGraph")
    c.setSubject("Controlled FewRel direct relation-selection results")
    _page_one(c, evidence, width, height)
    c.showPage()
    _page_two(c, evidence, width, height)
    c.save()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.evidence, args.out)


if __name__ == "__main__":
    main()
