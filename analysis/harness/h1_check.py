"""H1 checker for indicators/ehlers/SuperSmoother2Pole.c.

Implements docs/preregistration/H1_SuperSmoother2Pole_Criteria.md (incl. Amendment 1).
Zorro runs the filters (strategies/tests/H1_SuperSmoother2Pole_Harness.c) and writes raw
outputs; this script measures and writes PASS/FAIL.

Step 1  self-test (no Zorro file is read): simulate the recursion, confirm the S3 methods
        reproduce the S4 table within S5 tolerances, NC1/NC2 fail, and every input guard
        fires on a deliberately broken input. Any failure -> stop, exit 2.
Step 2  read the raw CSV, run guards, compute the 28 real checks + negative controls +
        observations O1-O3, write the results CSV, print the H1 verdict.

Usage:  python analysis/harness/h1_check.py [--selftest-only] [--raw PATH] [--out-dir DIR]
Expected-value labels: (a) criteria file S4/S5 (pre-registered); (b) simulated here.
"""
import argparse
import csv
import datetime
import hashlib
import io
import math
import os
import sys

import numpy as np

# ----------------------------------------------------------------- pre-registered numbers
N_BARS = 3000
W = 500
FLAT_LEVEL = 1.1
AMP = 0.01
RAMP_SLOPE = 0.0001
TS = (5, 10, 20, 40, 100)
INPUTS = ["flat"] + ["s%d" % t for t in TS] + ["ramp"]
VARIANTS = ["P10", "P14", "P20", "P30", "NC1", "NC2"]
REAL = {"P10": 10, "P14": 14, "P20": 20, "P30": 30}
TOL_FLAT, TOL_GAIN, TOL_LAG = 1e-9, 1e-4, 1e-3
TOL_X = 1e-12          # exported input vs recomputed x[n]
CLOCK_LO, CLOCK_HI = 0.8, 1.7
# criteria S4 table: flat error, gains T=5,10,20,40,100, ramp lag
EXPECT = {
    10: (0.0, [0.224200, 0.695059, 0.966116, 0.997024, 0.999785], 1.825321),
    14: (0.0, [0.116965, 0.446731, 0.894265, 0.991557, 0.999643], 2.704175),
    20: (0.0, [0.057665, 0.238406, 0.704174, 0.969143, 0.999037], 4.038666),
    30: (0.0, [0.025669, 0.108551, 0.404454, 0.870678, 0.995811], 6.277073),
}
NC_VS_P = 20  # S6: both controls are compared with the P=20 expected values

HEADER = (["n", "clock_close"] + ["x_" + i for i in INPUTS]
          + ["y_%s_%s" % (v, i) for v in VARIANTS for i in INPUTS])


# ----------------------------------------------------------------- inputs and filter
def make_inputs():
    n = np.arange(N_BARS, dtype=float)
    x = {"flat": np.full(N_BARS, FLAT_LEVEL)}
    for t in TS:
        x["s%d" % t] = FLAT_LEVEL + AMP * np.sin(2 * math.pi * n / t)
    x["ramp"] = FLAT_LEVEL + RAMP_SLOPE * n
    return x


def coeffs(p, degrees=False):
    c1 = math.exp(-math.sqrt(2.0) * math.pi / p)
    arg = math.sqrt(2.0) * (180.0 if degrees else math.pi) / p
    b1 = 2.0 * c1 * math.cos(arg)
    return (1.0 - b1 + c1 * c1) / 2.0, b1, -c1 * c1


def simulate(x, p, degrees=False):
    """Recursion of SuperSmoother2Pole.c. Seeds = x[0] (Zorro's seed is unknown; the
    transient is gone by n = 500, so it does not affect any registered check)."""
    c0, c2, c3 = coeffs(p, degrees)
    y = np.empty(len(x))
    y1 = y2 = x[0]
    xm = x[0]
    for i in range(len(x)):
        yi = c0 * (x[i] + xm) + c2 * y1 + c3 * y2
        y[i] = yi
        y2, y1, xm = y1, yi, x[i]
    return y


