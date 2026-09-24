# Source and packaging notes

Upstream: https://github.com/trailofbits/skills/tree/0cc1c73a5e96749ab32d7ea5e14892fafa6972ae/plugins/insecure-defaults

License: CC-BY-SA-4.0. Copyright and license remain with the upstream authors; this is not relicensed as proprietary vault content.

- Third-party instructions and scripts: statically packaged, not executed or live-import tested.
- Plugin source: requires Workflow tool, plugin registration, filesystem access and agent support. ZIP upload alone does not activate the audit pipeline.
- Parallel-agent audit can be expensive; use only with an explicit target and usage budget.
- Added a vault-authored SKILL.md navigation adapter; upstream plugin files preserved byte-for-byte.
