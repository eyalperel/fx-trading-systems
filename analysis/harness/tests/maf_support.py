"""Shared helpers for the MAF tests (MAMA / FAMA and FRAMA, specs/MAMA_ArticleFidelity.toml and specs/FRAMA_ArticleFidelity.toml;
HARNESS_DESIGN D7). NOT a test module.

* the pre-registered corrected code (the brief's code block, docs/harness/MAF_STAGE1_PROMPT.md) split into its four functions, and the
  inline control bodies derived from it (prefix substitution plus the declared edits; test_generator_maf asserts the spec's bodies are
  exactly these);
* own-model outputs of every variant (what a perfect Zorro run would export; superseded variants through the shared-state replay in the
  generator's call order), a synthetic Raw object and the checker's evaluation of it;
* numbers(path): every (b) number a spec stores (conditioning, findings, floors, effects, IMP fire tests), recomputed from reference.py
  and the checker only.
No .c file is read, Zorro is not run. Labels: (a) source states, (b) verified here, (c) inference.
"""
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(HARNESS, "..", ".."))
sys.path.insert(0, HARNESS)

import checker as C      # noqa: E402
import generator as G    # noqa: E402
import reference as R    # noqa: E402

MAMA_SPEC = os.path.join(HARNESS, "specs", "MAMA_ArticleFidelity.toml")
FRAMA_SPEC = os.path.join(HARNESS, "specs", "FRAMA_ArticleFidelity.toml")
PROMPT = os.path.join(ROOT, "docs", "harness", "MAF_STAGE1_PROMPT.md")
NUMBERS_PY = os.path.join(ROOT, "docs", "harness", "MAMA_FRAMA_STAGE1_NUMBERS.py")
REVIEW_MODEL = os.path.join(ROOT, "docs", "harness", "MAMA_FRAMA_REVIEW_MODEL.py")
TS = (5, 10, 20, 40, 100)
CHECKED_SINES = ("s10", "s20", "s40", "s100")
SIG = {"MAMACore": "var MAMACore(vars Price, var FastLimit, var SlowLimit,\n             var* pFama, var* pPeriod, var* pAlpha, var* pPhase)",
       "MAMA": "var MAMA(vars Price, var FastLimit, var SlowLimit, var* outFAMA)",
       "FRAMACore": "var FRAMACore(vars Price, vars High, vars Low, int N, var* pDim, var* pAlpha)",
       "FRAMA": "var FRAMA(vars Price, vars High, vars Low, int N)"}
_cache = {}


# ----------------------------------------------------------------------------- the pre-registered code
def brief_block():
    with open(PROMPT, encoding="utf-8") as f:
        return re.search(r"```c\n(.*?)```", f.read(), re.S).group(1)


def brief_functions():
    """{name: body text between the outer braces (without them)} for MAMACore, MAMA, FRAMACore, FRAMA, in the brief's order."""
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


def control_body(core, fn, prefix, edits, old_prefix):
    """A control: the corrected core body with every `old_prefix` identifier renamed to `prefix`, then the declared edits (each target
    exactly once, written with the NEW prefix), under the new function name. Comments kept as in the brief."""
    body = re.sub(r"\b%s" % re.escape(old_prefix), prefix, brief_functions()[core])
    body = _edit(body, edits)
    sig = SIG[core].replace("var %s(" % core, "var %s(" % fn)
    return "%s\n{\n%s\n}" % (sig, body.replace("\n", "\n").rstrip())


