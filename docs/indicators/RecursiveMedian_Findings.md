# Recursive Median Filter — Empirical Findings & Reclassification

**Date:** 2026-08-05, Week 12 Day 4
**Companion to:** `docs/indicators/RecursiveMedian_Theory.md` (Day 1 theory)
**Indicators:** #22 RM, #22b RMO
**Status:** Validated and **reclassified**. Retained in library with a narrowed use case.

---

## 1. Headline

The Day 1 theory is confirmed in every measurable respect. The **premise for using this
filter on crypto is not.**

| Claim | Status |
|---|---|
| Lag = 3.37 bars (2.00 median + 1.37 EMA) | ✅ Confirmed: **3.366**, decomposition exact |
| Alpha formulas, 0.707 placement | ✅ Confirmed: 0.422649 / 0.138102 |
| Median stage is active on outlier bars | ✅ Confirmed: **4.66×** divergence on tail bars |
| Cross-asset generalisation without retuning | ✅ Confirmed: 1.03× signal-frequency ratio |
| RMO has no AGC | ✅ Confirmed: **4.58×** amplitude variation on BTC vs 1.52× on FX |
| **"Flash crash resilience: critical for crypto"** | ⛔ **REFUTED — the rationale is inverted** |

---

## 2. The reclassification

### 2.1 What was expected

The indicator plan justified RM for crypto on the grounds of *"flash crash resilience."*
The implicit model: BTC/USD H4 contains corrupted prints — exchange glitches, thin-book
wicks, bad ticks — and a median filter rejects them where a linear filter propagates them
proportionally.

### 2.2 What the data shows

**BTC's extreme moves are real, not corrupt.** Behaviour of 99th-percentile absolute
moves over the following 5 bars (n = 76):

| Measure | Value | Interpretation |
|---|---|---|
| Reverted at all | 46.1% | Coin-flip |
| **Median retracement** | **−2.3%** | Moves *continue*, they do not revert |
| Mean retracement | +11.5% | Skewed by a minority that partly retrace |

A bad tick reverts ~100% within a bar or two. These do not revert. They are genuine price
discovery.

### 2.3 Why that inverts the rationale

**A median filter cannot distinguish a corrupted print from a genuine regime break.**
Both are outliers by rank, and rank is all the median uses — which is precisely the
property that gives it a 40% breakdown point. The filter rejects both identically.

- Outlier is a **bad tick** → rejecting it is correct, and free.
- Outlier is a **real move** → rejecting it is wrong, and costs lag exactly when
  responsiveness matters most.

On clean exchange OHLC, the second case dominates.

### 2.4 Measured cost, lag-matched

Through the deepest drop in the sample (−20.50% in one H4 bar), max |filter − price| over
the following 12 bars:

| Filter | Lag | Max deviation from price |
|---|---|---|
| RM (LP=12) | 3.366 bars | **1,793** |
| EMA α=0.40 | 1.500 bars | 965 |
| **EMA α=0.229 (lag-matched to RM)** | **3.366 bars** | **1,568** |

**RM tracks worse than a lag-matched EMA** — 1,793 vs 1,568. Whole-sample RMSE against
price confirms it: RM 993 vs lag-matched EMA 785.

This is not a baseline-lag artefact. Against an EMA calibrated to the identical 3.366-bar
lag, RM is still further from price, both through the crash and across the full sample.
The extra distance is the median stage rejecting real information.

### 2.5 The mechanism is working — that is the problem

Divergence between RM and a plain EMA, by bar type (BTC/USD H4):

| Bar type | n | mean \|RM − EMA\| |
|---|---|---|
| Ordinary (< 90th pct move) | 6,779 | 278.7 |
| Tail (≥ 99th pct move) | 76 | **1,299.6** |

**4.66× more divergence on tail bars.** The non-linearity is not dormant during extreme
moves — it fires exactly as designed. The design is simply wrong for this input, because
the tails it suppresses are signal rather than noise.

---

## 3. Revised classification

> **Recursive Median Filter (RM)** — outlier-robust smoother. Non-linear 5-bar median
> gate feeding a one-pole EMA. Breakdown point 40%; rejects runs of up to 2 consecutive
> corrupted bars.
>
> **NOT RECOMMENDED for clean exchange OHLC data (D1/H4 candles from a single venue).**
> On such data, large moves are genuine (BTC 99th-pct moves show −2.3% median
> retracement), and the median stage suppresses real price discovery. A lag-matched EMA
> tracks price more closely both through crash events and across the full sample.
>
> **APPROPRIATE for input containing genuine corruption:** tick data with bad prints,
> thin-liquidity venues, unvalidated or aggregated multi-exchange feeds, sensor-like
> series where isolated errors are known to occur.
>
> **The distinguishing question is not "are there outliers" but "do the outliers
> revert."** Test before use: if extreme moves retrace ~100% within a few bars, they are
> corruption and RM helps. If they persist, they are information and RM costs lag.

