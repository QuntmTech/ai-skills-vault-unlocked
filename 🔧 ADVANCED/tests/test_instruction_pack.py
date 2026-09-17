import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_instruction_pack as pack


class InstructionPackTests(unittest.TestCase):
    def test_current_documents_pass_and_core_is_short(self):
        outputs = pack.instruction_outputs()
        audit = json.loads(outputs[pack.ROOT / "metadata/instruction-pack-audit.json"])
        self.assertLessEqual(audit["core_word_count"], 500)
        self.assertFalse(audit["native_skill"])
        self.assertFalse(audit["private_source_files_included"])

    def test_combined_contains_complete_sources(self):
        outputs = pack.instruction_outputs()
        folder = pack.ROOT / "project-instructions"
        combined = outputs[folder / pack.COMBINED]
        for name in ("PROJECT-INSTRUCTIONS.md", "PROJECT-HANDBOOK.md"):
            self.assertIn((folder / name).read_text().strip(), combined)

    def test_privacy_patterns_use_synthetic_data(self):
        values = ("person" + "@" + "example.invalid",
                  "/" + "Users/" + "sample-user/project",
                  "https://" + "sample:password@" + "example.invalid",
                  "192." + "0.2.1",
                  "555" + "-010-1234")
        for value in values:
            with self.subTest(value_type=type(value).__name__):
                self.assertTrue(pack.privacy_errors(value))

    def test_context_placeholders_are_not_secrets(self):
        self.assertEqual(pack.privacy_errors("[PROJECT_NAME] [VERIFIED_SUMMARY]"), [])

    def test_private_identifier_is_case_insensitive(self):
        self.assertIn("private identifier", pack.privacy_errors("Private Example", ("private example",)))

    def test_zip_allowlist_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "project-instructions"
            folder.mkdir()
            for name in pack.FILES:
                (folder / name).write_text((pack.ROOT / "project-instructions" / name).read_text())
            (folder / "PRIVATE-CONTEXT.md").write_text("This must not enter the archive.")
            path = pack.package(root)
            with zipfile.ZipFile(path) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(set(archive.namelist()), {"project-compass/" + n for n in (*pack.FILES, pack.COMBINED)})
            original = path.read_bytes()
            with self.assertRaises(FileExistsError):
                pack.package(root)
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
