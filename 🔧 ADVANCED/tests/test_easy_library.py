import json
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_easy_library as easy
from skillverse import catalog


class EasyLibraryTests(unittest.TestCase):
    def test_consistent_user_facing_names(self):
        self.assertEqual(easy.READY, '📦 CLAUDE')
        self.assertEqual(easy.CHATGPT, '💬 CHATGPT')
        self.assertEqual(easy.START, '🔎 BROWSE LIBRARY.html')
        self.assertTrue((easy.VAULT / easy.START).is_file())
        for folder in (easy.READY, easy.CHATGPT, easy.COPY, easy.SETUP):
            self.assertTrue((easy.VAULT / folder / 'README.md').is_file())
        for old in ('📦 READY FOR CLAUDE', '💬 START HERE — CHATGPT', '📍 START HERE.html'):
            self.assertFalse((easy.VAULT / old).exists())

    def test_all_source_ids_accounted_for_once(self):
        ids = [i for e in json.loads(easy.MANIFEST.read_text())["entries"] for i in e["copies"]]
        self.assertEqual(sorted(ids), sorted(e["id"] for e in catalog()))
        self.assertEqual(len(ids), len(set(ids)))

    def test_all_skills_front_facing_with_source_and_zip_together(self):
        rows = json.loads(easy.MANIFEST.read_text())['entries']
        for row in rows:
            folder = easy.VAULT / row['folder']
            self.assertTrue(folder.is_relative_to(easy.VAULT / easy.READY))
            self.assertTrue((easy.VAULT / row['guide']).is_file())
            original = easy.ROOT / row['path']
            paths = easy.package_files(original.parent) if row['type'] == 'skill' else [original]
            for source in paths:
                copy = folder / source.relative_to(original.parent)
                self.assertEqual(copy.read_bytes(), source.read_bytes(), str(copy))
            self.assertTrue((easy.VAULT / row['front_source']).is_file())
            if row['zip']:
                self.assertEqual((easy.VAULT / row['zip']).parent, folder)
            else:
                self.assertFalse(list(folder.glob('*.zip')))
        self.assertEqual(sum(bool(row['zip']) for row in rows), 472)

    def test_zip_links_integrity_and_entrypoint(self):
        for row in json.loads(easy.MANIFEST.read_text())["entries"]:
            self.assertTrue((easy.VAULT / row["source"]).is_file())
            if not row["zip"]:
                continue
            with zipfile.ZipFile(easy.VAULT / row["zip"]) as archive:
                self.assertIsNone(archive.testzip())
                prefixes = {p.split("/")[0] for p in archive.namelist()}
                self.assertEqual(len(prefixes), 1)
                self.assertIn(next(iter(prefixes)) + "/SKILL.md", archive.namelist())
            self.assertTrue((easy.VAULT / row["reference"]).is_file())

    def test_artifact_hashes_match(self):
        for path, expected in json.loads(easy.MANIFEST.read_text())["artifacts"].items():
            self.assertEqual(easy.digest((easy.VAULT / path).read_bytes()), expected, path)

    def test_chatgpt_references_preserve_text_and_warnings(self):
        manifest = json.loads(easy.MANIFEST.read_text())
        references = [r for r in manifest['entries'] if r.get('chatgpt_reference')]
        self.assertEqual(len(references), manifest['summary']['zip_count'])
        for row in references:
            copy = (easy.VAULT / row['chatgpt_reference']).read_bytes()
            self.assertTrue(copy.endswith((easy.VAULT / row['reference']).read_bytes()))
            self.assertIn(b'not a native skill installation', copy)
            self.assertIn(b'No live ChatGPT test is claimed', copy)
            for signal in row['signals']:
                self.assertIn(signal.encode(), copy)
            document = easy.VAULT / row['chatgpt_reference']
            match = re.search(r'\[Preserved source and supporting files\]\(([^)]+)\)',
                              copy.decode(errors='replace'))
            self.assertIsNotNone(match, str(document))
            href = match.group(1)
            self.assertTrue((document.parent / unquote(href)).resolve().exists(),
                            f'Broken ChatGPT source link: {document} -> {href}')

    def test_chatgpt_bundle_matches_documents(self):
        folder = easy.VAULT / easy.CHATGPT
        docs = list(folder.rglob('*.md'))
        self.assertTrue((folder / 'README.md').is_file())
        self.assertTrue((folder / 'Project Instructions/PROJECT-INSTRUCTIONS.md').is_file())
        with zipfile.ZipFile(folder / 'ChatGPT-Reference-Pack.zip') as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(len(archive.namelist()), len(docs))
            for doc in docs:
                self.assertEqual(archive.read('ChatGPT Reference Pack/' + doc.relative_to(folder).as_posix()), doc.read_bytes())

    def test_modified_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "test.md"
            target.write_bytes(b"user changes")
            with self.assertRaises(ValueError):
                easy.apply_outputs({target: b"new output"}, {"test.md": easy.digest(b"old output")}, root)
            self.assertEqual(target.read_bytes(), b"user changes")

    def test_managed_update_and_idempotence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "test.md"
            easy.apply_outputs({target: b"old"}, {}, root)
            easy.apply_outputs({target: b"new"}, {"test.md": easy.digest(b"old")}, root)
            easy.apply_outputs({target: b"new"}, {}, root, check=True)
            with self.assertRaises(ValueError):
                easy.apply_outputs({target: b"stale"}, {}, root, check=True)

    def test_interrupted_retirement_is_safe_to_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = Path(easy.READY) / "Old Topic" / "retired.md"
            old = root / rel
            old.parent.mkdir(parents=True)
            old.write_bytes(b"managed output")
            old_hash = easy.digest(old.read_bytes())
            archived = root / "🔧 ADVANCED/dist/previous-easy-library" / old_hash / rel
            archived.parent.mkdir(parents=True)
            archived.write_bytes(b"managed output")
            replacement = root / easy.READY / "New Topic" / "current.md"

            easy.apply_outputs({replacement: b"new output"},
                               {rel.as_posix(): old_hash}, root)

            self.assertFalse(old.exists())
            self.assertEqual(archived.read_bytes(), b"managed output")
            self.assertEqual(replacement.read_bytes(), b"new output")

    def test_escaping_and_setup_flags(self):
        self.assertNotIn("</script>", easy.safe_payload({"label": "</script><script>alert(1)</script>"}))
        self.assertTrue(easy.needs_setup({"signals": ["MCP/tool connection mentioned"]}))
        self.assertFalse(easy.needs_setup({"signals": []}))
        self.assertEqual(easy.category("frontend-design"), "Design & Media")

    def test_coding_skills_have_readable_subcategories_and_names(self):
        rows = [row for row in json.loads(easy.MANIFEST.read_text())['entries']
                if row['category'] == 'Coding & Development']
        self.assertEqual(len(rows), 183)
        self.assertGreaterEqual(len({row['subcategory'] for row in rows}), 10)
        for row in rows:
            parts = Path(row['folder']).parts
            self.assertEqual(parts[0:2], (easy.READY, 'Coding & Development'))
            self.assertEqual(parts[2], row['subcategory'])
            self.assertEqual(parts[3].split(' [variant ')[0], row['display_name'])
            self.assertNotIn('-', row['display_name'])
        self.assertEqual(easy.friendly_name('mcp-server-patterns'), 'MCP Server Patterns')
        self.assertEqual(easy.coding_subcategory('python-testing'), '🧪 Testing & Debugging')
        self.assertEqual(easy.coding_subcategory('vercel:nextjs'), '🌐 Vercel Frontend & Next.js')

    def test_phase_one_topics_mirror_readable_subcategories(self):
        rows = json.loads(easy.MANIFEST.read_text())['entries']
        expected = {'Design & Media': 29, 'Writing & Documents': 19}
        for topic, count in expected.items():
            selected = [row for row in rows if row['category'] == topic]
            self.assertEqual(len(selected), count)
            self.assertGreaterEqual(len({row['subcategory'] for row in selected}), 5)
            for row in selected:
                self.assertEqual(Path(row['folder']).parts[0:2], (easy.READY, topic))
                self.assertEqual(Path(row['folder']).parts[2], row['subcategory'])
                if row.get('chatgpt_reference'):
                    chat = Path(row['chatgpt_reference'])
                    self.assertEqual(chat.parts[0:3], (easy.CHATGPT, 'Skill References', topic))
                    self.assertEqual(chat.parts[3], row['subcategory'])
                    self.assertTrue(chat.name.endswith('ChatGPT Reference.md'))

    def test_phase_two_topics_mirror_readable_subcategories(self):
        rows = json.loads(easy.MANIFEST.read_text())['entries']
        expected = {'Marketing & Business': 36, 'Research & Data': 25}
        for topic, count in expected.items():
            selected = [row for row in rows if row['category'] == topic]
            self.assertEqual(len(selected), count)
            self.assertGreaterEqual(len({row['subcategory'] for row in selected}), 7)
            for row in selected:
                self.assertEqual(Path(row['folder']).parts[0:2], (easy.READY, topic))
                self.assertEqual(Path(row['folder']).parts[2], row['subcategory'])
                if row.get('chatgpt_reference'):
                    chat = Path(row['chatgpt_reference'])
                    self.assertEqual(chat.parts[0:3], (easy.CHATGPT, 'Skill References', topic))
                    self.assertEqual(chat.parts[3], row['subcategory'])
                    self.assertTrue(chat.name.endswith('ChatGPT Reference.md'))
        self.assertEqual(easy.friendly_name('seo'), 'SEO')
        self.assertEqual(easy.friendly_name('hugging-face:hf-cli'), 'HF CLI')

    def test_phase_three_tools_mirror_readable_subcategories(self):
        rows = [row for row in json.loads(easy.MANIFEST.read_text())['entries']
                if row['category'] == 'Tools & Workflows']
        self.assertEqual(len(rows), 193)
        self.assertGreaterEqual(len({row['subcategory'] for row in rows}), 13)
        for row in rows:
            self.assertEqual(Path(row['folder']).parts[0:2],
                             (easy.READY, 'Tools & Workflows'))
            self.assertEqual(Path(row['folder']).parts[2], row['subcategory'])
            self.assertEqual(Path(row['folder']).parts[3].split(' [variant ')[0],
                             row['display_name'])
            if row.get('chatgpt_reference'):
                chat = Path(row['chatgpt_reference'])
                self.assertEqual(chat.parts[0:3],
                                 (easy.CHATGPT, 'Skill References', 'Tools & Workflows'))
                self.assertEqual(chat.parts[3], row['subcategory'])
                self.assertTrue(chat.name.endswith('ChatGPT Reference.md'))
        self.assertEqual(easy.friendly_name('enterprise-agent-ops'),
                         'Enterprise Agent Ops')
        self.assertEqual(easy.friendly_name('hipaa-compliance'),
                         'HIPAA Compliance')
        self.assertEqual(easy.tools_subcategory('stripe:stripe-best-practices'),
                         '💳 Payments & Billing')
        self.assertEqual(easy.tools_subcategory('claude-mem:weekly-digests'),
                         '🧠 Memory, Knowledge & Prompting')

    def test_rejects_symlink_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            actual = root / "actual"
            actual.mkdir()
            (root / "link").symlink_to(actual, target_is_directory=True)
            with self.assertRaises(ValueError):
                easy.apply_outputs({root / "link/test.md": b"data"}, {}, root)


if __name__ == "__main__":
    unittest.main()
