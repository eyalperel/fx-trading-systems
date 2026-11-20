# Fisher Transform — source review (code vs article)

**Date:** 2026-11-19 (planning chat). **Status:** review complete, decisions taken (user, 2026-11-19: all as recommended). No spec yet.
**File reviewed:** `indicators/ehlers/FisherTransform.c` (3456 bytes, mtime 2026-08). No dependencies (reads `priceHigh()` /
`priceLow()` itself, F-2).
**Sources (both read from the page images, not only the text layer):**
- **A — the reference.** Ehlers, J.F., "Using The Fisher Transform", *Technical Analysis of Stocks & Commodities* **V.20:11 (2002)**,
  pp. 40-42; **Fig. 5 "EasyLanguage code", p. 41** (project knowledge `Using The Fisher Transform.PDF`, PDF page 4; the PDF title
  reads "V. 20:11 (40-42)").
- **B — INFO variant.** Ehlers, *Cybernetic Analysis for Stocks and Futures* (Wiley 2004), ch. 1 "The Fisher Transform":
  **Fig. 1.7 (EasyLanguage), p. 7**; Fig. 1.8 (EFS), pp. 8-9 (book PDF pages 26-28,
  `C:/books/Cybernetic Analysis for Stocks and Futures ... (John F. Ehlers) ...pdf`).
**Context:** PROJECT_STATE §7 step 3, oscillator harness family (HARNESS_DESIGN D6), fourth indicator after Reflex, MESAStochastic and
LaguerreRSI. Fisher (10) is the C1 candidate of Strategy 1 (§1.2).
**Model:** every (b) number below is reproduced by `docs/harness/FISHER_REVIEW_MODEL.py` (float64, independent of the harness
tooling). Inputs as before: level 1.1, sine amplitude 0.01, ramp slope 1e-4, 3000 bars; "rows >= 200" are past every start-up effect.

Labels: (a) source states · (b) read or computed here · (c) inference.

---

## 1. Source formulas (a)

**A — TASC V.20:11, Fig. 5, p. 41:**

```
Inputs:  Price((H+L)/2), Len(10);
Vars:    MaxH(0), MinL(0), Fish(0);

MaxH=Highest(Price,Len);
MinL=Lowest(Price,Len);

Value1 = .33*2*((Price-MinL)/(MaxH-MinL)-.5)+.67*Value1[1];
If Value1 > .99 then Value1= .999;
If Value1 <-.99 then Value1=-.999;

Fish = .5*Log((1+Value1)/(1-Value1)) + .5*Fish[1];

Plot1(Fish, "Fisher");
Plot2(Fish[1], "Trigger");
```

(a) Text p. 41: Value1 normalises price within its last 10-day range, "centered on its midpoint and then doubled" to swing between
-1 and +1, smoothed by an EMA "whose alpha is 0.33"; the limits prevent a zero or negative denominator. Fish and Fish delayed by one
bar give a crossover system. (a) Equation: y = .5 ln((1 + x)/(1 - x)), inputs constrained to -1 < x < 1. (a) `Price` is an **input**
with default (H+L)/2; `Len` is adjustable.
(a) The clamp **trigger (.99) and the value set (.999) differ**: any Value1 above .99 becomes .999.
(a) No start-up rule (no `CurrentBar` clause). Value1 is not declared in `Vars` (EasyLanguage built-in, initial 0); Fish(0).

**B — Cybernetic Analysis, Fig. 1.7, p. 7** (inputs, vars, Highest/Lowest and plots as A):

```
Value1 = .5*2*((Price - MinL)/(MaxH - MinL) - .5) + .5*Value1[1];
If Value1 > .9999 then Value1 = .9999;
If Value1 < -.9999 then Value1 = -.9999;
Fish = 0.25*Log((1 + Value1)/(1 - Value1)) + .5*Fish[1];
```

