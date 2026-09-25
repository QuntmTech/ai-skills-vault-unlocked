#!/usr/bin/env python3
"""Create verified, human-sized skill upload batches without executing skills."""
import argparse
import hashlib
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_BATCH = 20
CATEGORY_ORDER = {
    name: index for index, name in enumerate((
        'Coding & Development',
        'Design & Media',
        'Writing & Documents',
        'Marketing & Business',
        'Research & Data',
        'Tools & Workflows',
    ))
}


def clean_filename(value):
    return value.replace('/', ' - ').replace(':', ' -').strip()


def inspect_zip(path):
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None, f'Corrupt ZIP: {path}'
        names = archive.namelist()
        roots = [name for name in names if name.count('/') == 1 and name.endswith('/SKILL.md')]
        skills = [name for name in names if name.endswith('/SKILL.md')]
        assert len(roots) == 1 and skills == roots, f'Expected one root SKILL.md: {path}'
        assert not any('.claude-plugin/' in name for name in names), f'Plugin manifest in skill ZIP: {path}'
        text = archive.read(roots[0]).decode('utf-8')
        match = re.search(r'^name:\s*(.+?)\s*$', text, re.MULTILINE)
        assert match, f'Missing internal skill name: {path}'
        name = match.group(1).strip('"\'')
        assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name), f'Invalid internal skill name: {path}'
        assert len(name) <= 64, f'Internal skill name is too long: {path}'
        assert 'claude' not in name.casefold(), f'Reserved word in internal skill name: {path}'
        return name


def add_batch(generated, folder, entries, platform, inventory, section):
    for batch_index in range(0, len(entries), MAX_BATCH):
        batch = entries[batch_index:batch_index + MAX_BATCH]
        batch_folder = folder / f'Batch {batch_index // MAX_BATCH + 1:02d} — {len(batch)} skills'
        for entry in batch:
            source = ROOT / entry['zip']
            destination = batch_folder / f"{entry['id']:04d} — {clean_filename(entry['display_name'])}.zip"
            data = source.read_bytes()
            assert destination not in generated
            generated[destination] = data
            inventory.append({
                'platform': platform,
                'section': section,
                'batch': destination.relative_to(ROOT / '📤 UPLOAD BATCHES').as_posix(),
                'file': destination.name,
                'id': entry['id'],
                'internal_name': entry['_internal_name'],
                'display_name': entry['display_name'],
                'category': entry['category'],
                'subcategory': entry.get('subcategory'),
                'status': entry['status'],
                'source': entry['zip'],
                'sha256': hashlib.sha256(data).hexdigest(),
            })


def add_grouped_batches(generated, base, entries, platform, inventory, section):
    grouped = defaultdict(list)
    for entry in entries:
        grouped[entry['category']].append(entry)
    categories = sorted(grouped, key=lambda name: (CATEGORY_ORDER.get(name, 99), name))
    for category in categories:
        rows = sorted(grouped[category], key=lambda row: (
            row.get('subcategory') or '', row['display_name'].casefold(), row['id']
        ))
        add_batch(generated, base / category, rows, platform, inventory, section)


def add_flat_upload_folder(generated, folder, entries):
    """Add ZIP-only copies for selecting an entire curated set at once."""
    seen_names = set()
    inventory = []
    for entry in entries:
        internal_name = entry['_internal_name']
        assert internal_name not in seen_names, f'Duplicate internal skill name: {internal_name}'
        seen_names.add(internal_name)
        source = ROOT / entry['zip']
        data = source.read_bytes()
        destination = folder / f"{entry['id']:04d} — {clean_filename(entry['display_name'])}.zip"
        assert destination not in generated
        generated[destination] = data
        inventory.append({
            'file': destination.name,
            'id': entry['id'],
            'internal_name': internal_name,
            'display_name': entry['display_name'],
            'category': entry['category'],
            'subcategory': entry.get('subcategory'),
            'status': entry['status'],
            'source': entry['zip'],
            'sha256': hashlib.sha256(data).hexdigest(),
        })
    return inventory


def primary_rank(entry):
    return (
        entry['status'] != 'Packaging checked',
        '/plugins/' in entry['path'],
        entry['id'],
    )


