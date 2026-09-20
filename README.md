# JevGraph

**Build evidence-backed candidate knowledge graphs with typed relation decisions.**

JevGraph is an open-source experiment in replacing open-ended “prompt → triples” extraction with a
bounded pipeline:

```text
documents → entity mentions → local candidate blocking → Jev relation choices
          → deterministic schema checks → proposed / review / rejected edges
```

It is designed for fixed or slowly changing ontologies where edge precision, source evidence, and
reproducibility matter. It does **not** claim that model output is true, approved, or safe for
consequential reuse.

## Why

Testing every pair among `n` entities is `O(n²)`. JevGraph first keeps only nearby pairs that satisfy
ontology type constraints, producing at most `O(nk)` model candidates for a configured local
neighbor bound `k`. Jev then evaluates closed-set `Choice` questions over those candidates. The
asymptotic reduction comes from blocking; Jev reduces decision cost and makes outputs easier to
validate.

## What is included

- YAML relation ontologies with domain/range constraints
- exact gazetteer mentions and character-level evidence spans
- bounded same-sentence candidate generation
- a transparent local keyword baseline
- a Vercel AI Gateway adapter for `typesafe-ai/jev`
- benchmark-only Vercel Gateway comparators for GPT-5.6 Luna and DeepSeek V4.1 Flash
- hard live-run budget, call, request-size, timeout, and no-retry gates
- proposed/review/rejected edge states with probabilities and request receipts
- pinned FewRel 1.0 closed-set benchmark tooling
- official-compatible FewRel 1.0 episodic validation for Jev, GPT-5.6 Luna, and DeepSeek V4.1 Flash
- JSON, CSV, and Neo4j Cypher outputs
- offline tests and GitHub Actions CI

## Quickstart

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/chenmingtang830/jevgraph.git
cd jevgraph
uv sync --all-extras --dev

uv run jevgraph build examples/company_events.txt \
  --ontology examples/ontology.yml \
  --entities examples/entities.yml \
  --provider keyword \
  --out runs/demo.json

uv run jevgraph export runs/demo.json --format csv --out runs/demo-csv
uv run jevgraph export runs/demo.json --format neo4j --out runs/demo.cypher
```

The keyword provider is a labeled deterministic demo baseline. It is not presented as a general
relation extractor.

## Live Jev run

JevGraph currently supports Jev through the Vercel AI Gateway evaluation-model protocol. A live run
requires both a key and an explicit budget:

```bash
export AI_GATEWAY_API_KEY="..."

uv run jevgraph build examples/company_events.txt \
  --ontology examples/ontology.yml \
  --entities examples/entities.yml \
  --provider jev \
  --batch-size 8 \
  --approved-budget-usd 0.05 \
  --call-ceiling 2 \
  --out runs/demo-jev.json
```

The runner uses a fixed upstream host and model, never retries, never falls back, refuses redirects,
bounds request/response sizes, and stops on unknown cost. Keys and headers are never exported.
Provider list prices, rate limits, aliases, and behavior can change; check the current
[TypeSafe model documentation](https://docs.typesafe.ai/models) and
[Vercel AI Gateway documentation](https://vercel.com/docs/ai-gateway) before relying on old results.
Published results therefore separate the Gateway's provider-reported charge from an illustrative
Jev list-price equivalent computed from reported input tokens.

## FewRel experiment

FewRel supplies sentences, entity pairs, and Wikidata-property labels, so this track isolates
closed-set relation classification. It does not measure entity extraction, candidate recall,
negative-edge rejection, or end-to-end graph quality.

```bash
uv run jevgraph fetch-fewrel --data-dir data/fewrel

# Exact request/case plan; no provider call.
uv run jevgraph benchmark \
  --data-dir data/fewrel \
  --provider plan \
  --relations 8 \
  --examples-per-relation 4 \
  --seed 7

# Free local baseline.
uv run jevgraph benchmark \
  --data-dir data/fewrel \
  --provider lexical \
  --relations 8 \
  --examples-per-relation 4 \
  --seed 7 \
  --out runs/fewrel-lexical.json

# Live model: explicit budget and artifact path required.
uv run jevgraph benchmark \
  --data-dir data/fewrel \
  --provider jev \
  --batch-size 8 \
  --relations 8 \
  --examples-per-relation 4 \
  --seed 7 \
  --approved-budget-usd 1.00 \
  --call-ceiling 4 \
  --out runs/fewrel-jev.json

# The same closed-set cases through a generic chat-model contract.
uv run jevgraph benchmark \
  --data-dir data/fewrel \
  --provider gpt-5.6-luna \
  --batch-size 8 \
  --relations 8 \
  --examples-per-relation 4 \
  --seed 7 \
  --approved-budget-usd 1.00 \
  --call-ceiling 4 \
  --out runs/fewrel-luna.json
```

Use `--case-offset` and `--case-limit` to create a separately recorded diagnostic slice without
silently retrying or overwriting a failed run.

Non-overlapping continuation shards can be merged while retaining failed request receipts:

```bash
uv run jevgraph merge-benchmarks runs/partial.json runs/continuation.json \
  --expected-cases 160 \
  --out runs/merged.json
