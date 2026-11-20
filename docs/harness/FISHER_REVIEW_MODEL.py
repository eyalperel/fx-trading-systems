"""Fisher Transform source review -- independent float64 model.

Reproduces every (b) number in docs/harness/FISHER_SOURCE_REVIEW.md.
Independent of the harness tooling (does not import analysis/harness).

Sources (a):
  A  Ehlers, "Using The Fisher Transform", TASC V.20:11 (2002) pp. 40-42, Fig. 5 (p. 41).
  B  Ehlers, Cybernetic Analysis for Stocks and Futures (Wiley 2004), ch. 1, Fig. 1.7 (p. 7).

Run: python docs/harness/FISHER_REVIEW_MODEL.py
"""
import math
import struct

N = 3000
LEVEL, AMP, SLOPE = 1.1, 0.01, 1e-4
ROW0 = 200                      # rows >= ROW0 are past every start-up effect
PERIODS = (5, 10, 20, 40, 100)
LENS = (10, 20)


def f32(v):
    return struct.unpack("f", struct.pack("f", v))[0]


SRC_A = dict(a=.33, b=.67, thr=.99, cl=.999, k=.5)       # Fig. 5, TASC 2002
SRC_B = dict(a=.5, b=.5, thr=.9999, cl=.9999, k=.25)     # Fig. 1.7, book 2004
CODE = dict(a=f32(.33), b=f32(.67), thr=f32(.99), cl=f32(.999), k=.5)  # FisherTransform.c literals (gotchas 9d.1)


def window(x, n, L):
    """Highest/Lowest over the last L values incl. x[n]; Zorro series() pads the
    history with x[0] (gotchas 9d.6) before L values exist."""
    w = x[max(0, n - L + 1):n + 1]
    if len(w) < L:
        w = w + [x[0]] * (L - len(w))
    return max(w), min(w)


class Fisher:
    """One instance. state=None -> own state; pass a shared dict to model file statics."""

    def __init__(self, L, p, state=None):
        self.L, self.p = L, p
        self.s = state if state is not None else {"v": 0.0, "f": 0.0}

    def step(self, x, n):
        p, s = self.p, self.s
        hi, lo = window(x, n, self.L)
        rng = hi - lo
        raw = 2 * ((x[n] - lo) / rng - .5) if rng > 0 else 0.0   # guard: F-4 (ours)
        pre = p["a"] * raw + p["b"] * s["v"]
        v = pre
        if v > p["thr"]:
            v = p["cl"]
        if v < -p["thr"]:
            v = -p["cl"]
        trig = s["f"]
        f = p["k"] * math.log((1 + v) / (1 - v)) + .5 * s["f"]
        s["v"], s["f"] = v, f
        return dict(raw=raw, pre=pre, v=v, f=f, trig=trig, rng=rng)


def run(x, L, p):
    inst = Fisher(L, p)
    return [inst.step(x, n) for n in range(len(x))]


def sine(T):
    return [LEVEL + AMP * math.sin(2 * math.pi * n / T) for n in range(N)]


