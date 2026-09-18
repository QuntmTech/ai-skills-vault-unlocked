# ChatGPT reference — Stripe Docs

Readable guidance, not a native skill installation. No live ChatGPT test is claimed. Supporting scripts and assets are not embedded in this document. Provider-specific commands may require adaptation; do not assume tools are available.

## Requirements to review

- Agent tools mentioned
- Plugin source — verify required plugin capabilities in Claude
- External tools or services mentioned — review availability

[Preserved source and supporting files](../../../%F0%9F%94%A7%20ADVANCED/skills/codex/plugins/stripe%20%E2%80%94%20stripe-docs/SKILL.md)

---

# Reference copy — stripe-docs

This is a reading/copy-paste aid, not an installed skill. It does not include supporting files or grant access to tools. Review the ZIP and audit report before using this workflow.

---
name: stripe-docs
description: Use when the user or agent needs to read, search, or look up Stripe documentation
  or API reference. Prefer this over curl or WebFetch for any docs.stripe.com content.
metadata:
  short-description: Read and search Stripe documentation from the terminal
allowed-tools:
- Bash(stripe docs *)
---

Use `stripe docs` instead of fetching [docs.stripe.com](https://docs.stripe.com/.md) content directly with `curl` or `WebFetch`.

- Fetches Markdown automatically
- Purpose-built for agents and terminal workflows

## Read a page by its web path

```bash
stripe docs /payments
```

## Search documentation by keyword

```bash
stripe docs search "payment intents"
```

## Look up API reference

```bash
# By resource name
stripe docs api product

# By HTTP method and path
stripe docs api GET /v1/products

# By event type
stripe docs api product.created
```