MAMA_CONTROLS = {   # vid: (function, prefix, edits); edits are written with the new prefix
    "NCH": ("mam_nch", "mxh_", [("var mxh_w1 = 962;  mxh_w1 = mxh_w1/10000;", "var mxh_w1 = 963;  mxh_w1 = mxh_w1/10000;")]),
    "NCF": ("mam_ncf", "mxf_", [("var mxf_h = 1;     mxf_h = mxf_h/2;", "var mxf_h = 51;    mxf_h = mxf_h/100;")]),
    "NC32": ("mam_nc32", "mx32_", [("var mx32_w1 = 962;  mx32_w1 = mx32_w1/10000;", "var mx32_w1 = 0.0962;"),
                                   ("var mx32_w2 = 5769; mx32_w2 = mx32_w2/10000;", "var mx32_w2 = 0.5769;"),
                                   ("var mx32_ka = 75;   mx32_ka = mx32_ka/1000;", "var mx32_ka = 0.075;"),
                                   ("var mx32_kb = 54;   mx32_kb = mx32_kb/100;", "var mx32_kb = 0.54;"),
                                   ("var mx32_a2 = 2;    mx32_a2 = mx32_a2/10;", "var mx32_a2 = 0.2;"),
                                   ("var mx32_a8 = 8;    mx32_a8 = mx32_a8/10;", "var mx32_a8 = 0.8;"),
                                   ("var mx32_c33 = 33;  mx32_c33 = mx32_c33/100;", "var mx32_c33 = 0.33;"),
                                   ("var mx32_c67 = 67;  mx32_c67 = mx32_c67/100;", "var mx32_c67 = 0.67;"),
                                   ("var mx32_dn = 67;   mx32_dn = mx32_dn/100;", "var mx32_dn = 0.67;")]),
    "NCP": ("mam_ncp", "mxp_", [("var mxp_pi = 4;    mxp_pi = mxp_pi*atan(1);       // S1: exact pi at run time (D3)",
                                 "var mxp_pi = PI;                                  // NCP: Zorro's PI macro (float32 3.14159)")]),
    "NCB": ("mam_ncb", "mxb_", [("var mxb_dn = 67;   mxb_dn = mxb_dn/100;", "var mxb_dn = 68;   mxb_dn = mxb_dn/100;")]),
}

FRAMA_CONTROLS = {
    "NCE": ("fra_nce", "fxe_", [("var fxe_k  = 46;  fxe_k  = fxe_k/10;", "var fxe_k  = 461; fxe_k  = fxe_k/100;")]),
    "NCN": ("fra_ncn", "fxn_", [("int fxn_h = N/2;", "int fxn_N = N + 2;                 // NCN: window N + 2 everywhere\n    int fxn_h = fxn_N/2;"),
                                ("for(fxn_i = 1; fxn_i < N; fxn_i++) {", "for(fxn_i = 1; fxn_i < fxn_N; fxn_i++) {"),
                                ("fxn_N3 = fxn_N3/N;", "fxn_N3 = fxn_N3/fxn_N;"),
                                ("for(fxn_i = fxn_h; fxn_i < N; fxn_i++) {", "for(fxn_i = fxn_h; fxn_i < fxn_N; fxn_i++) {"),
                                ("if(fxn_n[0] < N + 1) fxn_F[0] = Price[0];", "if(fxn_n[0] < fxn_N + 1) fxn_F[0] = Price[0];")]),
    "NC32": ("fra_nc32", "fx32_", [("var fx32_k  = 46;  fx32_k  = fx32_k/10;", "var fx32_k  = 4.6;"),
                                   ("var fx32_lo = 1;   fx32_lo = fx32_lo/100;", "var fx32_lo = 0.01;")]),
}

