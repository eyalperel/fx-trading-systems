# Cycle Premise — Second Null Test: Phase Coherence & Autocorrelation Periodogram

**Date:** 2026-08-05, Week 12 Day 5
**Companion to:** `docs/research/Cycle_Premise_Conclusions_and_Impact.md` (Week 11)
**Governed by:** Phase 2 Principle 6 (null gate)
**Outcome:** ⛔ **NO REJECTION.** 16 tests, two assets, two statistics, four nulls.
Minimum p = 0.117.

---

## 1. Summary

Week 11 tested the cycle premise through **spectral peak prominence** on a
`RoofingFilter → CyberCycle` chain. This test extends it in two directions:

| Test | Mechanism | Statistic | Result |
|---|---|---|---|
| Correlation Cycle | Quadrature projection onto a fixed-period cosine/sine basis | Phase coherence (circular resultant length R) | No rejection |
| Autocorrelation periodogram | Correlogram → Fourier across trial periods | Spectral peak prominence | No rejection |

Neither is significant on either asset against any of four null models.

**The headline is not the non-rejection.** It is that the Correlation Cycle's phase
coherence statistic reads **R ≈ 0.97 on real markets and R ≈ 0.97 on pure noise.** The
apparent coherence is manufactured by the indicator's sliding window, not measured from
the market.

---

## 2. Correction to the Day 2 pre-registration

The Week 12 Day 2 notes and roadmap v4.3 both stated that the Correlation Cycle
*"detects cycles via autocorrelation, not band-pass filtering — a genuinely different
mechanism, so it's a real second test of the premise rather than a repeat."*

**That was wrong.** The error came from working off `Measuring_Market_Cycles.pdf`
(V.34:09, 2016), which *is* autocorrelation-based, rather than the actual Week 12 article
`Correlation_As_A_Cycle_Indicator.pdf` (V.38:06, 2020).

The published Correlation Cycle computes:

```
Real = Pearson( Price,  cos(2*pi*n/Period) )
Imag = Pearson( Price, -sin(2*pi*n/Period) )
```

Price is correlated against a **fixed-period sinusoidal basis**, not against itself at
various lags. This is a normalised single-bin DFT over a sliding window — a matched
filter at one frequency, and therefore a **linear projection in the same family as the
band-pass chain already tested in Week 11**. Slutsky–Yule applies directly.

**Consequence:** the mechanism is not independent of Week 11. Two changes followed:

1. The tested claim was changed to **phase coherence**, which Week 11 genuinely did not
   test — spectral prominence measures power concentration; phase coherence measures
   regularity of phase progression. These are distinct properties.
2. The **autocorrelation periodogram** was implemented separately (Python only) to
   supply the genuinely independent mechanism the roadmap intended.

---

## 3. Result 1 — Phase coherence is an artefact of window overlap

### 3.1 The statistic

For phase steps Δθ₁…Δθₙ (wrapped to (−180°, 180°]), the mean resultant length is

```
R = | (1/n) · Σ exp(i·Δθ_k) |
```

R = 1 ⇒ every phase step identical (a genuine cycle advancing at fixed rate).
R = 0 ⇒ steps uniformly scattered. Circular variance = 1 − R.

Circular statistics are required because angles wrap: a linear standard deviation treats
+179° and −179° as 358° apart when they differ by 2°.

Computed on the **raw** angle, before Ehlers' monotonicity ratchet (§5).

### 3.2 Results

| Asset | Observed R | Null median R | Percentile | p |
|---|---|---|---|---|
| **EUR/USD D1** | **0.9706** | | | |
| — vs IID random walk | | 0.9705 | 51.3 | 0.487 |
| — vs fBm (H = 0.472) | | 0.9700 | 58.8 | 0.412 |
| — vs IAAFT | | 0.9698 | 62.1 | 0.379 |
| — vs stochastic volatility | | 0.9706 | 48.6 | 0.514 |
| **BTC/USD H4** | **0.9685** | | | |
| — vs IID random walk | | 0.9694 | 29.5 | 0.705 |
| — vs fBm (H = 0.523) | | 0.9713 | 3.5 | 0.965 |
| — vs IAAFT | | 0.9681 | 59.6 | 0.404 |
| — vs stochastic volatility | | 0.9707 | 8.5 | 0.915 |

