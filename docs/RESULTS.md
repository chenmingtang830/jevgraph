# Results

Status: v0.2 three-model hackathon pilot complete on 2026-09-20.

This page will contain aggregate results only. Detailed FewRel examples and run payloads remain in
gitignored `runs/` because they contain externally sourced text.

No result should be interpreted as a general model ranking, end-to-end knowledge-graph score, or
proof that a proposed edge is true. The aggregate evidence records are
[`docs/evidence/pilot-2026-09-20.json`](evidence/pilot-2026-09-20.json) and
[`docs/evidence/comparison-2026-09-20.json`](evidence/comparison-2026-09-20.json).

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

## GPT-5.6 Luna and DeepSeek V4.1 Flash comparison

All three models saw the same frozen 160 positive FewRel cases, supplied directed entity pairs, 16
relation descriptions, and the two abstention choices. The final chat-model configuration used
temperature zero and a 16,384 maximum-output-token ceiling. Jev used its native typed Choice
protocol; the chat models returned only a strict JSON map of relation IDs.

| Metric | Jev | GPT-5.6 Luna | DeepSeek V4.1 Flash |
| --- | ---: | ---: | ---: |
| Raw accuracy | **85.0% (136/160)** | 80.0% (128/160) | 83.75% (134/160) |
| Final case coverage | 100% | 100% | 100% after continuation |
| Successful / attempted requests | 20 / 21 | 20 / 20 | 51 / 53 |
| Batch plan | 8 | 8 | 8, then 4, then 2 |
| Request latency p50 / p95 | **444 / 625 ms** | 5,154 / 7,413 ms | 4,400 / 22,335 ms |
| Sequential request time, including failures | **9.46 s** | 106.73 s | 407.66 s |
| Successful input / output tokens | 128,988 / 32,456 | 18,548 / 8,918 | 36,137 / 79,506 |
| Known Gateway cost | $0 reported | $0.0144112 | $0.10255982 |
| Failed requests with unknown cost | 1 | 0 | 2 |
| Output contract | choice + probabilities + confidence | choice only | choice only |

DeepSeek reached almost the same raw accuracy as Jev, but two requests exhausted the output ceiling:
one at batch eight and one at batch four. The recorded run continued from non-overlapping offsets at
smaller batch sizes and retained both failed receipts. Batch two completed the remaining 76 cases.
This is useful product evidence: the model can classify the pairs, but it did not sustain the same
batch contract. Its latency percentiles therefore describe the mixed operational path, not a fixed
batch-eight run.

Luna completed every final request at batch eight. Two earlier exploratory runs with an unfixed
sampling default scored 80.625% and 73.75%; the final temperature-zero run scored 80.0%. Those runs
are not cherry-picked into the main table, but the variance motivated freezing the sampling setting.

The error pattern was mostly conservative abstention. Because this FewRel sample contains only
positive relations, every `none` answer is wrong: Jev selected `none` in 11 of 24 errors, Luna in all
32 errors, and DeepSeek in 25 of 26 errors. A separate negative-pair dataset is required before
calling that behavior good or bad for graph precision.

Jev's provider-reported cost was zero for successful requests; at the checked input list price its
successful input had a $0.00542 illustrative equivalent. That is not directly comparable to billed
chat-model cost. Across all exploratory and final calls in the hackathon, known billed cost was
$0.150184. Five failed requests across the Jev and chat experiments have unknown billing status; a
deliberately conservative request-size/output-ceiling calculation keeps the total below $0.315,
well inside the approved $5 cap.

## Synthetic end-to-end run

The repository-owned company-events example produced 12 mentions and 15 directed candidate edges.
JevGraph proposed the four explicit relations, rejected ten `none` directions, and deterministically
removed the reverse duplicate of the symmetric partnership edge. The explicit negative sentence did
not create a proposed edge. This is a functional demonstration, not a statistical evaluation.