NCT_BODY = """var fra_nct(vars Price, vars High, vars Low, int N, var* pDim, var* pAlpha)
{
    vars fxt_n = series(0, 2);      // per-instance call counter
    vars fxt_F = series(0, 2);
    vars fxt_D = series(0, 2);
    vars fxt_A = series(0, 2);
    fxt_n[0] = fxt_n[1] + 1;
    fxt_F[0] = fxt_F[1];  fxt_D[0] = fxt_D[1];  fxt_A[0] = fxt_A[1];   // held when not assigned (old: no update when N3 <= 0)
    var fxt_k  = 46;  fxt_k  = fxt_k/10;
    var fxt_lo = 1;   fxt_lo = fxt_lo/100;
    var fxt_u  = 1;
    var fxt_l2 = 2;   fxt_l2 = log(fxt_l2);
    int fxt_h = N/2;
    int fxt_i;
    var fxt_e = 0;
    var fxt_HH = High[0];
    var fxt_LL = Low[0];
    for(fxt_i = 1; fxt_i < N; fxt_i++) {
        if(High[fxt_i] > fxt_HH) fxt_HH = High[fxt_i];
        if(Low[fxt_i]  < fxt_LL) fxt_LL = Low[fxt_i];
    }
    var fxt_N3 = fxt_HH - fxt_LL;  fxt_N3 = fxt_N3/N;
    fxt_HH = High[0];  fxt_LL = Low[0];
    for(fxt_i = 0; fxt_i < fxt_h; fxt_i++) {
        if(High[fxt_i] > fxt_HH) fxt_HH = High[fxt_i];
        if(Low[fxt_i]  < fxt_LL) fxt_LL = Low[fxt_i];
    }
    var fxt_N1 = fxt_HH - fxt_LL;  fxt_N1 = fxt_N1/fxt_h;
    fxt_HH = High[fxt_h];  fxt_LL = Low[fxt_h];
    for(fxt_i = fxt_h; fxt_i < N; fxt_i++) {
        if(High[fxt_i] > fxt_HH) fxt_HH = High[fxt_i];
        if(Low[fxt_i]  < fxt_LL) fxt_LL = Low[fxt_i];
    }
    var fxt_N2 = fxt_HH - fxt_LL;  fxt_N2 = fxt_N2/fxt_h;
    if(fxt_n[0] == 1) fxt_F[0] = Price[0];          // old start-up: seed on the instance's first call
    if(fxt_N3 > 0) {                                 // old guard: no update when N3 <= 0; no N1 / N2 condition
        fxt_D[0] = log(fxt_N1 + fxt_N2) - log(fxt_N3);
        fxt_D[0] = fxt_D[0]/fxt_l2;
        fxt_e = fxt_D[0] - fxt_u;
        fxt_e = fxt_k*fxt_e;
        fxt_A[0] = exp(-fxt_e);
        if(fxt_A[0] < fxt_lo) fxt_A[0] = fxt_lo;
        if(fxt_A[0] > fxt_u)  fxt_A[0] = fxt_u;
        fxt_F[0] = fxt_A[0]*Price[0] + (fxt_u - fxt_A[0])*fxt_F[0];
    }
    *pDim   = fxt_D[0];
    *pAlpha = fxt_A[0];
    return fxt_F[0];
}"""


def mama_control(vid):
    fn, pre, ed = MAMA_CONTROLS[vid]
    return control_body("MAMACore", fn, pre, ed, "ma_")


def frama_control(vid):
    if vid == "NCT":
        return NCT_BODY
    fn, pre, ed = FRAMA_CONTROLS[vid]
    return control_body("FRAMACore", fn, pre, ed, "fr_")


# ----------------------------------------------------------------------------- spec, own-model raw file
def load(path):
    """-> (spec dict, checker dict, exact inputs, bars {input: (H, L)}), cached per path."""
    if path not in _cache:
        sp = G.load_spec(path)
        cs = G.to_checker_spec(sp)
        x = C.make_inputs(cs)
        _cache[path] = dict(spec=sp, cs=cs, x=x, bars=C.make_bars(cs, x))
    c = _cache[path]
    return c["spec"], c["cs"], c["x"], c["bars"]


def models(path):
    spec, cs, _, _ = load(path)
    return {v["id"]: R.IMP_MODELS[spec["imp"]["must_pass"][v["id"]]]() for v in cs["variants"]}


def own_model_outputs(path):
    """{variant id: {column: {input: array}}}: every variant simulated with ITS OWN [imp].must_pass model on the exact inputs."""
    c = _cache.get(path) or (load(path) and _cache[path])
    if "outs" in c:
        return c["outs"]
    spec, cs, x, bars = load(path)
    ms = models(path)
    out, shared = {}, {}
    for v in cs["variants"]:
        m = ms[v["id"]]
        if isinstance(m, (R.MamaShared, R.FramaShared, R.AtrShared)):
            key = (type(m).__name__, m[0])
            if key not in shared:
                shared[key] = C.adaptive_shared_outputs(cs, m, x, bars)
            mo_of = lambda i, key=key, vid=v["id"]: shared[key][(vid, i)]
        else:
            mo_of = lambda i, m=m: C.adaptive_out(m, x[i], *bars[i])
        ov = {}
        for o, i, _ in C.variant_columns(cs, v):
            ov.setdefault(o, {})[i] = np.asarray(getattr(mo_of(i), o), dtype=float)
        out[v["id"]] = ov
    c["outs"] = out
    return out


