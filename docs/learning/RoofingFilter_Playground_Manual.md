# Roofing Filter Playground Manual

How to use `roofing_playground.py`. Assumes you know Python; explains the
filter side, not the language side.

Companion to `RoofingFilter_Explained.md`, which covers *why* any of this
matters. The HighPass playground has its own manual, `PLAYGROUND_MANUAL.md`.

---

## Running it

**Just look at it** — ten worked sections, no arguments:

```
python docs/learning/roofing_playground.py
```

**One section only** (`--list` prints the names):

```
python docs/learning/roofing_playground.py gain
```

**Work in it** — runs every section, then leaves you at a prompt with everything
imported. This is the useful one:

```
python -i docs/learning/roofing_playground.py
```

**Ask one question:**

```
python -c "import sys; sys.path.insert(0,'docs/learning'); from roofing_playground import *; print(roof_gain(20))"
```

Use `python`, not `python3` (Microsoft Store shim on this machine).

---

## What's in it

### Parameters (top of the file)

| name | default | meaning |
|---|---|---|
| `HP_PERIOD` | 48 | `HighPassFilter.c` HPPeriod |
| `SS_PERIOD` | 10 | `SuperSmoother2Pole.c` Period — RoofingFilter's SSPeriod |
| `SEED` | 11 | random seed for the coin-flip section |

### Filters

| call | does |
|---|---|
| `highpass(x, hp_period=48, seed=None)` | Same arithmetic as `HighPassFilter.c`. `seed=None` starts the memory at zero; `seed=v` fills it with `v`, which is what the library does with `series(Price[0], 3)`. |
| `supersmoother(x, period=10, seed="first")` | Same arithmetic as `SuperSmoother2Pole.c`. Seeds at the input's first value, as the library does. |
| `roofing(x, hp_period=48, ss_period=10, hp_seed=None)` | High-pass, then SuperSmoother. `hp_seed=1.10` reproduces the library's start on EUR/USD. |
| `run_filter(num, den, x, seed=None)` | Raw 2nd-order engine. Supply any coefficient lists. |

**Historical defects** — both coefficient builders take flags that reproduce the
bugs found in the `data/fx/` files:

| call | gives |
|---|---|
| `hp_coeffs(48, with_0707=False)` | missing 0.707 — what notebook cells 18–19 compute |
| `hp_coeffs(48, with_0707=False, degrees_bug=True)` | pre-May-2026 `HighPassFilter.c` — run 1 of `data/fx/HP_EURUSD_D1.csv` |
| `hp_coeffs(48, degrees_bug=True)` | the half-fix — run 2, which explodes |
| `ss_coeffs(10, degrees_bug=True)` | pre-fix SuperSmoother |

### Coefficients and gain

| call | returns |
|---|---|
| `hp_alpha(period, with_0707=True, degrees_bug=False)` | alpha1. `hp_alpha(48)` = 0.088513 |
| `hp_coeffs(period, ...)` | `(num, den)` arrays for the high-pass |
| `ss_coeffs(period, ...)` | `(num, den)` arrays for the SuperSmoother |
| `gain(num, den, period)` | exact gain at that period, from coefficients alone |
| `roof_gain(period, hp_period=48, ss_period=10)` | the two gains multiplied |
| `corner(f, lo, hi)` | the period where gain function `f` crosses 0.7071 |
| `amplitude_at(y, period)` | `(amplitude, residual)` of the period-P sine in `y`, fitted — immune to the sampling trap |

**Sampling-trap gotcha:** never read gain as `(max − min)/2` of an output. The
peak falls between bars and reads low. Use `gain()` or `amplitude_at()`.

**Constant gotcha:** `ss_coeffs` uses `sqrt(2)`, like the library. Ehlers'
article uses `1.414`. Figures differ in the 4th decimal.

---

## Experiment 1 — the cascade really multiplies

Shows that the roofing filter's gain is the product of its two stages, checked
against a simulated sine rather than trusted.

```python
>>> x = np.sin(2*np.pi*np.arange(4000)/20)
>>> amp, resid = amplitude_at(roofing(x)[-1000:], 20)
>>> round(roof_gain(20), 6), round(amp, 6)
(0.890038, 0.890038)
```

Same to six decimals. Try another period in both places.

## Experiment 2 — collapse the band

```python
>>> max(roof_gain(p, 10, 10) for p in np.arange(3, 200, 0.01))
0.4778...
```

HPPeriod = SSPeriod = 10: no period gets even half its amplitude through. Raise
the first 10 to 15, 20, 30 and watch the peak climb (section `collapse` prints
the table).

## Experiment 3 — a cycle from nothing

Same filter, three different coin-flip walks:

```python
>>> for s in (1, 2, 3):
...     w = np.cumsum(np.random.default_rng(s).choice([-1.0, 1.0], 3000))
...     y = roofing(w)[500:]
...     sg = np.signbit(y)
...     print(s, round(2*len(y)/np.count_nonzero(sg[1:] != sg[:-1]), 2))
1 26.32
2 23.36
3 23.04
```

No cycle in any input; a ~23–26 bar rhythm in every output. That is the filter.

## Experiment 4 — the seed is the transient

```python
>>> flat = np.full(120, 1.10)
>>> a = roofing(flat, hp_seed=1.10)      # what the library does
>>> b = roofing(flat, hp_seed=None)      # memory starts at zero
>>> round(a[0], 5), round(a[30], 5), abs(b).max()
(1.09138, 0.26378, 0.0)
```

On flat price the zero-seeded version outputs exactly nothing. Every bit of `a`
is start-up artefact — and it matches your real CSV's row 1 ratio (0.992166).

## Experiment 5 — read stability off the coefficients

```python
>>> for kw in [{}, dict(with_0707=False, degrees_bug=True), dict(degrees_bug=True)]:
...     num, den = hp_coeffs(48, **kw)
...     print(kw, np.round(np.abs(np.roots(den)), 4))
{} [0.9115 0.9115]
{'with_0707': False, 'degrees_bug': True} [0.1789 0.1789]
{'degrees_bug': True} [3.2903 3.2903]
```

`np.roots(den)` gives the poles. Library: 0.9115, stable. Pre-fix: 0.1789,
stable but a different filter. Half-fix: **3.2903**, above 1 — it will explode,
and did. No data needed to know.

---

## Things worth trying next

- **Move the band.** `corner(lambda p: gain(*hp_coeffs(H), p), 5, 500)` for
  several H. How far is the corner from H each time? (Open question in the
  explainer.)
- **Old SuperSmoother.** `np.roots(ss_coeffs(10, degrees_bug=True)[1])` — are the
  poles complex? Does the pre-fix SuperSmoother ring? Not yet examined.
- **White vs red.** Replace `np.cumsum(...)` in experiment 3 with the raw steps.
  The rhythm should drop to ~11 bars.
- **Smoothing ratio at other SSPeriods.** Rebuild section `ratio` with
  `supersmoother(h, period=P)` for P in 5, 8, 14, 20, and compare with the
  1.7–4.6× column the notes carry from cell 19.
