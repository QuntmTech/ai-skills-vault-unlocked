#!/usr/bin/env python3
"""Build only the allowlisted, generalized project-instruction compilation."""
import argparse
import hashlib
import json
import os
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "README.md",
    "PROJECT-INSTRUCTIONS.md",
    "PROJECT-HANDBOOK.md",
    "PROJECT-CONTEXT.template.md",
    "CURATION-NOTES.md",
    "QUALITY-CHECKS.md",
)
COMBINED = "COPY-PASTE-ALL.md"
PATTERNS = {
    "email address": re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I),
    "personal absolute path": re.compile(r"(?:/Users/|/home/|[A-Z]:\\Users\\)", re.I),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "token-like credential": re.compile(r"(?:sk-(?:proj-|ant-)?[\w-]{20,}|gh[pousr]_[\w]{25,}|github_pat_[\w]{20,})"),
    "credential-bearing URL": re.compile(r"https?://[^\s/@:]+:[^\s/@]+@"),
    "IPv4 address": re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)"),
    "phone-like number": re.compile(r"(?<!\w)(?:\+\d{1,3}[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\w)"),
}


def privacy_errors(text, private_terms=()):
    findings = [label for label, pattern in PATTERNS.items() if pattern.search(text)]
    if any(term and term.casefold() in text.casefold() for term in private_terms):
        findings.append("private identifier")
    return findings


def instruction_outputs(root=ROOT):
    folder = root / "project-instructions"
    content = {}
    for name in FILES:
        path = folder / name
        if path.is_symlink():
            raise ValueError("Instruction sources must not be symlinks")
        content[name] = path.read_text()
    private_terms = tuple(x for x in (os.environ.get("USER"), os.environ.get("LOGNAME")) if x and len(x) > 4)
    for name, text in content.items():
        errors = privacy_errors(text, private_terms)
        if errors:
            raise ValueError(name + ": " + ", ".join(errors))
    core_words = len(content["PROJECT-INSTRUCTIONS.md"].split())
    if core_words > 500:
        raise ValueError("Core instruction budget exceeded: 500 words")
    combined = (
        "# PROJECT COMPASS — Complete reference\n\n"
        "Use this instead of the separate core and handbook, not in addition to them. "
        "This is project guidance, not a native skill or plugin. Follow the host's "
        "instruction hierarchy and permission controls.\n\n"
        + content["PROJECT-INSTRUCTIONS.md"].rstrip() + "\n\n---\n\n"
        + content["PROJECT-HANDBOOK.md"].rstrip() + "\n"
    )
    audit = {
        "schema_version": 1,
        "scope": "New PROJECT COMPASS documents only; pattern checks are not a comprehensive privacy guarantee",
        "source_documents": len(FILES),
        "core_word_count": core_words,
        "common_identifier_patterns": "passed",
        "private_source_files_included": False,
        "native_skill": False,
        "sha256": {name: hashlib.sha256(text.encode()).hexdigest() for name, text in content.items()},
    }
    return {folder / COMBINED: combined, root / "metadata/instruction-pack-audit.json": json.dumps(audit, indent=2) + "\n"}


def package(root=ROOT):
    folder = root / "project-instructions"
    generated = instruction_outputs(root)
    output = root / "dist"
    if output.is_symlink():
        raise ValueError("Output directory must not be a symlink")
    output.mkdir(exist_ok=True)
    path = output / "project-compass-documents.zip"
    # Exclusive creation protects previous downloads; remove/rename only on explicit request.
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in (*FILES, COMBINED):
            data = generated[folder / name] if name == COMBINED else (folder / name).read_text()
            info = zipfile.ZipInfo("project-compass/" + name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data.encode())
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    for path, content in instruction_outputs().items():
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit("Generated instruction output is stale: " + path.name)
        else:
            path.write_text(content)
    if args.zip:
        print(package())
    print("Instruction pack checked; no original source library is copied.")


if __name__ == "__main__":
    main()
