# Playground Manual

How to use `highpass_playground.py`. Assumes you know Python; explains the
filter side, not the language side.

Companion to `HighPass_Explained.md`, which covers *why* any of this matters.

---

## Running it

**Just look at it** — six worked demos, no arguments:

```
python docs/learning/highpass_playground.py
```

**Ask one question:**

```
python -c "import sys; sys.path.insert(0,'docs/learning'); from highpass_playground import *; print(alpha1(30))"
```

**Work in it** — runs the demos, then leaves you at a prompt with everything
imported. This is the useful one:

```
python -i docs/learning/highpass_playground.py
```

Note: use `python`, not `python3`. On this machine `python3` hits the Microsoft
Store shim and fails.

---

## What's in it

### Filters

| call | does |
|---|---|
| `highpass(prices, period=48, cascade=0.707)` | The real thing. Same arithmetic as `HighPassFilter.c`. |
| `broken(prices, period=48)` | Same filter with one factor of `(1-alpha)` dropped. Rings. Use it to see what a typo costs. |
| `engine(prices, gain, fb1, fb2)` | Raw 2-pole engine. Supply your own coefficients and break it however you like. |

`engine` computes, for each bar:

```
hp[t] = gain * (p[t] - 2*p[t-1] + p[t-2]) + fb1*hp[t-1] + fb2*hp[t-2]
```

The first term is the input side (the second difference). The other two are
feedback. The correct filter uses `gain = (1-a/2)**2`, `fb1 = 2*(1-a)`,
`fb2 = -(1-a)**2` where `a = alpha1(period)`.

### Coefficients

`alpha1(period, cascade=0.707)` — the filter's one tuning number.

Pass `cascade=1.0` to get what the Week 6 notebook computed by accident. At
period 48 that's 0.123024 against the correct 0.088513, a 39% error.

### Test signals

| call | shape |
|---|---|
| `ramp(n, start, step)` | A straight line. The filter should output zero throughout. |
| `tent(up, down, start, step)` | Up a straight line, down a straight line. Exactly one bend. |

`tent(5, 120)` gives a 5-bar climb, a peak at bar 5, then 120 bars down. The
long tail is so you can watch the response settle.

Build your own by hand — they're just lists of floats. Nothing here needs
market data.

### Analysis

| call | returns |
|---|---|
| `poles(fb1, fb2)` | `(description, magnitude)`. Says whether those coefficients ring, and with what cycle length. No data needed. |
| `settling(magnitude, residue=0.01)` | Bars for the envelope to shrink to `residue` of its size. |
| `sign_changes(values, start=0)` | How many times the series crosses zero from `start` onward. |
| `at_bars(label, values, bars)` | Prints selected bars in a row. Display only. |

**`sign_changes` gotcha:** pass `start=6` when looking at a `tent(5, ...)`
response. Bars 0–5 are zeros, and zeros next to a negative count oddly.

**Another:** the crossing count scales with how long you watch. A 60-bar tent
gives 5 crossings, a 120-bar tent gives 11. The ring period is fixed; you're
just seeing more of it.

---

## Experiment 1 — break the filter by one coefficient

Shows that a plausible typo changes the filter's category, and that market data
can't see it.

**Get the correct coefficients:**

```python
>>> a = alpha1(48)
>>> b = 1 - a
>>> gain, fb1, fb2 = (1-a/2)**2, 2*b, -b**2
>>> gain, fb1, fb2
(0.9134451794894659, 1.8229730409501264, -0.8308076770077377)
```

**Check your hand-built version matches the library's.** Don't skip this — if
you skip it and something looks odd later, you won't know whether it's the
change or your setup:

```python
>>> mine = engine(tent(5,60), gain, fb1, fb2)
>>> theirs = highpass(tent(5,60))
>>> max(abs(m-t) for m,t in zip(mine, theirs))
0.0
```

Exactly zero, because both paths do identical arithmetic in identical order.

**Now the typo.** Drop one factor of `(1-alpha)` from the last term: `-b**2`
becomes `-b`.

```python
>>> bad = engine(tent(5,60), gain, fb1, -b)
>>> sign_changes(mine, 6), sign_changes(bad, 6)
(0, 5)
```

Correct filter: never crosses zero. Broken filter: five crossings. One
coefficient.

**Look at the shape:**

