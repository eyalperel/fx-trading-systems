"""Checker (harness step 2, stage 2): generic version of analysis/harness/h1_check.py.

Implements docs/harness/STEP2_HANDOFF.md, "Stage 2 - checker" (pre-registered 2026-11-06).
Given a spec (plain dict, format is stage 3's job; `h1_spec()` is the hand-written one that
reproduces H1's setup) and a Zorro raw CSV it: builds the inputs, runs the eleven H1 guards,
measures flat error / least-squares sine gain / ramp lag, compares with the spec's expected
values, builds the negative-control report and writes a results file (exclusive create).
No Zorro run and no .c file is read here.

Copied from h1_check.py (H1 files are not modified; each copy cites its source function):
make_inputs, m_flat, m_gain, m_lag, load_raw, validate, next_results_path, check_rows.
Differences from H1, all by the stage 2 criteria:
  * column list, row count, input parameters and clock range come from the spec;
  * guard ERROR rows are written and the run continues to the results file;
  * results store expected/actual at full precision (repr) and abs_diff at %.3e (CLAUDE.md
    section 7); H1 stored %.6f;
  * a non-finite measurement is an ERROR row (H1: FAIL); unreachable after G_NONFINITE;
  * the NC report has two separate fields: fails_as_required (any check FAILs) and
    margin10_met (any error/tolerance ratio >= 10), D2 Amendment 1.
H1's observations O1-O3 are not reproduced (reported-only in H1, not in its verdict).

Labels: (a) source states, (b) verified here, (c) inference.
"""
import csv
import hashlib
import io
import math
import os
import re

import numpy as np

import reference as R

RESULT_FIELDS = ["check_id", "indicator", "params", "asset", "input", "expected", "actual",
                 "abs_diff", "tolerance", "ratio", "result", "role"]


# ----------------------------------------------------------------------------- spec
def _h1_expect():
    # Copied from h1_check.py EXPECT (= H1 criteria section 4 table, (a)):
    # P: (flat error, gains at T = 5,10,20,40,100, ramp lag). The table stores 6 decimals.
    return {
        10: (0.0, [0.224200, 0.695059, 0.966116, 0.997024, 0.999785], 1.825321),
        14: (0.0, [0.116965, 0.446731, 0.894265, 0.991557, 0.999643], 2.704175),
        20: (0.0, [0.057665, 0.238406, 0.704174, 0.969143, 0.999037], 4.038666),
        30: (0.0, [0.025669, 0.108551, 0.404454, 0.870678, 0.995811], 6.277073),
    }


def h1_spec():
    """Hand-written spec reproducing H1's setup (h1_check.py constants, section 5 tolerances)."""
    ex = _h1_expect()
    variants = [dict(id="P%d" % p, params="P=%d" % p, role="real", expected=ex[p])
                for p in (10, 14, 20, 30)]
    variants.append(dict(id="NC1", params="P=21 vs P=20 expected", role="neg_control", expected=ex[20]))
    variants.append(dict(id="NC2", params="cos arg in degrees vs P=20 expected", role="neg_control",
                         expected=ex[20]))
    return dict(batch="H1_SuperSmoother2Pole", id_prefix="H1", indicator="SuperSmoother2Pole",
                asset="synthetic (EURUSD D1 bar clock)",
                n_bars=3000, w=500, level=1.1, amp=0.01, slope=0.0001, ts=(5, 10, 20, 40, 100),
                clock_lo=0.8, clock_hi=1.7,
                tol_flat=1e-9, tol_gain=1e-4, tol_lag=1e-3, tol_x=1e-12,
                variants=variants)


def input_names(spec):
    return ["flat"] + ["s%d" % t for t in spec["ts"]] + ["ramp"]


def header_of(spec):
    ins = input_names(spec)
    return (["n", "clock_close"] + ["x_" + i for i in ins]
            + ["y_%s_%s" % (v["id"], i) for v in spec["variants"] for i in ins])