```

The downloader pins FewRel commit `278a2315d2138810a379cd8d5718914dc56e2582` and verifies SHA-256
digests. Downloaded data and detailed run artifacts are gitignored. See [the experiment
protocol](docs/EXPERIMENTS.md) and [current results](docs/RESULTS.md).

The default live batch size is eight. It is an observed Jev operating point, not a provider
throughput guarantee. The generic chat comparators are benchmark-only: they return relation IDs,
not Jev's probability distribution or confidence. The published DeepSeek run had to continue with
smaller batches after truncated completions; see the results rather than assuming batch parity.

### Track 2: FewRel episodic validation

This track builds on the published Track 1 closed-set comparison above. It mirrors FewRel's public
N-way K-shot task shape on `val_wiki`: each
episode samples 5 or 10 relations, supplies 1 or 5 labeled support examples per relation, and asks
the model to classify held-out queries for supplied entity pairs. Relation and query IDs are opaque,
and support/query order is independently shuffled. It supports Jev, GPT-5.6 Luna, and DeepSeek
V4.1 Flash through the same budgeted Gateway clients used in Track 1.

```bash
# Default is a deterministic, no-call plan.
uv run jevgraph benchmark-official \
  --data-dir data/fewrel \
  --model gpt-5.6-luna \
  --ways 5 \
  --shots 1 \
  --queries-per-relation 1 \
  --episodes 100 \
  --seed 17

# Live execution must be explicit and bounded.
uv run jevgraph benchmark-official \
  --data-dir data/fewrel \
  --model deepseek-v4.1-flash \
  --ways 5 \
  --shots 1 \
  --queries-per-relation 1 \
  --episodes 100 \
  --seed 17 \
  --execute \
  --approved-budget-usd 1.00 \
  --call-ceiling 100 \
  --out runs/fewrel-official-deepseek.json
```

Use the same episode parameters and seed for every compared model. This is an
**official-compatible validation track**, not an official hidden-test leaderboard submission:
FewRel does not publish its test examples, and the official reference evaluates 10,000 hidden-test
episodes. Queries are evaluated together in one prompt per episode. Their order is shuffled and the
prompt requires independent judgments, but a general LLM can still inspect other queries; results
therefore report `query_mode=batched_transductive`. The validation runner also does not test entity
discovery or candidate-pair generation.

The published 100-episode, 500-query run found 85.6% planned-case accuracy for Jev, 98.0% for
GPT-5.6 Luna, and 85.0% for DeepSeek V4.1 Flash after counting its 14 failed episodes against the
frozen denominator. Jev completed every episode with 368 ms p50 request latency; DeepSeek reached
98.84% on completed queries but only 86% coverage. See [the full results](docs/RESULTS.md) for cost,
failure, gating, and canary details.

Use `--episode-offset` and `--episode-limit` for a non-overlapping continuation after a failed
episode. Merge shards while retaining every failed receipt:

```bash
uv run jevgraph merge-episodic runs/partial.json runs/continuation.json \
  --expected-episodes 100 \
  --out runs/merged.json
```

For a long diagnostic run, `--continue-after-known-failure` records a failed episode and proceeds
to the next one only when the receipt includes a known cost. It never retries the episode, changes
models, or continues after an unknown-cost failure.

## Output contract

Each candidate records:

- canonical source and target entities
- the exact copied evidence window and character offsets
- the ontology relations allowed for that directed type pair
- selected relation, full probabilities, confidence, model, and request ID
- `proposed`, `review`, or `rejected` status plus a machine-readable reason

`proposed` means only that configured gates passed. Human or application authorization is outside
this project.

## Scope and limitations

- Entity discovery is deliberately not solved in v0.3; the CLI accepts an explicit entity catalog.
- Candidate generation is same-sentence and English-oriented.
- FewRel contains positive labeled pairs and is not an end-to-end KG benchmark.
- Public `val_wiki` episodic results are not official hidden-test leaderboard results. General LLMs
  may also have encountered FewRel-derived material during pretraining.
- The current model step only classifies an already supplied candidate pair into a fixed relation
  schema plus `none` / `insufficient_evidence`. It does not discover entities, invent relations,
  resolve coreference, or perform graph completion.
- Jev works best with compact relevant state, literal instructions, and bounded answers. Long,
  adversarial, multilingual, numeric, temporal, and multi-hop cases need separate evaluation.
- Provider probabilities and confidence are model outputs, not proof of calibration or correctness.

## Development

```bash
uv run ruff check .
uv run pytest
```

Architecture and safety boundaries are documented in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
Contributions are welcome through issues and pull requests.

## Dataset attribution

FewRel is maintained by THUNLP and described in *FewRel: A Large-Scale Supervised Few-Shot
Relation Classification Dataset with State-of-the-Art Evaluation* (Han et al., EMNLP 2018).
JevGraph does not redistribute the dataset; the pinned downloader retrieves it from the upstream
[FewRel repository](https://github.com/thunlp/FewRel).

## License

JevGraph code is licensed under Apache-2.0. External datasets and provider services retain their
own terms. JevGraph is an independent community project and is not affiliated with or endorsed by
TypeSafe AI, Vercel, THUNLP, or the model providers.
