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
MAF stage 1 (HARNESS_DESIGN D7, adaptive smoothers), a separate path keyed by spec["adaptive"] (generator.to_checker_spec_adaptive): bars
inputs (band High / Low, exported xh_ / xl_ and guarded), affine equivariance copies, trace of every column from row 1 with the pre-run
per-(input, column) conditioning classification (conditioning_table / conditioning_mismatches), per-column bounds, hull, equivariance,
ramp_exact / lag / flat known answers, per-column tolerances, an IMP replay whose INFO pairs are reported but never decide, the shared-state
replays of the superseded MAMA.c / FRAMA.c (adaptive_shared_slots), and a floor guard per column group. Older specs never enter it.

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
    """Every exported input (x_ columns): base inputs, then the invariance copies (none for the older specs). D7 (spec["adaptive"]):
    base inputs, band inputs, equivariance copies."""
    if spec.get("adaptive"):
        ad = spec["adaptive"]
        return list(ad["base"]) + list(ad["band"]) + [c["id"] for c in ad["copies"]]
    return base_names(spec) + copy_names(spec)


def variant_inputs(spec, v):
    """Inputs a variant is called on: the base inputs, plus the invariance copies when the variant says so, minus the variant's
    skipped inputs (LRSI stage 1, `skip`). Order = the generator's call order. D7: base + band inputs, plus the copies with
    equivariance = true."""
    if spec.get("adaptive"):
        return input_names(spec) if v.get("equivariance") else adaptive_traced(spec)
    ins = input_names(spec) if v.get("invariance") else base_names(spec)
    return [i for i in ins if i not in v.get("skip", ())]


def linear_list(spec):
    """The linear outputs of an oscillator spec as a list ([] without osc)."""
    if not spec.get("osc"):
        return []
    lin = spec["osc"]["linear"]
    if lin is None:                                  # FSH: no linear stage
        return []
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
    if spec.get("adaptive"):                     # D7: every output on every input of the variant (copies need all columns)
        return [(o, i, "%s_%s_%s" % (o, v["id"], i)) for o in outs for i in variant_inputs(spec, v)]
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
            + ([c for i in adaptive_bar_names(spec) for c in ("xh_" + i, "xl_" + i)] if spec.get("adaptive") else [])
            + [c for v in spec["variants"] for _, _, c in variant_columns(spec, v)])


# ----------------------------------------------------------------------------- D7 inputs (MAF stage 1)
def adaptive_traced(spec):
    """D7: the inputs every variant is called on and traced on (base + band; the copies are for equivariance and IMP only)."""
    ad = spec["adaptive"]
    return list(ad["base"]) + list(ad["band"])


def adaptive_bar_names(spec):
    """D7: inputs with their own High / Low (band inputs and copies of band inputs), in input order (= generator.adaptive_bar_ids)."""
    ad = spec["adaptive"]
    bs = set(ad["band"])
    return [i for i in input_names(spec) if i in bs or any(c["id"] == i and c["base"] in bs for c in ad["copies"])]


def make_bars(spec, x=None):
    """D7: {input: (High, Low)} for every input: point bars H = L = x; band H = x + h, L = x - h; a copy of a band input
    H = k*H_base + c, L = k*L_base + c (the generator's run-time order). Computed in float64 as the script computes them."""
    x = make_inputs(spec) if x is None else x
    ad = spec["adaptive"]
    out = {i: (x[i], x[i]) for i in input_names(spec)}
    for i in ad["band"]:
        out[i] = (x[i] + ad["band_half"], x[i] - ad["band_half"])
    for c in ad["copies"]:
        if c["base"] in ad["band"]:
            tr = ad["transforms"][c["tid"]]
            hb, lb = out[c["base"]]
            out[c["id"]] = (tr["scale"] * hb + tr["offset"], tr["scale"] * lb + tr["offset"])
    return out


def _adaptive_inputs(spec):
    n = np.arange(spec["n_bars"], dtype=float)
    ad = spec["adaptive"]
    x = {"flat": np.full(spec["n_bars"], spec["level"])}
    for t in spec["ts"]:
        x["s%d" % t] = spec["level"] + spec["amp"] * np.sin(2 * math.pi * n / t)
    x["ramp"] = spec["level"] + spec["slope"] * n
    if "rampdn" in ad["base"]:                                  # ATR stage 1: [inputs].ramp_down
        x["rampdn"] = spec["level"] - spec["slope"] * n
    for i in ad["band"]:
        x[i] = x[i[:-1]].copy()
    for c in ad["copies"]:
        tr = ad["transforms"][c["tid"]]
        x[c["id"]] = tr["scale"] * x[c["base"]] + tr["offset"]
    return x


# ----------------------------------------------------------------------------- inputs
def make_inputs(spec):
    """Copied from h1_check.make_inputs(), parameters from the spec."""
    if spec.get("adaptive"):
        return _adaptive_inputs(spec)
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
    osc = spec["osc"]
    outs = variant["outputs"]
    if not (osc.get("trace_outputs") or osc.get("bounds") or osc.get("ramp_exact_outputs") or osc.get("trigger")
            or osc.get("flat_zero")):
        return (len(spec["ts"]) + (1 if has_bound(spec, variant) else 0)
                + (len(spec.get("transforms", [])) if variant.get("invariance") else 0)
                + len(ramp_exact_inputs(spec, variant)) + (len(spec["ts"]) if osc.get("startup") else 0))
    # FSH stage 1 keys (each counts only what the variant exports)
    to = osc.get("trace_outputs")
    n = len(spec["ts"]) * (sum(o in outs for o in to) if to else 1)
    n += sum(o in outs for o in osc["bounds"]) if osc.get("bounds") else (1 if has_bound(spec, variant) else 0)
    n += len(spec.get("transforms", [])) if variant.get("invariance") else 0
    n += len(fisher_exact_pairs(spec, variant)) if osc.get("ramp_exact_outputs") else len(ramp_exact_inputs(spec, variant))
    n += len(spec["ts"]) if osc.get("startup") else 0
    n += 1 if has_trigger(spec, variant) else 0
    n += 1 if flat_zero_outputs(spec, variant) else 0
    return n


def fisher_exact_pairs(spec, variant):
    """[(output, input, expected)] of the ramp_exact_outputs checks the variant gets (exported output, input it is called on)."""
    reo = spec["osc"].get("ramp_exact_outputs") or {}
    ins = variant_inputs(spec, variant)
    return [(o, i, e) for o, tab in reo.items() if o in variant["outputs"] for i, e in tab.items() if i in ins]


