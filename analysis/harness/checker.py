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
RFX stage 1 (HARNESS_DESIGN D6, oscillator family): multi-output variants (`outputs`), invariance copies of the sines, and the
checks `trace` / `bound` / `invariance` (osc_rows), all opt-in through spec["osc"]; a spec without it behaves exactly as before.
MST stage 1 (MESAStochastic, D6 + its notes): the models are Reflex (ReflexOut: gate quantity sqrt(MS)) or MESAStochastic
(MesaOut: gate quantity HighestC - LowestC, the model's range); a two-sided ABSOLUTE bound `bound = [lo, hi]` read from a named
output (`bound_output`, e.g. the raw Stoc) next to the old one-sided relative scalar; `startup_info` variants get the INFO start-up row.

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


def base_names(spec):
    """flat, sines, [alt], ramp, [rampdn] (alt = the alternating / Nyquist input, RFF stage 1, only when spec["alt"] is true;
    rampdn = the falling ramp, LRSI stage 1, only when spec["rampdn"] is true)."""
    return (["flat"] + ["s%d" % t for t in spec["ts"]] + (["alt"] if spec.get("alt") else []) + ["ramp"]
            + (["rampdn"] if spec.get("rampdn") else []))


def copy_names(spec):
    """RFX stage 1 (D6 rule 4): one transformed copy of every sine per transform in spec["transforms"], ids <tid><T>."""
    return ["%s%d" % (tr["id"], t) for tr in spec.get("transforms", []) for t in spec["ts"]]


def input_names(spec):
    """Every exported input (x_ columns): base inputs, then the invariance copies (none for the older specs)."""
    return base_names(spec) + copy_names(spec)


def variant_inputs(spec, v):
    """Inputs a variant is called on: the base inputs, plus the invariance copies when the variant says so, minus the variant's
    skipped inputs (LRSI stage 1, `skip`). Order = the generator's call order."""
    ins = input_names(spec) if v.get("invariance") else base_names(spec)
    return [i for i in ins if i not in v.get("skip", ())]


def linear_list(spec):
    """The linear outputs of an oscillator spec as a list ([] without osc)."""
    if not spec.get("osc"):
        return []
    lin = spec["osc"]["linear"]
    return list(lin) if isinstance(lin, (list, tuple)) else [lin]


def skipped_pairs(spec):
    """[(variant id, input)] the spec skips (no call, no column, no check)."""
    return [(v["id"], i) for v in spec["variants"] for i in v.get("skip", ())]


def sine_inputs(spec):
    """Inputs on which the normalised output is well conditioned (sines and their copies)."""
    return ["s%d" % t for t in spec["ts"]] + copy_names(spec)


def input_amp(spec, iid):
    """Sine amplitude of an input (copies carry their transform's amplitude)."""
    for tr in spec.get("transforms", []):
        if iid.startswith(tr["id"]) and iid[len(tr["id"]):].isdigit():
            return tr["amp"]
    return spec["amp"]


def variant_columns(spec, v):
    """[(output or None, input, raw column name)] of one variant, in raw-file order. A variant without `outputs` has the one
    column family y_<id>_<input> (all older specs). With `outputs` the columns are <output>_<id>_<input>; the LAST output is
    the function's return value and is written for every input of the variant, the others for the base inputs only."""
    outs = v.get("outputs")
    if not outs:
        return [(None, i, "y_%s_%s" % (v["id"], i)) for i in variant_inputs(spec, v)]
    cols = []
    for k, o in enumerate(outs):
        ins = variant_inputs(spec, v) if k == len(outs) - 1 else [i for i in base_names(spec) if i not in v.get("skip", ())]
        cols += [(o, i, "%s_%s_%s" % (o, v["id"], i)) for i in ins]
    return cols


def variant_arrays(spec, raw, v):
    """{output (None for a plain variant): {input: array}} from the raw columns."""
    ov = {}
    for o, i, c in variant_columns(spec, v):
        ov.setdefault(o, {})[i] = raw.cols[c]
    return ov


def header_of(spec):
    ins = input_names(spec)
    return (["n", "clock_close"] + ["x_" + i for i in ins]
            + [c for v in spec["variants"] for _, _, c in variant_columns(spec, v)])


# ----------------------------------------------------------------------------- inputs
def make_inputs(spec):
    """Copied from h1_check.make_inputs(), parameters from the spec."""
    n = np.arange(spec["n_bars"], dtype=float)
    x = {"flat": np.full(spec["n_bars"], spec["level"])}
    for t in spec["ts"]:
        x["s%d" % t] = spec["level"] + spec["amp"] * np.sin(2 * math.pi * n / t)
    if spec.get("alt"):
        x["alt"] = spec["level"] + spec["amp"] * (1.0 - 2.0 * (n % 2))        # level + amp*(-1)^n, exact signs
    x["ramp"] = spec["level"] + spec["slope"] * n
    if spec.get("rampdn"):
        x["rampdn"] = spec["level"] - spec["slope"] * n
    for tr in spec.get("transforms", []):
        for t in spec["ts"]:
            x["%s%d" % (tr["id"], t)] = tr["level"] + tr["amp"] * np.sin(2 * math.pi * n / t)
    return x


# ----------------------------------------------------------------------------- measurements
def dc_gain_of(spec):
    """Reference DC gain of the spec's filter (D4). Default 1 = H1 / SS2 / SS3 behaviour."""
    return spec.get("dc_gain", 1.0)


def m_flat(spec, y):
    """h1_check.m_flat, generalised (D4 rule 2): max |y - dc_gain*level| over n >= warmup.
    dc_gain defaults to 1 (1.0*level == level exactly: H1 / SS2 / SS3 results unchanged)."""
    return float(np.max(np.abs(y[spec["w"]:] - dc_gain_of(spec) * spec["level"])))


def _fit(spec, y, t):
    """The least-squares fit y = a*sin(w n) + b*cos(w n) + c over n >= warmup (h1_check.m_gain). One fit
    feeds both the gain and the phase (D4 rule 3). Returns coef (a, b, c)."""
    w0 = spec["w"]
    n = np.arange(spec["n_bars"], dtype=float)[w0:]
    w = 2 * math.pi * n / t
    A = np.column_stack([np.sin(w), np.cos(w), np.ones_like(w)])
    coef, *_ = np.linalg.lstsq(A, y[w0:], rcond=None)
    return coef


def m_gain(spec, y, t):
    """Least-squares sine gain, h1_check.m_gain."""
    coef = _fit(spec, y, t)
    return float(math.hypot(coef[0], coef[1]) / spec["amp"])


def m_phase(spec, y, t):
    """Sine phase (rad) = atan2(b, a) of the SAME fit as m_gain = arg H(e^jw) (output leads when > 0).
    Convention shared with reference.phase_at (test_03 in test_reference_hp.py)."""
    coef = _fit(spec, y, t)
    return float(math.atan2(coef[1], coef[0]))


def _alt_fit(spec, y):
    """Least-squares fit y = a*(-1)^n + c over n >= warmup (decision 2A). Returns (a, c)."""
    w0 = spec["w"]
    n = np.arange(spec["n_bars"], dtype=float)[w0:]
    A = np.column_stack([1.0 - 2.0 * (n % 2), np.ones_like(n)])
    coef, *_ = np.linalg.lstsq(A, y[w0:], rcond=None)
    return float(coef[0]), float(coef[1])


def m_gain_alt(spec, y):
    """Gain at the Nyquist frequency (period 2 bars): |a| / amp of the (-1)^n fit."""
    return abs(_alt_fit(spec, y)[0]) / spec["amp"]


def m_phase_alt(spec, y):
    """Phase at Nyquist: only 0 or pi exist there (H(-1) is real): 0 if the (-1)^n coefficient is >= 0, else pi.
    Convention of reference.phase_at(f, 2) (= arg H(-1), +-pi for a negative value; compare with wrap_phase)."""
    return 0.0 if _alt_fit(spec, y)[0] >= 0 else math.pi


def wrap_phase(d):
    """Wrap an angle difference to (-pi, pi]; callers compare abs() with the tolerance."""
    w = (d + math.pi) % (2 * math.pi) - math.pi
    return math.pi if w == -math.pi else w


def m_ramp_res(spec, y, expected):
    """Ramp residual (D4 rule 4): max |y - expected| over the last 100 ramp bars."""
    return float(np.max(np.abs(y[-100:] - expected)))


def m_startup(spec, y, y_ref):
    """Start-up (D4): max |y - y_ref| over 0 <= n < warmup."""
    w = spec["w"]
    return float(np.max(np.abs(y[:w] - y_ref[:w])))


def m_lag(spec, x, y):
    """Ramp lag, h1_check.m_lag."""
    return float(np.mean((x[-100:] - y[-100:]) / spec["slope"]))


def measure(spec, x, yv):
    """yv: input -> output array for one variant. Returns (flat, [gains], lag)."""
    return (m_flat(spec, yv["flat"]), [m_gain(spec, yv["s%d" % t], t) for t in spec["ts"]],
            m_lag(spec, x["ramp"], yv["ramp"]))


# ----------------------------------------------------------------------------- checks
def _has_lag(spec):
    return dc_gain_of(spec) == 1


def _has_resid(spec, variant):
    return dc_gain_of(spec) != 1 and variant.get("resid") is not None


def _has_linear(spec, variant):
    """The v1 checks (flat, gains, phases, ramp ...) need the variant's linear output: the only output of a plain variant,
    spec["osc"]["linear"] of an oscillator spec (a variant that does not export it gets no linear checks)."""
    if not (spec.get("osc") and variant.get("outputs")):
        return True
    return any(o in variant["outputs"] for o in linear_list(spec))


def linear_views(spec, variant):
    """[(output, variant view)] for the v1 checks of one variant. One-output specs (RFX / MST): [(linear, variant)] (unchanged
    check ids). Multi-linear specs (LRSI): one view per exported linear output, carrying that output's table (expected, phases,
    gain_alt, phase_alt) from variant["linear_tables"]; the checker suffixes its check ids with -<output>."""
    if not isinstance(spec.get("osc", {}).get("linear"), (list, tuple)):
        lin = spec["osc"]["linear"] if spec.get("osc") else None
        return [(lin, variant)]
    out = []
    for o in linear_list(spec):
        if o in variant.get("outputs", ()) and o in variant.get("linear_tables", {}):
            t = variant["linear_tables"][o]
            vv = {k: val for k, val in variant.items() if k not in ("phases", "gain_alt", "phase_alt")}
            vv["expected"] = t["expected"]
            for k in ("phases", "gain_alt", "phase_alt"):
                if k in t:
                    vv[k] = t[k]
            out.append((o, vv))
    return out


def _n_linear_checks(spec, variant):
    """flat + gains + [lag] + [resid] + phases + linear start-ups + alt gain/phase for one (view of a) variant."""
    return (1 + len(spec["ts"]) + (1 if _has_lag(spec) else 0) + (1 if _has_resid(spec, variant) else 0)
            + len(variant.get("phases", {})) + len(spec.get("startup", []))
            + ((1 + (1 if variant.get("phase_alt") is not None else 0)) if spec.get("alt") else 0))


def ramp_exact_inputs(spec, variant):
    """Inputs of the ramp_exact check that the variant is called on (a skipped ramp has no check), in spec order."""
    rex = spec.get("osc", {}).get("ramp_exact") or {}
    ins = variant_inputs(spec, variant)
    return [i for i in rex if i in ins]


def bound_output_of(spec, variant):
    """Name of the output the bound check reads: spec["osc"]["bound_output"], default the variant's return output (Reflex)."""
    return spec["osc"].get("bound_output") or variant["outputs"][-1]


def has_bound(spec, variant):
    """The bound row exists only for a variant that exports its bound output (the superseded MESAStochastic returns only `out`)."""
    return bound_output_of(spec, variant) in variant["outputs"]


def n_osc_checks(spec, variant):
    """trace per sine + bound (if exported) + invariance per transform (only variants with `outputs` in an oscillator spec)."""
    if not (spec.get("osc") and variant.get("outputs")):
        return 0
    return (len(spec["ts"]) + (1 if has_bound(spec, variant) else 0)
            + (len(spec.get("transforms", [])) if variant.get("invariance") else 0)
            + len(ramp_exact_inputs(spec, variant)) + (len(spec["ts"]) if spec["osc"].get("startup") else 0))


def n_checks(spec, variant):
    """Number of checks one variant gets: flat, gains, [ramp-lag if dc_gain == 1], [ramp-res], phases, start-ups, and for an
    oscillator spec trace / bound / invariance / ramp_exact / start-up of the normalised output (n_osc_checks). For specs
    without the D4 keys this is 2 + len(ts) (H1 / SS2 / SS3). Multi-linear specs (LRSI): the linear count per exported linear output."""
    if not _has_linear(spec, variant):
        lin = 0
    elif spec.get("osc") and variant.get("outputs"):
        lin = sum(_n_linear_checks(spec, vv) for _, vv in linear_views(spec, variant))
    else:
        lin = _n_linear_checks(spec, variant)
    return lin + n_osc_checks(spec, variant)


def check_rows(spec, variant, x, yv, xe=None, ov=None):
    """Linear rows (yv: input -> the linear output, None = the variant has none) plus, in an oscillator spec, the
    trace / bound / invariance / INFO rows of osc_rows (ov: {output: {input: array}})."""
    rows = _linear_rows(spec, variant, x, yv, xe) if yv is not None else []
    if spec.get("osc") and ov is not None:
        rows += osc_rows(spec, variant, x, ov)
    return rows


def _linear_rows(spec, variant, x, yv, xe=None):
    """One row per check for one variant (h1_check.check_rows, floats kept unformatted).
    D4 additions, all opt-in from spec / variant keys: ramp-lag only at dc_gain 1, else ramp-res; phase-T<t> at the
    periods in variant["phases"]; startup-<input> for spec["startup"]. xe = the EXPORTED x columns (default: x)."""
    ef, eg, el = variant["expected"]
    rows = []

    def add(cid, inp, e, a, tol, d, res=None):
        fin = math.isfinite(a)
        if res is None:
            res = "ERROR" if not fin else ("PASS" if d <= tol else "FAIL")
        rows.append(dict(check_id="%s-%s-%s" % (spec["id_prefix"], variant["id"], cid),
                         indicator=spec["indicator"], params=variant["params"], asset=spec["asset"],
                         input=inp, expected=e, actual=a, abs_diff=d, tolerance=tol,
                         ratio=(d / tol) if math.isfinite(d) else float("nan"), result=res, role=variant["role"]))

    def row(cid, inp, e, a, tol, is_flat=False):
        fin = math.isfinite(a)
        d = abs(a - e) if fin else float("nan")
        res = None if not is_flat else ("ERROR" if not fin else ("PASS" if a <= tol else "FAIL"))
        add(cid, inp, e, a, tol, d, res=res)

    row("flat", "flat", ef, m_flat(spec, yv["flat"]), spec["tol_flat"], is_flat=True)
    for t, e in zip(spec["ts"], eg):
        row("gain-T%d" % t, "sine T=%d" % t, e, m_gain(spec, yv["s%d" % t], t), spec["tol_gain"])
    if spec.get("alt"):
        row("gain-alt", "alt (-1)^n", variant["gain_alt"], m_gain_alt(spec, yv["alt"]), spec["tol_gain"])
    if _has_lag(spec):
        row("ramp-lag", "ramp", el, m_lag(spec, x["ramp"], yv["ramp"]), spec["tol_lag"])
    if _has_resid(spec, variant):
        yr = yv["ramp"]
        d = m_ramp_res(spec, yr, variant["resid"])
        a = float(np.mean(yr[-100:]))
        add("ramp-res", "ramp (last 100 bars)", variant["resid"], a, spec["tol_resid"], d,
            res=None if math.isfinite(a) else "ERROR")
    for t, e in sorted(variant.get("phases", {}).items()):
        a = m_phase(spec, yv["s%d" % t], t)
        d = abs(wrap_phase(a - e)) if math.isfinite(a) else float("nan")
        add("phase-T%d" % t, "sine T=%d" % t, e, a, spec["tol_phase"], d)
    if spec.get("alt"):
        if variant.get("phase_alt") is not None:                     # expected gain >= phase_gate: checked
            e = variant["phase_alt"]
            a = m_phase_alt(spec, yv["alt"])
            d = abs(wrap_phase(a - e)) if math.isfinite(a) else float("nan")
            add("phase-alt", "alt (-1)^n", e, a, spec["tol_phase"], d)
        elif variant["gain_alt"] >= spec["phase_gate"]:              # table inconsistent with the gate: never silent
            add("phase-alt", "alt (-1)^n: phase_alt missing although gain_alt >= phase_gate", float("nan"),
                float("nan"), spec["tol_phase"], float("nan"), res="ERROR")
        else:                                                        # SKIP, not PASS: the gate binds here
            nan = float("nan")
            rows.append(dict(check_id="%s-%s-phase-alt" % (spec["id_prefix"], variant["id"]),
                             indicator=spec["indicator"], params=variant["params"], asset=spec["asset"],
                             input="alt (-1)^n: SKIP, gain < phase_gate (expected %r < %r)"
                                   % (variant["gain_alt"], spec["phase_gate"]),
                             expected=nan, actual=nan, abs_diff=nan, tolerance=spec["tol_phase"], ratio=nan,
                             result="SKIP", role="skip"))
    if spec.get("startup"):
        model = R.article_model(variant.get("article"))
        xs = x if xe is None else xe
        for i in spec["startup"]:
            if model is None:
                add("startup-%s" % i, "%s, n < %d" % (i, spec["w"]), 0.0, float("nan"), spec["tol_startup"],
                    float("nan"), res="ERROR")
                continue
            # the source's start-up rule: 'zero' (EasyLanguage Vars x(0), HP/RFF) unless the spec says otherwise
            # ([checks].startup_seed, e.g. 'pass3' for the UltimateSmoother: first 3 outputs = Price)
            yref = R.simulate(model, np.asarray(xs[i], dtype=float)[:spec["w"]], seed=spec.get("startup_seed", "zero"))
            a = m_startup(spec, yv[i], yref)
            add("startup-%s" % i, "%s, n < %d" % (i, spec["w"]), 0.0, a, spec["tol_startup"], a)
    return rows


def _kind(check_id):
    tail = check_id.split("-", 2)[2]
    if tail.startswith("gain"):
        return "gain"
    if tail.startswith("phase"):
        return "phase"
    if tail.startswith("ramp-res"):
        return "resid"
    if tail.startswith("startup"):
        return "startup"
    if tail.startswith("trace"):
        return "trace"
    if tail.startswith("bound"):
        return "bound"
    if tail.startswith("invar"):
        return "invariance"
    if tail.startswith("info"):
        return "info"
    if tail.startswith("exact"):                     # LRSI: ramp known answers of the normalised output (exact-ramp / exact-rampdn)
        return "ramp_exact"
    return "lag" if tail.startswith("ramp") else "flat"


def _extra_kinds(spec):
    """D4 kinds enabled by the spec (tolerance present), in report order."""
    return [k for k in ("phase", "resid", "startup", "trace", "bound", "invariance", "ramp_exact")
            if spec.get("tol_" + k) is not None]


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
                    for k in ("flat", "gain", "lag") + tuple(_extra_kinds(spec))}
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
    seeds = {v["id"]: v.get("seed") for v in spec["variants"]}        # None = price (old behaviour); D4
    vmap = {v["id"]: v for v in spec["variants"]}
    shared_cache = {}
    rows = []
    for kind, table in (("pass", imp["must_pass"]), ("fail", imp["must_fail"])):
        for vid, mstr in table.items():
            per, res = {}, None
            # D4: a variant that DECLARES a seed is replayed over the whole run (n >= 0): the seed only differs in
            # the start-up transient, which n >= warmup cannot see. No declared seed: n >= warmup (H1/SS2/SS3).
            lo = 0 if seeds.get(vid) is not None else w
            maker = R.IMP_MODELS.get(mstr)
            if maker is None:
                res = "ERROR"
            else:
                model = maker()
                if isinstance(model, R.MesaModel):                             # MST: replay roof / gated stoc / gated out
                    per = _imp_mesa(spec, raw, vmap[vid], model)
                elif isinstance(model, (R.ReflexModel, R.SharedModel)):        # RFX: replay sum / ms / gated r
                    per = _imp_reflex(spec, raw, vmap[vid], model, shared_cache)
                elif isinstance(model, (R.LrsiModel, R.LrsiShared)):           # LRS: replay l0 / l3 / den / gated out
                    per = _imp_lrsi(spec, raw, vmap[vid], model, shared_cache)
                else:
                    for i in variant_inputs(spec, vmap[vid]):
                        xi = raw.cols["x_" + i]
                        yi = raw.cols["y_%s_%s" % (vid, i)]
                        per[i] = float(np.max(np.abs(yi[lo:] - R.simulate_any(model, xi, seed=seeds.get(vid))[lo:])))
                overall = float("nan") if (not per or not all(math.isfinite(v) for v in per.values())) else max(per.values())
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
                             asset=spec["asset"], input="replay residual n>=%d, overall" % lo,
                             expected=0.0 if kind == "pass" else tol, actual=overall,
                             abs_diff=overall, tolerance=tol, ratio=(overall / tol) if fin else float("nan"),
                             result=res, role="imp", detail=per))
    return rows


