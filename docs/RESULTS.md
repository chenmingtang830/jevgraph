# Results

Status: v0.1 hackathon pilot complete on 2026-09-20.

This page will contain aggregate results only. Detailed FewRel examples and run payloads remain in
gitignored `runs/` because they contain externally sourced text.

No result should be interpreted as a general model ranking, end-to-end knowledge-graph score, or
proof that a proposed edge is true. The aggregate evidence record is
[`docs/evidence/pilot-2026-09-20.json`](evidence/pilot-2026-09-20.json).

## FewRel closed-set pilot

The frozen sample used 16 relations, 10 examples per relation, seed 17, and batches of eight. The
entity pair was supplied by FewRel. The model chose among all 16 relations plus `none` and
`insufficient_evidence`.

| Metric | Jev | Local lexical baseline |
| --- | ---: | ---: |
| Cases | 160 | 160 |
| Complete-case accuracy | 85.0% (136/160) | 13.125% (21/160) |
| Accuracy at the pre-existing 0.85 probability / 0.80 confidence gate | 100% (95/95) | n/a |
| Coverage at that gate | 59.375% (95/160) | n/a |
| Successful / attempted requests | 20 / 21 | local |
| Request latency p50 / p95 | 444 / 625 ms | local |
| Reported successful input / output tokens | 128,988 / 32,456 | n/a |

One request returned HTTP 503. The runner stopped without retrying; the remaining non-overlapping
80-case continuation shard completed, and the final result was merged by case ID while retaining
the failed receipt. Successful Gateway responses reported `$0.00` provider cost. The failed
request's billing status is unknown. At the checked `$0.042/M` Jev input list price, the reported
successful input tokens have an illustrative equivalent of about `$0.00542`; that is not an invoice.

Twelve successful requests contained small rounded probability-sum drift affecting 16 answers.
JevGraph accepted only totals within `[0.95, 1.05]`, renormalized them, and recorded the action in
each receipt. The Gateway responses did not report a resolved model revision, so the evidence names
the requested alias `typesafe-ai/jev` and leaves `resolved_model` null.

This positive-only track does not measure false-positive edge rejection. The 100% gated subset is an
observed risk/coverage point on this sample, not a calibrated production guarantee.

## Synthetic end-to-end run

The repository-owned company-events example produced 12 mentions and 15 directed candidate edges.
JevGraph proposed the four explicit relations, rejected ten `none` directions, and deterministically
removed the reverse duplicate of the symmetric partnership edge. The explicit negative sentence did
not create a proposed edge. This is a functional demonstration, not a statistical evaluation.
