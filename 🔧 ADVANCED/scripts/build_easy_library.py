#!/usr/bin/env python3
"""Generate the human-facing library; never execute collected skill code."""
import argparse
import hashlib
import json
import re
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import quote

from skillverse import ROOT, catalog, export, inspect, frontmatter
from build_instruction_pack import FILES, COMBINED

VAULT = ROOT.parent
READY = "📦 READY FOR CLAUDE"
SETUP = "⚠️ NEEDS SETUP"
COPY = "📋 COPY & PASTE"
START = "📍 START HERE.html"
MANIFEST = ROOT / "metadata/easy-library.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def category(label):
    """Conservative name-based browsing labels, not compatibility claims."""
    name = label.casefold()
    rules = (
        ("Design & Media", r"design|image|figma|canvas|theme|video|sora|remotion|manim|ui-|ux-|slides|pptx|presentation"),
        ("Writing & Documents", r"writ|copy|humaniz|docx|pdf|document|article|content|brand.voice"),
        ("Marketing & Business", r"^ads|seo|market|social|investor|sales|lead|brand|email|outreach|business"),
        ("Research & Data", r"research|search|scrap|data|analys|spreadsheet|finance|trading|scient|paper|hugging"),
        ("Coding & Development", r"code|api|test|debug|review|security|git|frontend|backend|python|swift|react|vercel|deploy|sql|rust|java|kotlin|django|laravel|perl|docker|node|css|html|mcp|tdd|cpp|csharp|dotnet|android|flutter|spring|supabase|cloudflare"),
    )
    for title, pattern in rules:
        if re.search(pattern, name):
            return title
    return "Tools & Workflows"


def needs_setup(report):
    signals = report.get("signals", [])
    return any(any(key in signal for key in (
        "MCP/tool", "Host-specific", "Agent tools", "Credentials/service", "Nested skill",
        "Plugin source", "External tools"
    )) for signal in signals)


