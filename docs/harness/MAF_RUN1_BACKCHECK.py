"""MAF run 1 back-check (planning chat, 2026-11-21). Independent of analysis/harness/{reference,checker}.py.
Models: the planning-chat review models (MAMA_FRAMA_REVIEW_MODEL.py), with MAMA's degree conversion in the corrected code's order
(deg = 180/pi; atan(.)*deg; 360/that). Inputs rebuilt from integers as the generator does (lvl 11/10, amp 1/100, slope 1/10000, pi = 4 atan 1,
h = 2/1000, copies k x + c), compared with the exported x first. Checks and tolerances as the two specs (D7)."""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # MAMA_FRAMA_REVIEW_MODEL.py lives beside this file
from MAMA_FRAMA_REVIEW_MODEL import get, f32

RAW = (sys.argv[1] if len(sys.argv) > 1 else "C:/Zorro/Data") .rstrip("/") + "/"   # folder holding GEN_MAM_raw_run1.csv / GEN_FRA_raw_run1.csv
NB = 3000
PI = 4 * math.atan(1)
LVL, AMP, SLP, HB = 11 / 10, 1 / 100, 1 / 10000, 2 / 1000
ZPI = f32(3.14159)


def load(f):
    with open(RAW + f) as fh:
        hdr = fh.readline().strip().split(",")
    a = np.loadtxt(RAW + f, delimiter=",", skiprows=1)
    assert a.shape == (NB, len(hdr)), a.shape
    return {h: a[:, i] for i, h in enumerate(hdr)}


def base_inputs():
    n = np.arange(NB, dtype=float)
    d = {"flat": np.full(NB, LVL), "ramp": LVL + SLP * n}
    for T in (5, 10, 20, 40, 100):
        d[f"s{T}"] = LVL + AMP * np.sin(2 * PI * n / T)
    return d


# ---------------------------------------------------------------- MAMA (corrected-code order; options for the controls)
def mama(x, FL, SL, w1=962 / 10000, dn=67 / 100, fama_k=1 / 2, pi=PI, f32lit=False, superseded=None):
    """superseded = None: corrected file (zero start, CurrentBar > 5, hold). superseded = list of call counters (bc per bar) for the old
    file: price seeds, series defaults re-set every bar, Period init 20, float32 literals, Zorro PI (x is that call's input)."""
    c = (lambda v: f32(v)) if f32lit else (lambda v: v)
    W1, W2, KA, KB = c(w1), c(5769 / 10000), c(75 / 1000), c(54 / 100)
    A2, A8, UP, DN, C33, C67 = c(2 / 10), c(8 / 10), 15 / 10, c(dn), c(33 / 100), c(67 / 100)
    deg = 180 / pi
    n = len(x)
    S, De, I1, Q1, jI, jQ, I2, Q2, Re, Im, P, Ph, M, F, AL = (np.zeros(n) for _ in range(15))
    old = superseded is not None
    x0 = x[0]
    P0 = 20.0 if old else 0.0
    for i in range(n):
        if old:
            S[i], M[i], F[i], P[i] = x[i], x[i], x[i], 20.0
            for a in (De, I1, Q1, jI, jQ, I2, Q2, Re, Im, Ph):
                a[i] = 0.0
            if superseded[i] <= 5:
                continue
            pad = {id(S): x0, id(M): x0, id(F): x0, id(P): 20.0}
            g = lambda a, k: get(a, i, k, pad.get(id(a), x0 if a is x else 0.0))
        else:
            for a in (S, De, I1, Q1, jI, jQ, I2, Q2, Re, Im, P, Ph, M, F, AL):
                a[i] = a[i - 1] if i else 0.0
            if i + 1 <= 5:
                continue
            g = lambda a, k: get(a, i, k, x0 if a is x else 0.0)
        S[i] = (4 * x[i] + 3 * g(x, 1) + 2 * g(x, 2) + g(x, 3)) / 10
        pf = KA * g(P, 1) + KB
        ht = lambda a: (W1 * a[i] + W2 * g(a, 2) - W2 * g(a, 4) - W1 * g(a, 6)) * pf
        De[i] = ht(S); Q1[i] = ht(De); I1[i] = g(De, 3); jI[i] = ht(I1); jQ[i] = ht(Q1)
        I2[i] = I1[i] - jQ[i]; Q2[i] = Q1[i] + jI[i]
        I2[i] = A2 * I2[i] + A8 * g(I2, 1); Q2[i] = A2 * Q2[i] + A8 * g(Q2, 1)
        Re[i] = I2[i] * g(I2, 1) + Q2[i] * g(Q2, 1)
        Im[i] = I2[i] * g(Q2, 1) - Q2[i] * g(I2, 1)
        Re[i] = A2 * Re[i] + A8 * g(Re, 1); Im[i] = A2 * Im[i] + A8 * g(Im, 1)
        p1 = g(P, 1)
        if Im[i] != 0 and Re[i] != 0:
            if old:
                P[i] = 360.0 / (math.atan(Im[i] / Re[i]) * 180.0 / pi)
            else:
                P[i] = 360 / (math.atan(Im[i] / Re[i]) * deg)
        if P[i] > UP * p1: P[i] = UP * p1
        if P[i] < DN * p1: P[i] = DN * p1
        if P[i] < 6: P[i] = 6
        if P[i] > 50: P[i] = 50
        P[i] = A2 * P[i] + A8 * p1
        if I1[i] != 0:
            Ph[i] = math.atan(Q1[i] / I1[i]) * 180.0 / pi if old else math.atan(Q1[i] / I1[i]) * deg
        dp = g(Ph, 1) - Ph[i]
        if dp < 1: dp = 1
        al = FL / dp
        if al < SL: al = SL
        if al > FL: al = FL
        AL[i] = al
        M[i] = al * x[i] + (1 - al) * g(M, 1)
        ah = fama_k * al
        F[i] = ah * M[i] + (1 - ah) * g(F, 1)
    return {"mama": M, "fama": F, "period": P, "alpha": AL, "phase": Ph}


