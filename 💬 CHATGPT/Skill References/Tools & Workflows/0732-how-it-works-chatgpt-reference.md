# ChatGPT reference — How It Works

Readable guidance, not a native skill installation. No live ChatGPT test is claimed. Supporting scripts and assets are not embedded in this document. Provider-specific commands may require adaptation; do not assume tools are available.

## Requirements to review

- Host-specific paths mentioned
- Agent tools mentioned
- Plugin source — verify required plugin capabilities in Claude

[Preserved source and supporting files](../../../%F0%9F%94%A7%20ADVANCED/skills/claude/plugins/claude-mem%20%E2%80%94%20how-it-works/SKILL.md)

---

# Reference copy — how-it-works

This is a reading/copy-paste aid, not an installed skill. It does not include supporting files or grant access to tools. Review the ZIP and audit report before using this workflow.

---
name: how-it-works
description: Explain how claude-mem captures observations, when memory injection kicks
  in, and where data lives. Use when the user asks "how does claude-mem work?" or
  "what is this thing doing?".
---

# How claude-mem works

## What it does

Every Read, Edit, and Bash that Claude makes turns into a compressed observation. Observations get summarized at session end. Relevant ones get auto-injected into future prompts so the next session starts with context from the last one — no re-explaining the codebase, no re-discovering decisions.

## When it kicks in

Memory injection starts on your second session in a project.

The first session in a fresh project seeds memory; subsequent sessions receive auto-injected context for relevant past work. Run `/learn-codebase` if you want to front-load the entire repo into memory in a single pass (~5 minutes, optional).

## Where data lives

Everything stays in ~/.claude-mem on this machine.

Nothing leaves your machine except calls to whichever AI provider you configured for compression (Claude / OpenRouter / Gemini). The SQLite database, vector index, logs, and settings all live under that directory and are removed cleanly on `npx claude-mem uninstall`.