# ----------------------------------------------------------------------------- inputs
def make_inputs(spec):
    """Copied from h1_check.make_inputs(), parameters from the spec."""
    n = np.arange(spec["n_bars"], dtype=float)
    x = {"flat": np.full(spec["n_bars"], spec["level"])}
    for t in spec["ts"]:
        x["s%d" % t] = spec["level"] + spec["amp"] * np.sin(2 * math.pi * n / t)
    x["ramp"] = spec["level"] + spec["slope"] * n
    return x


# ----------------------------------------------------------------------------- measurements
def m_flat(spec, y):
    """h1_check.m_flat."""
    return float(np.max(np.abs(y[spec["w"]:] - spec["level"])))


def m_gain(spec, y, t):
    """Least-squares sine gain, h1_check.m_gain."""
    w0 = spec["w"]
    n = np.arange(spec["n_bars"], dtype=float)[w0:]
    w = 2 * math.pi * n / t
    A = np.column_stack([np.sin(w), np.cos(w), np.ones_like(w)])
    coef, *_ = np.linalg.lstsq(A, y[w0:], rcond=None)
    return float(math.hypot(coef[0], coef[1]) / spec["amp"])


def m_lag(spec, x, y):
    """Ramp lag, h1_check.m_lag."""
    return float(np.mean((x[-100:] - y[-100:]) / spec["slope"]))


def measure(spec, x, yv):
    """yv: input -> output array for one variant. Returns (flat, [gains], lag)."""
    return (m_flat(spec, yv["flat"]), [m_gain(spec, yv["s%d" % t], t) for t in spec["ts"]],
            m_lag(spec, x["ramp"], yv["ramp"]))


# ----------------------------------------------------------------------------- checks
def check_rows(spec, variant, x, yv):
    """One row per check for one variant (h1_check.check_rows, floats kept unformatted)."""
    flat, gains, lag = measure(spec, x, yv)
    ef, eg, el = variant["expected"]
    rows = []

    def row(cid, inp, e, a, tol, is_flat=False):
        fin = math.isfinite(a)
        if not fin:
            res = "ERROR"
        elif is_flat:
            res = "PASS" if a <= tol else "FAIL"
        else:
            res = "PASS" if abs(a - e) <= tol else "FAIL"
        d = abs(a - e) if fin else float("nan")
        rows.append(dict(check_id="%s-%s-%s" % (spec["id_prefix"], variant["id"], cid),
                         indicator=spec["indicator"], params=variant["params"], asset=spec["asset"],
                         input=inp, expected=e, actual=a, abs_diff=d, tolerance=tol,
                         ratio=(d / tol) if fin else float("nan"), result=res, role=variant["role"]))
    row("flat", "flat", ef, flat, spec["tol_flat"], is_flat=True)
    for t, e, a in zip(spec["ts"], eg, gains):
        row("gain-T%d" % t, "sine T=%d" % t, e, a, spec["tol_gain"])
    row("ramp-lag", "ramp", el, lag, spec["tol_lag"])
    return rows


def _kind(check_id):
    tail = check_id.split("-", 2)[2]
    return "gain" if tail.startswith("gain") else ("lag" if tail.startswith("ramp") else "flat")


def nc_report(spec, rows):
    """Per negative control (D2 Amendment 1): every check's error/tolerance ratio and two
    separate fields. Returns {variant_id: dict}.

    Amendment 1 / G1: if spec has "detect_required" ({control id: [kinds]}), a kind is detected when at
    least one of the control's checks of that kind is FAIL, and fails_as_required needs EVERY listed
    kind detected (a control missing from the dict, or with an empty list, is NOT detected: strict).
    Without "detect_required" (H1) fails_as_required = any check FAILs, as before.
    `detected` (kind -> bool) is always computed; `required` is None without detect_required."""
    out = {}
    req_all = spec.get("detect_required")
    for v in spec["variants"]:
        if v["role"] != "neg_control":
            continue
        rs = [r for r in rows if r["role"] == "neg_control" and r["params"] == v["params"]
              and r["check_id"].startswith("%s-%s-" % (spec["id_prefix"], v["id"]))]
        ratios = {r["check_id"]: r["ratio"] for r in rs}
        mx = {}
        for r in rs:
            k = _kind(r["check_id"])
            mx[k] = max(mx.get(k, 0.0), r["ratio"])
        detected = {k: any(r["result"] == "FAIL" and _kind(r["check_id"]) == k for r in rs)
                    for k in ("flat", "gain", "lag")}
        if req_all is None:
            req = None
            far = any(r["result"] == "FAIL" for r in rs)
        else:
            req = list(req_all.get(v["id"], []))
            far = bool(req) and all(detected.get(k, False) for k in req)
        out[v["id"]] = dict(ratios=ratios, max_ratio=mx, fails_as_required=far,
                            margin10_met=any(r["ratio"] >= 10 for r in rs),
                            detected=detected, required=req)
    return out


