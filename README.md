# QUNTM SKILLVERSE

### Find a skill. Pick your AI. Get to work.

A searchable library of AI skills and workflows with individual ZIP exports,
whole-package duplicate detection, and visible compatibility warnings.

**Local preview · Not published · Redistribution review required**

## Start here

Double-click [the searchable catalog](catalog/index.html). It works offline:
no server, account, analytics or external scripts.
Prefer text? Open the [Markdown catalog](catalog/skills-catalog.md).

### General project instructions

Use [PROJECT COMPASS](project-instructions/README.md) for a concise, generalized
project-instruction system: a short core, a deeper handbook, a private context
template and a [single copy/paste version](project-instructions/COPY-PASTE-ALL.md).
It is a document pack, not another skill, and contains no imported private profiles.

## What is inside?

- **925 source entries:** 839 skill copies and 86 Claude commands.
- **571 distinct package contents**, compared using filenames and every included file.
- All 894 original entries, plus 31 previously unlisted nested skill variants.
- Supporting scripts, references, templates, assets and existing notices retained.

These counts are not a claim of 925 unique, original or universally compatible
skills. Some require particular plugins, MCP connections, accounts or local tools.

## Export your first skill

Requires Python 3.10+. Run from this repository folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
python3 scripts/skillverse.py search frontend-design
python3 scripts/skillverse.py show 91
python3 scripts/skillverse.py export 91 --target claude
```

Open `dist/`: you get one skill ZIP, a readable reference copy and a JSON
report. Originals are never edited; existing exports are never overwritten.
Use `--out dist/second-export` for another copy.

For Codex or another compatible host, use `--target portable`, extract the ZIP,
and review the complete folder before installing.

**Do not upload the whole repository as one skill.**
Read the [Claude / ChatGPT / Codex guide](docs/INSTALLATION.md).

## Why SKILLVERSE?

Find a useful workflow without dumping hundreds of skills into an agent.
Compare variants, retain the resources that make them work, and see unresolved
requirements before installation. No star-count promises or implied endorsement
by OpenAI, Anthropic, CC Switch or upstream authors.

## Layout

```text
catalog/       Offline searchable browser + Markdown index
skills/        Preserved skills grouped by original collection
commands/      Claude commands, kept separate from skills
metadata/      Content hashes, duplicates and review reports
scripts/       Search, inspect, export and validate
tests/         Export and preservation regression tests
docs/          Setup, architecture and publishing gates
project-instructions/  General-purpose PROJECT COMPASS compilation
dist/          Personal exports; ignored by Git
```

## Publication status

The tooling is a local preparation package, not a cleared public release.
Third-party licenses and credits remain intact, but license presence alone
does not prove redistribution rights. No blanket license applies to this vault.

Read [readiness](docs/READINESS.md), [license notice](LICENSE.md), and
[publishing gates](docs/PUBLISHING-CHECKLIST.md). No GitHub repository has been
created or pushed by this preparation.

## Contributor checks

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_repository.py
python3 scripts/build_repository.py --check
python3 scripts/audit_exports.py --check
git diff --check
```

Do not execute collected skill scripts to validate this repository.
See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
