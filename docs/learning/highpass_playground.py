"""
highpass_playground.py — poke at the high-pass filter and watch what it does.

Companion to docs/learning/HighPass_Explained.md.
No dependencies beyond the standard library.  Run it:  python highpass_playground.py

Everything here is small on purpose. Change the numbers and see what breaks.

This file exists because on 2026-09-10 a claim written into two repo documents
("the output decays monotonically after a bend") turned out to be wrong, and
nothing in an hour of reasoning caught it. Running the filter caught it in one
line. Keep it runnable.
"""

import math


# ---------------------------------------------------------------- the filter

def alpha1(period, cascade=0.707):
    """The filter's one tuning number.

    'cascade' is the 0.707 two-pole compensation factor. Set it to 1.0 to see
    what the Week 6 notebook accidentally computed.
    """
    x = cascade * 2.0 * math.pi / period
    return (math.cos(x) + math.sin(x) - 1.0) / math.cos(x)


def highpass(prices, period=48, cascade=0.707):
    """Ehlers' 2-pole high-pass, exactly as HighPassFilter.c computes it."""
    a = alpha1(period, cascade)
    gain = (1.0 - a / 2.0) ** 2          # multiplies the second difference
    fb1 = 2.0 * (1.0 - a)                # feedback on HP[t-1]
    fb2 = -(1.0 - a) ** 2                # feedback on HP[t-2]
    return engine(prices, gain, fb1, fb2)


def broken(prices, period=48):
    """The same filter with one factor of (1-alpha) dropped. It rings."""
    a = alpha1(period)
    return engine(prices, (1.0 - a / 2.0) ** 2, 2.0 * (1.0 - a), -(1.0 - a))


def engine(prices, gain, fb1, fb2):
    """Generic 2-pole engine. Pass your own coefficients to break it on purpose."""
    hp = [0.0] * len(prices)
    for t in range(2, len(prices)):
        second_diff = prices[t] - 2.0 * prices[t - 1] + prices[t - 2]
        hp[t] = gain * second_diff + fb1 * hp[t - 1] + fb2 * hp[t - 2]
    return hp


# ------------------------------------------------------------- test  signals

def tent(up=5, down=5, start=100.0, step=1.0):
    """Up a straight line, down a straight line. One corner, no noise at all."""
    prices = [start + i * step for i in range(up + 1)]
    peak = prices[-1]
    prices += [peak - i * step for i in range(1, down + 1)]
    return prices


def ramp(n=40, start=100.0, step=1.0):
    """A perfectly straight line. The high-pass should output zero throughout."""
    return [start + i * step for i in range(n)]


# ------------------------------------------------------------------ analysis

def poles(fb1, fb2):
    """Roots of z^2 - fb1*z - fb2. Returns (description, magnitude)."""
    disc = fb1 * fb1 + 4.0 * fb2          # fb2 is already negative
    if abs(disc) < 1e-12:
        return "repeated real root -> no sign changes", abs(fb1 / 2.0)
    if disc > 0:
        r1 = (fb1 + math.sqrt(disc)) / 2.0
        r2 = (fb1 - math.sqrt(disc)) / 2.0
        return "two real roots -> no sign changes", max(abs(r1), abs(r2))
    mag = math.sqrt(-fb2)
    angle = math.degrees(math.acos(fb1 / (2.0 * mag)))
    return f"complex roots -> RINGS, cycle {360.0 / angle:.1f} bars", mag


def settling(mag, residue=0.01):
    """Bars for the envelope to shrink to `residue` of its size."""
    return math.log10(residue) / math.log10(mag)


def sign_changes(values, start=0):
    return sum(1 for i in range(start + 1, len(values))
               if values[i] * values[i - 1] < 0)


def at_bars(label, values, bars):
    print(f"  {label:<10}" + "".join(f"{values[b]:>9.2f}" for b in bars))


# ---------------------------------------------------------------------- demo

if __name__ == "__main__":

    print("\n=== 1. STRAIGHT LINE — the filter should do nothing ===")
    p = ramp(8)
    print("  price  " + "".join(f"{v:>8.1f}" for v in p))
    print("  output " + "".join(f"{v:>8.1f}" for v in highpass(p)))
    print("  No bend, no output. This is why a ramp measures 0.0 bars of lag:")
    print("  the filter is switched off, not fast.")

    print("\n=== 2. TENT — one corner, no noise anywhere ===")
    p = tent(up=5, down=120)
    print("  Price climbs +1/bar to a peak at bar 5, then falls -1/bar.")
    print("  The filter fires at bar 6 — one bar AFTER the turn.\n")
    bars = [6, 10, 16, 20, 30, 40, 60, 80]
    print("  bar      " + "".join(f"{b:>9}" for b in bars))
    hp = highpass(p)
    at_bars("output", hp, bars)
    peak = max(range(len(hp)), key=lambda i: abs(hp[i]))
    print(f"\n  It does NOT just fade. It GROWS to {hp[peak]:.2f} at bar {peak},")
    print(f"  which is {abs(hp[peak] / hp[6]):.1f}x the kick it started from at bar 6,")
    print("  and only then decays.")
    print(f"  Sign changes over {len(hp)} bars: {sign_changes(hp, 6)}. It never crosses zero.")

    print("\n=== 3. THE SAME TENT THROUGH A BROKEN FILTER ===")
    print("  (one factor of (1-alpha) dropped from the last feedback term)\n")
    bars = [6, 10, 16, 20, 26, 30, 40, 60]
    print("  bar      " + "".join(f"{b:>9}" for b in bars))
    bad = broken(p)
    at_bars("correct", hp, bars)
    at_bars("broken", bad, bars)
    print(f"\n  Watch the broken row's signs: {sign_changes(bad, 6)} crossings. It swings.")
    print("  The correct row never does. Two completely different filters —")
    print("  and on real price both look like a squiggle around zero, which is")
    print("  why eyeballing a chart cannot tell them apart.")

    print("\n=== 4. WHICH ONE RINGS? — check the poles, no data needed ===")
    a = alpha1(48)
    for name, fb1, fb2 in [
        ("correct", 2 * (1 - a), -(1 - a) ** 2),
        ("broken", 2 * (1 - a), -(1 - a)),
        ("teaching example", 1.0, -0.5),
    ]:
        desc, mag = poles(fb1, fb2)
        print(f"  {name:<18} |root| = {mag:.4f}   {desc}")
    print("  One line of algebra, zero bars of price data.")

    print("\n=== 5. HOW LONG A DISTURBANCE LASTS ===")
    for period in (20, 48, 80):
        b = 1 - alpha1(period)
        print(f"  HPPeriod={period:<4} b={b:.6f}   "
              f"10%: {settling(b, 0.1):5.1f}   1%: {settling(b, 0.01):5.1f}   "
              f"0.1%: {settling(b, 0.001):5.1f} bars")
    print("  1% settling is roughly equal to HPPeriod.")
    print("  Each extra factor of 10 costs the same number of bars again.")
    print("  NOTE: these are measured from the PEAK, not from the bend.")
    print(f"  The peak arrives ~{1 / -math.log(1 - alpha1(48)):.0f} bars after the bend, so add that on.")

    print("\n=== 6. WHAT THE MISSING 0.707 COSTS ===")
    print(f"  correct  alpha at HPPeriod=48: {alpha1(48):.6f}")
    print(f"  notebook alpha at HPPeriod=48: {alpha1(48, cascade=1.0):.6f}")
    print(f"  error: {(alpha1(48, 1.0) / alpha1(48) - 1) * 100:.1f}%")
    print("  The notebook swept a filter the library does not contain.")
    print()
