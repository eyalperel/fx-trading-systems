"""Shared helpers for the ATR tests (specs/ATR_MT4Fidelity.toml; HARNESS_DESIGN D7 applied). NOT a test module.

* the pre-registered corrected code (the brief's code block, docs/harness/ATR_STAGE1_PROMPT.md) split into its two functions, and the inline
  control bodies derived from it (prefix substitution plus the declared edits; test_generator_atr asserts the spec's bodies are exactly these);
* numbers(path): every (b) number the spec stores (conditioning, floors, effects, IMP fire tests, findings), recomputed from reference.py and
  the checker only; planning_numbers(): the planning chat's script (docs/harness/ATR_STAGE1_NUMBERS.py) imported, for the item 1-6 comparison.
No .c file is read, Zorro is not run. Labels: (a) source states, (b) verified here, (c) inference.
"""
import importlib.util
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(HARNESS, "..", ".."))
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)

import checker as C      # noqa: E402
import generator as G    # noqa: E402
import reference as R    # noqa: E402
import maf_support as M  # noqa: E402

SPEC = os.path.join(HARNESS, "specs", "ATR_MT4Fidelity.toml")
PROMPT = os.path.join(ROOT, "docs", "harness", "ATR_STAGE1_PROMPT.md")
NUMBERS_PY = os.path.join(ROOT, "docs", "harness", "ATR_STAGE1_NUMBERS.py")
NUMBERS_OUT = os.path.join(ROOT, "docs", "harness", "ATR_STAGE1_NUMBERS_output.txt")
SIG = {"ATRMT4Core": "var ATRMT4Core(vars High, vars Low, vars Close, int Length, var* pTR)",
       "ATRMT4": "var ATRMT4(vars High, vars Low, vars Close, int Length)"}
CONTROLS = ("NCW", "NC0", "NCWi", "NCR", "NCZ", "NCS", "NCS2")


# ----------------------------------------------------------------------------- the pre-registered code
def brief_block():
    with open(PROMPT, encoding="utf-8") as f:
        return re.search(r"```c\n(.*?)```", f.read(), re.S).group(1)


