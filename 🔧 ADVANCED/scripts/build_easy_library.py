#!/usr/bin/env python3
"""Generate the human-facing library; never execute collected skill code."""
import argparse
import hashlib
import io
import json
import posixpath
import re
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import quote

from skillverse import ROOT, catalog, export, inspect, frontmatter, package_files
from build_instruction_pack import FILES, COMBINED

VAULT = ROOT.parent
READY = "📦 CLAUDE"
SETUP = "⚠️ NEEDS SETUP"
COPY = "📋 COPY & PASTE"
CHATGPT = "💬 CHATGPT"
START = "🔎 BROWSE LIBRARY.html"
MANIFEST = ROOT / "metadata/easy-library.json"
ORGANIZED_TOPICS = {"Coding & Development", "Design & Media", "Writing & Documents"}


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


def friendly_name(label):
    """Readable browsing name; canonical skill names inside packages stay unchanged."""
    name = label.split(":")[-1].replace("-", " ").replace("_", " ").strip().title()
    acronyms = {
        "Ai": "AI", "Api": "API", "Cdn": "CDN", "Ci": "CI", "Cli": "CLI",
        "Api2Pdf": "API2PDF", "Cpp": "C++", "Css": "CSS",
        "Docx": "Word Documents (DOCX)", "E2E": "E2E",
        "Gh": "GitHub", "Html": "HTML", "Ios": "iOS",
        "Json": "JSON", "Mcp": "MCP", "Ncc": "NCC", "Orm": "ORM", "Pr": "PR",
        "Pdf": "PDF", "Pptx": "PowerPoint (PPTX)", "Sdk": "SDK", "Sql": "SQL",
        "Ssh": "SSH", "Ssr": "SSR", "Swa": "SWA",
        "Swr": "SWR", "Tdd": "TDD", "Tsx": "TSX", "Ui": "UI", "Url": "URL",
        "Ux": "UX", "Waf": "WAF",
    }
    return " ".join(acronyms.get(word, word) for word in name.split())


def coding_subcategory(label):
    """Small, task-oriented groups for the otherwise overwhelming coding catalog."""
    name = label.casefold()
    leaf = name.split(":")[-1]
    if name.startswith(("vercel:", "vercel-plugin:")):
        if re.search(r"ai-|chat|eve|agent|workflow|queue|generation", leaf):
            return "🤖 Vercel AI & Automation"
        if re.search(r"next|react|shadcn|geist|swr|turbopack|turborepo|v0|satori|json-render|cms|microfrontend", leaf):
            return "🌐 Vercel Frontend & Next.js"
        return "☁️ Vercel Platform & Deployment"
    if re.search(r"security|threat|bounty|firewall|auth", name):
        return "🔐 Security & Authentication"
    if re.search(r"github|\bgh-|git-worktree|code-review|review-agent|brooks-review|review-claudemd", name):
        return "🔀 GitHub & Code Review"
    if re.search(r"test|debug|benchmark|eval|verification|regression|\btdd\b|webapp-testing", name):
        return "🧪 Testing & Debugging"
    if re.search(r"android|flutter|swift|kotlin-coroutines|mobile|desktop", name):
        return "📱 Mobile & Desktop Apps"
    if re.search(r"mcp|api-connector|claude-api|x-api|apify", name):
        return "🔌 APIs, MCP & Integrations"
    if re.search(r"postgres|supabase|database|storage|exposed|persistence", name):
        return "🗄️ Databases & Storage"
    if re.search(r"deploy|cloudflare|docker|pipeline|ci.?cd", name):
        return "🚀 DevOps & Deployment"
    if re.search(r"frontend|webapp|react|next|css|html|ui", name):
        return "🌐 Websites & Frontend"
    if re.search(r"backend|server|api|ktor|spring|django|laravel", name):
        return "⚙️ Backend & APIs"
    if re.search(r"python|rust|java|kotlin|perl|golang|csharp|cpp|dotnet|dart", name):
        return "💻 Languages & Frameworks"
    return "🧱 Architecture & Code Quality"


def design_subcategory(label):
    name = label.casefold()
    if re.search(r"video|manim|remotion|sora|videodb|ui-demo", name):
        return "🎬 Video, Motion & Demos"
    if re.search(r"slide|pptx|presentation", name):
        return "📊 Presentations & Slides"
    if re.search(r"figma|interface|frontend-design|liquid-glass|swiftui|design-is", name):
        return "🖥️ UI, UX & Product Design"
    if re.search(r"image|canvas", name):
        return "🖼️ Images & Visual Artwork"
    if re.search(r"theme|design-report|system-design|api-design", name):
        return "🎨 Design Systems & Reports"
    return "🧩 Creative Tools & Workflows"


