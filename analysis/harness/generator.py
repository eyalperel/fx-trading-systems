"""Generator (harness step 2, stage 3): spec (TOML) -> checker dict + one Zorro batch script.

Implements docs/harness/STEP2_HANDOFF.md "Stage 3" incl. Amendment 2.
  * load_spec / validate_spec: spec format and its refusal rules;
  * to_checker_spec: the dict analysis/harness/checker.py consumes;
  * build_script: the Light-C batch script (one [Test] click), H1's proven pattern, copied
    from strategies/tests/H1_SuperSmoother2Pole_Harness.c: constants built at run time from
    integers (gotchas 9d.1/9d.2), unconditional fixed-order calls, one row per fed bar,
    latch and write before quit() (9d.4), %.15f output;
  * lint_script: refuses a script that breaks a Light-C rule (see lint_script);
  * write_script: exclusive create, never overwrites a file.
No Zorro run happens here (stage 4).

Usage: python analysis/harness/generator.py SPEC.toml [--out-dir DIR] [--lint-only]
Labels: (a) source states, (b) verified here, (c) inference.
"""
import argparse
import copy
import math
import os
import re
import struct
import sys
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DEFAULT_OUT = os.path.join(REPO, "strategies", "tests")

LABEL_RE = re.compile(r"^\s*\((a|b|c)\)")
IDFRAG_RE = re.compile(r"^[A-Za-z0-9_]+$")


class SpecError(Exception):
    def __init__(self, errors):
        self.errors = errors            # list of (code, message)
        super().__init__("; ".join("%s: %s" % e for e in errors))


class LintError(Exception):
    def __init__(self, issues):
        self.issues = issues            # list of (rule, message)
        super().__init__("; ".join("%s: %s" % e for e in issues))


# ----------------------------------------------------------------------------- spec
def load_spec(path):
    with open(path, "rb") as f:
        return tomllib.load(f)


def input_ids(spec):
    return ["flat"] + ["s%d" % t for t in spec["inputs"]["sine_periods"]] + ["ramp"]


def _frac(pair):
    return pair[0] / pair[1]


def _has_label(s):
    return isinstance(s, str) and LABEL_RE.match(s) is not None


