#!/usr/bin/env python3
"""Build and validate public metadata without executing collected skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify generated files and safety rules")
    args = parser.parse_args()

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