# ---------------------------------------------------------------- FRAMA
def boxes(H, L, i, N):
    h = N // 2
    hh = lambda k: H[max(i - k, 0)]; ll = lambda k: L[max(i - k, 0)]
    N3 = (max(hh(k) for k in range(N)) - min(ll(k) for k in range(N))) / N
    N1 = (max(hh(k) for k in range(h)) - min(ll(k) for k in range(h))) / h
    N2 = (max(hh(k) for k in range(h, N)) - min(ll(k) for k in range(h, N))) / h
    return N1, N2, N3


def frama(x, H, L, N, k=46 / 10, lo=1 / 100, startup="source"):
    n = len(x); F = np.zeros(n); D = np.zeros(n); A = np.zeros(n); l2 = math.log(2)
    dim = 0.0; prev = None; al = 0.0
    for i in range(n):
        N1, N2, N3 = boxes(H, L, i, N)
        if startup == "source":
            if N1 > 0 and N2 > 0 and N3 > 0:
                dim = (math.log(N1 + N2) - math.log(N3)) / l2
            al = math.exp(-(k * (dim - 1)))
            if al < lo: al = lo
            if al > 1: al = 1
            F[i] = al * x[i] + (1 - al) * (F[i - 1] if i else 0.0)
            if i + 1 < N + 1: F[i] = x[i]
        else:   # NCT: old start-up and guard, per instance (dim / alpha held where N3 <= 0, zero start)
            if prev is None: prev = x[i]
            if N3 <= 0:
                F[i] = prev; D[i] = dim; A[i] = al; continue
            lg = math.log(N1 + N2) if N1 + N2 > 0 else -math.inf
            dim = (lg - math.log(N3)) / l2
            al = math.exp(-(k * (dim - 1)))
            if al < lo: al = lo
            if al > 1: al = 1
            prev = al * x[i] + (1 - al) * prev; F[i] = prev
        D[i] = dim; A[i] = al
    return {"out": F, "dim": D, "alpha": A}


def frama_superseded_shared(calls, T, n=NB):
    """Old FRAMA.c: one frama_prev / frama_init shared by every call, calls = list of (x, H, L) in the generator's order (NCS inputs then NCS2).
    float32 4.6 / .01. Returns list of outputs per call."""
    k, lo = f32(4.6), f32(0.01)
    outs = [np.zeros(n) for _ in calls]; prev = None
    for i in range(n):
        for c, (x, H, L) in enumerate(calls):
            r1 = boxes(H, L, i, 2 * T)
            N1, N2 = r1[0], r1[1]
            N3 = r1[2]
            if prev is None: prev = x[i]
            if N3 <= 0:
                outs[c][i] = prev; continue
            lg = math.log(N1 + N2) if N1 + N2 > 0 else -math.inf
            Dm = (lg - math.log(N3)) / math.log(2.0)
            a = math.exp(-k * (Dm - 1.0))
            if a > 1.0: a = 1.0
            if a < lo: a = lo
            prev = a * x[i] + (1.0 - a) * prev
            outs[c][i] = prev
    return outs


