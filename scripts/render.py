#!/usr/bin/env python3
"""Render templates against a private vars file.

Direction of flow is one-way: templates + private vars -> rendered output.
Rendered output is private by definition and must never be committed here.
See SANITIZATION.md.

Usage:
    python3 scripts/render.py --vars ../pc_dr-src/vars.yml --out ../pc_dr-src/rendered
    python3 scripts/render.py --vars ../pc_dr-src/vars.yml --check
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _yamlish  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_SUFFIX = ".tmpl"
SEARCH_DIRS = ["stacks", "watchdogs", "automation", "agent", "reference"]

VAR = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


def resolve(flat, name):
    if name in flat:
        return flat[name]
    return None


def render_text(text, flat, where, missing):
    def substitute(match):
        name = match.group(1)
        value = resolve(flat, name)
        if value is None:
            missing.append("%s: {{ %s }}" % (where, name))
            return match.group(0)
        return str(value)
    return VAR.sub(substitute, text)


def find_templates():
    for name in SEARCH_DIRS:
        base = ROOT / name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*" + TEMPLATE_SUFFIX)):
            yield path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vars", required=True, help="path to your private vars.yml")
    parser.add_argument("--out", help="output directory (required unless --check)")
    parser.add_argument("--check", action="store_true",
                        help="report unresolved variables without writing output")
    args = parser.parse_args()

    vars_path = Path(args.vars).expanduser()
    if not vars_path.is_file():
        print("no such vars file: %s" % vars_path, file=sys.stderr)
        return 2

    try:
        resolved = vars_path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        resolved = None
    if resolved is not None and resolved.name != "vars.example.yml":
        print("refusing to read a vars file from inside the repository: %s" % resolved,
              file=sys.stderr)
        print("keep real values in a private tree outside this repo "
              "(see SANITIZATION.md)", file=sys.stderr)
        return 2

    flat = _yamlish.flatten(_yamlish.load(vars_path))
    templates = list(find_templates())
    if not templates:
        print("no %s templates found under %s" % (TEMPLATE_SUFFIX, ", ".join(SEARCH_DIRS)))
        return 0

    missing, written = [], 0
    out_root = Path(args.out).expanduser() if args.out else None

    if out_root is not None:
        try:
            out_root.resolve().relative_to(ROOT.resolve())
        except ValueError:
            pass
        else:
            print("refusing to write rendered output inside the repository",
                  file=sys.stderr)
            return 2

    for template in templates:
        rel = template.relative_to(ROOT)
        text = render_text(template.read_text(encoding="utf-8"), flat, rel.as_posix(), missing)
        if args.check or out_root is None:
            continue
        target = out_root / rel.with_suffix("")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        written += 1

    if missing:
        print("unresolved variables (%d):" % len(missing))
        for item in sorted(set(missing)):
            print(" -", item)
        print("\nAdd the missing keys to your vars file, or fix the template.")
        return 1

    if args.check:
        print("render --check: ok (%d template(s), all variables resolve)" % len(templates))
    else:
        print("rendered %d file(s) to %s" % (written, out_root))
        print("This output is PRIVATE. Do not commit it to this repository.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