# ----------------------------------------------------------------------------- oscillator family (RFX stage 1, D6)
_MODEL_CACHE = {}


def model_out(model, x):
    """R.simulate_reflex / R.simulate_mesa (by the model's type), cached per (model, input content)."""
    x = np.ascontiguousarray(np.asarray(x, dtype=float))
    key = (model, hashlib.md5(x.tobytes()).hexdigest())
    if key not in _MODEL_CACHE:
        if isinstance(model, R.MesaModel):
            _MODEL_CACHE[key] = R.simulate_mesa(model, x)
        elif isinstance(model, R.LrsiModel):
            _MODEL_CACHE[key] = R.simulate_lrsi(model, x)
        else:
            _MODEL_CACHE[key] = R.simulate_reflex(model, x)
    return _MODEL_CACHE[key]


def gate_q(mo):
    """The conditioning quantity of a model output (D6 rule 2): Reflex sqrt(MS); MESAStochastic HighestC - LowestC (the
    model's own range; HARNESS_DESIGN D6 note: 'a gate on its min/max range'); Laguerre RSI CU + CD (the model's denominator)."""
    if isinstance(mo, R.MesaOut):
        return mo.rng
    if isinstance(mo, R.LrsiOut):
        return mo.den
    return np.sqrt(mo.ms)