def validate_spec(spec):
    """Returns (errors, infos). errors: list of (code, message), a non-empty list means the spec
    is refused. infos: INFO lines (D2 floor and per-control margin), never a refusal."""
    err, info = [], []
    need = ["batch", "zorro", "inputs", "clock", "tolerances", "expected", "variants"]
    for k in need:
        if k not in spec:
            err.append(("STRUCT", "missing section [%s]" % k))
    if err:
        return err, info
    b = spec["batch"]
    for k in ("name", "id_prefix", "indicator", "script_name"):
        if k not in b:
            err.append(("STRUCT", "[batch] missing %s" % k))
    if err:
        return err, info

    def idcheck(what, v):
        if not isinstance(v, str) or not v:
            err.append(("ID_NOT_C", "%s %r is not a non-empty string" % (what, v)))
        elif "-" in v:
            err.append(("ID_HYPHEN", "%s %r contains '-' (check ids are <prefix>-<variantid>-<check>)"
                        % (what, v)))
        elif not IDFRAG_RE.match(v):
            err.append(("ID_NOT_C", "%s %r is not a valid C identifier fragment [A-Za-z0-9_]" % (what, v)))

    idcheck("batch id_prefix", b["id_prefix"])
    ts = spec["inputs"].get("sine_periods", [])
    for t in ts:
        if not isinstance(t, int) or isinstance(t, bool) or t <= 0:
            err.append(("ID_NOT_C", "input id from sine period %r is not a positive integer" % (t,)))
    seen = set()
    for v in spec["variants"]:
        idcheck("variant id", v.get("id"))
        if v.get("id") in seen:
            err.append(("STRUCT", "duplicate variant id %r" % v.get("id")))
        seen.add(v.get("id"))

    # source labels on every tolerance and expected table
    for q in ("flat", "gain", "lag", "x"):
        t = spec["tolerances"].get(q)
        if not isinstance(t, dict) or "value" not in t:
            err.append(("STRUCT", "[tolerances.%s] missing or without value" % q))
        elif not _has_label(t.get("source")):
            err.append(("SOURCE_MISSING", "tolerance %s has no (a)/(b)/(c) source label" % q))
    for name, t in spec["expected"].items():
        if not _has_label(t.get("source")):
            err.append(("SOURCE_MISSING", "expected table %s has no (a)/(b)/(c) source label" % name))
        if len(t.get("gains", [])) != len(ts):
            err.append(("STRUCT", "expected table %s: %d gains for %d sine periods"
                        % (name, len(t.get("gains", [])), len(ts))))
        for k in ("flat", "lag"):
            if not isinstance(t.get(k), (int, float)):
                err.append(("STRUCT", "expected table %s: %s missing" % (name, k)))

    # variants
    roles = [v.get("role") for v in spec["variants"]]
    for v in spec["variants"]:
        vid = v.get("id")
        if v.get("role") not in ("real", "neg_control"):
            err.append(("STRUCT", "variant %s: role must be real or neg_control" % vid))
        if v.get("expected") not in spec["expected"]:
            err.append(("STRUCT", "variant %s: expected table %r not defined" % (vid, v.get("expected"))))
        if not isinstance(v.get("param"), int):
            err.append(("STRUCT", "variant %s: param must be an integer" % vid))
        if v.get("kind") == "inline":
            fn, body = v.get("function"), v.get("body")
            if not fn or not isinstance(body, str) or not re.search(r"\b%s\s*\(" % re.escape(fn), body):
                err.append(("STRUCT", "variant %s: inline needs function and a body defining it" % vid))
        elif v.get("kind") != "param":
            err.append(("STRUCT", "variant %s: kind must be param or inline" % vid))
    if "neg_control" not in roles:
        err.append(("NO_NEG_CONTROL", "no negative control (D2 Amendment 1: a control that is "
                                      "never seen to fail means the harness could be broken)"))

    # D1 literal replacements
    for r in spec.get("literal_replacements", []):
        if not r.get("literal"):
            err.append(("LITERAL_INCOMPLETE", "literal replacement without literal: %r" % (r,)))
        elif not isinstance(r.get("exact"), (int, float)):
            err.append(("LITERAL_INCOMPLETE", "literal replacement %r without exact value" % r["literal"]))
        elif not _has_label(r.get("source")):
            err.append(("LITERAL_INCOMPLETE", "literal replacement %r without (a)/(b)/(c) source"
                        % r["literal"]))
    if err:
        return err, info

    # INFO only: D2 floor x 10 <= tolerance per quantity; per-control 10x margin
    tol = {q: spec["tolerances"][q]["value"] for q in ("flat", "gain", "lag")}
    fl = spec.get("floor")
    for q in ("gain", "lag", "flat"):
        if fl and q in fl:
            ok = fl[q] * 10 <= tol[q]
            info.append("INFO D2 floor %s: floor %.3e x10 = %.3e %s tolerance %.3e -> %s"
                        % (q, fl[q], fl[q] * 10, "<=" if ok else ">", tol[q],
                           "window ok" if ok else "FLOOR x10 EXCEEDS TOLERANCE"))
        else:
            info.append("INFO D2 floor %s: no floor in spec (not checked)" % q)
    for v in spec["variants"]:
        if v["role"] != "neg_control":
            continue
        eff = v.get("effect")
        if not eff:
            info.append("INFO D2 margin %s: no measured effect in spec (not checked)" % v["id"])
            continue
        ratios = {q: eff[q] / tol[q] for q in ("gain", "lag", "flat") if q in eff}
        best = max(ratios, key=ratios.get)
        info.append("INFO D2 margin %s: error/tolerance %s -> %s"
                    % (v["id"], ", ".join("%s %.3gx" % (q, r) for q, r in ratios.items()),
                       "10x margin met (%s)" % best if ratios[best] >= 10 else "10x margin NOT met"))
    return err, info


def to_checker_spec(spec):
    """The dict analysis/harness/checker.py consumes (checker.h1_spec() has the same shape)."""
    errs, _ = validate_spec(spec)
    if errs:
        raise SpecError(errs)
    inp, b, t = spec["inputs"], spec["batch"], spec["tolerances"]
    variants = []
    for v in spec["variants"]:
        e = spec["expected"][v["expected"]]
        variants.append(dict(id=v["id"], params=v["label"], role=v["role"],
                             expected=(e["flat"], list(e["gains"]), e["lag"])))
    return dict(batch=b["name"], id_prefix=b["id_prefix"], indicator=b["indicator"],
                asset=b["asset_label"],
                n_bars=inp["n_bars"], w=inp["warmup"], level=_frac(inp["level"]),
                amp=_frac(inp["amp"]), slope=_frac(inp["slope"]), ts=tuple(inp["sine_periods"]),
                clock_lo=spec["clock"]["lo"], clock_hi=spec["clock"]["hi"],
                tol_flat=t["flat"]["value"], tol_gain=t["gain"]["value"], tol_lag=t["lag"]["value"],
                tol_x=t["x"]["value"], variants=variants)


