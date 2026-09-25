#!/usr/bin/env python3
"""Import eight reviewed UX packages from pinned clones; execute no upstream code."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = 'UX design additions — 2026-09-25'
REPOS = {
    'mae': ('mae616/design-skills', '79e3398bee27664de70c7b97a30dd928f6fe7976'),
    'rich': ('richhemsley3/claude-design-skills', '1185d0d84974eaed6e927b953243c96754de02b6'),
    'promax': ('nextlevelbuilder/ui-ux-pro-max-skill', 'dcc40ff5133ef78276117db0cc34e7b83cc8aeba'),
}
SELECTION = [
    ('mae', 'usability-psychologist', 'Usability & Cognitive Load Review', '🧭 UX Research & Usability'),
    ('mae', 'accessibility-engineer', 'Accessible Interface Design', '♿ Accessibility & Inclusive Design'),
    ('mae', 'creative-coder', 'Motion & Micro-Interaction Design', '✨ Motion & Interaction'),
    ('rich', 'wireframe-agent', 'Wireframe & Screen Layouts', '🖥️ UI, UX & Product Design'),
    ('rich', 'ux-flow-planner', 'User Flows & Onboarding', '🧭 UX Research & Usability'),
    ('rich', 'information-architect', 'Navigation & Information Architecture', '🧭 UX Research & Usability'),
    ('rich', 'content-copy-designer', 'UI Microcopy & Error Messages', '✍️ UI Writing & Microcopy'),
    ('promax', 'ui-ux-pro-max', 'UI UX Pro Max — Design System Toolkit', '🖥️ UI, UX & Product Design'),
]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources-dir', required=True, type=Path)
    args = parser.parse_args()
    metadata = ROOT/'metadata/community-imports.json'
    document = json.loads(metadata.read_text())
    generated = {}
    for key, name, title, subcategory in SELECTION:
        clone = args.sources_dir/key
        repo, commit = REPOS[key]
        assert subprocess.check_output(['git','-C',str(clone),'rev-parse','HEAD'],text=True).strip() == commit
        assert not subprocess.check_output(['git','-C',str(clone),'status','--porcelain'],text=True).strip()
        relative = ('.claude/skills/' if key == 'promax' else 'skills/') + name
        folder = clone/relative
        payload = {}
        for f in sorted(folder.rglob('*')):
            assert not f.is_symlink(), f
            if f.is_file():
                payload[f.relative_to(folder).as_posix()] = f.read_bytes()
        hashes = {p:hashlib.sha256(b).hexdigest() for p,b in payload.items()}
        original = payload['SKILL.md']
        text = original.decode()
        text = re.sub(r'^name: .*$', 'name: vault-'+name, text, count=1, flags=re.M)
        text = re.sub(r'^user-invocable: false\n', '', text, flags=re.M)
        front, body = text.split('---',2)[1:]
        notes = ['Individual Claude upload package; archive checks are not live-import or behavior verification.',
                 'Internal name is vault-'+name+' to reduce collisions; original entrypoint and MIT license are preserved.']
        changes = ['Namespaced internal skill name; removed Claude Code-only user-invocable metadata where present.',
                   'Added host capability and design-system adaptation guidance.']
        intro = ('\n\n## Vault portability notes\n\n'
                 'Use only files, screenshots and context the user supplies or authorizes. Do not imply access to a local project or a live browser when unavailable. '
                 'Review guidance is not proof of accessibility compliance, user research, performance, or runtime behavior. '
                 'Respect the user’s existing design system and scope.\n\n')
        if key == 'rich':
            body = body.replace('--sds-', '--example-')
            body = body.replace('## your design system Layout Constants', '## Example Layout Constants — Replace With Project Values')
            body = body.replace('## your design system Navigation Patterns', '## Example Navigation Patterns — Adapt to the Project')
            body = body.replace('The design system supports these navigation structures:', 'Example navigation structures (not a required design system):')
            body = re.sub(r'`/([a-z-]+)`', lambda m: ('the optional '+m.group(1)+' workflow'), body)
            intro += ('All numeric dimensions, colors, token names, product terminology and timings below are illustrative, not requirements for your project. '
                      'Map example tokens to the user’s supplied design tokens; do not invent installed components. '
                      'References to other workflows are optional, not available slash commands or required installed skills. '
                      'Only promise saved data, automatic retries or offline sync in UI copy when the product actually implements them.\n\n')
            changes += ['Relabeled upstream fixed design values as examples; renamed sds tokens to example tokens; removed slash-command assumptions.']
        if key == 'promax':
            body = body.replace('${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max', '${SKILL_DIR}')
            body = body.replace('see README for install instructions if Python is missing', 'if Python is unavailable, use the reference-only fallback below; do not install software automatically')
            intro += ('This package includes the upstream data, references and Python scripts; it is not a plugin. '
                      'If code execution is available, resolve the actual directory containing this SKILL.md and set SKILL_DIR to that directory in the shell session used by the examples. '
                      'Do not assume a plugin environment variable exists. Python search execution and live Claude import are unverified. '
                      'If code execution is unavailable, read references/quick-reference.md and references/pro-rules.md directly and clearly label your result as reference-based guidance, not database-search output. '
                      'Do not claim a search ran. Do not use --persist or --force unless saving or overwriting files is authorized.\n\n')
            notes += ['Python/code execution is needed for the bundled search tool. Without it, use the included reference-only fallback; no plugin installation required.']
            changes += ['Replaced plugin-root command paths with a resolved SKILL_DIR and documented reference-only fallback.']
        payload['UPSTREAM-SKILL.md'] = original
        payload['SKILL.md'] = ('---'+front+'---'+intro+body.lstrip()).encode()
        payload['LICENSE'] = (clone/'LICENSE').read_bytes()
        origin = {'repository':'https://github.com/'+repo,'commit':commit,'source_path':relative,'license':'MIT',
                  'upstream_files_sha256':hashes,'adaptations':changes}
        payload['UPSTREAM.json'] = (json.dumps(origin,indent=2)+'\n').encode()
        payload['SOURCE.md'] = ('# Source and adaptation\n\nhttps://github.com/'+repo+'/tree/'+commit+'/'+relative+'\n\nMIT; original authors retain copyright.\n\n'+'\n'.join('- '+x for x in notes+changes)+'\n').encode()
        path = 'skills/community/ux-design/'+name
        for rel,data in payload.items():
            generated[ROOT/path/rel] = data
        document['entries'][path+'/SKILL.md'] = {'collection':COLLECTION,'display_name':title,'category':'Design & Media',
          'subcategory':subcategory,'setup_notes':notes,'repository':origin['repository'],'commit':commit,'license':'MIT'}
    for path,data in generated.items():
        assert not path.is_symlink()
        assert not path.exists() or path.read_bytes()==data, path
    for path,data in generated.items():
        if not path.exists():
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(data)
    metadata.write_text(json.dumps(document,indent=2,ensure_ascii=False)+'\n')
    print('Imported eight UX packages with original bytes, provenance and licenses preserved.')

if __name__ == '__main__':
    main()
