## Summary

<!-- What changed and why? -->

## Verification

- [ ] `uv run ruff check .`
- [ ] `uv run pytest`
- [ ] `uv build` when packaging or dependency metadata changed
- [ ] Generated reports and evidence artifacts were rebuilt when their sources changed

## Publication safety

- [ ] No credentials, private documents, licensed benchmark text, prompts, or HTTP headers are included
- [ ] New claims link to committed evidence and state their measurement boundary
- [ ] Third-party datasets, code, and benchmarks retain their license, citation, and credit
- [ ] Model outputs remain labeled as candidate decisions rather than graph truth or Human Approval
