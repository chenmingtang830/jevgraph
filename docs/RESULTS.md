# Results

Status: v0.4.2 controlled direct relation-selection benchmark completed on 2026-09-20.

This is a narrow public FewRel relation-identification experiment, not a general model ranking,
end-to-end KG score, graph truth claim, calibration result, or Human Approval. The primary aggregate
is [`direct-reasoning-none-2026-09-20.json`](evidence/direct-reasoning-none-2026-09-20.json).
Release artifacts contain sanitized IDs, predictions, and receipts only—never FewRel sentences,
prompts, credentials, headers, or private reasoning.

## v0.4.2 primary: chat reasoning disabled

The frozen sample is FewRel 1.0 `train_wiki`, pinned revision
`278a2315d2138810a379cd8d5718914dc56e2582`: 16 relations × 10 cases, seed 17. Each request
contains one supplied sentence/entity pair, the same 16 named relation descriptions, and an opaque
`case_00000`-style ID. Original FewRel IDs stay local because they can include the gold relation.

All models use `relations-only`, batch size one, temperature zero, sequential execution, no retries
or fallback, and a 55-second timeout. Luna and DeepSeek explicitly use
`reasoning.effort="none"` and `max_tokens=4096`; Jev's native typed Choice protocol has no
equivalent chat reasoning-effort field. Planned-case accuracy counts uncovered cases as incorrect.

| Metric | Jev | GPT-5.6 Luna | DeepSeek V4.1 Flash |
| --- | ---: | ---: | ---: |
| Planned-case accuracy | 87.50% (140/160) | 89.375% (143/160) | **93.125% (149/160)** |
| Coverage | 99.375% (159/160) | 100% (160/160) | 99.375% (159/160) |
| Successful / attempted requests | 159 / 160 | 160 / 160 | 159 / 160 |
| Request latency p50 / p95 | 313 / 431 ms | 1,164 / 1,699 ms | 691 / 1,242 ms |
| Sequential request time | 51.97 s | 195.62 s | 120.44 s |
| Input / output tokens | 156,228 / 29,404 | 82,418 / 2,592 | 83,739 / 2,270 |
| Provider-reported cost | $0 | $0.019594 | $0.023389532 |
| Jev illustrative input-price equivalent | $0.006561576 | — | — |
| Cost / planned decision | $0.000041010 illustrative | $0.000122463 receipt | $0.000146185 receipt |

The chat inputs are semantically identical but provider usage accounting/tokenizers differ slightly.
Jev's input is larger because it uses a native typed `state + questions` payload rather than chat.
Its output is also intentionally richer: every choice response includes the selected relation, a
probability for each of the 16 criteria, and confidence, while chat baselines return one relation ID.
Explicitly disabling chat reasoning reduced output cost and tail latency: Luna output fell from
15,446 to 2,592 tokens; DeepSeek output fell from 76,936 to 2,270. DeepSeek retained its
planned-case accuracy; Luna dropped from 93.75% to 89.375%. Gateway usage does not separately
report reasoning tokens, so this is operational evidence rather than a token-level attribution.

Jev's one HTTP 503 had unknown billing status and was never retried; a non-overlapping continuation
began at the next global offset. DeepSeek's one known-cost failure was
`prediction_outside_criteria` (14 output tokens), not a capped completion; it was retained and not
retried. The controlled chat rerun cost was `$0.042983532`; all v0.4 known provider-reported cost
is `$0.177021484`. The conservative first-run plus controlled-rerun ceiling was `$3.583515668`,
below the `$5` project cap. Jev's illustrative value is not an invoice.

## Historical v0.4.0 provider-default reasoning run

The original v0.4.0 chat results used provider-default reasoning because no explicit effort was
sent. They remain published for audit at [`direct-2026-09-20.json`](evidence/direct-2026-09-20.json)
but are superseded for the primary comparison by the controlled v0.4.2 table.

| Metric | Luna default | DeepSeek default |
| --- | ---: | ---: |
| Planned-case accuracy | 93.75% | 93.125% |
| Output tokens | 15,446 | 76,936 |
| p95 latency | 4,104 ms | 15,627 ms |
| Provider-reported cost | $0.0350188 | $0.099019152 |

## Superseded v0.2 pilot and additional v0.3 stress test

The v0.2 Track 1 pilot is superseded because provider-visible IDs had the form `P101:123`, exposing
a gold-bearing relation prefix. The v0.3 public 5-way, 1-shot episodic result remains an additional
stress test, not the direct-comparison primary result: Jev 85.6%, Luna 98.0%, and DeepSeek 85.0%
planned-case accuracy over 500 queries. It has labeled support examples and batched queries, so it
answers a different question and is not FewRel's hidden leaderboard.

This benchmark does not test entity extraction, candidate generation, negative rejection, graph
truth, or approval for reuse.