# ----------------------------------------------------------------------------- raw file
class Raw:
    def __init__(self):
        self.header = []
        self.cols = {}
        self.nrows = 0
        self.issues = []     # (guard_id, message) found while parsing


def load_raw(stream):
    """Copied from h1_check.load_raw (spec independent)."""
    raw = Raw()
    rd = csv.reader(stream)
    try:
        raw.header = next(rd)
    except StopIteration:
        raw.issues.append(("G_EMPTY", "file is empty"))
        return raw
    data = {h: [] for h in raw.header}
    nonfinite = 0
    for ln, rec in enumerate(rd, start=2):
        if not rec:
            continue
        if len(rec) != len(raw.header):
            raw.issues.append(("G_RAGGED", "line %d has %d fields, header has %d"
                               % (ln, len(rec), len(raw.header))))
            continue
        for h, tok in zip(raw.header, rec):
            try:
                v = float(tok)
            except ValueError:
                v = float("nan")           # e.g. MSVC '-1.#IND00000', or a repeated header
                raw.issues.append(("G_UNPARSEABLE", "line %d col %s token %r" % (ln, h, tok)))
            if not math.isfinite(v):
                nonfinite += 1
            data[h].append(v)
    raw.nrows = len(data[raw.header[0]]) if raw.header else 0
    raw.cols = {h: np.array(v) for h, v in data.items()}
    if nonfinite:
        raw.issues.append(("G_NONFINITE", "%d NaN/inf/unparseable values" % nonfinite))
    return raw


def validate(spec, raw):
    """h1_check.validate with header, row count, clock range and inputs from the spec.
    Returns list of (guard_id, message); empty = all guards pass."""
    header, N = header_of(spec), spec["n_bars"]
    errs = list(raw.issues)
    if raw.header != header:
        missing = [h for h in header if h not in raw.header]
        extra = [h for h in raw.header if h not in header]
        errs.append(("G_HEADER", "header differs: missing %s extra %s" % (missing[:4], extra[:4])))
        return errs                      # cannot index columns reliably
    if raw.nrows != N:
        errs.append(("G_ROWCOUNT", "%d rows, expected %d" % (raw.nrows, N)))
    n = raw.cols["n"]
    if np.all(np.isfinite(n)):
        ni = n.astype(np.int64)
        if len(set(ni.tolist())) != len(ni):
            errs.append(("G_N_REPEAT", "n repeats (an x[n] was fed twice)"))
        d = np.diff(ni)
        if np.any(d > 1) or (len(ni) and ni[0] != 0):
            errs.append(("G_N_GAP", "n has a gap or does not start at 0 (an x[n] was skipped)"))
        if len(ni) == N and not np.array_equal(ni, np.arange(N)):
            errs.append(("G_N_SEQUENCE", "n is not exactly 0..%d in order" % (N - 1)))
    else:
        errs.append(("G_N_SEQUENCE", "n column has non-numeric entries"))
    lo, hi = spec["clock_lo"], spec["clock_hi"]
    cc = raw.cols["clock_close"]
    bad = ~np.isfinite(cc) | (cc < lo) | (cc > hi)
    if np.any(bad):
        k = int(np.argmax(bad))
        errs.append(("G_CLOCK", "%d rows with clock_close outside [%.1f, %.1f] "
                     "(first at row %d, value %r): wrong asset?" % (int(bad.sum()), lo, hi, k, cc[k])))
    if raw.nrows == N:
        x = make_inputs(spec)
        for i in input_names(spec):
            d = np.abs(raw.cols["x_" + i] - x[i])
            if not np.all(d <= spec["tol_x"]):          # NaN compares False -> also caught
                errs.append(("G_INPUT_MISMATCH", "x_%s differs from x[n]: max |diff| %.3g > %g"
                             % (i, float(np.nanmax(d)) if np.any(np.isfinite(d)) else float("nan"),
                                spec["tol_x"])))
    return errs


