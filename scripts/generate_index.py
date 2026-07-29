#!/usr/bin/env python3
"""Generate index.md from active-doctrine frontmatter.

index.md is a deterministic router. It is never edited by hand and holds no
independent authority - see GOVERNANCE.md. Regenerate it whenever doctrine
changes; check_template.py fails if it is stale.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _yamlish  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOCTRINE = ROOT / "doctrine"

HEADER = """<!-- GENERATED FILE - do not edit. Run: python3 scripts/generate_index.py -->

# Doctrine router

Consult this router for consequential operations work: architecture,
self-healing design, authority, integration, publication, or anything touching a
named critical service. Routine lookups and mechanical execution should not
incur doctrine ceremony.

Each entry states when retrieval **changes the decision** (consult) and when it
would only add ceremony (skip). Respect both.
"""

FOOTER = """
## Reading this router

`status` is whether guidance applies now. `authority` is whether it is adopted
policy or advisory judgment. `confidence` is how well the grounds support it.
These are independent axes - `active` + `advisory` + `low` means use it now as
the best bounded model while staying ready to revise it.

A retrieval miss during real work is a doctrine defect, not a user error. Fix
the trigger, the placement, or the SOUL residue according to the cause.
"""


def collect():
    pages = []
    for path in sorted(DOCTRINE.rglob("*.md")):
        fm, _ = _yamlish.frontmatter(path.read_text(encoding="utf-8"))
        if not fm or fm.get("type") != "doctrine":
            continue
        if fm.get("status") != "active":
            continue
        fm["_path"] = path.relative_to(ROOT).as_posix()
        fm["_domain"] = path.parent.name
        pages.append(fm)
    return pages


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def render(pages):
    out = [HEADER]
    domains = {}
    for page in pages:
        domains.setdefault(page["_domain"], []).append(page)

    for domain in sorted(domains):
        out.append("\n## %s\n" % domain.replace("-", " ").title())
        for page in sorted(domains[domain], key=lambda p: p.get("id", "")):
            out.append("### [%s](%s)\n" % (page.get("id", "?"), page["_path"]))
            summary = page.get("router_summary")
            if summary:
                out.append("%s\n" % summary)
            out.append(
                "`status: %s` · `authority: %s` · `confidence: %s`\n"
                % (
                    page.get("status", "?"),
                    page.get("authority", "?"),
                    page.get("confidence", "?"),
                )
            )
            consult = as_list(page.get("consult_when"))
            if consult:
                out.append("**Consult when:**\n")
                out.extend("- %s" % item for item in consult)
            skip = as_list(page.get("do_not_use_when"))
            if skip:
                out.append("\n**Skip when:**\n")
                out.extend("- %s" % item for item in skip)
            effect = page.get("decision_effect")
            if effect:
                out.append("\n**Decision effect:** %s\n" % effect)
            out.append("")

    out.append(FOOTER)
    text = "\n".join(out)
    text = text.replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")
    if not text.endswith("\n"):
        text += "\n"
    return text


def main():
    pages = collect()
    if not pages:
        print("no active doctrine pages found under doctrine/", file=sys.stderr)
        return 1
    (ROOT / "index.md").write_text(render(pages), encoding="utf-8")
    print("index.md: %d active doctrine page(s)" % len(pages))
    return 0


if __name__ == "__main__":
    sys.exit(main())
