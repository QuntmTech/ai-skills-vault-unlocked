# ChatGPT reference — Artifact Template Operating Calendar

Readable guidance, not a native skill installation. No live ChatGPT test is claimed. Supporting scripts and assets are not embedded in this document. Provider-specific commands may require adaptation; do not assume tools are available.

## Requirements to review

- Claude upload description will be shortened; full text retained
- Agent tools mentioned
- Plugin source — verify required plugin capabilities in Claude

[Preserved source and supporting files](../../../../%F0%9F%94%A7%20ADVANCED/skills/codex/plugins/openai-templates%20%E2%80%94%20artifact-template-operating-calendar/SKILL.md)

---

# Reference copy — artifact-template-operating-calendar

This is a reading/copy-paste aid, not an installed skill. It does not include supporting files or grant access to tools. Review the ZIP and audit report before using this workflow.

---
name: artifact-template-operating-calendar
description: Create a spreadsheet using the Operating Calendar template and its retained
  reference file. Use when the user selects or names Operating Calendar. Plan annual
  and monthly operating milestones,...
---
## Full original description

Create a spreadsheet using the Operating Calendar template and its retained reference file. Use when the user selects or names Operating Calendar. Plan annual and monthly operating milestones, campaigns, launches, deadlines, and recurring events.


# Operating Calendar

Create a new spreadsheet from this template. Keep the reference file unchanged.

## Workflow

1. Read `artifact-template.json` and resolve its paths relative to this skill directory.
2. Identify the prompt-advertised preinstalled spreadsheet capability. Use the available resource or filesystem tool to open its advertised resource, plugin, skill, or file target, then follow its reference/template workflow with the retained file. If no such capability can be identified and read, say it is unavailable and stop; do not recreate or install it.
3. Treat the user's prompt and available sources as the content input. Do not invent facts merely to fill a template slot.
4. Clone or import the reference instead of replacing its visual system with generic defaults.
5. Render and verify the finished spreadsheet, then return the final artifact.

## Fidelity

Preserve sheet structure, formulas, names, number formats, dimensions, tables, charts, validation, conditional formatting, and frozen panes.

User instructions control requested content and explicit deviations. The retained reference controls layout and formatting where the user has not requested a change.