def synth_raw(path, outs=None, x_cols=None):
    """A checker.Raw of a perfect run (own-model outputs). x_cols: {input: exported x} to override (e.g. %.15f-rounded)."""
    spec, cs, x, bars = load(path)
    outs = outs if outs is not None else own_model_outputs(path)
    raw = C.Raw()
    raw.header = C.header_of(cs)
    n = cs["n_bars"]
    raw.nrows = n
    raw.cols = {"n": np.arange(n, dtype=float), "clock_close": np.full(n, 1.1)}
    for i in C.input_names(cs):
        raw.cols["x_" + i] = np.array(x[i] if x_cols is None else x_cols[i])
    for i in C.adaptive_bar_names(cs):
        raw.cols["xh_" + i], raw.cols["xl_" + i] = np.array(bars[i][0]), np.array(bars[i][1])
    for v in cs["variants"]:
        for o, i, col in C.variant_columns(cs, v):
            raw.cols[col] = np.array(outs[v["id"]][o][i])
    return raw


def evaluated(path):
    c = _cache.get(path) or (load(path) and _cache[path])
    if "eval" not in c:
        _, cs, _, _ = load(path)
        c["eval"] = C.evaluate(cs, synth_raw(path))
    return c["eval"]


def kind_max(vid, path):
    """{kind: max over that variant's check rows of abs_diff x (kind tolerance / row tolerance)} on the own-model raw file: the effect
    of a control in units of the KIND's base tolerance (a column with its own tolerance, e.g. MAMA phase at 1e-8, counts at its own
    tolerance; a bound row's tolerance is |bound| x tol_bound, so its effect is the relative excess). effect / tol_kind = the detection
    ratio. INFO / imp / floor rows excluded."""
    rows, _ = evaluated(path)
    _, cs, _, _ = load(path)
    out = {}
    for r in rows:
        if r["role"] in ("imp", "floor") or r["check_id"].split("-", 2)[1] != vid:
            continue
        k = C._kind(r["check_id"])
        if k == "info":
            continue
        base = cs["tol_" + k]               # bound: the row tolerance is |bound| x tol_bound, so this is the RELATIVE excess
        val = r["abs_diff"] * (base / r["tolerance"]) if (r["tolerance"] and math.isfinite(r["abs_diff"])) else r["abs_diff"]
        out[k] = max(out.get(k, 0.0), float(val))
    return out


def ratio_max(vid, path):
    """{kind: max abs_diff / row tolerance} (the detection ratio)."""
    rows, _ = evaluated(path)
    out = {}
    for r in rows:
        if r["role"] in ("imp", "floor") or r["check_id"].split("-", 2)[1] != vid:
            continue
        k = C._kind(r["check_id"])
        if k == "info":
            continue
        out[k] = max(out.get(k, 0.0), float(r["ratio"]))
    return out


def round15(a):
    return np.array([float("%.15f" % v) for v in a])


def mx(a, b, r0=0):
    return float(np.max(np.abs(np.asarray(a)[r0:] - np.asarray(b)[r0:])))


