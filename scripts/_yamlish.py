"""Minimal YAML-subset reader. Standard library only.

This project deliberately has no third-party dependencies, so that validation
works on a fresh clone with nothing installed. PyYAML is used when it happens
to be available; otherwise the subset parser below handles what this repository
actually uses:

  * nested mappings by indentation
  * block sequences of scalars and of inline mappings
  * inline flow mappings on one line: { key: value, key2: value2 }
  * scalars typed as int, float, bool, null, or str
  * quoted scalars, which may contain ": "
  * `#` comments and blank lines

Anything beyond that subset - anchors, multi-line scalars, nested flow
sequences, multiple documents - is not supported and not used here.
"""

import re

try:  # pragma: no cover - depends on host
    import yaml as _pyyaml
except ImportError:  # pragma: no cover
    _pyyaml = None


def _scalar(raw):
    s = raw.strip()
    if not s:
        return None
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def _split_top(text):
    """Split a flow-mapping body on commas that are not inside quotes."""
    parts, buf, quote = [], "", None
    for ch in text:
        if quote:
            if ch == quote:
                quote = None
            buf += ch
        elif ch in "\"'":
            quote = ch
            buf += ch
        elif ch == ",":
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)
    return parts


def _flow_map(body):
    out = {}
    for part in _split_top(body):
        if ":" not in part:
            continue
        k, v = part.split(":", 1)
        out[k.strip()] = _scalar(v)
    return out


def _strip_comment(line):
    out, quote = "", None
    for ch in line:
        if quote:
            if ch == quote:
                quote = None
            out += ch
        elif ch in "\"'":
            quote = ch
            out += ch
        elif ch == "#":
            break
        else:
            out += ch
    return out.rstrip()


def _rows(text):
    """Yield (indent, content) for every significant line."""
    for raw in text.splitlines():
        line = _strip_comment(raw)
        if not line.strip():
            continue
        yield len(line) - len(line.lstrip(" ")), line.strip()


def _parse_block(rows, i, indent):
    """Parse a mapping or sequence at `indent`. Returns (value, next_index)."""
    if rows[i][1].startswith("- "):
        seq = []
        while i < len(rows) and rows[i][0] == indent and rows[i][1].startswith("- "):
            item = rows[i][1][2:].strip()
            if item.startswith("{") and item.endswith("}"):
                seq.append(_flow_map(item[1:-1]))
            else:
                seq.append(_scalar(item))
            i += 1
        return seq, i

    mapping = {}
    while i < len(rows) and rows[i][0] == indent and not rows[i][1].startswith("- "):
        content = rows[i][1]
        if ":" not in content:
            raise ValueError("unparsable line: %r" % content)
        key, rest = content.split(":", 1)
        key, rest = key.strip(), rest.strip()
        if rest.startswith("{") and rest.endswith("}"):
            mapping[key] = _flow_map(rest[1:-1])
            i += 1
        elif rest:
            mapping[key] = _scalar(rest)
            i += 1
        else:
            i += 1
            if i < len(rows) and rows[i][0] > indent:
                mapping[key], i = _parse_block(rows, i, rows[i][0])
            else:
                mapping[key] = None
    return mapping, i


def loads(text):
    """Parse a YAML-subset document into Python data."""
    if _pyyaml is not None:
        return _pyyaml.safe_load(text)
    rows = list(_rows(text))
    if not rows:
        return {}
    value, _ = _parse_block(rows, 0, rows[0][0])
    return value


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return loads(fh.read())


SCALAR_KEYS = ()


def frontmatter(text):
    """Return (frontmatter_dict, body). Empty dict when absent."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 3)
    if end == -1:
        return {}, text
    return loads(text[4:end + 1]) or {}, text[end + 5:]


def flatten(data, prefix=""):
    """Flatten nested mappings into {'a.b.c': value}."""
    out = {}
    if isinstance(data, dict):
        for k, v in data.items():
            key = "%s.%s" % (prefix, k) if prefix else str(k)
            if isinstance(v, dict):
                out.update(flatten(v, key))
            else:
                out[key] = v
    return out
