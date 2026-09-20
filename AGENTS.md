# Contributor guide

JevGraph constructs candidate knowledge graphs. It does not treat model output as truth.

- Preserve source spans, model identity, probabilities, and request receipts.
- Keep candidate generation, model decisions, deterministic validation, and human review distinct.
- Live provider calls must require an explicit budget, call ceiling, and credential source.
- Never add retries or fallback providers to benchmark runs.
- Never commit provider credentials, downloaded datasets, or run artifacts containing source text.
- Pin external datasets by commit and digest; preserve their license and citation requirements.
- Run `uv run ruff check .` and `uv run pytest` before committing.

