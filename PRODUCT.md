# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Developers and evaluation-minded teams building knowledge graphs from documents under a fixed or
slowly changing relation ontology. They need to understand what the pipeline measures, where model
judgment enters, and which evidence supports its operational claims.

## Product Purpose

JevGraph is an open-source, schema-guided document-to-candidate-graph pipeline. It turns locally
parsed documents into bounded candidate relation decisions with source evidence, deterministic
checks, explicit edge states, and retained provider receipts.

## Positioning

JevGraph does not ask a model to invent an unconstrained graph. Local mention extraction,
ontology-aware blocking, and deterministic validation narrow the model's job to typed relation
selection over auditable candidate pairs.

## Operating Context

Inputs are text, PDF, DOCX, or PPTX documents plus a relation ontology and entity catalog. Local
DocJev + LiteParse ingestion preserves canonical page mapping; Jev or a benchmark comparator makes
relation decisions through Vercel AI Gateway; outputs include JSON, CSV, or Neo4j Cypher.

## Capabilities and Constraints

- Candidate blocking reduces potential pair evaluation from all-pairs `O(n²)` toward bounded
  `O(nk)` work for configured neighbor bound `k`.
- Provider choices remain candidate decisions, not graph truth or Human Approval.
- The public FewRel comparison isolates relation identification for supplied entity pairs.
- The configured E2E benchmark is a repository-owned smoke/regression fixture, not external proof
  of general graph quality.
- Cost evidence keeps provider receipts separate from illustrative list-price equivalents.

## Brand Commitments

The public report uses Proofpress Boardroom Clarity: institutional white and warm paper, near-black
ink, fine rules, restrained teal, and compact evidence metadata.

## Evidence on Hand

- `benchmarks/company-events-v1.json`: digest-pinned configured E2E smoke fixture.
- `docs/evidence/direct-reasoning-none-2026-09-20.json`: controlled 160-case FewRel comparison.
- DocJev `real-small-v1-run01`: published 40-document / eight-packet classification and splitting
  pilot used as external document-layer context.

## Product Principles

- Bound model work before optimizing it.
- Preserve failures and cost basis as evidence.
- Keep candidate decisions separate from accepted graph truth.
- Prefer reproducible, inspectable stages over open-ended triple generation.