# ----------------------------------------------------------------------------- numbers
def numbers(path):
    """Every (b) number of the spec at `path`, recomputed: dict(conditioning, findings, floor, effects, ratios, fire, discrimination)."""
    spec, cs, x, bars = load(path)
    is_mama = cs["indicator"] == "MAMACore"
    vals, info = C.conditioning_table(cs)
    F = {}
    fl = {}
    real = [v for v in cs["variants"] if v["role"] == "real"]
    rm = {v["id"]: R.adaptive_article_model(v["article"]) for v in cs["variants"]}
    cols = cs["adaptive"]["columns"]
    traced = C.adaptive_traced(cs)

    def sim(vid, i, y=None, H=None, L=None):
        y = x[i] if y is None else y
        if H is None:
            H, L = bars[i]
        return R.adaptive_simulate(rm[vid], y, H, L)
    # IMP estimate: the model on the %.15f-rounded x (and H, L) vs the exact x, every variant's own model, checked / INFO pairs
    imp_est, imp_est_info = {}, {}
    bnames = set(C.adaptive_bar_names(cs))
    for v in real:
        t = v["table"]
        for i in C.variant_inputs(cs, v):
            a = sim(v["id"], i)
            H, L = bars[i]
            if i in bnames:
                b = R.adaptive_simulate(rm[v["id"]], round15(x[i]), round15(H), round15(L))
            else:
                b = R.adaptive_simulate(rm[v["id"]], round15(x[i]))
            for c in cols:
                d = mx(getattr(a, c), getattr(b, c))
                if c in info[t].get(i, []):
                    imp_est_info["imp_est_info_%s_%s_%s" % (v["id"], i, c)] = d
                else:
                    imp_est["imp_est_%s_%s_%s" % (v["id"], i, c)] = d
    F.update({k: v_ for k, v_ in imp_est.items()})
    F.update({k: v_ for k, v_ in imp_est_info.items()})
    # floors per kind / group: max over real variants and checked pairs of (conditioning, IMP estimate)
    tcol = cs.get("tolcols_trace", {})

    def grp(c):
        return c if c in tcol else ""
    for g in [""] + sorted(tcol):
        key = "trace" if not g else "trace_%s" % g
        cand = [vals[v["table"]][i][c] for v in real for i in traced for c in cols if grp(c) == g and c not in info[v["table"]].get(i, [])]
        cand += [d for k, d in imp_est.items() if grp(k.rsplit("_", 1)[1]) == g]
        fl[key] = max(cand)
    # equivariance floor = the model's own residual, rows >= eq_from
    ad = cs["adaptive"]
    eqcols = cs.get("tolcols_equivariance", {})
    eqv = {}
    for v in real:
        for cp in ad["copies"]:
            tr = ad["transforms"][cp["tid"]]
            a, b = sim(v["id"], cp["base"]), sim(v["id"], cp["id"])
            for c in cols:
                ref = tr["scale"] * getattr(a, c) + tr["offset"] if c in ad["level_columns"] else getattr(a, c)
                eqv[(v["id"], cp["tid"], c)] = mx(getattr(b, c), ref, ad["eq_from"])
                F["equiv_model_%s_%s_%s" % (v["id"], cp["tid"], c)] = eqv[(v["id"], cp["tid"], c)]
    for g in [""] + sorted(eqcols):
        fl["equivariance" if not g else "equivariance_%s" % g] = max(d for (_, _, c), d in eqv.items() if (c if c in eqcols else "") == g)
    if is_mama:
        _mama_findings(cs, x, F, rm, real)
    else:
        _frama_findings(cs, x, bars, F, rm, real, fl)
    # controls: effects on the own-model raw file (checker), ratios
    effects = {v["id"]: kind_max(v["id"], path) for v in cs["variants"] if v["role"] in ("neg_control", "info")}
    ratios = {v["id"]: ratio_max(v["id"], path) for v in cs["variants"] if v["role"] in ("neg_control", "info")}
    own = own_model_outputs(path)
    ref_id = [v for v in cs["variants"] if v["role"] == "real"][0]["id"]
    for v in cs["variants"]:
        if v["role"] == "real":
            continue
        for c in adaptive_cols(cs, v):
            for i in traced:
                F["effect_%s_%s_%s" % (v["id"], c, i)] = mx(own[v["id"]][c][i], own[ref_id][c][i])
    for v in cs["variants"]:
        if v["role"] == "neg_control" and isinstance(models(path)[v["id"]], (R.MamaShared, R.FramaShared)):
            for i in traced:
                for c in adaptive_cols(cs, v):
                    d = np.abs(own[v["id"]][c][i] - own[ref_id][c][i])
                    nz = np.nonzero(d > 1e-12)[0]
                    F["%s_%s_%s_max" % (v["id"].lower(), c, i)] = float(np.max(d))
                    F["%s_%s_%s_rows_gt_1e12" % (v["id"].lower(), c, i)] = int(len(nz))
                    F["%s_%s_%s_last_row_gt_1e12" % (v["id"].lower(), c, i)] = int(nz[-1]) if len(nz) else -1
                    F["%s_%s_%s_max_ge_1000" % (v["id"].lower(), c, i)] = float(np.max(d[1000:]))
    # IMP fire tests on the own-model raw file (exact x): must_pass own = 0, must_fail values, discrimination vs the first real model
    raw = synth_raw(path)
    fire = {r["check_id"]: dict(actual=r["actual"], ratio=r["ratio"], result=r["result"]) for r in C.imp_rows(cs, raw)}
    disc = {}
    for v in cs["variants"]:
        rows = _imp_one(cs, raw, v, cs["imp"]["must_pass"][ref_id])
        disc[v["id"]] = rows
    # IMP on the %.15f-rounded exported x (a perfect run printed with 15 decimals): must_pass of every variant
    xr = {i: round15(x[i]) for i in C.input_names(cs)}
    raw15 = synth_raw(path, x_cols=xr)
    for i in C.adaptive_bar_names(cs):
        raw15.cols["xh_" + i], raw15.cols["xl_" + i] = round15(bars[i][0]), round15(bars[i][1])
    imp15 = {r["check_id"]: dict(actual=r["actual"], ratio=r["ratio"], result=r["result"], worst=r["input"].split("worst ratio at ")[1].split(" ")[0],
                                 info_max=max(r["info_detail"].values()) if r["info_detail"] else 0.0)
             for r in C.imp_rows(cs, raw15) if r["check_id"].endswith("imp-pass")}
    return dict(conditioning=vals, info=info, findings=F, floor=fl, effects=effects, ratios=ratios, fire=fire, discrimination=disc,
                imp15=imp15)


