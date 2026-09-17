#!/usr/bin/env python3
"""Test every skill's two export formats without running any collected code."""
import argparse
import hashlib
import json
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

from skillverse import ROOT, catalog, export, frontmatter, package_files


def audit():
    outcomes = []
    for entry in catalog():
        if entry["type"] != "skill":
            continue
        folder = (ROOT / entry["path"]).parent
        files = package_files(folder)
        before = {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        for target in ("claude", "portable"):
            result = {"id": entry["id"], "target": target}
            with tempfile.TemporaryDirectory(prefix="skillverse-export-check-") as scratch:
                try:
                    archive_path = export(entry, target, Path(scratch), ROOT)
                except ValueError as exc:
                    result.update(status="blocked", reason=str(exc))
                else:
                    with zipfile.ZipFile(archive_path) as archive:
                        assert archive.testzip() is None, "ZIP integrity failed"
                        names = archive.namelist()
                        roots = {n.split("/")[0] for n in names}
                        assert len(roots) == 1, "Expected exactly one top-level skill folder"
                        prefix = next(iter(roots)) + "/"
                        assert {n[len(prefix):] for n in names} == set(before), "Missing or added asset"
                        for name in names:
                            rel = name[len(prefix):]
                            data = archive.read(name)
                            if rel == "SKILL.md":
                                meta, _ = frontmatter(data.decode())
                                assert meta["name"] == prefix[:-1]
                                assert meta["description"]
                                if target == "claude":
                                    assert len(meta["description"]) <= 200
                            else:
                                assert hashlib.sha256(data).hexdigest() == before[rel], "Resource changed"
                    result["status"] = "passed"
            assert before == {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}, "Source changed"
            outcomes.append(result)
    return {
        "schema_version": 1,
        "scope": "ZIP integrity, layout, asset preservation and source preservation; not live imports",
        "counts": dict(sorted(Counter(o["status"] for o in outcomes).items())),
        "entries": outcomes,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = audit()
    content = json.dumps(report, indent=2) + "\n"
    path = ROOT / "metadata/export-audit.json"
    if args.check:
        if not path.exists() or path.read_text() != content:
            raise SystemExit("Export audit changed. Rebuild and review it.")
    else:
        path.write_text(content)
    print(json.dumps(report["counts"]))
    print("Blocked packages remain in the vault; they were not silently repaired or removed.")


if __name__ == "__main__":
    main()
