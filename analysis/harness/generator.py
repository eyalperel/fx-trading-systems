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

RFX stage 1 (HARNESS_DESIGN D6, oscillator family), all opt-in, older specs regenerate byte-identical scripts:
  * variant `outputs = ["sum", "ms", "r"]`: the LAST name is the function's return value, the others are `var*`
    out-parameters passed after the integer params (`Y[k] = ReflexCore(S, 20, &Y[a], &Y[b])`); raw columns <output>_<id>_<input>;
  * [inputs.invariance] transforms: transformed copies of every sine (ids <tid><T>), called only by variants with
    `invariance = true`, written for the return output only;
  * [checks] trace_gate / bound / linear_output enable the trace, bound and invariance checks (checker.osc_rows).
MST stage 1 (MESAStochastic): output names roof / stoc / out (the return value is `r` or `out`); [checks].bound may be a two-sided
absolute pair [lo, hi] read from [checks].bound_output; variants may carry `startup_info = true` (INFO start-up row).
LRSI stage 1 (Laguerre RSI), all opt-in, older specs regenerate byte-identical scripts:
  * real-valued call parameters ([batch].real_params = true, opt-in): a `params` element may be a pair [n, d] (positive integers): the script builds it at run time,
    `var <p>_g<n>_<d> = n; <p>_g<n>_<d> = <p>_g<n>_<d> / d;` (gotchas 9d.1, 9d.8), and passes the variable;
  * output names l0 / l3 (linear) and den; [checks].linear_output may be a LIST (each linear output gets the v1 checks against its
    own table: variant key `expected_outputs = { l0 = "<table>", l3 = "<table>" }`);
  * [inputs].ramp_down: input `rampdn` (level - slope*n) after `ramp`;
  * [checks].ramp_exact = { ramp = 1.0, rampdn = 0.0 } (known answers of the normalised output, rows >= W) and
    [checks].startup_output = true (start-up rows < W of the normalised output vs the model, PASS/FAIL);
  * variant key `skip_inputs = [...]` (base inputs other than the sines): no call, no raw column, no check for those pairs;
  * [lint].no_static = [files]: the pre-run structural check that a file has no `static` token (comments excluded).
FSH stage 1 (Fisher Transform), all opt-in, older specs regenerate byte-identical scripts:
  * output names raw / v1 / rng / trig (five columns per call: FisherCore(S, Len, &raw, &v1, &rng, &trig) returns out);
  * [checks].linear_stage = false: the indicator has NO linear stage (F-7): no linear_output, no flat / gain / lag / phase tolerances
    or table keys (refused if present); expected tables carry only `article` and `source`;
  * [checks].trace_outputs = { <output> = ["range"] | ["range", "clamp"] }: trace replay on several outputs, per-output gates evaluated
    on the MODEL (range / amplitude >= trace_gate; min |pre-clamp v1 -/+ thr| >= [checks].clamp_gate); check ids trace-<output>-T<t>;
  * [checks].bounds = { <output> = [lo, hi] (absolute) | b (one-sided |y| <= b, relative allowance) }: one bound row per output;
  * [checks].ramp_exact_outputs = { <output> = { ramp = <number> | "model", rampdn = ... } }: ids exact-<output>-<input>;
  * [checks].trigger = true: new kind `trigger`, trig[n] == out[n-1] exactly for n >= 1 on every base input (Zorro-internal);
  * [checks].flat_zero = [outputs]: new kind `flat_zero`, every flat row of those outputs must be 0 (implementation known answer).
MAF stage 1 (HARNESS_DESIGN D7, adaptive smoothers: MAMA / FAMA, FRAMA), a SEPARATE path selected by [checks].adaptive = true
(validate_adaptive / to_checker_spec_adaptive / build_script_adaptive); older specs never enter it and regenerate byte-identical scripts:
  * bars inputs: [inputs].band_half = [n, d] and band_inputs = [base ids]: band copies <id>B with High = x + h, Low = x - h (built at run
    time); point inputs pass the same series as Price, High and Low (H = L = x). [checks].bars = true: calls pass (S, SH, SL);
  * [inputs.equivariance]: inputs = [sine ids] and transforms = [{id, scale = [n, d], offset = [n, d]}]: affine copies x' = k x + c (and
    H, L mapped the same way) of the listed inputs only, ids <tid><input without its leading 's'> (s40 -> sc40, s40B -> sc40B);
  * every output column is written for every input a variant is called on (copies included: equivariance needs all columns);
  * output names mama / fama / period / alpha / phase (MAMACore, returns mama) and out / dim / alpha (FRAMACore, returns out);
  * per-column tolerance overrides ([tolerances.<q>].columns = {column = value}); kinds trace (from row 1 = n >= 0, per (input, column)
    checked / INFO by the pre-registered conditioning classification of the expected table), bound (per column, from the expected
    table, relative allowance, optional first row), hull, equivariance, ramp_exact, lag, flat.

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

import reference as R

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DEFAULT_OUT = os.path.join(REPO, "strategies", "tests")

LABEL_RE = re.compile(r"^\s*\((a|b|c)\)")
IDFRAG_RE = re.compile(r"^[A-Za-z0-9_]+$")
DETECT_KINDS = ("flat", "gain", "lag", "phase", "resid", "startup", "trace", "bound", "invariance",
                "ramp_exact", "trigger", "flat_zero", "equivariance", "hull")   # checker._kind values (D4 adds three, D6 three, LRSI one,
#                                                                                  FSH two, MAF two)
OUTPUT_NAMES = ("sum", "ms", "r", "roof", "stoc", "out", "l0", "l3", "den",
                "raw", "v1", "rng", "trig")  # variant outputs (RFX, MST, LRSI: l0 / l3 / den / out; FSH: raw / v1 / rng / trig / out)
ADAPTIVE_COLUMNS = ("mama", "fama", "period", "alpha", "phase", "out", "dim", "tr", "atr")   # MAF (D7): MAMACore / FRAMACore; ATR: tr, atr
ADAPTIVE_RETURNS = ("mama", "out", "atr")
ADAPTIVE_KINDS = ("trace", "bound", "hull", "equivariance", "ramp_exact", "lag", "flat", "window_hull", "known_value")   # ATR adds two
BAR_ARGS = ("phl", "hlc")                    # order of the three series a bars call passes: (Price, High, Low) [default] or (High, Low, Close) [ATR]
TRACE_GATES = ("range", "clamp")             # FSH: per-output trace gates (range / amplitude; clamp distance of the pre-clamp v1)
LINEAR_ONLY_TOLS = ("flat", "gain", "lag", "phase", "resid")      # tolerances of the v1 checks (refused with linear_stage = false)
LINEAR_ONLY_KEYS = ("flat", "gains", "lag", "phases", "resid", "gain_alt", "phase_alt")   # expected-table keys of the v1 checks
RETURN_NAMES = ("r", "out")                  # the last output listed is the function's return value, one of these
LINEAR_NAMES = ("sum", "ms", "roof", "l0", "l3")   # outputs the v1 checks may read
SKIPPABLE = ("flat", "alt", "ramp", "rampdn")      # base inputs a variant may skip (never a sine: trace / start-up need them)
IMP_CORRECTION_FIELDS = ("list", "replaces", "model", "amendment", "source")   # [imp_corrections.<id>], all required
SEEDS = ("zero", "price")                    # output-history seed of a variant (reference.simulate); also 'pass<n>' (USE)


def seed_ok(s):
    """A variant / start-up seed: zero, price or pass<n> (n >= 1; USE stage 1, reference.simulate)."""
    return s in SEEDS or (isinstance(s, str) and R.pass_n(s) is not None and R.pass_n(s) >= 1)


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


def alternating_of(spec):
    """[inputs].alternating (RFF stage 1, decision 2A): adds the Nyquist input 'alt'. Default off (old specs unchanged)."""
    return spec["inputs"].get("alternating", False) is True


def copies_of(spec):
    """[inputs.invariance].transforms (D6 rule 4): [{id, level [n, d], amp [n, d]}], default none."""
    inv = spec["inputs"].get("invariance")
    return list(inv.get("transforms", [])) if isinstance(inv, dict) and isinstance(inv.get("transforms"), list) else []


def osc_of(spec):
    """True when [checks].trace_gate is present: the oscillator check set (trace / bound / invariance) is on."""
    chk = spec.get("checks", {})
    return isinstance(chk, dict) and chk.get("trace_gate") is not None


def nolin_of(spec):
    """True when the oscillator spec declares NO linear stage ([checks].linear_stage = false, FSH stage 1, F-7)."""
    chk = spec.get("checks", {})
    return osc_of(spec) and isinstance(chk, dict) and chk.get("linear_stage") is False


FISHER_CHECK_KEYS = ("linear_stage", "trace_outputs", "clamp_gate", "bounds", "ramp_exact_outputs", "trigger", "flat_zero")


def fisher_checked_outputs(chk):
    """Outputs a real variant must export under the FSH keys: trace_outputs, bounds, ramp_exact_outputs, flat_zero, and trig (+ out)
    for the trigger check. [] for every older spec."""
    out = []
    for k in ("trace_outputs", "bounds", "ramp_exact_outputs"):
        if isinstance(chk.get(k), dict):
            out += [o for o in chk[k] if o not in out]
    if isinstance(chk.get("flat_zero"), list):
        out += [o for o in chk["flat_zero"] if isinstance(o, str) and o not in out]
    if chk.get("trigger") is True:
        out += [o for o in ("trig", "out") if o not in out]
    return out


def _fisher_check_errors(spec, chk):
    """Validation of the FSH stage 1 [checks] keys (all optional). Returns [(code, message)]."""
    err = []
    to = chk.get("trace_outputs")
    if to is not None:
        if (not isinstance(to, dict) or not to or any(o not in OUTPUT_NAMES for o in to)
                or any(not isinstance(g, list) or not g or len(set(g)) != len(g) or any(x not in TRACE_GATES for x in g)
                       or "range" not in g for g in to.values())):
            err.append(("TRACE_OUTPUTS_BAD", "[checks].trace_outputs %r must map output names from %s to a gate list containing "
                        "'range' (and optionally 'clamp')" % (to, "/".join(OUTPUT_NAMES))))
    uses_clamp = isinstance(to, dict) and any(isinstance(g, list) and "clamp" in g for g in to.values())
    cg = chk.get("clamp_gate")
    if uses_clamp and (not _is_num(cg) or cg <= 0):
        err.append(("TRACE_OUTPUTS_BAD", "[checks].clamp_gate %r must be a positive number (a trace output uses the clamp gate)" % (cg,)))
    elif cg is not None and not uses_clamp:
        err.append(("TRACE_OUTPUTS_BAD", "[checks].clamp_gate given but no trace output uses the 'clamp' gate"))
    bs = chk.get("bounds")
    if bs is not None:
        ok = isinstance(bs, dict) and bool(bs)
        for o, b_ in (bs.items() if isinstance(bs, dict) else []):
            pair = isinstance(b_, list) and len(b_) == 2 and all(_is_num(i) for i in b_) and b_[0] < b_[1]
            if o not in OUTPUT_NAMES or not (pair or (_is_num(b_) and b_ > 0)):
                ok = False
        if not ok:
            err.append(("BOUNDS_BAD", "[checks].bounds %r must map output names to [lo, hi] (lo < hi, absolute) or a positive "
                        "number b (|y| <= b, relative allowance)" % (bs,)))
    reo = chk.get("ramp_exact_outputs")
    if reo is not None:
        want = ["ramp"] + (["rampdn"] if ramp_down_of(spec) else [])
        ok = isinstance(reo, dict) and bool(reo)
        for o, tab in (reo.items() if isinstance(reo, dict) else []):
            if (o not in OUTPUT_NAMES or not isinstance(tab, dict) or not tab or any(i not in want for i in tab)
                    or not all(_is_num(e) or e == "model" for e in tab.values())):
                ok = False
        if not ok:
            err.append(("RAMP_EXACT_BAD", "[checks].ramp_exact_outputs %r must map output names to {input from %s: number or "
                        "\"model\"}" % (reo, want)))
        if "ramp_exact" in chk:
            err.append(("RAMP_EXACT_BAD", "[checks].ramp_exact and ramp_exact_outputs are exclusive"))
    if "trigger" in chk and not isinstance(chk["trigger"], bool):
        err.append(("TRIGGER_BAD", "[checks].trigger %r must be true or false" % (chk["trigger"],)))
    fz = chk.get("flat_zero")
    if fz is not None and (not isinstance(fz, list) or not fz or len(set(fz)) != len(fz) or any(o not in OUTPUT_NAMES for o in fz)):
        err.append(("FLAT_ZERO_BAD", "[checks].flat_zero %r must be a non-empty list of distinct output names" % (fz,)))
    return err


def ramp_down_of(spec):
    """[inputs].ramp_down (LRSI stage 1): adds the falling ramp 'rampdn' (level - slope*n) after 'ramp'. Default off."""
    return spec["inputs"].get("ramp_down", False) is True


def input_ids(spec):
    """flat, sines, [alt], ramp, [rampdn], then the invariance copies. alt sits after the sines and before ramp, rampdn right
    after ramp, so without the flags the ids and slots are exactly the old ones."""
    return (["flat"] + ["s%d" % t for t in spec["inputs"]["sine_periods"]]
            + (["alt"] if alternating_of(spec) else []) + ["ramp"] + (["rampdn"] if ramp_down_of(spec) else [])
            + ["%s%d" % (tr["id"], t) for tr in copies_of(spec) for t in spec["inputs"]["sine_periods"]])


def linear_outputs_of(spec):
    """[checks].linear_output as a list ([] without it). A string is the one-output form of RFX / MST."""
    lo = spec.get("checks", {}).get("linear_output") if isinstance(spec.get("checks"), dict) else None
    if lo is None:
        return []
    return list(lo) if isinstance(lo, list) else [lo]


def multi_linear(spec):
    """True when [checks].linear_output is a list (LRSI: l0 and l3, each against its own table; check ids carry -<output>)."""
    return isinstance(spec.get("checks", {}).get("linear_output"), list)