def norm_out(mo):
    """The normalised output of a model output: Reflex r, MESAStochastic out, Laguerre RSI out."""
    return mo.out if isinstance(mo, (R.MesaOut, R.LrsiOut)) else mo.r


def gate_mask_q(spec, q, amp):
    """Conditioning gate (D6 rule 2): rows n >= warmup where q/amplitude >= spec["osc"]["gate"] (q = gate_q of the MODEL)."""
    return q[spec["w"]:] / amp >= spec["osc"]["gate"]


def gate_mask(spec, ms, amp):
    """Reflex form of the gate: rows n >= warmup where sqrt(MS)/amplitude >= spec["osc"]["gate"]."""
    return gate_mask_q(spec, np.sqrt(ms), amp)


def m_trace(spec, r_zorro, mo, amp):
    """Trace quantity: max |r_Zorro - r_model| over the gated rows >= warmup (the model's gate quantity, the model's normalised
    output). Returns (d, rows used, rows gated out)."""
    w = spec["w"]
    mask = gate_mask_q(spec, gate_q(mo), amp)
    used = int(mask.sum())
    d = float(np.max(np.abs(r_zorro[w:][mask] - norm_out(mo)[w:][mask]))) if used else float("nan")
    return d, used, int(mask.size - used)


def m_bound(arrays):
    """max |r| over every row of every given array."""
    return float(max(np.max(np.abs(a)) for a in arrays))


