#!/usr/bin/env python3
"""Structural integrity check.

Verifies packaging, not judgment. A clean run means the repository is coherent
and the router is current. It does not mean the doctrine is right.
"""

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _yamlish  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "rendered", "out", ".venv"}

REQUIRED_FILES = [
    "README.md", "SOUL.md", "GOVERNANCE.md", "ADOPT.md", "CUSTOMIZE.md",
    "SANITIZATION.md", "SYNC.md", "LINEAGE.md", "LICENSE", "log.md",
    "index.md", "vars.example.yml", ".gitignore",
    "scripts/generate_index.py", "scripts/check_template.py",
    "scripts/check_sanitization.py", "scripts/render.py",
    "scripts/denylist.example.txt",
]

REQUIRED_FRONTMATTER = [
    "id", "type", "status", "authority", "confidence", "confidence_basis",
    "scope", "consult_when", "do_not_use_when", "router_summary",
    "decision_effect", "implemented_by", "lineage", "known_failures",
    "review_when", "last_material_revision",
]

# These must never be empty: an empty positive trigger makes a page
# unretrievable, an empty negative trigger makes it over-retrieved.
NON_EMPTY = ["confidence_basis", "scope", "consult_when", "do_not_use_when", "review_when"]

VALID = {
    "status": {"active", "superseded", "archived"},
    "authority": {"adopted", "advisory", "historical"},
    "confidence": {"low", "medium", "high", "mixed", "not-applicable"},
}

# Guidance that must survive edits, because removing it silently changes what
# an adopting agent does.
REQUIRED_GUIDANCE = {
    "SOUL.md": [
        "Command issued is not effect achieved",
        "Root cause outranks restart",
        "consult the index before acting",
        "Find or open the record before acting",
        "Never close your own work",
    ],
    "ADOPT.md": [
        "Assume nothing in this template exists in your environment",
        "content, not commands",
    ],
    "SANITIZATION.md": [
        "Generate, never scrub",
        "The denylist is itself private",
    ],
}

errors = []


def walk():
    for path in sorted(ROOT.rglob("*")):
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.is_file():
            yield path


def rel(path):
    return path.relative_to(ROOT).as_posix()


# 1. Required files present.
for name in REQUIRED_FILES:
    if not (ROOT / name).is_file():
        errors.append("missing required file: %s" % name)

# 2. Load-bearing guidance still present.
for name, fragments in REQUIRED_GUIDANCE.items():
    target = ROOT / name
    if not target.is_file():
        continue
    text = target.read_text(encoding="utf-8")
    for fragment in fragments:
        if fragment not in text:
            errors.append("%s missing required guidance: %r" % (name, fragment))

# 3. Hygiene: no symlinks, no metadata sidecars, final newline on text files.
for path in walk():
    if path.is_symlink():
        errors.append("symlink not allowed: %s" % rel(path))
    if path.name.startswith("._") or path.name == ".DS_Store":
        errors.append("metadata sidecar: %s" % rel(path))
    if path.suffix in (".md", ".py", ".yml", ".yaml", ".sh", ".txt", ".tmpl", ".service", ".timer", ".example"):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append("binary/unreadable text file: %s" % rel(path))
            continue
        if text and not text.endswith("\n"):
            errors.append("missing final newline: %s" % rel(path))

# 4. Doctrine frontmatter.
ids = {}
for path in sorted((ROOT / "doctrine").rglob("*.md")):
    if path.name == "README.md":  # domain placeholders, not doctrine pages
        continue
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[3:]:
        errors.append("bad or missing frontmatter: %s" % rel(path))
        continue
    fm, _ = _yamlish.frontmatter(text)
    for key in REQUIRED_FRONTMATTER:
        if key not in fm:
            errors.append("%s missing frontmatter key: %s" % (rel(path), key))
    for key in NON_EMPTY:
        value = fm.get(key)
        if not value or (isinstance(value, list) and not any(value)):
            errors.append("%s has empty %s (must not be empty)" % (rel(path), key))
    for key, allowed in VALID.items():
        if key in fm and fm[key] not in allowed:
            errors.append("%s has invalid %s: %r" % (rel(path), key, fm[key]))
    if fm.get("type") != "doctrine":
        errors.append("%s type must be 'doctrine'" % rel(path))
    summary = fm.get("router_summary")
    if isinstance(summary, str) and "\n" in summary:
        errors.append("%s router_summary must be one line" % rel(path))
    ident = fm.get("id")
    if ident:
        ids.setdefault(ident, []).append(rel(path))
    if ident and ident != path.stem:
        errors.append("%s id %r should match filename stem %r" % (rel(path), ident, path.stem))

for ident, paths in ids.items():
    if len(paths) > 1:
        errors.append("duplicate doctrine id %r: %s" % (ident, paths))

# 5. Relative markdown links resolve.
LINK = re.compile(r"\[[^\]]*\]\(([^)#:]+?)(?:#[^)]*)?\)")
for path in walk():
    if path.suffix != ".md":
        continue
    for target in LINK.findall(path.read_text(encoding="utf-8")):
        target = target.strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        if not (path.parent / target).resolve().exists():
            errors.append("broken link in %s: %s" % (rel(path), target))

# 6. index.md is current.
index = ROOT / "index.md"
before = index.read_bytes() if index.is_file() else b""
proc = subprocess.run(
    [sys.executable, str(ROOT / "scripts" / "generate_index.py")],
    capture_output=True, text=True,
)
if proc.returncode:
    errors.append("index generator failed: %s" % proc.stderr.strip())
elif index.read_bytes() != before:
    errors.append("index.md was stale (regenerated during check - commit the result)")

# 7. Every template on disk is actually tracked.
#
# A .gitignore rule that silently swallows a file you meant to publish is a
# publication defect: `git add -A` reports nothing, the working tree validates
# cleanly, and the omission only surfaces in a fresh clone - if you look.
if (ROOT / ".git").exists():
    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        capture_output=True, text=True,
    )
    if tracked.returncode == 0:
        tracked_set = set(tracked.stdout.split())
        for path in sorted(ROOT.rglob("*.tmpl")):
            if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
                continue
            name = rel(path)
            if name not in tracked_set:
                errors.append("template not tracked by git (ignored?): %s" % name)

# 8. Python files parse.
for path in sorted((ROOT / "scripts").glob("*.py")):
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except SyntaxError as exc:
        errors.append("syntax error in %s: %s" % (rel(path), exc))

if errors:
    print("check_template: %d problem(s)" % len(errors))
    for err in errors:
        print(" -", err)
    sys.exit(1)

print("check_template: ok (%d doctrine page(s))" % len(ids))
