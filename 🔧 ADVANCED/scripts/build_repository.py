#!/usr/bin/env python3
"""Build and validate public metadata without executing collected skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import os
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote
from skillverse import contained, frontmatter, inspect
from build_instruction_pack import instruction_outputs


ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "metadata"
CATALOG_JSON = METADATA / "catalog.json"
LEGACY_JSON = METADATA / "legacy-manifest.json"
CATALOG_MD = ROOT / "catalog" / "skills-catalog.md"
INVENTORY_JSON = METADATA / "inventory.json"
LICENSE_AUDIT_JSON = METADATA / "license-audit.json"

PATH_MAP = (
    ("/01 CC SWITCH SKILLS/01 Managed/", "skills/cc-switch/managed/"),
    ("/01 CC SWITCH SKILLS/02 Extra & Unmanaged/", "skills/cc-switch/community/"),
    ("/02 CODEX SKILLS/01 System/", "skills/codex/system/"),
    ("/02 CODEX SKILLS/02 Local/", "skills/codex/local/"),
    ("/02 CODEX SKILLS/03 Agent Skills/", "skills/codex/agent-skills/"),
    ("/02 CODEX SKILLS/04 Plugins/", "skills/codex/plugins/"),
    ("/03 CLAUDE SKILLS/01 Global/", "skills/claude/global/"),
    ("/03 CLAUDE SKILLS/02 Installed Plugins/", "skills/claude/plugins/"),
    ("/04 CLAUDE COMMANDS/01 Global Commands/", "commands/claude/global/"),
    ("/04 CLAUDE COMMANDS/02 Plugin Commands/", "commands/claude/plugins/"),
)

TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".py", ".js", ".mjs",
    ".cjs", ".ts", ".tsx", ".sh", ".ps1", ".pl", ".swift", ".toml",
    ".xml", ".xsd", ".html", ".css",
}

SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{30,})"),
    "Anthropic key": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "Google API key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "OpenAI key": re.compile(r"sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{40,}"),
    "Slack token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def map_legacy_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    for old, new in PATH_MAP:
        if old in normalized:
            return new + normalized.split(old, 1)[1]
    raise ValueError(f"cannot map legacy path: {value}")


def load_catalog() -> dict:
    if CATALOG_JSON.exists():
        data = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
        if data.get("schema_version") == 1:
            known = {e["path"] for e in data["entries"]}
            next_id = max(e["id"] for e in data["entries"]) + 1
            for path in sorted((ROOT / "skills").rglob("SKILL.md")):
                relative = path.relative_to(ROOT).as_posix()
                if relative not in known:
                    meta, _ = frontmatter(path.read_text())
                    data["entries"].append({
                        "id": next_id, "label": str(meta.get("name", path.parent.name)),
                        "type": "skill", "collection": "Additional nested skill variants",
                        "description": str(meta.get("description", "")), "path": relative,
                    })
                    next_id += 1
            data["entry_count"] = len(data["entries"])
            return data

    legacy = json.loads(LEGACY_JSON.read_text(encoding="utf-8"))
    entries = []
    for item in legacy["entries"]:
        entries.append(
            {
                "id": item["number"],
                "label": item["label"],
                "type": item["type"],
                "collection": item["section"],
                "description": item.get("description", ""),
                "path": map_legacy_path(item["vault_path"]),
            }
        )
    return {"schema_version": 1, "entry_count": len(entries), "entries": entries}


def catalog_markdown(catalog: dict) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in catalog["entries"]:
        grouped[item["collection"]].append(item)

    skill_count = sum(item["type"] == "skill" for item in catalog["entries"])
    command_count = sum(item["type"] == "command" for item in catalog["entries"])
    lines = [
        "# Skills and commands catalog",
        "",
        f"**{len(catalog['entries'])} source entries:** {skill_count} skills and {command_count} commands.",
        "",
        "Every link is repository-relative and can be opened directly on GitHub.",
        "Review a skill before installing or executing any included script.",
        "",
    ]
    for collection in sorted(grouped):
        items = sorted(grouped[collection], key=lambda item: item["label"].casefold())
        lines.extend([f"## {collection} ({len(items)})", ""])
        for item in items:
            link = "../" + quote(item["path"], safe="/")
            description = " ".join(item["description"].split()).replace("<", "&lt;").replace(">", "&gt;")
            suffix = f" — {description}" if description else ""
            lines.append(f"- [`{item['label']}`]({link}){suffix}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def license_for(path: Path) -> str | None:
    for candidate in sorted(path.parent.iterdir(), key=lambda p: p.name.casefold()):
        if candidate.is_file() and (
            candidate.name.casefold().startswith("license")
            or candidate.name.casefold().startswith("copying")
        ):
            return candidate.relative_to(ROOT).as_posix()
    return None


def build_inventory() -> tuple[dict, dict]:
    files = sorted((ROOT / "skills").rglob("SKILL.md"))
    files.extend(sorted((ROOT / "commands").rglob("*.md")))
    records = []
    status_counts: Counter[str] = Counter()
    unverified = []
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        license_path = license_for(path)
        license_status = "adjacent-license-found" if license_path else "no-adjacent-license"
        status_counts[license_status] += 1
        if not license_path:
            unverified.append(relative)
        records.append(
            {
                "type": "skill" if path.name == "SKILL.md" else "command",
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "license_status": license_status,
                "license_path": license_path,
            }
        )
    inventory = {
        "schema_version": 1,
        "entry_count": len(records),
        "skill_file_count": sum(r["type"] == "skill" for r in records),
        "command_file_count": sum(r["type"] == "command" for r in records),
        "entries": records,
    }
    audit = {
        "schema_version": 1,
        "scope": "SKILL.md and Claude command Markdown files",
        "counts": dict(sorted(status_counts.items())),
        "unverified_paths": unverified,
        "note": "Unverified means no adjacent LICENSE or COPYING file was found; it is not a legal conclusion.",
    }
    return inventory, audit


def json_text(value: dict) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def generated_outputs() -> dict[Path, str]:
    catalog = load_catalog()
    inventory, audit = build_inventory()
    packages = [inspect(entry, ROOT) for entry in catalog["entries"]]
    groups = defaultdict(list)
    for item in packages:
        groups[item["package_sha256"]].append(item["id"])
    report = {
        "schema_version": 1,
        "scope": "Every catalog entry, including nested skill variants; static checks only",
        "entry_count": len(packages),
        "unique_package_contents": len(groups),
        "exact_duplicate_groups": [ids for ids in groups.values() if len(ids) > 1],
        "format_counts": dict(sorted(Counter(p["format"] for p in packages).items())),
        "publication_status": "blocked-pending-provenance-and-license-review",
        "entries": packages,
    }
    public_rows = [{**e, **p} for e, p in zip(catalog["entries"], packages)]
    template = (ROOT / "scripts/catalog-template.html").read_text()
    payload = json.dumps(public_rows, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return {
        **instruction_outputs(ROOT),
        CATALOG_JSON: json_text(catalog),
        CATALOG_MD: catalog_markdown(catalog),
        INVENTORY_JSON: json_text(inventory),
        LICENSE_AUDIT_JSON: json_text(audit),
        METADATA / "package-audit.json": json_text(report),
        ROOT / "catalog/index.html": template.replace("__CATALOG_DATA__", payload),
    }


def safety_errors(catalog: dict) -> list[str]:
    errors = []
    ids = [item["id"] for item in catalog["entries"]]
    paths = [item["path"] for item in catalog["entries"]]
    if len(set(ids)) != len(ids) or len(set(paths)) != len(paths):
        errors.append("catalog IDs and paths must be unique")
    if catalog["entry_count"] != len(ids):
        errors.append("catalog entry count mismatch")
    for item in catalog["entries"]:
        try:
            path = contained(ROOT, item["path"])
        except ValueError:
            errors.append("unsafe catalog path")
            continue
        if not path.is_file():
            errors.append(f"missing catalog target: {item['path']}")

    forbidden_names = {".DS_Store", "Thumbs.db"}
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(part in {".git", ".venv", "__pycache__", "dist", ".audit-work"} for part in relative.parts):
            continue
        if path.name in forbidden_names or path.suffix == ".pyc":
            continue  # OS junk is ignored, never packaged or deleted.
        if path.is_symlink():
            errors.append(f"symlink requires review: {relative}")
            continue
        if path.is_file() and path.name in {".env", ".env.local", ".env.production", ".env.development"}:
            errors.append(f"environment file prohibited: {path.relative_to(ROOT)}")
        if not path.is_file() or path.suffix.casefold() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"possible {label}: {path.relative_to(ROOT)}")
    return sorted(set(errors))


def simplify_names(vault: Path) -> None:
    """Rename presentation paths only; preserve bytes and refuse collisions."""
    directories = {"📦 READY FOR CLAUDE": "📦 CLAUDE", "💬 START HERE — CHATGPT": "💬 CHATGPT"}
    files = {
        "📍 START HERE.html": "🔎 BROWSE LIBRARY.html",
        "📦 READY FOR CLAUDE/READ ME FIRST.md": "📦 CLAUDE/README.md",
        "💬 START HERE — CHATGPT/START HERE.md": "💬 CHATGPT/README.md",
        "⚠️ NEEDS SETUP/READ ME FIRST.md": "⚠️ NEEDS SETUP/README.md",
        "📋 COPY & PASTE/READ ME FIRST.md": "📋 COPY & PASTE/README.md",
    }
    def prefix(path):
        for old, new in directories.items():
            if path == old or path.startswith(old + "/"):
                return new + path[len(old):]
        return path
    def mapped(path):
        return files.get(path, prefix(path))
    targets = {**directories, **files}
    before = {}
    for old, new in targets.items():
        src, dst = vault / old, vault / new
        if not src.exists() or dst.exists() or src.is_symlink():
            raise ValueError("Migration source missing or destination occupied: " + old)
        for path in ([src] if src.is_file() else src.rglob("*")):
            if path.is_symlink():
                raise ValueError("Migration refuses symlinks")
            if path.is_file():
                before[path.relative_to(vault).as_posix()] = sha256(path)
    manifest_path = vault / "🔧 ADVANCED/metadata/easy-library.json"
    manifest = json.loads(manifest_path.read_text())
    ledger = vault / "🔧 ADVANCED/metadata/naming-migration.json"
    if ledger.exists():
        raise ValueError("Naming migration already recorded")
    for old, new in directories.items():
        (vault / old).rename(vault / new)
    for old, new in files.items():
        (vault / prefix(old)).rename(vault / new)
    for old, expected in before.items():
        if sha256(vault / mapped(old)) != expected:
            raise ValueError("Preservation mismatch: " + old)
    # Remap managed-output ownership before regenerating changed links and guides.
    manifest["artifacts"] = {mapped(p): h for p, h in manifest["artifacts"].items()}
    manifest_path.write_text(json_text(manifest))
    replacements = {
        "📦 READY FOR CLAUDE": "📦 CLAUDE",
        "💬 START HERE — CHATGPT": "💬 CHATGPT",
        "📍 START HERE.html": "🔎 BROWSE LIBRARY.html",
        "READY FOR CLAUDE": "CLAUDE",
        "START HERE — CHATGPT": "CHATGPT",
        "START HERE.md": "README.md",
        "READ ME FIRST.md": "README.md",
        "# 💬 Start here — ChatGPT": "# 💬 ChatGPT — usage guide",
    }
    documents = ("README.md", ".gitattributes", "🔧 ADVANCED/README.md",
                 "🔧 ADVANCED/scripts/easy-library-template.html",
                 "🔧 ADVANCED/scripts/chatgpt-start-here.md",
                 "🔧 ADVANCED/tests/test_easy_library.py")
    for name in documents:
        path = vault / name
        content = path.read_text()
        for old, new in replacements.items():
            content = content.replace(old, new).replace(old.replace(" ", "%20"), new.replace(" ", "%20"))
        path.write_text(content)
    ledger.write_text(json_text({"scope": "Presentation renames; file bytes verified before regenerating links",
                                "files": [{"from": p, "to": mapped(p), "sha256": h} for p, h in sorted(before.items())]}))
    print(f"Renamed and verified {len(before)} files; no files deleted.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify generated files and safety rules")
    parser.add_argument("--organize", action="store_true", help="One-time preservation-checked move into Advanced")
    parser.add_argument("--simplify-names", action="store_true", help="Preserve files while simplifying user-facing names")
    args = parser.parse_args()

    if args.simplify_names:
        simplify_names(ROOT.parent)
        return 0

    if args.organize:
        destination = ROOT / "🔧 ADVANCED"
        if destination.exists() or ROOT.name == "🔧 ADVANCED":
            raise SystemExit("Already organized; refusing to move again")
        names = ("catalog", "commands", "docs", "metadata", "scripts", "skills", "tests",
                 "project-instructions", "dist", "requirements-dev.txt", "CODE_OF_CONDUCT.md",
                 "CONTRIBUTING.md", "SECURITY.md", "THIRD_PARTY_NOTICES.md", "README.md")
        paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
        before = {p: sha256(ROOT / p) for p in paths if p and Path(p).parts[0] in names}
        destination.mkdir()
        for name in names:
            if (ROOT / name).exists():
                (ROOT / name).rename(destination / name)
        for path, digest in before.items():
            if sha256(destination / path) != digest:
                raise SystemExit("Preservation mismatch: " + path)
        (destination / "metadata/layout-migration.json").write_text(json_text({
            "scope": "Tracked files moved without byte changes at migration time",
            "files": before, "destination_prefix": "🔧 ADVANCED/"}))
        print(f"Preserved {len(before)} tracked files during relocation.", flush=True)
        os.execv(sys.executable, [sys.executable, str(destination / "scripts/build_repository.py")])

    outputs = generated_outputs()
    catalog = json.loads(outputs[CATALOG_JSON])
    errors = safety_errors(catalog)

    if args.check:
        for path, expected in outputs.items():
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                errors.append(f"generated file is stale: {path.relative_to(ROOT)}")
    else:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in sorted(set(errors)):
            print(f"- {error}", file=sys.stderr)
        return 1

    inventory = json.loads(outputs[INVENTORY_JSON])
    audit = json.loads(outputs[LICENSE_AUDIT_JSON])
    print(
        "Validated "
        f"{catalog['entry_count']} source entries, "
        f"{inventory['skill_file_count']} skill files, and "
        f"{inventory['command_file_count']} command files."
    )
    print(
        "License audit: "
        f"{audit['counts'].get('adjacent-license-found', 0)} adjacent license files found; "
        "not redistribution clearance. See package-audit.json for declarations and ancestors."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
