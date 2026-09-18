# ChatGPT reference — Artifact Template Operating Review

Readable guidance, not a native skill installation. No live ChatGPT test is claimed. Supporting scripts and assets are not embedded in this document. Provider-specific commands may require adaptation; do not assume tools are available.

## Requirements to review

- Claude upload description will be shortened; full text retained
- Agent tools mentioned
- Plugin source — verify required plugin capabilities in Claude

[Preserved source and supporting files](../../../%F0%9F%94%A7%20ADVANCED/skills/codex/plugins/openai-templates%20%E2%80%94%20artifact-template-operating-review/SKILL.md)

---

# Reference copy — artifact-template-operating-review

This is a reading/copy-paste aid, not an installed skill. It does not include supporting files or grant access to tools. Review the ZIP and audit report before using this workflow.

---
name: artifact-template-operating-review
description: Create a presentation using the Operating Review template and its retained
  reference file. Use when the user selects or names Operating Review. Run weekly
  operating reviews with scorecards,...
---
## Full original description

Create a presentation using the Operating Review template and its retained reference file. Use when the user selects or names Operating Review. Run weekly operating reviews with scorecards, functional updates, risks, decisions, and action items.


# Operating Review

Create a new presentation from this template. Keep the reference file unchanged.

## Workflow

1. Read `artifact-template.json` and resolve its paths relative to this skill directory.
2. Identify the prompt-advertised preinstalled presentation or slides capability. Use the available resource or filesystem tool to open its advertised resource, plugin, skill, or file target, then follow its reference/template workflow with the retained file. If no such capability can be identified and read, say it is unavailable and stop; do not recreate or install it.
3. Treat the user's prompt and available sources as the content input. Do not invent facts merely to fill a template slot.
4. Clone or import the reference instead of replacing its visual system with generic defaults.
5. Render and verify the finished presentation, then return the final artifact.

## Fidelity

Preserve source slides, layouts, masters, typography, geometry, images, charts, tables, and recurring slide chrome.

User instructions control requested content and explicit deviations. The retained reference controls layout and formatting where the user has not requested a change.
