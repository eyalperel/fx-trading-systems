"""No-magic-numbers lint for the NNFX template (decision T11).

Usage:  python tools/lint_literals.py FILE [FILE ...]
Exit code 0 = no violations (exemptions allowed and listed), 1 = violations.

Logic files: the only numeric literals allowed are 0 and 1. Any other number fails
unless its line carries `// lint:allow <reason>` (non-empty reason); every exemption is
printed as an EXEMPT line. Numbers inside comments and string/char literals are ignored.

Config files (name ends in `_Config.h`): every line holding a number must carry a source
label in a comment on that line: (a), (b), (c), a decision id (T<n>, M-D<n>) or a source
key in [..]. Decimal literals fail there (Light-C reads them as float32, gotchas 9d.1):
build non-integers from integers, e.g. `x = 3; x /= 2;`.
"""
import re
import sys
from dataclasses import dataclass, field

# A numeric literal: hex, or decimal with optional fraction / exponent, not glued to an
# identifier character on the left.
NUM_RE = re.compile(r"(?<![A-Za-z0-9_.])(0[xX][0-9A-Fa-f]+|(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)")
ALLOWED = {"0", "1"}
ALLOW_RE = re.compile(r"lint:allow\b(.*)")
LABEL_RE = re.compile(r"\((?:a|b|c)\)|\bT\d+\b|\bM-D\d+\b|\[[^\]]+\]")


@dataclass
class Finding:
    line: int
    token: str
    reason: str


@dataclass
class Result:
    violations: list = field(default_factory=list)
    exemptions: list = field(default_factory=list)


def _split_code_comment(text):
    """Return per-line (code, comment) with string/char literals blanked in code."""
    code_lines, comment_lines = [""], [""]
    i, n = 0, len(text)
    in_block = False
    while i < n:
        ch = text[i]
        if ch == "\n":
            code_lines.append("")
            comment_lines.append("")
            i += 1
            continue
        if in_block:
            if text.startswith("*/", i):
                in_block = False
                i += 2
            else:
                comment_lines[-1] += ch
                i += 1
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            comment_lines[-1] += text[i + 2:j]
            i = j
            continue
        if text.startswith("/*", i):
            in_block = True
            i += 2
            continue
        if ch in "\"'":
            q = ch
            code_lines[-1] += " "
            i += 1
            while i < n and text[i] != q and text[i] != "\n":
                i += 2 if text[i] == "\\" else 1
            i += 1
            continue
        code_lines[-1] += ch
        i += 1
    return list(zip(code_lines, comment_lines))


def lint_text(text, mode="logic"):
    res = Result()
    for ln, (code, comment) in enumerate(_split_code_comment(text), start=1):
        tokens = NUM_RE.findall(code)
        if not tokens:
            continue
        if mode == "config":
            for t in tokens:
                if "." in t or "e" in t.lower() and not t.lower().startswith("0x"):
                    res.violations.append(Finding(ln, t, "decimal literal in config (float32); build from integers"))
            if not LABEL_RE.search(comment):
                res.violations.append(Finding(ln, tokens[0], "number without a source label ((a)/(b)/(c), T<n>, M-D<n> or [key])"))
            continue
        bad = [t for t in tokens if t not in ALLOWED]
        if not bad:
            continue
        m = ALLOW_RE.search(comment)
        if m and m.group(1).strip():
            res.exemptions.append(Finding(ln, ",".join(bad), m.group(1).strip()))
        else:
            for t in bad:
                res.violations.append(Finding(ln, t, "numeric literal other than 0 / 1" + (" (lint:allow needs a reason)" if m else "")))
    return res


def mode_for(path):
    return "config" if path.endswith("_Config.h") else "logic"


def main(paths):
    total_v = total_e = 0
    for p in paths:
        with open(p, encoding="utf-8") as f:
            r = lint_text(f.read(), mode_for(p))
        for v in r.violations:
            print(f"FAIL   {p}:{v.line}  {v.token}  {v.reason}")
        for e in r.exemptions:
            print(f"EXEMPT {p}:{e.line}  {e.token}  {e.reason}")
        total_v += len(r.violations)
        total_e += len(r.exemptions)
    print(f"lint_literals: {len(paths)} file(s), {total_v} violation(s), {total_e} exemption(s)")
    return 1 if total_v else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