def make_outputs(x):
    y = {}
    for v in VARIANTS:
        for i in INPUTS:
            if v == "NC1":
                y[(v, i)] = simulate(x[i], 21)
            elif v == "NC2":
                y[(v, i)] = simulate(x[i], 20, degrees=True)
            else:
                y[(v, i)] = simulate(x[i], REAL[v])
    return y


# ----------------------------------------------------------------- measurements (S3)
def m_flat(y):
    return float(np.max(np.abs(y[W:] - FLAT_LEVEL)))


def m_gain(y, t):
    n = np.arange(N_BARS, dtype=float)[W:]
    w = 2 * math.pi * n / t
    A = np.column_stack([np.sin(w), np.cos(w), np.ones_like(w)])
    coef, *_ = np.linalg.lstsq(A, y[W:], rcond=None)
    return float(math.hypot(coef[0], coef[1]) / AMP)


def m_lag(x, y):
    return float(np.mean((x[-100:] - y[-100:]) / RAMP_SLOPE))


def measure(x, yv):
    """yv: dict input -> output array for one variant. Returns (flat, [gains], lag)."""
    return (m_flat(yv["flat"]), [m_gain(yv["s%d" % t], t) for t in TS],
            m_lag(x["ramp"], yv["ramp"]))


def check_rows(variant, label, x, yv, exp_p, role):
    """28/7 check rows for one variant against EXPECT[exp_p]."""
    flat, gains, lag = measure(x, yv)
    ef, eg, el = EXPECT[exp_p]
    rows = []

    def row(cid, inp, e, a, tol):
        res = "PASS" if (math.isfinite(a) and abs(a - e) <= tol) else "FAIL"
        if cid.endswith("flat"):
            res = "PASS" if (math.isfinite(a) and a <= tol) else "FAIL"
        rows.append(dict(check_id="H1-%s-%s" % (variant, cid), indicator="SuperSmoother2Pole",
                         params=label, asset="synthetic (EURUSD D1 bar clock)", input=inp,
                         expected="%.6f" % e, actual="%.6f" % a, tolerance="%g" % tol,
                         result=res, role=role))
    row("flat", "flat", ef, flat, TOL_FLAT)
    for t, e, a in zip(TS, eg, gains):
        row("gain-T%d" % t, "sine T=%d" % t, e, a, TOL_GAIN)
    row("ramp-lag", "ramp", el, lag, TOL_LAG)
    return rows


def nc_fails_as_required(rows):
    return any(r["result"] == "FAIL" for r in rows
               if r["check_id"].split("-", 2)[2].startswith(("gain", "ramp")))


# ----------------------------------------------------------------- raw file: load + guards
class Raw:
    def __init__(self):
        self.header = []
        self.cols = {}
        self.nrows = 0
        self.issues = []     # (guard_id, message) found while parsing


def load_raw(stream):
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


