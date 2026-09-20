# Results

Status: v0.2 closed-set pilot and v0.3 episodic validation complete on 2026-09-20.

This page contains aggregate results. FewRel source examples and provider payloads remain
gitignored, while sanitized ID/prediction/receipt run artifacts are published in the v0.3 release
evidence bundle.

No result should be interpreted as a general model ranking, end-to-end knowledge-graph score, or
proof that a proposed edge is true. The aggregate evidence records are
[`docs/evidence/pilot-2026-09-20.json`](evidence/pilot-2026-09-20.json) and
[`docs/evidence/comparison-2026-09-20.json`](evidence/comparison-2026-09-20.json). The v0.3
episodic evidence is
[`docs/evidence/episodic-2026-09-20.json`](evidence/episodic-2026-09-20.json).

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

### Jev cost planning

The 2026-09-20 Gateway evidence is deliberately reported three ways. Successful Jev receipts
reported `$0`; some Vercel catalog surfaces marked the model free; the Gateway `/v1/models` API
listed `$0.042/M` input tokens and `$0/M` output tokens. The API price is therefore used only for
an illustrative forward estimate, while receipts remain the source of truth for this run.

Observed input density ranged from 471 tokens per query in the 5-way 1-shot episodic run to 806
tokens per case in the 16-relation Track 1 run. At `$0.042/M`, that corresponds to roughly
`$0.000020–$0.000034` per already-selected candidate pair, or `$1.98–$3.39` per 100,000 decisions.
A `$5` allowance would cover roughly 148,000–253,000 similar decisions. This is an empirical
payload-range estimate, not a provider quote: ontology size, support count, sentence length,
batching, caching, pricing, and free-tier policy can all change it.

## FewRel public episodic validation

Track 2 used 100 deterministic 5-way 1-shot episodes from public `val_wiki`, with one held-out
query per relation: 500 planned query decisions. Relation IDs and query IDs were opaque to the
models, and support/query order was independently shuffled. Every episode used one batched request,
reported as `query_mode=batched_transductive`. This is public validation shaped like the FewRel
task, not a hidden-test leaderboard result and not an end-to-end graph benchmark.

| Metric | Jev | GPT-5.6 Luna | DeepSeek V4.1 Flash |
| --- | ---: | ---: | ---: |
| Correct / planned queries | 428 / 500 | **490 / 500** | 425 / 500 |
| Planned-case accuracy | 85.6% | **98.0%** | 85.0% |
| Complete-case accuracy | 85.6% | 98.0% | **98.84%** (425/430) |
| Coverage | **100%** | **100%** | 86% |
| Successful / attempted episodes | **100 / 100** | **100 / 100** | 86 / 100 |
| Request latency p50 / p95 | **368 / 471 ms** | 6,142 / 16,651 ms | 11,821 / 49,474 ms |
| Sequential request time | **36.97 s** | 775.44 s | 1,834.85 s |
| Input / output tokens | 235,361 / 31,800 | 85,403 / 75,602 | 92,879 / 423,869 |
| Provider-reported known cost | **$0** | $0.107803 | $0.49140142 |
| Unknown-cost requests | 0 | 0 | 2 |

DeepSeek had 12 completions hit the 16,384 output-token ceiling and two requests time out at 55
seconds. It was nearly perfect when it completed, but planned-case accuracy counts missing queries
against the frozen denominator. Its known-cost failed requests consumed `$0.2393376`, 48.7% of its
known formal-run cost. The runner did not retry them: it preserved each receipt and continued only
after known-cost failures; the two unknown-cost timeouts stopped their shards and required
non-overlapping manual continuations.

Jev completed all 100 episodes in 36.97 seconds of sequential request time. At the pre-existing
0.85 probability / 0.80 confidence gate, it retained 286/500 queries (57.2% coverage) with 278/286
correct (97.2%). That is a useful triage point, not a calibration guarantee, and it did not repeat
Track 1's observed 100% gated accuracy.

Luna was the strongest result under the full request contract: 98.0% planned-case accuracy with no
failed episodes. On the identical cases, Luna corrected 64 cases Jev missed, while Jev corrected
two cases Luna missed; both were correct on 426 and both wrong on eight.

The five-episode canaries were the first five episodes of the same seed-17 stream, not independent
evaluation data. They existed only to verify provider contracts before the formal run: Jev scored
72%, Luna 96%, and DeepSeek 100%. The gap between those tiny checks and the 100-episode operational
result is itself a warning against ranking models from canaries.

Across v0.3 canaries and formal calls, known Gateway cost was `$0.62699352`. Including every v0.2
exploratory and formal call brings known project cost to `$0.77717750`. Charging each unknown-cost
request at its conservative configured ceiling yields a project upper bound of `$0.98180870`, below
the approved `$5` cap.

## Synthetic end-to-end run

The repository-owned company-events example produced 12 mentions and 15 directed candidate edges.
JevGraph proposed the four explicit relations, rejected ten `none` directions, and deterministically
removed the reverse duplicate of the symmetric partnership edge. The explicit negative sentence did
not create a proposed edge. This is a functional demonstration, not a statistical evaluation.
