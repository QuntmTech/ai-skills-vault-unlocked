# Community additions — September 24, 2026

17 packages, six upstream repositories. This is a pinned source import, not a
global installation or a claim of successful runtime use in Claude or ChatGPT.
The existing library is preserved. All new packages appear in the ordinary
topic folders, with actual source files and an individual ZIP together.

## Find the additions

| Topic / subcategory | Visible package names |
| --- | --- |
| Tools & Workflows / Memory, Knowledge & Prompting | ADHD Friendly Answers |
| Design & Media / UI, UX & Product Design | Impeccable — UI Design & Polish |
| Marketing & Business / Conversion, Offers & Pricing | Conversion Copywriting; Conversion Rate Optimization; Offer Design; Pricing & Monetization; Product Marketing Context |
| Coding & Development / Xcode Build Performance | Xcode Build Orchestrator; Xcode Build Benchmark; Xcode Compilation Analyzer; Xcode Project Analyzer; SPM Build Analysis; Xcode Build Fixer |
| Coding & Development / Mobile & Desktop Apps | SwiftUI Expert |
| Coding & Development / Security & Authentication | Security Review of Code Changes; Find Related Vulnerabilities; Insecure Defaults — Plugin Workflow Guide |

Use the vault's **📦 CLAUDE** directory for source-plus-ZIP folders. The same
topics under **💬 CHATGPT / Skill References** contain readable references.
ChatGPT references are context documents, not native installers. Read each
VAULT GUIDE.md before using its package.

## Important requirements

- ADHD Friendly Answers is optional formatting guidance, not diagnosis or treatment.
- Impeccable expects developer tools/project access; its launcher can download an
  upstream binary. No such binary was downloaded or executed during packaging.
- Marketing packages need real product context. Only the five listed skills are
  imported; optional related marketing skills are not all bundled.
- Xcode packages need macOS, Xcode, Python and the target project. Benchmarks can
  consume significant CPU and disk. They are not storage-cleaning utilities.
- SwiftUI's profiling scripts need macOS/Xcode tooling; ordinary cloud chat
  cannot operate a local device or Xcode session just by reading the instructions.
- Trail of Bits reviews need repository/code-search tools. Insecure Defaults is
  currently a plugin workflow, not an upstream standalone skill. Its added
  navigation adapter explicitly stops when the required Workflow tool/plugin
  registration is unavailable. Uploading its ZIP alone does not activate it.
- No upstream scripts or workflows were run. No live AI-host import is certified.

## Preservation and provenance

Each package includes upstream license/notice files, SOURCE.md and UPSTREAM.json.
The latter pins the exact Git commit and hashes the original selected files.
The import manifest is [community-imports.json](../metadata/community-imports.json).

Two adaptations are explicit rather than hidden:

1. Six Xcode packages refer to one another. Every ZIP contains all six companion
   reference sets under companion-skills, with resolvable Markdown links. The
   original top-level SKILL.md is retained as UPSTREAM-SKILL.md. Companion
   REFERENCE.md files are guidance, not automatically installed agent skills.
2. The Insecure Defaults plugin has no upstream SKILL.md. The vault adds a
   CC-BY-SA-4.0 navigation adapter while preserving the complete plugin's original
   selected files. This adapter does not impersonate a working standalone audit.

The other imported source files are retained byte-for-byte. Regression tests
check recorded upstream hashes, source/ZIP visibility, Xcode companion links and
the workflow warning. Packaging checks are not a comprehensive security audit.

## Maintain this batch

Run maintenance commands from **🔧 ADVANCED**. The importer requires six clean
clones named upstream-adhd, upstream-impeccable, upstream-marketing,
upstream-xcode, upstream-swiftui and upstream-security at the exact revisions
listed in scripts/import_community_skills.py. It refuses changed destinations.

```bash
python3 scripts/import_community_skills.py --sources-dir /path/to/reviewed-clones
python3 scripts/build_repository.py
python3 scripts/build_easy_library.py
python3 scripts/audit_exports.py
python3 -m unittest discover -s tests -v
python3 scripts/build_repository.py --check
python3 scripts/build_easy_library.py --check
python3 scripts/audit_exports.py --check
git diff --check
```

Do not run collected scripts just to validate packaging. A future upstream
refresh must review changes and preserve the existing version, not silently
overwrite the pinned import. Optional skilldiff, multi-agent ADHD reasoning and
AccessLint were not installed or included in this batch.

The repository remains private. Preserve attribution and applicable share-alike
obligations; do not treat these third-party packages as exclusively owned content
or as blanket-cleared material for resale.