def validate(raw):
    """Return list of (guard_id, message). Empty list = all guards pass."""
    errs = list(raw.issues)
    if raw.header != HEADER:
        missing = [h for h in HEADER if h not in raw.header]
        extra = [h for h in raw.header if h not in HEADER]
        errs.append(("G_HEADER", "header differs: missing %s extra %s" % (missing[:4], extra[:4])))
        return errs                      # cannot index columns reliably
    if raw.nrows != N_BARS:
        errs.append(("G_ROWCOUNT", "%d rows, expected %d" % (raw.nrows, N_BARS)))
    n = raw.cols["n"]
    if np.all(np.isfinite(n)):
        ni = n.astype(np.int64)
        if len(set(ni.tolist())) != len(ni):
            errs.append(("G_N_REPEAT", "n repeats (an x[n] was fed twice)"))
        d = np.diff(ni)
        if np.any(d > 1) or (len(ni) and ni[0] != 0):
            errs.append(("G_N_GAP", "n has a gap or does not start at 0 (an x[n] was skipped)"))
        if len(ni) == N_BARS and not np.array_equal(ni, np.arange(N_BARS)):
            errs.append(("G_N_SEQUENCE", "n is not exactly 0..%d in order" % (N_BARS - 1)))
    else:
        errs.append(("G_N_SEQUENCE", "n column has non-numeric entries"))
    cc = raw.cols["clock_close"]
    bad = ~np.isfinite(cc) | (cc < CLOCK_LO) | (cc > CLOCK_HI)
    if np.any(bad):
        errs.append(("G_CLOCK", "%d rows with clock_close outside [%.1f, %.1f] "
                     "(first at row %d, value %r): wrong asset?"
                     % (int(bad.sum()), CLOCK_LO, CLOCK_HI, int(np.argmax(bad)), cc[np.argmax(bad)])))
    if raw.nrows == N_BARS:
        x = make_inputs()
        for i in INPUTS:
            d = np.abs(raw.cols["x_" + i] - x[i])
            if not np.all(d <= TOL_X):          # NaN compares False -> also caught
                errs.append(("G_INPUT_MISMATCH", "x_%s differs from x[n]: max |diff| %.3g > %g"
                             % (i, float(np.nanmax(d)) if np.any(np.isfinite(d)) else float("nan"), TOL_X)))
    return errs


# ----------------------------------------------------------------- full evaluation
def evaluate(raw):
    """Assumes validate() found nothing. Returns (rows, nc_verdicts, observations)."""
    x = make_inputs()
    yv = {v: {i: raw.cols["y_%s_%s" % (v, i)] for i in INPUTS} for v in VARIANTS}
    rows = []
    for v, p in REAL.items():
        rows += check_rows(v, "P=%d" % p, x, yv[v], p, "real")
    nc = {}
    for v, lab in (("NC1", "P=21 vs P=20 expected"), ("NC2", "cos arg in degrees vs P=20 expected")):
        r = check_rows(v, lab, x, yv[v], NC_VS_P, "neg_control")
        rows += r
        nc[v] = nc_fails_as_required(r)
    obs = []
    for v in VARIANTS:
        e = np.abs(yv[v]["flat"] - FLAT_LEVEL)
        bad = np.nonzero(e > 1e-9)[0]
        obs.append(dict(variant=v, O1_max_flat_err_n0_499="%.6g" % float(e[:W].max()),
                        O2_first_n_err_le_1e9=int(bad[-1] + 1) if len(bad) else 0))
    o3 = []
    for v in VARIANTS:
        for i in ("flat", "ramp"):
            for k in range(10):
                o3.append((v, i, k, float(x[i][k]), float(yv[v][i][k])))
    return rows, nc, obs, o3


RESULT_FIELDS = ["check_id", "indicator", "params", "asset", "input", "expected", "actual",
                 "tolerance", "result", "role"]


def verdict(rows, nc, errs, nvariants):
    real = [r for r in rows if r["role"] == "real"]
    n_pass = sum(r["result"] == "PASS" for r in real)
    n_fail = sum(r["result"] == "FAIL" for r in real)
    n_err = len(errs) + sum(r["result"] == "ERROR" for r in rows)
    ok = (len(real) == 28 and n_pass == 28 and nc.get("NC1") and nc.get("NC2")
          and n_err == 0 and nvariants == 6)
    return ok, n_pass, n_fail, n_err