def writing_subcategory(label):
    name = label.casefold()
    if re.search(r"article|brand-voice|content-engine|humanizer", name):
        return "✍️ Writing, Voice & Content"
    if re.search(r"docx|documents:documents", name):
        return "📝 Word Documents"
    if re.search(r"pdf|api2pdf|nutrient", name):
        return "📄 PDF & Document Processing"
    if re.search(r"notion|dropbox", name):
        return "🗂️ Knowledge & File Management"
    if re.search(r"write-a-skill|writing-plans|writing-skills", name):
        return "🧠 Skills, Plans & Instructions"
    return "⚙️ Document Automation & Utilities"


def browsing_subcategory(topic, label):
    if topic == "Coding & Development":
        return coding_subcategory(label)
    if topic == "Design & Media":
        return design_subcategory(label)
    if topic == "Writing & Documents":
        return writing_subcategory(label)
    return None


def visible_folder(entry, topic, used):
    source = Path(entry['path'])
    # The nested readable-name migration is deliberately scoped to the large
    # Coding & Development topic. Every other topic keeps its established path.
    name = (friendly_name(entry['label'])
            if topic in ORGANIZED_TOPICS and entry['type'] == 'skill'
            else (source.parent.name if entry['type'] == 'skill' else source.stem))
    parts = [READY, topic]
    if topic in ORGANIZED_TOPICS and entry['type'] == 'skill':
        parts.append(browsing_subcategory(topic, entry['label']))
    folder = '/'.join([*parts, name])
    if folder.casefold() in used:
        folder += f" [variant {entry['id']:04d}]"
    if folder.casefold() in used:
        raise ValueError('Visible folder collision: ' + folder)
    used.add(folder.casefold())
    return folder