def call_params(v):
    """Arguments of a variant's call after the input series: `params = [48, 10]` (RFF stage 1, decision 1A) or `param = 48` (old
    form); an element may be a pair [n, d] (LRSI: a real value built at run time). None if neither is given."""
    if "params" in v:
        return v["params"]
    return [v["param"]] if "param" in v else None


def _is_pair(p):
    return (isinstance(p, list) and len(p) == 2
            and all(isinstance(i, int) and not isinstance(i, bool) and i > 0 for i in p))


def real_param_name(prefix, pair):
    """Light-C name of a real-valued parameter n/d: <prefix>_g<n>_<d> (LRSI stage 1)."""
    return "%s_g%d_%d" % (prefix, pair[0], pair[1])


def real_params(spec):
    """Distinct [n, d] pairs used by any variant, in first-use order."""
    out = []
    for v in spec["variants"]:
        for p in call_params(v) or []:
            if _is_pair(p) and p not in out:
                out.append(p)
    return out


def skips_of(v):
    """skip_inputs of a variant (LRSI stage 1, Amendment 1 A): base input ids not called. Default none."""
    s = v.get("skip_inputs")
    return list(s) if isinstance(s, list) else []


def includes(spec):
    """[zorro].include as a list of paths (dependency order, gotchas 5.3); a plain string is a one-element list."""
    inc = spec["zorro"]["include"]
    return [inc] if isinstance(inc, str) else list(inc)


def _frac(pair):
    return pair[0] / pair[1]


def _has_label(s):
    return isinstance(s, str) and LABEL_RE.match(s) is not None


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def dc_gain_of(spec):
    """[checks].dc_gain, default 1 (a spec without [checks] behaves exactly as H1 / SS2 / SS3)."""
    return spec.get("checks", {}).get("dc_gain", 1.0)


def phase_periods(table):
    """expected.<P>.phases as {int period: radians}; TOML keys arrive as strings, fixtures may use ints."""
    out = {}
    for k, v in table.get("phases", {}).items():
        try:
            out[int(k)] = v
        except (TypeError, ValueError):
            out[k] = v
    return out


