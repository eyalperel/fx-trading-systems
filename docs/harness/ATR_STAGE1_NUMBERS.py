"""ATR stage 1 numbers (planning chat, 2026-11-21). Source of every (b) number in
docs/harness/ATR_STAGE1_PROMPT.md. float64, independent of the harness tooling.

Decisions S1-S8 (user, 2026-11-21). Inputs: level 1.1, amplitude 0.01, slope 1e-4,
3000 bars. Point bars H = L = C = x. Band bars H = x + h, L = x - h, C = x, h = 2/10000.
Copies: sc = 10x - 9.9 (H, L mapped the same way: h -> 10h), of = x + 1.1.
Model = MetaQuotes ATR.mq4 (review §2), per instance: row 0 TR = 0, ATR = 0;
rows 1..P-1 ATR = 0; row P = mean TR[1..P]; then ATR[r] = ATR[r-1] + (TR[r] - TR[r-P])/P.
"""
import numpy as np

N, LEVEL, AMP, SLOPE = 3000, 1.1, 0.01, 1e-4
HB = 2 / 10000
SEED = 20261121
TOL_TRACE = 1e-12
COND_BOUND = TOL_TRACE / 10
n = np.arange(N)

BASE = {"flat": np.full(N, LEVEL), "ramp": LEVEL + SLOPE * n, "rampdn": LEVEL - SLOPE * n}
for T in (5, 10, 20, 40, 100):
    BASE[f"s{T}"] = LEVEL + AMP * np.sin(2 * np.pi * n / T)


def make_inputs():
    """name -> (H, L, C). Point: all base inputs; band: suffix B on all base inputs."""
    d = {}
    for k, x in BASE.items():
        d[k] = (x, x, x)
        d[k + "B"] = (x + HB, x - HB, x)
    x = BASE["s40"]
    d["sc40B"] = (10 * x - 9.9 + 10 * HB, 10 * x - 9.9 - 10 * HB, 10 * x - 9.9)
    d["of40B"] = (x + 1.1 + HB, x + 1.1 - HB, x + 1.1)
    return d


def true_range(H, L, C):
    tr = np.zeros(len(C))
    for r in range(1, len(C)):
        tr[r] = max(H[r], C[r - 1]) - min(L[r], C[r - 1])
    return tr


def atr_model(H, L, C, P=14, tr_kind="mt4", avg="sma", first="mt4", startup="mt4"):
    """Correct model = defaults. Controls: P=15 (NCW); first='with_tr0' (NC0: row P = mean TR[0..P-1]
    instead of TR[1..P], running update unchanged); avg='wilder' (NCWi); tr_kind='hl' (NCR: TR = H - L); startup='tr' (NCZ: rows < P
    output the running mean of the TRs so far instead of 0)."""
    Nn = len(C)
    if tr_kind == "mt4":
        tr = true_range(H, L, C)
    else:
        tr = np.array(H) - np.array(L)
        tr[0] = 0.0
    a = np.zeros(Nn)
    if first == "with_tr0":
        a[P] = tr[0:P].sum() / P          # off-by-one: first window TR[0..P-1] at row P
        start = P + 1
    else:
        s = 0.0
        for r in range(1, P + 1):
            s += tr[r]
        a[P] = s / P
        start = P + 1
    for r in range(start, Nn):
        if avg == "sma":
            a[r] = a[r - 1] + (tr[r] - tr[r - P]) / P
        else:
            a[r] = (a[r - 1] * (P - 1) + tr[r]) / P
    if startup == "tr":
        for r in range(1, P):
            a[r] = tr[1:r + 1].sum() / r
    return tr, a