def m_invariance_q(spec, base, copy, q, amp):
    """Zorro-internal: max |r(base) - r(copy)| over the gated rows >= warmup (gate from the model's gate quantity q of the base sine)."""
    w = spec["w"]
    mask = gate_mask_q(spec, q, amp)
    return (float(np.max(np.abs(base[w:][mask] - copy[w:][mask]))) if mask.any() else float("nan")), int(mask.sum())


def m_invariance(spec, base, copy, ms, amp):
    """Reflex form of m_invariance_q (gate from the model's MS of the base sine)."""
    return m_invariance_q(spec, base, copy, np.sqrt(ms), amp)


def m_bound_two_sided(arrays, lo, hi):
    """(max value, min value, excess) over every row of every given array; excess = max(0, max - hi, lo - min)."""
    top = float(max(np.max(a) for a in arrays))
    bot = float(min(np.min(a) for a in arrays))
    return top, bot, max(0.0, top - hi, lo - bot)


def _orow(spec, variant, cid, inp, e, a, tol, d, res=None, role=None):
    fin = math.isfinite(a) and math.isfinite(d)
    if res is None:
        res = "ERROR" if not fin else ("PASS" if d <= tol else "FAIL")
    return dict(check_id="%s-%s-%s" % (spec["id_prefix"], variant["id"], cid), indicator=spec["indicator"],
                params=variant["params"], asset=spec["asset"], input=inp, expected=e, actual=a, abs_diff=d,
                tolerance=tol, ratio=(d / tol) if (math.isfinite(d) and tol) else float("nan"), result=res,
                role=role or variant["role"])


