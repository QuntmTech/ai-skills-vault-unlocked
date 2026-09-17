# How SKILLVERSE works

1. Browse the offline catalog.
2. Inspect the original instructions, resources and review signals.
3. Export one skill to a ZIP, reference Markdown and JSON report.
4. Install it in a compatible host and verify a small task.

Nothing installs itself, connects an account or executes collected code.
All original variants remain intact.

## Counts

The initial catalog had 894 entries. A full inventory added 31 nested skill
variants with IDs 895–925: the catalog now covers 839 skills and 86 commands.

Duplicate grouping hashes relative filenames and every included file's bytes.
OS junk and generated caches are excluded. Mode bits are not part of duplicate
grouping, so this is not an automatic deletion rule.

## Labels

- **Structurally valid:** metadata and checked local Markdown links passed.
- **Needs review:** a name, metadata or local-link issue was found.
- **Command only:** a Claude command, not a standalone skill upload.
- **Tool signals:** heuristic mentions, not a complete dependency inventory.
- **License evidence:** a declaration or license/notice file was found, not
  redistribution approval.

A structurally valid ZIP can still rely on unavailable tools or contain unsafe
instructions. Publication rights and behavioral testing are separate gates.
