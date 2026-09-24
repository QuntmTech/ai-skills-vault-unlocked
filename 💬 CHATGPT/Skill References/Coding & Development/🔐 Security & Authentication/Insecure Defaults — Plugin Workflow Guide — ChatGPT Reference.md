# ChatGPT reference — Insecure Defaults — Plugin Workflow Guide

Readable guidance, not a native skill installation. No live ChatGPT test is claimed. Supporting scripts and assets are not embedded in this document. Provider-specific commands may require adaptation; do not assume tools are available.

## Requirements to review

- Agent tools mentioned
- Executable code included; not executed or behavior-tested
- Third-party instructions and scripts: statically packaged, not executed or live-import tested.
- Plugin source: requires Workflow tool, plugin registration, filesystem access and agent support. ZIP upload alone does not activate the audit pipeline.
- Parallel-agent audit can be expensive; use only with an explicit target and usage budget.

[Preserved source and supporting files](../../../../%F0%9F%94%A7%20ADVANCED/skills/community/security/insecure-defaults/SKILL.md)

---

# Reference copy — insecure-defaults

This is a reading/copy-paste aid, not an installed skill. It does not include supporting files or grant access to tools. Review the ZIP and audit report before using this workflow.

---
name: insecure-defaults
description: Review requirements and use the preserved Trail of Bits insecure-defaults
  plugin workflow for auditing configuration security. Requires a compatible developer
  host and Workflow tool.
license: CC-BY-SA-4.0
disable-model-invocation: true
---

# Insecure defaults — plugin workflow guide

This vault-authored adapter preserves a plugin, not a standalone executable Claude-app skill. Read [the upstream README](README.md) and [the upstream audit command](commands/audit.md). The detection corpus, workflow and plugin manifest are included unchanged.

Before execution, verify that the host supports the plugin's Workflow tool, plugin registration, filesystem access and required agent models. A ZIP upload alone does not register the workflow. If any capability is missing, explain the setup requirement and stop; do not simulate a successful audit.

Use the upstream audit command after compatible plugin installation; do not invoke its pipeline directly. This can spawn multiple agents and consume substantial usage. Obtain the user's audit scope before running. No runtime validation has been performed by this vault.