# ----------------------------------------------------------------------------- script
def _chunks(items, size):
    return [items[i:i + size] for i in range(0, len(items), size)]


def _fn_of(spec, v):
    return v["function"] if v["kind"] == "inline" else spec["batch"]["indicator"]


def build_script(spec):
    """Returns (script text, list of inline function bodies). Raises SpecError if the spec is
    refused. The text is not linted here (write_script lints)."""
    errs, _ = validate_spec(spec)
    if errs:
        raise SpecError(errs)
    b, z, inp = spec["batch"], spec["zorro"], spec["inputs"]
    P = b["id_prefix"].upper()
    p = b["id_prefix"].lower()
    ts = inp["sine_periods"]
    ids = input_ids(spec)
    nin = len(ids)
    variants = spec["variants"]
    nvar = len(variants)
    ncalls = nvar * nin
    N = inp["n_bars"]
    L = []
    a = L.append

    # ---- header comment
    a("// %s.c  (GENERATED by analysis/harness/generator.py from the spec; edit the spec, not this file)" % b["script_name"])
    a("//")
    a("// PURPOSE:  Batch harness %s. Feeds synthetic inputs through %s (%d variants:" % (b["id_prefix"], b["indicator"], nvar))
    a("//           %s) and writes the RAW outputs. It does NOT judge anything." % ", ".join(
        v["id"] + (" [control]" if v["role"] == "neg_control" else "") for v in variants))
    a("//           Python (analysis/harness/checker.py) measures and writes PASS/FAIL.")
    a("// PREREG:   %s" % b["prereg"])
    a("// INPUTS:   Synthetic only, from the bar counter n: flat | level+amp*sin(2*pi*n/T), T=%s | ramp level+slope*n"
      % ",".join(str(t) for t in ts))
    a("//           level=%d/%d amp=%d/%d slope=%d/%d. (b, H1 run 1) Decimal literals are float32 in this Zorro"
      % (inp["level"][0], inp["level"][1], inp["amp"][0], inp["amp"][1], inp["slope"][0], inp["slope"][1]))
    a("//           build and the PI macro is 3.14159, so every constant is built at run time from integers.")
    a("//           %s is used only as a bar clock; clock_close is exported for the checker's magnitude guard." % z["clock_asset"])
    a("// OUTPUT:   %s  (%d rows n=0..%d + header; %d columns; values printed with 15 decimals)"
      % (z["raw_file"], N, N - 1, 2 + nin + nvar * nin))
    a("// CALLS:    %d filter calls per bar, variant-major, unconditional, fixed order (gotchas 3.1)." % ncalls)
    a("// FEEDING:  every x[n], n=0..%d, reaches the filters exactly once; INITRUN and EXITRUN feed and write nothing." % (N - 1))
    a("// NO LOOKBACK GUARD: LookBack = 0, warmup bars are exported too; the checker requires n = 0..%d contiguous." % (N - 1))
    a("// SOURCES:  expected values and tolerances are in the spec, each with an (a)/(b)/(c) label.")
    a("//           Pattern copied from strategies/tests/H1_SuperSmoother2Pole_Harness.c (b: H1 run 2 PASS).")
    a("// Y[] index = variant*%d + input." % nin)
    a("")
    a("#include <default.c>")
    a('#include "%s"' % z["include"])
    a("")
    a('#define %s_RAW "%s"' % (P, z["raw_file"]))
    a('#define %s_MARK "%s"' % (P, z["marker_file"]))
    a("#define %s_NBARS %d" % (P, N))
    a("")
    a("static int %s_n = 0;" % p)
    a("static int %s_done = 0;" % p)
    a("static int %s_hdr = 0;" % p)
    a("static int %s_rows = 0;" % p)
    a("")
    bodies = []
    for v in variants:
        if v["kind"] == "inline":
            for line in v.get("comment", "").splitlines():
                a("// " + line)
            body = v["body"].rstrip("\n")
            bodies.append(body)
            L.extend(body.split("\n"))
            a("")
    a("void run()")
    a("{")
    a("\t// Settings must be assigned on every call, including INITRUN, or Zorro never sees them.")
    a("\tBarPeriod = %d;" % z["bar_period"])
    a("\tStartDate = %d;" % z["start_date"])
    a("\tEndDate   = %d;" % z["end_date"])
    a("\tLookBack  = 0;")
    a('\tasset("%s");' % z["clock_asset"])
    a("")
    a("\tif(is(INITRUN)) {")
    a("\t\t%s_n = 0; %s_done = 0; %s_hdr = 0; %s_rows = 0;\t// declared initialisers" % (p, p, p, p))
    a("\t\tfile_delete(%s_RAW);" % P)
    a("\t\tfile_delete(%s_MARK);" % P)
    a("\t\treturn;")
    a("\t}")
    a("\tif(is(EXITRUN)) {")
    a('\t\tprintf("\\n%s EXIT: rows written = %%d, done = %%d  (expected %d and 1)", %s_rows, %s_done);'
      % (b["id_prefix"], N, p, p))
    a("\t\t// marker file: if it exists after the run, EXITRUN ran even if the printf was lost (gotchas 9d.4)")
    a('\t\tfile_append(%s_MARK, strf("EXITRUN ran: rows=%%d done=%%d\\n", %s_rows, %s_done), 0);' % (P, p, p))
    a("\t\treturn;")
    a("\t}")
    a("")
    a("\tint n;")
    a("\tvar X[%d];" % nin)
    a("\tvar Y[%d];" % ncalls)
    a("\tn = %s_n;" % p)
    a("")
    a("\t// --- constants built at RUN TIME from integers (gotchas 9d.1, 9d.2) ---")
    a("\tvar lvl = %d;\tlvl = lvl / %d;" % tuple(inp["level"]))
    a("\tvar amp = %d;\tamp = amp / %d;" % tuple(inp["amp"]))
    a("\tvar slp = %d;\tslp = slp / %d;" % tuple(inp["slope"]))
    a("\tvar pi_x = 4;\tpi_x = pi_x * atan(1);")
    a("")
    a("\t// --- inputs from the bar counter (radians); no decimal literal, no PI macro ---")
    a("\tX[0] = lvl;")
    for k, t in enumerate(ts, start=1):
        a("\tX[%d] = lvl + amp * sin(2 * pi_x * n / %d);" % (k, t))
    a("\tX[%d] = lvl + slp * n;" % (nin - 1))
    a("")
    a("\t// --- input series: %d unconditional calls, fixed order ---" % nin)
    for k in range(nin):
        a("\tvars S%d = series(X[%d], %d);" % (k, k, z["series_len"]))
    a("")
    a("\t// --- %d filter calls, variant-major, unconditional, fixed order ---" % ncalls)
    slot = 0
    for v in variants:
        for k, iid in enumerate(ids):
            a("\tY[%d] = %s(S%d, %d);\t// %s %s" % (slot, _fn_of(spec, v), k, v["param"], v["id"], iid))
            slot += 1
    a("")
    a("\t// --- write one row per fed bar ---")
    a("\tif(!%s_done) {" % p)
    a("\t\tif(!%s_hdr) {" % p)
    hdr_cols = ["n", "clock_close"] + ["x_" + i for i in ids]
    a('\t\t\tfile_append(%s_RAW, "%s", 0);' % (P, ",".join(hdr_cols)))
    for v in variants:
        a('\t\t\tfile_append(%s_RAW, ",%s", 0);' % (P, ",".join("y_%s_%s" % (v["id"], i) for i in ids)))
    a('\t\t\tfile_append(%s_RAW, "\\n", 0);' % P)
    a("\t\t\t%s_hdr = 1;" % p)
    a("\t\t}")
    first = [("%d", "n"), ("%.15f", "priceClose()")] + [("%.15f", "X[%d]" % k) for k in range(nin)]
    for ci, ch in enumerate(_chunks(first, 9)):
        fmt = ",".join(f for f, _ in ch)
        args = ", ".join(e for _, e in ch)
        a('\t\tfile_append(%s_RAW, strf("%s%s", %s), 0);' % (P, "," if ci else "", fmt, args))
    for vi in range(nvar):
        for ci, ch in enumerate(_chunks(list(range(vi * nin, (vi + 1) * nin)), 9)):
            fmt = ",".join("%.15f" for _ in ch)
            args = ",".join("Y[%d]" % j for j in ch)
            a('\t\tfile_append(%s_RAW, strf(",%s", %s), 0);' % (P, fmt, args))
    a('\t\tfile_append(%s_RAW, "\\n", 0);' % P)
    a("\t\t%s_rows += 1;" % p)
    a("\t\tif(n == %s_NBARS - 1) {" % P)
    a("\t\t\t%s_done = 1;\t// latch first; nothing is written after this row" % p)
    a('\t\t\tquit("%s batch complete: %d rows written");' % (b["id_prefix"], N))
    a("\t\t} else {")
    a("\t\t\t%s_n += 1;" % p)
    a("\t\t}")
    a("\t}")
    a("}")
    return "\n".join(L) + "\n", bodies


