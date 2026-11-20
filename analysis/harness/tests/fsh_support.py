"""Shared helpers for the FSH tests (Fisher Transform, specs/FSH_ArticleFidelity.toml). NOT a test module.

The RFX helpers (rfx_support) are spec-agnostic: this module binds them to the FSH spec. A perfect run = every variant's columns simulated
with ITS OWN [imp].must_pass model (reference.simulate_fisher via checker.model_out; NCS / NCT: reference.simulate_fisher_shared over all
superseded calls in the generator's variant-major order). `numbers()` recomputes every (b) number the spec stores (findings, floors,
effects, IMP fire tests) from reference.py and the checker, so test_reference_fsh_spec can compare them with the spec (pre-run iii).
No .c file is read, Zorro is not run. Labels: (a) source states, (b) verified here, (c) inference.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rfx_support as _X     # noqa: E402

C, G, R = _X.C, _X.G, _X.R
HARNESS = _X.HARNESS
ROOT = os.path.normpath(os.path.join(HARNESS, "..", ".."))
SPEC_PATH = os.path.join(HARNESS, "specs", "FSH_ArticleFidelity.toml")
REVIEW_MODEL = os.path.join(ROOT, "docs", "harness", "FISHER_REVIEW_MODEL.py")
TS = (5, 10, 20, 40, 100)
REAL = {"FR10": 10, "FR20": 20}
CONTROLS = ("NCW", "NCC", "NCK", "NCL", "NC32", "NCS", "NCT")
INFO = ("NCB",)
OUTS = ("out", "v1", "raw")
ULP_SEED = 12345                     # numpy default_rng seed of the 1-ulp floor estimate (deterministic)


def load(path=SPEC_PATH):
    return _X.load(path)


def own_model_outputs(path=SPEC_PATH):
    return _X.own_model_outputs(path)


def synth_raw(outs=None, path=SPEC_PATH):
    return _X.synth_raw(path, outs)


def raw_csv_text(outs=None, path=SPEC_PATH):
    return _X.raw_csv_text(path, outs)


def evaluated(path=SPEC_PATH):
    return _X.evaluated(path)


def kind_max(vid, path=SPEC_PATH):
    return _X.kind_max(vid, path)


def review_model():
    """The planning chat's independent model (docs/harness/FISHER_REVIEW_MODEL.py), imported without running its __main__."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("fisher_review_model", REVIEW_MODEL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def inputs(cs):
    """The exact inputs of the spec (checker.make_inputs)."""
    return C.make_inputs(cs)


def _f(v):
    return float(v)


