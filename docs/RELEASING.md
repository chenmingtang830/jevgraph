# Releasing JevGraph

Releases are evidence-bearing artifacts. A tag is ready only after the following checks pass.

## Before tagging

1. Update the version in `pyproject.toml` and `CITATION.cff`; they must match.
2. Rebuild generated reports from committed aggregate evidence.
3. Confirm every benchmark claim states its task boundary, coverage, failure handling, and cost
   basis.
4. Run the full local gate:

   ```bash
   uv sync --all-extras --dev
   uv run ruff check .
   uv run pytest
   uv build
   ```

5. Inspect the wheel and source archive. They must not contain credentials, `.env` files,
   downloaded datasets, FewRel sentences, raw prompts, HTTP headers, or detailed private receipts.
6. Confirm `NOTICE`, `ACKNOWLEDGEMENTS.md`, `CITATION.cff`, and third-party license notes still match
   the bundled and optional dependencies.
7. Merge through a protected pull request with all required checks and conversations resolved.

## Publish

Create an annotated version tag that exactly matches the package version:

```bash
git tag -a v0.5.1 -m "JevGraph v0.5.1"
git push origin v0.5.1
```

The `Release` workflow re-runs lint and tests, verifies the tag/version match, builds the wheel and
source archive in a clean runner, lists their contents, generates `SHA256SUMS`, creates build
provenance attestations, and uploads the artifacts to a GitHub release.

## After publishing

- Download the release assets and verify the checksum manifest.
- Install the wheel into a clean environment and run `jevgraph --help`.
- Confirm the release notes link the exact evidence and interactive report used for public claims.
- Never replace a benchmark artifact silently. Publish a new version and keep the prior evidence
  available with its supersession note.