```python
>>> [round(bad[i],2) for i in range(6, 40, 2)]
[-1.83, -4.41, -5.09, -3.98, -1.74, 0.7, 2.49, 3.16, 2.67, 1.38,
 -0.15, -1.37, -1.93, -1.76, -1.03, -0.09, 0.72]
```

A decaying sine wave. Peaks at −5.09, +3.16, −1.93, each about 0.61 of the last,
roughly 10 bars apart. Both numbers were predicted by `poles(fb1, -b)` before
any data was involved: magnitude 0.9547 over a 10.4-bar half cycle gives 0.61,
and the full cycle is 20.8 bars.

**The punchline:**

```python
>>> bad[6], mine[6]
(-1.8268903589789318, -1.8268903589789318)
```

Identical at the first bar of the response, because the changed coefficient
multiplies `hp[t-2]`, which is still zero there. The two filters only separate
once feedback has something to work with — and on real price that's buried under
the next thousand bends.

---

## Experiment 2 — verify superposition

Shows that the output is *exactly* the sum of responses to every past bend, and
why that makes a single reading uninterpretable.

**Two different bends, at different times, of different sizes.** Both 60 bars so
they can be added pointwise:

```python
>>> A = [100.0]*10 + [100.0 + i for i in range(1, 51)]      # bend at bar 10, slope 0 -> +1
>>> B = [100.0]*30 + [100.0 + 2*i for i in range(1, 31)]    # bend at bar 30, slope 0 -> +2
>>> C = [x+y for x,y in zip(A,B)]                            # both bends, one series
```

Check C really carries both:

```python
>>> C[8:12], C[28:32]
([200.0, 200.0, 201.0, 202.0], [219.0, 220.0, 223.0, 226.0])
```

Slope goes 0 → +1 at bar 10, and +1 → +3 at bar 30. Both bends arrived intact.
The level (around 200 instead of 100) is irrelevant — the filter only sees bend.

**Do not** build C by concatenating A and B. That creates a third bend at the
join.

**The test:**

```python
>>> hA, hB, hC = highpass(A), highpass(B), highpass(C)
>>> max(abs(hC[i] - (hA[i]+hB[i])) for i in range(len(hC)))
2.4868995751603507e-14
```

**How to read that number.** It's floating-point rounding, not a real
discrepancy. Outputs are of order 1–10 and a double carries ~16 significant
digits, so the noise floor sits near 1e-15. You're a rounding or two above it.

If superposition were merely approximate you'd see an error scaled to the signal
— 0.01, 0.5, something visible. Fourteen orders below the output is exact.

**Why it matters:**

```python
>>> hA[40], hB[40], hC[40]
(1.7561099201980455, 7.954404530760994, 9.710514450959032)
```

1.756 + 7.954 = 9.711.

In a real session you would see **only** 9.710514. The split is knowable here
only because we built the bends separately. The filter's entire state is three
numbers, and none of them records where anything came from.

Two things in those figures:

- The bend at bar 10, **thirty bars old**, still supplies 18% of the reading.
- The bend at bar 30, ten bars old, supplies 7.95 — its **peak**. The response
  grows for ~11 bars before decaying, so the dominant contributor is neither
  the newest movement nor a fading remnant.

A reading of 9.71 could be one big recent bend or a pile of old small ones.
Nothing downstream can separate them.

---

## Things worth trying next

- **Sweep the period.** `[round(alpha1(p),6) for p in (10,20,48,80,120)]` — watch
  alpha fall as the period rises, and check `settling(1-alpha1(p))` against the
  rule of thumb that 1% settling ≈ period.

- **Find where the response peaks.** For a `tent(5, 200)`, get
  `max(range(len(hp)), key=lambda i: abs(hp[i]))` at several periods. Compare
  against `1/-math.log(1-alpha1(p))`.

- **Three bends instead of two.** Superposition should still hold exactly. It's
  a one-line extension of experiment 2 and worth doing once.

- **Make the ring worse.** In `engine`, push `fb2` further from `-b**2` and watch
  the crossing count climb. Past `fb2 = -1` the poles leave the unit circle and
  the filter diverges — try it, it's instructive.

- **Feed it a sine.** `[100 + 5*math.sin(2*math.pi*i/20) for i in range(200)]` at
  various periods. This is the frequency-response question from a different
  angle, and it's the one experiment here that starts to resemble real price.