1,000 surrogates per null. Rejection required observed R above the null 95th percentile
(one-sided — the claim is that markets are *more* coherent than noise).

### 3.3 Interpretation

**R ≈ 0.97 in isolation looks like near-mechanical cycle regularity.** It is not.

A random number generator produces R = 0.9705. Real EUR/USD produces 0.9706 and sits at
the **51st percentile** of the IID null — the exact centre.

**The cause is window overlap.** Consecutive 20-bar windows share 19 of 20 bars, so
consecutive phase angles are nearly identical *by construction*. The sliding window
manufactures phase coherence from any input.

> This is Slutsky–Yule in a second guise. Week 11 found a filter chain manufacturing a
> ~20-bar oscillation from Brownian motion. Here a sliding-window correlation
> manufactures phase regularity from noise. Same class of artefact, different indicator
> family.

On BTC, real data scores **below** the null median against three of four nulls
(3.5th percentile vs fBm). Real BTC phase is *less* coherent than matched noise.

---

## 4. Result 2 — Autocorrelation periodogram reproduces the Week 11 direction

Implemented on **raw log returns with no roofing pre-filter**, deliberately: Ehlers
band-passes before correlating, which reimports the artefact under test.

| Asset | Observed prominence | Null median | Percentile | p |
|---|---|---|---|---|
| **EUR/USD D1** | **1.181** | | | |
| — vs IID random walk | | 2.700 | 8.3 | 0.917 |
| — vs fBm | | 2.949 | 5.3 | 0.947 |
| — vs IAAFT | | 1.686 | 6.3 | 0.937 |
| — vs stochastic volatility | | 2.580 | 7.0 | 0.930 |
| **BTC/USD H4** | **4.026** | | | |
| — vs IID random walk | | 2.621 | 84.0 | 0.160 |
| — vs fBm | | 2.623 | 88.3 | 0.117 |
| — vs IAAFT | | 4.021 | 54.3 | 0.457 |
| — vs stochastic volatility | | 2.793 | 83.3 | 0.167 |

300 surrogates per null for this statistic (cost-bound).

**EUR/USD scores below the null median on all four nulls (5.3rd–8.3rd percentile).**
Noise produces a *sharper* correlogram peak than the real market does.

This reproduces Week 11's directional finding (8th percentile FX, 6.6th crypto) through a
**completely different mechanism** — autocorrelation rather than band-pass filtering.
Two independent methods, same direction.

**BTC runs higher (84th percentile) but is far from significant.** The IAAFT result is
the informative one: IAAFT preserves BTC's exact power spectrum, and observed prominence
(4.026) matches its null median (4.021) almost exactly, at the 54th percentile. BTC's
correlogram structure is fully explained by its power spectrum, with no additional cyclic
content.

---

## 5. The monotonicity ratchet manufactures the "trend mode" signature

Ehlers applies, after computing the phase:

```
if(Angle[1] - Angle < 270 && Angle < Angle[1]) Angle = Angle[1];
```

This **forbids phase from decreasing** except across a wrap.

| Asset | Bars where the ratchet held angle flat | Negative Δ before → after |
|---|---|---|
| EUR/USD D1 | **26.6%** | 15.1% → 3.2% |
| BTC/USD H4 | **28.6%** | — |

The flatlining Ehlers presents as evidence of trend mode is therefore **partly
manufactured by the guard**: when phase would retreat, it is held flat instead. The
signature appears on any input, including pure noise.

Separately, his 9°/bar trend threshold fires on **33.7% (FX) / 36.7% (BTC)** of bars on
the *raw* angle, before the ratchet adds its 27%. The state variable declares "trend" on
roughly a third of all bars using a criterion noise satisfies equally well.

**All null testing used the raw, unratcheted angle.** Testing the ratcheted angle would
have measured the smoother, not the market.

---

## 6. Implementation validated by independent reimplementation

The Zorro Light-C implementation and a from-scratch NumPy reimplementation agree:

| Asset | R (Zorro) | R (Python) | frac \|Δ\|<9° Zorro / Python |
|---|---|---|---|
| EUR/USD D1 | 0.9703 | 0.9706 | 0.3373 / 0.3408 |
| BTC/USD H4 | 0.9686 | 0.9685 | 0.3669 / 0.3672 |

Two independent implementations of the same specification converging is stronger evidence
of correctness than either alone.

---

## 7. Classification under Principle 6