def numbers(path=SPEC_PATH):
    """Every (b) number of the spec, recomputed: {'findings': {...}, 'floor': {...}, 'effects': {vid: {kind: v}},
    'fire_test': {...}, 'discrimination': {...}}. Uses only reference.py and the checker (no value is read from the spec)."""
    spec, cs, x = load(path)
    W, AMP = cs["w"], cs["amp"]
    base = C.base_names(cs)
    F = {}
    m = {L: R.fisher_article(L) for L in (10, 20)}
    sim = {(L, i): R.simulate_fisher(m[L], x[i]) for L in (10, 20) for i in x}
    # 1 exact bounds
    F["ln1999"] = math.log(1999.0)
    F["pre_clamp_max_analytic"] = 33 / 100 + 67 / 100 * (999 / 1000)
    F["clamp_jump"] = math.atanh(999 / 1000) - math.atanh(99 / 100)
    for L in (10, 20):
        allo = [sim[(L, i)] for i in x]
        F["raw_min_all_FR%d" % L] = _f(min(np.min(o.raw) for o in allo))
        F["raw_max_all_FR%d" % L] = _f(max(np.max(o.raw) for o in allo))
        F["v1_min_all_FR%d" % L] = _f(min(np.min(o.v1) for o in allo))
        F["v1_max_all_FR%d" % L] = _f(max(np.max(o.v1) for o in allo))
        F["v1_rows_in_gap_FR%d" % L] = int(sum(int(np.sum((np.abs(o.v1) > 99 / 100) & (np.abs(o.v1) < 999 / 1000))) for o in allo))
        F["out_max_abs_all_FR%d" % L] = _f(max(np.max(np.abs(o.out)) for o in allo))
        F["out_max_abs_sines_ge_W_FR%d" % L] = _f(max(np.max(np.abs(sim[(L, "s%d" % t)].out[W:])) for t in TS))
        F["out_max_abs_T100_ge_W_FR%d" % L] = _f(np.max(np.abs(sim[(L, "s100")].out[W:])))
    # 2 gate margins, 3 Fish range
    for L in (10, 20):
        for t in TS:
            o = sim[(L, "s%d" % t)]
            F["gate_range_FR%d_T%d" % (L, t)] = _f(np.min(o.rng[W:]) / AMP)
            F["gate_clamp_FR%d_T%d" % (L, t)] = _f(np.min(o.cdist[W:]))
            F["out_min_FR%d_T%d" % (L, t)] = _f(np.min(o.out[W:]))
            F["out_max_FR%d_T%d" % (L, t)] = _f(np.max(o.out[W:]))
            F["clamped_share_FR%d_T%d" % (L, t)] = _f(np.mean(np.abs(o.pre[W:]) > 99 / 100))
    # 4 ramps
    for L in (10, 20):
        for i, sg in (("ramp", 1.0), ("rampdn", -1.0)):
            o = sim[(L, i)]
            F["%s_raw_first_row_exact_FR%d" % (i, L)] = int(max(k for k in range(len(o.raw)) if o.raw[k] != sg) + 1)
            F["%s_v1_first_row_exact_FR%d" % (i, L)] = int(max(k for k in range(len(o.v1)) if o.v1[k] != sg * (999 / 1000)) + 1)
            F["%s_out_first_row_1e12_FR%d" % (i, L)] = int(max(k for k in range(len(o.out))
                                                             if abs(o.out[k] - sg * math.log(1999.0)) > 1e-12) + 1)
            F["%s_out_minus_ln1999_ge_W_FR%d" % (i, L)] = _f(np.max(np.abs(o.out[W:] - sg * math.log(1999.0))))
    # 5 flat
    for L in (10, 20):
        o = sim[(L, "flat")]
        F["flat_guard_rows_FR%d" % L] = int(np.sum(o.rng == 0))
        F["flat_max_abs_FR%d" % L] = _f(max(np.max(np.abs(o.raw)), np.max(np.abs(o.v1)), np.max(np.abs(o.out))))
    # 6 invariance (model, ungated, rows >= W, five sines)
    for L in (10, 20):
        for tr in cs["transforms"]:
            F["invariance_%s_FR%d" % (tr["id"], L)] = _f(max(np.max(np.abs(sim[(L, "s%d" % t)].out[W:] - sim[(L, "%s%d" % (tr["id"], t))].out[W:]))
                                                          for t in TS))
    # 7 memory, start-up (INFO, F-5): source A zero start vs an EFS-style start (first L-1 bars not computed, state stays 0)
    F["memory_v1_n"] = math.log(1e-12) / math.log(67 / 100)
    F["memory_fish_n"] = math.log(1e-12) / math.log(1 / 2)
    for L in (10, 20):
        for t in TS:
            xs = x["s%d" % t]
            z = sim[(L, "s%d" % t)].out
            e = _efs_start(m[L], xs)
            d = np.abs(z - e)
            F["startup_efs_max_FR%d_T%d" % (L, t)] = _f(np.max(d[:W]))
            nz = np.nonzero(d > 1e-12)[0]
            F["startup_efs_last_row_FR%d_T%d" % (L, t)] = int(nz[-1]) if len(nz) else -1
    # 8 floor estimates
    fl = floor_estimates(cs, x)
    # controls and info: effects via the checker on the own-model raw file
    effects = {}
    for v in cs["variants"]:
        if v["role"] in ("neg_control", "info"):
            effects[v["id"]] = kind_max(v["id"], path)
    # per-T effects (model vs the FR10 model, rows >= W) for the report and [findings]
    ctl_models = {vid: R.IMP_MODELS[spec["imp"]["must_pass"][vid]]() for vid in ("NCW", "NCC", "NCK", "NCL", "NC32", "NCB")}
    for vid, mm in ctl_models.items():
        for t in TS:
            o, r = R.simulate_fisher(mm, x["s%d" % t]), sim[(10, "s%d" % t)]
            for q in OUTS:
                F["effect_%s_%s_T%d" % (vid, q, t)] = _f(np.max(np.abs(getattr(o, q)[W:] - getattr(r, q)[W:])))
        for i in ("ramp", "rampdn"):
            o = R.simulate_fisher(mm, x[i])
            F["effect_%s_%s_v1_last" % (vid, i)] = _f(o.v1[-1])
            F["effect_%s_%s_out_last" % (vid, i)] = _f(o.out[-1])
    # NCS / NCT per (instance, input), shared statics in the generator's call order
    own = own_model_outputs(path)
    for vid in ("NCS", "NCT"):
        for i in base:
            d = np.abs(own[vid]["out"][i] - sim[(10, i)].out)
            nz = np.nonzero(d > 1e-12)[0]
            F["%s_%s_ge_W" % (vid.lower(), i)] = _f(np.max(d[W:]))
            F["%s_%s_lt_W" % (vid.lower(), i)] = _f(np.max(d[:W]))
            F["%s_%s_rows_gt_1e12" % (vid.lower(), i)] = int(len(nz))
            F["%s_%s_first_row_gt_1e12" % (vid.lower(), i)] = int(nz[0]) if len(nz) else -1
    # planning-chat cross-check: two instances (L10, L20) sharing the old file's state on one sine, rows >= 200
    for t in (20, 40, 100):
        xs = x["s%d" % t]
        s = R.simulate_fisher_shared([10, 20], [xs, xs])
        o32 = R.simulate_fisher(R.fisher_article(10, literals="float32"), xs)
        F["shared_L10_L20_T%d_ge_200" % t] = _f(np.max(np.abs(s[0].out[200:] - o32.out[200:])))
    # IMP fire tests on the own-model raw file
    raw = synth_raw(path=path)
    rows = C.imp_rows(cs, raw)
    fire = {r["check_id"]: r["actual"] for r in rows}
    disc = {}
    fr10 = R.fisher_article(10)
    for v in cs["variants"]:
        per = C._imp_fisher(cs, raw, v, fr10, {})
        disc[v["id"]] = _f(max(per.values()))
    return dict(findings=F, floor=fl, effects=effects, fire=fire, discrimination=disc)


