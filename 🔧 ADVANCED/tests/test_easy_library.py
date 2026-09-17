import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_easy_library as easy
from skillverse import catalog


class EasyLibraryTests(unittest.TestCase):
    def test_all_source_ids_accounted_for_once(self):
        ids = [i for e in json.loads(easy.MANIFEST.read_text())["entries"] for i in e["copies"]]
        self.assertEqual(sorted(ids), sorted(e["id"] for e in catalog()))
        self.assertEqual(len(ids), len(set(ids)))

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

    def test_escaping_and_setup_flags(self):
        self.assertNotIn("</script>", easy.safe_payload({"label": "</script><script>alert(1)</script>"}))
        self.assertTrue(easy.needs_setup({"signals": ["MCP/tool connection mentioned"]}))
        self.assertFalse(easy.needs_setup({"signals": []}))
        self.assertEqual(easy.category("frontend-design"), "Design & Media")

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
