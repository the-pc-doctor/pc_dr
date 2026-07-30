#!/usr/bin/env python3
"""Publication gate. Deny-by-default scan for private material.

See SANITIZATION.md for the threat model and the deny classes.

Two rules this script exists to enforce mechanically:

  1. Placeholders use reserved ranges (RFC 5737 addresses, RFC 2606 domains),
     so any real value is a hard failure rather than a judgment call.
  2. The identity denylist is loaded from OUTSIDE the repository, because a
     committed denylist of real names and hostnames discloses exactly the
     values it exists to exclude.

Usage:
    python3 scripts/check_sanitization.py [--strict] [--history] [--quiet]

    --strict    fail when no identity denylist is available (use in CI and
                before any push)
    --history   additionally scan every blob reachable in git history; a secret
                removed in a later commit is still published
"""

import argparse
import math
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "rendered", "out", ".venv", "node_modules"}
SKIP_NAMES = {".denylist.local", "denylist.txt"}
TEXT_SUFFIXES = {
    ".md", ".py", ".yml", ".yaml", ".sh", ".txt", ".tmpl", ".service",
    ".timer", ".conf", ".json", ".env", ".example", ".cfg", ".ini", "",
}

PRAGMA = re.compile(r"#\s*sanitize:allow\s+(\S+)")

# Reserved placeholder space. Anything in these is intentional.
ALLOWED_IP = re.compile(r"\b(?:192\.0\.2|198\.51\.100|203\.0\.113)\.\d{1,3}\b")
ALLOWED_DOMAINS = ("example.com", "example.org", "example.net", "lab.example", "lab.internal")
ALLOWED_MAC_PREFIX = "de:ad:be:ef"
ALLOWED_LITERALS = {
    # Network base addresses, not hosts. The CGNAT range is named in the docs
    # as a range that is denied; the range notation itself is not an address.
    "100.64.0.0", "10.0.0.0", "172.16.0.0", "192.168.0.0",
    "192.0.2.0", "198.51.100.0", "203.0.113.0",
    "0.0.0.0", "127.0.0.1", "255.255.255.255",
}
ALLOWED_HOME_USERS = {"operator", "user", "agent", "youruser", "someuser", "$USER"}
PLACEHOLDER_VALUE = re.compile(
    r"^\s*(?:\{\{.*\}\}|\$\{?[\w:?+\-]*\}?|<[^>]+>|CHANGEME|REPLACE\w*|example\S*|"
    r"placeholder\S*|your[-_]\S*|\S*_ref|null|~|)\s*$",
    re.I,
)

# systemd template units (`unit@instance.timer`) and similar constructs match  # sanitize:allow pattern-definition
# the email pattern. The distinguishing feature is that the right-hand side
# ends in a file or unit extension rather than a top-level domain.
NOT_A_DOMAIN = re.compile(
    r"\.(?:timer|service|socket|target|mount|path|slice|device|swap|automount|"
    r"yaml|yml|sh|py|md|json|conf|cfg|ini|tmpl|log|txt|example|local|internal)$",
    re.I,
)

