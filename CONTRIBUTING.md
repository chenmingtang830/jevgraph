# Contributing

Issues and pull requests are welcome.

## Development

```bash
uv sync --all-extras --dev
uv run ruff check .
uv run pytest
uv build
```

Provider tests must use synthetic mocked responses and must not spend credits. Do not commit
credentials, downloaded datasets, detailed live-run payloads, or source text from third-party
benchmarks.

## Evidence states

- Local fixtures and keyword results are implementation checks, not model evidence.
- A live canary validates transport and response handling only.
- Benchmark claims require a pinned dataset, deterministic sampling parameters, complete-case
  coverage, failures, latency conditions, usage, and cost basis.
- A `proposed` graph edge is still a candidate. Do not relabel it verified or approved.

## Changes

Keep candidate generation, provider decisions, deterministic checks, and downstream authorization
separate. Add or update tests for contract changes. New datasets need a pinned revision, integrity
digest, source link, license note, and citation.

