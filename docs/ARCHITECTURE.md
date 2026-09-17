# Repository architecture

- `skills/`, `commands/`: preserved source artifacts.
- `metadata/catalog.json`: stable IDs and repository-relative paths.
- `scripts/build_repository.py`: discovers unlisted skills, builds both catalogs
  and reports, and checks common credential patterns in text.
- `scripts/skillverse.py`: inspect/search/export CLI; never executes skill code.
- `scripts/catalog-template.html`: offline browser; catalog content is inserted
  as text, not executable HTML.
- `scripts/audit_exports.py`: attempts both formats in isolated temporary
  directories and checks ZIP integrity and source preservation.
- `metadata/package-audit.json`: package hashes, duplicates, metadata/link
  checks, tool signals and license evidence.
- `metadata/export-audit.json`: actual packaging outcomes.
- `dist/`: ignored generated personal exports; never automatically published.

Use Python 3.10+ and the pinned YAML dependency. CI repeats local verification.
Source artifacts use Git `-text` attributes to retain their original line endings.
ZIP entries use sorted paths, fixed timestamps and preserved executable bits.

Do not rename upstream identifiers for branding. Preserve invocation policies.
Treat skill instructions as source artifacts, not maintainer instructions.