### 3.1 RMO

> **Recursive Median Oscillator (RMO)** — RM through a 2-pole high-pass. Zero-centred
> momentum oscillator, passband ≈ 12–30 bars.
>
> **Eliminated as Strategy 2 C2** — |ρ| = 0.799 with MESA Stochastic. See
> `C2_Decision_Week12.md`.
>
> **No AGC.** Amplitude varies 4.58× across BTC/USD H4 segments vs 1.52× on EUR/USD D1.
> Sign is regime-stable; magnitude is not. Zero-crossing use survives; any threshold-based
> use requires a normalisation wrapper.
>
> Inherits RM's input-quality caveat.

---

## 4. Confirmed as theorised

Recorded because these validate the theory-before-code protocol, not merely the code.

**Lag.** Day 1 predicted 3.37 bars from first principles (median 2.00 on a monotonic ramp
+ EMA (1−α)/α = 1.37 at P=12), written and pushed before implementation. Measured ramp
steady-state: **3.366 bars**, decomposition exact (median 2.000, EMA 1.366). A
sorting-network error, misplaced 0.707, or wrong alpha would each have broken this.

**Alphas.** alpha1 (LP=12, no 0.707) = 0.422649 vs 0.422650 predicted. alpha2 (HP=30,
with 0.707) = 0.138102 exact. The two-alpha confusion flagged on Day 1 as the highest-
probability bug did not occur.

**Cross-asset stability.** RMO zero-crossings per 100 bars: 9.33 (EUR/USD D1) vs 9.07
(BTC/USD H4) — a **1.03× ratio** against a 2× threshold, with identical parameters and no
retuning. Stronger than expected, and consistent with the library standard set by
HP=48/SS=10 and Fisher P=10.

**Smoothing ratios transfer from synthetic to real data.** Alpha-Beta at Gain=0.10 was
predicted from white-noise simulation to give σ ratio 0.688; measured 0.694 (FX) and
0.690 (BTC).

---

## 5. Methodological finding — lag measurement

Recorded separately because it invalidates a method that would otherwise look reasonable.

| Method | Pure 3-bar delay | EMA α=0.40 (analytic 1.50) | Verdict |
|---|---|---|---|
| First-difference cross-correlation | — | **0.00** | ⛔ **INVALID** |
| MSE-minimising shift | 3.00 ✅ | 0.94 | ⚠️ Biased ~0.65× for smoothers |
| **Ramp steady-state** | 3.00 ✅ | **1.500** ✅ | ✅ **Exact — adopted** |

First-difference cross-correlation reported **zero lag for a filter with known 1.50-bar
lag**. Differencing an EMA yields α·(P[t] − EMA[t−1]), dominated by the current price
change, so it peaks at lag 0 regardless of how much the level trails.

**This was caught only because the instrument was validated against a case with a known
answer before being applied to an unknown one.** Had it not been, criterion C-4 would
have been measured with a method that produces confident nonsense.

**Standing rule adopted:** validate any measurement instrument against a known ground
truth before applying it to the quantity of interest.

---

## 6. Open items

| # | Item | Disposition |
|---|---|---|
| 1 | Does RM help on genuinely corrupted data? | Untested — would need tick data or a synthetic bad-tick injection. Worth a controlled test if RM is ever proposed for live use. |
| 2 | RMO against a non-roofing-filter C1 | Untested. The 0.799 correlation is specific to MESA Stochastic. |
| 3 | Alpha-Beta gain sweep at corrected 0.02/0.05/0.10/0.20 | Not run. Low priority — the filter is a forecast, not a smoother, and an EMA dominates it for smoothing. |
| 4 | Strategy-level validation | Out of scope for Phase 2. All findings here are indicator-level. |

---

## 7. References

- `docs/indicators/RecursiveMedian_Theory.md` — Day 1 theory and registered predictions
- `docs/indicators/C2_Selection_Criteria_PreRegistered.md` — binding criteria
- `docs/indicators/C2_Decision_Week12.md` — C2 elimination record
- Ehlers, J. F. (2018). "Recursive Median Filters." *S&C* 36:03, 8–11
- Data: `RM_C2_EURUSD_D1.csv` (2,596 bars), `RM_C2_BTCUSD_H4.csv` (7,534 bars)