NETWORK_PATTERNS = [
    ("rfc1918 address", re.compile(
        r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
        r"|192\.168\.\d{1,3}\.\d{1,3})\b")),
    ("carrier-grade nat / overlay address", re.compile(
        r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b")),
    ("hardware address", re.compile(r"\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b", re.I)),
    ("dynamic dns hostname", re.compile(
        r"\b[\w-]+\.(?:asuscomm\.com|duckdns\.org|no-ip\.\w+|dynu\.\w+|ddns\.net"
        r"|synology\.me|myqnapcloud\.com|ts\.net|tailnet\.\w+)\b", re.I)),
]

SECRET_PATTERNS = [
    ("private key block", re.compile(r"-{5}BEGIN [A-Z ]*PRIVATE KEY")),  # sanitize:allow pattern-definition
    ("provider api key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),  # sanitize:allow pattern-definition
    ("github token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{30,}")),  # sanitize:allow pattern-definition
    ("aws access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),  # sanitize:allow pattern-definition
    ("bot token", re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b")),  # sanitize:allow pattern-definition
    ("json web token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),  # sanitize:allow pattern-definition
    ("basic auth in url", re.compile(r"://[^/\s:@]+:[^/\s@]{4,}@")),  # sanitize:allow pattern-definition
    ("authorization header value", re.compile(r"Authorization\s*:\s*(?:Basic|Bearer)\s+[A-Za-z0-9+/=_.-]{12,}", re.I)),  # sanitize:allow pattern-definition
]

SECRET_ASSIGN = re.compile(
    r"(?P<key>[\w.\-]*(?:password|passwd|secret|api[_-]?key|apikey|token|bearer))"
    r"\s*[:=]\s*(?P<value>[^\s,;#}\]]+)",
    re.I,
)

HOME_PATH = re.compile(r"/(?:home|Users)/([A-Za-z][\w.\-]{1,})")
EMAIL = re.compile(r"\b[\w.+-]+@([\w-]+\.[\w.-]+)\b")
HIGH_ENTROPY = re.compile(r"\b[A-Za-z0-9+/=_-]{24,}\b")
LONG_HEX = re.compile(r"\b[0-9a-f]{32,}\b", re.I)


class Finding:
    def __init__(self, where, line_no, label, sample):
        self.where, self.line_no, self.label = where, line_no, label
        self.sample = sample if len(sample) <= 60 else sample[:57] + "..."

    def __str__(self):
        loc = "%s:%s" % (self.where, self.line_no) if self.line_no else self.where
        return "%s  [%s]  %s" % (loc, self.label, self.sample)


def load_denylist():
    """Load real identifiers from outside the repository. Never committed."""
    candidates = []
    env = os.environ.get("PC_DR_DENYLIST")
    if env:
        candidates.append(Path(env))
    candidates += [ROOT / ".denylist.local", ROOT.parent / "denylist.txt"]
    for path in candidates:
        if path.is_file():
            literals, regexes = [], []
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("re:"):
                    try:
                        regexes.append(re.compile(line[3:], re.I))
                    except re.error as exc:
                        print("warning: bad regex in denylist: %s (%s)" % (line, exc),
                              file=sys.stderr)
                else:
                    literals.append(re.compile(r"\b%s\b" % re.escape(line), re.I))
            return path, literals + regexes
    return None, []


def entropy(token):
    counts = Counter(token)
    total = len(token)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def looks_random(token):
    """Heuristic: mixed case, digits, and high entropy - not an identifier."""
    if not (any(c.isupper() for c in token) and any(c.islower() for c in token)):
        return False
    if sum(c.isdigit() for c in token) < 2:
        return False
    if "-" in token or "_" in token and token.count("_") > 2:
        return False
    return entropy(token) >= 3.6


def scan_text(where, text, denylist, findings):
    for line_no, line in enumerate(text.splitlines(), 1):
        pragma = PRAGMA.search(line)
        if pragma:
            continue

        for label, pattern in NETWORK_PATTERNS:
            for match in pattern.finditer(line):
                hit = match.group(0)
                if hit in ALLOWED_LITERALS or ALLOWED_IP.fullmatch(hit):
                    continue
                if label == "hardware address" and hit.lower().startswith(ALLOWED_MAC_PREFIX):
                    continue
                findings.append(Finding(where, line_no, label, hit))

        for label, pattern in SECRET_PATTERNS:
            match = pattern.search(line)
            if match:
                findings.append(Finding(where, line_no, label, match.group(0)))

        for match in SECRET_ASSIGN.finditer(line):
            key, value = match.group("key"), match.group("value")
            if key.lower().endswith(("_ref", "-ref")):
                continue
            if PLACEHOLDER_VALUE.match(value.strip("\"'")):
                continue
            if value.strip("\"'").lower() in ("true", "false", "none", "required", "optional"):
                continue
            # Source code, not a credential: a function call. A real secret is
            # an opaque literal, never an expression.
            #
            # Deliberately narrow. An earlier version also skipped anything
            # matching `identifier.identifier`, which would have skipped a
            # dotted secret such as a token in three parts - so that is gone.
            if "(" in value:
                continue
            findings.append(Finding(where, line_no, "credential assignment",
                                    "%s = %s" % (key, value)))

        for match in HOME_PATH.finditer(line):
            user = match.group(1)
            if user not in ALLOWED_HOME_USERS and not user.startswith(("{{", "$", "<")):
                findings.append(Finding(where, line_no, "real home path", match.group(0)))

        for match in EMAIL.finditer(line):
            domain = match.group(1)
            if domain.lower() in ALLOWED_DOMAINS or NOT_A_DOMAIN.search(domain):
                continue
            findings.append(Finding(where, line_no, "email address", match.group(0)))

        for match in LONG_HEX.finditer(line):
            findings.append(Finding(where, line_no, "long hex run", match.group(0)))

        for match in HIGH_ENTROPY.finditer(line):
            token = match.group(0)
            if looks_random(token):
                findings.append(Finding(where, line_no, "high-entropy string", token))

        for pattern in denylist:
            match = pattern.search(line)
            if match:
                findings.append(Finding(where, line_no, "denylisted identifier",
                                        match.group(0)))


def iter_files():
    for path in sorted(ROOT.rglob("*")):
        parts = path.relative_to(ROOT).parts
        if any(part in SKIP_DIRS for part in parts) or path.name in SKIP_NAMES:
            continue
        if not path.is_file():
            continue
        if path.suffix not in TEXT_SUFFIXES:
            continue
        yield path


def scan_history(denylist, findings):
    try:
        objects = subprocess.run(
            ["git", "-C", str(ROOT), "rev-list", "--objects", "--all"],
            capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("warning: --history requested but git history is unavailable",
              file=sys.stderr)
        return 0
    candidates = []
    for row in objects.splitlines():
        parts = row.split(maxsplit=1)
        if len(parts) != 2:
            continue
        sha, name = parts
        if Path(name).name in SKIP_NAMES:
            continue
        if Path(name).suffix not in TEXT_SUFFIXES or not Path(name).suffix:
            continue
        candidates.append((sha, name))

    # Keep blobs only. Tree objects list child SHAs, which would otherwise be
    # reported as long hex runs - noise that would train you to ignore output.
    if candidates:
        check = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "--batch-check"],
            input="\n".join(sha for sha, _ in candidates) + "\n",
            capture_output=True, text=True)
        blobs = {
            line.split()[0] for line in check.stdout.splitlines()
            if len(line.split()) >= 2 and line.split()[1] == "blob"
        }
        candidates = [(sha, name) for sha, name in candidates if sha in blobs]

    seen = 0
    for sha, name in candidates:
        blob = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-p", sha],
                              capture_output=True)
        if blob.returncode:
            continue
        try:
            text = blob.stdout.decode("utf-8")
        except UnicodeDecodeError:
            continue
        seen += 1
        scan_text("history:%s (%s)" % (name, sha[:8]), text, denylist, findings)
    return seen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true",
                        help="fail when no identity denylist is available")
    parser.add_argument("--history", action="store_true",
                        help="also scan every blob reachable in git history")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    denylist_path, denylist = load_denylist()
    findings = []

    scanned = 0
    for path in iter_files():
        scanned += 1
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(Finding(path.relative_to(ROOT).as_posix(), 0,
                                    "unreadable text file", path.name))
            continue
        scan_text(path.relative_to(ROOT).as_posix(), text, denylist, findings)

    history_blobs = scan_history(denylist, findings) if args.history else 0

    if denylist_path:
        if not args.quiet:
            print("denylist: %d pattern(s) from %s" % (len(denylist), denylist_path))
    else:
        print("WARNING: no identity denylist found. Personal names, real "
              "hostnames, device names, and record identifiers are NOT being "
              "checked. See SANITIZATION.md and scripts/denylist.example.txt.",
              file=sys.stderr)

    allowances = subprocess.run(
        ["grep", "-rn", "sanitize:allow", str(ROOT), "--exclude-dir=.git"],
        capture_output=True, text=True).stdout.strip()
    allowance_count = len(allowances.splitlines()) if allowances else 0

    if findings:
        print("check_sanitization: %d finding(s) in %d file(s)%s"
              % (len(findings), scanned,
                 " + %d history blob(s)" % history_blobs if args.history else ""))
        for finding in findings:
            print(" -", finding)
        print("\nEach finding is a publication blocker. Fix the source, or mark a")
        print("reviewed exception inline with:  # sanitize:allow <reason>")
        return 1

    print("check_sanitization: ok (%d file(s)%s, %d reviewed allowance(s))"
          % (scanned,
             " + %d history blob(s)" % history_blobs if args.history else "",
             allowance_count))

    if args.strict and not denylist_path:
        print("check_sanitization: FAIL - --strict requires an identity denylist")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
