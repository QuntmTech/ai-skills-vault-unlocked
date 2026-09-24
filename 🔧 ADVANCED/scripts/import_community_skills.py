#!/usr/bin/env python3
"""Import pinned, reviewed source snapshots. Never execute upstream code.

Usage: python3 scripts/import_community_skills.py --sources-dir /path/to/clones
Clones must have the names and exact commits below. Refuse changed destinations.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOS = {
    'adhd': ('ayghri/i-have-adhd', '839872f9d1cd634fed642b4589ce7226199cc15f', 'MIT'),
    'impeccable': ('pbakaus/impeccable', 'edb9c7fbcba158fb6236bd043d6cba18d9cde8d3', 'Apache-2.0'),
    'marketing': ('coreyhaines31/marketingskills', '5b2c0007766c6a1cf1d53fd8fc73e979e0821022', 'MIT'),
    'xcode': ('AvdLee/Xcode-Build-Optimization-Agent-Skill', '6bd7b596cd688b1127ded00e812b1b6937ec35d6', 'MIT'),
    'swiftui': ('AvdLee/SwiftUI-Agent-Skill', 'b24e68a965dc4b5bd2cc41dc60c094a26a9379ce', 'MIT'),
    'security': ('trailofbits/skills', '0cc1c73a5e96749ab32d7ea5e14892fafa6972ae', 'CC-BY-SA-4.0'),
}
XCODE = ['xcode-build-orchestrator', 'xcode-build-benchmark', 'xcode-compilation-analyzer',
         'xcode-project-analyzer', 'spm-build-analysis', 'xcode-build-fixer']
SELECTION = [
    ('adhd', 'skills/i-have-adhd', 'i-have-adhd', 'ADHD Friendly Answers', 'Tools & Workflows', '🧠 Memory, Knowledge & Prompting'),
    ('impeccable', 'plugin/skills/impeccable', 'impeccable', 'Impeccable — UI Design & Polish', 'Design & Media', '🖥️ UI, UX & Product Design'),
    *[('marketing', 'skills/' + n, n, title, 'Marketing & Business', '💰 Conversion, Offers & Pricing') for n, title in [
        ('copywriting', 'Conversion Copywriting'), ('cro', 'Conversion Rate Optimization'),
        ('offers', 'Offer Design'), ('pricing', 'Pricing & Monetization'),
        ('product-marketing', 'Product Marketing Context')]],
    *[('xcode', 'skills/' + n, n, n.replace('-', ' ').title().replace('Xcode', 'Xcode').replace('Spm', 'SPM'),
       'Coding & Development', '🍎 Xcode Build Performance') for n in XCODE],
    ('swiftui', 'skills/swiftui-expert-skill', 'swiftui-expert-skill', 'SwiftUI Expert', 'Coding & Development', '📱 Mobile & Desktop Apps'),
    *[('security', 'plugins/' + n + '/skills/' + n, n, title, 'Coding & Development', '🔐 Security & Authentication') for n, title in [
        ('differential-review', 'Security Review of Code Changes'), ('variant-analysis', 'Find Related Vulnerabilities')]],
    ('security', 'plugins/insecure-defaults', 'insecure-defaults', 'Insecure Defaults — Plugin Workflow Guide', 'Coding & Development', '🔐 Security & Authentication'),
]


def files(folder):
    result = {}
    for p in sorted(folder.rglob('*')):
        if p.is_symlink():
            raise ValueError('Symlink requires review: ' + str(p))
        if p.is_file():
            result[p.relative_to(folder).as_posix()] = p.read_bytes()
    return result


def adapt_xcode(data, companion=False):
    # Bundle sibling guidance under one upload root; keep the original entrypoint too.
    prefix = '../' if companion else 'companion-skills/'
    for name in XCODE:
        data = data.replace('../' + name + '/SKILL.md', prefix + name + '/REFERENCE.md')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources-dir', required=True, type=Path)
    args = parser.parse_args()
    clones = {}
    for key, (_, commit, _) in REPOS.items():
        clone = args.sources_dir / ('upstream-' + key)
        actual = subprocess.check_output(['git', '-C', str(clone), 'rev-parse', 'HEAD'], text=True).strip()
        if actual != commit:
            raise ValueError('Unexpected upstream revision: ' + key)
        if subprocess.check_output(['git', '-C', str(clone), 'status', '--porcelain'], text=True):
            raise ValueError('Upstream clone has modifications: ' + key)
        clones[key] = clone
    generated, entries, modes = {}, {}, {}
    for key, source_path, name, display, category, subcategory in SELECTION:
        repo, commit, license_name = REPOS[key]
        clone = clones[key]
        payload = files(clone / source_path)
        source_modes = {p: (clone / source_path / p).stat().st_mode & 0o777 for p in payload}
        original_hashes = {p: hashlib.sha256(b).hexdigest() for p, b in payload.items()}
        changes = []
        notes = ['Third-party instructions and scripts: statically packaged, not executed or live-import tested.']
        if key == 'xcode':
            changes.append('Sibling Markdown links redirected to bundled companion references; original SKILL.md preserved as UPSTREAM-SKILL.md.')
            payload['UPSTREAM-SKILL.md'] = payload['SKILL.md']
            payload['SKILL.md'] = adapt_xcode(payload['SKILL.md'].decode()).encode()
            for other in XCODE:
                for rel, data in files(clone / 'skills' / other).items():
                    target = 'REFERENCE.md' if rel == 'SKILL.md' else rel
                    if rel == 'SKILL.md':
                        data = adapt_xcode(data.decode(), companion=True).encode()
                    payload['companion-skills/' + other + '/' + target] = data
                    source_modes['companion-skills/' + other + '/' + target] = (clone / 'skills' / other / rel).stat().st_mode & 0o777
            notes += ['External tools required: macOS, Xcode, Python and access to the target project; ordinary cloud chat cannot run local Xcode.',
                      'All six specialist packages are visible in the Xcode category. Companion guidance/assets are also bundled inside each ZIP; these are references, not automatically installed skills.',
                      'Build benchmarking consumes CPU and disk space. This is not a cache cleaner. Review any clean-build, source-touch or project-change commands before execution.']
        if key == 'security' and name == 'insecure-defaults':
            changes.append('Added a vault-authored SKILL.md navigation adapter; upstream plugin files preserved byte-for-byte.')
            payload['SKILL.md'] = ("---\nname: insecure-defaults\ndescription: Review requirements and use the preserved Trail of Bits insecure-defaults plugin workflow for auditing configuration security. Requires a compatible developer host and Workflow tool.\nlicense: CC-BY-SA-4.0\ndisable-model-invocation: true\n---\n\n# Insecure defaults — plugin workflow guide\n\n"
                "This vault-authored adapter preserves a plugin, not a standalone executable Claude-app skill. Read [the upstream README](README.md) and [the upstream audit command](commands/audit.md). The detection corpus, workflow and plugin manifest are included unchanged.\n\n"
                "Before execution, verify that the host supports the plugin's Workflow tool, plugin registration, filesystem access and required agent models. A ZIP upload alone does not register the workflow. If any capability is missing, explain the setup requirement and stop; do not simulate a successful audit.\n\n"
                "Use the upstream audit command after compatible plugin installation; do not invoke its pipeline directly. This can spawn multiple agents and consume substantial usage. Obtain the user's audit scope before running. No runtime validation has been performed by this vault.\n").encode()
            notes += ['Plugin source: requires Workflow tool, plugin registration, filesystem access and agent support. ZIP upload alone does not activate the audit pipeline.',
                      'Parallel-agent audit can be expensive; use only with an explicit target and usage budget.']
        elif key == 'security':
            notes.append('External tools required: repository/filesystem access and compatible code-search or agent tools. Preserve Trail of Bits attribution and CC-BY-SA-4.0 notices.')
        elif key == 'impeccable':
            notes.append('External tools required: developer shell and project access. Its launcher may download an upstream binary on first use; no binary was downloaded or executed by the vault import.')
        elif key == 'swiftui':
            notes.append('External tools required for profiling: macOS, Xcode/xctrace and Python. Guidance can be read independently; scripts require local project/device access.')
        elif key == 'adhd':
            notes.append('Optional response style only, not a diagnosis or treatment. Do not infer that the reader has ADHD. Safety, accuracy and user instructions override formatting preferences.')
        else:
            notes.append('Marketing guidance only; verify factual claims, prices and product context. Related optional marketing skills are not all included.')
        for license_file in ('LICENSE', 'LICENSE.md', 'NOTICE.md', 'NOTICE'):
            if (clone / license_file).is_file():
                payload[license_file] = (clone / license_file).read_bytes()
        if not any(p.lower().startswith('license') for p in payload):
            raise ValueError('Missing license: ' + name)
        origin = {'repository': 'https://github.com/' + repo, 'commit': commit, 'source_path': source_path,
                  'license': license_name, 'upstream_files_sha256': original_hashes, 'adaptations': changes}
        payload['UPSTREAM.json'] = (json.dumps(origin, indent=2) + '\n').encode()
        payload['SOURCE.md'] = ('# Source and packaging notes\n\nUpstream: https://github.com/' + repo + '/tree/' + commit + '/' + source_path +
            '\n\nLicense: ' + license_name + '. Copyright and license remain with the upstream authors; this is not relicensed as proprietary vault content.\n\n' +
            '\n'.join('- ' + n for n in notes + changes) + '\n').encode()
        path = 'skills/community/' + key + '/' + name
        for rel, data in payload.items():
            generated[ROOT / path / rel] = data
            modes[ROOT / path / rel] = source_modes.get(rel, 0o644)
        entries[path + '/SKILL.md'] = {'collection': 'Community additions — 2026-09-24', 'display_name': display,
                                     'category': category, 'subcategory': subcategory, 'setup_notes': notes,
                                     'repository': origin['repository'], 'commit': commit, 'license': license_name}
    generated[ROOT / 'metadata/community-imports.json'] = (json.dumps({'schema_version': 1, 'entries': entries}, indent=2, ensure_ascii=False) + '\n').encode()
    # Preflight the entire batch before writing, including metadata.
    for path, data in generated.items():
        if path.is_symlink() or (path.exists() and path.read_bytes() != data):
            raise ValueError('Destination differs; preserved without overwrite: ' + str(path))
    for path, data in generated.items():
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(modes.get(path, 0o644))
    print(f'Imported {len(entries)} packages from {len(REPOS)} pinned repositories; no upstream code executed.')


if __name__ == '__main__':
    main()