def brief_functions():
    """{name: body text between the outer braces (without them)} for ATRMT4Core and ATRMT4."""
    block = brief_block()
    out = {}
    for name, sig in SIG.items():
        i = block.index(sig) + len(sig)
        j = block.index("{", i)
        depth, k = 0, j
        while True:
            if block[k] == "{":
                depth += 1
            elif block[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        out[name] = block[j + 1:k].strip("\n")
    return out


def _edit(body, edits):
    for old, new in edits:
        if body.count(old) != 1:
            raise AssertionError("edit target occurs %d times: %r" % (body.count(old), old))
        body = body.replace(old, new)
    return body


# vid: (function, prefix, edits); edits are written with the NEW prefix, each target exactly once
ATR_CONTROLS = {
    "NC0": ("atr_nc0", "ax0_", [("for(ax0_i = 0; ax0_i < Length; ax0_i++)", "for(ax0_i = 1; ax0_i <= Length; ax0_i++)")]),
    "NCWi": ("atr_ncwi", "axi_", [("axi_A[0] = axi_A[1] + (axi_TR[0] - axi_TR[Length])/Length;",
                                    "axi_A[0] = (axi_A[1]*(Length - 1) + axi_TR[0])/Length;")]),
    "NCR": ("atr_ncr", "axr_", [("axr_TR[0] = axr_th - axr_tl;", "axr_TR[0] = High[0] - Low[0];")]),
    "NCZ": ("atr_ncz", "axz_", [("    if(axz_n[0] > Length + 1)",
                                  "    if(axz_n[0] > 1 && axz_n[0] <= Length) {   // NCZ: start-up rows output the mean of the TRs so far\n"
                                  "        for(axz_i = 0; axz_i < axz_n[0] - 1; axz_i++)\n"
                                  "            axz_s = axz_s + axz_TR[axz_i];\n"
                                  "        axz_A[0] = axz_s/(axz_n[0] - 1);\n"
                                  "    }\n"
                                  "    if(axz_n[0] > Length + 1)")]),
}

NCS_BODY = """static var ats_prev = 0;         // NCS: the running ATR in ONE file static shared by every call (restart Zorro before a rerun)
var atr_ncs(vars High, vars Low, vars Close, int Length)
{
    vars ats_n  = series(0, 2);            // per-instance CurrentBar (9d.9)
    vars ats_TR = series(0, Length + 2);   // explicit length (9d.10)
    var ats_a = 0;
    var ats_th = 0;
    var ats_tl = 0;
    var ats_s  = 0;
    int ats_i;
    ats_n[0] = ats_n[1] + 1;
    ats_TR[0] = 0;
    if(ats_n[0] > 1) {
        ats_th = High[0];
        if(Close[1] > ats_th) ats_th = Close[1];
        ats_tl = Low[0];
        if(Close[1] < ats_tl) ats_tl = Close[1];
        ats_TR[0] = ats_th - ats_tl;
    }
    if(ats_n[0] == Length + 1) {
        for(ats_i = 0; ats_i < Length; ats_i++)
            ats_s = ats_s + ats_TR[ats_i];
        ats_a = ats_s/Length;
    }
    if(ats_n[0] > Length + 1)
        ats_a = ats_prev + (ats_TR[0] - ats_TR[Length])/Length;
    ats_prev = ats_a;                      // the shared state
    return ats_a;
}"""


def control_body(vid):
    """The inline body of a control: the corrected ATRMT4Core body with `at_` renamed to the control's prefix, then the declared edits."""
    if vid == "NCS":
        return NCS_BODY
    fn, pre, edits = ATR_CONTROLS[vid]
    body = re.sub(r"\bat_", pre, brief_functions()["ATRMT4Core"])
    body = _edit(body, edits)
    sig = SIG["ATRMT4Core"].replace("var ATRMT4Core(", "var %s(" % fn)
    return "%s\n{\n%s\n}" % (sig, body.rstrip())


# ----------------------------------------------------------------------------- spec, own-model raw file (via maf_support: generic)
def load(path=SPEC):
    return M.load(path)


def planning_numbers():
    """The planning chat's script as a module (docs/harness/ATR_STAGE1_NUMBERS.py)."""
    spec = importlib.util.spec_from_file_location("ATR_STAGE1_NUMBERS", NUMBERS_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tol_summary(path=SPEC):
    _, cs, _, _ = load(path)
    return {k: v for k, v in cs.items() if k.startswith("tol_")}


def generated_call_order(spec, vids):
    """[(variant id, input)] of the calls of the given variants IN THE GENERATED SCRIPT: parsed from the text build_script_adaptive writes
    (the `// <variant> <input>` comment of every call line), in text order. The shared-state replay must use this order (MAF lesson)."""
    text, _ = G.build_script(spec)
    out = []
    for line in text.split("\n"):
        m = re.match(r"\s*Y\[\d+\] = \w+\(.*\);\s*// (\w+) (\w+)\s*$", line)
        if m and m.group(1) in vids:
            out.append((m.group(1), m.group(2)))
    return out


# ----------------------------------------------------------------------------- numbers
def _ncs_order_replay(cs, x, bars, order):
    """NCS replay over an explicit call order [(variant id, input)]: {(vid, input): AtrOut}. Every call passes Length = 14."""
    out = R.simulate_atr_shared([14] * len(order), [x[i] for _, i in order], [bars[i][0] for _, i in order], [bars[i][1] for _, i in order])
    return {k: o for k, o in zip(order, out)}


def numbers(path=SPEC):
    """Every (b) number of the ATR spec, recomputed: dict(conditioning, info, findings, floor, effects, ratios, fire, discrimination,
    imp15, ncs)."""
    spec, cs, x, bars = load(path)
    vals, info = C.conditioning_table(cs)
    cols = cs["adaptive"]["columns"]
    traced = C.adaptive_traced(cs)
    real = [v for v in cs["variants"] if v["role"] == "real"]
    rm = {v["id"]: R.adaptive_article_model(v["article"]) for v in cs["variants"]}
    F, fl = {}, {}
    # own-model outputs (what a perfect run exports), every variant with its OWN [imp] model
    own = M.own_model_outputs(path)
    ref_id = real[0]["id"]

    def sim(vid, i, xx=None, H=None, L=None):
        return R.adaptive_simulate(rm[vid], x[i] if xx is None else xx, *(bars[i] if H is None else (H, L)))
    # IMP estimate: the model on the %.15f-rounded H, L, C vs exact
    imp_est = {}
    for v in real:
        for i in C.variant_inputs(cs, v):
            a = sim(v["id"], i)
            H, L = bars[i]
            b = R.adaptive_simulate(rm[v["id"]], M.round15(x[i]), M.round15(H), M.round15(L))
            for c in cols:
                imp_est["imp_est_%s_%s_%s" % (v["id"], i, c)] = M.mx(getattr(a, c), getattr(b, c))
    F.update(imp_est)
    cand = [vals[v["table"]][i][c] for v in real for i in traced for c in cols]
    fl["trace"] = max(cand + list(imp_est.values()))
    ad = cs["adaptive"]
    eqv = {}
    for v in real:
        for cp in ad["copies"]:
            tr_ = ad["transforms"][cp["tid"]]
            a, b = sim(v["id"], cp["base"]), sim(v["id"], cp["id"])
            for c in cols:
                ref = abs(tr_["scale"]) * getattr(a, c) if c in ad["scale_columns"] else getattr(a, c)
                eqv[(v["id"], cp["tid"], c)] = M.mx(getattr(b, c), ref, ad["eq_from"])
                F["equiv_model_%s_%s_%s" % (v["id"], cp["tid"], c)] = eqv[(v["id"], cp["tid"], c)]
    fl["equivariance"] = max(eqv.values())
    # known answers, zero rows, start-up, bounds, hull (model; rows >= the table's window)
    kn = 0.0
    for v in real:
        P = v["window"]
        for c, m_ in ad["known_value"].items():
            for i, val in m_.items():
                d = M.mx(getattr(sim(v["id"], i), c)[P:], np.full(len(x[i]) - P, val))
                F["known_diff_%s_%s" % (v["id"], i)] = d
                kn = max(kn, d)
        o = sim(v["id"], "s20")
        F["startup_s20_%s" % v["id"]] = float(o.atr[P])
        F["zero_rows_max_%s" % v["id"]] = float(max(np.max(np.abs(sim(v["id"], i).atr[:P])) for i in traced))
        amin, tmin, hull = np.inf, np.inf, 0.0
        for i in C.input_names(cs):
            oi = sim(v["id"], i)
            H, L = bars[i]
            amin = min(amin, float(np.min(oi.atr)))
            tmin = min(tmin, float(np.min(oi.tr[1:] - (H[1:] - L[1:]))))
            sw = np.lib.stride_tricks.sliding_window_view(oi.tr, P)
            lo, hi = sw.min(axis=1)[1:], sw.max(axis=1)[1:]
            a_ = oi.atr[P:]
            hull = max(hull, float(np.max(np.maximum(np.maximum(lo - a_, a_ - hi), 0.0) / np.maximum(np.abs(a_), 1e-300))))
        F["atr_min_every_input_%s" % v["id"]] = amin
        F["tr_minus_range_min_%s" % v["id"]] = tmin
        F["window_hull_rel_violation_max_%s" % v["id"]] = hull
    fl["known_value"] = kn
    # effects, ratios (checker on the own-model raw file); per (input, column) max |control - AT14|
    ctl = [v for v in cs["variants"] if v["role"] in ("neg_control", "info")]
    effects = {v["id"]: M.kind_max(v["id"], path) for v in ctl}
    ratios = {v["id"]: M.ratio_max(v["id"], path) for v in ctl}
    for v in ctl:
        for c in C.adaptive_columns(cs, v):
            eff, first, last = {}, {}, {}
            for i in traced:
                d = np.abs(own[v["id"]][c][i] - own[ref_id][c][i])
                nz = np.nonzero(d > 10 * cs["tol_trace"])[0]
                eff[i], first[i], last[i] = float(np.max(d)), (int(nz[0]) if len(nz) else -1), (int(nz[-1]) if len(nz) else -1)
            F["effect_%s_%s" % (v["id"], c)] = eff                      # max |control - AT14| over all rows, per input
            F["first_row_gt_10tol_%s_%s" % (v["id"], c)] = first       # first / last row where it exceeds 10 x the trace tolerance (-1: never)
            F["last_row_gt_10tol_%s_%s" % (v["id"], c)] = last
    # IMP fire tests on the own-model raw file
    raw = M.synth_raw(path)
    fire = {r["check_id"]: dict(actual=r["actual"], ratio=r["ratio"], result=r["result"]) for r in C.imp_rows(cs, raw)}
    disc = {v["id"]: M._imp_one(cs, raw, v, cs["imp"]["must_pass"][ref_id]) for v in cs["variants"]}
    xr = {i: M.round15(x[i]) for i in C.input_names(cs)}
    raw15 = M.synth_raw(path, x_cols=xr)
    for i in C.adaptive_bar_names(cs):
        raw15.cols["xh_" + i], raw15.cols["xl_" + i] = M.round15(bars[i][0]), M.round15(bars[i][1])
    imp15 = {r["check_id"]: dict(actual=r["actual"], ratio=r["ratio"], result=r["result"],
                                 worst=r["input"].split("worst ratio at ")[1].split(" ")[0], detail=r["detail"])
             for r in C.imp_rows(cs, raw15) if r["check_id"].endswith("imp-pass")}
    # NCS in the GENERATED call order (parsed from the script text) and, for comparison, the input-major order
    gen = generated_call_order(spec, ("NCS", "NCS2"))
    names = [i for i in traced]
    alt = [(vid, i) for i in names for vid in ("NCS", "NCS2")]
    ncs = {}
    for tag, order in (("generated", gen), ("input_major", alt)):
        rep = _ncs_order_replay(cs, x, bars, order)
        ncs[tag] = {k: dict(effect=M.mx(o.atr, own[ref_id]["atr"][k[1]]),
                            ratio=M.mx(o.atr, own[ref_id]["atr"][k[1]]) / cs["tol_trace"]) for k, o in rep.items()}
    return dict(conditioning=vals, info=info, findings=F, floor=fl, effects=effects, ratios=ratios, fire=fire, discrimination=disc,
                imp15=imp15, ncs=ncs, generated_order=gen)
