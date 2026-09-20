# Direct relation-selection benchmark brief

Open the [self-contained HTML report](index.html) or the
[two-page PDF](../../output/pdf/jevgraph-v0.5.1-direct-relation-report.pdf).

The first page puts the three recorded comparisons directly beside each other:

- p95 latency: Jev 431 ms, Luna 1,699 ms, DeepSeek 1,242 ms;
- cost per 100 planned decisions: Jev 0.410¢ illustrative, Luna 1.225¢ receipt,
  DeepSeek 1.462¢ receipt; and
- planned-case accuracy: Jev 87.50%, Luna 89.375%, DeepSeek 93.125%.

The second page contains only the frozen task definition, execution controls, retained failures,
and publication boundary. This follows the result-first field-report logic of
[DocJev](https://github.com/jerryjliu/docjev/blob/main/docs/report/README.md) using Proofpress's
Boardroom Clarity visual system.

Both formats are offline artifacts built from the committed sanitized aggregate evidence. They make
no API calls and contain no FewRel sentences, prompts, credentials, or request headers.

## Rebuild

From the repository root:

```bash
uv run python scripts/build_visual_report.py
uv run python scripts/build_pdf_report.py
```

The builders validate or derive the displayed metrics from
[`direct-reasoning-none-2026-09-20.json`](../evidence/direct-reasoning-none-2026-09-20.json).