def validate_spec(spec):
    """Returns (errors, infos). errors: list of (code, message), a non-empty list means the spec
    is refused. infos: INFO lines (D2 floor and per-control margin), never a refusal."""
    if adaptive_of(spec):                          # MAF (D7): its own validation; older specs never reach it
        return validate_adaptive(spec)
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
    if "real_params" in b and not isinstance(b["real_params"], bool):
        err.append(("PARAMS_BAD", "[batch].real_params %r must be true or false" % (b["real_params"],)))
    if "alternating" in spec["inputs"] and not isinstance(spec["inputs"]["alternating"], bool):
        err.append(("ALT_BAD", "[inputs].alternating %r must be true or false" % (spec["inputs"]["alternating"],)))
    alt = alternating_of(spec)
    if "ramp_down" in spec["inputs"] and not isinstance(spec["inputs"]["ramp_down"], bool):
        err.append(("RAMPDN_BAD", "[inputs].ramp_down %r must be true or false" % (spec["inputs"]["ramp_down"],)))
    inc = spec["zorro"].get("include")
    if not (isinstance(inc, str) and inc) and not (isinstance(inc, list) and inc
                                                   and all(isinstance(i, str) and i for i in inc)):
        err.append(("INCLUDE_BAD", "[zorro].include %r must be a path or a non-empty list of paths" % (inc,)))
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
    chk = spec.get("checks", {})
    if not isinstance(chk, dict):
        err.append(("CHECKS_BAD", "[checks] must be a table"))
        chk = {}
    dc = chk.get("dc_gain", 1.0)
    if not _is_num(dc):
        err.append(("CHECKS_BAD", "[checks].dc_gain %r is not a number" % (dc,)))
        dc = 1.0
    gate = chk.get("phase_gate")
    if gate is not None and (not _is_num(gate) or gate <= 0):
        err.append(("CHECKS_BAD", "[checks].phase_gate %r must be a positive number" % (gate,)))
    sin = chk.get("startup_inputs")
    if sin is not None:
        ids_ok = input_ids(spec)
        if not isinstance(sin, list) or not sin or any(i not in ids_ok for i in sin):
            err.append(("STARTUP_BAD", "[checks].startup_inputs %r: need a non-empty list of %s" % (sin, ids_ok)))
    if "startup_seed" in chk and not seed_ok(chk["startup_seed"]):
        err.append(("STARTUP_BAD", "[checks].startup_seed %r must be one of %s or pass<n>"
                    % (chk["startup_seed"], "/".join(SEEDS))))
    has_lag = dc == 1
    any_phases = any(phase_periods(t) for t in spec["expected"].values() if isinstance(t, dict))
    # D6: oscillator check set (trace / bound / invariance), on when [checks].trace_gate is present
    osc = osc_of(spec)
    transforms = copies_of(spec)
    inv = spec["inputs"].get("invariance")
    if inv is not None:
        tl = inv.get("transforms") if isinstance(inv, dict) else None
        if not osc:
            err.append(("INVARIANCE_BAD", "[inputs.invariance] needs [checks].trace_gate (the oscillator check set)"))
        if not isinstance(tl, list) or not tl:
            err.append(("INVARIANCE_BAD", "[inputs.invariance] needs a non-empty transforms list"))
        else:
            tids = set()
            for tr in tl:
                tid = tr.get("id") if isinstance(tr, dict) else None
                if (not isinstance(tid, str) or not re.fullmatch(r"[A-Za-z_]+", tid) or tid in ("s", "flat", "alt", "ramp")
                        or tid in tids):
                    err.append(("INVARIANCE_BAD", "transform id %r must be unique letters, not s/flat/alt/ramp" % (tid,)))
                    continue
                tids.add(tid)
                for k in ("level", "amp"):
                    pr = tr.get(k)
                    if (not isinstance(pr, list) or len(pr) != 2 or not all(isinstance(i, int) and not isinstance(i, bool)
                                                                            and i > 0 for i in pr)):
                        err.append(("INVARIANCE_BAD", "transform %s: %s %r must be [numerator, denominator], positive integers"
                                    % (tid, k, pr)))
    nolin = nolin_of(spec)
    if osc:
        tg, bd, lo = chk.get("trace_gate"), chk.get("bound"), chk.get("linear_output")
        if not _is_num(tg) or tg <= 0:
            err.append(("OSC_BAD", "[checks].trace_gate %r must be a positive number" % (tg,)))
        if "linear_stage" in chk and not isinstance(chk["linear_stage"], bool):
            err.append(("LINEAR_STAGE_BAD", "[checks].linear_stage %r must be true or false" % (chk["linear_stage"],)))
        err.extend(_fisher_check_errors(spec, chk))     # FSH stage 1 keys (trace_outputs, bounds, ramp_exact_outputs, ...)
        if "bounds" in chk:                              # FSH: one bound per output (validated above); `bound` must be absent
            if "bound" in chk or "bound_output" in chk:
                err.append(("OSC_BAD", "[checks].bounds and [checks].bound / bound_output are exclusive"))
        elif isinstance(bd, list):                       # MST: two-sided absolute bound [lo, hi]
            if len(bd) != 2 or not all(_is_num(b_) for b_ in bd) or not bd[0] < bd[1]:
                err.append(("OSC_BAD", "[checks].bound %r must be a positive number or a pair [lo, hi] with lo < hi" % (bd,)))
            if chk.get("bound_output") not in OUTPUT_NAMES or chk.get("bound_output") in LINEAR_NAMES:
                err.append(("OSC_BAD", "[checks].bound_output %r must name a non-linear output (a two-sided bound is read from it)"
                            % (chk.get("bound_output"),)))
        elif not _is_num(bd) or bd <= 0:
            err.append(("OSC_BAD", "[checks].bound %r must be a positive number or a pair [lo, hi]" % (bd,)))
        elif "bound_output" in chk:
            err.append(("OSC_BAD", "[checks].bound_output is only valid with a two-sided bound [lo, hi]"))
        if nolin:                                        # FSH (F-7): no linear stage, so no linear output and no v1 checks
            if "linear_output" in chk:
                err.append(("OSC_BAD", "[checks].linear_output given with [checks].linear_stage = false"))
        elif isinstance(lo, list):                       # LRSI: several linear outputs, each with its own table
            if not lo or len(set(lo)) != len(lo) or any(o not in LINEAR_NAMES for o in lo):
                err.append(("OSC_BAD", "[checks].linear_output %r must be a non-empty list of distinct names from %s"
                            % (lo, "/".join(LINEAR_NAMES))))
        elif lo not in LINEAR_NAMES:
            err.append(("OSC_BAD", "[checks].linear_output %r must be one of %s (the output the v1 checks read)"
                        % (lo, "/".join(LINEAR_NAMES))))
        rex = chk.get("ramp_exact")
        if rex is not None:
            want = ["ramp"] + (["rampdn"] if ramp_down_of(spec) else [])
            if (not isinstance(rex, dict) or not rex or any(k not in want for k in rex)
                    or not all(_is_num(v_) for v_ in rex.values())):
                err.append(("RAMP_EXACT_BAD", "[checks].ramp_exact %r must map inputs from %s to a number" % (rex, want)))
        so = chk.get("startup_output")
        if so is not None and not isinstance(so, bool):
            err.append(("OSC_BAD", "[checks].startup_output %r must be true or false" % (so,)))
    elif ("bound" in chk or "linear_output" in chk or "bound_output" in chk or "ramp_exact" in chk
          or "startup_output" in chk):
        err.append(("OSC_BAD", "[checks].bound / linear_output / bound_output / ramp_exact / startup_output without "
                               "[checks].trace_gate"))
    elif any(k in chk for k in FISHER_CHECK_KEYS):
        err.append(("OSC_BAD", "[checks].%s without [checks].trace_gate" % "/".join(k for k in FISHER_CHECK_KEYS if k in chk)))
    osu = osc and chk.get("startup_output") is True               # start-up of the normalised output, PASS/FAIL
    orex = osc and ((isinstance(chk.get("ramp_exact"), dict) and bool(chk.get("ramp_exact")))
                    or (isinstance(chk.get("ramp_exact_outputs"), dict) and bool(chk.get("ramp_exact_outputs"))))
    otrig = osc and chk.get("trigger") is True                    # FSH: trig[n] == out[n-1]
    ofz = osc and isinstance(chk.get("flat_zero"), list) and bool(chk.get("flat_zero"))
    need_tol = ["flat", "gain", "x"] + (["lag"] if has_lag else []) \
        + (["phase"] if any_phases or alt else []) \
        + (["resid"] if not has_lag else []) + (["startup"] if sin or osu else []) \
        + (["trace", "bound"] + (["invariance"] if transforms else []) if osc else []) \
        + (["ramp_exact"] if orex else []) + (["trigger"] if otrig else []) + (["flat_zero"] if ofz else [])
    if nolin:                                                     # FSH (F-7): the v1 tolerances do not apply, and are refused
        need_tol = [q for q in need_tol if q not in LINEAR_ONLY_TOLS]
        for q in LINEAR_ONLY_TOLS:
            if q in spec["tolerances"]:
                err.append(("LINEAR_NOT_APPLICABLE", "[tolerances.%s] given with [checks].linear_stage = false (no v1 checks)" % q))
    for q in need_tol:
        t = spec["tolerances"].get(q)
        if not isinstance(t, dict) or "value" not in t:
            err.append(("STRUCT", "[tolerances.%s] missing or without value" % q))
        elif not _has_label(t.get("source")):
            err.append(("SOURCE_MISSING", "tolerance %s has no (a)/(b)/(c) source label" % q))
    for name, t in spec["expected"].items():
        if not _has_label(t.get("source")):
            err.append(("SOURCE_MISSING", "expected table %s has no (a)/(b)/(c) source label" % name))
        if nolin:                                                 # FSH: the table names only the article model (trace replay)
            for k in LINEAR_ONLY_KEYS:
                if k in t:
                    err.append(("LINEAR_NOT_APPLICABLE", "expected table %s: %s given with [checks].linear_stage = false" % (name, k)))
            if not isinstance(t.get("article"), str) or R.osc_article_model(t.get("article")) is None:
                err.append(("ARTICLE_MODEL", "expected table %s: article = %r is not a model in reference.osc_article_model"
                            % (name, t.get("article"))))
            continue
        if len(t.get("gains", [])) != len(ts):
            err.append(("STRUCT", "expected table %s: %d gains for %d sine periods"
                        % (name, len(t.get("gains", [])), len(ts))))
        for k in ("flat", "lag"):
            if k == "lag" and not has_lag:
                if "lag" in t:
                    err.append(("LAG_NOT_APPLICABLE", "expected table %s: lag given but [checks].dc_gain is %g "
                                "(ramp lag only at DC gain 1, D4 rule 1)" % (name, dc)))
                continue
            if not isinstance(t.get(k), (int, float)):
                err.append(("STRUCT", "expected table %s: %s missing" % (name, k)))
        if has_lag:
            if "resid" in t:
                err.append(("RESID_NOT_APPLICABLE", "expected table %s: resid given at dc_gain 1" % name))
        elif not _is_num(t.get("resid")):
            err.append(("STRUCT", "expected table %s: resid missing (required at dc_gain != 1, D4 rule 4)" % name))
        ph = phase_periods(t)
        if ph and gate is None:
            err.append(("PHASE_GATE_MISSING", "expected table %s lists phases but [checks].phase_gate is missing "
                        "(D4 rule 3: the spec pre-registers the gate)" % name))
        for T, val in ph.items():
            if T not in ts or not _is_num(val) or not (-math.pi < val <= math.pi):
                err.append(("PHASE_BAD", "expected table %s: phase for period %r = %r (period must be one of the "
                            "sine periods, value a number in (-pi, pi])" % (name, T, val)))
            elif gate is not None and _is_num(gate) and len(t.get("gains", [])) == len(ts):
                g = t["gains"][ts.index(T)]
                if g < gate:
                    err.append(("PHASE_GATE", "expected table %s: phase listed at T=%d where the reference gain "
                                "%.4g < phase_gate %g (phase undefined near gain 0)" % (name, T, g, gate)))
        if alt:
            ga, pa = t.get("gain_alt"), t.get("phase_alt")
            if not _is_num(ga):
                err.append(("STRUCT", "expected table %s: gain_alt missing ([inputs].alternating is on)" % name))
            elif gate is None:
                err.append(("PHASE_GATE_MISSING", "expected table %s: [inputs].alternating needs "
                            "[checks].phase_gate (the alt phase is gated)" % name))
            elif ga >= gate and not _is_num(pa):
                err.append(("ALT_PHASE_MISSING", "expected table %s: gain_alt %.4g >= phase_gate %g but phase_alt is "
                            "missing (the alt phase is checked wherever the gain reaches the gate)" % (name, ga, gate)))
            elif ga < gate and pa is not None:
                err.append(("PHASE_GATE", "expected table %s: phase_alt listed where gain_alt %.4g < phase_gate %g "
                            "(the alt phase is written as SKIP there)" % (name, ga, gate)))
            elif pa is not None and not (-math.pi < pa <= math.pi):
                err.append(("PHASE_BAD", "expected table %s: phase_alt %r not in (-pi, pi]" % (name, pa)))
        elif "gain_alt" in t or "phase_alt" in t:
            err.append(("ALT_NOT_ENABLED", "expected table %s lists gain_alt / phase_alt but [inputs].alternating "
                        "is not true" % name))
        if sin:
            if not isinstance(t.get("article"), str) or R.article_model(t.get("article")) is None:
                err.append(("ARTICLE_MODEL", "expected table %s: article = %r is not a model in "
                            "reference.article_model (needed by the start-up check)" % (name, t.get("article"))))
        if osc and (not isinstance(t.get("article"), str) or R.osc_article_model(t.get("article")) is None):
            err.append(("ARTICLE_MODEL", "expected table %s: article = %r is not a model in "
                        "reference.osc_article_model (reflex_article / mesa_article / lrsi_article; needed by the trace check)"
                        % (name, t.get("article"))))

    # variants
    roles = [v.get("role") for v in spec["variants"]]
    for v in spec["variants"]:
        vid = v.get("id")
        if v.get("role") not in ("real", "neg_control", "info"):
            err.append(("STRUCT", "variant %s: role must be real, neg_control or info" % vid))
        if v.get("expected") not in spec["expected"]:
            err.append(("STRUCT", "variant %s: expected table %r not defined" % (vid, v.get("expected"))))
        if "seed" in v and not seed_ok(v["seed"]):
            err.append(("SEED_BAD", "variant %s: seed %r must be one of %s or pass<n>" % (vid, v["seed"], "/".join(SEEDS))))
        if "params" in v and "param" in v:
            err.append(("PARAMS_BAD", "variant %s: give param or params, not both" % vid))
        elif "params" in v:
            pl = v["params"]
            rp = b.get("real_params") is True            # LRSI: [n, d] pairs only in a spec that opts in (older specs refuse them)
            if (not isinstance(pl, list) or not pl
                    or not all((isinstance(i, int) and not isinstance(i, bool)) or (rp and _is_pair(i)) for i in pl)):
                err.append(("PARAMS_BAD", "variant %s: params %r must be a non-empty list of integers%s" % (
                    vid, pl, " or [n, d] pairs of positive integers (a real value built at run time)" if rp
                    else " ([n, d] pairs need [batch].real_params = true)")))
        elif not isinstance(v.get("param"), int):
            err.append(("STRUCT", "variant %s: param must be an integer" % vid))
        if osc:
            outs = v.get("outputs")
            lins = linear_outputs_of(spec)
            if (not isinstance(outs, list) or not outs or any(o not in OUTPUT_NAMES for o in outs)
                    or len(set(outs)) != len(outs) or outs[-1] not in RETURN_NAMES
                    or any(o in RETURN_NAMES for o in outs[:-1])):
                err.append(("OUTPUTS_BAD", "variant %s: outputs %r must be a list of unique names from %s ending in %s "
                            "(the return value, once)" % (vid, outs, "/".join(OUTPUT_NAMES), " or ".join(RETURN_NAMES))))
            elif v.get("role") == "real" and any(o not in outs for o in lins):
                err.append(("OUTPUTS_BAD", "variant %s: a real variant must export the linear output %r"
                            % (vid, spec["checks"].get("linear_output"))))
            elif v.get("role") == "real" and any(o not in outs for o in fisher_checked_outputs(chk)):
                err.append(("OUTPUTS_BAD", "variant %s: a real variant must export every checked output %s"
                            % (vid, fisher_checked_outputs(chk))))
            elif multi_linear(spec):                     # LRSI: one expected table per exported linear output
                eo = v.get("expected_outputs")
                mine = [o for o in outs if o in lins]
                if mine and (not isinstance(eo, dict) or sorted(eo) != sorted(mine)
                             or any(eo[o] not in spec["expected"] for o in mine)):
                    err.append(("EXPECTED_OUTPUTS_BAD", "variant %s: expected_outputs %r must name a defined expected table for "
                                "each exported linear output %s" % (vid, eo, mine)))
                elif not mine and "expected_outputs" in v:
                    err.append(("EXPECTED_OUTPUTS_BAD", "variant %s: expected_outputs without a linear output" % vid))
            sk = v.get("skip_inputs")
            if sk is not None:
                ok_ids = [i for i in SKIPPABLE if i in input_ids(spec)]
                if (not isinstance(sk, list) or not sk or len(set(sk)) != len(sk)
                        or any(i not in ok_ids for i in sk)):
                    err.append(("SKIP_BAD", "variant %s: skip_inputs %r must be a non-empty list of distinct ids from %s "
                                "(never a sine: trace and start-up need them)" % (vid, sk, ok_ids)))
                elif isinstance(outs, list) and any(o in lins for o in outs):
                    err.append(("SKIP_BAD", "variant %s: skip_inputs on a variant that exports a linear output (its v1 checks "
                                "need every base input)" % vid))
            if "invariance" in v and not isinstance(v["invariance"], bool):
                err.append(("INVARIANCE_BAD", "variant %s: invariance %r must be true or false" % (vid, v["invariance"])))
            if "startup_info" in v and not isinstance(v["startup_info"], bool):
                err.append(("OSC_BAD", "variant %s: startup_info %r must be true or false" % (vid, v["startup_info"])))
            if v.get("invariance") is True and not transforms:
                err.append(("INVARIANCE_BAD", "variant %s: invariance = true but [inputs.invariance] is missing" % vid))
        elif "outputs" in v or "invariance" in v or "startup_info" in v:
            err.append(("OSC_BAD", "variant %s: outputs / invariance / startup_info without [checks].trace_gate" % vid))
        if "skip_inputs" in v and not osc:
            err.append(("SKIP_BAD", "variant %s: skip_inputs without [checks].trace_gate" % vid))
        if "expected_outputs" in v and not multi_linear(spec):
            err.append(("EXPECTED_OUTPUTS_BAD", "variant %s: expected_outputs needs [checks].linear_output as a list" % vid))
        if v.get("kind") == "inline":
            fn, body = v.get("function"), v.get("body")
            if not fn or not isinstance(body, str) or not re.search(r"\b%s\s*\(" % re.escape(fn), body):
                err.append(("STRUCT", "variant %s: inline needs function and a body defining it" % vid))
        elif v.get("kind") != "param":
            err.append(("STRUCT", "variant %s: kind must be param or inline" % vid))
        err.extend(_lint_allow_errors(v))
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
    # Amendment 1: [detect] (G1) and [ox] (G2) sections
    ctrl = [v.get("id") for v in spec["variants"] if v.get("role") == "neg_control"]
    det = spec.get("detect")
    if det is not None:
        req = det.get("required")
        if not isinstance(req, dict):
            err.append(("DETECT_MISSING", "[detect] without a [detect.required] table"))
        else:
            for vid, kinds in req.items():
                if vid not in ctrl:
                    err.append(("DETECT_UNKNOWN_ID", "[detect.required] key %r is not a neg_control variant id"
                                % vid))
                applicable = ([] if nolin else ["flat", "gain"] + (["lag"] if has_lag else ["resid"])
                              + (["phase"] if any_phases else [])) + (["startup"] if sin or osu else []) \
                    + (["trace", "bound"] + (["invariance"] if transforms else []) if osc else []) \
                    + (["ramp_exact"] if orex else []) + (["trigger"] if otrig else []) + (["flat_zero"] if ofz else [])
                if (not isinstance(kinds, list) or not kinds
                        or any(k not in DETECT_KINDS or k not in applicable for k in kinds)):
                    err.append(("DETECT_BAD_KIND", "[detect.required] %s = %r: need a non-empty list of kinds the "
                                "spec actually checks (%s)" % (vid, kinds, "/".join(applicable))))
            for vid in ctrl:
                if vid not in req:
                    err.append(("DETECT_MISSING", "neg_control %s has no entry in [detect.required]" % vid))
    ox = spec.get("ox")
    if ox is not None:
        for k in ("reference_raw", "reference_sha256"):
            if not isinstance(ox.get(k), str) or not ox.get(k):
                err.append(("OX_INCOMPLETE", "[ox] missing %s" % k))
        sh = ox.get("reference_sha256")
        if isinstance(sh, str) and sh and not re.fullmatch(r"[0-9a-f]{64}", sh):
            err.append(("OX_INCOMPLETE", "[ox] reference_sha256 is not 64 lowercase hex digits"))
    # Amendment 2: [effect_corrections.<id>] supersedes single quantities of [variants.effect] in the
    # INFO margin lines (reporting only; the verdict never reads these)
    corr = spec.get("effect_corrections", {})
    for vid, c in corr.items():
        if vid not in ctrl:
            err.append(("EFFECT_CORRECTION_UNKNOWN_ID",
                        "[effect_corrections.%s]: %r is not a neg_control variant id" % (vid, vid)))
            continue
        qs = [q for q in c if q != "source"]
        bad = [q for q in qs if q not in DETECT_KINDS or isinstance(c[q], bool)
               or not isinstance(c[q], (int, float))]
        if not qs or bad:
            err.append(("EFFECT_CORRECTION_BAD", "[effect_corrections.%s]: need >= 1 numeric quantity in %s, "
                        "got %s" % (vid, "/".join(DETECT_KINDS), bad if bad else "none")))
        if not _has_label(c.get("source")):
            err.append(("EFFECT_CORRECTION_BAD", "[effect_corrections.%s] has no (a)/(b)/(c) source label"
                        % vid))
    # SS3: `rule` key of [[literal_replacements]], [corrected_code], [imp] + [tolerances.imp]
    for r in spec.get("literal_replacements", []):
        if "rule" in r and (not isinstance(r["rule"], str) or not r["rule"].strip()):
            err.append(("LITERAL_INCOMPLETE", "literal replacement %r: rule must be a non-empty string"
                        % r.get("literal")))
    lt = spec.get("lint")
    if lt is not None:
        ns = lt.get("no_static") if isinstance(lt, dict) else None
        if not isinstance(ns, list) or not ns or not all(isinstance(p, str) and p for p in ns):
            err.append(("LINT_SECTION_BAD", "[lint].no_static %r must be a non-empty list of repo-relative paths" % (ns,)))
        elif not _has_label(lt.get("source")):
            err.append(("SOURCE_MISSING", "[lint] has no (a)/(b)/(c) source label"))
    cc = spec.get("corrected_code")
    if cc is not None:
        for k in ("file", "function", "lines"):
            if not isinstance(cc.get(k), str) or not cc.get(k).strip():
                err.append(("CORRECTED_CODE_BAD", "[corrected_code] missing or empty %s" % k))
    imp = spec.get("imp")
    if imp is not None:
        ti = spec["tolerances"].get("imp")
        if not isinstance(ti, dict) or isinstance(ti.get("value"), bool) \
                or not isinstance(ti.get("value"), (int, float)) or ti["value"] <= 0:
            err.append(("IMP_TOL_MISSING", "[imp] needs [tolerances.imp] with a positive numeric value"))
        elif not _has_label(ti.get("source")):
            err.append(("SOURCE_MISSING", "tolerance imp has no (a)/(b)/(c) source label"))
        vids = [v.get("id") for v in spec["variants"]]
        n_listed = 0
        for lst in ("must_pass", "must_fail"):
            tab = imp.get(lst)
            if not isinstance(tab, dict):
                err.append(("IMP_BAD", "[imp].%s must be a table {variant id = model}" % lst))
                continue
            for vid, model in tab.items():
                n_listed += 1
                if vid not in vids:
                    err.append(("IMP_UNKNOWN_ID", "[imp].%s key %r is not a variant id" % (lst, vid)))
                if model not in R.IMP_MODELS:
                    err.append(("IMP_UNKNOWN_MODEL", "[imp].%s %s = %r is not in the model registry "
                                "(reference.IMP_MODELS)" % (lst, vid, model)))
        if not n_listed:
            err.append(("IMP_BAD", "[imp] lists no variant"))
    # Amendment 2 mechanism: [imp_corrections.<id>] supersedes ONE pre-registered [imp] model string; [imp] itself
    # stays as the record (precedent: [effect_corrections]). One INFO line per correction, appended after the margins.
    corr_info = []
    ic = spec.get("imp_corrections")
    if ic is not None:
        imp_ok = isinstance(imp, dict) and all(isinstance(imp.get(k), dict) for k in ("must_pass", "must_fail"))
        if not isinstance(ic, dict) or not all(isinstance(c, dict) for c in ic.values()):
            err.append(("IMP_CORRECTION_BAD", "[imp_corrections] must be a table of tables, one per variant id"))
        elif not imp_ok:
            err.append(("IMP_CORRECTION_BAD", "[imp_corrections] needs an [imp] section with must_pass and "
                        "must_fail tables"))
        else:
            for vid, c in ic.items():
                where = "[imp_corrections.%s]" % vid
                miss = [k for k in IMP_CORRECTION_FIELDS if k not in c]
                extra = [k for k in c if k not in IMP_CORRECTION_FIELDS]
                if miss or extra:
                    err.append(("IMP_CORRECTION_BAD", "%s: missing %s, unexpected %s (fields: %s)"
                                % (where, miss or "none", extra or "none", "/".join(IMP_CORRECTION_FIELDS))))
                    continue
                bad = []
                if c["list"] not in ("must_pass", "must_fail"):
                    bad.append("list must be must_pass or must_fail, got %r" % (c["list"],))
                for k in ("replaces", "model", "amendment"):
                    if not isinstance(c[k], str) or not c[k].strip():
                        bad.append("%s must be a non-empty string" % k)
                if not _has_label(c["source"]):
                    bad.append("source has no (a)/(b)/(c) label")
                if bad:
                    err.append(("IMP_CORRECTION_BAD", "%s: %s" % (where, "; ".join(bad))))
                    continue
                tab = imp[c["list"]]
                if vid not in tab:
                    err.append(("IMP_CORRECTION_UNKNOWN_ID", "%s: %r is not a key of [imp].%s"
                                % (where, vid, c["list"])))
                    continue
                if tab[vid] != c["replaces"]:
                    err.append(("IMP_CORRECTION_REPLACES_MISMATCH", "%s: replaces %r but [imp].%s.%s is %r"
                                % (where, c["replaces"], c["list"], vid, tab[vid])))
                if c["model"] not in R.IMP_MODELS:
                    err.append(("IMP_CORRECTION_UNKNOWN_MODEL", "%s: model %r is not in the model registry "
                                "(reference.IMP_MODELS)" % (where, c["model"])))
                corr_info.append("INFO IMP correction applied: %s %s: %s -> %s (Amendment %s)"
                                 % (vid, c["list"], c["replaces"], c["model"], c["amendment"]))
    if err:
        return err, info

    # INFO only: D2 floor x 10 <= tolerance per quantity; per-control 10x margin
    kinds_on = ([] if nolin else ["gain"] + (["lag"] if has_lag else []) + ["flat"] + (["phase"] if any_phases else [])
                + (["resid"] if not has_lag else [])) + (["startup"] if sin or osu else []) \
        + (["trace"] + (["invariance"] if transforms else []) if osc else []) \
        + (["ramp_exact"] if orex else []) + (["bound"] if nolin else []) \
        + (["trigger"] if otrig else []) + (["flat_zero"] if ofz else [])
    tol = {q: spec["tolerances"][q]["value"] for q in kinds_on}

    def _ratio(e, t_):
        """effect / tolerance; a zero tolerance (trigger: exact) gives inf for a non-zero effect, 0 for none."""
        return e / t_ if t_ else (float("inf") if e else 0.0)
    fl = spec.get("floor")
    for q in kinds_on:
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
        fix = {q: x for q, x in corr.get(v["id"], {}).items() if q != "source"}
        if not eff and not fix:
            info.append("INFO D2 margin %s: no measured effect in spec (not checked)" % v["id"])
            continue
        eff = dict(eff or {}, **fix)
        ratios = {q: _ratio(eff[q], tol[q]) for q in kinds_on if q in eff}
        if not ratios:
            info.append("INFO D2 margin %s: no measured effect for a checked quantity (not checked)" % v["id"])
            continue
        best = max(ratios, key=ratios.get)
        note = (" (corrected: %s, Amendment 2)" % ", ".join(q for q in kinds_on if q in fix)
                if fix else "")
        info.append("INFO D2 margin %s: error/tolerance %s -> %s%s"
                    % (v["id"], ", ".join("%s %.3gx" % (q, r) for q, r in ratios.items()),
                       "10x margin met (%s)" % best if ratios[best] >= 10 else "10x margin NOT met", note))
    for v in spec["variants"]:                      # role "info" (USE stage 1): run and reported, never PASS/FAIL
        if v["role"] == "info":
            eff = v.get("effect") or {}
            ratios = {q: _ratio(eff[q], tol[q]) for q in kinds_on if q in eff}
            info.append("INFO variant %s (role info, not a control, not in [detect]): effect/tolerance %s; "
                        "reported, never PASS/FAIL" % (v["id"], ", ".join("%s %.3gx" % (q, r) for q, r in ratios.items())
                                                       or "no measured effect in spec"))
    info.extend(corr_info)
    return err, info


