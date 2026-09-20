# Results

Status: v0.4 direct relation-selection benchmark completed on 2026-09-20.

This page reports a narrow public-sample experiment, not a general model ranking, end-to-end
knowledge-graph score, graph truth claim, calibration result, or Human Approval. Aggregate evidence
is committed at [`docs/evidence/direct-2026-09-20.json`](evidence/direct-2026-09-20.json). The
v0.4 release publishes sanitized raw receipts (including failures), but never FewRel sentences,
prompts, credentials, or request headers.

## v0.4 primary: direct closed-set relation selection

Each request contained one supplied FewRel sentence/entity pair and the same 16 named relation
descriptions. Models returned one relation ID. The provider only saw an opaque `case_00000`-style
ID; original FewRel IDs remained local because they can include the gold relation prefix. The
frozen sample is FewRel 1.0 `train_wiki`, pinned revision
`278a2315d2138810a379cd8d5718914dc56e2582`, 16 relations × 10 cases, seed 17.

All runs used `relations-only` (no abstentions), batch size one, temperature zero, sequential
execution, no retries or fallback, and a 55-second timeout. Chat requests used a 4,096-token output
cap. Planned-case accuracy counts an uncompleted case as wrong.

| Metric | Jev | GPT-5.6 Luna | DeepSeek V4.1 Flash |
| --- | ---: | ---: | ---: |
| Planned-case accuracy | 87.50% (140/160) | **93.75% (150/160)** | 93.125% (149/160) |
| Coverage | 99.375% (159/160) | 100% (160/160) | 99.375% (159/160) |
| Successful / attempted requests | 159 / 160 | 160 / 160 | 159 / 160 |
| Request latency p50 / p95 | 313 / 431 ms | 1,769 / 4,104 ms | 2,276 / 15,627 ms |
| Sequential request time | 51.97 s | 333.86 s | 639.61 s |
| Input / output tokens | 156,228 / 29,404 | 82,418 / 15,446 | 87,709 / 76,936 |
| Provider-reported cost | $0 | $0.0350188 | $0.099019152 |
| Jev illustrative input-price equivalent | $0.006561576 | — | — |

Jev received one HTTP 503 at global case offset 98 with unknown billing status. It was not retried;
the runner stopped, then a separately recorded non-overlapping continuation started at offset 99.
The merged artifact retains the failed receipt. DeepSeek had one known-cost single-case
`incomplete_choice` after using the full 4,096-token output cap (`$0.0050775`); it too was retained
and not retried, while the next case proceeded. Luna completed every request.

The no-call conservative ceiling was `$1.798564168` across the three planned runs, below the `$5`
project cap. Actual known provider-reported cost was `$0.134037952`. One Jev request has unknown
billing status; the project does not claim a final invoice. Jev's `$0.006561576` value is an
illustrative input-token equivalent at the checked `$0.042/M` list price, not an invoice and not
comparable to billed chat-model cost.

The result isolates model choice among supplied relations for supplied pairs. It does not test
entity extraction, candidate generation, pair-blocking recall, negative rejection, graph truth, or
whether an output should be approved for use. FewRel is positive-only in this track and public, so
pretraining exposure remains a limitation.

## Superseded v0.2 pilot

The v0.2 Track 1 result is superseded and must not be used for model-capability claims. Its
provider-visible case IDs had the form `P101:123`, exposing a gold-bearing relation prefix. The
historical aggregate remains in the repository for audit only; v0.4 replaced it with opaque IDs.

## Additional stress test: v0.3 episodic FewRel validation

The v0.3 result is retained because failures and operating behavior are useful evidence, but it
answers a different question: public 5-way, 1-shot episodes with five batched query decisions and
labeled support examples. It is not the v0.4 primary table and not FewRel's hidden official
leaderboard.

| Metric | Jev | GPT-5.6 Luna | DeepSeek V4.1 Flash |
| --- | ---: | ---: | ---: |
| Planned-case accuracy | 85.6% (428/500) | **98.0% (490/500)** | 85.0% (425/500) |
| Coverage | 100% | 100% | 86% |
| Successful / attempted episodes | 100 / 100 | 100 / 100 | 86 / 100 |
| Request latency p50 / p95 | 368 / 471 ms | 6,142 / 16,651 ms | 11,821 / 49,474 ms |
| Provider-reported known cost | $0 | $0.107803 | $0.49140142 |

The v0.3 aggregate is [`docs/evidence/episodic-2026-09-20.json`](evidence/episodic-2026-09-20.json).
DeepSeek's twelve capped completions and two unknown-cost timeouts remain in that evidence; they
were not retried. This stress test still does not evaluate entity discovery or candidate generation.

## Synthetic end-to-end run

The repository-owned company-events example is a functional demonstration of mentions, local
candidate generation, validation, and export. It is not a statistical evaluation or evidence of
end-to-end graph quality.
