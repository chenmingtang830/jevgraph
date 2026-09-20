# Architecture

JevGraph treats graph construction as a bounded decision pipeline, not open-ended triple
generation.

```text
documents
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

## Provider contract

The Jev adapter uses Vercel AI Gateway's evaluation-model protocol. Each candidate is one `Choice`
question over ontology relations allowed by the source/target types, plus `none` and
`insufficient_evidence`. Requests are size-bounded, sequential, and never retried. A run requires
both a configured key and an explicit dollar budget.
