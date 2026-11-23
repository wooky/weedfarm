"""Minimal S-expression reader/writer for KiCad files."""
import re

_TOKEN = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))', re.S)


class Sym(str):
    """Unquoted atom."""


def parse(text):
    stack, cur = [], []
    pos = 0
    while True:
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        op, cl, qs, atom = m.groups()
        if op:
            stack.append(cur)
            cur = []
        elif cl:
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif qs is not None:
            cur.append(bytes(qs[1:-1], "utf-8").decode("unicode_escape") if "\\" in qs else qs[1:-1])
        else:
            cur.append(Sym(atom))
    return cur[0]


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def dump(e, indent=0):
    if isinstance(e, list):
        inner = [dump(x, indent + 1) for x in e]
        flat = "(" + " ".join(inner) + ")"
        if len(flat) < 100 and "\n" not in flat:
            return flat
        pad = "\n" + "  " * (indent + 1)
        return "(" + inner[0] + "".join(pad + x for x in inner[1:]) + ")"
    if isinstance(e, Sym):
        return str(e)
    if isinstance(e, bool):
        return "yes" if e else "no"
    if isinstance(e, (int, float)):
        return f"{e:g}" if isinstance(e, float) else str(e)
    return q(e)


def find(e, key):
    return [x for x in e if isinstance(x, list) and x and x[0] == key]


def find1(e, key):
    r = find(e, key)
    return r[0] if r else None