def mx(a, b, r0=0):
    return float(np.max(np.abs(np.asarray(a)[r0:] - np.asarray(b)[r0:])))


def out(s):
    print(s, flush=True)


if __name__ == "__main__":
    B = base_inputs()
    # ======================================================== MAMA
    R = load("GEN_MAM_raw_run1.csv")
    X = dict(B)
    X["sc40"] = 10 * B["s40"] + (0 - 99) / 10
    X["of40"] = 1 * B["s40"] + 11 / 10
    out("== MAM: rebuilt inputs vs exported x (max |diff|; %.15f export resolution 5e-16)")
    for k, v in X.items():
        out(f"  {k:5s} {mx(v, R['x_' + k]):.3e}")
    CHK = ("s10", "s20", "s40", "s100"); INFO = ("flat", "ramp", "s5")
    COLS = ("mama", "fama", "alpha", "period", "phase")
    TOL = {"mama": 1e-9, "fama": 1e-9, "alpha": 1e-9, "period": 1e-9, "phase": 1e-8}
    V = {"MA05": (1 / 2, 1 / 20), "MA03": (3 / 10, 1 / 10)}
    model = {}
    nfail = 0; nreal = 0
    for v, (FL, SL) in V.items():
        out(f"\n== MAM {v}: trace (all rows) checked / INFO; tol 1e-9 (phase 1e-8)")
        for k in CHK + INFO + ("sc40", "of40"):
            model[(v, k)] = mama(X[k], FL, SL)
        for k in CHK + INFO:
            line = []
            for q in COLS:
                d = mx(R[f"{q}_{v}_{k}"], model[(v, k)][q])
                checked = k in CHK or (k == "s5" and q == "period")
                if checked:
                    nreal += 1; ok = d <= TOL[q]; nfail += (not ok)
                    line.append(f"{q} {d:.3e}{'' if ok else ' FAIL'}")
                else:
                    line.append(f"{q} {d:.3e} (INFO)")
            out(f"  {k:5s} " + "  ".join(line))
        # bounds, every input
        amin = min(R[f"alpha_{v}_{k}"][5:].min() for k in CHK + INFO + ("sc40", "of40"))
        amax = max(R[f"alpha_{v}_{k}"][5:].max() for k in CHK + INFO + ("sc40", "of40"))
        pmax = max(R[f"period_{v}_{k}"].max() for k in CHK + INFO + ("sc40", "of40"))
        b1 = amin >= SL * (1 - 1e-12) and amax <= FL * (1 + 1e-12); b2 = pmax <= 50 * (1 + 1e-12)
        nreal += 2; nfail += (not b1) + (not b2)
        out(f"  bound alpha rows n>=5 in [{amin!r}, {amax!r}] vs [{SL}, {FL}]: {'PASS' if b1 else 'FAIL'}; Period max {pmax!r}: {'PASS' if b2 else 'FAIL'}")
        # equivariance s40, rows >= 1000
        eq = []
        for cp, (kk, cc) in (("sc40", (10, (0 - 99) / 10)), ("of40", (1, 11 / 10))):
            for q in COLS:
                ref = kk * R[f"{q}_{v}_s40"] + cc if q in ("mama", "fama") else R[f"{q}_{v}_s40"]
                d = mx(R[f"{q}_{v}_{cp}"], ref, 1000); ok = d <= TOL[q]
                nreal += 1; nfail += (not ok)
                eq.append(f"{cp}:{q} {d:.3e}{'' if ok else ' FAIL'}")
        out("  equivariance n>=1000: " + "  ".join(eq))
        # IMP: replay on exported x
        imp = {}
        for k in CHK + INFO + ("sc40", "of40"):
            r = mama(R["x_" + k], FL, SL)
            imp[k] = {q: mx(R[f"{q}_{v}_{k}"], r[q]) for q in COLS}
        worst_chk = max((imp[k][q] / TOL[q], k, q, imp[k][q]) for k in CHK + ("sc40", "of40") for q in COLS)
        worst_info = max((imp[k][q] / TOL[q], k, q, imp[k][q]) for k in INFO for q in COLS)
        out(f"  IMP checked inputs worst {worst_chk[1]}:{worst_chk[2]} {worst_chk[3]!r} (ratio {worst_chk[0]:.3e}); INFO inputs worst {worst_info[1]}:{worst_info[2]} {worst_info[3]!r}")
    out(f"\n  MAM real checks counted here: {nreal}, FAIL {nfail}")
    # controls vs MA05 model
    out("\n== MAM controls vs the MA05 model: max |diff| all rows on checked pairs (ratio to tol); bounds")
    ctrl = {"NCB": dict(dn=68 / 100), "NCH": dict(w1=963 / 10000), "NCF": dict(fama_k=51 / 100), "NC32": dict(f32lit=True), "NCP": dict(pi=ZPI)}
    for c, kw in ctrl.items():
        best = max(((mx(R[f"{q}_{c}_{k}"], model[("MA05", k)][q]) / TOL[q], k, q) for k in CHK + ("s5",) for q in COLS
                    if k in CHK or q == "period"))
        pmax = max(R[f"period_{c}_{k}"].max() for k in CHK + INFO)
        amn = min(R[f"alpha_{c}_{k}"][5:].min() for k in CHK + INFO); amx = max(R[f"alpha_{c}_{k}"][5:].max() for k in CHK + INFO)
        # own-model IMP (must_pass) on every input
        impc = max(mx(R[f"{q}_{c}_{k}"], mama(R["x_" + k], 1 / 2, 1 / 20, **kw)[q]) / TOL[q] for k in CHK for q in COLS)
        out(f"  {c:5s} trace best {best[1]}:{best[2]} ratio {best[0]:.3e}; Period max {pmax!r}; alpha [{amn!r}, {amx!r}]; own-model IMP worst ratio (checked) {impc:.3e}")
    # NCS / NCS2: replay with shared barCount, 14 calls per bar, NCS flat..ramp then NCS2 flat..ramp
    order = [("NCS", k) for k in ("flat", "s5", "s10", "s20", "s40", "s100", "ramp")] + [("NCS2", k) for k in ("flat", "s5", "s10", "s20", "s40", "s100", "ramp")]
    out("\n== MAM NCS / NCS2: vs the MA05 model (detection) and vs the shared-barCount replay (IMP), all rows")
    for j, (c, k) in enumerate(order):
        bc = [14 * i + j + 1 for i in range(NB)]
        rep = mama(R["x_" + k], 1 / 2, 1 / 20, f32lit=True, pi=ZPI, superseded=bc)
        det = max(mx(R[f"{q}_{c}_{k}"], model[("MA05", k)][q]) for q in ("mama", "fama")) if k in CHK else float("nan")
        imp = max(mx(R[f"{q}_{c}_{k}"], rep[q]) for q in ("mama", "fama"))
        out(f"  {c:4s} {k:5s} vs MA05 model {det:.6e}   replay IMP {imp:.3e}")
    # must_fail
    mf = max(mx(R[f"{q}_MA05_{k}"], mama(R["x_" + k], 1 / 2, 1 / 20, w1=963 / 10000)[q]) for k in CHK for q in COLS)
    out(f"  must_fail MA05 replayed with NCH model: {mf!r}")

    # ======================================================== FRAMA
    R = load("GEN_FRA_raw_run1.csv")
    X = dict(B)
    for T in ("ramp", "s5", "s10", "s20", "s40", "s100"):
        X[T + "B"] = B[T]
    X["sc40B"] = 10 * B["s40"] + (0 - 99) / 10
    X["of40B"] = 1 * B["s40"] + 11 / 10
    HL = {k: (X[k], X[k]) for k in ("flat", "ramp", "s5", "s10", "s20", "s40", "s100")}
    for k in ("rampB", "s5B", "s10B", "s20B", "s40B", "s100B"):
        HL[k] = (X[k] + HB, X[k] - HB)
    HL["sc40B"] = (10 * (B["s40"] + HB) + (0 - 99) / 10, 10 * (B["s40"] - HB) + (0 - 99) / 10)
    HL["of40B"] = (1 * (B["s40"] + HB) + 11 / 10, 1 * (B["s40"] - HB) + 11 / 10)
    out("\n== FRA: rebuilt inputs vs exported x / xh / xl")
    for k, v in X.items():
        s = f"  {k:6s} x {mx(v, R['x_' + k]):.3e}"
        if "xh_" + k in R:
            s += f"  xh {mx(HL[k][0], R['xh_' + k]):.3e}  xl {mx(HL[k][1], R['xl_' + k]):.3e}"
        out(s)
    PT = ("flat", "ramp", "s5", "s10", "s20", "s40", "s100"); BD = ("rampB", "s5B", "s10B", "s20B", "s40B", "s100B")
    ALLI = PT + BD
    CF = ("out", "dim", "alpha")
    fm = {}; nreal = 0; nfail = 0
    for v, N in (("FR16", 16), ("FR32", 32)):
        out(f"\n== FRA {v}: trace all rows, tol 1e-10")
        for k in ALLI + ("sc40B", "of40B"):
            fm[(v, k)] = frama(X[k], *HL[k], N)
        for k in ALLI:
            line = []
            for q in CF:
                d = mx(R[f"{q}_{v}_{k}"], fm[(v, k)][q])
                if k == "flat" and q != "out":
                    line.append(f"{q} {d:.3e} (INFO)")
                else:
                    ok = d <= 1e-10; nreal += 1; nfail += (not ok)
                    line.append(f"{q} {d:.3e}{'' if ok else ' FAIL'}")
            out(f"  {k:6s} " + "  ".join(line))
        ins = ALLI + ("sc40B", "of40B")
        amin = min(R[f"alpha_{v}_{k}"].min() for k in ins); amax = max(R[f"alpha_{v}_{k}"].max() for k in ins)
        dmax = max(R[f"dim_{v}_{k}"].max() for k in ins)
        e46 = math.exp(-4.6)
        hull = max(max(np.max(R[f"out_{v}_{k}"] - np.maximum.accumulate(R["x_" + k])), np.max(np.minimum.accumulate(R["x_" + k]) - R[f"out_{v}_{k}"])) for k in ins)
        b = [amin >= e46 * (1 - 1e-12) and amax <= 1 + 1e-12, dmax <= 2 * (1 + 1e-12), hull <= 1e-15]
        nreal += 3; nfail += sum(not t for t in b)
        out(f"  bounds: alpha [{amin!r}, {amax!r}] (exp(-4.6) = {e46!r}) {'PASS' if b[0] else 'FAIL'}; dim max {dmax!r} {'PASS' if b[1] else 'FAIL'}; hull excess {hull:.3e} {'PASS' if b[2] else 'FAIL'}")
        ra = mx(R[f"out_{v}_ramp"], R["x_ramp"])
        r1 = SLP * (N / 2 - 1) + 2 * HB; r3 = SLP * (N - 1) + 2 * HB
        D = math.log2(4 * r1 / r3); a = math.exp(-4.6 * (D - 1)); lag = (1 - a) / a
        lagm = float(np.mean((R["x_rampB"] - R[f"out_{v}_rampB"])[-100:]) / SLP)
        fl = mx(R[f"out_{v}_flat"], np.full(NB, LVL))
        ka = [ra <= 1e-12, abs(lagm - lag) <= 1e-6, fl <= 1e-12]
        nreal += 3; nfail += sum(not t for t in ka)
        out(f"  known answers: point ramp |out - x| {ra:.3e} {'PASS' if ka[0] else 'FAIL'}; band ramp lag {lagm!r} vs {lag!r} (diff {abs(lagm-lag):.3e}) "
            f"{'PASS' if ka[1] else 'FAIL'}; flat |out - 1.1| {fl:.3e} {'PASS' if ka[2] else 'FAIL'}")
        eq = []
        for cp, (kk, cc) in (("sc40B", (10, (0 - 99) / 10)), ("of40B", (1, 11 / 10))):
            for q in CF:
                ref = kk * R[f"{q}_{v}_s40B"] + cc if q == "out" else R[f"{q}_{v}_s40B"]
                d = mx(R[f"{q}_{v}_{cp}"], ref); ok = d <= 1e-10; nreal += 1; nfail += (not ok)
                eq.append(f"{cp}:{q} {d:.3e}{'' if ok else ' FAIL'}")
        out("  equivariance (all rows): " + "  ".join(eq))
        imp = max((mx(R[f"{q}_{v}_{k}"], frama(R["x_" + k], R.get("xh_" + k, R["x_" + k]), R.get("xl_" + k, R["x_" + k]), N)[q]), k, q)
                  for k in ins for q in CF if not (k == "flat" and q != "out"))
        out(f"  IMP (exported x / xh / xl, all inputs incl. copies) worst {imp[1]}:{imp[2]} {imp[0]!r}")
    out(f"\n  FRA real checks counted here: {nreal}, FAIL {nfail}")
    out("\n== FRA controls vs the FR16 model: best trace ratio (tol 1e-10); bounds; own-model IMP")
    fctrl = {"NCE": dict(k=461 / 100), "NCN": "N18", "NC32": dict(k=f32(4.6), lo=f32(0.01)), "NCT": dict(startup="old")}
    for c, kw in fctrl.items():
        best = max((mx(R[f"{q}_{c}_{k}"], fm[("FR16", k)][q]) / 1e-10, k, q) for k in ALLI for q in CF if not (k == "flat" and q != "out"))
        amn = min(R[f"alpha_{c}_{k}"].min() for k in ALLI)
        if kw == "N18":
            own = lambda x, H, L: frama(x, H, L, 18)
        else:
            own = lambda x, H, L, kw=kw: frama(x, H, L, 16, **kw)
        impc = max(mx(R[f"{q}_{c}_{k}"], own(R["x_" + k], R.get("xh_" + k, R["x_" + k]), R.get("xl_" + k, R["x_" + k]))[q]) for k in ALLI for q in CF
                   if not (k == "flat" and q != "out"))
        out(f"  {c:5s} best {best[1]}:{best[2]} ratio {best[0]:.3e}; alpha min {amn!r}; own-model IMP {impc:.3e}")
    GORD = ("flat", "s5", "s10", "s20", "s40", "s100", "ramp") + BD     # the generator's call order (GEN_FRA_FRAMA.c lines 591-616)
    calls = [(R["x_" + k], R.get("xh_" + k, R["x_" + k]), R.get("xl_" + k, R["x_" + k])) for k in GORD] * 2
    outs = frama_superseded_shared(calls, 8)
    out("  NCS / NCS2 (out): vs FR16 model, all rows | rows >= 1000 | shared-state replay IMP (generator order)")
    for j, k in enumerate(GORD):
        for c, o in (("NCS", outs[j]), ("NCS2", outs[j + len(GORD)])):
            out(f"    {c:4s} {k:6s} {mx(R[f'out_{c}_{k}'], fm[('FR16', k)]['out']):.6e} | {mx(R[f'out_{c}_{k}'], fm[('FR16', k)]['out'], 1000):.6e} | {mx(R[f'out_{c}_{k}'], o):.3e}")
    out("  other required kinds (FR16 reference values: band ramp lag 34.05274879969143, flat 1.1, hull, alpha >= exp(-4.6)):")
    lag16 = 34.05274879969143
    for c in ("NCE", "NCN", "NCT", "NC32", "NCS", "NCS2"):
        lagc = float(np.mean((R["x_rampB"] - R[f"out_{c}_rampB"])[-100:]) / SLP)
        flc = mx(R[f"out_{c}_flat"], np.full(NB, LVL))
        hl = max(max(np.max(R[f"out_{c}_{k}"] - np.maximum.accumulate(R["x_" + k])), np.max(np.minimum.accumulate(R["x_" + k]) - R[f"out_{c}_{k}"])) for k in ALLI)
        amn = min(R[f"alpha_{c}_{k}"].min() for k in ALLI) if f"alpha_{c}_flat" in R else float("nan")
        out(f"    {c:5s} lag {lagc!r} (diff {abs(lagc-lag16):.3e}, ratio {abs(lagc-lag16)/1e-6:.3e}); flat {flc:.3e} (ratio {flc/1e-12:.3e}); hull excess {hl:.3e}; alpha min {amn!r} (below exp(-4.6) by {math.exp(-4.6)-amn:.3e})")
    mf = max(mx(R[f"{q}_FR16_{k}"], frama(R["x_" + k], R.get("xh_" + k, R["x_" + k]), R.get("xl_" + k, R["x_" + k]), 16, k=461 / 100)[q]) for k in ALLI for q in CF)
    out(f"  must_fail FR16 replayed with NCE model: {mf!r}")