def osc_rows(spec, variant, x, ov):
    """The D6 checks of one variant with `outputs`: trace per sine (rule 2), bound (rule 3), invariance per transform
    (rule 4, only variants with invariance = true) and, for real variants, INFO rows (flat / ramp / start-up of the
    normalised output, R-4 and finding 5: never PASS/FAIL). The normalised output is the LAST output."""
    osc, w = spec["osc"], spec["w"]
    rz = ov[variant["outputs"][-1]]
    model = R.osc_article_model(variant.get("article"))
    rows = []
    for t in spec["ts"]:
        iid = "s%d" % t
        if model is None or iid not in rz:
            rows.append(_orow(spec, variant, "trace-T%d" % t, "sine T=%d" % t, 0.0, float("nan"), spec["tol_trace"],
                              float("nan"), res="ERROR"))
            continue
        d, used, gated = m_trace(spec, rz[iid], model_out(model, x[iid]), spec["amp"])
        rows.append(_orow(spec, variant, "trace-T%d" % t,
                          "sine T=%d, rows>=%d, gated out %d of %d" % (t, w, gated, gated + used), 0.0, d,
                          spec["tol_trace"], d))
    bo = bound_output_of(spec, variant)
    if isinstance(osc["bound"], (list, tuple)):                      # MST: two-sided ABSOLUTE bound [lo, hi] on the named output
        if has_bound(spec, variant):
            lo_b, hi_b = osc["bound"]
            allr = list(ov.get(bo, {}).values())
            if allr and all(np.all(np.isfinite(a_)) for a_ in allr):
                top, bot, exc = m_bound_two_sided(allr, lo_b, hi_b)
                low = (lo_b - bot) > max(0.0, top - hi_b)              # expected / actual report the breached side (min if low)
                rows.append(_orow(spec, variant, "bound", "%s over every row of %d inputs: min %r, max %r vs [%r, %r]; %s side reported"
                                  % (bo, len(allr), bot, top, lo_b, hi_b, "low" if low else "high"),
                                  lo_b if low else hi_b, bot if low else top, spec["tol_bound"], exc))
            else:
                rows.append(_orow(spec, variant, "bound", "%s: no rows or non-finite" % bo, hi_b, float("nan"),
                                  spec["tol_bound"], float("nan"), res="ERROR"))
    else:                                                            # Reflex: one-sided, RELATIVE allowance on the return output
        allr = [rz[i] for i in variant_inputs(spec, variant) if i in rz]
        a = m_bound(allr) if allr else float("nan")
        b = osc["bound"]
        rows.append(_orow(spec, variant, "bound", "max |r| over every row of %d inputs" % len(allr), b, a,
                          b * spec["tol_bound"], max(0.0, a - b) if math.isfinite(a) else float("nan")))
    if variant.get("invariance"):
        for tr in spec.get("transforms", []):
            worst, used_all = 0.0, 0
            for t in spec["ts"]:
                base, cp = "s%d" % t, "%s%d" % (tr["id"], t)
                if model is None or base not in rz or cp not in rz:
                    worst = float("nan")
                    break
                d, used = m_invariance_q(spec, rz[base], rz[cp], gate_q(model_out(model, x[base])), spec["amp"])
                worst, used_all = max(worst, d) if math.isfinite(d) else float("nan"), used_all + used
                if not math.isfinite(worst):
                    break
            rows.append(_orow(spec, variant, "invar-%s" % tr["id"],
                              "%s: every sine vs its copy (level %g, amp %g), %d gated rows used" % (tr["id"], tr["level"], tr["amp"], used_all),
                              0.0, worst, spec["tol_invariance"], worst))
    rex = osc.get("ramp_exact") or {}
    for iid in ramp_exact_inputs(spec, variant):                     # LRSI: known answers, rows >= W (absolute tol)
        if iid not in rz:
            rows.append(_orow(spec, variant, "exact-%s" % iid, "%s: no column" % iid, rex[iid], float("nan"),
                              spec["tol_ramp_exact"], float("nan"), res="ERROR"))
            continue
        a_ = rz[iid][w:]
        dev = np.abs(a_ - rex[iid])
        k = int(np.argmax(dev)) if np.all(np.isfinite(dev)) else 0
        d = float(dev[k]) if np.all(np.isfinite(dev)) else float("nan")
        rows.append(_orow(spec, variant, "exact-%s" % iid,
                          "%s, rows>=%d: out must equal %r (row furthest from it reported: n=%d)" % (iid, w, rex[iid], w + k),
                          rex[iid], float(a_[k]), spec["tol_ramp_exact"], d))
    if osc.get("startup"):                                           # LRSI: start-up of the normalised output vs the model (L-1)
        for t in spec["ts"]:
            iid = "s%d" % t
            if model is None or iid not in rz:
                rows.append(_orow(spec, variant, "startup-%s" % iid, "%s, rows<%d" % (iid, w), 0.0, float("nan"),
                                  spec["tol_startup"], float("nan"), res="ERROR"))
                continue
            d = float(np.max(np.abs(rz[iid][:w] - norm_out(model_out(model, x[iid]))[:w])))
            rows.append(_orow(spec, variant, "startup-%s" % iid, "%s, rows<%d: max |out - model| (source start-up, L-1)" % (iid, w),
                              0.0, d, spec["tol_startup"], d))
    if variant["role"] == "real" and model is not None:
        nan = float("nan")
        for iid, label in (("flat", "flat"), ("ramp", "ramp")):
            if iid in rz:
                mo = model_out(model, x[iid])
                a = float(np.max(np.abs(rz[iid][w:])))
                e = float(np.max(np.abs(norm_out(mo)[w:])))
                rows.append(_orow(spec, variant, "info-%s" % label, "%s, rows>=%d: max |r| (INFO, ill-conditioned)" % (label, w),
                                  e, a, nan, abs(a - e), res="INFO", role="info"))
    if (variant["role"] == "real" or variant.get("startup_info")) and model is not None and not osc.get("startup"):
        d = 0.0
        for t in spec["ts"]:
            iid = "s%d" % t
            if iid in rz:
                d = max(d, float(np.max(np.abs(rz[iid][:w] - norm_out(model_out(model, x[iid]))[:w]))))
        rows.append(_orow(spec, variant, "info-startup", "sines, rows<%d: max |r - model| (INFO, R-4)" % w, 0.0, d,
                          float("nan"), d, res="INFO", role="info"))
    return rows


