# PROJECT COMPASS

General-purpose instructions for reliable AI project work.

## The easiest way to use it

1. Copy [PROJECT-INSTRUCTIONS.md](PROJECT-INSTRUCTIONS.md) into your project's
   instruction area, where your AI product supports one.
2. Attach [PROJECT-HANDBOOK.md](PROJECT-HANDBOOK.md) as reference knowledge.
3. Optionally fill in [PROJECT-CONTEXT.template.md](PROJECT-CONTEXT.template.md)
   **privately**, with only the context that project needs.

Prefer one file? Use [COPY-PASTE-ALL.md](COPY-PASTE-ALL.md), which combines the
instructions and handbook. Do not load both the combined file and separate
versions: that repeats instructions and wastes context.

The compilation covers engineering, research, design, writing, business
decisions and technical operations. Use only sections relevant to the task.
No particular vendor, operating system, business model or personal profile
is assumed.

## What this is—and is not

This is project guidance, **not a native skill ZIP or plugin**. Product-specific
file limits, instruction fields, persistence and tool access differ. An
attachment alone does not grant permissions or guarantee it will be consulted.
Tell the assistant which file to use and verify a small task first.

For repository use, adapt the short instructions to the host's supported rules
file; merge with existing rules rather than replacing them blindly. Keep the
handbook available as a reference, not an always-loaded wall of text.

## Private setup

Do not fill public templates with real account names, credentials, customer
records, private links or production details. Keep filled-in context outside
this repository. Use environment variables or the platform's secret manager
for secrets, never project instructions.

See [CURATION-NOTES.md](CURATION-NOTES.md) for scope and omissions, and
[QUALITY-CHECKS.md](QUALITY-CHECKS.md) for realistic test scenarios.

## Rebuild and check the download

From the repository root:

```bash
python3 scripts/build_instruction_pack.py
python3 scripts/build_instruction_pack.py --check
python3 scripts/build_instruction_pack.py --zip
```

The ZIP in `dist/` is a document bundle for extraction—not a one-click
installation. It contains only the six compilation documents plus the combined copy,
not the source instruction library or any filled-in private context.
