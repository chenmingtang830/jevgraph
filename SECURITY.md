# Security policy

## Supported versions

JevGraph is experimental. Security fixes target the latest tagged release.

## Report a vulnerability

Please use GitHub's private vulnerability reporting for this repository. Do not open a public issue
containing credentials, private documents, or exploitable details.

## Credential and data boundaries

- Supply `AI_GATEWAY_API_KEY` through the environment only.
- Never commit `.env` files or put keys in CLI arguments, URLs, graph outputs, or receipts.
- Live requests send candidate evidence to Vercel AI Gateway and the selected upstream provider.
- A local run does not guarantee that upstream computation or billing stops when the process exits.
- Use synthetic or approved data, provider-side spend controls, and a narrowly scoped key.