> **Correlation Cycle Indicator (#23)** — enters the library **classified as a filter,
> not a cycle detector.** Same classification CyberCycle received in Week 11.
>
> **Legitimate:** Real and Imag are well-formed bounded quadrature projections
> (verified Real² + Imag² ≤ 1 throughout; mean 0.524, max 0.958). As a normalised
> single-frequency projection with a characterised response, the outputs are what they
> claim to be.
>
> **Not supported:** phase, phase rate of change, and the derived State variable carry
> no information about market cyclicality that noise does not also carry. Phase
> coherence on real data is indistinguishable from phase coherence on a random walk
> (51st percentile).
>
> **Forbidden uses:** cycle-mode / trend-mode regime classification via the State
> variable; period or phase extrapolation; parameter adaptation driven by measured phase.

### 7.1 Why visual inspection would have produced a false positive

The roadmap's original Day 5 validation asked whether *"the reading aligns with visually
obvious cycle/trend periods."*

That check would have passed. On any input — including pure noise — the phase looks
coherent (R ≈ 0.97), and the state variable flips convincingly between trend and cycle on
a third of bars. **Without the surrogate comparison, the indicator appears to work.**

This is the concrete case for Principle 6.

---

## 8. Registered predictions — both confirmed

| Prediction (registered before running) | Confidence | Outcome |
|---|---|---|
| Correlation Cycle phase coherence: non-rejection | ~85% | ✅ Confirmed (min p = 0.379) |
| Autocorrelation periodogram: non-rejection | ~80% | ✅ Confirmed (min p = 0.117) |
| Possible surprise: real data *below* null median | — | ✅ Occurred — FX on both statistics |

Stated reasoning at registration: *H(returns) ≈ 0.5 on both assets means returns are
close to memoryless, and memoryless increments have no mechanism for producing coherent
phase progression.* Measured here: H(ret) = 0.472 (FX), 0.523 (BTC).

---

## 9. Cumulative state of the cycle premise

| Week | Mechanism | Statistic | Tests | Min p | Result |
|---|---|---|---|---|---|
| 11 | Band-pass (Roofing → CyberCycle) | Spectral peak prominence | 48 | 0.070 | No rejection |
| 11 | Band-pass, regime-conditional (FX) | Spectral peak prominence | — | — | No rejection, weaker bound (~15.8%) |
| **12** | **Quadrature projection** | **Phase coherence** | **8** | **0.379** | **No rejection** |
| **12** | **Autocorrelation** | **Correlogram peak prominence** | **8** | **0.117** | **No rejection** |

**Three mechanistically distinct methods. 64 tests. No rejection.** Two of the three
show real data scoring *below* the null median on FX — noise looks more cyclic than the
market does.

The Week 11 conclusion is strengthened, not merely repeated: the earlier objection that
only one filter chain had been tested is now closed.

---

## 10. Limitations

- **Fixed Period = 20** throughout. A cycle at another period would not be detected by
  this specific projection. Mitigated by the periodogram, which scans 8–48 bars.
- **Two assets, two timeframes.** No claim beyond EUR/USD D1 and BTC/USD H4.
- **Non-rejection is not proof of absence.** No formal power analysis was run for the
  phase-coherence statistic, so no variance bound is quoted (unlike Week 11's 4.4% / 5.0%
  bounds). **The R ≈ 0.97 window-overlap floor probably makes this statistic
  low-powered** — if most of R is manufactured, little dynamic range remains to detect a
  real signal. Establishing that bound is deferred.
- **Periodogram used 300 surrogates**, not 1,000, for cost reasons.
- **Autocorrelation periodogram exists in Python only.** No Light-C port, deliberately:
  porting an indicator before knowing whether its mechanism detects anything would risk
  building on an invalidated result. Reconsider only if a future test rejects.

---

## 11. Artefacts

| Item | Path |
|---|---|
| Indicator | `indicators/ehlers/CorrelationCycle.c` |
| Test script | `strategies/tests/Test_CorrelationCycle.c` |
| Exports | `CorrCycle_EURUSD_D1.csv` (2,596), `CorrCycle_BTCUSD_H4.csv` (7,534) |
| Week 11 basis | `docs/research/Cycle_Premise_Conclusions_and_Impact.md` |
| Source | Ehlers, "Correlation As A Cycle Indicator," *S&C* V.38:06 (2020), 8–15 |
