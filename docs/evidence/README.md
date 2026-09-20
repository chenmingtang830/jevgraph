# Experiment evidence

Aggregate evidence is committed here. Detailed benchmark artifacts may be published as release
assets when they contain only case IDs, predictions, sanitized request receipts, request hashes,
usage, latency, cost, and failure status.

Never publish provider credentials, authorization headers, raw prompts, FewRel sentences, or graph
demo runs that embed source documents. Failed requests are evidence and must remain in any merged
or released artifact rather than being silently retried or discarded.

Billing evidence must retain its basis. In particular, preserve Jev's provider-reported `$0`
separately from the input-token list-price equivalent used for forward cost planning.

The v0.3 release evidence bundle contains aggregate records plus sanitized Track 1 and Track 2 raw
run JSON. The raw files contain only IDs, predictions, receipts, hashes, usage, latency, cost, and
failure state. A SHA-256 manifest covers every bundled file. FewRel data itself is not redistributed;
obtain it from the pinned upstream revision using `jevgraph fetch-fewrel` and observe its license.
