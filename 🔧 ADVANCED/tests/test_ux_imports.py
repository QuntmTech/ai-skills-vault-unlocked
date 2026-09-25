import ast
import json
import sys
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_upload_batches as batches
from skillverse import frontmatter

class UXImportsTests(unittest.TestCase):
    def test_eight_uploads_and_resources(self):
        rows=json.loads((batches.ROOT/'🔧 ADVANCED/metadata/easy-library.json').read_text())['entries']
        entries=[e for e in rows if e.get('collection')=='UX design additions — 2026-09-25']
        self.assertEqual(len(entries),8)
        names=set()
        for e in entries:
            with zipfile.ZipFile(batches.ROOT/e['zip']) as z:
                self.assertIsNone(z.testzip())
                members=z.namelist()
                self.assertFalse(any('.claude-plugin' in n for n in members))
                entrypoints=[n for n in members if n.endswith('/SKILL.md')]
                self.assertEqual(len(entrypoints),1)
                text=z.read(entrypoints[0]).decode()
                meta,_=frontmatter(text)
                self.assertTrue(meta['name'].startswith('vault-'))
                self.assertNotIn(meta['name'],names)
                names.add(meta['name'])
                self.assertNotIn('CLAUDE_PLUGIN_ROOT',text)
                self.assertIn(meta['name']+'/LICENSE',members)
                self.assertIn(meta['name']+'/UPSTREAM-SKILL.md',members)
                if 'pro-max' in meta['name']:
                    self.assertIn(meta['name']+'/scripts/search.py',members)
                    self.assertTrue(any('/data/' in n and n.endswith('.csv') for n in members))
                    for n in members:
                        if n.endswith('.py'): ast.parse(z.read(n).decode(),filename=n)
    def test_upload_batch_copies_unchanged(self):
        for p,data in batches.outputs().items():
            self.assertEqual(p.read_bytes(),data)

if __name__=='__main__': unittest.main()
