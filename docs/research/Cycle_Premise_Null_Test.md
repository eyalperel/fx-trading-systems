# Null-Hypothesis Test of the Ehlers Cycle Premise

**EUR/USD D1 and BTC/USD H4 — surrogate data testing of the RoofingFilter → CyberCycle pipeline**

Date: 2026-08-03
Status: Complete
Scope: indicator-level validity of the cycle-extraction premise. **Not** a strategy-level or P&L validation.

---

## 1. Question

John Ehlers' body of work rests on the premise that

> price = trend + cycle + noise

and that digital filters can separate these components, exposing a tradable cycle. Every oscillator in this library built on cycle extraction inherits that premise. It had never been tested.

**Question asked:** is the oscillation produced by `RoofingFilter → CyberCycle` on real market data distinguishable from the oscillation the same pipeline produces on data containing no cycle by construction?

---

## 2. Why the premise needs decomposing before it can be tested

The premise bundles three claims with very different status.

| Claim | Status |
|---|---|
| **A.** Price decomposes into trend + cycle + noise | **Unfalsifiable.** The spectral representation theorem guarantees any covariance-stationary process is representable as an integral of sinusoids; Wold's decomposition guarantees the trend/stochastic split. True of a random walk, true of a random number generator. Carries no information. |
| **B.** The cycle component has identifiable, persistent spectral peaks | **Testable.** Contradicted by prior literature (below) and by this experiment. |
| **C.** Filtering recovers that cycle | **Testable, and actively dangerous.** Filters manufacture apparent cycles from noise. |

Claim A is a theorem dressed as an insight. Claims B and C carry the entire load.

### 2.1 Prior literature

- **Granger (1966), "The Typical Spectral Shape of an Economic Variable"** — economic series in levels show spectral mass concentrated at low frequency, declining smoothly, with *no* series of peaks corresponding to cycles of different lengths. Replicated across 58 countries (Levy & Dezhbakhsh) and across 100 series (MPRA 53584), holding for financial variables to a lesser extent.
- **Slutsky (1937) / Yule (1927)** — the moving summation or average of a random series generates oscillations where none exist. As the number of summations grows, the artefacts converge to sine waves.
- **Nelson & Kang (1981), "Spurious Periodicity in Inappropriately Detrended Time Series"** — detrending a random walk *induces* pseudo-periodic behaviour, with apparent cycle duration matched to sample length regardless of how much data is used.

Claim C is precisely what the RoofingFilter does: it high-pass detrends, then low-pass smooths. Both operations are named in the Slutsky/Nelson-Kang results as cycle-manufacturing.

### 2.2 Ehlers contradicts himself across the corpus

In *Whiter Is Brighter* (S&C 33:1, 2015) Ehlers explicitly abandons the deterministic-waveform-plus-noise model, stating that a more correct model of market data is one comprised **solely of pink noise**.

**This library therefore straddles two incompatible market models.** MAMA/FAMA, Cyber Cycle, DominantCycle and the phasor/market-state work assume a measurable dominant cycle. The Universal Oscillator and spectral-dilation work assume there isn't one. The corpus is not unified and should not be treated as such.

**Additional finding — Ehlers mislabels his own measurement.** He states market spectral power grows 6 dB per octave. 6 dB/octave in power is f^−2 — **brown noise, i.e. integrated white noise, i.e. a random walk**. Pink noise is f^−1, 3 dB/octave. His measurement is correct; his label is wrong. Measured here:

| Series | PSD slope | dB/octave |
|---|---|---|
| EUR/USD log price | f^−1.835 | 5.52 |
| BTC/USD log price | f^−1.837 | 5.53 |
| synthetic random walk | f^−1.848 | 5.56 |
| EUR/USD log returns | f^−0.001 | 0.00 |
| synthetic white noise | f^+0.039 | −0.12 |

"Spectral dilation" is integration. Two markets differing 10× in volatility and 10× in kurtosis produce indistinguishable spectral slopes, both matching Brownian motion.

---

## 3. Method

### 3.1 Pipeline under test