def special_batches(generated, rows):
    batches = {
        '🎨 UX UI Design — Claude Uploads': [
            entry for entry in rows if entry.get('collection') == 'UX design additions — 2026-09-25'
        ],
        '🔀 GitHub & Code Review — Claude Uploads': [
            entry for entry in rows if entry.get('subcategory') == '🔀 GitHub & Code Review'
        ],
    }
    assert [len(value) for value in batches.values()] == [8, 11]
    for title, entries in batches.items():
        folder = ROOT / '📤 UPLOAD BATCHES' / title
        checksums, inventory = [], []
        for entry in entries:
            source = ROOT / entry['zip']
            internal_name = inspect_zip(source)
            destination = folder / (clean_filename(entry['display_name']) + '.zip')
            data = source.read_bytes()
            generated[destination] = data
            checksums.append(hashlib.sha256(data).hexdigest() + '  ' + destination.name)
            inventory.append({
                'file': destination.name,
                'source': entry['zip'],
                'status': entry['status'],
                'requirements': entry['signals'],
            })
        generated[folder / 'SHA256SUMS.txt'] = ('\n'.join(checksums) + '\n').encode()
        generated[folder / 'Requirements.json'] = (json.dumps(inventory, indent=2, ensure_ascii=False) + '\n').encode()
        generated[folder / 'READ ME.md'] = (
            f'# {title}\n\n{len(entries)} individual skill ZIPs. Select the ZIP files together in Claude’s skill uploader if your interface supports multiple selection. Leave individual ZIPs zipped; do not upload this entire folder as one skill.\n\n'
            'Original packages remain in their category folders. These are byte-identical copies with readable filenames. Check Requirements.json for each skill. Archive integrity does not prove successful Claude import or runtime behavior. If Claude reports an existing internal name, skip it unless you intentionally want to replace that installed skill.\n\n'
            'GitHub/code-review workflows may need repository access, GitHub authentication, shell tools or Claude Code; uploading a skill does not grant those capabilities. UI UX Pro Max requires code execution/Python for search and provides a reference-only fallback without it. No account imports were performed.\n'
        ).encode()
    return {entry['_internal_name'] for entries in batches.values() for entry in entries}


