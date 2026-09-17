# Installation

## Download the complete library

```bash
git clone https://github.com/YOUR_ACCOUNT/limitless-ai-skills-vault.git
cd limitless-ai-skills-vault
```

You may also use GitHub's **Code → Download ZIP** option.

## Install a Codex skill

Copy the complete directory containing `SKILL.md`:

```bash
mkdir -p "$HOME/.codex/skills"
cp -R "skills/codex/local/SKILL_NAME" "$HOME/.codex/skills/"
```

## Install a Claude skill

```bash
mkdir -p "$HOME/.claude/skills"
cp -R "skills/claude/global/SKILL_NAME" "$HOME/.claude/skills/"
```

## Install a Claude slash command

Review the selected Markdown file, then copy it to the command directory used by
your Claude Code installation:

```bash
mkdir -p "$HOME/.claude/commands"
cp "commands/claude/global/COMMAND_NAME.md" "$HOME/.claude/commands/"
```

## Before enabling a skill

1. Read `SKILL.md` completely.
2. Inspect included scripts and dependencies.
3. Confirm referenced tools are installed and trusted.
4. Keep secrets in environment variables or your platform's secret manager.
5. Test unfamiliar automation in a disposable project first.