def adaptive_cols(cs, v):
    return C.adaptive_columns(cs, v)


def _imp_one(cs, raw, v, mstr):
    """Max ratio residual / column tolerance of variant v's exported columns replayed with model mstr (checked pairs)."""
    sub = dict(cs)
    sub["imp"] = dict(cs["imp"], must_pass={v["id"]: mstr}, must_fail={})
    r = C.imp_rows(sub, raw)[0]
    return dict(actual=r["actual"], ratio=r["ratio"], worst=r["input"].split("worst ratio at ")[1].split(" ")[0])


def _mama_findings(cs, x, F, rm, real):
    for v in real:
        for i in CHECKED_SINES:
            o = R.adaptive_simulate(rm[v["id"]], x[i])
            F["alpha_min_ge5_%s_%s" % (v["id"], i)] = float(np.min(o.alpha[5:]))
            F["alpha_max_ge5_%s_%s" % (v["id"], i)] = float(np.max(o.alpha[5:]))
            F["period_max_all_%s_%s" % (v["id"], i)] = float(np.max(o.period))
            F["period_min_ge1000_%s_%s" % (v["id"], i)] = float(np.min(o.period[1000:]))
            F["period_max_ge1000_%s_%s" % (v["id"], i)] = float(np.max(o.period[1000:]))
            F["fama_min_ge1000_%s_%s" % (v["id"], i)] = float(np.min(o.fama[1000:]))
            F["fama_max_ge1000_%s_%s" % (v["id"], i)] = float(np.max(o.fama[1000:]))
        F["alpha_rows_lt5_max_%s" % v["id"]] = float(max(np.max(np.abs(R.adaptive_simulate(rm[v["id"]], x[i]).alpha[:5])) for i in x))
        F["period_max_every_input_%s" % v["id"]] = float(max(np.max(R.adaptive_simulate(rm[v["id"]], x[i]).period) for i in x))
        # equivariance item 3 on s20 and s40 (model copies sc = 10x - 9.9, of = x + 1.1)
        for i in ("s20", "s40"):
            a = R.adaptive_simulate(rm[v["id"]], x[i])
            for tid, k, c0 in (("sc", 10.0, -99 / 10), ("of", 1.0, 11 / 10)):
                b = R.adaptive_simulate(rm[v["id"]], k * x[i] + c0)
                last = -1
                for c in R.MAMA_COLUMNS:
                    ref = k * getattr(a, c) + c0 if c in ("mama", "fama") else getattr(a, c)
                    d = np.abs(getattr(b, c) - ref)
                    nz = np.nonzero(d > (1e-8 if c == "phase" else 1e-9))[0]
                    last = max(last, int(nz[-1]) if len(nz) else -1)
                    F["equiv_ge1000_%s_%s_%s_%s" % (v["id"], i, tid, c)] = float(np.max(d[1000:]))
                F["equiv_last_row_off_%s_%s_%s" % (v["id"], i, tid)] = last