# ----------------------------------------------------------------------------- IMP + floor guard (SS3)
def imp_rows(spec, raw, x=None):
    """[imp] (SS3 spec decision 4, pass item 6). For every variant in must_pass / must_fail: replay the
    recursion with the named model (reference.IMP_MODELS, explicit registry, no eval) on the x columns
    EXPORTED in the raw file; residual = max |y_Zorro - y_replay| over n >= warmup, per input and overall.
    One row per listed variant and list (role "imp"). must_pass: residual <= tol; must_fail: residual > tol.
    An unknown model string or a non-finite residual is an ERROR row. Per-input residuals are kept in
    row["detail"] (not written to the CSV columns)."""
    imp, w, p = spec["imp"], spec["w"], spec["id_prefix"]
    tol = imp["tol"]
    rows = []
    for kind, table in (("pass", imp["must_pass"]), ("fail", imp["must_fail"])):
        for vid, mstr in table.items():
            per, res = {}, None
            maker = R.IMP_MODELS.get(mstr)
            if maker is None:
                res = "ERROR"
            else:
                model = maker()
                for i in input_names(spec):
                    xi = raw.cols["x_" + i]
                    yi = raw.cols["y_%s_%s" % (vid, i)]
                    per[i] = float(np.max(np.abs(yi[w:] - R.simulate(model, xi)[w:])))
                overall = max(per.values())
                if not math.isfinite(overall):
                    res = "ERROR"
            if res == "ERROR":
                overall = float("nan")
            elif kind == "pass":
                res = "PASS" if overall <= tol else "FAIL"
            else:
                res = "PASS" if overall > tol else "FAIL"
            fin = math.isfinite(overall)
            rows.append(dict(check_id="%s-%s-imp-%s" % (p, vid, kind), indicator=spec["indicator"],
                             params="IMP must_%s: %s" % (kind, mstr),
                             asset=spec["asset"], input="replay residual n>=%d, overall" % w,
                             expected=0.0 if kind == "pass" else tol, actual=overall,
                             abs_diff=overall, tolerance=tol, ratio=(overall / tol) if fin else float("nan"),
                             result=res, role="imp", detail=per))
    return rows


def floor_rows(spec, rows):
    """Pass item 7: per REAL variant max gain |Zorro - book| <= tol_gain/10 and lag <= tol_lag/10
    (D2 rule 3 floor side). A failing row means the tolerance window is invalid (see the trailer)."""
    out = []
    for v in spec["variants"]:
        if v["role"] != "real":
            continue
        pre = "%s-%s-" % (spec["id_prefix"], v["id"])
        rs = [r for r in rows if r["role"] == "real" and r["check_id"].startswith(pre)]
        for q, tol in (("gain", spec["tol_gain"] / 10), ("lag", spec["tol_lag"] / 10)):
            ds = [r["abs_diff"] for r in rs if _kind(r["check_id"]) == q]
            a = max(ds) if ds else float("nan")
            fin = math.isfinite(a)
            out.append(dict(check_id="%sfloor-%s" % (pre, q), indicator=spec["indicator"],
                            params=v["params"], asset=spec["asset"], input="max |Zorro - book| " + q,
                            expected=0.0, actual=a, abs_diff=a, tolerance=tol,
                            ratio=(a / tol) if fin else float("nan"),
                            result=("ERROR" if not fin else ("PASS" if a <= tol else "FAIL")), role="floor"))
    return out


