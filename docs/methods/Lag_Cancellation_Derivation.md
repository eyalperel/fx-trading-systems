# Removing Lag Without Restoring Noise

**Method note.** Derived during the Week 14 review, session 1, 2026-08-31.
Applies to any filter claiming low or zero lag, not only to UltimateSmoother.

Written to be read from the top by someone who has forgotten all of it.

---

## 1. The problem

SuperSmoother2Pole at Period 20 smooths well, but its output trails price by
**4.04 bars**. That is the whole point of the trade-off: to remove fast noise you
must average over several bars, and averaging over past bars means the answer you
report is about the past.

The question this note answers: **can the lag be removed without giving the noise
back?**

---

## 2. The naive approach — add back part of the gap

Price is at 13 right now. The smoother's output says 9, because it is showing
where price was a few bars ago.

The difference between them is a measure of how far behind the filter is:

    gap = price - smooth = 13 - 9 = 4

So an obvious idea: add some of that gap back.

    output = smooth + alpha * (price - smooth)

### It works on a ramp

Price rising 1 per bar. smooth = 9, price = 13, alpha = 1:

    output = 9 + 1 * (13 - 9) = 13

Lag gone.

### It fails on noise

Feed the fast wiggle +1, -1, +1, -1. SuperSmoother rejects this exactly, so
smooth = 0 while price = +1, and alpha = 1:

    output = 0 + 1 * (1 - 0) = 1

All the noise is back.

| filter | ramp | fast wiggle |
|---|---|---|
| SuperSmoother alone | 4 bars behind | 0% noise |
| correction, alpha = 1 | 0 bars behind | 100% noise |
| correction, alpha = 0.5 | 2 bars behind | 50% noise |

### Why it fails

Expand the formula:

    output = smooth + alpha*price - alpha*smooth
           = alpha*price + (1 - alpha)*smooth

**It is just a blend of price and the smoothed line.** A blend takes both
ingredients in the same proportion. Any lag you recover arrives with proportional
noise. There is no value of alpha that escapes this.

### The blocker, stated precisely

`price - smooth` contains **the lag AND the noise the filter removed, summed into
one number**. No single coefficient can add back one part without the other.

The problem is not that a gap must exist. It is that **the gap cannot be split**.

> This is the same conflation as the Week 5 SNR metric, which called
> `price - indicator` "noise" when it is lag and noise combined. See
> `docs/Week14_Session1_Handoff.md` section 4.1.

### This is what the Week 5 file does

`indicators/ehlers/UltimateSmoother_W5_Superseded.c` implements exactly this:

    SS[0]    = SuperSmoother(Price)
    Residual = Price[0] - SS[0]
    US[0]    = SS[0] + gamma * (Residual + US[1] - SS[1])

with `gamma = 0.0395` at Period 20 — which is numerically identical to `c0`,
SuperSmoother's own input coefficient. It removes 0.166 bars of the 4.04, or
4.1%, and was recorded as "near-zero-lag."

---

## 3. What a solution needs

To remove lag without restoring noise you need to add back something containing
the lag but **not** the noise. A fraction of the residual will not do, because
that quantity has both mixed in.

So the fast and slow parts of price have to be available **separately**, each
computed by its own filter:

    price = slow part + fast part

- a **low-pass** filter gives the slow part (passes slow, blocks fast)
- a **high-pass** filter gives the fast part (passes fast, blocks slow)

---

## 4. The published approach

Ehlers' UltimateSmoother, implemented in `indicators/ehlers/UltimateSmootherE.c`:

    UltimateSmoother = Price - HighPass(Price)

Take price, work out its fast component with a dedicated filter, subtract it.
**Smoothing by subtraction rather than by averaging.**

Nothing is being split. The fast part was never fused with anything — it was
computed on its own from the start.

---

## 5. Finding that structure in the published formula

Ehlers publishes the filter as one opaque line:

    US[t] = (1-c1)*P[t] + (2*c1-c2)*P[t-1] - (c1+c3)*P[t-2]
          + c2*US[t-1] + c3*US[t-2]

Same shape as every filter in this library — weights on past prices, weights on
past outputs. Nothing in it says what the filter is.

### The trick: ask what it throws away

Instead of "what is this filter?", ask **"what does it discard?"**

    discarded = Price - US

If we can name that, we know the filter, because `US = Price - discarded`.

### Working it out, Period = 20

Building blocks, same as SuperSmoother:

    a1 = exp(-sqrt(2)*pi / 20) = exp(-0.222144) = 0.800881
    b1 = 2 * a1 * cos(sqrt(2)*pi / 20)
       = 2 * 0.800881 * 0.975435
       = 1.562244

Named coefficients:

    c2 = b1              = 1.562244
    c3 = -a1*a1          = -0.641410
    c1 = (1 + c2 - c3)/4 = 3.203654 / 4 = 0.800914

Price-side weights of US:

    1 - c1     = 1 - 0.800914           =  0.199086
    2*c1 - c2  = 1.601828 - 1.562244    =  0.039584
    -(c1 + c3) = -(0.800914 - 0.641410) = -0.159504

Subtract these from the weights that would reproduce price unchanged:

    weights reproducing price :   1.0000, -1.5622,  0.6413
    price-side weights of US  :   0.1991,  0.0395, -0.1596
                                  ------------------------
    difference (discarded)    :   0.8009, -1.6018,  0.8009

### Normalise

Divide the row by its first element, 0.8009:

    0.8009 / 0.8009 = +1
   -1.6018 / 0.8009 = -2
    0.8009 / 0.8009 = +1

