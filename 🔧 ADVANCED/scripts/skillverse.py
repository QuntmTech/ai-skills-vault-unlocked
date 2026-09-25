#!/usr/bin/env python3
"""Inspect and package selected skills. Never execute their contents."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".DS_Store", "__pycache__", ".git", "node_modules"}
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
CLAUDE_NAME_ALIASES = {
    "claude-api": "anthropic-api",
    "claude-devfleet": "agent-devfleet",
}


def contained(root, relative):
    rel = PurePosixPath(relative)
    if rel.is_absolute() or ".." in rel.parts or "\\" in relative:
        raise ValueError("Unsafe relative path")
    candidate = root / relative
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError("Path escapes repository")
    return candidate


def frontmatter(text):
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if not match:
        raise ValueError("Missing YAML frontmatter")
    try:
        meta = yaml.safe_load(match[1])
    except yaml.YAMLError as exc:
        raise ValueError("Invalid YAML frontmatter") from exc
    if not isinstance(meta, dict):
        raise ValueError("Frontmatter must be a mapping")
    return meta, text[match.end():]


def package_files(folder):
    files = []
    for path in sorted(folder.rglob("*")):
        rel = path.relative_to(folder)
        if any(part in SKIP for part in rel.parts) or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError("Symlink requires manual review: " + rel.as_posix())
        if path.is_file():
            if any(part.startswith(".env") and part != ".env.example" for part in rel.parts):
                raise ValueError("Environment file requires review: " + rel.as_posix())
            files.append(path)
    return files


def inspect(entry, root=ROOT):
    source = contained(root, entry["path"])
    text = source.read_text(encoding="utf-8")
    result = {"id": entry["id"], "path": entry["path"], "type": entry["type"],
              "label": entry["label"], "issues": [], "signals": [],
              "license_evidence": [], "publication": "review-required"}
    if entry["type"] != "skill":
        result["format"] = "command-only"
        result["issues"].append("Slash command; not a standalone skill")
        result["package_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        return result
    files = package_files(source.parent)
    digest = hashlib.sha256()
    for file in files:
        digest.update(file.relative_to(source.parent).as_posix().encode() + b"\0")
        digest.update(hashlib.sha256(file.read_bytes()).digest())
    result.update(package_sha256=digest.hexdigest(), file_count=len(files),
                  bytes=sum(f.stat().st_size for f in files))
    try:
        meta, body = frontmatter(text)
    except ValueError as exc:
        result["format"] = "needs-repair"
        result["issues"].append(str(exc))
        return result
    name = meta.get("name")
    description = meta.get("description")
    if not isinstance(name, str) or not NAME.fullmatch(name) or len(name) > 64:
        result["issues"].append("Name needs portable normalization")
    if not isinstance(description, str) or not description.strip():
        result["issues"].append("Missing description")
    elif len(" ".join(description.split())) > 200:
        result["signals"].append("Claude upload description will be shortened; full text retained")
    if meta.get("license"):
        result["license_evidence"].append({"frontmatter": str(meta["license"])})
    # Search within this package and its collection, never inherit this repo's license.
    parent = source.parent
    boundary = root / Path(entry["path"]).parts[0]
    while parent != boundary and parent != root:
        for file in sorted(parent.iterdir()):
            if file.is_file() and file.name.lower().startswith(("license", "copying", "notice")):
                result["license_evidence"].append({"file": file.relative_to(root).as_posix()})
        parent = parent.parent
    signals = (
        (r"\bmcp\b|mcp__", "MCP/tool connection mentioned"),
        (r"CLAUDE_PLUGIN_ROOT|CODEX_HOME|/mnt/|/Users/|~/(?:\.claude|\.codex)", "Host-specific paths mentioned"),
        (r"\b(?:Bash|Read|Write|Edit|AskUserQuestion|TodoWrite|Task)\b", "Agent tools mentioned"),
        (r"\b(?:API_KEY|access.token|api.key)\b", "Credentials/service setup mentioned"),
    )
    for pattern, label in signals:
        if re.search(pattern, text, re.I):
            result["signals"].append(label)
    if any(f.suffix in {".py", ".sh", ".js", ".ts", ".mjs", ".ps1"} for f in files):
        result["signals"].append("Executable code included; not executed or behavior-tested")
    if any(f.name == "SKILL.md" and f != source for f in files):
        result["signals"].append("Nested skill variant included; review before upload")
    missing = []
    # Code examples aren't links to package resources.
    prose = re.sub(r"(?ms)^\s*(```|~~~).*?^\s*\1[^\n]*$", "", body)
    prose = re.sub(r"`[^`\n]*`", "", prose)
    for link in re.findall(r"\]\(([^\s)]+)(?:\s+[^)]*)?\)", prose):
        url = urlsplit(link)
        if url.scheme or url.netloc or not url.path or link.startswith(("#", "/")):
            continue
        path = source.parent / unquote(url.path)
        if not path.resolve().is_relative_to(source.parent.resolve()) or not path.exists():
            missing.append(link)
    result["missing_local_links"] = sorted(set(missing))
    if missing:
        result["issues"].append("Missing/outside-package Markdown links need review")
    result["format"] = "needs-review" if result["issues"] else "structurally-valid"
    return result


def catalog(root=ROOT):
    return json.loads((root / "metadata/catalog.json").read_text())["entries"]


def export(entry, target, out, root=ROOT):
    report = inspect(entry, root)
    if entry["type"] != "skill":
        raise ValueError("Commands stay separate; use the command file in Claude Code")
    source = contained(root, entry["path"])
    meta, body = frontmatter(source.read_text())
    if report.get("missing_local_links"):
        raise ValueError("Resolve missing/outside-package Markdown links before exporting")
    if not isinstance(meta.get("description"), str) or not meta["description"].strip():
        raise ValueError("Provide a meaningful description before export")
    original_meta = dict(meta)
    name = re.sub(r"[^a-z0-9]+", "-", str(meta.get("name") or source.parent.name).lower()).strip("-")[:64].rstrip("-")
    if not name:
        raise ValueError("Cannot derive a portable name")
    meta["name"] = name
    changes = []
    if meta != original_meta:
        changes.append("Normalized or supplied skill name")
    if target == "claude":
        if "claude" in name:
            replacement = CLAUDE_NAME_ALIASES.get(name)
            if not replacement:
                raise ValueError("Claude upload name contains reserved word: " + name)
            name = replacement
            meta["name"] = name
            changes.append("Replaced a Claude-reserved internal skill name")
        desc = " ".join(meta["description"].split())
        if len(desc) > 200:
            meta["description"] = desc[:197].rsplit(" ", 1)[0] + "..."
            body = "## Full original description\n\n" + original_meta["description"].strip() + "\n\n" + body
            changes.append("Shortened discovery description to 200 characters; full description retained in body")
    skill = "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n" + body
    report.update(target=target, normalization=changes, original_metadata=original_meta,
                  warning="Structure only; not an import, runtime, security or redistribution approval")
    if out.is_symlink():
        raise ValueError("Output directory cannot be a symlink")
    if out.resolve().is_relative_to((root / "skills").resolve()) or out.resolve().is_relative_to((root / "commands").resolve()):
        raise ValueError("Output must not be inside source collections")
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{entry['id']:04d}-{name}-{target}"
    zip_path, report_path = out / (stem + ".zip"), out / (stem + ".json")
    prompt_path = out / (stem + "-reference.md")
    if any(p.exists() or p.is_symlink() for p in (zip_path, report_path, prompt_path)):
        raise ValueError("Export already exists; choose a new output folder")
    files = package_files(source.parent)
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            rel = file.relative_to(source.parent).as_posix()
            if target == "claude" and file != source and (
                file.name == "SKILL.md" or ".claude-plugin" in file.relative_to(source.parent).parts
            ):
                continue
            info = zipfile.ZipInfo(name + "/" + rel, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if file.stat().st_mode & 0o111 else 0o100644) << 16
            archive.writestr(info, skill.encode() if file == source else file.read_bytes())
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    prompt_path.write_text(
        "# Reference copy — " + name + "\n\n"
        "This is a reading/copy-paste aid, not an installed skill. It does not include "
        "supporting files or grant access to tools. Review the ZIP and audit report "
        "before using this workflow.\n\n" + skill)
    return zip_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    search = commands.add_parser("search")
    search.add_argument("query")
    show = commands.add_parser("show")
    show.add_argument("id", type=int)
    package = commands.add_parser("export")
    package.add_argument("id", type=int)
    package.add_argument("--target", choices=["claude", "portable"], default="portable")
    package.add_argument("--out", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    entries = catalog()
    if args.action == "search":
        for item in entries:
            if args.query.lower() in (item["label"] + " " + item["description"]).lower():
                print(f"{item['id']:4}  {item['type']:7} {item['label']}  [{item['collection']}]")
        return 0
    entry = next((e for e in entries if e["id"] == args.id), None)
    if entry is None:
        parser.error("Unknown catalog ID")
    if args.action == "show":
        print(json.dumps(inspect(entry), indent=2, ensure_ascii=False))
    else:
        print(export(entry, args.target, args.out))
        print("Read the neighboring JSON report before use. No account was modified.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
