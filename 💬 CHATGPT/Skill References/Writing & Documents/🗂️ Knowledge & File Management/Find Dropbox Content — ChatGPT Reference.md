# ChatGPT reference — Find Dropbox Content

Readable guidance, not a native skill installation. No live ChatGPT test is claimed. Supporting scripts and assets are not embedded in this document. Provider-specific commands may require adaptation; do not assume tools are available.

## Requirements to review

- Claude upload description will be shortened; full text retained
- MCP/tool connection mentioned
- Plugin source — verify required plugin capabilities in Claude
- External tools or services mentioned — review availability

[Preserved source and supporting files](../../../../%F0%9F%94%A7%20ADVANCED/skills/codex/plugins/app-69b31dc2110c8191b8b47dc98fe5a052%20%E2%80%94%20find-dropbox-content/SKILL.md)

---

# Reference copy — find-dropbox-content

This is a reading/copy-paste aid, not an installed skill. It does not include supporting files or grant access to tools. Review the ZIP and audit report before using this workflow.

---
name: find-dropbox-content
description: Find Dropbox files and folders relevant to a user request. Use when the
  user asks to search Dropbox, find a document, locate recent files, browse a folder,
  identify likely source files, or narrow...
---
## Full original description

Find Dropbox files and folders relevant to a user request. Use when the user asks to search Dropbox, find a document, locate recent files, browse a folder, identify likely source files, or narrow down where content lives before reading, sharing, organizing, or restoring it.


# Find Dropbox Content

Use this skill to locate relevant Dropbox files and folders without changing anything.

## Tools

- `search`
- `list_folder`
- `get_file_metadata`

## Workflow

1. Clarify the search target only if the user request is too broad to act on.
2. Use `search` for broad keyword, title, file type, or natural-language searches.
3. When `search` returns a cursor and more results are needed, continue with `search` using the cursor only.
4. Use `list_folder` with `recursive=false` when the user names a folder or wants to browse a location.
5. When `list_folder` returns a cursor and more folder results are needed, continue with `list_folder` using the cursor only.
6. Use `get_file_metadata` for strong candidates before presenting a final recommendation.

## Output

Return the best matches first. For each result, include:

- Name
- Object type: file or folder
- Path or stable identifier
- Modified time when available
- Why it matched the request
- Any ambiguity or confidence caveat

## Safety

Do not create, copy, move, delete, restore, download, or share content. If the user asks to take one of those actions after finding content, switch to the relevant Dropbox skill.

## Good Triggers

- "Find the Q4 planning deck in Dropbox."
- "Search Dropbox for onboarding docs."
- "What files are in this folder?"
- "Find recent PDFs about the launch plan."
- "Where is the customer contract?"

## Do Not Use When

- The user already provided an exact file and wants its content inspected. Use `inspect-dropbox-file`.
- The user explicitly asks to create a shared link. Use `share-dropbox-content`.
- The user asks to add viewers or share directly with named recipients. Explain that recipient-sharing is unavailable until the required MCP tools are exposed.
- The user asks to restore or recover content. Explain that recovery is unavailable until the Dropbox restore tool is exposed.