def ncs_replay(inputs, names, P=14, order="input_major"):
    """NCS: the correct body with the running ATR value kept in ONE file static (ats_prev) shared by every
    call; TR and the per-instance counter are per-instance series. Two instances per input. order:
    'input_major' = per bar, for each input: inst1, inst2; 'instance_major' = per bar, inst1 over all inputs,
    then inst2 over all inputs. The tooling must recompute this in the GENERATED script's call order."""
    calls = []
    if order == "input_major":
        for k in names:
            calls += [(k, 1), (k, 2)]
    else:
        calls = [(k, 1) for k in names] + [(k, 2) for k in names]
    trs = {k: true_range(*inputs[k]) for k in names}
    out = {c: np.zeros(N) for c in calls}
    prev = 0.0
    for r in range(N):
        for c in calls:
            k = c[0]
            tr = trs[k]
            if r < P:
                v = 0.0
            elif r == P:
                v = tr[1:P + 1].sum() / P
            else:
                v = prev + (tr[r] - tr[r - P]) / P
            out[c][r] = v
            prev = v
    return out


def rounded(H, L, C):
    f = lambda v: np.array([float("%.15f" % t) for t in v])
    return f(H), f(L), f(C)


def main():
    inp = make_inputs()
    names = [k for k in inp if k not in ("sc40B", "of40B")]
    rng = np.random.default_rng(SEED)
    print(f"Inputs ({len(names)} + 2 copies): {', '.join(names)}; copies sc40B, of40B")

    for P in (14, 20):
        tag = f"AT{P}"
        print(f"\n===== {tag}")
        ref = {k: atr_model(*inp[k], P=P) for k in inp}

        # 1 conditioning: 5 draws, u in {-1,0,1} per row, x(1 + 2^-52 u) on C; H, L rebuilt from the perturbed x
        print("1. Conditioning, all rows, 5 draws, max |perturbed - ref| (bound %.0e)" % COND_BOUND)
        worst = {"tr": 0.0, "atr": 0.0}
        for k in names:
            H, L, C = inp[k]
            off_h, off_l = H - C, L - C
            m = {"tr": 0.0, "atr": 0.0}
            for _ in range(5):
                u = rng.integers(-1, 2, N)
                Cp = C * (1 + u * 2.0 ** -52)
                tr, a = atr_model(Cp + off_h, Cp + off_l, Cp, P=P)
                m["tr"] = max(m["tr"], np.abs(tr - ref[k][0]).max())
                m["atr"] = max(m["atr"], np.abs(a - ref[k][1]).max())
            cls = "checked" if max(m.values()) <= COND_BOUND else "INFO"
            worst = {c: max(worst[c], m[c]) for c in m}
            print(f"   {k:8s} tr {m['tr']:.3e}  atr {m['atr']:.3e}  -> {cls}")
        print(f"   max over inputs: tr {worst['tr']:.3e}, atr {worst['atr']:.3e}")

        # 2 known answers
        print("2. Known answers, rows >= P (max |diff|); rows 0..P-1 zero")
        ka = [("flat", 0.0), ("flatB", 2 * HB), ("ramp", SLOPE), ("rampdn", SLOPE),
              ("rampB", 2 * HB), ("rampdnB", 2 * HB)]
        for k, e in ka:
            tr, a = ref[k]
            print(f"   {k:8s} expected {e!r:24s} max diff {np.abs(a[P:] - e).max():.3e}  zero rows {bool((a[:P] == 0).all())}")
        tr, a = ref["s20"]
        print(f"   start-up s20 ATR[{P}] = {a[P]!r} (mean TR[1..{P}])")

        # 3 bounds: ATR >= 0, TR >= H - L, window hull min TR[r-P+1..r] <= ATR <= max
        print("3. Bounds (worst over all inputs): ATR min, TR - (H-L) min, hull violation max (relative)")
        amin, tmin, hull = np.inf, np.inf, 0.0
        for k in inp:
            H, L, C = inp[k]
            tr, a = ref[k]
            amin = min(amin, a.min())
            tmin = min(tmin, (tr[1:] - (H[1:] - L[1:])).min())
            for r in range(P, N):
                w = tr[r - P + 1:r + 1]
                lo, hi = w.min(), w.max()
                v = max(lo - a[r], a[r] - hi, 0.0)
                if v > 0:
                    hull = max(hull, v / max(abs(a[r]), 1e-300))
        print(f"   ATR min {amin:.3e}; TR-(H-L) min {tmin:.3e}; hull rel. violation max {hull:.3e}")

        # 4 equivariance on s40B: sc -> 10x, of -> unchanged, all rows
        b = ref["s40B"]
        sc = ref["sc40B"]
        of = ref["of40B"]
        print("4. Equivariance s40B, all rows: sc |tr - 10 tr|, |atr - 10 atr|; of |tr - tr|, |atr - atr|")
        print(f"   sc tr {np.abs(sc[0] - 10 * b[0]).max():.3e} atr {np.abs(sc[1] - 10 * b[1]).max():.3e}; "
              f"of tr {np.abs(of[0] - b[0]).max():.3e} atr {np.abs(of[1] - b[1]).max():.3e}")

        # 5 IMP estimate: model fed %.15f-rounded H, L, C vs exact
        print("5. IMP estimate (rounded inputs), max |diff| over every input incl. copies")
        imp = {"tr": 0.0, "atr": 0.0}
        for k in inp:
            tr, a = atr_model(*rounded(*inp[k]), P=P)
            imp["tr"] = max(imp["tr"], np.abs(tr - ref[k][0]).max())
            imp["atr"] = max(imp["atr"], np.abs(a - ref[k][1]).max())
        print(f"   tr {imp['tr']:.3e}  atr {imp['atr']:.3e}  (tolerance {TOL_TRACE:.0e}: floor x10 = {10*max(imp.values()):.1e})")

        if P != 14:
            continue
        # 6 control effects vs AT14, max over all rows
        print("6. Control effects vs AT14, max |diff| over all rows (tr | atr)")
        ctl = {"NCW": dict(P=15), "NC0": dict(first="with_tr0"), "NCWi": dict(avg="wilder"),
               "NCR": dict(tr_kind="hl"), "NCZ": dict(startup="tr")}
        for c, kw in ctl.items():
            kw2 = dict(kw); kw2.setdefault("P", 14)
            row, blind, best, last = [], [], (0.0, ""), {}
            for k in names:
                tr, a = atr_model(*inp[k], **kw2)
                dt = np.abs(tr - ref[k][0]).max(); da = np.abs(a - ref[k][1]).max()
                row.append(f"{k}:{da:.2e}")
                if max(dt, da) <= 10 * TOL_TRACE:
                    blind.append(k)
                if da > best[0]:
                    best = (da, k)
                # rows where the control differs (first / last), to tell start-up-only from persistent
                d = np.nonzero(np.abs(a - ref[k][1]) > 10 * TOL_TRACE)[0]
                if len(d):
                    last[k] = (int(d[0]), int(d[-1]))
            print(f"   {c:5s} atr  " + "  ".join(row))
            print(f"         tr max {max(np.abs(atr_model(*inp[k], **kw2)[0] - ref[k][0]).max() for k in names):.3e}; "
                  f"atr max {best[0]:.3e} ({best[1]}, {best[0]/TOL_TRACE:.1e} x tol); blind (<= 10 tol): {blind}")
            spans = sorted(set(last.values()))
            print(f"         differing rows (first, last) over inputs: {spans[:3]}{' ...' if len(spans) > 3 else ''}")
        for order in ("input_major", "instance_major"):
            out = ncs_replay(inp, names, P=14, order=order)
            row, mn = [], np.inf
            for (k, i), v in out.items():
                d = np.abs(v - ref[k][1]).max()
                mn = min(mn, d)
                if i == 2 or k in ("flat", "s20"):
                    row.append(f"{k}#{i}:{d:.2e}")
            print(f"   NCS ({order}) atr  " + "  ".join(row))
            print(f"         min over (instance, input) = {mn:.3e}")


if __name__ == "__main__":
    main()