def _shared_group(spec, model):
    """[(index, variant id)] of the variants whose must_pass model is a SharedModel of the same Ls, in call order."""
    out = []
    for vid, mstr in spec["imp"]["must_pass"].items():
        mk = R.IMP_MODELS.get(mstr)
        m = mk() if mk else None
        if isinstance(m, R.SharedModel) and m.Ls == model.Ls:
            out.append((m.index, vid))
    return sorted(out)


def _imp_reflex(spec, raw, v, model, cache):
    """IMP replay of an RFX variant: the exported sum / ms columns (base inputs, absolute) and the return output r on the
    well-conditioned inputs only (sines and copies, rows >= warmup, gate from the replay's own MS). A SharedModel replays
    the old Reflex.c's shared MS over ALL call slots of its group in the generator's call order (variant-major, each
    variant's inputs in order). Returns {input: residual}; a non-finite value (everything gated out) is an ERROR upstream."""
    w, vid = spec["w"], v["id"]
    outs = v["outputs"]
    ret = outs[-1]
    vmap = {u["id"]: u for u in spec["variants"]}
    if isinstance(model, R.SharedModel):
        if model.Ls not in cache:
            group = _shared_group(spec, model)
            slots = [(gvid, i) for _, gvid in group for i in variant_inputs(spec, vmap[gvid])]
            Ls = [model.Ls[idx] for idx, gvid in group for _ in variant_inputs(spec, vmap[gvid])]
            sims = R.simulate_shared(Ls, [raw.cols["x_" + i] for _, i in slots])
            cache[model.Ls] = dict(zip(slots, sims))
        mo_of = lambda i: cache[model.Ls][(vid, i)]
    else:
        mo_of = lambda i: model_out(model, raw.cols["x_" + i])
    sines = set(sine_inputs(spec))
    per = {}
    for i in variant_inputs(spec, v):
        mo = mo_of(i)
        d = 0.0
        for o, arr in (("sum", mo.sum), ("ms", mo.ms)):
            if o in outs and o != ret and i in base_names(spec):
                d = max(d, float(np.max(np.abs(raw.cols["%s_%s_%s" % (o, vid, i)][w:] - arr[w:]))))
        if i in sines:
            mask = gate_mask(spec, mo.ms, input_amp(spec, i))
            zr = raw.cols["%s_%s_%s" % (ret, vid, i)][w:]
            dr = float(np.max(np.abs(zr[mask] - mo.r[w:][mask]))) if mask.any() else float("nan")
            d = float("nan") if not math.isfinite(dr) else max(d, dr)           # nothing left after the gate: ERROR upstream, never 0
        per[i] = d
    return per


