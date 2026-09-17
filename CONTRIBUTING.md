# Contributing

Contributions are welcome when they preserve provenance and keep the vault safe.

## Adding a skill

1. Add the complete skill directory under the matching provider collection.
2. Include its original license and attribution.
3. Add a repository-relative entry to `metadata/catalog.json` if it belongs in
   the curated catalog.
4. Run the builder and validator.
5. Explain the source, version, and reason for inclusion in the pull request.

## Pull-request requirements

- No secrets or personal absolute paths.
- No generated caches or operating-system metadata.
- No silent replacement of an existing skill.
- Provider and version differences must remain explicit.
- New scripts should be deterministic and should not download or execute remote
  code during validation.

```bash
python3 scripts/build_repository.py
python3 scripts/build_repository.py --check
git diff --check
```