Unchanged from `Test_CyberCycle.c`: `HP_PERIOD=48`, `SS_PERIOD=10`, `CC_ALPHA=0.07`, 100-bar warmup. Identical parameters used for both assets so any cross-asset difference is a property of the market, not of tuning.

### 3.2 Zorro → Python port validation (gate)

The Python port was validated against Zorro ground truth before any surrogate work:

| Stage | max abs diff (post burn-in) | correlation |
|---|---|---|
| roofing | 5.01e-06 | 0.99999991 |
| cycle | 5.01e-06 | 0.99999987 |
| trigger | 5.01e-06 | 0.99999993 |

CSV precision is `%.5f`, so the rounding floor is 5.0e-06. **The residual is exactly the file's rounding floor — no formula discrepancy.** This independently confirms two prior corrections in this project: the `0.707` multiplier inside the HP `alpha1` trig arguments, and that Zorro Light-C trig takes radians.

A reproducibility check also passed: the May 2026 Zorro run reproduced bit-for-bit in August 2026.

**Burn-in = 300 bars**, discarding both the zero-state IIR transient and the `scipy.lfilter` startup transient (measured to decay to 6.9e-08 by bar 300). Applied identically to real and surrogate series.

### 3.3 Null models

Each generates a price series of matched length, pushed through the identical pipeline. All are amplitude-adjusted to the real return marginal, so nothing can be rejected merely for having wrong tails.

| Null | Construction | Question |
|---|---|---|
| **A** bootstrap | IID resample of real log-returns → cumsum | Anything beyond IID? |
| **B** fGn | Fractional Gaussian noise (Davies–Harte, exact) at DFA-estimated H | Anything beyond Ehlers' own 2015 pink-noise model? |
| **C** IAAFT | Iterative amplitude-adjusted Fourier transform | Is the cycle **phase-coherent**, i.e. extrapolatable? |
| **D** stochastic vol | IID returns × long-memory volatility process | **Anything beyond volatility clustering?** |

**Null D is decisive.** Nulls A, B and C all produce H(|returns|) ≈ 0.50, i.e. no volatility clustering — so a difference from those could be a cycle *or* just clustering. Only D separates the two. It was added after DFA revealed the long memory lives in volatility, not returns.

**Note on Null C's role.** IAAFT preserves the power spectrum exactly, so any spectral peak is reproduced by construction. It therefore *cannot* test whether a cycle exists — it tests whether the cycle's phase is coherent. A cycle you can measure but whose phase is random is untradable.

### 3.4 Measured memory structure

| | EUR/USD D1 | BTC/USD H4 |
|---|---|---|
| H(returns), DFA | 0.460 | 0.523 |
| H(\|returns\|), DFA | **0.658** | **0.766** |
| kurtosis | 2.02 | 20.62 |
| annualised vol | 7.7% | 79.1% |

DFA estimator calibrated against exact fGn: recovers known H within ±0.02 across H = 0.3–0.9.

**The long memory is in volatility, not returns.** H(returns) ≈ 0.5 for both assets. Ehlers' pink-noise claim is defensible for volatility and not for returns — and it is returns, not volatility, that a cycle would have to live in.

### 3.5 Metrics

Six statistics computed on the CyberCycle output. `peak_prominence` (peak PSD ÷ median PSD across the 10–48 bar passband) does the discriminating work: a genuine cycle gives a tall narrow peak, a Slutsky artefact gives a broad low bump. Both yield a "dominant period" under argmax; only the first is a cycle.

**Metric discrimination check** (known inputs through the real pipeline):

| Input | dom_period | **prominence** | zero_cross | stability | acf_half |
|---|---|---|---|---|---|
| pure sine P=20 | 19.69 | **5,976,270** | 20.00 | 0.80 | 0.995 |
| random walk | 34.13 | **8.75** | 20.40 | 8.22 | 0.284 |
| white noise | 17.07 | **2.25** | 10.14 | 5.04 | 0.246 |

Six orders of magnitude of discrimination. Note the random-walk row: **the pipeline returns a 20.4-bar zero-crossing period from pure Brownian motion.**

### 3.6 Positive control (detection power)

A 20-bar sinusoid injected into Null B at known SNR, to establish what the test *could* have found. Without this, a null result is unfalsifiable — the same criticism levelled at Claim A.

