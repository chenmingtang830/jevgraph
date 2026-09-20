# Experiment protocol

## Primary track: v0.4.2 controlled direct relation selection

This protocol measures only relation identification for an already supplied directed candidate pair:

```text
sentence + source entity + target entity + 16 explicit relations → one selected relation
```

The frozen public sample is FewRel 1.0 `train_wiki`, revision
`278a2315d2138810a379cd8d5718914dc56e2582`: 16 relations × 10 cases, seed 17, 160 planned
decisions. All three models receive the same case sequence, relation IDs, names, descriptions, and
ordering. Each provider request holds exactly one case, uses a locally generated opaque
`case_00000`-style ID, and contains no source ID that encodes the gold relation. Original FewRel
IDs stay local to scoring and audit.

The answer set is explicitly `relations-only`: exactly the 16 sampled FewRel relations, with no
`none` or `insufficient_evidence` option. That is appropriate only because this split is
positive-only; it does not assess negative rejection.

| Setting | Value |
| --- | --- |
| Models | `typesafe-ai/jev`, `openai/gpt-5.6-luna`, `deepseek/deepseek-v4.1-flash` |
| Batch size / requests | 1 / 160 per model |
| Temperature / execution | 0 / sequential, no concurrency |
| Retries / fallback | 0 / 0 |
| Timeout | 55 seconds |
| Chat completion limit | 4,096 tokens |
| Chat reasoning effort | explicit `none` |
| Score | correct predictions divided by all 160 planned cases |

The controlled chat rerun no-call ceiling was Luna `$0.8710942` plus DeepSeek `$0.9138573`.
Together with the first v0.4 run's conservative `$1.798564168` ceiling, the conservative combined
upper bound was `$3.583515668`, below the project `$5` absolute cap. These are safeguards, not
provider quotes.

No case is retried. A failed receipt is always persisted. With
`--continue-after-known-failure`, a known-cost failure is skipped and the next case starts. An
unknown-cost failure stops immediately; after an upper-bound audit, a separate non-overlapping
shard may start from the next global case offset and be merged while retaining that receipt.

Coverage is completed planned cases divided by 160. Planned-case accuracy counts every uncovered
case as incorrect; complete-case accuracy is diagnostic only. Provider-reported charges and Jev's
input-token illustrative list-price equivalent remain separate.

The v0.2 closed-set pilot is **superseded** for capability claims: provider-visible IDs used the
form `P101:123`, which exposed a gold-bearing relation prefix. The v0.3 5-way few-shot episodic
public validation remains an **additional stress test**, not the v0.4 primary comparison: it has
labeled support examples and five query decisions per request.

## Questions

1. Can Jev classify a known entity pair into a fixed relation schema?
2. Can local blocking retain the supported edges while avoiding all-pairs evaluation?
3. At a fixed probability/confidence threshold, what fraction of edges are proposed, sent to
   review, or rejected?
4. What are complete-case accuracy, latency, token use, and provider-reported cost?
5. How do generic chat models compare on contract completion, batch reliability, and orchestration
   cost when given the same candidate pairs?

## Tracks

- **Synthetic end to end:** repository-owned text, gazetteer entities, local candidate generation,
  keyword baseline, and optional Jev decisions.
- **FewRel direct closed set (v0.4.2):** the primary track above: supplied entity pair, one opaque
  case per request, 16 relations-only choices, temperature zero, 4,096 chat output tokens, and
  explicit `reasoning.effort=none` for chat models.
- **Chat-model comparison (v0.4.2):** the exact same FewRel sample, relation criteria, and opaque
  case ordering through Vercel AI Gateway to `openai/gpt-5.6-luna` and
  `deepseek/deepseek-v4.1-flash`. Chat models return only selected IDs; no self-reported
  probability is requested or compared with Jev probabilities.
- **FewRel episodic validation (v0.3 stress test):** deterministic 5-way or
  10-way, 1-shot or 5-shot episodes come from pinned public `val_wiki`. Relation and query IDs are
  opaque and support/query order is independently shuffled. This is official-shaped public
  validation, not the hidden official leaderboard.
- **Future end to end:** a separately licensed ontology-based KG construction corpus. Do not infer
  end-to-end quality from the FewRel track.

## Reporting rules

- Pin the dataset revision and verify its SHA-256 digest.
- Deterministically sample relations and examples with a recorded seed.
- Print the exact planned call count before a live run.
- No retries, concurrency, fallback model, or silent truncation.
- Failed and missing calls count against coverage; partial runs cannot be described as complete.
- `--continue-after-known-failure` may skip a failed episode without retrying it, but only when its
  receipt includes a known cost. Unknown-cost failures still stop the run.
- A manual continuation may start at a non-overlapping case offset and use a smaller batch after a
  failure. The merged artifact retains every failed receipt and reports the mixed batch plan.
- Provider probabilities are not calibrated correctness guarantees.
- Preserve source-specific license and citation information; downloaded data is gitignored.
- Compare direct models only with identical split, seed, 160-case ordering, relation descriptions,
  choice set, and request configuration. Compare episodic models only with identical episode count,
  ways, shots, and query count.
- Episodic requests batch every query in one prompt and must report
  `query_mode=batched_transductive`; query ordering cannot encode relation ordering.
- Non-overlapping episode continuations retain failed receipts and are merged by case/request ID.
- Chat baselines return relation IDs only. Do not compare their absent confidence values to Jev's
  probability output or interpret raw accuracy as probability calibration.
- Keep provider-reported billing separate from illustrative list-price equivalents. A `$0` Jev
  receipt describes current Gateway billing for that request, not a durable zero-cost claim.

## Live budget

The live runner requires `--approved-budget-usd` and refuses values above `$5.00`. It stops before
starting another request when the conservative reservation would exceed the remaining budget, and
also stops if accumulated provider-reported cost reaches the cap. Unknown cost stops the run.

Episodic summaries report `provider_reported_cost_usd` from receipts whose cost basis is the
Gateway, plus `illustrative_jev_list_price_equivalent_usd` computed from reported input tokens at
the checked `$0.042/M` Jev input price. The latter is a planning estimate, not an invoice.