def outputs():
    document = json.loads((ROOT / '🔧 ADVANCED/metadata/easy-library.json').read_text())
    rows = [dict(entry) for entry in document['entries'] if entry.get('zip')]
    for entry in rows:
        entry['_internal_name'] = inspect_zip(ROOT / entry['zip'])

    generated = {}
    prepared_names = special_batches(generated, rows)

    by_name = defaultdict(list)
    for entry in rows:
        by_name[entry['_internal_name']].append(entry)
    primary, alternates = [], []
    for name in sorted(by_name):
        variants = sorted(by_name[name], key=primary_rank)
        primary.append(variants[0])
        alternates.extend(variants[1:])

    primary = sorted(primary, key=lambda row: (
        CATEGORY_ORDER.get(row['category'], 99), row['category'],
        row.get('subcategory') or '', row['display_name'].casefold(), row['id'],
    ))
    new_for_claude = [entry for entry in primary if entry['_internal_name'] not in prepared_names]
    prepared_for_claude = [entry for entry in primary if entry['_internal_name'] in prepared_names]

    complete_root = ROOT / '📤 UPLOAD BATCHES/🌐 COMPLETE SKILL BULK UPLOADS'
    inventory = []
    claude_root = complete_root / '📦 CLAUDE — BULK UPLOADS'
    chatgpt_root = complete_root / '💬 CHATGPT — BULK UPLOADS'

    add_grouped_batches(generated, claude_root / '01 UPLOAD THESE NEXT — NEW PRIMARY SKILLS',
                        new_for_claude, 'Claude', inventory, 'new-primary')
    add_grouped_batches(generated, claude_root / '02 ALREADY PREPARED — SKIP IF INSTALLED',
                        prepared_for_claude, 'Claude', inventory, 'previously-prepared')
    add_grouped_batches(generated, claude_root / '⚠️ ALTERNATE SAME-NAME VERSIONS — DO NOT BULK UPLOAD',
                        alternates, 'Claude', inventory, 'alternate-conflict')
    add_grouped_batches(generated, chatgpt_root / '01 ALL PRIMARY SKILLS',
                        primary, 'ChatGPT', inventory, 'all-primary')
    add_grouped_batches(generated, chatgpt_root / '⚠️ ALTERNATE SAME-NAME VERSIONS — DO NOT BULK UPLOAD',
                        alternates, 'ChatGPT', inventory, 'alternate-conflict')

    shared_note = (
        f'Each numbered batch contains at most {MAX_BATCH} individual ZIP files. Open one Batch folder, select all '
        'ZIPs in that folder, and upload them together only if your interface supports multi-selection. Do not upload '
        'the Batch folder itself. Packages passed structural checks, but no live account imports or runtime behavior '
        'are claimed. Skills that require external tools, credentials, local paths, or code execution still need that '
        'setup after installation.\n\nThe alternate section is preserved for completeness but is not a bulk-upload '
        'queue: those packages share internal names with primary choices and can trigger Replace/Already exists prompts.\n'
    )
    generated[claude_root / '00 START HERE.md'] = (
        '# Claude bulk uploads\n\n'
        f'Upload **01 UPLOAD THESE NEXT** first: {len(new_for_claude)} primary skills not already included in the '
        'earlier UX/UI and GitHub/code-review batches. **02 ALREADY PREPARED** contains the remaining '
        f'{len(prepared_for_claude)} primary skills and should be skipped when those names are already installed.\n\n'
        + shared_note
    ).encode()
    generated[chatgpt_root / '00 START HERE.md'] = (
        '# ChatGPT bulk uploads\n\n'
        f'**01 ALL PRIMARY SKILLS** contains {len(primary)} distinct internal skill names. ChatGPT skill upload is '
        'available only on eligible plans/workspaces with the required permissions.\n\n' + shared_note
    ).encode()
    summary = {
        'source_zip_packages': len(rows),
        'distinct_primary_internal_names': len(primary),
        'same_name_alternate_packages': len(alternates),
        'claude_new_primary': len(new_for_claude),
        'claude_previously_prepared_primary': len(prepared_for_claude),
        'chatgpt_primary': len(primary),
        'maximum_zips_per_numbered_batch': MAX_BATCH,
        'category_counts': {
            category: sum(entry['category'] == category for entry in primary)
            for category in CATEGORY_ORDER
        },
        'claims': {
            'archive_integrity_checked': True,
            'single_root_skill_entrypoint_checked': True,
            'reserved_internal_names_checked': True,
            'plugin_manifests_excluded': True,
            'live_claude_imports_verified': 0,
            'live_chatgpt_imports_verified': 0,
        },
    }
    generated[complete_root / '00 INVENTORY.json'] = (
        json.dumps({'summary': summary, 'entries': inventory}, indent=2, ensure_ascii=False) + '\n'
    ).encode()
    generated[complete_root / 'README.md'] = (
        '# Complete skill bulk uploads\n\n'
        f'{len(primary)} primary skills are organized for both Claude and ChatGPT. The {len(alternates)} alternate '
        'same-name packages are preserved separately and must not be uploaded as part of the primary queue.\n\n'
        'Start with the platform folder’s **00 START HERE.md** file.\n'
    ).encode()

    flat_root = ROOT / '📤 UPLOAD BATCHES/⚡ ONE-FOLDER BULK UPLOADS'
    flat_folder = flat_root / '📦 CLAUDE — TOOLS WORKFLOWS + WRITING DOCUMENTS — UPLOAD ALL'
    flat_categories = {'Tools & Workflows', 'Writing & Documents'}
    flat_entries = [entry for entry in primary if entry['category'] in flat_categories]
    flat_inventory = add_flat_upload_folder(generated, flat_folder, flat_entries)
    flat_counts = {
        category: sum(entry['category'] == category for entry in flat_entries)
        for category in sorted(flat_categories)
    }
    assert flat_counts == {'Tools & Workflows': 173, 'Writing & Documents': 16}
    assert len(flat_entries) == len({entry['_internal_name'] for entry in flat_entries}) == 189
    generated[flat_root / '00 INVENTORY.json'] = (
        json.dumps({
            'summary': {
                'platform': 'Claude',
                'distinct_primary_skills': len(flat_entries),
                'category_counts': flat_counts,
                'zip_only_upload_folder': flat_folder.relative_to(flat_root).as_posix(),
                'live_claude_imports_verified': 0,
            },
            'entries': flat_inventory,
        }, indent=2, ensure_ascii=False) + '\n'
    ).encode()
    generated[flat_root / 'README.md'] = (
        '# One-folder Claude bulk upload\n\n'
        f'The **{flat_folder.name}** folder contains exactly {len(flat_entries)} individual ZIP files: '
        f"{flat_counts['Tools & Workflows']} Tools & Workflows skills and "
        f"{flat_counts['Writing & Documents']} Writing & Documents skills.\n\n"
        'Open that folder, select all ZIP files, and add them with Claude’s skill uploader if the interface accepts '
        'that many files at once. The upload folder itself contains no README, inventory, subfolders, or alternate '
        'same-name packages. Packages passed structural checks; live account import and runtime behavior were not tested.\n'
    ).encode()
    summary['claude_flat_tools_and_writing'] = len(flat_entries)
    return generated, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    generated, summary = outputs()
    for path, data in generated.items():
        if path.exists():
            assert path.read_bytes() == data, 'Existing batch differs; preserved: ' + str(path)
        else:
            assert not args.check, 'Missing output: ' + str(path)
    if not args.check:
        for path, data in generated.items():
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