def main():
    print("== Exact bounds (b)")
    print("A: |Fish| < 2*atanh(.999) = ln(1999) =", repr(math.log(1999)))
    print("B: |Fish| < atanh(.9999) = ln(19999)/2 =", repr(.5 * math.log(19999)))
    print("Fish jump if the A clamp flips at .99: atanh(.999)-atanh(.99) =", repr(math.atanh(.999) - math.atanh(.99)))
    print("A pre-clamp max: .33 + .67*.999 =", repr(.33 + .67 * .999))

    print("\n== Memory (b)")
    print(".67^n < 1e-12 from n =", repr(math.log(1e-12) / math.log(.67)))
    print(".5^n  < 1e-12 from n =", repr(math.log(1e-12) / math.log(.5)))

    print("\n== Float32 literals in FisherTransform.c (b)")
    for c in (.33, .67, .99, .999, .5):
        print(f"  {c}: float32 {f32(c)!r}  rel err {(f32(c) - c) / c:.3e}")
    print("  float32(.33)+float32(.67) - 1 =", repr(f32(.33) + f32(.67) - 1))

    print("\n== Sines, rows >= %d, source A (Fish range; clamp share; min rng/amp; min |pre -/+ .99|) | B range; max|A-B|; max|code-A|" % ROW0)
    for L in LENS:
        for T in PERIODS:
            x = sine(T)
            a = run(x, L, SRC_A)[ROW0:]
            b = run(x, L, SRC_B)[ROW0:]
            c = run(x, L, CODE)[ROW0:]
            fmin = min(r["f"] for r in a)
            fmax = max(r["f"] for r in a)
            share = sum(abs(r["pre"]) > .99 for r in a) / len(a)
            mrng = min(r["rng"] for r in a) / AMP
            dthr = min(min(abs(r["pre"] - .99), abs(r["pre"] + .99)) for r in a)
            bmin = min(r["f"] for r in b)
            bmax = max(r["f"] for r in b)
            dab = max(abs(p["f"] - q["f"]) for p, q in zip(a, b))
            dca = max(abs(p["f"] - q["f"]) for p, q in zip(c, a))
            print(f"  L{L} T{T:3d}: {fmin:+.6f}..{fmax:+.6f}; {share:.2f}; {mrng:.6f}; {dthr:.3e} | "
                  f"{bmin:+.6f}..{bmax:+.6f}; {dab:.6f}; {dca:.3e}")

    print("\n== Ramps and flat, L10, source A (b)")
    for name, x in (("rampup", [LEVEL + SLOPE * n for n in range(N)]),
                    ("rampdn", [LEVEL - SLOPE * n for n in range(N)])):
        o = run(x, 10, SRC_A)
        last_raw = max((i for i, r in enumerate(o) if abs(r["raw"]) != 1.0), default=None)
        last_v = max((i for i, r in enumerate(o) if abs(r["v"]) != .999), default=None)
        lim = math.log(1999) * (1 if name == "rampup" else -1)
        last_f = max((i for i, r in enumerate(o) if abs(r["f"] - lim) > 1e-12), default=None)
        print(f"  {name}: raw = +-1 exactly after row {last_raw}; v = +-.999 exactly after row {last_v}; "
              f"|Fish - ln(1999)| <= 1e-12 after row {last_f}; Fish[-1] = {o[-1]['f']!r}")
    o = run([LEVEL] * N, 10, SRC_A)
    print(f"  flat: guard fires on {sum(r['rng'] == 0 for r in o)}/{N} rows; raw, v, Fish all 0: "
          f"{all(r['raw'] == 0 and r['v'] == 0 and r['f'] == 0 for r in o)}")

    print("\n== F-1 shared statics: two instances (L10, L20) on one sine, one shared state (b)")
    for T in (20, 40, 100):
        x = sine(T)
        shared = {"v": 0.0, "f": 0.0}
        i10, i20 = Fisher(10, CODE, shared), Fisher(20, CODE, shared)
        out10 = []
        for n in range(N):
            out10.append(i10.step(x, n)["f"])
            i20.step(x, n)
        own = [r["f"] for r in run(x, 10, CODE)]
        print(f"  T{T:3d}: max |shared - own| (L10, rows >= {ROW0}) = "
              f"{max(abs(p - q) for p, q in zip(out10[ROW0:], own[ROW0:])):.6f}")

    print("\n== Start-up, source A vs EFS-style skip (first L-1 bars not computed), L10, max |diff| rows < 200 (INFO, F-5)")
    for T in PERIODS:
        x = sine(T)
        z = [r["f"] for r in run(x, 10, SRC_A)]
        inst = Fisher(10, SRC_A)
        e = []
        for n in range(N):
            if n < 9:
                e.append(0.0)
            else:
                e.append(inst.step(x, n)["f"])
        d = [abs(p - q) for p, q in zip(z, e)]
        last = max((i for i, v in enumerate(d) if v > 1e-12), default=None)
        print(f"  T{T:3d}: max {max(d[:ROW0]):.6f}; last row > 1e-12: {last}")


if __name__ == "__main__":
    main()