def to_checker_spec(spec):
    """The dict analysis/harness/checker.py consumes (checker.h1_spec() has the same shape)."""
    if adaptive_of(spec):
        return to_checker_spec_adaptive(spec)
    errs, infos = validate_spec(spec)
    if errs:
        raise SpecError(errs)
    inp, b, t = spec["inputs"], spec["batch"], spec["tolerances"]
    variants = []
    for v in spec["variants"]:
        e = spec["expected"][v["expected"]]
        vd = dict(id=v["id"], params=v["label"], role=v["role"],
                  expected=(e.get("flat"), list(e.get("gains", [])), e.get("lag")))     # FSH (no linear stage): (None, [], None)
        # D4 keys, added ONLY when the spec / table / variant carries them (old specs: dict unchanged)
        if "seed" in v:
            vd["seed"] = v["seed"]
        if "article" in e:
            vd["article"] = e["article"]
        if "resid" in e:
            vd["resid"] = e["resid"]
        if "phases" in e:
            vd["phases"] = phase_periods(e)
        if "outputs" in v:                       # RFX stage 1 (D6): only oscillator specs
            vd["outputs"] = list(v["outputs"])
            if v.get("invariance"):
                vd["invariance"] = True
            if v.get("startup_info"):
                vd["startup_info"] = True
        if alternating_of(spec):                 # RFF stage 1 (2A): alt keys only when the flag is on
            vd["gain_alt"] = e["gain_alt"]
            if "phase_alt" in e:
                vd["phase_alt"] = e["phase_alt"]
        if skips_of(v):                          # LRSI stage 1 (Amendment 1 A): skipped base inputs
            vd["skip"] = skips_of(v)
        if multi_linear(spec) and v.get("expected_outputs"):     # LRSI: one table per linear output
            lt = {}
            for o, tname in v["expected_outputs"].items():
                te = spec["expected"][tname]
                td = dict(table=tname, expected=(te["flat"], list(te["gains"]), te.get("lag")))
                if "phases" in te:
                    td["phases"] = phase_periods(te)
                if alternating_of(spec):
                    td["gain_alt"] = te["gain_alt"]
                    if "phase_alt" in te:
                        td["phase_alt"] = te["phase_alt"]
                lt[o] = td
            vd["linear_tables"] = {o: lt[o] for o in linear_outputs_of(spec) if o in lt}
        variants.append(vd)
    d = dict(batch=b["name"], id_prefix=b["id_prefix"], indicator=b["indicator"],
             asset=b["asset_label"],
             n_bars=inp["n_bars"], w=inp["warmup"], level=_frac(inp["level"]),
             amp=_frac(inp["amp"]), slope=_frac(inp["slope"]), ts=tuple(inp["sine_periods"]),
             clock_lo=spec["clock"]["lo"], clock_hi=spec["clock"]["hi"],
             tol_flat=t.get("flat", {}).get("value"), tol_gain=t.get("gain", {}).get("value"),
             tol_lag=t.get("lag", {}).get("value"),
             tol_x=t["x"]["value"], variants=variants)
    # Amendment 1 keys, added ONLY when the spec has the section: a spec without them (H1) gives the
    # dict checker.h1_spec() has (test_g1) and the pre-amendment results format.
    if "checks" in spec:
        d["dc_gain"] = spec["checks"].get("dc_gain", 1.0)
        if spec["checks"].get("startup_inputs"):
            d["startup"] = list(spec["checks"]["startup_inputs"])
        if "startup_seed" in spec["checks"]:
            d["startup_seed"] = spec["checks"]["startup_seed"]
        for q in ("phase", "resid", "startup"):
            if q in t:
                d["tol_" + q] = t[q]["value"]
    if alternating_of(spec):
        d["alt"] = True
        d["phase_gate"] = spec["checks"]["phase_gate"]
    if ramp_down_of(spec):
        d["rampdn"] = True
    if osc_of(spec):
        ck = spec["checks"]
        lin = ck.get("linear_output")                       # None: no linear stage (FSH, linear_stage = false)
        d["osc"] = dict(gate=ck["trace_gate"], bound=ck.get("bound"),
                        linear=list(lin) if isinstance(lin, list) else lin)
        if "bound_output" in ck:
            d["osc"]["bound_output"] = ck["bound_output"]
        if ck.get("ramp_exact"):
            d["osc"]["ramp_exact"] = dict(ck["ramp_exact"])
        if ck.get("startup_output") is True:
            d["osc"]["startup"] = True
        # FSH stage 1 keys, added ONLY when present (older specs: dict unchanged)
        if ck.get("trace_outputs"):
            d["osc"]["trace_outputs"] = {o: list(g) for o, g in ck["trace_outputs"].items()}
        if "clamp_gate" in ck:
            d["osc"]["clamp_gate"] = ck["clamp_gate"]
        if ck.get("bounds"):
            d["osc"]["bounds"] = {o: (list(b_) if isinstance(b_, list) else b_) for o, b_ in ck["bounds"].items()}
        if ck.get("ramp_exact_outputs"):
            d["osc"]["ramp_exact_outputs"] = {o: dict(tab) for o, tab in ck["ramp_exact_outputs"].items()}
        if ck.get("trigger") is True:
            d["osc"]["trigger"] = True
        if ck.get("flat_zero"):
            d["osc"]["flat_zero"] = list(ck["flat_zero"])
        for q in ("trace", "bound", "invariance", "ramp_exact", "trigger", "flat_zero"):
            if q in t:
                d["tol_" + q] = t[q]["value"]
    if copies_of(spec):
        d["transforms"] = [dict(id=tr["id"], level=_frac(tr["level"]), amp=_frac(tr["amp"])) for tr in copies_of(spec)]
    if "detect" in spec:
        d["detect_required"] = {k: list(v) for k, v in spec["detect"]["required"].items()}
    if "ox" in spec:
        d["ox"] = dict(reference_raw=spec["ox"]["reference_raw"],
                       reference_sha256=spec["ox"]["reference_sha256"])
    if "literal_info" in spec:
        d["literal_info"] = dict(spec["literal_info"])
    if "imp" in spec:
        d["imp"] = dict(must_pass=dict(spec["imp"]["must_pass"]), must_fail=dict(spec["imp"]["must_fail"]),
                        tol=t["imp"]["value"])
        # [imp_corrections] (validated above): the amendment's model replaces the pre-registered string; the spec's
        # own [imp] tables are copies here, so the record in the spec is not touched.
        for vid, c in spec.get("imp_corrections", {}).items():
            d["imp"][c["list"]][vid] = c["model"]
    if "detect" in spec or "ox" in spec or "literal_info" in spec or "imp_corrections" in spec:
        d["info_lines"] = list(infos)
        if "lint" in spec:                       # LRSI Amendment 1 C: the pre-run no-static record goes into the results header
            d["info_lines"] += no_static_lines(no_static_report(spec))
        d["extended_report"] = True
    return d


# ----------------------------------------------------------------------------- script
def _chunks(items, size):
    return [items[i:i + size] for i in range(0, len(items), size)]


def _decimal_tokens(text):
    return [m.group(1) for m in _DECIMAL_RE.finditer(_strip(text))]


def _lint_allow_errors(v):
    """Validation of the scoped float32 exemption fields on one variant (code LINT_ALLOW)."""
    vid = v.get("id")
    has_l, has_r = "lint_allow_float32" in v, "lint_allow_reason" in v
    if not has_l and not has_r:
        return []
    e = []
    lits, reason = v.get("lint_allow_float32"), v.get("lint_allow_reason")
    if has_l and not has_r:
        e.append(("LINT_ALLOW", "variant %s: lint_allow_float32 without lint_allow_reason" % vid))
    if has_r and not has_l:
        e.append(("LINT_ALLOW", "variant %s: lint_allow_reason without lint_allow_float32" % vid))
    if has_r and (not isinstance(reason, str) or not reason.strip()):
        e.append(("LINT_ALLOW", "variant %s: lint_allow_reason must be a non-empty string" % vid))
    if v.get("kind") != "inline":
        e.append(("LINT_ALLOW", "variant %s: lint_allow_* is only valid on an inline variant" % vid))
    if has_l:
        if not isinstance(lits, list) or not lits or not all(isinstance(x, str) and x for x in lits):
            e.append(("LINT_ALLOW", "variant %s: lint_allow_float32 must be a non-empty list of literal strings" % vid))
        elif v.get("kind") == "inline" and isinstance(v.get("body"), str):
            present = _decimal_tokens(v["body"])
            for x in lits:
                if x not in present:
                    e.append(("LINT_ALLOW", "variant %s: exempted literal %s does not occur as a decimal literal "
                              "in its body (stale exemption)" % (vid, x)))
    return e


def lint_allowances(spec):
    """[(variant id, body text as emitted, [literals], reason)] for every variant that carries an exemption."""
    out = []
    for v in spec["variants"]:
        if v.get("kind") == "inline" and v.get("lint_allow_float32"):
            out.append((v["id"], v["body"].rstrip("\n"), list(v["lint_allow_float32"]), v["lint_allow_reason"]))
    return out


def lint_infos(allow):
    return ["INFO L_FLOAT32 exemption used: variant %s, literal %s, reason: %s" % (vid, lit, reason)
            for vid, _, lits, reason in allow for lit in lits]


def _fn_of(spec, v):
    """The function a variant calls: inline -> its own; a param variant -> [batch].indicator unless it names an included
    function (`function = ...`, RFX: the superseded Reflex_Superseded from its own include)."""
    return v["function"] if (v["kind"] == "inline" or v.get("function")) else spec["batch"]["indicator"]