def has_trigger(spec, variant):
    """FSH: the trigger row exists for a variant that exports trig and returns out."""
    return bool(spec["osc"].get("trigger")) and "trig" in variant["outputs"] and variant["outputs"][-1] == "out"


def flat_zero_outputs(spec, variant):
    """FSH: the flat_zero outputs the variant exports (flat must be one of its inputs); [] = no flat_zero row."""
    fz = spec["osc"].get("flat_zero") or []
    if "flat" not in variant_inputs(spec, variant):
        return []
    return [o for o in fz if o in variant["outputs"]]


def n_checks(spec, variant):
    """Number of checks one variant gets: flat, gains, [ramp-lag if dc_gain == 1], [ramp-res], phases, start-ups, and for an
    oscillator spec trace / bound / invariance / ramp_exact / start-up of the normalised output (n_osc_checks). For specs
    without the D4 keys this is 2 + len(ts) (H1 / SS2 / SS3). Multi-linear specs (LRSI): the linear count per exported linear output."""
    if spec.get("adaptive"):
        return adaptive_n_checks(spec, variant)
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
    if tail.startswith("trigger"):                   # FSH: trig[n] == out[n-1]
        return "trigger"
    if tail.startswith("flatzero"):                  # FSH: flat rows of raw / v1 / out are 0
        return "flat_zero"
    if tail.startswith("equiv"):                     # MAF (D7): out(kx + c) = k out(x) + c, adaptation columns unchanged
        return "equivariance"
    if tail.startswith("hull"):                      # MAF (D7): out within the running [min x, max x]
        return "hull"
    if tail.startswith("whull"):                     # ATR: column within [min, max] of the TR window of length P
        return "window_hull"
    if tail.startswith("known"):                     # ATR: column equals a pre-registered constant on rows >= the window
        return "known_value"
    return "lag" if tail.startswith("ramp") else "flat"