def _imp_mesa(spec, raw, v, model):
    """IMP replay of an MST variant (HARNESS_DESIGN section 1, first question), residual per input, rows >= warmup:
    the linear output (roof) on every base input (absolute); the raw stoc on the base SINES and the return output on the sines and
    their copies, only on rows the REPLAY's own range gates in (flat / alt / ramp roof are rounding noise, the normalisation
    amplifies it: those rows are INFO, as in Reflex). A non-finite value (everything gated out) is an ERROR upstream, never 0."""
    w = spec["w"]
    vid, outs = v["id"], v["outputs"]
    lin = spec["osc"]["linear"]
    sines = set(sine_inputs(spec))
    per = {}
    for i in variant_inputs(spec, v):
        mo = model_out(model, raw.cols["x_" + i])
        d = 0.0
        for o in outs:
            col = "%s_%s_%s" % (o, vid, i)
            if col not in raw.cols:
                continue
            arr = getattr(mo, o)
            if o == lin:
                d = max(d, float(np.max(np.abs(raw.cols[col][w:] - arr[w:]))))
            elif i in sines:
                mask = gate_mask_q(spec, gate_q(mo), input_amp(spec, i))
                dr = float(np.max(np.abs(raw.cols[col][w:][mask] - arr[w:][mask]))) if mask.any() else float("nan")
                d = float("nan") if not math.isfinite(dr) else max(d, dr)
        per[i] = d
    return per


def lrsi_shared_slots(spec, model):
    """[(variant id, input, gamma)] of every call of the superseded LaguerreRSI file, in the generator's ACTUAL call order: the
    variants whose [imp].must_pass model is an LrsiShared with the same gammas, in spec (= variant-major call) order, each on its
    variant_inputs (skipped inputs have no call). Only these calls touch the file statics; other variants' calls in between do not."""
    out = []
    for v in spec["variants"]:
        mk = R.IMP_MODELS.get(spec["imp"]["must_pass"].get(v["id"], ""))
        m = mk() if mk else None
        if isinstance(m, R.LrsiShared) and m.gs == model.gs:
            out += [(v["id"], i, m.gs[m.index]) for i in variant_inputs(spec, v)]
    return out


def _imp_lrsi(spec, raw, v, model, cache):
    """IMP replay of an LRS variant, residual per input, rows >= warmup: l0 / l3 / den (every exported base input, absolute) and the
    return output `out` on the sines and their copies, only on rows the REPLAY's own CU + CD gates in (flat / alt / ramp out is INFO;
    the ramps are checked by ramp_exact). An LrsiShared model replays the superseded file's shared statics over ALL its calls in the
    generator's call order (lrsi_shared_slots). A non-finite value (everything gated out) is an ERROR upstream, never 0."""
    w, vid = spec["w"], v["id"]
    outs = v["outputs"]
    ret = outs[-1]
    if isinstance(model, R.LrsiShared):
        key = ("lrsi", model.gs)
        if key not in cache:
            slots = lrsi_shared_slots(spec, model)
            sims = R.simulate_lrsi_shared([s[2] for s in slots], [raw.cols["x_" + s[1]] for s in slots])
            cache[key] = {(s[0], s[1]): o for s, o in zip(slots, sims)}
        mo_of = lambda i: cache[key][(vid, i)]
    else:
        mo_of = lambda i: model_out(model, raw.cols["x_" + i])
    sines = set(sine_inputs(spec))
    per = {}
    for i in variant_inputs(spec, v):
        mo = mo_of(i)
        d = 0.0
        for o in outs:
            col = "%s_%s_%s" % (o, vid, i)
            if col not in raw.cols:
                continue
            arr = getattr(mo, o)
            if o != ret:
                d = max(d, float(np.max(np.abs(raw.cols[col][w:] - arr[w:]))))
            elif i in sines:
                mask = gate_mask_q(spec, mo.den, input_amp(spec, i))
                dr = float(np.max(np.abs(raw.cols[col][w:][mask] - arr[w:][mask]))) if mask.any() else float("nan")
                d = float("nan") if not math.isfinite(dr) else max(d, dr)
        per[i] = d
    return per


