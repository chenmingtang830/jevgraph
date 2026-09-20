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
- hard live-run budget, call, request-size, timeout, and no-retry gates
- proposed/review/rejected edge states with probabilities and request receipts
- pinned FewRel 1.0 closed-set benchmark tooling
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

# Live Jev: explicit budget and artifact path required.
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

The default live batch size is eight. A 32-question pilot request returned HTTP 503 through the
Gateway, while the frozen eight-question batches completed reliably enough for the published pilot.
This is an observed operational default, not a provider throughput guarantee.

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

- Entity discovery is deliberately not solved in v0.1; the CLI accepts an explicit entity catalog.
- Candidate generation is same-sentence and English-oriented.
- FewRel contains positive labeled pairs and is not an end-to-end KG benchmark.
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
