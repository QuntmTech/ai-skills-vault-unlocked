"""Check source provenance and dependency packaging without executing imports."""
import hashlib
import json
import re
import sys
import unittest
import zipfile
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_easy_library as easy
from skillverse import frontmatter


class CommunityImportsTests(unittest.TestCase):
    def test_seventeen_pinned_packages_and_original_bytes(self):
        imports = json.loads((easy.ROOT / 'metadata/community-imports.json').read_text())['entries']
        self.assertEqual(len(imports), 17)
        for path, info in imports.items():
            folder = (easy.ROOT / path).parent
            origin = json.loads((folder / 'UPSTREAM.json').read_text())
            self.assertRegex(origin['commit'], r'^[a-f0-9]{40}$')
            self.assertEqual(origin['commit'], info['commit'])
            self.assertTrue((folder / 'LICENSE').exists())
            for rel, expected in origin['upstream_files_sha256'].items():
                original = folder / rel
                if '/xcode/' in path and rel == 'SKILL.md':
                    original = folder / 'UPSTREAM-SKILL.md'
                self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), expected, str(original))

    def test_all_new_packages_visible_and_requirements_propagated(self):
        imports = json.loads((easy.ROOT / 'metadata/community-imports.json').read_text())['entries']
        rows = {r['path']: r for r in json.loads(easy.MANIFEST.read_text())['entries']}
        for path, info in imports.items():
            row = rows[path]
            self.assertEqual(row['category'], info['category'])
            self.assertEqual(row['subcategory'], info['subcategory'])
            self.assertTrue(row['zip'])
            self.assertTrue(row['chatgpt_reference'])
            self.assertTrue(set(info['setup_notes']).issubset(row['signals']))
            self.assertIn('/' + info['subcategory'] + '/', row['folder'])

    def test_xcode_companions_have_resolvable_workflow_links_in_zips(self):
        rows = json.loads(easy.MANIFEST.read_text())['entries']
        for row in rows:
            if not row['path'].startswith('skills/community/xcode/'):
                continue
            with zipfile.ZipFile(easy.VAULT / row['zip']) as z:
                names = set(z.namelist())
                root = next(iter(names)).split('/')[0]
                self.assertEqual(sum(n.endswith('/REFERENCE.md') for n in names), 6)
                for n in names:
                    if n.endswith('/SKILL.md') or n.endswith('/REFERENCE.md'):
                        text = z.read(n).decode()
                        for link in re.findall(r'\]\(([^)]+)\)', text):
                            if '://' in link or link.startswith('#'):
                                continue
                            import posixpath
                            target = posixpath.normpath(posixpath.join(posixpath.dirname(n), unquote(link.split('#')[0])))
                            self.assertIn(target, names, f'{n}: {link}')
                self.assertIn(root + '/UPSTREAM-SKILL.md', names)

    def test_workflow_adapter_never_claims_upload_is_installation(self):
        path = easy.ROOT / 'skills/community/security/insecure-defaults/SKILL.md'
        text = path.read_text()
        meta, _ = frontmatter(text)
        self.assertTrue(meta['disable-model-invocation'])
        self.assertIn('A ZIP upload alone does not register the workflow', text)
        self.assertIn('CC-BY-SA-4.0', text)


if __name__ == '__main__':
    unittest.main()