def safe_payload(value):
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def outputs(root=ROOT, vault=VAULT):
    generated = {}
    rows = []
    seen = {}
    audit = []
    for entry in catalog(root):
        report = inspect(entry, root)
        entry = dict(entry)
        if entry["type"] == "skill":
            text = (root / entry["path"]).read_text()
            meta, _ = frontmatter(text)
            entry["description"] = " ".join(str(meta.get("description", entry["description"])).split())
            if "/plugins/" in entry["path"]:
                report["signals"].append("Plugin source — verify required plugin capabilities in Claude")
            if re.search(r"\b(?:CLI|connector|connected|terminal|shell|subagents?|Stripe|Dropbox)\b", text, re.I):
                report["signals"].append("External tools or services mentioned — review availability")
        entry["display_name"] = entry["label"].split(":")[-1].replace("-", " ").replace("_", " ").strip().title()
        if entry["type"] != "skill":
            row = {**entry, "category": "Claude Code Commands", "status": "Command — not a skill ZIP",
                   "source": "🔧 ADVANCED/" + entry["path"], "zip": None,
                   "signals": report["issues"], "copies": [entry["id"]]}
            rows.append(row)
            continue
        key = report["package_sha256"]
        if key in seen:
            seen[key]["copies"].append(entry["id"])
            continue
        row = {**entry, "category": category(entry["label"]), "source": "🔧 ADVANCED/" + entry["path"],
               "signals": report["signals"], "copies": [entry["id"]], "zip": None}
        seen[key] = row
        rows.append(row)
        with tempfile.TemporaryDirectory(prefix="vault-claude-export-") as folder:
            try:
                archive = export(entry, "claude", Path(folder), root)
            except ValueError as error:
                row["status"] = "Needs repair — no ZIP"
                row["signals"] = [str(error), *report["signals"]]
                continue
            with zipfile.ZipFile(archive) as z:
                if z.testzip() is not None:
                    raise ValueError("ZIP integrity failure")
                names = z.namelist()
                prefixes = {name.split("/")[0] for name in names}
                if len(prefixes) != 1 or next(iter(prefixes)) + "/SKILL.md" not in names:
                    raise ValueError("ZIP entrypoint/layout failure")
            setup = needs_setup(report)
            row["status"] = "Needs tool/setup review" if setup else "Packaging checked"
            section = SETUP + "/Packaged - Review Requirements" if setup else READY
            zip_relative = section + "/" + row["category"] + "/" + archive.name
            row["zip"] = zip_relative
            generated[vault / zip_relative] = archive.read_bytes()
            ref = archive.with_name(archive.stem + "-reference.md")
            ref_relative = COPY + "/Skill References/" + row["category"] + "/" + ref.name
            row["reference"] = ref_relative
            generated[vault / ref_relative] = ref.read_bytes()
            audit.append(json.loads(archive.with_suffix(".json").read_text()))
    counts = dict(Counter(row["status"] for row in rows))
    summary = {"catalog_entries": len(catalog(root)), "browse_entries": len(rows),
               "zip_count": sum(row["zip"] is not None for row in rows),
               "live_claude_imports_verified": 0, "status_counts": counts}
    manifest = {"schema_version": 1, "scope": "Packaging and heuristic requirements only; no live imports",
                "summary": summary, "entries": rows, "artifacts": {}}
    template = (root / "scripts/easy-library-template.html").read_text()
    generated[vault / START] = template.replace("__LIBRARY_DATA__", safe_payload(manifest)).encode()
    # Markdown works on GitHub, where the offline HTML page is not rendered.
    lines = ["# Browse skills and downloads", "",
             "Download the GitHub release ZIP and extract it once. Browse the topic folders directly.",
             "The HTML search page is optional. No website, Python or manual skill zipping is required.", "",
             "Packaging checked does not mean tested inside Claude. Review tool requirements.",
             "Identical whole packages share one ZIP; all source copies remain in Advanced.", ""]
    for title in sorted({row["category"] for row in rows}):
        lines += ["## " + title, ""]
        for row in (r for r in rows if r["category"] == title):
            label = row["label"].replace("[", "").replace("]", "").replace("\n", " ")
            link = row["zip"] or row["source"]
            lines.append("- [" + label + "](" + quote("../" + link, safe="/") + ") — " + row["status"]
                         + ("; " + str(len(row["copies"])) + " identical source copies" if len(row["copies"]) > 1 else ""))
        lines.append("")
    generated[vault / READY / "BROWSE ALL SKILLS.md"] = "\n".join(lines).encode()
    generated[root / "metadata/upload-reports.json"] = (json.dumps(audit, ensure_ascii=False, indent=2) + "\n").encode()
    for name in (*FILES, COMBINED):
        generated[vault / COPY / "Project Instructions" / name] = (root / "project-instructions" / name).read_bytes()
    generated[vault / READY / "READ ME FIRST.md"] = (
        "# Ready-made Claude ZIPs\n\n"
        "1. Open a topic folder here and choose a skill ZIP. The website is optional.\n"
        "2. Read its requirements, then select its ZIP. Do not unzip that individual ZIP.\n"
        "3. In Claude, use Customize → Skills → add/create → upload (labels may vary).\n"
        "4. Try a harmless task and confirm the skill activates.\n\n"
        "No manual zipping or Terminal commands are needed. These packages passed structural checks, "
        "not live Claude imports or a full code/security review. Enable only what you need. "
        "Do not install same-name variants together without review.\n\n"
        "Skills requiring known tools or host setup are in ⚠️ NEEDS SETUP. "
        "All source versions are preserved under 🔧 ADVANCED.\n\n"
        "Official guide: https://support.claude.com/en/articles/12512198-how-to-create-custom-skills\n"
    ).encode()
    problem_lines = ["# Needs setup or repair", "",
                     "Packaged ZIPs here mention special tools, accounts, host paths or nested skills.",
                     "These are heuristic flags, not proof that a skill is incompatible.",
                     "For details without a website, use the matching readable Skill Reference in COPY & PASTE.",
                     "The searchable menu is an optional alternative.", "",
                     "## No ZIP generated", ""]
    for row in rows:
        if row["status"] == "Needs repair — no ZIP":
            problem_lines += ["- " + str(row["id"]) + " · " + row["label"] + ": " + "; ".join(row["signals"])]
    problem_lines += ["", "Claude Code slash commands are not native Claude skill ZIPs; find them through the menu.",
                      "No originals were removed. No repaired behavior or successful account import is claimed.", ""]
    generated[vault / SETUP / "READ ME FIRST.md"] = "\n".join(problem_lines).encode()
    generated[vault / COPY / "READ ME FIRST.md"] = (
        "# Copy and paste — not skill installation\n\n"
        "For general project guidance, open Project Instructions/COPY-PASTE-ALL.md. "
        "Use it instead of the separate core and handbook, not alongside them.\n\n"
        "Skill References contains readable individual instructions. These copies do not include "
        "supporting assets and do not install tools. Use the skill ZIP for native Claude installation.\n\n"
        "Keep filled-in personal context outside this library and outside GitHub.\n"
    ).encode()
    manifest["artifacts"] = {p.relative_to(vault).as_posix(): digest(data) for p, data in generated.items()}
    generated[root / "metadata/easy-library.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    return generated, summary


def apply_outputs(generated, previous, vault, check=False):
    errors = []
    expected = {p.relative_to(vault).as_posix() for p in generated}
    retired = []
    for rel, old_hash in previous.items():
        if rel in expected:
            continue
        if Path(rel).is_absolute() or ".." in Path(rel).parts:
            raise ValueError("Unsafe prior manifest path")
        old = vault / rel
        if not old.exists():
            continue
        destination = vault / "🔧 ADVANCED/dist/previous-easy-library" / old_hash / rel
        if old.is_symlink() or digest(old.read_bytes()) != old_hash or destination.exists():
            errors.append("Changed retired output preserved for manual review: " + rel)
        elif check:
            errors.append("Retired output requires archival: " + rel)
        else:
            retired.append((old, destination))
    for path, data in generated.items():
        rel = path.relative_to(vault).as_posix()
        # macOS /var itself is a system symlink; reject links within our output
        # tree, not unrelated ancestors of the explicitly selected vault.
        parts = path.relative_to(vault).parts
        if any(vault.joinpath(*parts[:i]).is_symlink() for i in range(1, len(parts) + 1)):
            errors.append("Symlink output refused: " + rel)
            continue
        existing = path.read_bytes() if path.exists() else None
        if check:
            if existing != data:
                errors.append("Missing or stale: " + rel)
        elif existing not in (None, data) and digest(existing) != previous.get(rel):
            errors.append("Changed or unmanaged file preserved: " + rel)
    if errors:
        raise ValueError("\n".join(errors))
    if not check:
        for old, destination in retired:
            destination.parent.mkdir(parents=True, exist_ok=True)
            old.rename(destination)
        for path, data in generated.items():
            if not path.exists() or path.read_bytes() != data:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    previous = {}
    if MANIFEST.exists():
        previous = json.loads(MANIFEST.read_text()).get("artifacts", {})
        previous[MANIFEST.relative_to(VAULT).as_posix()] = digest(MANIFEST.read_bytes())
    generated, summary = outputs()
    apply_outputs(generated, previous, VAULT, args.check)
    print(json.dumps(summary, indent=2))
    print("No source files deleted; no collected code executed; no live import claimed.")


if __name__ == "__main__":
    main()