def build_script(spec):
    """Returns (script text, list of inline function bodies). Raises SpecError if the spec is
    refused. The text is not linted here (write_script lints)."""
    if adaptive_of(spec):
        return build_script_adaptive(spec)
    errs, _ = validate_spec(spec)
    if errs:
        raise SpecError(errs)
    b, z, inp = spec["batch"], spec["zorro"], spec["inputs"]
    P = b["id_prefix"].upper()
    p = b["id_prefix"].lower()
    ts = inp["sine_periods"]
    ids = input_ids(spec)
    alt = alternating_of(spec)
    nin = len(ids)
    transforms = copies_of(spec)
    nbase = nin - len(transforms) * len(ts)
    variants = spec["variants"]
    nvar = len(variants)
    plan = []                                # per variant: (input indexes it is called on, outputs per call, first Y slot)
    nslots = ncalls = 0
    rdn = ramp_down_of(spec)
    for v in variants:
        ks = list(range(nin)) if v.get("invariance") else list(range(nbase))
        ks = [k for k in ks if ids[k] not in skips_of(v)]          # LRSI: skipped inputs get no call (the rest keep their order)
        nout = len(v.get("outputs") or [None])
        plan.append((ks, nout, nslots))
        nslots += nout * len(ks)
        ncalls += len(ks)

    def vcols(vi):
        """[(raw column name, Y slot)] of variant vi, in raw-file order (= checker.variant_columns)."""
        v = variants[vi]
        ks, nout, first = plan[vi]
        if not v.get("outputs"):
            return [("y_%s_%s" % (v["id"], ids[k]), first + j) for j, k in enumerate(ks)]
        return [("%s_%s_%s" % (o, v["id"], ids[k]), first + j * nout + q)
                for q, o in enumerate(v["outputs"]) for j, k in enumerate(ks) if q == nout - 1 or k < nbase]
    ycols = sum(len(vcols(vi)) for vi in range(nvar))
    N = inp["n_bars"]
    L = []
    a = L.append

    # ---- header comment
    a("// %s.c  (GENERATED by analysis/harness/generator.py from the spec; edit the spec, not this file)" % b["script_name"])
    a("//")
    a("// PURPOSE:  Batch harness %s. Feeds synthetic inputs through %s (%d variants:" % (b["id_prefix"], b["indicator"], nvar))
    a("//           %s) and writes the RAW outputs. It does NOT judge anything." % ", ".join(
        v["id"] + (" [control]" if v["role"] == "neg_control" else (" [info]" if v["role"] == "info" else ""))
        for v in variants))
    a("//           Python (analysis/harness/checker.py) measures and writes PASS/FAIL.")
    a("// PREREG:   %s" % b["prereg"])
    a("// INPUTS:   Synthetic only, from the bar counter n: flat | level+amp*sin(2*pi*n/T), T=%s%s | ramp level+slope*n"
      % (",".join(str(t) for t in ts), " | alt level+amp*(-1)^n" if alternating_of(spec) else "")
      + (" | rampdn level-slope*n" if rdn else ""))
    a("//           level=%d/%d amp=%d/%d slope=%d/%d. (b, H1 run 1) Decimal literals are float32 in this Zorro"
      % (inp["level"][0], inp["level"][1], inp["amp"][0], inp["amp"][1], inp["slope"][0], inp["slope"][1]))
    a("//           build and the PI macro is 3.14159, so every constant is built at run time from integers.")
    a("//           %s is used only as a bar clock; clock_close is exported for the checker's magnitude guard." % z["clock_asset"])
    a("// OUTPUT:   %s  (%d rows n=0..%d + header; %d columns; values printed with 15 decimals)"
      % (z["raw_file"], N, N - 1, 2 + nin + ycols))
    if transforms:
        a("//           copies %s: every sine again with the transform's level/amp (sc/of ...), for variants with invariance." %
          ", ".join("%s (level %d/%d amp %d/%d)" % (tr["id"], tr["level"][0], tr["level"][1], tr["amp"][0], tr["amp"][1])
                    for tr in transforms))
    a("// CALLS:    %d filter calls per bar, variant-major, unconditional, fixed order (gotchas 3.1)." % ncalls)
    skipped = [(v["id"], i) for v in variants for i in skips_of(v)]
    if skipped:
        a("// SKIPPED:  no call, no column, no check for %s (spec skip_inputs)." % ", ".join("%s on %s" % s for s in skipped))
    if real_params(spec):
        a("// REALS:    real-valued parameters built at run time from integers (gotchas 9d.1, 9d.8): %s."
          % ", ".join("%s = %d/%d" % (real_param_name(p, pr), pr[0], pr[1]) for pr in real_params(spec)))
    a("// FEEDING:  every x[n], n=0..%d, reaches the filters exactly once; INITRUN and EXITRUN feed and write nothing." % (N - 1))
    a("// NO LOOKBACK GUARD: LookBack = 0, warmup bars are exported too; the checker requires n = 0..%d contiguous." % (N - 1))
    a("// SOURCES:  expected values and tolerances are in the spec, each with an (a)/(b)/(c) label.")
    a("//           Pattern copied from strategies/tests/H1_SuperSmoother2Pole_Harness.c (b: H1 run 2 PASS).")
    if nslots == nvar * nin:
        a("// Y[] index = variant*%d + input." % nin)
    else:
        a("// Y[] slots: variant-major; per call the outputs in the listed order (the last is the return value); see the call comments.")
    a("")
    a("#include <default.c>")
    for inc in includes(spec):
        a('#include "%s"' % inc)
    a("")
    a('#define %s_RAW "%s"' % (P, z["raw_file"]))
    a('#define %s_MARK "%s"' % (P, z["marker_file"]))
    a("#define %s_NBARS %d" % (P, N))
    a("")
    a("static int %s_n = 0;" % p)
    a("static int %s_done = 0;" % p)
    a("static int %s_hdr = 0;" % p)
    a("static int %s_rows = 0;" % p)
    if alt:
        a("static int %s_sgn = 1;\t// alt input sign, flipped once per fed bar (reset at INITRUN)" % p)
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
    a("\t\t%s_n = 0; %s_done = 0; %s_hdr = 0; %s_rows = 0;%s\t// declared initialisers"
      % (p, p, p, p, (" %s_sgn = 1;" % p) if alt else ""))
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
    a("\tvar Y[%d];" % nslots)
    ptr_names = []                           # out-parameter locals (RFX): declared ONCE, reused by every call (copied right after it)
    for v in variants:
        for o in (v.get("outputs") or [])[:-1]:
            if o not in ptr_names:
                ptr_names.append(o)
    for o in ptr_names:
        a("\tvar %s_o_%s;" % (p, o))
    a("\tn = %s_n;" % p)
    a("")
    a("\t// --- constants built at RUN TIME from integers (gotchas 9d.1, 9d.2) ---")
    a("\tvar lvl = %d;\tlvl = lvl / %d;" % tuple(inp["level"]))
    a("\tvar amp = %d;\tamp = amp / %d;" % tuple(inp["amp"]))
    a("\tvar slp = %d;\tslp = slp / %d;" % tuple(inp["slope"]))
    a("\tvar pi_x = 4;\tpi_x = pi_x * atan(1);")
    for tr in transforms:
        a("\tvar lvl_%s = %d;\tlvl_%s = lvl_%s / %d;" % (tr["id"], tr["level"][0], tr["id"], tr["id"], tr["level"][1]))
        a("\tvar amp_%s = %d;\tamp_%s = amp_%s / %d;" % (tr["id"], tr["amp"][0], tr["id"], tr["id"], tr["amp"][1]))
    for pr in real_params(spec):
        nm = real_param_name(p, pr)
        a("\tvar %s = %d;\t%s = %s / %d;" % (nm, pr[0], nm, nm, pr[1]))
    a("")
    a("\t// --- inputs from the bar counter (radians); no decimal literal, no PI macro ---")
    a("\tX[0] = lvl;")
    for k, t in enumerate(ts, start=1):
        a("\tX[%d] = lvl + amp * sin(2 * pi_x * n / %d);" % (k, t))
    if alt:
        a("\tX[%d] = lvl + amp * %s_sgn;" % (len(ts) + 1, p))
    a("\tX[%d] = lvl + slp * n;" % (nbase - 2 if rdn else nbase - 1))
    if rdn:
        a("\tX[%d] = lvl - slp * n;" % (nbase - 1))
    kk = nbase
    for tr in transforms:
        for t in ts:
            a("\tX[%d] = lvl_%s + amp_%s * sin(2 * pi_x * n / %d);" % (kk, tr["id"], tr["id"], t))
            kk += 1
    a("")
    a("\t// --- input series: %d unconditional calls, fixed order ---" % nin)
    for k in range(nin):
        a("\tvars S%d = series(X[%d], %d);" % (k, k, z["series_len"]))
    a("")
    a("\t// --- %d filter calls, variant-major, unconditional, fixed order ---" % ncalls)
    for v, (ks, nout, first) in zip(variants, plan):
        for j, k in enumerate(ks):
            s0 = first + j * nout
            outs = (v.get("outputs") or [])[:-1]
            ptrs = "".join(", &%s_o_%s" % (p, o) for o in outs)      # out-parameters (RFX): all outputs but the last, via local scalars
            args = ", ".join(real_param_name(p, i) if _is_pair(i) else "%d" % i for i in call_params(v))
            a("\tY[%d] = %s(S%d, %s%s);\t// %s %s" % (s0 + nout - 1, _fn_of(spec, v), k, args, ptrs, v["id"], ids[k]))
            for q, o in enumerate(outs):                              # copied before the next call overwrites the local
                a("\tY[%d] = %s_o_%s;" % (s0 + q, p, o))
    a("")
    a("\t// --- write one row per fed bar ---")
    a("\tif(!%s_done) {" % p)
    a("\t\tif(!%s_hdr) {" % p)
    hdr_cols = ["n", "clock_close"] + ["x_" + i for i in ids]
    a('\t\t\tfile_append(%s_RAW, "%s", 0);' % (P, ",".join(hdr_cols)))
    for vi in range(nvar):
        for hc in _chunks([c for c, _ in vcols(vi)], 9) if len(vcols(vi)) > 9 else [[c for c, _ in vcols(vi)]]:
            a('\t\t\tfile_append(%s_RAW, ",%s", 0);' % (P, ",".join(hc)))      # > 9 columns (RFX): several short appends
    a('\t\t\tfile_append(%s_RAW, "\\n", 0);' % P)
    a("\t\t\t%s_hdr = 1;" % p)
    a("\t\t}")
    first = [("%d", "n"), ("%.15f", "priceClose()")] + [("%.15f", "X[%d]" % k) for k in range(nin)]
    for ci, ch in enumerate(_chunks(first, 9)):
        fmt = ",".join(f for f, _ in ch)
        args = ", ".join(e for _, e in ch)
        a('\t\tfile_append(%s_RAW, strf("%s%s", %s), 0);' % (P, "," if ci else "", fmt, args))
    for vi in range(nvar):
        for ci, ch in enumerate(_chunks([s for _, s in vcols(vi)], 9)):
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
    if alt:
        a("\t\t\t%s_sgn = -%s_sgn;" % (p, p))
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


def lint_script(text, inline_bodies=(), include_base=DEFAULT_OUT, allow=()):
    """Returns a list of (rule, message); empty = clean.
    L_PI        no `PI` token in harness plumbing (comments, strings and the inline negative-control
                bodies excluded: they are mutated indicator copies, D3 allows PI; Amendment 2).
    L_FLOAT32   no decimal literal whose float32 value differs from its float64 value (gotchas
                9d.1). Applies to the whole script including inline bodies.
    L_QUIT      no file_append after quit( in the same block (9d.4).
    L_INCLUDE   every #include "path" resolves from include_base (strategies/tests/) to an
                existing file (9d.3). <angle> includes are not checked.
    allow       [(variant id, body, [literals], reason)] from lint_allowances(spec): each listed literal is
                exempt from L_FLOAT32 inside that variant's inline body only (first occurrence of the body
                in the text); everywhere else, including the generated main script, it is still refused."""
    issues = []
    plumbing = text
    for body in inline_bodies:
        plumbing = plumbing.replace(body, " ")
    for m in re.finditer(r"\bPI\b", _strip(plumbing)):
        issues.append(("L_PI", "PI token in harness code (line %d of the plumbing text)"
                       % (_strip(plumbing)[:m.start()].count("\n") + 1)))
        break
    ftext = text
    for _, body, lits, _r in allow:
        i = ftext.find(body)
        if i >= 0:
            new_body = _DECIMAL_RE.sub(lambda m: "0" if m.group(1) in lits else m.group(0), body)
            ftext = ftext[:i] + new_body + ftext[i + len(body):]
    fclean = _strip(ftext)
    for m in _DECIMAL_RE.finditer(fclean):
        tok = m.group(1)
        if not _f32_exact(float(tok)):
            issues.append(("L_FLOAT32", "decimal literal %s is not float32-exact (line %d)"
                           % (tok, fclean[:m.start()].count("\n") + 1)))
    clean = _strip(text)
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
_STATIC_RE = re.compile(r"\bstatic\b")
_STATIC_NAME_RE = re.compile(r"\bstatic\s+(?:\w+\s*\*?\s+)*?\**\s*(\w+)\s*(?:[=;\[,(])")


def lint_no_static(text):
    """[(line, name)] of every `static` token outside comments and strings (LRSI Amendment 1 C: the corrected LaguerreRSI.c must
    have none). `name` is the declared identifier when it can be read, else '?'."""
    clean = _strip(text)
    hits = []
    for m in _STATIC_RE.finditer(clean):
        nm = _STATIC_NAME_RE.match(clean, m.start())
        hits.append((clean[:m.start()].count("\n") + 1, nm.group(1) if nm else "?"))
    return hits


def no_static_report(spec, root=REPO):
    """[(path, hits or None if the file is missing)] for every file in [lint].no_static (paths relative to the repo root)."""
    out = []
    for p in (spec.get("lint") or {}).get("no_static", []):
        full = os.path.normpath(os.path.join(root, p))
        if not os.path.isfile(full):
            out.append((p, None))
            continue
        with open(full, encoding="utf-8", errors="replace") as f:
            out.append((p, lint_no_static(f.read())))
    return out


