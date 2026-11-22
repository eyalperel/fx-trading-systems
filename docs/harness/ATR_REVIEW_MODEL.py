"""ATR source review model (planning chat, 2026-11-21).

Independent float64 model of MetaQuotes' ATR.mq4 (installed copy, MQL4/Indicators,
sha256 prefixes 134da529e0382b89 / c5c680c466e7d87f, identical code), used to compute
every (b) number in docs/harness/ATR_SOURCE_REVIEW.md. Does not read any .c file and
does not use the harness tooling.

Inputs as earlier reviews: level 1.1, sine amplitude 0.01, ramp slope 1e-4, 3000 bars.
Bars: "point" H = L = C = x; "band" H = x + h, L = x - h, C = x, h = 1e-3 (a spec
decision; chosen here only to compute known answers).
"""
import numpy as np

N, LEVEL, AMP, SLOPE, H = 3000, 1.1, 0.01, 1e-4, 1e-3
P = 14


def mt4_atr(high, low, close, period=P):
    """ATR.mq4 OnCalculate, prev_calculated == 0 path, lines 74-100 (a)."""
    n = len(close)
    tr = np.zeros(n)
    atr = np.zeros(n)
    for i in range(1, n):                                   # line 79-80
        tr[i] = max(high[i], close[i - 1]) - min(low[i], close[i - 1])
    first = 0.0
    for i in range(1, period + 1):                          # lines 83-87
        atr[i] = 0.0
        first += tr[i]
    first /= period                                         # line 89
    atr[period] = first                                     # line 90
    for i in range(period + 1, n):                          # lines 96-99
        atr[i] = atr[i - 1] + (tr[i] - tr[i - period]) / period
    return tr, atr


def direct_sma(tr, period=P):
    out = np.zeros(len(tr))
    for i in range(period, len(tr)):
        out[i] = tr[i - period + 1:i + 1].sum() / period
    return out


def wilder_zorro(tr, period=P):
    """Zorro manual ATR(): ATR = (ATR1*(n-1) + TR)/n (a). Zorro's own start-up is not
    stated in the manual; here seeded like MT4 (mean of TR[1..n] at row n) (c)."""
    out = np.zeros(len(tr))
    out[period] = tr[1:period + 1].sum() / period
    for i in range(period + 1, len(tr)):
        out[i] = (out[i - 1] * (period - 1) + tr[i]) / period
    return out


n = np.arange(N)
inputs = {"flat": np.full(N, LEVEL), "ramp": LEVEL + SLOPE * n,
          "rampdn": LEVEL - SLOPE * n}
for T in (5, 10, 20, 40, 100):
    inputs[f"s{T}"] = LEVEL + AMP * np.sin(2 * np.pi * n / T)


def bars(x, kind):
    return (x, x, x) if kind == "point" else (x + H, x - H, x)


def report():
    print("1. Known answers (rows >= P), max |ATR - expected|")
    cases = [("flat", "point", 0.0), ("flat", "band", 2 * H),
             ("ramp", "point", SLOPE), ("rampdn", "point", SLOPE),
             ("ramp", "band", H + max(H, SLOPE)), ("rampdn", "band", H + max(H, SLOPE))]
    for name, kind, exp in cases:
        _, a = mt4_atr(*bars(inputs[name], kind))
        print(f"   {name:6s} {kind:5s} expected {exp:.6e}  max diff {np.abs(a[P:] - exp).max():.3e}"
              f"  rows 1..{P-1} all zero: {bool((a[1:P] == 0).all())}")

    print("2. Start-up: ATR[P] uses TR[1..P]; TR[0] = 0 never enters (a)")
    x = inputs["s20"]
    tr, a = mt4_atr(*bars(x, "point"))
    print(f"   ATR[{P}] = {a[P]:.15e}; mean TR[1..{P}] = {tr[1:P+1].mean():.15e}; "
          f"mean TR[0..{P-1}] = {tr[0:P].mean():.15e}")

    print("3. Running-sum update vs direct 14-bar mean (rounding carried forward), all rows")
    for name in ("ramp", "s5", "s20", "s100"):
        for kind in ("point", "band"):
            tr, a = mt4_atr(*bars(inputs[name], kind))
            d = np.abs(a - direct_sma(tr)).max()
            print(f"   {name:5s} {kind:5s} max |running - direct| = {d:.3e}  (ATR scale {a[P:].mean():.3e})")

    print("4. SMA (MT4) vs Wilder (Zorro ATR form), rows >= 200, max relative diff")
    for name in ("s5", "s10", "s20", "s40", "s100"):
        for kind in ("point", "band"):
            tr, a = mt4_atr(*bars(inputs[name], kind))
            w = wilder_zorro(tr)
            r = np.abs(a[200:] - w[200:]) / a[200:]
            print(f"   {name:5s} {kind:5s} {r.max():.3e}")

    print("5. Window-length error (P = 14 vs 15), point bars, rows >= 200, max |diff|")
    for name in ("s5", "s10", "s20", "s40", "s100"):
        tr, a14 = mt4_atr(*bars(inputs[name], "point"), period=14)
        _, a15 = mt4_atr(*bars(inputs[name], "point"), period=15)
        print(f"   {name:5s} {np.abs(a14[200:] - a15[200:]).max():.3e}  (ATR scale {a14[200:].mean():.3e})")

    print("6. True-range form: max(H,C1)-min(L,C1) vs max(H-L,|H-C1|,|L-C1|), all inputs, band bars")
    worst = 0.0
    for x in inputs.values():
        hh, ll, cc = bars(x, "band")
        for i in range(1, N):
            a = max(hh[i], cc[i-1]) - min(ll[i], cc[i-1])
            b = max(hh[i] - ll[i], abs(hh[i] - cc[i-1]), abs(ll[i] - cc[i-1]))
            worst = max(worst, abs(a - b))
    print(f"   max |diff| = {worst:.3e}")


if __name__ == "__main__":
    report()