def _efs_start(m, xs):
    """Source A with an EFS-style start (review F-5): the first L-1 bars are not computed (output 0, state stays 0)."""
    hi, lo = R.fisher_window(xs, m.L)                  # the window over the FULL history (EFS stores prices from bar 1)
    n = len(xs)
    out = np.zeros(n)
    vp = fp = 0.0
    for t in range(m.L - 1, n):
        raw, _ = R._fisher_raw(float(xs[t]), float(hi[t]), float(lo[t]))
        _, vp, fp = R._fisher_step(raw, vp, fp, m.a, m.b, m.thr, m.cl, m.k)
        out[t] = fp
    return out


def floor_estimates(cs, x):
    """(b) Floor quantities of the FSH spec, model only (no Zorro):
    own_model_*      the checker on the own-model raw file (model = code: 0 for trace / ramp_exact / flat_zero / trigger);
    imp_exported_x   the article model on x printed with %.15f (the exported columns IMP replays) vs on the exact x, rows >= W,
                     every base input, max over raw / v1 / out (the IMP residual a perfect Zorro run would show);
    x_1ulp           the article model on x moved by -1 / 0 / +1 ulp per row (numpy default_rng(ULP_SEED)) vs the exact x, rows >= W,
                     sines and ramps (flat excluded: Zorro's flat is one double, the guard fires exactly), max over raw / v1 / out
                     (an estimate of Zorro vs the model if Zorro's sin() differs from numpy's by an ulp)."""
    W = cs["w"]
    rng = np.random.default_rng(ULP_SEED)
    out = {}
    for L in (10, 20):
        m = R.fisher_article(L)
        e1 = e2 = 0.0
        for i in C.base_names(cs):
            a = R.simulate_fisher(m, x[i])
            b = R.simulate_fisher(m, np.array([float("%.15f" % v) for v in x[i]]))
            e1 = max(e1, max(float(np.max(np.abs(getattr(a, q)[W:] - getattr(b, q)[W:]))) for q in OUTS))
            if i != "flat":
                xp = x[i] + rng.choice([-1.0, 0.0, 1.0], size=len(x[i])) * np.spacing(x[i])
                c = R.simulate_fisher(m, xp)
                e2 = max(e2, max(float(np.max(np.abs(getattr(a, q)[W:] - getattr(c, q)[W:]))) for q in OUTS))
        out["imp_exported_x_FR%d" % L] = e1
        out["x_1ulp_FR%d" % L] = e2
    return out
