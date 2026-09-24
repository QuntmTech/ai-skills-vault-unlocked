---
name: insecure-defaults
description: Review requirements and use the preserved Trail of Bits insecure-defaults plugin workflow for auditing configuration security. Requires a compatible developer host and Workflow tool.
license: CC-BY-SA-4.0
disable-model-invocation: true
---

# Insecure defaults — plugin workflow guide

This vault-authored adapter preserves a plugin, not a standalone executable Claude-app skill. Read [the upstream README](README.md) and [the upstream audit command](commands/audit.md). The detection corpus, workflow and plugin manifest are included unchanged.

Before execution, verify that the host supports the plugin's Workflow tool, plugin registration, filesystem access and required agent models. A ZIP upload alone does not register the workflow. If any capability is missing, explain the setup requirement and stop; do not simulate a successful audit.

Use the upstream audit command after compatible plugin installation; do not invoke its pipeline directly. This can spawn multiple agents and consume substantial usage. Obtain the user's audit scope before running. No runtime validation has been performed by this vault.
