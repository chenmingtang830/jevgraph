# Architecture

JevGraph treats graph construction as a bounded decision pipeline, not open-ended triple
generation.

```text
PDF / DOCX / PPTX / text
  -> local DocJev/LiteParse ingestion (document formats)
  -> canonical hashes, ordered page text, and source map
  -> exact entity mentions
  -> typed candidate blocking
  -> minimal evidence windows
  -> closed-set relation decisions
  -> deterministic schema checks
  -> proposed / review / rejected edges
  -> JSON graph and CSV/Neo4j exports
```

## Complexity

Naively testing every entity pair is quadratic. JevGraph only creates pairs that share a bounded
evidence window and satisfy at least one ontology domain/range rule. With at most `k` local
neighbors per entity, model work is proportional to `O(nk)` candidate edges rather than all
`O(n^2)` pairs. Jev lowers the constant further by evaluating many typed questions against one
shared state.

## Authority boundary

A provider result is a typed recommendation. `proposed` means that the selected relation passed
configured probability, confidence, and schema checks; it does not mean the relation is true or
approved for consequential reuse. `review` preserves uncertain and insufficient-evidence results.
`rejected` preserves explicit `none` outcomes. Downstream systems decide who may approve a
candidate graph.

## Evidence and reproducibility

Every candidate records exact character offsets and the copied source window. Every decision
references a sanitized request receipt containing provider, requested and resolved model, usage,
latency, cost, and a request hash. Credentials and authorization headers are never exported.
When a provider rounds a large probability distribution, JevGraph accepts totals only within
`[0.95, 1.05]`, renormalizes them, and records the number of affected answers in the receipt.

For PDF, DOCX, and PPTX, the optional document adapter pins DocJev revision
`9ed0fe05984ce1906af9272b8b400c8d46520f98` and uses its local LiteParse path only. JevGraph
stores source and canonical hashes, parser metadata, ordered canonical page spans, and the overlap
between each evidence window and page-local OCR offsets. Separator characters inserted between
pages are deliberately not attributed to a source page. This is page-level text provenance, not a
PDF bounding-box claim.

## Provider contract

The Jev adapter uses Vercel AI Gateway's evaluation-model protocol. Each candidate is one `Choice`
question over ontology relations allowed by the source/target types, plus `none` and
`insufficient_evidence`. Requests are size-bounded, sequential, and never retried. A run requires
both a configured key and an explicit dollar budget.

The default live batch size is eight. It is based on the v0.1 pilot's observed Gateway behavior and
does not claim a provider-side concurrency guarantee.

The GPT-5.6 Luna and DeepSeek V4.1 Flash adapters exist only in the FewRel benchmark runner. They
receive the same relation schema and supplied entity pairs, use temperature zero, and must return
one relation ID per case in a strict JSON map. They do not emit probabilities, cannot pass the
graph builder's probability/confidence gates, and are not silently substituted for Jev.

## What the model does—and does not do

The model sees only candidates created upstream. For the end-to-end demo, exact gazetteer matching
creates mentions and deterministic same-sentence/type blocking creates candidate pairs. For the
FewRel track, the dataset supplies the entity pair directly. The provider selects a relation for
each pair. It does not perform open-ended entity discovery, pair discovery, ontology induction,
coreference resolution, graph completion, approval, or truth determination.

## End-to-end boundary

JevGraph's open-source E2E contract is schema-guided: one supported source document plus a declared
ontology and entity catalog produces a complete candidate-graph artifact. Document parsing and
candidate construction are local. Selecting the keyword provider keeps the entire run offline;
selecting Jev adds the existing explicit budget/call gates. Multi-document packet splitting,
open-ended entity discovery, entity resolution, and human approval are not silently inferred.