(a) Text p. 7: "alpha is 0.5". (a) Fig. 1.8 (EFS) has the same arithmetic, but its window starts from the bar's own `high()` /
`low()` and then takes max / min over the stored (H+L)/2 values (so the current bar's real High and Low are inside the window); it
returns nothing until Len prices are stored; `Value1_1` and `Fish_1` start at 0. (a) Text under Fig. 1.9 says "eight-day channel"
while the code uses Len 10. (a) Neither A nor B guards MaxH = MinL.

| Item | A (TASC 2002) | B (book 2004) |
|---|---|---|
| Value1 EMA | .33 / .67 | .5 / .5 |
| Clamp | trigger .99, set .999 | trigger .9999, set .9999 |
| Log gain | .5 ln = arctanh | .25 ln = arctanh / 2 |
| Fish feedback | + .5 Fish[1] | + .5 Fish[1] |

## 2. Line-by-line comparison (code vs A)

| Stage | Source A (a) | `.c` (b) | Verdict |
|---|---|---|---|
| Input | `Price` input, default (H+L)/2 | line 42: `series((priceHigh() + priceLow()) * 0.5)` inside the function; no Price parameter | **F-2** |
| Window | `Highest(Price,Len)`, `Lowest(Price,Len)` (incl. current bar) | lines 45-46: `MaxVal(ft_Mid, Period)`, `MinVal(...)` | Matches (c: Zorro MaxVal/MinVal take the last Period values incl. [0]; to be confirmed by the trace check) |
| Normalise | `2*((Price-MinL)/(MaxH-MinL)-.5)` | line 53, same | Matches |
| Zero range | none (division by zero) | lines 51-52: `ft_raw = 0` when range <= 0 | **F-4** |
| Value1 EMA | `.33*... + .67*Value1[1]` | line 60, same, float32 literals | Matches; literals **F-3** |
| Clamp | `> .99` -> `.999`; `< -.99` -> `-.999` | lines 64-65, same, float32 literals | Matches; literals **F-3** |
| Fish | `.5*Log((1+V)/(1-V)) + .5*Fish[1]` | line 77, same (`0.5`, `1.0` exact) | Matches |
| Trigger | `Fish[1]` (plot) | line 71: global `ft_Trigger = ft_Fish` before the update | Value matches; global **F-1** |
| State scope | per instance (EasyLanguage vars) | `static ft_Value1`, `static ft_Fish`, global `ft_Trigger`: **shared by every call** | **F-1** |
| Start-up | not defined | statics start 0, INITRUN reset; window padded with x[0] by `series()` (gotchas 9d.6) | **F-5**, **F-9** |
| Literal products | — | none at the start of an expression (`0.33 * ft_raw`, `2.0 * (...)`, `0.5 * log(...)`) | OK (gotchas 9d.8) |
| Exports | — | none | **F-7** |
| Header | — | date "October 2002" (PDF reads V.20:11; c: issue 11 = November); "Extreme readings (±2.5) are statistically meaningful" unsourced; "second EMA (alpha=0.5)" for the Fish feedback (not an EMA: gain from arctanh to Fish is 1/(1-.5) = 2); "highest high / lowest low" for midpoints | **F-8** |

**Source used by the code:** A, on every arithmetic line (.33 / .67, .99 / .999, .5 ln, + .5 Fish[1]). The header cites A.

## 3. Behaviour — measured (b)

**Exact bounds.**
- raw = 2((x - MinL)/(MaxH - MinL) - .5) in [-1, 1] (x is inside its own window); 0 when the guard fires.
- Pre-clamp |Value1| <= .33 + .67 x .999 = 0.99933; after the clamp |Value1| <= .999, and **no value lies in (.99, .999)**.
- |Fish| < .5 ln(1999)/(1 - .5) = **ln(1999) = 7.6004023345004** (A). Approached geometrically while Value1 is pinned, never
  attained exactly. B: |Fish| < ln(19999)/2 = 4.951718775643043.

**Clamp discontinuity.** If rounding flips the clamp at .99, Value1 jumps between ~.99 and .999 and Fish jumps by
atanh(.999) - atanh(.99) = **1.1535487548879537**. A trace comparison must gate rows whose pre-clamp Value1 is near ±.99.

**Memory.** Value1: .67^n < 1e-12 from n = 69; Fish: .5^n from n = 40; plus the Len-bar window.

**Sines, rows >= 200, source A** (Fish range; share of rows clamped; min range / amplitude; min |pre-clamp ∓ .99|) and B, and the
float32-literal effect of the current `.c` (max |code - A| in Fish):

| L, T | A Fish range | clamped | min rng/amp | min dist to ±.99 | B Fish range | max \|A - B\| | max \|code - A\| |
|---|---|---|---|---|---|---|---|
| 10, 5 | -0.333957..+0.352907 | 0.00 | 1.902113 | 6.609e-01 | -0.254153..+0.302488 | 0.079804 | 1.396e-08 |
| 10, 10 | ±0.943519 | 0.00 | 1.902113 | 4.309e-01 | ±0.751806 | 0.306644 | 5.860e-08 |
| 10, 20 | ±2.614129 | 0.00 | 1.000000 | 8.903e-02 | ±2.001859 | 0.961196 | 5.316e-07 |
| 10, 40 | ±7.421263 | 0.20 | 0.292893 | 1.639e-03 | ±4.884963 | 2.628208 | 1.242e-05 |
| 10, 100 | ±7.600402 | 0.68 | 0.048943 | 1.199e-03 | ±4.951719 | 2.709052 | 1.288e-05 |
| 20, 5 | -0.333957..+0.352907 | 0.00 | 1.902113 | 6.609e-01 | -0.254153..+0.302488 | 0.079804 | 1.396e-08 |
| 20, 10 | ±0.943519 | 0.00 | 1.902113 | 4.309e-01 | ±0.751806 | 0.306644 | 5.860e-08 |
| 20, 20 | ±1.869538 | 0.00 | 2.000000 | 2.047e-01 | ±1.290141 | 0.752579 | 2.288e-07 |
| 20, 40 | ±4.918061 | 0.00 | 1.000000 | 1.719e-03 | ±3.988799 | 1.893151 | 6.367e-06 |
| 20, 100 | ±7.600402 | 0.62 | 0.190983 | 7.121e-04 | ±4.951719 | 3.536973 | 1.288e-05 |

- (b) **Fisher saturates on long cycles.** At T = 100 Fish sits at the clamp on 62-68% of rows and its range reaches the bound;
  at T = 40, L = 10, 20% of rows are clamped. The header's "±2.5" is exceeded on every sine with T >= 20 at L = 10.
- (b) **Windowed:** T <= L rows are identical for L = 10 and L = 20 (T = 5, 10); only T > L tells window lengths apart
  (MST finding 1 again). The spec needs T > L for every L tested.
- (b) **Well conditioned on these sines:** min range / amplitude 0.0489 (L10, T100); the nearest pre-clamp value to ±.99 is
  7.1e-4 away (L20, T100), i.e. no clamp flip is expected from rounding at ~1e-15.
- (b) **Float32 literals matter for the floor:** the current `.c` literals alone move Fish by up to 1.29e-5 (T = 40 / 100), the
  same order as the D6 trace default (3e-5). `float32(.33) + float32(.67) - 1 = 2.98e-8`.
- (b) **Ramp is a known answer** (L10): raw = ±1 exactly from row 1; Value1 = ±.999 exactly from row 12; Fish within 1e-12 of
  ±ln(1999) from row 53 (geometric approach, not exact).
- (b) **Flat:** the guard fires on every row; raw, Value1 and Fish are 0 exactly (our guard, F-4; not a source answer).
- (b) **Shared statics (F-1):** two instances (L10 and L20) sharing the `.c`'s state on one sine: L10 output differs from its own
  instance by 0.707983 / 2.692527 / 2.695127 (T = 20 / 40 / 100, rows >= 200). Silent, permanent, not a start-up effect.
- (b) **Start-up is source-dependent (F-5):** A with the window padded by x[0] from bar 1 vs an EFS-style start (first L-1 bars
  not computed) differ by up to 0.48 / 1.26 / 2.45 / 3.53 / 4.70 (T = 5 / 10 / 20 / 40 / 100), last row > 1e-12 at 60-80.

## 4. Deviations and decisions (user, 2026-11-19: all as recommended)

| # | Deviation | Impact (b) | Decision |
|---|---|---|---|
| **Source** | A and B are different indicators | Fish differs by up to 3.54 (§3) | **A is the reference** (the `.c` follows it, its header cites it, the Fisher (10) slot choice was measured on this code). **B is an INFO variant** (role `info`, never PASS/FAIL, as NCL in USE). Choosing B for trading is a later slot decision on backtest evidence |
| **F-1** | `static ft_Value1`, `static ft_Fish`, global `ft_Trigger` shared by every call (R-1 / L-3 class) | Up to 2.70 on a second instance, permanent (§3) | **Fix:** per-instance `series` state; trigger as an out-parameter. Old file kept as `FisherTransform_Superseded.c`, called as two instances = shared-state control (D6 rule 5) |
| **F-2** | Input fixed inside the function (`priceHigh()` / `priceLow()`); the source has `Price` as an input | Harness cannot feed synthetic inputs | **Fix:** `FisherTransform(vars Price, int Len)`; callers pass `series((priceHigh() + priceLow())/2)`. Clean signature change, no alias for the old form (an untested second entry point); stage 1 greps and updates callers (test scripts only: no strategy exists) |
| **F-3** | Literals .33, .67, .99, .999 are float32 (gotchas 9d.1) | Up to 1.29e-5 in Fish (§3) | **Fix:** build each from integers at run time (D1 rule 2: taken literally at the decimal value) |
| **F-4** | Zero-range guard (raw = 0) not in either source (they divide by zero) | Flat input: raw = Value1 = Fish = 0 on every row | **Keep, labelled as ours** in the header. raw = 0 is mid-channel, a neutral reading; holding the previous raw would keep an extreme reading alive through a data gap. Flat = implementation known answer (0 exactly), not a source check. (c) A zero-range 10-bar window should be very rare on real FX / BTC data |
| **F-5** | Start-up not defined by the source (EasyLanguage: MaxBarsBack; EFS: skips L-1 bars and uses a different window) | Up to 4.70 for ~60-80 rows depending on the convention (§3) | **INFO only** (D6 rule 6): A and B themselves disagree, so there is nothing to grade against. No counter needed. W >= start-up memory, measured by the spec |
| **F-6** | EFS window includes the bar's real High / Low | — | **Record only;** the EasyLanguage listing is the reference |
| **F-7** | No exports (D6 rule 1) | — | **Fix:** `FisherCore(Price, Len, &raw, &v1, &rng)` returning Fish (exact outputs set by stage 1 tooling); `FisherTransform()` a thin wrapper. No linear front end from price (the normalisation divides by the range), so no v1 gain / phase checks on price; checks are trace on raw, v1 and Fish |
| **F-8** | Header: date, "±2.5" claim, "second EMA" description, "highest high" wording | Wrong text read later as fact | **Fix header:** source and page, formula, deviations fixed, this review's path, claims labelled; record the saturation finding (§3) |
| **F-9** | INITRUN resets of the statics never run in generated harness scripts (they return at INITRUN) | None after F-1 | **No action;** removed with F-1. Restart Zorro before any rerun of a script that calls the superseded file |

**Exact bounds (D6 rule 3):** three, all on exported stages: raw in [-1, 1]; |v1| <= .999 with no value in (.99, .999); |Fish| <
ln(1999). Unlike LaguerreRSI, the final output's bound is approached but not attained, so its check is an inequality with the D6
relative allowance.

**Gates (D6 rule 2), both evaluated on the MODEL:** (1) range / amplitude >= g (min 0.0489 here); (2) **new:** |pre-clamp v1 ∓ .99|
>= g2, because a clamp flip makes Fish jump by 1.154 (§3). Gated rows counted and reported.

**Floor:** no `PI` and no trig in the indicator. (c) The floor should be float64 rounding plus the IMP residual; the spec measures it.
(c) The harness's own sine inputs still use run-time π (9d.2 rule) and are fed identically to the model.

## 5. Dependencies

None. `InverseFisher.c` is a separate indicator (not reviewed). `MaxVal` / `MinVal` are Zorro built-ins (c: semantics to be confirmed
by the trace check, which compares the whole window result).

## 6. For the spec (not decided here)

- Variants: L = 10 (the slot value) and L = 20; source B as an INFO variant at L = 10.
- Sines T = 5, 10, 20, 40, 100 (T > L at 20 / 40 / 100 for L = 10; 40 / 100 for L = 20; T = 40 / 100 exercise the clamp).
- Trace replay on raw, v1 and Fish, rows >= W; both gates above; tolerance from the measured floor (D2 rule 3).
- Bounds: the three above, every row of every input.
- Ramps: raw = ±1 and v1 = ±.999 exactly (kind `ramp_exact`), Fish -> ±ln(1999) (tolerance; geometric approach).
- Flat: raw = v1 = Fish = 0 exactly (implementation known answer under F-4).
- Invariance (D6 rule 4): scale x k and offset; raw and Fish are scale- and offset-invariant by construction.
- Start-up: INFO (F-5).
- Controls (candidates): the real superseded file as two instances (shared state, F-1); EMA weight off in its third digit (D2 rule
  4: e.g. .34 / .66 or .33 / .68); clamp set value = trigger (.99 / .99); log gain .25 instead of .5; window Len + 1 (needs T > L);
  the float32-literal body (effect 1.29e-5: probably below 10 x tolerance, then INFO).