# ----------------------------------------------------------------------------- lint
_STRIP_RE = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:[^"\\\n]|\\.)*"', re.S)
_DECIMAL_RE = re.compile(r"(?<![\w.])(\d+\.\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+)(?![\w.])")


def _strip(text):
    return _STRIP_RE.sub(" ", text)


def _f32_exact(x):
    try:
        return struct.unpack("f", struct.pack("f", x))[0] == x
    except OverflowError:
        return False


def lint_script(text, inline_bodies=(), include_base=DEFAULT_OUT):
    """Returns a list of (rule, message); empty = clean.
    L_PI        no `PI` token in harness plumbing (comments, strings and the inline negative-control
                bodies excluded: they are mutated indicator copies, D3 allows PI; Amendment 2).
    L_FLOAT32   no decimal literal whose float32 value differs from its float64 value (gotchas
                9d.1). Applies to the whole script including inline bodies.
    L_QUIT      no file_append after quit( in the same block (9d.4).
    L_INCLUDE   every #include "path" resolves from include_base (strategies/tests/) to an
                existing file (9d.3). <angle> includes are not checked."""
    issues = []
    plumbing = text
    for body in inline_bodies:
        plumbing = plumbing.replace(body, " ")
    for m in re.finditer(r"\bPI\b", _strip(plumbing)):
        issues.append(("L_PI", "PI token in harness code (line %d of the plumbing text)"
                       % (_strip(plumbing)[:m.start()].count("\n") + 1)))
        break
    clean = _strip(text)
    for m in _DECIMAL_RE.finditer(clean):
        tok = m.group(1)
        if not _f32_exact(float(tok)):
            issues.append(("L_FLOAT32", "decimal literal %s is not float32-exact (line %d)"
                           % (tok, clean[:m.start()].count("\n") + 1)))
    for m in re.finditer(r"\bquit\s*\(", clean):
        depth = 0
        for ch_i in range(m.end(), len(clean)):
            ch = clean[ch_i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth < 0:
                    break
            elif clean.startswith("file_append", ch_i):
                issues.append(("L_QUIT", "file_append after quit( in the same block (line %d)"
                               % (clean[:ch_i].count("\n") + 1)))
                break
    for line in text.split("\n"):
        mi = re.match(r'\s*#include\s+"([^"]+)"', line)
        if mi and not os.path.isfile(os.path.normpath(os.path.join(include_base, mi.group(1)))):
            issues.append(("L_INCLUDE", "include %r does not resolve from %s" % (mi.group(1), include_base)))
    return issues


# ----------------------------------------------------------------------------- writer
def write_script(spec, out_dir, include_base=DEFAULT_OUT):
    """Lint, then write <out_dir>/<script_name>.c with exclusive create (FileExistsError if the
    file exists: an existing .c is never overwritten). Returns the path."""
    text, bodies = build_script(spec)
    issues = lint_script(text, bodies, include_base)
    if issues:
        raise LintError(issues)
    path = os.path.join(out_dir, spec["batch"]["script_name"] + ".c")
    with open(path, "x", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out-dir", default=DEFAULT_OUT)
    ap.add_argument("--lint-only", action="store_true")
    a = ap.parse_args()
    spec = load_spec(a.spec)
    errs, infos = validate_spec(spec)
    for c, m in errs:
        print("SPEC REFUSED %s: %s" % (c, m))
    for i in infos:
        print(i)
    if errs:
        sys.exit(2)
    text, bodies = build_script(spec)
    issues = lint_script(text, bodies)
    for r, m in issues:
        print("LINT REFUSED %s: %s" % (r, m))
    if issues:
        sys.exit(3)
    if a.lint_only:
        print("lint clean; nothing written")
        return
    print("written: " + write_script(spec, a.out_dir))


if __name__ == "__main__":
    main()