def outputs(root=ROOT, vault=VAULT):
    generated = {}
    rows = []
    seen = {}
    audit = []
    used_folders = set()
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
        topic = category(entry["label"]) if entry["type"] == "skill" else "Claude Code Commands"
        entry["display_name"] = (friendly_name(entry["label"]) if topic in ORGANIZED_TOPICS
                                 else entry["label"].split(":")[-1].replace("-", " ").replace("_", " ").strip().title())
        if entry["type"] != "skill":
            row = {**entry, "category": "Claude Code Commands", "status": "Command — not a skill ZIP",
                   "source": "🔧 ADVANCED/" + entry["path"], "zip": None,
                   "signals": report["issues"], "copies": [entry["id"]]}
            rows.append(row)
            row['folder'] = visible_folder(entry, 'Claude Code Commands', used_folders)
            continue
        key = report["package_sha256"]
        if key in seen:
            seen[key]["copies"].append(entry["id"])
            continue
        row = {**entry, "category": topic, "source": "🔧 ADVANCED/" + entry["path"],
               "signals": report["signals"], "copies": [entry["id"]], "zip": None}
        row["subcategory"] = browsing_subcategory(row["category"], entry["label"])
        seen[key] = row
        rows.append(row)
        row['folder'] = visible_folder(entry, row['category'], used_folders)
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
            zip_relative = row['folder'] + '/' + archive.name
            row["zip"] = zip_relative
            generated[vault / zip_relative] = archive.read_bytes()
            ref = archive.with_name(archive.stem + "-reference.md")
            ref_relative = COPY + "/Skill References/" + row["category"] + "/" + ref.name
            row["reference"] = ref_relative
            generated[vault / ref_relative] = ref.read_bytes()
            if row["category"] in ORGANIZED_TOPICS:
                chat_name = Path(row['folder']).name + " — ChatGPT Reference.md"
                chat_path = CHATGPT + "/Skill References/" + row["category"] + "/" + row["subcategory"] + "/" + chat_name
            else:
                chat_path = CHATGPT + "/Skill References/" + row["category"] + "/" + ref.name.replace("-claude-reference", "-chatgpt-reference")
            row["chatgpt_reference"] = chat_path
            chat_source = posixpath.relpath(row["source"], start=posixpath.dirname(chat_path))
            context = ("# ChatGPT reference — " + row["display_name"] + "\n\n"
                       "Readable guidance, not a native skill installation. No live ChatGPT test is claimed. "
                       "Supporting scripts and assets are not embedded in this document. "
                       "Provider-specific commands may require adaptation; do not assume tools are available.\n\n"
                       "## Requirements to review\n\n" +
                       "\n".join("- " + signal for signal in row["signals"]) +
                       ("\n" if row["signals"] else "No special setup signals detected; this is not a compatibility guarantee.\n") +
                       "\n[Preserved source and supporting files](" + quote(chat_source, safe="/") + ")\n\n---\n\n")
            generated[vault / chat_path] = context.encode() + ref.read_bytes()
            audit.append(json.loads(archive.with_suffix(".json").read_text()))
    entries_by_id = {e['id']: e for e in catalog(root)}
    for row in rows:
        source = root / row['path']
        source_files = package_files(source.parent) if row['type'] == 'skill' else [source]
        for path in source_files:
            relative = path.relative_to(source.parent).as_posix()
            destination = vault / row['folder'] / relative
            if destination in generated and generated[destination] != path.read_bytes():
                raise ValueError('Source/output collision: ' + str(destination))
            generated[destination] = path.read_bytes()
        row['front_source'] = row['folder'] + '/' + source.name
        row['guide'] = row['folder'] + '/VAULT GUIDE.md'
        if vault / row['guide'] in generated:
            raise ValueError('Reserved guide filename already exists in source')
        report = inspect(entries_by_id[row['id']], root)
        license_links = []
        for evidence in report.get('license_evidence', []):
            if 'file' in evidence:
                original = root / evidence['file']
                relative = 'License Notices/' + evidence['file']
                generated[vault / row['folder'] / relative] = original.read_bytes()
                license_links.append('- [License or notice](' + quote(relative, safe='/') + ')')
        guide = ['# ' + row['display_name'], '', '**Status: ' + row['status'] + '**', '',
                 '[Open the actual source file](' + quote(source.name) + ')', '',
                 'This folder contains the preserved instructions and available supporting files directly. '
                 'No collected scripts were executed. Review requirements before use.', '']
        if row['zip']:
            guide += ['[Upload this ZIP to Claude](' + quote(Path(row['zip']).name) + ')', '',
                      'Do not unzip the individual skill ZIP for Claude upload. The ZIP may normalize metadata; '
                      'The unpacked files preserve the original bytes. No live Claude import is verified.', '']
        else:
            guide += ['No native skill ZIP is supplied: ' + row['status'] + '.', '']
        guide += ['## Requirements and limitations', '', *('- ' + s for s in row['signals']), '',
                  'Packaging checks do not prove runtime behavior, security, or redistribution rights.', '',
                  '## Source copies represented', '']
        for source_id in row['copies']:
            original = entries_by_id[source_id]
            advanced_source = '🔧 ADVANCED/' + original['path']
            relative_source = posixpath.relpath(advanced_source, start=row['folder'])
            guide.append('- [' + str(source_id) + ' · ' + original['collection'] + '](' +
                         quote(relative_source, safe='/') + ')')
        guide += ['', 'Identical whole packages share this folder; distinct variants have separate folders.', '', *license_links, '']
        generated[vault / row['guide']] = '\n'.join(guide).encode()
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
        selected = [r for r in rows if r["category"] == title]
        selected.sort(key=lambda r: ((r.get("subcategory") or ""), r["display_name"]))
        current_subcategory = None
        for row in selected:
            if row.get("subcategory") != current_subcategory:
                current_subcategory = row.get("subcategory")
                if current_subcategory:
                    lines += ["### " + current_subcategory, ""]
            label = row["label"].replace("[", "").replace("]", "").replace("\n", " ")
            link = row['guide']
            lines.append("- [" + label + "](" + quote("../" + link, safe="/") + ") — " + row["status"]
                         + ("; " + str(len(row["copies"])) + " identical source copies" if len(row["copies"]) > 1 else ""))
        lines.append("")
    generated[vault / READY / "BROWSE ALL SKILLS.md"] = "\n".join(lines).encode()
    generated[root / "metadata/upload-reports.json"] = (json.dumps(audit, ensure_ascii=False, indent=2) + "\n").encode()
    for name in (*FILES, COMBINED):
        generated[vault / COPY / "Project Instructions" / name] = (root / "project-instructions" / name).read_bytes()
        generated[vault / CHATGPT / "Project Instructions" / name] = (root / "project-instructions" / name).read_bytes()
    chat_rows = [row for row in rows if row.get("chatgpt_reference")]
    chat_start = (root / "scripts/chatgpt-start-here.md").read_text().replace("__REFERENCE_COUNT__", str(len(chat_rows)))
    generated[vault / CHATGPT / "README.md"] = chat_start.encode()
    generated[vault / CHATGPT / "Project Instructions/README.md"] = (
        "# Project instructions for ChatGPT\n\n"
        "Start with PROJECT-INSTRUCTIONS.md for concise guidance and PROJECT-HANDBOOK.md as reference. "
        "Alternatively choose COPY-PASTE-ALL.md instead of both. Do not duplicate the same guidance.\n\n"
        "Copy only relevant instructions into the supported project instruction area, within its limits; "
        "upload the handbook as a source. These documents do not install native skills. "
        "Keep filled-in PROJECT-CONTEXT.template.md private and outside this repository.\n\n"
        "[Return to setup guide](../README.md)\n"
    ).encode()
    chat_index = ["# Browse ChatGPT references", "", "These are readable documents, not verified native skill packages.",
                  "Review each document's requirements. No supporting scripts/assets are embedded.", ""]
    for title in sorted({row["category"] for row in chat_rows}):
        chat_index += ["## " + title, ""]
        selected = [r for r in chat_rows if r["category"] == title]
        selected.sort(key=lambda r: ((r.get("subcategory") or ""), r["display_name"]))
        current_subcategory = None
        for row in selected:
            if row.get("subcategory") != current_subcategory:
                current_subcategory = row.get("subcategory")
                if current_subcategory:
                    chat_index += ["### " + current_subcategory, ""]
            relative = Path(row["chatgpt_reference"]).relative_to(CHATGPT).as_posix()
            label = row["display_name"].replace("[", "").replace("]", "")
            chat_index.append("- [" + label + "](" + quote(relative, safe="/") + ") — " +
                              ("requirements flagged" if row["status"] == "Needs tool/setup review" else "no special setup signals detected"))
        chat_index.append("")
    chat_index += ["## Not converted to references here", "",
                   "The 13 incomplete skill packages and 86 command entries remain in the original catalog; "
                   "they are not represented as ChatGPT-ready workflows.", ""]
    generated[vault / CHATGPT / "BROWSE REFERENCES.md"] = "\n".join(chat_index).encode()
    # An optional document bundle for extraction, never a native skill installer.
    bundle = io.BytesIO()
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, data in sorted(generated.items()):
            if path.is_relative_to(vault / CHATGPT):
                info = zipfile.ZipInfo("ChatGPT Reference Pack/" + path.relative_to(vault / CHATGPT).as_posix())
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
    generated[vault / CHATGPT / "ChatGPT-Reference-Pack.zip"] = bundle.getvalue()
    generated[vault / READY / "README.md"] = (
        "# Claude — all skills and source files\n\n"
        "All 485 distinct skills are visible here: 472 with a ZIP and 13 with source files and repair warnings. "
        "The 86 command entries are visible separately under Claude Code Commands. "
        "Together these represent all 925 catalog entries, including identical source copies.\n\n"
        "1. Open a topic. Coding & Development, Design & Media, and Writing & Documents have smaller task-based subcategories; then open the clearly named skill folder. "
        "SKILL.md and supporting files are directly inside, beside the upload ZIP.\n"
        "Read VAULT GUIDE.md for setup warnings. Same-name distinct variants have a suffix to prevent overwriting.\n"
        "2. Read its requirements, then select its ZIP. Do not unzip that individual ZIP.\n"
        "3. In Claude, use Customize → Skills → add/create → upload (labels may vary).\n"
        "4. Try a harmless task and confirm the skill activates.\n\n"
        "No manual zipping or Terminal commands are needed. Available ZIPs passed structural checks, "
        "not live Claude imports or a full code/security review. Enable only what you need. "
        "Do not install same-name variants together without review.\n\n"
        "Skills requiring tools or host setup remain here, with warnings inside their own folders. "
        "All source versions are preserved under 🔧 ADVANCED.\n\n"
        "Official guide: https://support.claude.com/en/articles/12512198-how-to-create-custom-skills\n"
    ).encode()
    problem_lines = ["# Setup and repair report", "",
                     "All skill folders and available ZIPs are now together in 📦 CLAUDE, grouped by topic.",
                     "This is a report only; skills are not hidden in a separate setup collection.",
                     "These are heuristic flags, not proof that a skill is incompatible.",
                     "For details without a website, use the matching readable Skill Reference in COPY & PASTE.",
                     "The searchable menu is an optional alternative.", "",
                     "## No ZIP generated", ""]
    for row in rows:
        if row["status"] == "Needs repair — no ZIP":
            problem_lines += ["- [" + str(row["id"]) + " · " + row["label"] + "](" + quote('../' + row['guide'], safe='/') + "): " + "; ".join(row["signals"])]
    problem_lines += ["", "Claude Code slash commands are not native Claude skill ZIPs; find them through the menu.",
                      "No originals were removed. No repaired behavior or successful account import is claimed.", ""]
    generated[vault / SETUP / "README.md"] = "\n".join(problem_lines).encode()
    generated[vault / COPY / "README.md"] = (
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
