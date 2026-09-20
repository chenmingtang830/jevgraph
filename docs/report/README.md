# JevGraph project and benchmark field report

Open the [self-contained three-page HTML report](index.html). The focused relation-selection
[two-page PDF](../../output/pdf/jevgraph-v0.5.1-direct-relation-report.pdf) remains available as a
separate printable benchmark brief.

The three HTML pages answer three different questions:

- **What is JevGraph?** One architecture diagram shows the complete document-to-candidate-graph
  pipeline, its local preparation, the bounded Jev decision, and the pinned smoke graph.
- **What does DocJev show?** Its separately published 40-document / eight-packet classification and
  split pilot, with latency, cost, and the one split-quality tradeoff shown together.
- **What did JevGraph measure?** The controlled 160-case direct relation-selection comparison across
  Jev, GPT-5.6 Luna, and DeepSeek V4.1 Flash.

The report keeps the DocJev pilot, JevGraph E2E smoke fixture, and FewRel relation benchmark visibly
separate. It follows the result-first field-report logic of
[DocJev](https://github.com/jerryjliu/docjev/blob/main/docs/report/README.md) using Proofpress's
Boardroom Clarity visual system.

The HTML is an offline artifact built from committed sanitized aggregate evidence. It makes no API
calls and contains no FewRel sentences, prompts, credentials, or request headers.

## Rebuild

From the repository root:

```bash
uv run python scripts/build_visual_report.py
uv run python scripts/build_pdf_report.py
```

The HTML builder validates or derives the displayed metrics from
[`direct-reasoning-none-2026-09-20.json`](../evidence/direct-reasoning-none-2026-09-20.json) and
[`project-report-2026-09-20.json`](../evidence/project-report-2026-09-20.json).
