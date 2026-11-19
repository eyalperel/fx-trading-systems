"""Laguerre RSI source review model (planning chat, 2026-11-19).

Reproduces every (b) number in docs/harness/LAGUERRERSI_SOURCE_REVIEW.md.
Float64, independent of the harness tooling. Run: python docs/harness/LAGUERRERSI_REVIEW_MODEL.py

src()   = Ehlers, Cybernetic Analysis (2004) Fig. 14.8 (p. 221) as printed:
          all histories start at 0, RSI(0), RSI held when CU + CD = 0.
cfile() = indicators/ehlers/LaguerreRSI.c before the review (mtime 2026-08-21):
          first call with Close > 0 sets L0..L3 (and their [1]) to Close, skips the
          computation and returns 0.5; CU + CD == 0 returns a held value starting at 0.5.
          seeded=False models a second instance (file static lr_init already 1).
"""
import numpy as np


def _step(c, g, p):
    L0 = (1 - g) * c + g * p[0]
    L1 = -g * L0 + p[0] + g * p[1]
    L2 = -g * L1 + p[1] + g * p[2]
    L3 = -g * L2 + p[2] + g * p[3]
    cu = cd = 0.0
    for a, b in ((L0, L1), (L1, L2), (L2, L3)):
        if a >= b:
            cu += a - b
        else:
            cd += b - a
    return [L0, L1, L2, L3], cu, cd


def src(x, g, hold0=0.0):
    L = [0.0] * 4
    rsi = hold0
    out, Ls, den = [], [], []
    for c in x:
        L, cu, cd = _step(c, g, L)
        if cu + cd != 0:
            rsi = cu / (cu + cd)
        out.append(rsi)
        Ls.append(L)
        den.append(cu + cd)
    return np.array(out), np.array(Ls), np.array(den)


def cfile(x, g, seeded=True, prev=0.5):
    L = [0.0] * 4
    out = []
    first = seeded
    for c in x:
        if first and c > 0:
            L = [c] * 4
            first = False
            out.append(0.5)
            continue
        L, cu, cd = _step(c, g, L)
        if cu + cd == 0:
            out.append(prev)
            continue
        prev = cu / (cu + cd)
        out.append(prev)
    return np.array(out)


if __name__ == "__main__":
    N = 3000
    n = np.arange(N)
    lvl, amp, s = 1.1, 0.01, 1e-4
    for g in (0.5, 0.7, 0.8):
        print(f"gamma = {g}")
        for T in (5, 10, 20, 40, 100):
            x = lvl + amp * np.sin(2 * np.pi * n / T)
            a, _, d = src(x, g)
            dif = np.abs(a - cfile(x, g))
            last = int(np.max(np.where(dif > 1e-12)[0]))
            r = a[200:]
            print(f"  T={T:3d} startup max {dif.max()!r} last>1e-12 row {last} "
                  f"min {r.min()!r} max {r.max()!r} pinned {np.mean((r == 0) | (r == 1))!r} "
                  f"min(CU+CD)/amp {d[200:].min() / amp!r}")
        x = lvl + s * n
        a, L, _ = src(x, g)
        print(f"  rising ramp: last row RSI != 1: {int(np.max(np.where(a != 1.0)[0]))}; "
              f"lag L0 {np.mean((x - L[:, 0])[-100:]) / s!r}, L3 {np.mean((x - L[:, 3])[-100:]) / s!r}, "
              f"theory L3 {g / (1 - g) + 3 * (1 + g) / (1 - g)!r}")
        a, _, _ = src(lvl - s * n, g)
        print(f"  falling ramp: last row RSI != 0: {int(np.max(np.where(a != 0.0)[0]))}")
        x = np.full(N, lvl)
        a, Ls, d = src(x, g)
        z = np.where(d == 0)[0]
        print(f"  flat: first row CU+CD == 0: {int(z.min()) if len(z) else None}"
              f"{'' if not len(z) else f', RSI held at {a[z.min()]!r}'}; "
              f".c flat outputs {np.unique(cfile(x, g))}")
        e = np.abs(Ls[:, 3] - lvl) / lvl
        print(f"  flat: L3 zero-start rel err < 1e-12 from row {int(np.where(e < 1e-12)[0].min())}")
