"""ATR run 1 back-check (planning chat, 2026-11-22). Read 1 of 2 (HARNESS_DESIGN §4): written BEFORE Claude Code's checker,
independent of analysis/harness/checker.py and reference.py. Models: docs/harness/ATR_STAGE1_NUMBERS.py (planning-chat code).

  python docs/harness/ATR_RUN1_BACKCHECK.py <C:/Zorro/Data/GEN_ATR_raw_run1.csv>

Inputs for the models are rebuilt from the spec's integers (level 11/10, amplitude 1/100, slope 1/10000, h 2/10000, pi = 4 atan 1;
copies of s40B as the generator builds them: k * series + c, sc k = 10, c = -99/10; of k = 1, c = 11/10), NOT from the exported x
(D6 lesson). The exported x is only used for the input guard and the IMP replay. NCS / NCS2 are replayed in the generated order
(per bar: NCS on the 16 inputs, then NCS2 on the same 16; order parsed from strategies/tests/GEN_ATR_MT4.c by the stage 2 read-through).
Check sets and tolerances: spec ATR_MT4Fidelity.toml (trace 1e-12 from n = 0; bounds atr >= 0 and tr >= H - L with abs 1e-15,
window_hull rel 1e-12 + abs 1e-15 at rows >= P; known values 1e-12 at rows >= P; equivariance 1e-12 at rows >= 1; imp 1e-12).
"""
import csv, importlib.util, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("nums", os.path.join(HERE, "ATR_STAGE1_NUMBERS.py"))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)

TOL, ABS = 1e-12, 1e-15
ORDER = ["flat", "s5", "s10", "s20", "s40", "s100", "ramp", "rampdn",
         "flatB", "rampB", "rampdnB", "s5B", "s10B", "s20B", "s40B", "s100B"]
COPIES = ["sc40B", "of40B"]
KNOWN = {"flat": 0.0, "flatB": 4e-4, "rampB": 4e-4, "rampdnB": 4e-4, "ramp": 1e-4, "rampdn": 1e-4}


def build_inputs(N):
    n = np.arange(N, dtype=float)
    lvl = 11 / 10; amp = 1 / 100; slp = 1 / 10000; hb = 2 / 10000; pi = 4 * math.atan(1)
    base = {"flat": np.full(N, lvl), "ramp": lvl + slp * n, "rampdn": lvl - slp * n}
    for T in (5, 10, 20, 40, 100):
        base["s%d" % T] = lvl + amp * np.sin(2 * pi * n / T)
    d = {}
    for k, x in base.items():
        d[k] = (x, x, x)
        d[k + "B"] = (x + hb, x - hb, x)
    H, L, C = d["s40B"]
    for name, k, c in (("sc40B", 10.0, -99 / 10), ("of40B", 1.0, 11 / 10)):
        d[name] = (k * H + c, k * L + c, k * C + c)
    return d


def load(path):
    rows = list(csv.reader(open(path, newline="")))
    h = rows[0]
    a = np.array([[float(v) for v in r] for r in rows[1:]])
    return {c: a[:, i] for i, c in enumerate(h)}


def exported(raw, k):
    x = raw["x_" + k]
    if ("xh_" + k) in raw:
        return raw["xh_" + k], raw["xl_" + k], x
    return x, x, x