def floor_quantities(spec):
    """(kind, tolerance/10) the floor guard checks per real variant: gain, lag (dc_gain 1 only), then the D4 kinds
    enabled by the spec. gain and lag first: H1 / SS2 / SS3 rows unchanged."""
    q = [("gain", spec["tol_gain"] / 10)]
    if _has_lag(spec):
        q.append(("lag", spec["tol_lag"] / 10))
    return q + [(k, spec["tol_" + k] / 10) for k in _extra_kinds(spec) if k != "bound"]     # bound: no Zorro-vs-book difference


def floor_rows(spec, rows):
    """Pass item 7: per REAL variant max |Zorro - book| <= tolerance/10 per quantity (D2 rule 3 floor side):
    gain, lag (dc_gain 1), phase, resid, startup. A failing row means the tolerance window is invalid."""
    out = []
    for v in spec["variants"]:
        if v["role"] != "real":
            continue
        pre = "%s-%s-" % (spec["id_prefix"], v["id"])
        rs = [r for r in rows if r["role"] == "real" and r["check_id"].startswith(pre)]
        for q, tol in floor_quantities(spec):
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
    xe = {i: raw.cols["x_" + i] for i in input_names(spec)}          # EXPORTED inputs (start-up reference)
    rows = []
    for v in spec["variants"]:
        ov = variant_arrays(spec, raw, v)
        if v.get("outputs") and spec.get("osc") and isinstance(spec["osc"]["linear"], (list, tuple)):
            vr = []                                            # LRSI: v1 checks per linear output, own table, ids suffixed -<output>
            for o, vv in linear_views(spec, v):
                for r in _linear_rows(spec, vv, x, ov[o], xe):
                    r["check_id"] += "-" + o
                    r["input"] = "%s: %s" % (o, r["input"])
                    vr.append(r)
            vr += osc_rows(spec, v, x, ov)
        elif v.get("outputs"):                                 # RFX: the linear stage is one named output
            yv = ov.get(spec["osc"]["linear"]) if spec.get("osc") else None
            vr = check_rows(spec, v, x, yv, xe=xe, ov=ov)
        else:
            vr = check_rows(spec, v, x, ov[None], xe=xe)
        if v["role"] == "info":              # USE stage 1: an INFO variant is measured and reported, never PASS/FAIL
            for r in vr:
                if r["result"] in ("PASS", "FAIL"):
                    r["result"] = "INFO"
                if r["result"] != "SKIP":
                    r["role"] = "info"
        rows += vr
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
    expect_real = sum(n_checks(spec, v) for v in spec["variants"] if v["role"] == "real")
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
        fl = {q: [r["actual"] for r in rows if r["check_id"] == pre + "floor-" + q][0]
              for q, _ in floor_quantities(spec)}
        txt = "# O_IMP_RESIDUAL %s imp=%s zorro_vs_book_gain_max=%.3e" % (
            v["id"], "%.3e" % imp[0] if imp else "n/a", fl["gain"])
        if "lag" in fl:
            txt += " zorro_vs_book_lag=%.3e" % fl["lag"]
        for k in _extra_kinds(spec):
            if k in fl:
                txt += " zorro_vs_book_%s=%.3e" % (k, fl[k])
        out.append(txt + " (INFO)")
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
        ninfo = sum(v["role"] == "info" for v in spec["variants"])
        xinfo = (" info=%d" % ninfo) if ninfo else ""
        if not ext:
            f.write("# batch=%s variants_run=%d\n" % (spec["batch"], len(spec["variants"]) if not errs
                                                       else 0))
        elif not errs:
            f.write("# batch=%s variants_run=%d real=%d neg_control=%d%s\n"
                    % (spec["batch"], len(spec["variants"]), nreal, nneg, xinfo))
        else:
            gids = sorted(set(g for g, _ in errs))
            f.write("# batch=%s variants NOT evaluated (guard fired: %s) variants_defined=%d real=%d "
                    "neg_control=%d%s\n" % (spec["batch"], ",".join(gids), len(spec["variants"]), nreal, nneg, xinfo))
        f.write("# real_checks=%d PASS=%d FAIL=%d ERROR=%d\n"
                % (c["n_real"], c["n_pass"], c["n_fail"], c["n_err"]))
        sk_pairs = skipped_pairs(spec)
        if sk_pairs:
            f.write("# SKIPPED_INPUTS=%d (variant:input; no call, no raw column, no check; spec skip_inputs): %s\n"
                    % (len(sk_pairs), ",".join("%s:%s" % s for s in sk_pairs)))
        if spec.get("alt"):
            sk = [r["check_id"] for r in rows if r["result"] == "SKIP"]
            f.write("# SKIP=%d (alt phase where the expected gain < phase_gate %g; not a PASS, not counted in "
                    "real_checks): %s\n" % (len(sk), spec["phase_gate"], ",".join(sk)))
        for vid, d in nc.items():
            xk = _extra_kinds(spec)
            f.write("# NC %s fails_as_required=%s margin10_met=%s max_ratio gain=%.3e lag=%.3e flat=%.3e"
                    % (vid, d["fails_as_required"], d["margin10_met"], d["max_ratio"].get("gain", 0.0),
                       d["max_ratio"].get("lag", 0.0), d["max_ratio"].get("flat", 0.0)))
            for k in xk:
                f.write(" %s=%.3e" % (k, d["max_ratio"].get(k, 0.0)))
            if d["required"] is not None:
                f.write(" detected gain=%s lag=%s flat=%s"
                        % (d["detected"]["gain"], d["detected"]["lag"], d["detected"]["flat"]))
                for k in xk:
                    f.write(" %s=%s" % (k, d["detected"][k]))
                f.write(" required=%s" % ",".join(d["required"]))
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
            + [c for v in spec["variants"] if v["role"] == "real" for _, _, c in variant_columns(spec, v)])


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