def write_results(path, rows, nc, errs, obs, o3, raw_path, raw_sha):
    ok, n_pass, n_fail, n_err = verdict(rows, nc, errs, len(VARIANTS) if not errs else 0)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RESULT_FIELDS, lineterminator="\n")
        w.writeheader()
        for e in errs:
            w.writerow(dict(check_id="H1-GUARD-" + e[0], indicator="harness", params="",
                            asset="", input="raw csv", expected="guard clean", actual=e[1],
                            tolerance="", result="ERROR", role="guard"))
        for r in rows:
            w.writerow(r)
        for v in ("NC1", "NC2"):
            if v in nc:
                w.writerow(dict(check_id="H1-%s-verdict" % v, indicator="SuperSmoother2Pole",
                                params="control must FAIL a gain or ramp check", asset="",
                                input="all", expected="FAILS_AS_REQUIRED",
                                actual="FAILS_AS_REQUIRED" if nc[v] else "DID_NOT_FAIL",
                                tolerance="", result="PASS" if nc[v] else "FAIL", role="neg_control"))
        out = csv.writer(f, lineterminator="\n")
        out.writerow(["# batch=H1_SuperSmoother2Pole", "variants_run=%d" % len(VARIANTS)
                      if not errs else "variants_run=unverified"])
        out.writerow(["# real_checks=28 PASS=%d FAIL=%d ERROR=%d" % (n_pass, n_fail, n_err)])
        out.writerow(["# neg_controls NC1_fails_as_required=%s NC2_fails_as_required=%s"
                      % (nc.get("NC1"), nc.get("NC2"))])
        out.writerow(["# raw_file=%s sha256=%s" % (raw_path, raw_sha)])
        out.writerow(["# H1 VERDICT: %s" % ("PASS" if ok else "FAIL")])
        if obs:
            out.writerow(["# OBSERVATIONS O1-O3 (Amendment 1, A1.2) - reported only, not in verdict"])
            out.writerow(["# O1/O2 per variant: variant, O1_max_flat_err_n0_499, O2_first_n_err_le_1e9"])
            for o in obs:
                out.writerow(["# O12", o["variant"], o["O1_max_flat_err_n0_499"],
                              o["O2_first_n_err_le_1e9"]])
            out.writerow(["# O3 raw rows n=0..9: variant, input, n, x, y"])
            for v, i, k, xv, yv in o3:
                out.writerow(["# O3", v, i, k, "%.15f" % xv, "%.15f" % yv])
    return ok, n_pass, n_fail, n_err


# ----------------------------------------------------------------- step 1: self-test
def fake_zorro_csv(y_override=None, mutate=None):
    """Text of a raw CSV as the harness would write it, produced from the simulation."""
    x = make_inputs()
    y = make_outputs(x)
    if y_override:
        y.update(y_override)
    clock = np.full(N_BARS, 1.1)
    lines = [",".join(HEADER)]
    for k in range(N_BARS):
        vals = ["%d" % k, "%.15f" % clock[k]] + ["%.15f" % x[i][k] for i in INPUTS]
        vals += ["%.15f" % y[(v, i)][k] for v in VARIANTS for i in INPUTS]
        lines.append(",".join(vals))
    if mutate:
        lines = mutate(lines)
    return "\n".join(lines) + "\n"