def checks(raw, inp, var, P, cols, names, model_for):
    """Return list of (kind, name, value, tol) on the variant's columns vs model_for(k)."""
    out = []
    for k in names:
        mtr, matr = model_for(k)
        if "tr" in cols:
            out.append(("trace", "tr:" + k, float(np.abs(raw["tr_%s_%s" % (var, k)] - mtr).max()), TOL))
        out.append(("trace", "atr:" + k, float(np.abs(raw["atr_%s_%s" % (var, k)] - matr).max()), TOL))
    # bounds over every input (and copies if exported)
    ks = [k for k in names + COPIES if ("atr_%s_%s" % (var, k)) in raw]
    out.append(("bound", "atr>=0", max(0.0, -min(raw["atr_%s_%s" % (var, k)].min() for k in ks)) , ABS))
    if "tr" in cols:
        v = 0.0
        for k in ks:
            H, L, _ = inp[k]
            v = max(v, float(-(raw["tr_%s_%s" % (var, k)][1:] - (H[1:] - L[1:])).min()))
        out.append(("bound", "tr>=H-L", max(0.0, v), ABS))
    worst = 0.0
    for k in ks:
        a = raw["atr_%s_%s" % (var, k)]
        tr = raw["tr_%s_%s" % (var, k)] if "tr" in cols else M.true_range(*inp[k])
        for r in range(P, len(a)):
            w = tr[r - P + 1:r + 1]; lo, hi = w.min(), w.max()
            exc = max(lo - a[r] - TOL * abs(lo), a[r] - hi - TOL * abs(hi), 0.0)
            worst = max(worst, exc)
    out.append(("window_hull", "atr in TR window", worst, ABS))
    for k, e in KNOWN.items():
        out.append(("known_value", "atr:" + k, float(np.abs(raw["atr_%s_%s" % (var, k)][P:] - e).max()), TOL))
    if "tr" in cols and ("tr_%s_sc40B" % var) in raw:
        for c in ("tr", "atr"):
            b = raw["%s_%s_s40B" % (c, var)]
            out.append(("equivariance", c + ":sc", float(np.abs(raw["%s_%s_sc40B" % (c, var)][1:] - 10 * b[1:]).max()), TOL))
            out.append(("equivariance", c + ":of", float(np.abs(raw["%s_%s_of40B" % (c, var)][1:] - b[1:]).max()), TOL))
    return out


