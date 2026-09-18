# ChatGPT reference — Eve

Readable guidance, not a native skill installation. No live ChatGPT test is claimed. Supporting scripts and assets are not embedded in this document. Provider-specific commands may require adaptation; do not assume tools are available.

## Requirements to review

- Claude upload description will be shortened; full text retained
- MCP/tool connection mentioned
- Agent tools mentioned
- Plugin source — verify required plugin capabilities in Claude
- External tools or services mentioned — review availability

[Preserved source and supporting files](../../../%F0%9F%94%A7%20ADVANCED/skills/claude/plugins/vercel%20%E2%80%94%20eve%20%E2%80%94%20Copy%202/SKILL.md)

---

# Reference copy — eve

This is a reading/copy-paste aid, not an installed skill. It does not include supporting files or grant access to tools. Review the ZIP and audit report before using this workflow.

---
name: eve
description: Build durable backend AI agents with the eve framework. Use when creating,
  editing, or debugging an eve project — agent instructions, skills, tools, connections,
  channels, sandboxes, subagents,...
---
## Full original description

Build durable backend AI agents with the eve framework. Use when creating, editing, or debugging an eve project — agent instructions, skills, tools, connections, channels, sandboxes, subagents, schedules, or evals.


# eve

eve is a filesystem-first framework for durable backend AI agents. An agent is
a directory on disk — instructions, skills, tools, connections, channels,
subagents, and schedules are all files — and eve compiles and runs it.

## Vercel Agent Runs

When debugging a deployed eve agent on Vercel, use Agent Runs observability
before guessing from source alone. Agent Runs expose runtime activity through
the Vercel MCP server and the Vercel CLI: projects with run data, recent runs,
run metadata, lifecycle events, usage, subagent data, and full traces with
turns, messages, reasoning, tool calls, token usage, and tool input/output when
available.

To inspect runs through Vercel MCP, list the available Vercel MCP tools and
use the Agent Runs tools exposed by the server. Tool names and schemas can
change, so inspect the tool list/schema before hard-coding a name from memory.

For CLI usage, ask the installed CLI for the current Agent Runs surface:

```bash
vercel agent-runs --help
vercel agent-runs <subcommand> --help
```

Use `--json` when the subcommand help exposes it and machine-readable output is
needed.

If `vercel agent-runs` is missing, check `vercel --version` and upgrade first:

```bash
npm i -g vercel@latest
vercel agent-runs --help
```

## Source of truth

The complete documentation ships inside the `eve` package. Do not rely on this
skill for guidance — always read the bundled docs, which match the installed
version exactly:

```
node_modules/eve/docs/
```

Start with `node_modules/eve/docs/README.md`. It contains the full
index and recommended reading order. Before writing any eve code, read the
relevant guide there first.

If `eve` is not installed yet, install it (`npm install eve`) or scaffold a new
agent with `npx eve init <agent-name>`, then read the bundled docs.
