import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import skillverse as sv


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / "skills/demo"
        self.folder.mkdir(parents=True)
        self.source = self.folder / "SKILL.md"
        self.source.write_text("---\nname: demo\ndescription: Test a small workflow.\n---\n\nDo the task.\n")
        self.entry = {"id": 1, "path": "skills/demo/SKILL.md", "type": "skill", "label": "demo"}
        self.out = self.root / "dist"

    def export(self, target="portable", out=None):
        return sv.export(self.entry, target, out or self.out, self.root)

    def test_preserves_source_and_assets(self):
        (self.folder / "assets").mkdir()
        asset = self.folder / "assets/example.bin"
        asset.write_bytes(bytes(range(256)))
        before = self.source.read_bytes()
        path = self.export()
        with zipfile.ZipFile(path) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(z.read("demo/assets/example.bin"), asset.read_bytes())
            self.assertIn("demo/SKILL.md", z.namelist())
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(len(list(self.out.glob("*reference.md"))), 1)

    def test_refuses_overwrite(self):
        path = self.export()
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            self.export()
        self.assertEqual(path.read_bytes(), before)

    def test_deterministic_archives(self):
        first = self.export().read_bytes()
        second = self.export(out=self.root / "second").read_bytes()
        self.assertEqual(first, second)

    def test_rejects_traversal(self):
        for value in ("../secret", "/etc/passwd", "skills/../../secret", "skills\\secret"):
            with self.assertRaises(ValueError):
                sv.contained(self.root, value)

    def test_rejects_symlink_input(self):
        (self.folder / "link").symlink_to(self.source)
        with self.assertRaises(ValueError):
            self.export()

    def test_rejects_symlink_output(self):
        actual = self.root / "actual"
        actual.mkdir()
        self.out.symlink_to(actual)
        with self.assertRaises(ValueError):
            self.export()

    def test_rejects_output_inside_sources(self):
        with self.assertRaises(ValueError):
            self.export(out=self.folder / "output")

    def test_rejects_environment_file(self):
        (self.folder / ".env").write_text("EXAMPLE=value")
        with self.assertRaises(ValueError):
            self.export()

    def test_ignores_os_junk_without_deleting(self):
        junk = self.folder / ".DS_Store"
        junk.write_bytes(b"test")
        with zipfile.ZipFile(self.export()) as z:
            self.assertNotIn("demo/.DS_Store", z.namelist())
        self.assertTrue(junk.exists())

    def test_normalizes_missing_name_in_export_only(self):
        self.source.write_text("---\ndescription: Do a task.\n---\nBody.")
        with zipfile.ZipFile(self.export()) as z:
            meta, _ = sv.frontmatter(z.read("demo/SKILL.md").decode())
            self.assertEqual(meta["name"], "demo")
        self.assertNotIn("name:", self.source.read_text())

    def test_claude_description_retains_full_original(self):
        description = "A detailed description of a workflow. " * 10
        self.source.write_text("---\nname: demo\ndescription: " + description + "\n---\nBody.")
        with zipfile.ZipFile(self.export("claude")) as z:
            meta, body = sv.frontmatter(z.read("demo/SKILL.md").decode())
            self.assertLessEqual(len(meta["description"]), 200)
            self.assertIn(description.strip(), body)

    def test_claude_export_replaces_reserved_internal_name(self):
        self.source.write_text(
            "---\nname: claude-api\ndescription: Explain an API workflow.\n---\nBody."
        )
        with zipfile.ZipFile(self.export("claude")) as archive:
            self.assertIn("anthropic-api/SKILL.md", archive.namelist())
            meta, _ = sv.frontmatter(archive.read("anthropic-api/SKILL.md").decode())
            self.assertEqual(meta["name"], "anthropic-api")

    def test_claude_export_omits_nested_entrypoints_and_plugin_manifest(self):
        nested = self.folder / "upstream/SKILL.md"
        nested.parent.mkdir()
        nested.write_text("---\nname: upstream\ndescription: Preserved source.\n---\nBody.")
        manifest = self.folder / ".claude-plugin/plugin.json"
        manifest.parent.mkdir()
        manifest.write_text('{"name":"demo"}\n')
        with zipfile.ZipFile(self.export("claude")) as archive:
            self.assertNotIn("demo/upstream/SKILL.md", archive.namelist())
            self.assertNotIn("demo/.claude-plugin/plugin.json", archive.namelist())
            self.assertIn("demo/SKILL.md", archive.namelist())
        self.assertTrue(nested.exists())
        self.assertTrue(manifest.exists())

    def test_claude_export_omits_nested_zip_without_deleting_source(self):
        nested_archive = self.folder / "browser.zip"
        nested_archive.write_bytes(b"nested archive placeholder")
        with zipfile.ZipFile(self.export("claude")) as archive:
            self.assertNotIn("demo/browser.zip", archive.namelist())
            self.assertIn("demo/SKILL.md", archive.namelist())
        self.assertTrue(nested_archive.exists())

    def test_keeps_policy_metadata_and_agent_file(self):
        self.source.write_text("---\nname: demo\ndescription: Do a task.\ndisable-model-invocation: true\n---\nBody.")
        (self.folder / "agents").mkdir()
        policy = self.folder / "agents/openai.yaml"
        policy.write_text("policy:\n  allow_implicit_invocation: false\n")
        with zipfile.ZipFile(self.export()) as z:
            meta, _ = sv.frontmatter(z.read("demo/SKILL.md").decode())
            self.assertTrue(meta["disable-model-invocation"])
            self.assertEqual(z.read("demo/agents/openai.yaml"), policy.read_bytes())

    def test_invalid_yaml_fails(self):
        self.source.write_text("---\nname: [\n---\nBody.")
        with self.assertRaises(ValueError):
            self.export()

    def test_missing_description_fails(self):
        self.source.write_text("---\nname: demo\n---\nBody.")
        with self.assertRaises(ValueError):
            self.export()

    def test_missing_resource_fails(self):
        self.source.write_text(self.source.read_text() + "\n[Read reference](references/missing.md)")
        with self.assertRaises(ValueError):
            self.export()

    def test_code_examples_not_misread_as_links(self):
        self.source.write_text(self.source.read_text() + "\n```md\n[Example](url)\n```\n")
        self.assertEqual(sv.inspect(self.entry, self.root)["missing_local_links"], [])

    def test_present_asset_link_succeeds(self):
        (self.folder / "guide.md").write_text("Guide")
        self.source.write_text(self.source.read_text() + "\n[Guide](guide.md)")
        self.export()

    def test_package_hash_detects_support_file_change(self):
        resource = self.folder / "guide.md"
        resource.write_text("Version 1")
        before = sv.inspect(self.entry, self.root)["package_sha256"]
        resource.write_text("Version 2")
        after = sv.inspect(self.entry, self.root)["package_sha256"]
        self.assertNotEqual(before, after)

    def test_commands_not_disguised_as_skills(self):
        self.entry["type"] = "command"
        with self.assertRaises(ValueError):
            self.export()

    def test_license_declaration_not_cleared(self):
        (self.folder / "LICENSE").write_text("License requiring review")
        report = sv.inspect(self.entry, self.root)
        self.assertEqual(report["publication"], "review-required")
        self.assertTrue(report["license_evidence"])


if __name__ == "__main__":
    unittest.main()
