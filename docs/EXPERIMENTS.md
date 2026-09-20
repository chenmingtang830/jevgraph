# Experiment protocol

## Questions

1. Can Jev classify a known entity pair into a fixed relation schema?
2. Can local blocking retain the supported edges while avoiding all-pairs evaluation?
3. At a fixed probability/confidence threshold, what fraction of edges are proposed, sent to
   review, or rejected?
4. What are complete-case accuracy, latency, token use, and provider-reported cost?

## Tracks

- **Synthetic end to end:** repository-owned text, gazetteer entities, local candidate generation,
  keyword baseline, and optional Jev decisions.
- **FewRel closed set:** externally downloaded FewRel 1.0 examples with supplied entity pairs. This
  isolates relation classification; it does not test entity discovery or negative-edge rejection.
- **Future end to end:** a separately licensed ontology-based KG construction corpus. Do not infer
  end-to-end quality from the FewRel track.

## Reporting rules

- Pin the dataset revision and verify its SHA-256 digest.
- Deterministically sample relations and examples with a recorded seed.
- Print the exact planned call count before a live run.
- No retries, concurrency, fallback model, or silent truncation.
- Failed and missing calls count against coverage; partial runs cannot be described as complete.
- Provider probabilities are not calibrated correctness guarantees.
- Preserve source-specific license and citation information; downloaded data is gitignored.

## Live budget

The live runner requires `--approved-budget-usd` and refuses values above `$5.00`. It stops before
starting another request when the conservative reservation would exceed the remaining budget, and
also stops if accumulated provider-reported cost reaches the cap. Unknown cost stops the run.

