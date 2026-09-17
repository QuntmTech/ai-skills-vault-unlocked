# Repository architecture

The repository separates human navigation, source artifacts, and generated
metadata.

- `skills/` and `commands/` are the preserved source artifacts.
- `metadata/catalog.json` is the sanitized, curated source of truth for the
  public catalog.
- `catalog/skills-catalog.md`, `metadata/inventory.json`, and
  `metadata/license-audit.json` are generated.
- `scripts/build_repository.py` performs deterministic generation and safety
  validation without executing collected skills.

Top-level collection names are normalized for public use. Internal skill folder
names remain unchanged because tools and documentation may refer to those names.

