# How the vault works

## What is a skill?

A skill is a directory centered on a `SKILL.md` file. The file explains when an
AI agent should use the skill and how to perform the workflow. A skill may also
include scripts, templates, examples, references, or assets.

Slash commands are stored separately under `commands/claude/` because they are
invoked differently from skills.

## Why are there multiple copies of some skills?

The vault preserves provider-specific and versioned copies. A Codex plugin copy
may differ from a Claude plugin copy even when their visible names match. The
curated catalog de-duplicates the browsing experience without deleting those
source variants.

## How the catalog is built

`metadata/catalog.json` contains the curated 894-entry catalog using only
repository-relative paths. `scripts/build_repository.py` uses it to generate:

- `catalog/skills-catalog.md`
- `metadata/inventory.json`
- `metadata/license-audit.json`

The inventory hashes every skill and command file so maintainers can detect
changes without executing any collected content.

## Trust model

The repository is a library, not an active installation directory. Downloading
it does not automatically enable every skill. Users choose individual skills,
review their contents, and copy them into the location supported by their AI
tool.