---

## 4. Results

### 4.1 Detection power

| | EUR/USD D1 | BTC/USD H4 |
|---|---|---|
| 80% power at | −14.7 dB | ~−14.3 dB |
| **95% power at** | **−13.5 dB** | **−13.0 dB** |
| corresponding cycle share of return variance | **4.4%** | **5.0%** |

A cycle carrying more than ~4–5% of return variance would have been detected with 95% probability on either asset. The instrument works.

### 4.2 EUR/USD D1 — two-sided rank p-values (N = 1,000 per null)

| Metric | A boot | B fgn | C iaaft | D stochvol |
|---|---|---|---|---|
| dominant_period | 0.078 | 0.112 | 0.506 | 0.070 |
| peak_prominence | 0.116 | 0.162 | 0.236 | 0.124 |
| zero_cross_period | 0.852 | 0.662 | 0.218 | 0.710 |
| period_stability | 0.354 | 0.388 | 0.866 | 0.314 |
| acf_half_period | 0.614 | 0.594 | 0.376 | 0.682 |
| rms_amplitude | 0.538 | 0.926 | 0.406 | 0.310 |

**24 tests, zero below 0.05, minimum 0.070.**

### 4.3 BTC/USD H4 — two-sided rank p-values (N = 1,000 per null)

| Metric | REAL | A boot | B fgn | C iaaft | D stochvol |
|---|---|---|---|---|---|
| dominant_period | 51.200 | 0.442 | 0.518 | 0.808 | 0.450 |
| peak_prominence | 2.912 | 0.138 | 0.112 | 0.218 | 0.132 |
| zero_cross_period | 19.809 | 0.340 | 0.154 | 0.390 | 0.252 |
| period_stability | 8.435 | 0.602 | 0.532 | 0.808 | 0.644 |
| acf_half_period | 0.104 | 0.200 | 0.228 | 0.248 | 0.238 |
| rms_amplitude | 668.889 | 0.852 | 0.686 | 0.986 | 0.604 |

**24 tests, zero below 0.05, minimum 0.112.**

### 4.4 The result is directional, not merely null

Real markets are **less** cyclical than the noise nulls on the discriminating metric:

| | real prominence | Null-D mean | percentile |
|---|---|---|---|
| EUR/USD D1 | 3.17 | 4.75 | 8th |
| BTC/USD H4 | 2.91 | 4.50 | 6.6th |

Pink noise and stochastic-volatility noise pushed through the RoofingFilter → CyberCycle pipeline produce a **better-defined spectral peak than real market data does.**

Period stability agrees: EUR/USD's dominant cycle wanders 8.89 bars (81st percentile of null — *more* unstable than noise); a pure sine scores 0.80.

### 4.5 The filter's fingerprint

`zero_cross_period` across three completely different inputs:

| Input | zero-crossing period |
|---|---|
| EUR/USD D1 (≈4 weeks per 20 bars) | 19.51 |
| BTC/USD H4 (≈3.3 days per 20 bars) | 19.81 |
| synthetic random walk | 20.40 |

Two markets with a 10× volatility difference on different timeframes, plus pure Brownian motion, all return ~20 bars. There is no economic mechanism that would give a daily FX rate and a 4-hour crypto series the same cycle length. There is an obvious mechanical one: **it is the resonant period of the filter chain.** The pipeline outputs ~20 bars regardless of input.

`acf_half_period` confirms the absence of oscillatory coherence: a genuine oscillation must be strongly anti-correlated half a cycle away (pure sine = 0.995). EUR/USD scores 0.246; BTC scores 0.104.

---

## 5. Conclusions

1. **The premise as stated (Claim A) is unfalsifiable** and carries no information. It is a theorem, not a market insight.

2. **Claim B fails empirically on both assets.** No spectral peak distinguishable from noise, across 6 metrics × 4 nulls × 2 assets = 48 tests, minimum p = 0.070.

3. **Claim C is confirmed as an artefact mechanism.** The pipeline manufactures a ~20-bar oscillation from pure Brownian motion. Slutsky (1937) and Nelson & Kang (1981) predicted exactly this.