def main(path):
    raw = load(path)
    N = len(raw["n"])
    inp = build_inputs(N)
    print("raw %s: %d rows, %d columns; n from %d to %d" % (os.path.basename(path), N, len(raw), raw["n"][0], raw["n"][-1]))

    # input guard: exported vs integer-built
    g = 0.0
    for k in ORDER + COPIES:
        for e, m in zip(exported(raw, k), inp[k]):
            g = max(g, float(np.abs(e - m).max()))
    print("INPUT GUARD max |exported - integer-built| = %.3e (tol 1e-12): %s" % (g, "PASS" if g <= 1e-12 else "FAIL"))

    real_total, real_pass = 0, 0
    ref = {}
    for var, P in (("AT14", 14), ("AT20", 20)):
        mod = {k: M.atr_model(*inp[k], P=P) for k in ORDER + COPIES}
        ref[var] = mod
        res = checks(raw, inp, var, P, ("tr", "atr"), ORDER, lambda k: mod[k])
        npass = sum(v <= t for _, _, v, t in res)
        real_total += len(res); real_pass += npass
        kinds = {}
        for kind, name, v, t in res:
            kinds.setdefault(kind, []).append((v, name))
        print("\n%s: %d checks, %d PASS" % (var, len(res), npass))
        for kind, vs in kinds.items():
            v, nm = max(vs)
            print("   %-13s n=%2d  max %.3e (%s)" % (kind, len(vs), v, nm))
        for kind, name, v, t in res:
            if v > t:
                print("   FAIL %s %s %.3e" % (kind, name, v))
    print("\nREAL CHECKS: %d / %d PASS" % (real_pass, real_total))

    # controls: each judged against the AT14 model (the spec's rule), on its own columns
    nc_ncs = M.ncs_replay(inp, ORDER, P=14, order="instance_major")
    ctl = [("NCW", ("tr", "atr")), ("NC0", ("tr", "atr")), ("NCWi", ("tr", "atr")), ("NCR", ("tr", "atr")),
           ("NCZ", ("tr", "atr")), ("NCS", ("atr",)), ("NCS2", ("atr",))]
    print("\nCONTROLS (vs the AT14 model; FAIL checks per kind; max ratio to tolerance)")
    for c, cols in ctl:
        res = checks(raw, inp, c, 14, cols, ORDER, lambda k: ref["AT14"][k])
        per = {}
        for kind, name, v, t in res:
            f, mx = per.get(kind, (0, 0.0))
            per[kind] = (f + (v > t), max(mx, v / t))
        nf = sum(f for f, _ in per.values())
        print("   %-5s FAIL checks %3d | " % (c, nf) + "  ".join("%s %d (%.2e x)" % (k, f, mx) for k, (f, mx) in per.items()))

    # IMP: each variant's own model fed the EXPORTED (rounded) inputs vs the raw columns; NCS via the generated-order replay
    print("\nIMP (own model fed the exported %.15f inputs; must_pass <= 1e-12)")
    kw = {"AT14": dict(P=14), "AT20": dict(P=20), "NCW": dict(P=15), "NC0": dict(P=14, first="with_tr0"),
          "NCWi": dict(P=14, avg="wilder"), "NCR": dict(P=14, tr_kind="hl"), "NCZ": dict(P=14, startup="tr")}
    exp_inp = {k: exported(raw, k) for k in ORDER + COPIES}
    for v, a in kw.items():
        names = ORDER + (COPIES if v in ("AT14", "AT20") else [])
        worst = (0.0, "")
        for k in names:
            mtr, matr = M.atr_model(*exp_inp[k], **a)
            for c, m in (("tr", mtr), ("atr", matr)):
                d = float(np.abs(raw["%s_%s_%s" % (c, v, k)] - m).max())
                if d > worst[0]:
                    worst = (d, "%s:%s" % (k, c))
        print("   %-5s %.15e (%s) %s" % (v, worst[0], worst[1], "PASS" if worst[0] <= TOL else "FAIL"))
    rep = M.ncs_replay(exp_inp, ORDER, P=14, order="instance_major")
    for i, v in ((1, "NCS"), (2, "NCS2")):
        worst = max((float(np.abs(raw["atr_%s_%s" % (v, k)] - rep[(k, i)]).max()), k) for k in ORDER)
        print("   %-5s %.15e (%s:atr) %s" % (v, worst[0], worst[1], "PASS" if worst[0] <= TOL else "FAIL"))
    # must_fail
    # must_fail over EVERY exported input of the variant (copies included: FSH Amendment 2 lesson; first version of this file
    # looped ORDER only and gave 1.870e-4 instead of the copy-driven maximum, found before the prediction was written)
    mf1 = max(float(np.abs(raw["atr_AT14_%s" % k] - M.atr_model(*exp_inp[k], P=14, avg="wilder")[1]).max()) for k in ORDER + COPIES)
    mf2 = max(float(np.abs(raw["atr_NCS_%s" % k] - M.atr_model(*exp_inp[k], P=14)[1]).max()) for k in ORDER)
    print("   must_fail AT14 vs Wilder model %.15e (%s);  NCS vs AT14 model %.15e (%s)"
          % (mf1, "detected" if mf1 > 10 * TOL else "NOT", mf2, "detected" if mf2 > 10 * TOL else "NOT"))
    # NCS integer-built replay vs raw (the order check)
    worst = max((float(np.abs(raw["atr_%s_%s" % (v, k)] - nc_ncs[(k, i)]).max()), v, k)
                for i, v in ((1, "NCS"), (2, "NCS2")) for k in ORDER)
    print("\nNCS generated-order replay (integer-built inputs) vs raw: max %.3e (%s %s)" % worst)
    # floor: real variants vs integer-built model, all checked columns
    fl = max(float(np.abs(raw["%s_%s_%s" % (c, v, k)] - ref[v][k][0 if c == "tr" else 1]).max())
             for v in ("AT14", "AT20") for k in ORDER + COPIES for c in ("tr", "atr"))
    print("FLOOR Zorro vs integer-built model, real variants, every column and input: %.3e (x10 = %.1e vs tol 1e-12)" % (fl, 10 * fl))


if __name__ == "__main__":
    main(sys.argv[1])