def no_static_issues(report):
    """Lint issues (rule L_NO_STATIC) for a no_static_report: a missing file or any static token refuses the script."""
    out = []
    for p, hits in report:
        if hits is None:
            out.append(("L_NO_STATIC", "%s not found (the no-static check needs the file)" % p))
        elif hits:
            out.append(("L_NO_STATIC", "%s has %d static token(s): %s" % (p, len(hits), ", ".join(
                "%s (line %d)" % (n, ln) for ln, n in hits))))
    return out


def no_static_lines(report):
    """INFO lines for the results header / lint output (one per file)."""
    lines = []
    for p, hits in report:
        if hits is None:
            lines.append("INFO L_NO_STATIC %s: file not found (no-static check not done)" % p)
        elif not hits:
            lines.append("INFO L_NO_STATIC %s: 0 static tokens (comments excluded): PASS" % p)
        else:
            lines.append("INFO L_NO_STATIC %s: %d static token(s) (comments excluded): FAIL %s"
                         % (p, len(hits), ", ".join("%s line %d" % (n, ln) for ln, n in hits)))
    return lines


def write_script(spec, out_dir, include_base=DEFAULT_OUT):
    """Lint, then write <out_dir>/<script_name>.c with exclusive create (FileExistsError if the
    file exists: an existing .c is never overwritten). Returns the path."""
    text, bodies = build_script(spec)
    issues = lint_script(text, bodies, include_base, allow=lint_allowances(spec)) + no_static_issues(no_static_report(spec))
    if issues:
        raise LintError(issues)
    path = os.path.join(out_dir, spec["batch"]["script_name"] + ".c")
    with open(path, "x", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


# ----------------------------------------------------------------------------- MAF stage 1: adaptive smoothers (HARNESS_DESIGN D7)
def adaptive_of(spec):
    """True when the spec selects the D7 adaptive-smoother check set ([checks].adaptive = true)."""
    chk = spec.get("checks") if isinstance(spec, dict) else None
    return isinstance(chk, dict) and chk.get("adaptive") is True


def adaptive_base_ids(spec):
    """flat, the sines, ramp (point bars), then rampdn when [inputs].ramp_down = true (ATR stage 1; off by default)."""
    return (["flat"] + ["s%d" % t for t in spec["inputs"]["sine_periods"]] + ["ramp"]
            + (["rampdn"] if ramp_down_of(spec) else []))


def band_ids(spec):
    """Band copies of [inputs].band_inputs, ids <id>B (High = x + h, Low = x - h)."""
    return ["%sB" % i for i in spec["inputs"].get("band_inputs", [])]


def eq_section(spec):
    e = spec["inputs"].get("equivariance")
    return e if isinstance(e, dict) else {}


def copy_id(tid, iid):
    """Id of the affine copy `tid` of input iid: s40 -> sc40, s40B -> sc40B (the leading 's' of the sine id is dropped)."""
    return tid + iid[1:]


def eq_copies(spec):
    """[(copy id, transform id, base input id)] in input order (transform-major)."""
    e = eq_section(spec)
    return [(copy_id(tr["id"], i), tr["id"], i) for tr in e.get("transforms", []) for i in e.get("inputs", [])]


def adaptive_input_ids(spec):
    """Base inputs, band inputs, then the equivariance copies."""
    return adaptive_base_ids(spec) + band_ids(spec) + [c for c, _, _ in eq_copies(spec)]


def adaptive_bar_ids(spec):
    """Inputs with their own High / Low (band inputs and copies of band inputs), in input order."""
    bs = set(band_ids(spec))
    return [i for i in adaptive_input_ids(spec) if i in bs or any(c == i and b in bs for c, _, b in eq_copies(spec))]


def _tol_cols(t):
    c = t.get("columns") if isinstance(t, dict) else None
    return dict(c) if isinstance(c, dict) else {}


def _pair_any(p):
    """[n, d] with d > 0 (n any integer, e.g. a negative offset)."""
    return (isinstance(p, list) and len(p) == 2 and all(isinstance(i, int) and not isinstance(i, bool) for i in p) and p[1] > 0)


def adaptive_kinds_on(spec):
    """The D7 kinds the spec checks (tolerance needed for each)."""
    chk = spec.get("checks", {})
    k = ["trace", "bound"]
    if chk.get("hull"):
        k.append("hull")
    if eq_copies(spec):
        k.append("equivariance")
    for q, key in (("ramp_exact", "ramp_exact"), ("lag", "ramp_lag"), ("flat", "flat"), ("window_hull", "window_hull"),
                   ("known_value", "known_value")):
        if chk.get(key):
            k.append(q)
    return k


def validate_adaptive(spec):
    """Validation of a D7 (adaptive) spec. Returns (errors, infos) like validate_spec."""
    err, info = [], []
    for k in ("batch", "zorro", "inputs", "clock", "tolerances", "expected", "variants", "checks", "conditioning"):
        if k not in spec:
            err.append(("STRUCT", "missing section [%s]" % k))
    if err:
        return err, info
    b, inp, chk, tols = spec["batch"], spec["inputs"], spec["checks"], spec["tolerances"]
    for k in ("name", "id_prefix", "indicator", "script_name"):
        if k not in b:
            err.append(("STRUCT", "[batch] missing %s" % k))
    if err:
        return err, info

    def idcheck(what, v):
        if not isinstance(v, str) or not v or not IDFRAG_RE.match(v):
            err.append(("ID_NOT_C", "%s %r is not a valid C identifier fragment [A-Za-z0-9_]" % (what, v)))
        elif "-" in v:
            err.append(("ID_HYPHEN", "%s %r contains '-'" % (what, v)))
    idcheck("batch id_prefix", b["id_prefix"])
    inc = spec["zorro"].get("include")
    if not (isinstance(inc, list) and inc and all(isinstance(i, str) and i for i in inc)) and not (isinstance(inc, str) and inc):
        err.append(("INCLUDE_BAD", "[zorro].include %r must be a path or a non-empty list of paths" % (inc,)))
    ts = inp.get("sine_periods", [])
    if not isinstance(ts, list) or not ts or any(not isinstance(t, int) or isinstance(t, bool) or t <= 0 for t in ts):
        err.append(("ID_NOT_C", "[inputs].sine_periods %r must be positive integers" % (ts,)))
        return err, info
    if "ramp_down" in inp and not isinstance(inp["ramp_down"], bool):
        err.append(("ADAPTIVE_BAD", "[inputs].ramp_down %r must be true or false" % (inp["ramp_down"],)))
    if err:
        return err, info
    base = adaptive_base_ids(spec)
    if "band_inputs" in inp or "band_half" in inp:
        bi, bh = inp.get("band_inputs"), inp.get("band_half")
        if (not isinstance(bi, list) or not bi or len(set(bi)) != len(bi) or any(i not in base or (i == "flat" and inp.get("band_flat") is not True) for i in bi)
                or not _is_pair(bh)):
            err.append(("BARS_BAD", "[inputs].band_inputs %r must be distinct base ids (flat only with [inputs].band_flat = true) and band_half %r "
                        "a positive pair [n, d]"
                        % (bi, bh)))
            return err, info
    ids = adaptive_base_ids(spec) + band_ids(spec)
    eq = inp.get("equivariance")
    if eq is not None:
        ei, tl = (eq.get("inputs"), eq.get("transforms")) if isinstance(eq, dict) else (None, None)
        sines = [i for i in ids if i.startswith("s")]
        if not isinstance(ei, list) or not ei or len(set(ei)) != len(ei) or any(i not in sines for i in ei):
            err.append(("EQUIVARIANCE_BAD", "[inputs.equivariance].inputs %r must be distinct sine ids from %s" % (ei, sines)))
        tids = set()
        for tr in (tl if isinstance(tl, list) and tl else [None]):
            tid = tr.get("id") if isinstance(tr, dict) else None
            if (not isinstance(tid, str) or not re.fullmatch(r"[a-z]+", tid) or tid in ("s", "flat", "ramp") or tid in tids
                    or not _is_pair(tr.get("scale")) or not _pair_any(tr.get("offset"))):
                err.append(("EQUIVARIANCE_BAD", "transform %r: need a unique lower-case id (not s / flat / ramp), scale [n, d] > 0 and "
                            "offset [n, d] (d > 0)" % (tr,)))
            tids.add(tid)
        if err:
            return err, info
    all_ids = adaptive_input_ids(spec)
    for v in spec["variants"]:
        idcheck("variant id", v.get("id"))
    if len({v.get("id") for v in spec["variants"]}) != len(spec["variants"]):
        err.append(("STRUCT", "duplicate variant id"))
    # [checks]
    cols = chk.get("columns")
    if not isinstance(cols, list) or not cols or len(set(cols)) != len(cols) or any(c not in ADAPTIVE_COLUMNS for c in cols):
        err.append(("ADAPTIVE_BAD", "[checks].columns %r must be distinct names from %s" % (cols, "/".join(ADAPTIVE_COLUMNS))))
        return err, info
    lv = chk.get("level_columns", [])
    if not isinstance(lv, list) or any(c not in cols for c in lv):
        err.append(("ADAPTIVE_BAD", "[checks].level_columns %r must be a subset of the columns" % (lv,)))
    if eq is not None:
        fn = chk.get("equivariance_from_n")
        if not isinstance(fn, int) or isinstance(fn, bool) or fn < 0 or fn >= inp["n_bars"]:
            err.append(("EQUIVARIANCE_BAD", "[checks].equivariance_from_n %r must be an integer row in [0, n_bars)" % (fn,)))
    hull = chk.get("hull")
    if hull is not None and (not isinstance(hull, list) or not hull or any(c not in cols for c in hull)):
        err.append(("ADAPTIVE_BAD", "[checks].hull %r must be a non-empty list of columns" % (hull,)))
    for key in ("ramp_exact", "ramp_lag"):
        t = chk.get(key)
        if t is not None and (not isinstance(t, dict) or not t or any(c not in cols or i not in all_ids for c, i in t.items())):
            err.append(("ADAPTIVE_BAD", "[checks].%s %r must map columns to input ids" % (key, t)))
    fl = chk.get("flat")
    if fl is not None and (not isinstance(fl, list) or not fl or any(c not in cols for c in fl)):
        err.append(("ADAPTIVE_BAD", "[checks].flat %r must be a non-empty list of columns (equal to the level on every flat row)" % (fl,)))
    fi = chk.get("flat_info")
    if fi is not None and (not isinstance(fi, dict) or not isinstance(fi.get("columns"), list) or any(c not in cols for c in fi["columns"])
                           or not isinstance(fi.get("from_n"), int)):
        err.append(("ADAPTIVE_BAD", "[checks].flat_info %r must be {columns = [...], from_n = <row>}" % (fi,)))
    if "bars" in chk and not isinstance(chk["bars"], bool):
        err.append(("BARS_BAD", "[checks].bars %r must be true or false" % (chk["bars"],)))
    if band_ids(spec) and chk.get("bars") is not True:
        err.append(("BARS_BAD", "band inputs need [checks].bars = true (the calls pass High / Low)"))
    if "bar_args" in chk and chk["bar_args"] not in BAR_ARGS:
        err.append(("BARS_BAD", "[checks].bar_args %r must be one of %s" % (chk["bar_args"], "/".join(BAR_ARGS))))
    sc = chk.get("scale_columns")                               # ATR stage 1: equivariance role 'scale' (copy = |k| x base, offset ignored)
    if sc is not None and (not isinstance(sc, list) or not sc or len(set(sc)) != len(sc) or any(c not in cols for c in sc)
                           or any(c in lv for c in sc)):
        err.append(("ADAPTIVE_BAD", "[checks].scale_columns %r must be distinct columns, none of them also in level_columns %r (a column "
                    "has one equivariance role)" % (sc, lv)))
    rb = chk.get("range_bound")                                 # ATR stage 1: column >= High - Low on rows >= 1
    if rb is not None and (not isinstance(rb, list) or not rb or len(set(rb)) != len(rb) or any(c not in cols for c in rb)):
        err.append(("ADAPTIVE_BAD", "[checks].range_bound %r must be a non-empty list of distinct columns" % (rb,)))
    wh = chk.get("window_hull")                                 # ATR stage 1: {column = of-column}: column within [min, max] of `of` over the window
    if wh is not None and (not isinstance(wh, dict) or not wh or any(c not in cols or o not in cols or c == o for c, o in wh.items())):
        err.append(("ADAPTIVE_BAD", "[checks].window_hull %r must map columns to another exported column (the window source)" % (wh,)))
    kv = chk.get("known_value")                                 # ATR stage 1: {column = {input = [n, d]}}: column == n/d on rows >= the table's window
    if kv is not None and (not isinstance(kv, dict) or not kv or any(
            c not in cols or not isinstance(m_, dict) or not m_ or any(i not in all_ids or not _pair_any(pr) for i, pr in m_.items())
            for c, m_ in kv.items())):
        err.append(("ADAPTIVE_BAD", "[checks].known_value %r must map columns to {input = [n, d]} (inputs of the spec, d > 0)" % (kv,)))
    if err:
        return err, info
    # tolerances
    kinds = adaptive_kinds_on(spec)
    for q in ["x", "imp"] + kinds:
        t = tols.get(q)
        if not isinstance(t, dict) or not _is_num(t.get("value")) or t["value"] < 0:
            err.append(("STRUCT", "[tolerances.%s] missing or without a numeric value" % q))
        elif not _has_label(t.get("source")):
            err.append(("SOURCE_MISSING", "tolerance %s has no (a)/(b)/(c) source label" % q))
        elif any(c not in cols or not _is_num(val) or val <= 0 for c, val in _tol_cols(t).items()):
            err.append(("TOL_COLUMNS_BAD", "[tolerances.%s].columns %r must map columns to positive numbers" % (q, t.get("columns"))))
        elif "abs" in t and (q not in ("bound", "window_hull") or not _is_num(t["abs"]) or t["abs"] <= 0):
            err.append(("STRUCT", "[tolerances.%s].abs %r: only bound / window_hull take a positive absolute allowance" % (q, t["abs"])))
    # conditioning (D7 rule 3)
    cd = spec["conditioning"]
    traced = adaptive_base_ids(spec) + band_ids(spec)
    if (not isinstance(cd.get("seed"), int) or not isinstance(cd.get("draws"), int) or cd["draws"] < 1
            or not isinstance(cd.get("skip_draws", 0), int) or cd.get("skip_draws", 0) < 0 or not isinstance(cd.get("bound"), dict)
            or sorted(cd["bound"]) != sorted(cols) or not _has_label(cd.get("source"))
            or not isinstance(cd.get("order"), list) or sorted(cd["order"]) != sorted(traced)):
        err.append(("CONDITIONING_BAD", "[conditioning] needs integer seed, draws >= 1, skip_draws >= 0, bound = {every column: value}, "
                    "order = every traced input %s once, and a labelled source" % traced))
    else:
        tt = tols.get("trace", {})
        for c in cols:
            want = _tol_cols(tt).get(c, tt.get("value")) / 10
            if not math.isclose(cd["bound"][c], want, rel_tol=1e-12):
                err.append(("CONDITIONING_BAD", "[conditioning].bound.%s = %r is not the trace tolerance / 10 = %r (S2)"
                            % (c, cd["bound"][c], want)))
    # expected tables
    for name, t in spec["expected"].items():
        if not _has_label(t.get("source")):
            err.append(("SOURCE_MISSING", "expected table %s has no (a)/(b)/(c) source label" % name))
        if R.adaptive_article_model(t.get("article")) is None:
            err.append(("ARTICLE_MODEL", "expected table %s: article = %r is not a model in reference.adaptive_article_model"
                        % (name, t.get("article"))))
        bd = t.get("bounds")
        if not isinstance(bd, dict) or not bd:
            err.append(("BOUNDS_BAD", "expected table %s: bounds must be {column = {lo, hi, from_n}}" % name))
        else:
            for c, s in bd.items():
                if (c not in cols or not isinstance(s, dict) or not s or any(k not in ("lo", "hi", "from_n") for k in s)
                        or not ("lo" in s or "hi" in s) or any(not _is_num(s[k]) for k in ("lo", "hi") if k in s)
                        or ("lo" in s and "hi" in s and not s["lo"] < s["hi"])
                        or not isinstance(s.get("from_n", 0), int)):
                    err.append(("BOUNDS_BAD", "expected table %s: bound %s = %r" % (name, c, s)))
        if chk.get("ramp_lag") and not _is_num(t.get("ramp_lag")):
            err.append(("STRUCT", "expected table %s: ramp_lag (bars) missing ([checks].ramp_lag is on)" % name))
        if (chk.get("window_hull") or chk.get("known_value")) and (not isinstance(t.get("window"), int) or isinstance(t.get("window"), bool)
                                                                   or t["window"] < 1):
            err.append(("STRUCT", "expected table %s: window (integer >= 1: the first row of the window / known-value checks) missing" % name))
        cc = t.get("conditioning")
        if (not isinstance(cc, dict) or not isinstance(cc.get("info"), dict) or not isinstance(cc.get("values"), dict)
                or any(i not in all_ids or not isinstance(l, list) or any(c not in cols for c in l) for i, l in cc["info"].items())
                or sorted(cc["values"]) != sorted(i for i in all_ids if i in cc["values"]) or not cc["values"]):
            err.append(("CONDITIONING_BAD", "expected table %s: conditioning must have info = {input: [columns]} and values = "
                        "{input: {column: value}}" % name))
    # variants
    roles = [v.get("role") for v in spec["variants"]]
    rp = b.get("real_params") is True
    for v in spec["variants"]:
        vid = v.get("id")
        if v.get("role") not in ("real", "neg_control", "info"):
            err.append(("STRUCT", "variant %s: role must be real, neg_control or info" % vid))
        if v.get("expected") not in spec["expected"]:
            err.append(("STRUCT", "variant %s: expected table %r not defined" % (vid, v.get("expected"))))
        pl = v.get("params")
        if (not isinstance(pl, list) or not pl
                or not all((isinstance(i, int) and not isinstance(i, bool)) or (rp and _is_pair(i)) for i in pl)):
            err.append(("PARAMS_BAD", "variant %s: params %r must be integers%s" % (vid, pl, " or [n, d] pairs" if rp else "")))
        outs = v.get("outputs")
        if (not isinstance(outs, list) or not outs or len(set(outs)) != len(outs) or any(o not in cols for o in outs)
                or outs[-1] not in ADAPTIVE_RETURNS or any(o in ADAPTIVE_RETURNS for o in outs[:-1])):
            err.append(("OUTPUTS_BAD", "variant %s: outputs %r must be distinct columns ending in the return value (%s)"
                        % (vid, outs, " or ".join(ADAPTIVE_RETURNS))))
        elif v.get("role") == "real" and sorted(outs) != sorted(cols):
            err.append(("OUTPUTS_BAD", "variant %s: a real variant must export every column %s" % (vid, cols)))
        if "equivariance" in v and not isinstance(v["equivariance"], bool):
            err.append(("EQUIVARIANCE_BAD", "variant %s: equivariance must be true or false" % vid))
        if v.get("equivariance") and not eq_copies(spec):
            err.append(("EQUIVARIANCE_BAD", "variant %s: equivariance = true but [inputs.equivariance] is missing" % vid))
        if v.get("role") == "real" and eq_copies(spec) and not v.get("equivariance"):
            err.append(("EQUIVARIANCE_BAD", "variant %s: a real variant must be called on the equivariance copies" % vid))
        if v.get("kind") == "inline":
            fn, body = v.get("function"), v.get("body")
            if not fn or not isinstance(body, str) or not re.search(r"\b%s\s*\(" % re.escape(fn), body):
                err.append(("STRUCT", "variant %s: inline needs function and a body defining it" % vid))
        elif v.get("kind") != "param":
            err.append(("STRUCT", "variant %s: kind must be param or inline" % vid))
        err.extend(_lint_allow_errors(v))
    if "neg_control" not in roles:
        err.append(("NO_NEG_CONTROL", "no negative control"))
    ctrl = [v.get("id") for v in spec["variants"] if v.get("role") == "neg_control"]
    req = (spec.get("detect") or {}).get("required")
    if not isinstance(req, dict):
        err.append(("DETECT_MISSING", "[detect.required] missing"))
    else:
        for vid, ks in req.items():
            if vid not in ctrl:
                err.append(("DETECT_UNKNOWN_ID", "[detect.required] key %r is not a neg_control variant id" % vid))
            if not isinstance(ks, list) or not ks or any(k not in kinds for k in ks):
                err.append(("DETECT_BAD_KIND", "[detect.required] %s = %r: need a non-empty list of kinds the spec checks (%s)"
                            % (vid, ks, "/".join(kinds))))
        for vid in ctrl:
            if vid not in req:
                err.append(("DETECT_MISSING", "neg_control %s has no entry in [detect.required]" % vid))
        io = (spec.get("detect") or {}).get("info_only", {})     # MAF review: kinds >= 10x deliberately reported as INFO only
        if not isinstance(io, dict) or any(vid not in ctrl or not isinstance(ks, list) or not ks or any(k not in kinds for k in ks)
                                           or set(ks) & set(req.get(vid, [])) for vid, ks in (io.items() if isinstance(io, dict) else [])):
            err.append(("DETECT_BAD_KIND", "[detect.info_only] %r must map controls to checked kinds that are not in [detect.required]" % (io,)))
    imp = spec.get("imp")
    vids = [v.get("id") for v in spec["variants"]]
    if not isinstance(imp, dict) or not all(isinstance(imp.get(k), dict) for k in ("must_pass", "must_fail")):
        err.append(("IMP_BAD", "[imp] needs must_pass and must_fail tables"))
    else:
        for lst in ("must_pass", "must_fail"):
            for vid, model in imp[lst].items():
                if vid not in vids:
                    err.append(("IMP_UNKNOWN_ID", "[imp].%s key %r is not a variant id" % (lst, vid)))
                if model not in R.IMP_MODELS:
                    err.append(("IMP_UNKNOWN_MODEL", "[imp].%s %s = %r is not in reference.IMP_MODELS" % (lst, vid, model)))
        for vid in vids:
            if vid not in imp["must_pass"]:
                err.append(("IMP_BAD", "variant %s has no [imp].must_pass model" % vid))
    lt = spec.get("lint")
    if lt is not None:
        ns = lt.get("no_static") if isinstance(lt, dict) else None
        if not isinstance(ns, list) or not ns or not _has_label(lt.get("source")):
            err.append(("LINT_SECTION_BAD", "[lint].no_static must be a non-empty list of paths with a labelled source"))
    if err:
        return err, info
    # INFO: D2 floor x 10 <= tolerance per quantity (and per column override); per-control 10x margin
    fl = spec.get("floor") or {}
    for q in kinds:
        if q in ("bound", "hull", "window_hull"):
            continue
        t = tols[q]
        for c, tv in [(None, t["value"])] + sorted(_tol_cols(t).items()):
            key = q if c is None else "%s_%s" % (q, c)
            if key in fl:
                ok = fl[key] * 10 <= tv
                info.append("INFO D2 floor %s: floor %.3e x10 = %.3e %s tolerance %.3e -> %s"
                            % (key, fl[key], fl[key] * 10, "<=" if ok else ">", tv, "window ok" if ok else "FLOOR x10 EXCEEDS TOLERANCE"))
            else:
                info.append("INFO D2 floor %s: no floor in spec (not checked)" % key)
    for v in spec["variants"]:
        if v["role"] not in ("neg_control", "info"):
            continue
        eff = v.get("effect") or {}
        ratios = {q: (eff[q] / tols[q]["value"] if tols[q]["value"] else float("inf")) for q in kinds if q in eff}
        if v["role"] == "info":
            info.append("INFO variant %s (role info, not a control, not in [detect]): effect/tolerance %s; reported, never PASS/FAIL"
                        % (v["id"], ", ".join("%s %.3gx" % kv for kv in ratios.items()) or "no measured effect in spec"))
            continue
        if not ratios:
            info.append("INFO D2 margin %s: no measured effect in spec (not checked)" % v["id"])
            continue
        io = (spec.get("detect") or {}).get("info_only", {}).get(v["id"], [])
        req_r = {q: r for q, r in ratios.items() if q not in io}
        best = max(req_r, key=req_r.get) if req_r else None
        info.append("INFO D2 margin %s: error/tolerance %s -> %s%s" % (
            v["id"], ", ".join("%s %.3gx%s" % (q, r, " (INFO only)" if q in io else "") for q, r in ratios.items()),
            "10x margin met (%s)" % best if best and req_r[best] >= 10 else "10x margin NOT met",
            "; INFO-only kinds %s ([detect.info_only])" % ", ".join(io) if io else ""))
    return err, info


def to_checker_spec_adaptive(spec):
    """The checker dict of a D7 spec (checker.adaptive_* reads spec['adaptive'])."""
    errs, infos = validate_adaptive(spec)
    if errs:
        raise SpecError(errs)
    inp, b, t, chk = spec["inputs"], spec["batch"], spec["tolerances"], spec["checks"]
    eq = eq_section(spec)
    variants = []
    for v in spec["variants"]:
        e = spec["expected"][v["expected"]]
        cc = e["conditioning"]
        variants.append(dict(id=v["id"], params=v["label"], role=v["role"], expected=(None, [], None), table=v["expected"],
                             article=e["article"], outputs=list(v["outputs"]), equivariance=bool(v.get("equivariance")),
                             bounds={c: dict(s) for c, s in e["bounds"].items()}, ramp_lag=e.get("ramp_lag"), window=e.get("window"),
                             info_pairs=sorted((i, c) for i, l in cc["info"].items() for c in l)))
    ad = dict(columns=list(chk["columns"]), level_columns=list(chk.get("level_columns", [])), bars=chk.get("bars") is True,
              base=adaptive_base_ids(spec), band=band_ids(spec),
              band_half=_frac(inp["band_half"]) if "band_half" in inp else None,
              copies=[dict(id=c, tid=tid, base=i) for c, tid, i in eq_copies(spec)],
              transforms={tr["id"]: dict(scale=_frac(tr["scale"]), offset=_frac(tr["offset"])) for tr in eq.get("transforms", [])},
              eq_inputs=list(eq.get("inputs", [])), eq_from=chk.get("equivariance_from_n", 0),
              hull=list(chk.get("hull") or []), ramp_exact=dict(chk.get("ramp_exact") or {}), ramp_lag=dict(chk.get("ramp_lag") or {}),
              flat=list(chk.get("flat") or []), flat_info=dict(chk["flat_info"]) if chk.get("flat_info") else None,
              kinds=adaptive_kinds_on(spec))
    ad.update(scale_columns=list(chk.get("scale_columns") or []), range_bound=list(chk.get("range_bound") or []),
              window_hull=dict(chk.get("window_hull") or {}),
              known_value={c: {i: _frac(pr) for i, pr in m_.items()} for c, m_ in (chk.get("known_value") or {}).items()},
              bar_args=chk.get("bar_args", "phl"))
    cd = spec["conditioning"]
    ad["conditioning"] = dict(seed=cd["seed"], draws=cd["draws"], skip_draws=cd.get("skip_draws", 0), order=list(cd["order"]),
                              bound=dict(cd["bound"]))
    ad["tables"] = {n: dict(article=e["article"], info={i: list(l) for i, l in e["conditioning"]["info"].items()},
                            values={i: dict(c) for i, c in e["conditioning"]["values"].items()}) for n, e in spec["expected"].items()}
    ad["real_tables"] = []
    for v in spec["variants"]:
        if v["role"] == "real" and v["expected"] not in ad["real_tables"]:
            ad["real_tables"].append(v["expected"])
    d = dict(batch=b["name"], id_prefix=b["id_prefix"], indicator=b["indicator"], asset=b["asset_label"],
             n_bars=inp["n_bars"], w=inp["warmup"], level=_frac(inp["level"]), amp=_frac(inp["amp"]), slope=_frac(inp["slope"]),
             ts=tuple(inp["sine_periods"]), clock_lo=spec["clock"]["lo"], clock_hi=spec["clock"]["hi"],
             tol_flat=None, tol_gain=None, tol_lag=None, tol_x=t["x"]["value"], variants=variants, adaptive=ad, dc_gain=1.0)
    for q in ad["kinds"]:
        d["tol_" + q] = t[q]["value"]
        d["tolcols_" + q] = _tol_cols(t[q])
    d["detect_required"] = {k: list(v) for k, v in spec["detect"]["required"].items()}
    d["imp"] = dict(must_pass=dict(spec["imp"]["must_pass"]), must_fail=dict(spec["imp"]["must_fail"]), tol=t["imp"]["value"],
                    cols=_tol_cols(t["imp"]))
    d["tol_imp"], d["tolcols_imp"] = t["imp"]["value"], _tol_cols(t["imp"])
    d["tol_bound_abs"] = t.get("bound", {}).get("abs", 0.0)                 # ATR stage 1: absolute allowance next to the relative one
    d["tol_window_hull_abs"] = t.get("window_hull", {}).get("abs", 0.0)
    d["info_lines"] = list(infos)
    if "lint" in spec:
        d["info_lines"] += no_static_lines(no_static_report(spec))
    d["extended_report"] = True
    return d


def build_script_adaptive(spec):
    """The Light-C batch script of a D7 spec (same plumbing as build_script: run-time integer constants, unconditional fixed-order
    calls, out-parameters through local scalars, latch and write before quit()). Returns (text, inline bodies)."""
    errs, _ = validate_adaptive(spec)
    if errs:
        raise SpecError(errs)
    b, z, inp, chk = spec["batch"], spec["zorro"], spec["inputs"], spec["checks"]
    P, p = b["id_prefix"].upper(), b["id_prefix"].lower()
    ts = inp["sine_periods"]
    ids = adaptive_input_ids(spec)
    base, bands, copies = adaptive_base_ids(spec), band_ids(spec), eq_copies(spec)
    bar_ids = adaptive_bar_ids(spec)
    bars = chk.get("bars") is True
    nin, nbar = len(ids), len(bar_ids)
    traced = base + bands
    tr_of = {tr["id"]: tr for tr in eq_section(spec).get("transforms", [])}
    variants = spec["variants"]
    plan, nslots, ncalls = [], 0, 0
    for v in variants:
        ks = [ids.index(i) for i in (ids if v.get("equivariance") else traced)]
        nout = len(v["outputs"])
        plan.append((ks, nout, nslots))
        nslots += nout * len(ks)
        ncalls += len(ks)

    def vcols(vi):
        v = variants[vi]
        ks, nout, first = plan[vi]
        return [("%s_%s_%s" % (o, v["id"], ids[k]), first + j * nout + q) for q, o in enumerate(v["outputs"]) for j, k in enumerate(ks)]
    ycols = sum(len(vcols(vi)) for vi in range(len(variants)))
    N = inp["n_bars"]
    L = []
    a = L.append
    a("// %s.c  (GENERATED by analysis/harness/generator.py from the spec; edit the spec, not this file)" % b["script_name"])
    a("//")
    a("// PURPOSE:  Batch harness %s (HARNESS_DESIGN D7, adaptive smoothers). Feeds synthetic inputs through %s (%d variants:"
      % (b["id_prefix"], b["indicator"], len(variants)))
    a("//           %s) and writes the RAW outputs. It does NOT judge anything." % ", ".join(
        v["id"] + (" [control]" if v["role"] == "neg_control" else (" [info]" if v["role"] == "info" else "")) for v in variants))
    a("//           Python (analysis/harness/checker.py) measures and writes PASS/FAIL.")
    a("// PREREG:   %s" % b["prereg"])
    a("// INPUTS:   Synthetic only, from the bar counter n: flat | level+amp*sin(2*pi*n/T), T=%s | ramp level+slope*n"
      % ",".join(str(t) for t in ts))
    if ramp_down_of(spec):
        a("//           plus rampdn level-slope*n (falling ramp).")
    a("//           level=%d/%d amp=%d/%d slope=%d/%d. (b, H1 run 1) Decimal literals are float32 in this Zorro"
      % (inp["level"][0], inp["level"][1], inp["amp"][0], inp["amp"][1], inp["slope"][0], inp["slope"][1]))
    a("//           build and the PI macro is 3.14159, so every constant is built at run time from integers.")
    if bands:
        a("//           band bars %s: the same x with High = x + h, Low = x - h, h = %d/%d; point bars pass x as %s."
          % (", ".join(bands), inp["band_half"][0], inp["band_half"][1],
             "High, Low and Close" if chk.get("bar_args") == "hlc" else "Price, High and Low"))
    for c, tid, i in copies:
        tr = tr_of[tid]
        a("//           copy %s = %d/%d * %s %s %d/%d (x, High and Low mapped together)"
          % (c, tr["scale"][0], tr["scale"][1], i, "+" if tr["offset"][0] >= 0 else "-", abs(tr["offset"][0]), tr["offset"][1]))
    a("//           %s is used only as a bar clock; clock_close is exported for the checker's magnitude guard." % z["clock_asset"])
    a("// OUTPUT:   %s  (%d rows n=0..%d + header; %d columns; values printed with 15 decimals)"
      % (z["raw_file"], N, N - 1, 2 + nin + 2 * nbar + ycols))
    a("// CALLS:    %d indicator calls per bar, variant-major, unconditional, fixed order (gotchas 3.1)." % ncalls)
    if real_params(spec):
        a("// REALS:    real-valued parameters built at run time from integers (gotchas 9d.1, 9d.8): %s."
          % ", ".join("%s = %d/%d" % (real_param_name(p, pr), pr[0], pr[1]) for pr in real_params(spec)))
    a("// FEEDING:  every x[n], n=0..%d, reaches the indicators exactly once; INITRUN and EXITRUN feed and write nothing." % (N - 1))
    a("// NO LOOKBACK GUARD: LookBack = 0, warmup bars are exported too; the checker requires n = 0..%d contiguous." % (N - 1))
    a("// SOURCES:  expected values and tolerances are in the spec, each with an (a)/(b)/(c) label.")
    a("// Y[] slots: variant-major; per call the outputs in the listed order (the last is the return value); see the call comments.")
    a("")
    a("#include <default.c>")
    for inc_ in includes(spec):
        a('#include "%s"' % inc_)
    a("")
    a('#define %s_RAW "%s"' % (P, z["raw_file"]))
    a('#define %s_MARK "%s"' % (P, z["marker_file"]))
    a("#define %s_NBARS %d" % (P, N))
    a("")
    for s in ("n", "done", "hdr", "rows"):
        a("static int %s_%s = 0;" % (p, s))
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
    a('\t\tprintf("\\n%s EXIT: rows written = %%d, done = %%d  (expected %d and 1)", %s_rows, %s_done);' % (b["id_prefix"], N, p, p))
    a("\t\t// marker file: if it exists after the run, EXITRUN ran even if the printf was lost (gotchas 9d.4)")
    a('\t\tfile_append(%s_MARK, strf("EXITRUN ran: rows=%%d done=%%d\\n", %s_rows, %s_done), 0);' % (P, p, p))
    a("\t\treturn;")
    a("\t}")
    a("")
    a("\tint n;")
    a("\tvar X[%d];" % nin)
    if nbar:
        a("\tvar XH[%d];" % nbar)
        a("\tvar XL[%d];" % nbar)
    a("\tvar Y[%d];" % nslots)
    ptr_names = []
    for v in variants:
        for o in v["outputs"][:-1]:
            if o not in ptr_names:
                ptr_names.append(o)
    for o in ptr_names:
        a("\tvar %s_o_%s;" % (p, o))
    a("\tn = %s_n;" % p)
    a("")
    a("\t// --- constants built at RUN TIME from integers (gotchas 9d.1, 9d.2, 9d.8) ---")
    a("\tvar lvl = %d;\tlvl = lvl / %d;" % tuple(inp["level"]))
    a("\tvar amp = %d;\tamp = amp / %d;" % tuple(inp["amp"]))
    a("\tvar slp = %d;\tslp = slp / %d;" % tuple(inp["slope"]))
    a("\tvar pi_x = 4;\tpi_x = pi_x * atan(1);")
    if bands:
        a("\tvar %s_hb = %d;\t%s_hb = %s_hb / %d;" % (p, inp["band_half"][0], p, p, inp["band_half"][1]))
    for tid, tr in tr_of.items():
        kn, cn = "%s_k_%s" % (p, tid), "%s_c_%s" % (p, tid)
        a("\tvar %s = %d;\t%s = %s / %d;" % (kn, tr["scale"][0], kn, kn, tr["scale"][1]))
        a("\tvar %s = 0;\t%s = %s %s %d;\t%s = %s / %d;" % (cn, cn, cn, "+" if tr["offset"][0] >= 0 else "-", abs(tr["offset"][0]),
                                                           cn, cn, tr["offset"][1]))
    for pr in real_params(spec):
        nm = real_param_name(p, pr)
        a("\tvar %s = %d;\t%s = %s / %d;" % (nm, pr[0], nm, nm, pr[1]))
    a("")
    a("\t// --- inputs from the bar counter (radians); no decimal literal, no PI macro ---")

    def x_expr(iid):
        bid = iid[:-1] if iid in bands else iid
        if bid == "flat":
            return "lvl"
        if bid == "ramp":
            return "lvl + slp * n"
        if bid == "rampdn":
            return "lvl - slp * n"
        return "lvl + amp * sin(2 * pi_x * n / %d)" % int(bid[1:])
    for k, iid in enumerate(ids):
        cp = [(tid, bi) for c, tid, bi in copies if c == iid]
        if cp:
            tid, bi = cp[0]
            a("\tX[%d] = %s_k_%s * X[%d] + %s_c_%s;\t// %s" % (k, p, tid, ids.index(bi), p, tid, iid))
        else:
            a("\tX[%d] = %s;\t// %s" % (k, x_expr(iid), iid))
    for j, iid in enumerate(bar_ids):
        cp = [(tid, bi) for c, tid, bi in copies if c == iid]
        if cp:
            tid, bi = cp[0]
            jb = bar_ids.index(bi)
            a("\tXH[%d] = %s_k_%s * XH[%d] + %s_c_%s;\t// %s High" % (j, p, tid, jb, p, tid, iid))
            a("\tXL[%d] = %s_k_%s * XL[%d] + %s_c_%s;\t// %s Low" % (j, p, tid, jb, p, tid, iid))
        else:
            a("\tXH[%d] = X[%d] + %s_hb;\t// %s High" % (j, ids.index(iid), p, iid))
            a("\tXL[%d] = X[%d] - %s_hb;\t// %s Low" % (j, ids.index(iid), p, iid))
    a("")
    a("\t// --- input series: %d unconditional calls, fixed order ---" % (nin + 2 * nbar))
    for k in range(nin):
        a("\tvars S%d = series(X[%d], %d);" % (k, k, z["series_len"]))
    for j in range(nbar):
        a("\tvars SHi%d = series(XH[%d], %d);" % (j, j, z["series_len"]))
        a("\tvars SLo%d = series(XL[%d], %d);" % (j, j, z["series_len"]))
    a("")
    a("\t// --- %d indicator calls, variant-major, unconditional, fixed order ---" % ncalls)
    for v, (ks, nout, first) in zip(variants, plan):
        for j, k in enumerate(ks):
            s0 = first + j * nout
            outs = v["outputs"][:-1]
            ptrs = "".join(", &%s_o_%s" % (p, o) for o in outs)
            args = ", ".join(real_param_name(p, i) if _is_pair(i) else "%d" % i for i in v["params"])
            if bars:
                if ids[k] in bar_ids:
                    jb = bar_ids.index(ids[k])
                    series_args = ("SHi%d, SLo%d, S%d" % (jb, jb, k)) if chk.get("bar_args") == "hlc" else ("S%d, SHi%d, SLo%d" % (k, jb, jb))
                else:
                    series_args = "S%d, S%d, S%d" % (k, k, k)
            else:
                series_args = "S%d" % k
            a("\tY[%d] = %s(%s, %s%s);\t// %s %s" % (s0 + nout - 1, _fn_of(spec, v), series_args, args, ptrs, v["id"], ids[k]))
            for q, o in enumerate(outs):
                a("\tY[%d] = %s_o_%s;" % (s0 + q, p, o))
    a("")
    a("\t// --- write one row per fed bar ---")
    a("\tif(!%s_done) {" % p)
    a("\t\tif(!%s_hdr) {" % p)
    hdr = ["n", "clock_close"] + ["x_" + i for i in ids] + [c for i in bar_ids for c in ("xh_" + i, "xl_" + i)]
    for hc in _chunks(hdr, 9):
        a('\t\t\tfile_append(%s_RAW, "%s%s", 0);' % (P, "" if hc[0] == "n" else ",", ",".join(hc)))
    for vi in range(len(variants)):
        for hc in _chunks([c for c, _ in vcols(vi)], 9):
            a('\t\t\tfile_append(%s_RAW, ",%s", 0);' % (P, ",".join(hc)))
    a('\t\t\tfile_append(%s_RAW, "\\n", 0);' % P)
    a("\t\t\t%s_hdr = 1;" % p)
    a("\t\t}")
    first = ([("%d", "n"), ("%.15f", "priceClose()")] + [("%.15f", "X[%d]" % k) for k in range(nin)]
             + [("%.15f", "%s[%d]" % (arr, j)) for j in range(nbar) for arr in ("XH", "XL")])
    for ci, ch in enumerate(_chunks(first, 9)):
        a('\t\tfile_append(%s_RAW, strf("%s%s", %s), 0);' % (P, "," if ci else "", ",".join(f for f, _ in ch), ", ".join(e for _, e in ch)))
    for vi in range(len(variants)):
        for ch in _chunks([s for _, s in vcols(vi)], 9):
            a('\t\tfile_append(%s_RAW, strf(",%s", %s), 0);' % (P, ",".join("%.15f" for _ in ch), ",".join("Y[%d]" % j for j in ch)))
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
    allow = lint_allowances(spec)
    nsr = no_static_report(spec)
    issues = lint_script(text, bodies, allow=allow) + no_static_issues(nsr)
    for i in lint_infos(allow) + no_static_lines(nsr):
        print(i)
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