The discarded part has weights in the ratio **1, -2, 1**.

That is the standard numerator of a **2-pole high-pass filter**. So:

    UltimateSmoother = Price - HighPass(Price)

confirmed from the coefficients.

### A note on normalising

Dividing by the first element makes it 1 by construction — that part is
guaranteed and is not the finding. What is not guaranteed is that the other two
come out as exactly -2 and exactly 1.

The choice of divisor does not matter. Dividing by the middle element instead
gives -0.5, 1, -0.5, which is the same filter scaled by -1/2. Scaling every
weight by a constant scales the output by that constant, so a zero output stays
zero. The property lives in the **ratios**, not in any particular scaling.

---

## 6. Why 1, -2, 1 gives exactly zero lag

Apply the pattern to three consecutive bars:

    1*P[t] - 2*P[t-1] + 1*P[t-2]

Regroup as two subtractions:

    = (P[t] - P[t-1]) - (P[t-1] - P[t-2])

The first bracket is the change from last bar to now. The second is the change
over the bar before that. So the expression is **the change in price minus the
previous change in price — the change in the change.**

That is a discrete **second derivative**.

### On a straight line it is exactly zero

A straight line rises by the same amount every bar, so the two changes are equal
and subtracting them gives zero:

    ramp 10, 11, 12:     (12 - 11) - (11 - 10) = 1 - 1 = 0
    ramp 100, 105, 110:  (110 - 105) - (105 - 100) = 5 - 5 = 0

This holds for **any** straight line, of any slope, at any level. That is the
definition of a straight line: constant change per step.

### Therefore

On a ramp the high-pass outputs exactly nothing, so:

    US = Price - 0 = Price

**Lag is exactly 0.0000 bars by construction.** Not a good approximation — an
algebraic identity. It is why the measurement reads 0.0000 rather than 0.02.

### It holds at every Period

The discarded row was `0.8009, -1.6018, 0.8009`, and 0.8009 is `a1`, which
depends on Period. A different Period gives a different scale — say
`0.75, -1.50, 0.75` — but normalising still gives 1, -2, 1. The scale changes
with Period; the ratio does not. The zero-lag-on-a-ramp property is structural,
not tuned.

---

## 7. The limit of the claim

**A ramp is a straight line. Real price is not.**

The second derivative of a straight line is zero. The second derivative of a
curve is not. So the moment price bends — a turn, a cycle peak, a trend change —
the high-pass produces output and the filter subtracts something real.

> **What has been established:** UltimateSmootherE has exactly zero lag on inputs
> that are straight lines.
>
> **What has NOT been established:** anything about its lag on a curve, a turn, or
> a cycle. That is a separate question. Nothing in this repo currently answers it.

Any future claim that this filter is "zero lag" without qualifying the input is
overstating the measurement.

---

## 8. How to measure lag properly

### The method

Feed the filter a **synthetic ramp** with slope exactly 1 per bar. A filter with
unity DC gain tracks a ramp with a constant offset once settled. With slope 1,
that offset in value **is** the lag in bars.

Instrument: `strategies/tests/Test_USLag.c`. It uses no market data — the asset
supplies only a bar clock — so it runs on a fresh clone with no CSV dependency.

### Why not detrended cross-correlation

Week 5 specified detrended cross-correlation. **It cannot work here.**
Detrending removes the trend, and a ramp consists of nothing but trend, so
detrending removes the entire signal. A correlation computed on the remainder
reports near-zero lag for filters that plainly lag.

That is the failure mode this review exists to catch: **a check that could not
have failed.** Before trusting any measurement, test the instrument on filters
whose answer you already know.

### Known-answer controls

    EMA, alpha = 0.2      lag 4.00 bars (independently computed)
    SuperSmoother2Pole    lag 4.04 bars (independently computed)

If the instrument returns these, it works.

---

## 9. Verification record

`Test_USLag.c` run 2026-08-31, output at `C:\Zorro\Data\US_Lag.csv`, bar 2697.
Lag is `ramp - output`:

| filter | Zorro (lite-C) | independent scipy | agreement |
|---|---|---|---|
| UltimateSmootherE | 0.000000 | 0.000000 | exact |
| UltimateSmoother_W5_Superseded | 3.872503 | 3.8725 | 4 dp |
| SuperSmoother2Pole | 4.038670 | 4.0387 | 4 dp |

Two independent implementations — Zorro lite-C on a live bar clock, scipy on a
synthetic ramp — agree to four decimals on all three filters. This confirms the
instrument, the coefficients in all three `.c` files, and the measured values
simultaneously.

Note that `usE` reads exactly 2697.000000 against a ramp value of 2697, not
2696.9998. The algebraic exactness is visible in the raw output.

**Caveat:** the CSV is written to the Zorro install directory and is not tracked.
See GAP-1.10.

---

## 10. Summary

1. Lag cannot be removed by adding back a fraction of `price - smooth`, because
   that residual contains lag and noise summed together and no scalar splits them.
2. It can be removed by computing the fast component separately with a high-pass
   filter and subtracting it.
3. A 2-pole high-pass has numerator ratio 1, -2, 1, which is a discrete second
   derivative and annihilates straight lines exactly.
4. Hence exactly 0.0000 bars of lag on a ramp, at every Period, by construction.
5. **On straight lines only.** Behaviour on curves is unmeasured.
6. Measure lag with a ramp, never with detrended cross-correlation, and always
   test the instrument against filters whose lag you already know.
