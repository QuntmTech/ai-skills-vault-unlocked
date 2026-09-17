# Pick one skill, not the whole vault

## 1. Find and inspect

Open `catalog/index.html`, search a topic and expand **Requirements & export**.
Read the original instructions and supporting resources. Set up Python using
the main README. Use the entry ID from the catalog; 91 is a real example.

```bash
python3 scripts/skillverse.py show 91
python3 scripts/skillverse.py export 91 --target claude
```

## 2. Choose your destination

| Destination | Package / installation |
| --- | --- |
| Claude chat / desktop | Export with `--target claude`; upload the one-skill ZIP using Customize → Skills and its add/upload control, where available. |
| ChatGPT | Review the Skills interface available in your desktop account. Use a portable package if it accepts archives; otherwise use its supported extracted-folder/authoring workflow. Universal ZIP upload is not claimed. |
| Codex | Export with `--target portable`; extract the inner folder and copy it to `~/.agents/skills/<skill-name>/`. |
| Claude Code | Export with `--target portable`; extract the inner folder and copy it to `~/.claude/skills/<skill-name>/`. |
| Reading / copy-paste | Use the exported `-reference.md`. This is not native installation and does not include supporting files or grant tools. |

If an installation folder already exists, compare it first. Do not overwrite
it or install multiple same-name variants blindly. Do not install the whole vault.

The [OpenAI skills guide](https://learn.chatgpt.com/docs/build-skills) distinguishes
standalone desktop/CLI/IDE skills from plugin distribution across other surfaces.
Account controls and available import interfaces can vary. This package is not
a published ChatGPT plugin or a claim that every ChatGPT account has ZIP import.

See also the [Claude authoring guide](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)
and [Claude Code skills](https://code.claude.com/docs/en/skills).

## 3. Understand the export

Each ZIP contains one skill folder with `SKILL.md` and supporting files.
Names are normalized in exported copies only. Claude exports shorten discovery
descriptions longer than 200 characters, keeping the full description in the
body. Original metadata and changes are recorded in the adjacent JSON report.
Portable exports retain full descriptions. Existing policy/dependency fields
and `agents/openai.yaml` are preserved.

Tool references are not automatically rewritten: changing a tool name does not
make the equivalent tool available in another host. Some skills require their
original plugin ecosystem. Inspect the report before enabling them.

## 4. Test a small task

Use a disposable document or project. Verify the host selected the skill, can
access its resources, and produces the expected result before allowing important
edits or external actions. Local ZIP tests do not prove live import or task success.

## If export stops

Missing metadata/resources, symlinks, environment files, command-only entries or
existing output filenames cause a refusal. Resolve the exact issue rather than
deleting warnings. Use `--out dist/another-export` to avoid an existing filename.

The link check covers ordinary Markdown links outside code examples, not every
possible reference embedded in prose or scripts. All scripts still need review.
