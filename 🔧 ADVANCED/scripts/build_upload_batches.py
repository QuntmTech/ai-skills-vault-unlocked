#!/usr/bin/env python3
"""Create flat, verified copies of existing ZIPs for the requested upload batches."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def outputs():
    rows = json.loads((ROOT/'🔧 ADVANCED/metadata/easy-library.json').read_text())['entries']
    batches = {
        '🎨 UX UI Design — Claude Uploads': [e for e in rows if e.get('collection') == 'UX design additions — 2026-09-25'],
        '🔀 GitHub & Code Review — Claude Uploads': [e for e in rows if e.get('subcategory') == '🔀 GitHub & Code Review'],
    }
    assert [len(v) for v in batches.values()] == [8, 11]
    generated = {}
    for title, entries in batches.items():
        folder = ROOT/'📤 UPLOAD BATCHES'/title
        checksums, inventory = [], []
        for e in entries:
            assert e.get('zip'), e['label']
            src = ROOT/e['zip']
            with zipfile.ZipFile(src) as z:
                assert z.testzip() is None
                assert not any('.claude-plugin' in n for n in z.namelist())
            dest = folder/(e['display_name'].replace('/',' - ')+'.zip')
            assert dest not in generated
            data = src.read_bytes()
            generated[dest] = data
            checksums.append(hashlib.sha256(data).hexdigest()+'  '+dest.name)
            inventory.append({'file':dest.name,'source':e['zip'],'status':e['status'],'requirements':e['signals']})
        generated[folder/'SHA256SUMS.txt'] = ('\n'.join(checksums)+'\n').encode()
        generated[folder/'Requirements.json'] = (json.dumps(inventory,indent=2,ensure_ascii=False)+'\n').encode()
        generated[folder/'READ ME.md'] = (f'# {title}\n\n{len(entries)} individual skill ZIPs. Select the ZIP files together in Claude’s skill uploader if your interface supports multiple selection. Leave individual ZIPs zipped; do not upload this entire folder as one skill.\n\n'
            'Original packages remain in their category folders. These are byte-identical copies with readable filenames. Check Requirements.json for each skill. Archive integrity does not prove successful Claude import or runtime behavior. If Claude reports an existing internal name, skip it unless you intentionally want to replace that installed skill.\n\n'
            'GitHub/code-review workflows may need repository access, GitHub authentication, shell tools or Claude Code; uploading a skill does not grant those capabilities. UI UX Pro Max requires code execution/Python for search and provides a reference-only fallback without it. No account imports were performed.\n').encode()
    return generated

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    generated=outputs()
    for path,data in generated.items():
        if path.exists():
            assert path.read_bytes()==data, 'Existing batch differs; preserved: '+str(path)
        else:
            assert not args.check, 'Missing output: '+str(path)
    if not args.check:
        for path,data in generated.items():
            if not path.exists():
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(data)
    print('Verified 8 UX/UI ZIPs and 11 GitHub/code-review ZIPs; originals unchanged.')

if __name__=='__main__': main()