def selftest():
    failures = []

    def report(name, ok, detail=""):
        print("  [%s] %s %s" % ("ok  " if ok else "FAIL", name, detail))
        if not ok:
            failures.append(name)

    print("STEP 1a: simulated recursion vs pre-registered S4 table (tolerances S5)")
    x = make_inputs()
    for p in REAL.values():
        yv = {i: simulate(x[i], p) for i in INPUTS}
        flat, gains, lag = measure(x, yv)
        ef, eg, el = EXPECT[p]
        worst_g = max(abs(a - e) for a, e in zip(gains, eg))
        report("P=%d flat<=1e-9, gains<=1e-4, lag<=1e-3" % p,
               flat <= TOL_FLAT and worst_g <= TOL_GAIN and abs(lag - el) <= TOL_LAG,
               "(flat %.2e, worst gain diff %.2e, lag diff %.2e)" % (flat, worst_g, abs(lag - el)))

    print("STEP 1b: negative controls must FAIL a gain or ramp check vs P=20 values")
    sim = make_outputs(x)
    for v in ("NC1", "NC2"):
        yv = {i: sim[(v, i)] for i in INPUTS}
        rows = check_rows(v, v, x, yv, NC_VS_P, "neg_control")
        flat_ok = [r for r in rows if r["check_id"].endswith("flat")][0]["result"] == "PASS"
        g20 = [r for r in rows if r["check_id"].endswith("gain-T20")][0]["actual"]
        lag = [r for r in rows if r["check_id"].endswith("ramp-lag")][0]["actual"]
        report("%s fails as required" % v, nc_fails_as_required(rows),
               "(gain T=20 %s, ramp lag %s, flat check %s; S6 quotes %s)"
               % (g20, lag, "PASS" if flat_ok else "FAIL",
                  "0.669/4.262" if v == "NC1" else "0.531/5.426"))

    print("STEP 1c: loader + guards on a simulated 'Zorro' CSV, then each guard on broken input")
    good = fake_zorro_csv()
    raw = load_raw(io.StringIO(good))
    errs = validate(raw)
    report("clean simulated file passes all guards", not errs, str(errs))
    rows, nc, obs, o3 = evaluate(raw)
    ok, n_pass, n_fail, n_err = verdict(rows, nc, errs, len(VARIANTS))
    report("clean file -> 28 real PASS, NC1+NC2 fail as required, H1 PASS",
           ok and n_pass == 28, "(PASS=%d FAIL=%d ERR=%d)" % (n_pass, n_fail, n_err))

    def row_cell(lines, r, col, new):
        f = lines[r].split(",")
        f[HEADER.index(col)] = new
        lines[r] = ",".join(f)
        return lines

    def drop_col(lines):
        k = HEADER.index("y_P20_s20")
        return [",".join(c for j, c in enumerate(l.split(",")) if j != k) for l in lines]

    def dup_n(lines):
        lines[101] = lines[100]
        return lines

    def trunc6(lines):
        out = [lines[0]]
        for l in lines[1:]:
            out.append(",".join(l.split(",")[:1] + ["%.6f" % float(c) for c in l.split(",")[1:]]))
        return out

    broken = [
        ("G_NONFINITE/G_UNPARSEABLE: MSVC NaN token", lambda L: row_cell(L, 700, "y_P20_s10", "-1.#IND00000000000"), "G_UNPARSEABLE"),
        ("G_NONFINITE: 'inf' value", lambda L: row_cell(L, 700, "y_P14_ramp", "inf"), "G_NONFINITE"),
        ("G_N_GAP: row deleted (an x[n] skipped)", lambda L: L[:50] + L[51:], "G_N_GAP"),
        ("G_N_REPEAT: row n repeated (x[n] fed twice)", dup_n, "G_N_REPEAT"),
        ("G_ROWCOUNT: file ends at 2999 rows", lambda L: L[:-1], "G_ROWCOUNT"),
        ("G_HEADER: a column missing", drop_col, "G_HEADER"),
        ("G_UNPARSEABLE: header repeated mid-file", lambda L: L[:900] + [L[0]] + L[900:], "G_UNPARSEABLE"),
        ("G_INPUT_MISMATCH: x_s20 corrupted by 1e-6", lambda L: row_cell(L, 400, "x_s20", "%.15f" % (float(L[400].split(",")[HEADER.index("x_s20")]) + 1e-6)), "G_INPUT_MISMATCH"),
        ("G_INPUT_MISMATCH: values written with %f (6 decimals)", trunc6, "G_INPUT_MISMATCH"),
        ("G_CLOCK: clock_close = 0 (no data / wrong asset)", lambda L: row_cell(L, 10, "clock_close", "0.000000000000000"), "G_CLOCK"),
        ("G_CLOCK: clock_close = 1900 (BTC-like magnitude)", lambda L: row_cell(L, 10, "clock_close", "1900.0"), "G_CLOCK"),
    ]
    for name, mut, want in broken:
        rw = load_raw(io.StringIO(fake_zorro_csv(mutate=mut)))
        e = validate(rw)
        ids = [g for g, _ in e]
        fired = want in ids
        report("guard fires: " + name, fired,
               ("-> " + [m for g, m in e if g == want][0][:90]) if fired else "-> DID NOT FIRE: %s" % ids)

    print("STEP 1d: the checks themselves fire on broken filter output")
    # (i) a wrong filter in the P=20 slot (period 21) must FAIL real checks
    wrong = {("P20", i): simulate(x[i], 21) for i in INPUTS}
    rw = load_raw(io.StringIO(fake_zorro_csv(y_override=wrong)))
    r2, nc2, _, _ = evaluate(rw)
    n_fail_real = sum(r["result"] == "FAIL" for r in r2 if r["role"] == "real")
    report("real filter replaced by P=21 -> real checks FAIL, H1 not PASS",
           n_fail_real > 0 and not verdict(r2, nc2, validate(rw), 6)[0], "(%d real FAIL)" % n_fail_real)
    # (ii) a control that is secretly the correct P=20 filter must be reported as NOT failing
    fine = {("NC1", i): simulate(x[i], 20) for i in INPUTS}
    rw = load_raw(io.StringIO(fake_zorro_csv(y_override=fine)))
    r3, nc3, _, _ = evaluate(rw)
    report("NC1 secretly correct -> 'DID_NOT_FAIL', H1 not PASS",
           (not nc3["NC1"]) and not verdict(r3, nc3, validate(rw), 6)[0])
    # (iii) peak-based gain would be wrong (criteria S3 warning) - the LS method is not
    y20 = simulate(x["s20"], 20)
    peak = (y20[W:].max() - y20[W:].min()) / 2 / AMP
    report("LS gain (T=20, P=20) differs from peak-based gain, as S3 warns",
           abs(m_gain(y20, 20) - peak) > 1e-4,
           "(LS %.6f, peak-based %.6f)" % (m_gain(y20, 20), peak))
    return not failures


# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="C:/Zorro/Data/H1_SS2P_raw.csv")
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    ap.add_argument("--selftest-only", action="store_true")
    a = ap.parse_args()

    print("H1 checker - STEP 1: self-test (no Zorro file is read)")
    if not selftest():
        print("\nSELF-TEST FAILED - stopping. The Zorro file was NOT read.")
        sys.exit(2)
    print("\nSELF-TEST PASSED.")
    if a.selftest_only:
        return

    print("\nSTEP 2: reading %s" % a.raw)
    if not os.path.exists(a.raw):
        print("raw file not found - run the Zorro harness first.")
        sys.exit(3)
    with open(a.raw, "rb") as f:
        blob = f.read()
    sha = hashlib.sha256(blob).hexdigest()
    raw = load_raw(io.StringIO(blob.decode("utf-8", errors="replace")))
    errs = validate(raw)
    os.makedirs(a.out_dir, exist_ok=True)
    out = os.path.join(a.out_dir, "H1_SuperSmoother2Pole_%s.csv" % datetime.date.today().strftime("%Y%m%d"))
    if errs:
        for g, m in errs:
            print("  GUARD ERROR %s: %s" % (g, m))
        write_results(out, [], {}, errs, [], [], a.raw, sha)
        print("H1 VERDICT: FAIL (guard errors; no checks computed). Results: %s" % out)
        sys.exit(1)
    rows, nc, obs, o3 = evaluate(raw)
    ok, n_pass, n_fail, n_err = write_results(out, rows, nc, [], obs, o3, a.raw, sha)
    print("variants run: %d (4 periods + 2 negative controls)" % len(VARIANTS))
    print("real checks: PASS=%d FAIL=%d ERROR=%d" % (n_pass, n_fail, n_err))
    print("NC1 fails as required: %s | NC2 fails as required: %s" % (nc["NC1"], nc["NC2"]))
    for r in rows:
        if r["role"] == "real" and r["result"] != "PASS":
            print("  FAIL %s expected %s actual %s" % (r["check_id"], r["expected"], r["actual"]))
    print("H1 VERDICT: %s\nResults: %s" % ("PASS" if ok else "FAIL", out))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