def evaluate(spec, raw):
    """Assumes validate() found nothing. Returns (rows, nc_report)."""
    x = make_inputs(spec)
    rows = []
    for v in spec["variants"]:
        yv = {i: raw.cols["y_%s_%s" % (v["id"], i)] for i in input_names(spec)}
        rows += check_rows(spec, v, x, yv)
    nc = nc_report(spec, rows)
    if spec.get("imp"):
        rows += imp_rows(spec, raw, x) + floor_rows(spec, rows)
    return rows, nc


# ----------------------------------------------------------------------------- verdict, writer
def counts(spec, rows, errs):
    real = [r for r in rows if r["role"] == "real"]
    n_err = len(errs) + sum(r["result"] == "ERROR" for r in rows)
    return dict(n_real=len(real), n_pass=sum(r["result"] == "PASS" for r in real),
                n_fail=sum(r["result"] == "FAIL" for r in real), n_err=n_err)


def verdict(spec, rows, nc, errs):
    c = counts(spec, rows, errs)
    n_real_variants = sum(v["role"] == "real" for v in spec["variants"])
    expect_real = n_real_variants * (2 + len(spec["ts"]))
    ok = (c["n_real"] == expect_real and c["n_pass"] == expect_real and c["n_err"] == 0
          and all(d["fails_as_required"] for d in nc.values()) and len(nc) > 0
          and all(r["result"] == "PASS" for r in rows if r["role"] in ("imp", "floor")))
    return ok, c


def next_results_path(out_dir, batch, date_str):
    """<batch>_<date>[_run<k>].csv, as h1_check.next_results_path: the un-suffixed file is
    run 1; the result is the next free run number."""
    base = "%s_%s" % (batch, date_str)
    used = 0
    if os.path.isdir(out_dir):
        for name in os.listdir(out_dir):
            if name == base + ".csv":
                used = max(used, 1)
            m = re.fullmatch(re.escape(base) + r"_run(\d+)\.csv", name)
            if m:
                used = max(used, int(m.group(1)))
    k = used + 1
    return os.path.join(out_dir, base + ".csv" if k == 1 else "%s_run%d.csv" % (base, k)), k


def _fmt(v):
    return repr(float(v))


def imp_trailer(spec, rows):
    """Trailer lines for specs with [imp]: IMP per-input residuals, O_PEAK, O_IMP_RESIDUAL, and the floor
    guard message. Empty list without [imp] (H1 / SS2 output unchanged)."""
    if not spec.get("imp") or not rows:
        return []
    p = spec["id_prefix"]
    out = []
    for r in rows:
        if r["role"] == "imp":
            out.append("# IMP %s residual overall=%.3e tol=%g %s per_input: %s" % (
                r["check_id"], r["actual"], r["tolerance"], r["result"],
                " ".join("%s=%.3e" % kv for kv in r.get("detail", {}).items())))
    for v in spec["variants"]:
        if v["role"] != "real":
            continue
        pre = "%s-%s-" % (p, v["id"])
        gains = [r["actual"] for r in rows if r["role"] == "real" and r["check_id"].startswith(pre)
                 and _kind(r["check_id"]) == "gain"]
        out.append("# O_PEAK %s max_measured_gain=%r (INFO)" % (v["id"], max(gains)))
    for v in spec["variants"]:
        if v["role"] != "real":
            continue
        pre = "%s-%s-" % (p, v["id"])
        imp = [r["actual"] for r in rows if r["role"] == "imp" and r["check_id"] == pre + "imp-pass"]
        fl = {q: [r["actual"] for r in rows if r["check_id"] == pre + "floor-" + q][0] for q in ("gain", "lag")}
        out.append("# O_IMP_RESIDUAL %s imp=%s zorro_vs_book_gain_max=%.3e zorro_vs_book_lag=%.3e (INFO)" % (
            v["id"], "%.3e" % imp[0] if imp else "n/a", fl["gain"], fl["lag"]))
    bad = sorted(r["check_id"] for r in rows if r["role"] == "floor" and r["result"] != "PASS")
    if bad:
        out.append("# FLOOR_GUARD FAIL: tolerance window invalid (item 7; not accepted until explained): "
                   + ",".join(bad))
    return out