def _frama_findings(cs, x, bars, F, rm, real, fl):
    ad = cs["adaptive"]
    h = ad["band_half"]
    for v in real:
        m = rm[v["id"]]
        N = m.N
        o = R.adaptive_simulate(m, x["ramp"])
        F["point_ramp_out_minus_x_%s" % v["id"]] = mx(o.out, x["ramp"])
        F["point_ramp_alpha_min_%s" % v["id"]] = float(np.min(o.alpha))
        F["point_ramp_dim_%s" % v["id"]] = float(o.dim[500])
        F["point_ramp_dim_analytic_%s" % v["id"]] = math.log2(4 * (N / 2 - 1) / (N - 1))
        ob = R.adaptive_simulate(m, x["rampB"], *bars["rampB"])
        r1 = cs["slope"] * (N / 2 - 1) + 2 * h
        r3 = cs["slope"] * (N - 1) + 2 * h
        D = math.log2(4 * r1 / r3)
        a = math.exp(-4.6 * (D - 1))
        lag = (1 - a) / a
        F["band_ramp_D_analytic_%s" % v["id"]] = D
        F["band_ramp_D_model_%s" % v["id"]] = float(ob.dim[2000])
        F["band_ramp_alpha_analytic_%s" % v["id"]] = a
        F["band_ramp_lag_analytic_%s" % v["id"]] = lag
        meas = float(np.mean((x["rampB"][-100:] - ob.out[-100:]) / cs["slope"]))
        F["band_ramp_lag_model_%s" % v["id"]] = meas
        ln = (x["rampB"] - ob.out) / cs["slope"]
        nz = np.nonzero(np.abs(ln - lag) > 1e-9)[0]
        F["band_ramp_lag_last_row_off_1e9_%s" % v["id"]] = int(nz[-1]) if len(nz) else -1
        fl["lag"] = max(fl.get("lag", 0.0), abs(meas - lag))
        of = R.adaptive_simulate(m, x["flat"])
        F["point_flat_out_minus_level_%s" % v["id"]] = mx(of.out, np.full(len(of.out), cs["level"]))
        F["point_flat_dim_max_abs_%s" % v["id"]] = float(np.max(np.abs(of.dim)))
        fl["ramp_exact"] = max(fl.get("ramp_exact", 0.0), F["point_ramp_out_minus_x_%s" % v["id"]])
        fl["flat"] = max(fl.get("flat", 0.0), F["point_flat_out_minus_level_%s" % v["id"]])
        amin, dmax, hull = 1.0, 0.0, 0.0
        for i in C.input_names(cs):
            oi = R.adaptive_simulate(m, x[i], *bars[i])
            amin, dmax = min(amin, float(np.min(oi.alpha))), max(dmax, float(np.max(oi.dim)))
            hull = max(hull, float(np.max(np.maximum(oi.out - np.maximum.accumulate(x[i]), np.minimum.accumulate(x[i]) - oi.out))))
        F["alpha_min_every_input_%s" % v["id"]] = amin
        F["dim_max_every_input_%s" % v["id"]] = dmax
        F["hull_excess_model_%s" % v["id"]] = hull
    F["exp_minus_4_6"] = math.exp(-4.6)
