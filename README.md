# Limitless AI Skills Vault

A public-ready library of reusable AI-agent skills and slash commands collected
from Codex, Claude Code, CC Switch, and installed plugin ecosystems.

The repository contains **894 curated catalog entries**: 808 skills and 86
commands. The physical archive contains additional versioned and plugin copies,
so the raw `SKILL.md` count is higher than the curated catalog count.

## Start here

1. Browse [`catalog/skills-catalog.md`](catalog/skills-catalog.md).
2. Open the linked `SKILL.md` or command file and review it.
3. Copy the complete skill directory into your agent's supported skills folder.
4. Restart or reload the agent if it does not discover new skills automatically.

See [`docs/HOW-IT-WORKS.md`](docs/HOW-IT-WORKS.md) and
[`docs/INSTALLATION.md`](docs/INSTALLATION.md) for detailed instructions.

## Repository layout

```text
catalog/                 Human-readable catalog
skills/
  cc-switch/             CC Switch managed and community skills
  codex/                 Codex system, local, agent, and plugin skills
  claude/                Claude global and plugin skills
commands/claude/         Claude global and plugin slash commands
metadata/                Machine-readable catalog, inventory, and audits
scripts/                 Catalog builder and repository validator
docs/                    Installation, architecture, and publishing guides
```

## Quick installation examples

Clone the repository:

```bash
git clone https://github.com/YOUR_ACCOUNT/limitless-ai-skills-vault.git
cd limitless-ai-skills-vault
```

Install one Codex skill:

```bash
cp -R "skills/codex/local/example-skill" "$HOME/.codex/skills/"
```

Install one Claude skill:

```bash
cp -R "skills/claude/global/example-skill" "$HOME/.claude/skills/"
```

Replace `example-skill` with a real folder from the catalog. Never copy the
entire vault into an active agent directory unless that tool explicitly supports
large skill collections.

## Safety

Skills are instructions and may reference scripts, external services, package
managers, or tools that are not installed on your computer. Review a skill
before using it. Do not paste credentials into skill files, commit `.env` files,
or execute unfamiliar scripts without inspection.

## Licensing and provenance

This is an aggregation. Individual skills and assets retain their original
licenses and ownership. A license file inside a skill directory controls that
skill when present. Items without an explicit license require provenance review
before redistribution. See [`LICENSE.md`](LICENSE.md) and
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md). Every pull request must pass:

```bash
python3 scripts/build_repository.py --check
```

