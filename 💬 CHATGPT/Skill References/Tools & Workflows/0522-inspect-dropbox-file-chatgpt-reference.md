# ChatGPT reference — Inspect Dropbox File

Readable guidance, not a native skill installation. No live ChatGPT test is claimed. Supporting scripts and assets are not embedded in this document. Provider-specific commands may require adaptation; do not assume tools are available.

## Requirements to review

- Claude upload description will be shortened; full text retained
- MCP/tool connection mentioned
- Agent tools mentioned
- Plugin source — verify required plugin capabilities in Claude
- External tools or services mentioned — review availability

[Preserved source and supporting files](../../../%F0%9F%94%A7%20ADVANCED/skills/codex/plugins/app-69b31dc2110c8191b8b47dc98fe5a052%20%E2%80%94%20inspect-dropbox-file/SKILL.md)

---

# Reference copy — inspect-dropbox-file

This is a reading/copy-paste aid, not an installed skill. It does not include supporting files or grant access to tools. Review the ZIP and audit report before using this workflow.

---
name: inspect-dropbox-file
description: Inspect a Dropbox file or folder by checking metadata, shared links,
  and file content when needed. Use when the user asks what a file is, whether it
  is shared, when it changed, what access links...
---
## Full original description

Inspect a Dropbox file or folder by checking metadata, shared links, and file content when needed. Use when the user asks what a file is, whether it is shared, when it changed, what access links exist, or asks to read/analyze a Dropbox file.


# Inspect Dropbox File

Use this skill to understand a Dropbox file or folder before summarizing, comparing, sharing, restoring, or organizing it.

## Tools

- `get_file_metadata`
- `fetch`
- `list_shared_links`
- `get_shared_link_metadata`
- `search`
- `list_folder`

## Workflow

1. Identify the target file or folder from the user request.
2. If the target is ambiguous, use `search` or `list_folder` to find likely matches.
3. Call `get_file_metadata` for the chosen item.
4. If the user asks about content, summary, extraction, or analysis, use `fetch` for files.
5. If the user asks about version history or rollback options, explain that the current Dropbox MCP tools do not expose revision listing or restore operations.
6. If the user asks about sharing or access, use `list_shared_links`; continue while the response indicates has_more or returns a cursor before claiming the shared-link listing is complete.
7. If the user provides a Dropbox shared link or asks about a specific link, use `get_shared_link_metadata`.

## Output

Summarize only the details relevant to the user request. Include:

- Name and path
- File or folder type
- Size and modified time when available
- Sharing/link status when relevant, including whether shared-link pagination is complete
- Version-history limitation when relevant
- Fetched content summary when relevant
- Recommended next action, if the user asked for one

## Safety

This is a read-only workflow. Do not create links, change sharing, copy, move, delete, or restore content. If the user asks for a mutation, explain the intended action and switch to the relevant Dropbox skill.

## Good Triggers

- "What is this Dropbox file?"
- "Summarize this file."
- "Check whether this folder is shared."
- "Show me the revision history."
- "When was this document last updated?"

## Do Not Use When

- The user only wants to search or browse. Use `find-dropbox-content`.
- The user wants to create a shared link or inspect shared-link state. Use `share-dropbox-content`.
- The user wants to add viewers or share directly with named recipients. Explain that recipient-sharing is unavailable until the required MCP tools are exposed.
- The user wants to restore a revision. Explain that recovery is unavailable until the Dropbox restore tool is exposed.