def _extra_kinds(spec):
    """D4 kinds enabled by the spec (tolerance present), in report order."""
    return [k for k in ("phase", "resid", "startup", "trace", "bound", "invariance", "ramp_exact", "trigger", "flat_zero",
                        "equivariance", "hull", "window_hull", "known_value")
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
        if spec.get("adaptive"):                         # D7: the exported High / Low of the band inputs and their copies
            bars = make_bars(spec, x)
            for i in adaptive_bar_names(spec):
                for k, col in ((0, "xh_"), (1, "xl_")):
                    d = np.abs(raw.cols[col + i] - bars[i][k])
                    if not np.all(d <= spec["tol_x"]):
                        errs.append(("G_INPUT_MISMATCH", "%s%s differs from the band input: max |diff| %.3g > %g"
                                     % (col, i, float(np.nanmax(d)) if np.any(np.isfinite(d)) else float("nan"), spec["tol_x"])))
    return errs


# ----------------------------------------------------------------------------- IMP + floor guard (SS3)
def imp_rows(spec, raw, x=None):
    """[imp] (SS3 spec decision 4, pass item 6). For every variant in must_pass / must_fail: replay the
    recursion with the named model (reference.IMP_MODELS, explicit registry, no eval) on the x columns
    EXPORTED in the raw file; residual = max |y_Zorro - y_replay| over n >= warmup, per input and overall.
    One row per listed variant and list (role "imp"). must_pass: residual <= tol; must_fail: residual > tol.
    An unknown model string or a non-finite residual is an ERROR row. Per-input residuals are kept in
    row["detail"] (not written to the CSV columns)."""
    if spec.get("adaptive"):
        return adaptive_imp_rows(spec, raw)
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
                elif isinstance(model, (R.FisherModel, R.FisherShared)):       # FSH: replay raw / v1 / rng / trig / out
                    per = _imp_fisher(spec, raw, vmap[vid], model, shared_cache)
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
        elif isinstance(model, R.FisherModel):
            _MODEL_CACHE[key] = R.simulate_fisher(model, x)
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
    if isinstance(mo, R.FisherOut):                  # FSH: the model's window range MaxH - MinL
        return mo.rng
    return np.sqrt(mo.ms)


def norm_out(mo):
    """The normalised output of a model output: Reflex r, MESAStochastic out, Laguerre RSI out, Fisher out."""
    return mo.out if isinstance(mo, (R.MesaOut, R.LrsiOut, R.FisherOut)) else mo.r


def osc_mask(spec, mo, amp, gates):
    """FSH per-output gate (rows n >= warmup), evaluated on the MODEL: 'range' = gate_q(mo)/amp >= trace_gate (D6 rule 2);
    'clamp' = min |pre-clamp v1 -/+ thr| >= clamp_gate (a rounding flip of the clamp moves Fish by atanh(.999) - atanh(.99)).
    (c) The clamp gate removes the flip row only; a flip would also move later rows (v1 memory .67^n, Fish .5^n); none is expected
    on these inputs (model margin 7.1e-4 vs the gate 1e-6)."""
    w = spec["w"]
    m = gate_mask_q(spec, gate_q(mo), amp)
    if "clamp" in gates:
        m = m & (mo.cdist[w:] >= spec["osc"]["clamp_gate"])
    return m


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


def _trace_rows_multi(spec, variant, x, ov, model):
    """FSH: trace replay of every exported output in spec["osc"]["trace_outputs"], per sine, rows >= warmup, on the rows the MODEL's
    gates for that output let in (osc_mask). Ids trace-<output>-T<t>. Every row of a sine gated = ERROR (nothing compared)."""
    w = spec["w"]
    rows = []
    for o, gates in spec["osc"]["trace_outputs"].items():
        if o not in variant["outputs"]:
            continue
        zo = ov.get(o, {})
        for t in spec["ts"]:
            iid, cid = "s%d" % t, "trace-%s-T%d" % (o, t)
            if model is None or iid not in zo:
                rows.append(_orow(spec, variant, cid, "%s, sine T=%d" % (o, t), 0.0, float("nan"), spec["tol_trace"],
                                  float("nan"), res="ERROR"))
                continue
            mo = model_out(model, x[iid])
            mask = osc_mask(spec, mo, spec["amp"], gates)
            used = int(mask.sum())
            d = float(np.max(np.abs(zo[iid][w:][mask] - getattr(mo, o)[w:][mask]))) if used else float("nan")
            rows.append(_orow(spec, variant, cid, "%s, sine T=%d, rows>=%d, gates %s, gated out %d of %d"
                              % (o, t, w, "+".join(gates), mask.size - used, mask.size), 0.0, d, spec["tol_trace"], d))
    return rows


def _bound_rows_multi(spec, variant, ov):
    """FSH: one bound row per exported output of spec["osc"]["bounds"], every row of every input of that output. A pair [lo, hi] is
    two-sided with the ABSOLUTE allowance tol_bound (MST form); a number b is one-sided |y| <= b with the RELATIVE allowance
    b * tol_bound (Reflex form). Ids bound-<output>."""
    rows = []
    tol = spec["tol_bound"]
    for o, b in spec["osc"]["bounds"].items():
        if o not in variant["outputs"]:
            continue
        allr = list(ov.get(o, {}).values())
        cid = "bound-%s" % o
        if not allr or not all(np.all(np.isfinite(a_)) for a_ in allr):
            rows.append(_orow(spec, variant, cid, "%s: no rows or non-finite" % o, float("nan"), float("nan"), tol,
                              float("nan"), res="ERROR"))
        elif isinstance(b, (list, tuple)):
            top, bot, exc = m_bound_two_sided(allr, b[0], b[1])
            low = (b[0] - bot) > max(0.0, top - b[1])
            rows.append(_orow(spec, variant, cid, "%s over every row of %d inputs: min %r, max %r vs [%r, %r]; %s side reported"
                              % (o, len(allr), bot, top, b[0], b[1], "low" if low else "high"),
                              b[0] if low else b[1], bot if low else top, tol, exc))
        else:
            a = m_bound(allr)
            rows.append(_orow(spec, variant, cid, "max |%s| over every row of %d inputs vs %r (relative allowance)" % (o, len(allr), b),
                              b, a, b * tol, max(0.0, a - b)))
    return rows


def _exact_rows_multi(spec, variant, x, ov, model):
    """FSH: known answers on the ramps, rows >= warmup, per (output, input) of ramp_exact_outputs: a number, or "model" (the article
    model's own output on that input, row by row). ABSOLUTE tolerance tol_ramp_exact. Ids exact-<output>-<input>."""
    w = spec["w"]
    rows = []
    tol = spec["tol_ramp_exact"]
    for o, iid, e in fisher_exact_pairs(spec, variant):
        cid = "exact-%s-%s" % (o, iid)
        zo = ov.get(o, {})
        if iid not in zo or (e == "model" and model is None):
            rows.append(_orow(spec, variant, cid, "%s %s: no column or no model" % (o, iid), float("nan"), float("nan"), tol,
                              float("nan"), res="ERROR"))
            continue
        a_ = zo[iid][w:]
        ref = getattr(model_out(model, x[iid]), o)[w:] if e == "model" else np.full(a_.shape, float(e))
        dev = np.abs(a_ - ref)
        fin = bool(np.all(np.isfinite(dev)))
        k = int(np.argmax(dev)) if fin else 0
        d = float(dev[k]) if fin else float("nan")
        rows.append(_orow(spec, variant, cid, "%s %s, rows>=%d: must equal %s (row furthest from it reported: n=%d); max |%s| = %r"
                          % (o, iid, w, "the model" if e == "model" else repr(float(e)), w + k, o,
                             float(np.max(np.abs(a_))) if fin else float("nan")),
                          float(ref[k]), float(a_[k]), tol, d))
    return rows


def _trigger_row(spec, variant, ov):
    """FSH: trig[n] must equal out[n-1] exactly for n >= 1 on every input trig is exported for (Zorro-internal, no model)."""
    tr, out = ov["trig"], ov[variant["outputs"][-1]]
    ins = [i for i in tr if i in out]
    if not ins:
        return _orow(spec, variant, "trigger", "no trig column", 0.0, float("nan"), spec["tol_trigger"], float("nan"), res="ERROR")
    d = 0.0
    for i in ins:
        di = np.abs(tr[i][1:] - out[i][:-1])
        if not np.all(np.isfinite(di)):
            d = float("nan")
            break
        d = max(d, float(np.max(di)))
    t0 = max(float(np.max(np.abs(tr[i][:1]))) for i in ins)
    return _orow(spec, variant, "trigger", "trig[n] vs %s[n-1], n>=1, %d inputs (exact); max |trig[0]| = %r (INFO)"
                 % (variant["outputs"][-1], len(ins), t0), 0.0, d, spec["tol_trigger"], d)


def _flat_zero_row(spec, variant, ov):
    """FSH: every flat row (n >= 0) of the listed outputs must be 0 (implementation known answer under the zero-range guard)."""
    outs = flat_zero_outputs(spec, variant)
    vals = [ov[o]["flat"] for o in outs if "flat" in ov.get(o, {})]
    if len(vals) != len(outs) or not all(np.all(np.isfinite(a_)) for a_ in vals):
        return _orow(spec, variant, "flatzero", "flat: missing or non-finite", 0.0, float("nan"), spec["tol_flat_zero"],
                     float("nan"), res="ERROR")
    per = {o: float(np.max(np.abs(a_))) for o, a_ in zip(outs, vals)}
    d = max(per.values())
    return _orow(spec, variant, "flatzero", "flat, every row: max |y| of %s (%s)"
                 % ("/".join(outs), ", ".join("%s %r" % kv for kv in per.items())), 0.0, d, spec["tol_flat_zero"], d)


def osc_rows(spec, variant, x, ov):
    """The D6 checks of one variant with `outputs`: trace per sine (rule 2), bound (rule 3), invariance per transform
    (rule 4, only variants with invariance = true) and, for real variants, INFO rows (flat / ramp / start-up of the
    normalised output, R-4 and finding 5: never PASS/FAIL). The normalised output is the LAST output."""
    osc, w = spec["osc"], spec["w"]
    rz = ov[variant["outputs"][-1]]
    model = R.osc_article_model(variant.get("article"))
    rows = []
    if osc.get("trace_outputs"):                                     # FSH: trace on several outputs, per-output gates on the MODEL
        rows += _trace_rows_multi(spec, variant, x, ov, model)
    else:
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
    bo = bound_output_of(spec, variant) if not osc.get("bounds") else None
    if osc.get("bounds"):                                            # FSH: one bound row per exported output
        rows += _bound_rows_multi(spec, variant, ov)
    elif isinstance(osc["bound"], (list, tuple)):                    # MST: two-sided ABSOLUTE bound [lo, hi] on the named output
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
                if (osc.get("trace_outputs") or {}).get(variant["outputs"][-1]):   # FSH: the return output's trace gates
                    mask = osc_mask(spec, model_out(model, x[base]), spec["amp"], osc["trace_outputs"][variant["outputs"][-1]])
                    used = int(mask.sum())
                    d = float(np.max(np.abs(rz[base][w:][mask] - rz[cp][w:][mask]))) if used else float("nan")
                else:
                    d, used = m_invariance_q(spec, rz[base], rz[cp], gate_q(model_out(model, x[base])), spec["amp"])
                worst, used_all = max(worst, d) if math.isfinite(d) else float("nan"), used_all + used
                if not math.isfinite(worst):
                    break
            rows.append(_orow(spec, variant, "invar-%s" % tr["id"],
                              "%s: every sine vs its copy (level %g, amp %g), %d gated rows used" % (tr["id"], tr["level"], tr["amp"], used_all),
                              0.0, worst, spec["tol_invariance"], worst))
    if osc.get("ramp_exact_outputs"):                                # FSH: known answers per output (number or the model)
        rows += _exact_rows_multi(spec, variant, x, ov, model)
    if has_trigger(spec, variant):
        rows.append(_trigger_row(spec, variant, ov))
    if flat_zero_outputs(spec, variant):
        rows.append(_flat_zero_row(spec, variant, ov))
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


# ----------------------------------------------------------------------------- adaptive smoothers (MAF stage 1, D7)
_AD_CACHE = {}


def _h(a):
    return None if a is None else hashlib.md5(np.ascontiguousarray(np.asarray(a, dtype=float)).tobytes()).hexdigest()


def adaptive_out(model, x, H=None, L=None):
    """reference.adaptive_simulate cached per (model, input content, High, Low)."""
    key = (model, _h(x), _h(H), _h(L))
    if key not in _AD_CACHE:
        _AD_CACHE[key] = R.adaptive_simulate(model, np.asarray(x, dtype=float), H, L)
    return _AD_CACHE[key]


def col_tol(spec, q, col):
    """Tolerance of kind q for one column (per-column override, else the kind's value)."""
    return spec.get("tolcols_" + q, {}).get(col, spec["tol_" + q])


def _arow(spec, variant, cid, inp, e, a, q, col, d, res=None, role=None):
    r = _orow(spec, variant, cid, inp, e, a, col_tol(spec, q, col) if col else spec["tol_" + q], d, res=res, role=role)
    r["tgroup"] = col if (col and col in spec.get("tolcols_" + q, {})) else ""
    return r


def adaptive_columns(spec, variant):
    """The variant's exported columns in the spec's column order."""
    return [c for c in spec["adaptive"]["columns"] if c in variant["outputs"]]


def adaptive_n_checks(spec, v):
    """PASS/FAIL checks of one D7 variant: trace per CHECKED (input, column) (rule 3), one bound per bounded column, one hull row,
    equivariance per (input, transform, column), ramp_exact / lag / flat per listed (column, input)."""
    ad = spec["adaptive"]
    cols = adaptive_columns(spec, v)
    vin = variant_inputs(spec, v)
    info = {tuple(p) for p in v["info_pairs"]}
    n = sum((i, c) not in info for i in adaptive_traced(spec) for c in cols)
    n += sum(c in cols for c in v["bounds"])
    n += sum(c in cols for c in ad.get("range_bound", ()))
    n += sum(c in cols for c in ad.get("window_hull", {}))
    n += 1 if any(c in cols for c in ad["hull"]) else 0
    if v.get("equivariance"):
        n += sum(1 for cp in ad["copies"] if cp["base"] in ad["eq_inputs"]) * len(cols)
    n += sum(1 for c, i in ad["ramp_exact"].items() if c in cols and i in vin)
    n += sum(1 for c, i in ad["ramp_lag"].items() if c in cols and i in vin)
    n += sum(1 for c in ad["flat"] if c in cols and "flat" in vin)
    n += sum(1 for c, m_ in ad.get("known_value", {}).items() if c in cols for i in m_ if i in vin)
    return n


def adaptive_rows(spec, v, x, bars, ov):
    """The D7 checks of one variant (HARNESS_DESIGN D7 rules 2-6):
      trace-<col>-<input>    every exported column vs the source model, every row n >= w (w = 0: from row 1), on the base and band
                             inputs; an (input, column) pair listed as INFO in the expected table's conditioning (rule 3) is written
                             as info-trace-<col>-<input> (INFO, never PASS/FAIL) for real / info variants and skipped for controls;
      bound-<col>            the expected table's per-column bounds over every row n >= from_n of every input of the variant,
                             relative allowance |bound| x tol_bound (the larger relative excess side is reported);
      hull                   the hull columns within the running [min x, max x] of the input, every row, absolute tol_hull;
      equiv-<tid>-<col>      on each equivariance input: copy = k base + c (level columns) or = base (the rest), rows >= eq_from;
      exact-<col>-<input>    ramp_exact: the column equals x on every row;
      ramp-lag-<input>       mean (x - y)/slope over the last 100 rows vs the expected table's ramp_lag;
      flat-<col>             the column equals the level on every flat row;
      info-flat              (real only) max |col - level| on flat rows >= flat_info.from_n (INFO)."""
    ad, w = spec["adaptive"], spec["w"]
    model = R.adaptive_article_model(v.get("article"))
    cols = adaptive_columns(spec, v)
    vin = variant_inputs(spec, v)
    info = {tuple(p) for p in v["info_pairs"]}
    nan = float("nan")
    rows = []
    for i in adaptive_traced(spec):
        mo = adaptive_out(model, x[i], *bars[i]) if model is not None else None
        for c in cols:
            is_info = (i, c) in info
            if is_info and v["role"] == "neg_control":
                continue
            cid = ("info-trace-%s-%s" if is_info else "trace-%s-%s") % (c, i)
            z = ov.get(c, {}).get(i)
            if mo is None or z is None:
                rows.append(_arow(spec, v, cid, "%s %s: no column or no model" % (c, i), 0.0, nan, "trace", c, nan, res="ERROR"))
                continue
            dev = np.abs(z[w:] - getattr(mo, c)[w:])
            fin = bool(np.all(np.isfinite(dev)))
            k = int(np.argmax(dev)) if fin else 0
            d = float(dev[k]) if fin else nan
            txt = "%s %s, rows n>=%d vs the source model (max at n=%d)%s" % (c, i, w, w + k, "; INFO (rule 3: ill-conditioned)" if is_info else "")
            rows.append(_arow(spec, v, cid, txt, float(getattr(mo, c)[w + k]), float(z[w + k]) if fin else nan, "trace", c, d,
                              res="INFO" if is_info else None, role="info" if is_info else None))
    for c, s in v["bounds"].items():
        if c not in cols:
            continue
        f0 = int(s.get("from_n", 0))
        arrs = [ov[c][i][f0:] for i in vin if i in ov.get(c, {})]
        if not arrs or not all(np.all(np.isfinite(a_)) for a_ in arrs):
            rows.append(_arow(spec, v, "bound-%s" % c, "%s: no rows or non-finite" % c, nan, nan, "bound", None, nan, res="ERROR"))
            continue
        top, bot = float(max(np.max(a_) for a_ in arrs)), float(min(np.min(a_) for a_ in arrs))
        sides = []
        if "lo" in s:
            sides.append(("low", s["lo"], bot, max(0.0, s["lo"] - bot)))
        if "hi" in s:
            sides.append(("high", s["hi"], top, max(0.0, top - s["hi"])))
        side, bnd, val, exc = max(sides, key=lambda t: t[3] / abs(t[1]) if t[1] else (float("inf") if t[3] else 0.0))
        r = _orow(spec, v, "bound-%s" % c, "%s over rows n>=%d of %d inputs: min %r, max %r vs [%s, %s]; %s side reported (relative "
                  "allowance)" % (c, f0, len(arrs), bot, top, repr(s.get("lo", "-inf")), repr(s.get("hi", "inf")), side),
                  bnd, val, abs(bnd) * spec["tol_bound"] + spec.get("tol_bound_abs", 0.0), exc)
        r["tgroup"] = ""
        rows.append(r)
    for c in ad.get("range_bound", ()):                          # ATR: column >= High - Low on rows >= 1 (row 0 has no previous close)
        if c not in cols:
            continue
        bots = []
        for i in vin:
            H_, L_ = bars[i]
            z = ov.get(c, {}).get(i)
            if z is not None:
                bots.append(float(np.min(z[1:] - (H_[1:] - L_[1:]))))
        ok = bool(bots) and len(bots) == len(vin) and all(math.isfinite(b_) for b_ in bots)
        bot = min(bots) if ok else nan
        r = _orow(spec, v, "bound-%s-range" % c, "%s - (High - Low) over rows n>=1 of %d inputs: min %r, must be >= 0 (absolute allowance)"
                  % (c, len(vin), bot), 0.0, bot, spec.get("tol_bound_abs", 0.0), max(0.0, -bot) if ok else nan, res=None if ok else "ERROR")
        r["tgroup"] = ""
        rows.append(r)
    for c, of in ad.get("window_hull", {}).items():              # ATR: column within [min, max] of `of` over the last window rows, rows >= window
        if c not in cols:
            continue
        w0 = v["window"]
        worst, where, ok = 0.0, "", True
        for i in vin:
            t_ = ov[of][i] if of in cols else getattr(adaptive_out(model, x[i], *bars[i]), of)
            sw = np.lib.stride_tricks.sliding_window_view(t_, w0)          # sw[k] = t_[k .. k+w0-1]: row r = k + w0 - 1
            lo_, hi_ = sw.min(axis=1)[1:], sw.max(axis=1)[1:]              # rows r = w0 .. N-1
            a_ = ov[c][i][w0:]
            e_ = np.maximum(np.maximum(lo_ - a_ - np.abs(lo_) * spec["tol_window_hull"], a_ - hi_ - np.abs(hi_) * spec["tol_window_hull"]),
                            0.0)
            if not np.all(np.isfinite(e_)):
                ok = False
                break
            if float(np.max(e_)) > worst or not where:
                worst, where = max(worst, float(np.max(e_))), "%s n=%d" % (i, w0 + int(np.argmax(e_)))
        tol_ = spec.get("tol_window_hull_abs") or spec["tol_window_hull"]
        r = _orow(spec, v, "whull-%s" % c, "%s within [min, max] of %s over the last %d rows, rows n>=%d of %d inputs; largest net excess at "
                  "%s (relative allowance %g x the violated bound, then absolute)" % (c, of, w0, w0, len(vin), where, spec["tol_window_hull"]),
                  0.0, worst if ok else nan, tol_, worst if ok else nan, res=None if ok else "ERROR")
        r["tgroup"] = ""
        rows.append(r)
    hc = [c for c in ad["hull"] if c in cols]
    if hc:
        worst, where = 0.0, ""
        for i in vin:
            rmax, rmin = np.maximum.accumulate(x[i]), np.minimum.accumulate(x[i])
            for c in hc:
                y = ov[c][i]
                e_ = np.maximum(y - rmax, rmin - y)
                if not np.all(np.isfinite(e_)):
                    worst, where = nan, "%s %s non-finite" % (c, i)
                    break
                m_ = float(np.max(e_))
                if m_ > worst or not where:
                    worst, where = max(worst, m_), "%s %s n=%d" % (c, i, int(np.argmax(e_)))
            if not math.isfinite(worst):
                break
        d = max(0.0, worst) if math.isfinite(worst) else nan
        rows.append(_arow(spec, v, "hull", "%s within the running [min x, max x], every row of %d inputs; largest excess at %s"
                          % ("/".join(hc), len(vin), where), 0.0, worst, "hull", None, d))
    if v.get("equivariance"):
        f0 = ad["eq_from"]
        for cp in ad["copies"]:
            if cp["base"] not in ad["eq_inputs"]:
                continue
            tr = ad["transforms"][cp["tid"]]
            for c in cols:
                b_, y = ov.get(c, {}).get(cp["base"]), ov.get(c, {}).get(cp["id"])
                cid = "equiv-%s-%s" % (cp["tid"], c) + ("" if len(ad["eq_inputs"]) == 1 else "-" + cp["base"])
                if b_ is None or y is None:
                    rows.append(_arow(spec, v, cid, "%s: no column" % c, 0.0, nan, "equivariance", c, nan, res="ERROR"))
                    continue
                lvl = c in ad["level_columns"]
                scl = c in ad.get("scale_columns", ())              # ATR: copy = |k| x base, the offset has no effect
                ref = tr["scale"] * b_[f0:] + tr["offset"] if lvl else (abs(tr["scale"]) * b_[f0:] if scl else b_[f0:])
                dev = np.abs(y[f0:] - ref)
                fin = bool(np.all(np.isfinite(dev)))
                k = int(np.argmax(dev)) if fin else 0
                d = float(dev[k]) if fin else nan
                rows.append(_arow(spec, v, cid, "%s %s vs %s %s, rows n>=%d (max at n=%d)" % (
                    c, cp["id"], ("%r x %s %s + %r" % (tr["scale"], c, cp["base"], tr["offset"]) if lvl else (
                        "%r x %s %s (scale role)" % (abs(tr["scale"]), c, cp["base"]) if scl else c)), "" if (lvl or scl) else cp["base"],
                    f0, f0 + k), float(ref[k]) if fin else nan, float(y[f0 + k]) if fin else nan, "equivariance", c, d))
    for c, i in ad["ramp_exact"].items():
        if c in cols and i in vin:
            dev = np.abs(ov[c][i] - x[i])
            fin = bool(np.all(np.isfinite(dev)))
            k = int(np.argmax(dev)) if fin else 0
            rows.append(_arow(spec, v, "exact-%s-%s" % (c, i), "%s %s must equal x on every row (row furthest from it: n=%d)" % (c, i, k),
                              float(x[i][k]), float(ov[c][i][k]), "ramp_exact", None, float(dev[k]) if fin else nan))
    for c, i in ad["ramp_lag"].items():
        if c in cols and i in vin:
            m_ = float(np.mean((x[i][-100:] - ov[c][i][-100:]) / spec["slope"]))
            e_ = v.get("ramp_lag")
            rows.append(_arow(spec, v, "ramp-lag-%s" % i, "%s %s: mean (x - y)/slope over the last 100 rows (bars) vs (1 - alpha)/alpha"
                              % (c, i), e_, m_, "lag", None, abs(m_ - e_) if e_ is not None else nan))
    for c in ad["flat"]:
        if c in cols and "flat" in vin:
            dev = np.abs(ov[c]["flat"] - spec["level"])
            rows.append(_arow(spec, v, "flat-%s" % c, "%s flat: must equal the level on every row" % c, spec["level"],
                              float(ov[c]["flat"][int(np.argmax(dev))]), "flat", None, float(np.max(dev))))
    for c, m_ in ad.get("known_value", {}).items():              # ATR: column == constant on rows >= the table's window
        if c not in cols:
            continue
        for i, val in m_.items():
            if i not in vin:
                continue
            w0 = v["window"]
            dev = np.abs(ov[c][i][w0:] - val)
            fin = bool(np.all(np.isfinite(dev)))
            k = int(np.argmax(dev)) if fin else 0
            rows.append(_arow(spec, v, "known-%s-%s" % (c, i), "%s %s must equal %r on every row n>=%d (row furthest from it: n=%d)"
                              % (c, i, val, w0, w0 + k), val, float(ov[c][i][w0 + k]) if fin else nan, "known_value", None,
                              float(dev[k]) if fin else nan))
    fi = ad.get("flat_info")
    if fi and v["role"] == "real" and "flat" in vin:
        f0 = fi["from_n"]
        per = {c: float(np.max(np.abs(ov[c]["flat"][f0:] - spec["level"]))) for c in fi["columns"] if c in cols}
        d = max(per.values()) if per else nan
        rows.append(_orow(spec, v, "info-flat", "flat, rows n>=%d: max |y - level| (%s) (INFO, D7 rule 6 / C-1)"
                          % (f0, ", ".join("%s %r" % kv for kv in per.items())), spec["level"], spec["level"] + d, nan, d,
                          res="INFO", role="info"))
    return rows


def conditioning_table(spec):
    """D7 rule 3, the pre-run classifier (deterministic): {table: {input: {column: value}}} and {table: {input: [INFO columns]}} for
    every expected table of a real variant (variant order). One numpy default_rng(seed); skip_draws draws of n_bars integers are
    consumed first; then for each table, for each input of [conditioning].order (base and band inputs), and then for each table, for each
    equivariance copy: reference.conditioning (draws perturbations x(1 + 2^-52 u), max |column change| over ALL rows). A band input
    is perturbed as x with High / Low = y +- h built from the perturbed y; a copy of a band input with h = k x h. A column is INFO on an
    input when its value exceeds [conditioning].bound (= trace tolerance / 10, S2)."""
    ad = spec["adaptive"]
    cd = ad["conditioning"]
    rng = np.random.default_rng(cd["seed"])
    for _ in range(cd["skip_draws"]):
        rng.integers(-1, 2, spec["n_bars"])
    x = make_inputs(spec)
    band = set(ad["band"])
    hoff = {i: (ad["band_half"] if i in band else None) for i in input_names(spec)}
    for c in ad["copies"]:
        hoff[c["id"]] = ad["transforms"][c["tid"]]["scale"] * ad["band_half"] if c["base"] in band else None
    cols = ad["columns"]
    vals = {t: {} for t in ad["real_tables"]}
    for seq in (cd["order"], [c["id"] for c in ad["copies"]]):
        for t in ad["real_tables"]:
            m = R.adaptive_article_model(ad["tables"][t]["article"])
            for i in seq:
                vals[t][i] = R.conditioning(m, x[i], cols, rng, cd["draws"], hoff[i])
    info = {t: {i: [c for c in cols if vals[t][i][c] > cd["bound"][c]] for i in vals[t]} for t in vals}
    return vals, {t: {i: l for i, l in info[t].items() if l} for t in info}


def conditioning_mismatches(spec, recomputed=None):
    """Differences between the spec's pre-registered INFO lists and the recomputed classification ([] = identical; any entry is a
    pre-run STOP). Tables of real variants only."""
    vals, info = recomputed or conditioning_table(spec)
    out = []
    for t in info:
        mine = {i: sorted(l) for i, l in spec["adaptive"]["tables"][t]["info"].items() if l}
        got = {i: sorted(l) for i, l in info[t].items()}
        if mine != got:
            out.append("%s: spec INFO %r, recomputed %r" % (t, mine, got))
    return out


def adaptive_shared_slots(spec, model):
    """[(variant id, input, instance parameter)] of every call of a superseded file, in the generator's ACTUAL call order: the variants
    whose [imp].must_pass model has the same shared type and instance list, in spec (= variant-major call) order, each on its
    variant_inputs. Only these calls touch the file statics."""
    out = []
    for v in spec["variants"]:
        mk = R.IMP_MODELS.get(spec["imp"]["must_pass"].get(v["id"], ""))
        m = mk() if mk else None
        if type(m) is type(model) and m[0] == model[0]:
            out += [(v["id"], i, m[0][m.index]) for i in variant_inputs(spec, v)]
    return out


def adaptive_shared_outputs(spec, model, xs, bars):
    """{(variant id, input): MamaOut / FramaOut} of the shared-state replay over adaptive_shared_slots."""
    slots = adaptive_shared_slots(spec, model)
    if isinstance(model, R.MamaShared):
        sims = R.simulate_mama_shared([(_pv(p[0]), _pv(p[1])) for _, _, p in slots], [xs[i] for _, i, _ in slots])
    elif isinstance(model, R.AtrShared):
        sims = R.simulate_atr_shared([p for _, _, p in slots], [xs[i] for _, i, _ in slots],
                                     [bars[i][0] for _, i, _ in slots], [bars[i][1] for _, i, _ in slots])
    else:
        sims = R.simulate_frama_shared([p for _, _, p in slots], [xs[i] for _, i, _ in slots],
                                       [bars[i][0] for _, i, _ in slots], [bars[i][1] for _, i, _ in slots])
    return {(s[0], s[1]): o for s, o in zip(slots, sims)}


def _pv(p):
    return p[0] / p[1]


def adaptive_imp_rows(spec, raw):
    """[imp] of a D7 spec: replay each listed variant's model on the x (and High / Low) columns EXPORTED by Zorro; residual per
    (input, column) over every row (n >= 0, D7 rule 2). Pairs the variant's expected table classifies as INFO (rule 3) are reported
    separately (row['info_detail'], trailer) and never decide PASS/FAIL; on the checked pairs the ratio residual / column tolerance
    (tolerances.imp, per-column overrides) decides: must_pass PASS iff every ratio <= 1, must_fail PASS iff some ratio > 1. The row
    reports the pair with the largest ratio. A shared (superseded) model replays all its calls in the generator's call order."""
    imp, p = spec["imp"], spec["id_prefix"]
    vmap = {v["id"]: v for v in spec["variants"]}
    names = input_names(spec)
    xs = {i: raw.cols["x_" + i] for i in names}
    bset = set(adaptive_bar_names(spec))
    bars = {i: ((raw.cols["xh_" + i], raw.cols["xl_" + i]) if i in bset else (xs[i], xs[i])) for i in names}
    cache, rows = {}, []
    for kind, table in (("pass", imp["must_pass"]), ("fail", imp["must_fail"])):
        for vid, mstr in table.items():
            v = vmap[vid]
            maker = R.IMP_MODELS.get(mstr)
            per, per_info = {}, {}
            if maker is not None:
                model = maker()
                if isinstance(model, (R.MamaShared, R.FramaShared, R.AtrShared)):
                    key = (type(model).__name__, model[0])
                    if key not in cache:
                        cache[key] = adaptive_shared_outputs(spec, model, xs, bars)
                    mo_of = lambda i, key=key: cache[key][(vid, i)]
                else:
                    mo_of = lambda i, model=model: adaptive_out(model, xs[i], *bars[i])
                info = {tuple(q) for q in v["info_pairs"]}
                for i in variant_inputs(spec, v):
                    mo = mo_of(i)
                    for c in adaptive_columns(spec, v):
                        d = float(np.max(np.abs(raw.cols["%s_%s_%s" % (c, vid, i)] - getattr(mo, c))))
                        (per_info if (i, c) in info else per)["%s:%s" % (i, c)] = d
            ratios = {k: d / col_tol(spec, "imp", k.split(":")[1]) for k, d in per.items()}
            if maker is None or not per or not all(math.isfinite(r_) for r_ in ratios.values()):
                res, worst, d, tol, ratio = "ERROR", "none", float("nan"), imp["tol"], float("nan")
            else:
                worst = max(ratios, key=ratios.get)
                d, tol, ratio = per[worst], col_tol(spec, "imp", worst.split(":")[1]), ratios[worst]
                res = ("PASS" if ratio <= 1 else "FAIL") if kind == "pass" else ("PASS" if ratio > 1 else "FAIL")
            rows.append(dict(check_id="%s-%s-imp-%s" % (p, vid, kind), indicator=spec["indicator"],
                             params="IMP must_%s: %s" % (kind, mstr), asset=spec["asset"],
                             input="replay residual n>=0, checked (input:column) pairs, worst ratio at %s (column tolerances: %s); "
                                   "%d INFO pairs reported in the trailer" % (worst, ", ".join(
                                       "%s %g" % (c, col_tol(spec, "imp", c)) for c in adaptive_columns(spec, v)), len(per_info)),
                             expected=0.0 if kind == "pass" else tol, actual=d, abs_diff=d, tolerance=tol, ratio=ratio,
                             result=res, role="imp", detail=per, info_detail=per_info))
    return rows


def adaptive_floor_quantities(spec):
    """(key, tolerance/10) of the D7 floor guard per real variant: every Zorro-vs-model kind (not bound / hull: structural), and a
    'kind:column' key per column override (e.g. trace:phase)."""
    out = []
    for q in spec["adaptive"]["kinds"]:
        if q in ("bound", "hull", "window_hull"):
            continue
        out.append((q, spec["tol_" + q] / 10))
        out += [("%s:%s" % (q, c), t / 10) for c, t in sorted(spec.get("tolcols_" + q, {}).items())]
    return out


def adaptive_trailer(spec, rows):
    """Trailer lines of a D7 spec: per IMP row the checked residuals and, separately, the INFO pairs; per real variant the
    Zorro-vs-model maxima per floor key; the floor guard message."""
    out = []
    for r in rows:
        if r["role"] == "imp":
            out.append("# IMP %s %s worst=%s tol=%g ratio=%.3e checked: %s" % (
                r["check_id"], r["result"], repr(float(r["actual"])), r["tolerance"], r["ratio"],
                " ".join("%s=%s" % (k, repr(d)) for k, d in r.get("detail", {}).items())))
            if r.get("info_detail"):
                out.append("# IMP_INFO %s (rule-3 INFO pairs, never PASS/FAIL): %s" % (
                    r["check_id"], " ".join("%s=%s" % (k, repr(d)) for k, d in r["info_detail"].items())))
    for v in spec["variants"]:
        if v["role"] != "real":
            continue
        pre = "%s-%s-" % (spec["id_prefix"], v["id"])
        imp = [r["actual"] for r in rows if r["role"] == "imp" and r["check_id"] == pre + "imp-pass"]
        fl = {r["check_id"][len(pre) + 6:]: r["actual"] for r in rows if r["role"] == "floor" and r["check_id"].startswith(pre + "floor-")}
        out.append("# O_IMP_RESIDUAL %s imp=%s %s (INFO)" % (v["id"], repr(float(imp[0])) if imp else "n/a",
                                                             " ".join("zorro_vs_model_%s=%.3e" % kv for kv in fl.items())))
    bad = sorted(r["check_id"] for r in rows if r["role"] == "floor" and r["result"] != "PASS")
    if bad:
        out.append("# FLOOR_GUARD FAIL: tolerance window invalid (item 7; not accepted until explained): " + ",".join(bad))
    return out


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


def fisher_shared_slots(spec, model):
    """[(variant id, input, L)] of every call of the superseded FisherTransform file, in the generator's ACTUAL call order: the
    variants whose [imp].must_pass model is a FisherShared with the same L list, in spec (= variant-major call) order, each on its
    variant_inputs. Only these calls touch the file statics ft_Value1 / ft_Fish."""
    out = []
    for v in spec["variants"]:
        mk = R.IMP_MODELS.get(spec["imp"]["must_pass"].get(v["id"], ""))
        m = mk() if mk else None
        if isinstance(m, R.FisherShared) and m.Ls == model.Ls:
            out += [(v["id"], i, m.Ls[m.index]) for i in variant_inputs(spec, v)]
    return out


def _imp_fisher(spec, raw, v, model, cache):
    """IMP replay of an FSH variant on the EXPORTED x, residual per input, rows >= warmup. Every exported output is compared; on the
    sines and their copies an output listed in [checks].trace_outputs is compared only on the rows the REPLAY's own gates let in
    (osc_mask); everything else (rng, trig, and every output on flat / ramp / rampdn: exact known answers there) absolutely. A
    FisherShared model replays the superseded file's shared statics over ALL its calls in the generator's call order
    (fisher_shared_slots). A non-finite value (everything gated out) is an ERROR upstream, never 0."""
    w, vid = spec["w"], v["id"]
    if isinstance(model, R.FisherShared):
        key = ("fisher", model.Ls)
        if key not in cache:
            slots = fisher_shared_slots(spec, model)
            sims = R.simulate_fisher_shared([s[2] for s in slots], [raw.cols["x_" + s[1]] for s in slots])
            cache[key] = {(s[0], s[1]): o for s, o in zip(slots, sims)}
        mo_of = lambda i: cache[key][(vid, i)]
    else:
        mo_of = lambda i: model_out(model, raw.cols["x_" + i])
    sines = set(sine_inputs(spec))
    to = spec["osc"].get("trace_outputs") or {}
    per = {}
    for i in variant_inputs(spec, v):
        mo = mo_of(i)
        d = 0.0
        for o in v["outputs"]:
            col = "%s_%s_%s" % (o, vid, i)
            if col not in raw.cols:
                continue
            z, arr = raw.cols[col][w:], getattr(mo, o)[w:]
            if i in sines and o in to:
                mask = osc_mask(spec, mo, input_amp(spec, i), to[o])
                dr = float(np.max(np.abs(z[mask] - arr[mask]))) if mask.any() else float("nan")
            else:
                dr = float(np.max(np.abs(z - arr)))
            d = float("nan") if not math.isfinite(dr) else max(d, dr)
            if not math.isfinite(d):
                break
        per[i] = d
    return per


def floor_quantities(spec):
    """(kind, tolerance/10) the floor guard checks per real variant: gain, lag (dc_gain 1 only), then the D4 kinds
    enabled by the spec. gain and lag first: H1 / SS2 / SS3 rows unchanged. A spec without a linear stage (FSH: no gain / lag
    tolerance) has no gain / lag rows. D7: per (kind, column-tolerance group), keys 'trace' / 'trace:phase' ..."""
    if spec.get("adaptive"):
        return adaptive_floor_quantities(spec)
    q = [("gain", spec["tol_gain"] / 10)] if spec.get("tol_gain") is not None else []
    if _has_lag(spec) and spec.get("tol_lag") is not None:
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
            if spec.get("adaptive"):                   # D7: key 'kind' or 'kind:column' (the column's own tolerance group)
                kq, _, grp = q.partition(":")
                ds = [r["abs_diff"] for r in rs if _kind(r["check_id"]) == kq and r.get("tgroup", "") == grp]
            else:
                ds = [r["abs_diff"] for r in rs if _kind(r["check_id"]) == q]
            a = max(ds) if ds else float("nan")
            fin = math.isfinite(a)
            out.append(dict(check_id="%sfloor-%s" % (pre, q.replace(":", "-")), indicator=spec["indicator"],
                            params=v["params"], asset=spec["asset"], input="max |Zorro - book| " + q,
                            expected=0.0, actual=a, abs_diff=a, tolerance=tol,
                            ratio=(a / tol) if (fin and tol) else float("nan"),      # FSH trigger: tolerance 0 (exact)
                            result=("ERROR" if not fin else ("PASS" if a <= tol else "FAIL")), role="floor"))
    return out


def evaluate(spec, raw):
    """Assumes validate() found nothing. Returns (rows, nc_report)."""
    x = make_inputs(spec)
    xe = {i: raw.cols["x_" + i] for i in input_names(spec)}          # EXPORTED inputs (start-up reference)
    rows = []
    bars = make_bars(spec, x) if spec.get("adaptive") else None
    for v in spec["variants"]:
        ov = variant_arrays(spec, raw, v)
        if spec.get("adaptive"):                               # MAF (D7)
            vr = adaptive_rows(spec, v, x, bars, ov)
        elif v.get("outputs") and spec.get("osc") and isinstance(spec["osc"]["linear"], (list, tuple)):
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
    if spec.get("adaptive"):
        return adaptive_trailer(spec, rows)
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
        if gains:                                          # FSH: no linear stage, no gain rows, no O_PEAK line
            out.append("# O_PEAK %s max_measured_gain=%r (INFO)" % (v["id"], max(gains)))
    for v in spec["variants"]:
        if v["role"] != "real":
            continue
        pre = "%s-%s-" % (p, v["id"])
        imp = [r["actual"] for r in rows if r["role"] == "imp" and r["check_id"] == pre + "imp-pass"]
        fl = {q: [r["actual"] for r in rows if r["check_id"] == pre + "floor-" + q][0]
              for q, _ in floor_quantities(spec)}
        txt = "# O_IMP_RESIDUAL %s imp=%s" % (v["id"], "%.3e" % imp[0] if imp else "n/a")
        if "gain" in fl:
            txt += " zorro_vs_book_gain_max=%.3e" % fl["gain"]
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