def write_results(path, spec, rows, nc, errs, raw_path, raw_sha, ox_lines=None):
    """Exclusive create (mode 'x'): refuses with FileExistsError to overwrite.

    spec["extended_report"] (set by generator.to_checker_spec when the spec has [detect], [ox] or
    [literal_info], Amendment 1 A1.4) switches on the extended trailer: variant-count split, literal_info,
    D2 lines, OX block. Without it the output is exactly the pre-amendment format (H1)."""
    ok, c = verdict(spec, rows, nc, errs)
    p = spec["id_prefix"]
    with open(path, "x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RESULT_FIELDS, lineterminator="\n")
        w.writeheader()
        for g, m in errs:
            w.writerow(dict(check_id="%s-GUARD-%s" % (p, g), indicator="harness", params="",
                            asset="", input="raw csv", expected="guard clean", actual=m,
                            tolerance="", result="ERROR", role="guard"))
        for r in rows:
            full = dict(r, expected=_fmt(r["expected"]), actual=_fmt(r["actual"]),
                        abs_diff="%.3e" % r["abs_diff"], tolerance="%g" % r["tolerance"],
                        ratio="%.3e" % r["ratio"])
            w.writerow({k: v for k, v in full.items() if k in RESULT_FIELDS})
        for vid, d in nc.items():
            if d["required"] is None:
                w.writerow(dict(check_id="%s-%s-verdict" % (p, vid), indicator=spec["indicator"],
                                params="control must FAIL at least one check", asset="", input="all",
                                expected="FAILS_AS_REQUIRED",
                                actual="FAILS_AS_REQUIRED" if d["fails_as_required"] else "DID_NOT_FAIL",
                                result="PASS" if d["fails_as_required"] else "FAIL", role="neg_control"))
            else:
                miss = [k for k in d["required"] if not d["detected"].get(k, False)]
                w.writerow(dict(check_id="%s-%s-verdict" % (p, vid), indicator=spec["indicator"],
                                params="control must FAIL at least one check of EVERY required kind",
                                asset="", input="all",
                                expected="DETECTED:" + ",".join(d["required"]),
                                actual="DETECTED" if d["fails_as_required"] else
                                "NOT_DETECTED:" + (",".join(miss) if miss else "no required kind listed"),
                                result="PASS" if d["fails_as_required"] else "FAIL", role="neg_control"))
        ext = bool(spec.get("extended_report"))
        nreal = sum(v["role"] == "real" for v in spec["variants"])
        nneg = sum(v["role"] == "neg_control" for v in spec["variants"])
        if not ext:
            f.write("# batch=%s variants_run=%d\n" % (spec["batch"], len(spec["variants"]) if not errs
                                                       else 0))
        elif not errs:
            f.write("# batch=%s variants_run=%d real=%d neg_control=%d\n"
                    % (spec["batch"], len(spec["variants"]), nreal, nneg))
        else:
            gids = sorted(set(g for g, _ in errs))
            f.write("# batch=%s variants NOT evaluated (guard fired: %s) variants_defined=%d real=%d "
                    "neg_control=%d\n" % (spec["batch"], ",".join(gids), len(spec["variants"]), nreal, nneg))
        f.write("# real_checks=%d PASS=%d FAIL=%d ERROR=%d\n"
                % (c["n_real"], c["n_pass"], c["n_fail"], c["n_err"]))
        for vid, d in nc.items():
            f.write("# NC %s fails_as_required=%s margin10_met=%s max_ratio gain=%.3e lag=%.3e flat=%.3e"
                    % (vid, d["fails_as_required"], d["margin10_met"], d["max_ratio"].get("gain", 0.0),
                       d["max_ratio"].get("lag", 0.0), d["max_ratio"].get("flat", 0.0)))
            if d["required"] is not None:
                f.write(" detected gain=%s lag=%s flat=%s required=%s"
                        % (d["detected"]["gain"], d["detected"]["lag"], d["detected"]["flat"],
                           ",".join(d["required"])))
            f.write("\n")
        if ext:
            li = spec.get("literal_info")
            if li:
                f.write("# literal_info (article literals vs exact constants; INFO, never PASS/FAIL, "
                        "D1 rule 3) gain_max=%s lag_max=%s source=%s\n"
                        % (li.get("gain_max"), li.get("lag_max"), li.get("source", "")))
            for line in spec.get("info_lines", []):
                f.write("# %s\n" % line)
            for line in imp_trailer(spec, rows):
                f.write(line + "\n")
            for line in (ox_lines or []):
                f.write(line + "\n")
        f.write("# raw_file=%s sha256=%s\n" % (raw_path, raw_sha))
        f.write("# VERDICT: %s\n" % ("PASS" if ok else "FAIL"))
    return ok, c


# ----------------------------------------------------------------------------- OX (Amendment 1, G2)
def ox_columns(spec):
    """Columns compared by OX, derived (A2): n, clock_close, every x_<input>, and y_<id>_<input> for
    each role == 'real' variant."""
    ins = input_names(spec)
    return (["n", "clock_close"] + ["x_" + i for i in ins]
            + ["y_%s_%s" % (v["id"], i) for v in spec["variants"] if v["role"] == "real" for i in ins])


def _read_tokens(blob):
    """-> (header, {col: [token strings]}). Tokens stay strings (no float conversion). A short row
    gets '<missing>' for absent fields."""
    rd = csv.reader(io.StringIO(blob.decode("utf-8", errors="replace")))
    header = next(rd)
    cols = {h: [] for h in header}
    for rec in rd:
        if not rec:
            continue
        for k, h in enumerate(header):
            cols[h].append(rec[k] if k < len(rec) else "<missing>")
    return header, cols


def ox_compare(spec, raw_blob, reference_path=None):
    """OX: compare the raw output (bytes) with the registered reference raw file by string-token
    equality on ox_columns(spec). INFO only: returns '# OX ...' lines, never raises, never touches
    the verdict. The reference sha256 is checked first; a missing / different reference or a
    missing column gives '# OX not available: <reason>'.

    max_abs_diff per column is "beyond Amendment 1, reporting only" (A7): the largest |a - b| over the
    tokens that differ as strings and parse as numbers."""
    try:
        ox = spec["ox"]
        ref = reference_path or ox["reference_raw"]
        if not os.path.isfile(ref):
            return ["# OX not available: reference file not found: %s" % ref]
        with open(ref, "rb") as fh:
            rblob = fh.read()
        rsha = hashlib.sha256(rblob).hexdigest()
        if rsha != ox["reference_sha256"]:
            return ["# OX not available: reference sha256 %s differs from registered %s (%s)"
                    % (rsha, ox["reference_sha256"], ref)]
        gh, gc = _read_tokens(raw_blob)
        rh, rc = _read_tokens(rblob)
        cols = ox_columns(spec)
        for c in cols:
            if c not in gc:
                return ["# OX not available: column %s missing in the raw file under test" % c]
            if c not in rc:
                return ["# OX not available: column %s missing in the reference file" % c]
        ng, nr = len(gc[cols[0]]), len(rc[cols[0]])
        m = min(ng, nr)
        out = ["# OX raw vs reference %s (sha256 %s verified): rows under test=%d reference=%d compared=%d"
               % (ref, rsha, ng, nr, m)]
        if ng != nr:
            out.append("# OX row count differs: under test %d, reference %d (compared the first %d)"
                       % (ng, nr, m))
        n_col_diff, n_tok_diff = 0, 0
        for c in cols:
            a, b = gc[c][:m], rc[c][:m]
            idx = [i for i in range(m) if a[i] != b[i]]
            mx = 0.0
            for i in idx:
                try:
                    mx = max(mx, abs(float(a[i]) - float(b[i])))
                except ValueError:
                    mx = float("nan")
                    break
            n_tok_diff += len(idx)
            n_col_diff += bool(idx)
            if idx:
                out.append("# OX col=%s differing_tokens=%d first_diff_row=%d under_test=%s reference=%s "
                           "max_abs_diff=%.3e" % (c, len(idx), idx[0], a[idx[0]], b[idx[0]], mx))
            else:
                out.append("# OX col=%s differing_tokens=0 first_diff_row=none max_abs_diff=0.000e+00" % c)
        out.append("# OX summary: columns=%d columns_differing=%d differing_tokens=%d (INFO only: does not "
                   "change PASS/FAIL; a mismatch must be explained before the result is accepted)"
                   % (len(cols), n_col_diff, n_tok_diff))
        out.append("# OX note: max_abs_diff is beyond Amendment 1, reporting only")
        return out
    except Exception as e:                       # OX must never break the run (INFO only)
        return ["# OX not available: %s: %s" % (type(e).__name__, e)]


def run_check(spec, raw_path, out_dir, date_str, ox_reference=None):
    """Read the raw file in place, guard, measure, write the results file. A firing guard
    writes ERROR rows; checks are computed only when no guard fired (as H1).
    If spec has "ox" the OX block is computed (also when a guard fired, A4) and written; ox_reference
    overrides the registered reference path (tests)."""
    with open(raw_path, "rb") as fh:
        blob = fh.read()
    sha = hashlib.sha256(blob).hexdigest()
    raw = load_raw(io.StringIO(blob.decode("utf-8", errors="replace")))
    errs = validate(spec, raw)
    rows, nc = ([], {}) if errs else evaluate(spec, raw)
    ox_lines = ox_compare(spec, blob, ox_reference) if spec.get("ox") else None
    os.makedirs(out_dir, exist_ok=True)
    path, k = next_results_path(out_dir, spec["batch"], date_str)
    ok, c = write_results(path, spec, rows, nc, errs, raw_path, sha, ox_lines)
    return dict(path=path, run=k, ok=ok, counts=c, errs=errs, rows=rows, nc=nc, sha256=sha,
                ox=ox_lines)


# ----------------------------------------------------------------------------- CLI (A6)
def main(argv=None):
    """python analysis/harness/checker.py <spec.toml> <raw.csv> [--out-dir DIR] [--date YYYYMMDD]
    Exit code: 0 verdict PASS, 1 verdict FAIL, 2 refused (spec refused by generator.validate_spec,
    or raw file missing). The results file is created exclusively (never overwritten)."""
    import argparse
    import datetime
    import sys
    import generator as G
    ap = argparse.ArgumentParser(description="Check a Zorro raw CSV against a harness spec.")
    ap.add_argument("spec")
    ap.add_argument("raw")
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    ap.add_argument("--date", default=datetime.date.today().strftime("%Y%m%d"))
    a = ap.parse_args(argv)
    if not os.path.isfile(a.raw):
        print("REFUSED: raw file not found: %s" % a.raw)
        return 2
    try:
        tspec = G.load_spec(a.spec)
    except Exception as e:
        print("REFUSED: cannot read spec %s: %s: %s" % (a.spec, type(e).__name__, e))
        return 2
    errs, infos = G.validate_spec(tspec)
    if errs:
        for code, msg in errs:
            print("SPEC REFUSED %s: %s" % (code, msg))
        return 2
    for line in infos:
        print(line)
    res = run_check(G.to_checker_spec(tspec), a.raw, a.out_dir, a.date)
    print("VERDICT: %s  (real checks PASS=%d FAIL=%d ERROR=%d)" % (
        "PASS" if res["ok"] else "FAIL", res["counts"]["n_pass"], res["counts"]["n_fail"],
        res["counts"]["n_err"]))
    print("results: %s" % res["path"])
    sys.stdout.flush()
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