4. **Quantitative bound:** if a persistent 20-bar cycle existed carrying more than ~4–5% of return variance, it would have been detected with 95% probability on either asset. None was.

5. **The crypto arm closes the "EUR/USD is unusually efficient" escape.** BTC/USD H4 — less mature, more retail-driven, more regime-prone — shows *less* cycle structure than EUR/USD by both prominence and phase coherence.

6. **Volatility clustering is the real structure.** H(|returns|) = 0.658 (FX) and 0.766 (crypto), while H(returns) ≈ 0.5 for both. Null D reproduces everything the real data does.

### 5.1 Failed prediction (recorded)

Before seeing BTC data, the prediction was recorded that BTC prominence would exceed EUR/USD's, reasoning that stronger volatility clustering would feed the resonator more energy. **This was wrong** — BTC came in lower (2.91 vs 3.17). Recorded rather than dropped.

---

## 6. Impact on the indicator library

| Component | Status |
|---|---|
| SuperSmoother, Ultimate Smoother | **Unaffected.** Known frequency response, less lag than SMA at equal smoothing. True regardless of cycles. |
| FAMA / FRAMA / Decycler baselines | **Unaffected.** Trend extraction from an integrated process. Independently justified. |
| Fisher Transform (C1) | **Unaffected.** Nonlinear rescaling of normalised price position, not cycle-based. |
| RoofingFilter | **Valid as a band-pass filter.** The *interpretation* of its output as "the cycle" fails. |
| Cyber Cycle | **No evidence it measures anything beyond filtered noise** on either asset. |
| DominantCycle / adaptive-period methods | **Weakened.** The period they adapt to is unstable and indistinguishable from noise. |
| MESAStochastic, phasor/market-state | **Requires the same test** before library confidence. |

**The baseline work is on firmer ground than the oscillator work.** This is consistent with the pre-existing project finding that simple approaches outperform complex ones.

---

## 7. Limitations (stated explicitly)

This experiment tests:

- **One pipeline** — HP=48 / SS=10 / α=0.07. Other parameterisations untested.
- **Two assets, two timeframes.** No claim beyond these.
- **A fixed-period cycle.** Adaptive-period and time-varying-frequency cycles are not directly tested, though the period-stability result bears on them.
- **Persistent cycles.** A cycle appearing only in specific regimes could evade these aggregate metrics. Regime-conditional testing is not done here.
- **Indicator-level behaviour only.** This says nothing about whether a strategy using these indicators is profitable. Indicator validation ≠ strategy validation.

What is closed off is the specific claim that a measurable, extractable, phase-coherent cycle exists at the scale the Cyber Cycle targets, on these two assets.

---

## 8. Reproducibility

```
src/pipeline.py     Zorro-validated port; loop + vectorised, cross-checked
src/surrogates.py   DFA, Davies-Harte fGn, IAAFT, stochastic vol, sine control
src/metrics.py      six detection statistics, BURN_IN = 300
run_experiment.py   EUR/USD arm
run_btc*.py         BTC arm
out/                p-values, null distributions, power curves, figures
```

Zorro export scripts: `Test_CyberCycle_Surrogate.c`, `Test_CyberCycle_Surrogate_BTC.c`.
Seed 20260803. N = 1,000 surrogates per null.

**Known deviation:** `period_stability` uses `step=25` for EUR/USD and `step=50` for BTC (runtime; 5,927 vs 2,236 bars). Applied consistently to real and surrogate within each asset, so within-asset comparisons are valid; the raw stability values are not directly comparable across assets.

---

## 9. Recommended next actions

1. Re-run this test against `Reflex`, `ELI` and `MESAStochastic` before granting them library confidence.
2. Add regime-conditional testing — split by volatility state and re-test, to address the "intermittent cycle" limitation.
3. Reclassify the library explicitly into *trend extractors* (evidence-supported) and *cycle extractors* (unsupported on these assets).
4. Update Week 8 notes: the CyberCycle "VALIDATED ✅ (with conditions)" status should record that the conditions now include a failed cycle-existence test.
5. Carry the corrected framing into README: this is a **filter library with characterised frequency response**, not a cycle-extraction library.
