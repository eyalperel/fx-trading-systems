> ⚠️ **PARTIALLY SUPERSEDED, 2026-08-10 — see `Scope_Correction_2026-08-10.md`.**
>
> **Part 1 (findings) and Part 3 (limitations) stand unedited.** No measurement, p-value,
> positive control or stated bound is retracted or revised.
>
> **Part 2 §2.3 — forward-looking recommendations — is superseded.** Those recommendations
> produced roadmap Principles 6–7 and criterion C-7, all three of which are now withdrawn.
> The finding did not carry the weight of a gate on future indicator work: it covers three
> linear-projection mechanisms, two assets, one parameterisation and a 10–48 bar passband.
> Part 3 says as much, and is the reason for this correction rather than an argument
> against it.
>
> **Part 4 action list:** items 5 (add null gate) and 6 (reorganise Week 14 by evidence
> status) are void. Remaining items stand as recorded.
>
> **Also unaffected:** §1.5's statement that this is not a finding against band-pass
> filters — that distinction is now the project's operating principle rather than a caveat.

---

# Cycle Premise Null Test — Conclusions & Project Impact

**Date:** 2026-08-03
**Companion to:** `Cycle_Premise_Null_Test.md` (full method and results)
**Project state at time of writing:** Week 11 of 48, Phase 2 (Indicator Deep Dive)

---

## Part 1 — Conclusions

### 1.1 What was tested

Whether the oscillation produced by `RoofingFilter → CyberCycle` on real market data is distinguishable from the oscillation the same pipeline produces on data containing no cycle by construction.

Tested on EUR/USD D1 (2015–2024, 2,236 bars) and BTC/USD H4 (2020–2024, 5,927 bars), against four null models, on six detection metrics, with 1,000 surrogates per null.

### 1.2 What was found

**No null rejected on either asset.** 48 tests, minimum p = 0.070.

**The result is directional, not merely inconclusive.** Real markets scored *lower* on spectral peak prominence than the noise nulls — 8th percentile for EUR/USD, 6.6th for BTC. Pink noise and stochastic-volatility noise pushed through this pipeline produce a better-defined spectral peak than real market data does.

**The pipeline has a fingerprint.** Zero-crossing period was 19.51 bars (EUR/USD D1), 19.81 (BTC/USD H4), and 20.40 (pure Brownian motion). A daily FX rate, a 4-hour crypto series, and a random number generator all return ~20 bars. That is the resonant period of the filter chain, not a property of any market.

**Quantitative bound.** A positive control established that a 20-bar cycle carrying more than 4.4% (FX) or 5.0% (crypto) of return variance would have been detected with 95% probability. None was.

**The real structure is volatility, not returns.** DFA gave H(returns) ≈ 0.5 on both assets, but H(|returns|) = 0.658 (FX) and 0.766 (crypto). Null D — stochastic volatility with zero cycle and zero return memory — reproduced everything the real data does.

### 1.3 The three-claim decomposition

The premise "price = trend + cycle + noise" bundles claims of very different status:

- **Claim A (a decomposition exists)** — unfalsifiable. Guaranteed by the spectral representation theorem for any stationary process, including a random number generator. Carries no information.
- **Claim B (the cycle has identifiable, persistent peaks)** — fails empirically here, consistent with Granger (1966).
- **Claim C (filtering recovers the cycle)** — confirmed as an artefact mechanism. Slutsky (1937) and Nelson & Kang (1981) predicted that detrending and smoothing manufacture apparent cycles from random data. Demonstrated directly: pure Brownian motion through this pipeline yields a clean ~20-bar oscillation.

### 1.4 Ehlers contradicts himself, and mislabels his own measurement

In *Whiter Is Brighter* (2015) Ehlers abandons the deterministic-waveform-plus-noise model in favour of one comprised solely of pink noise. **This library therefore straddles two incompatible market models** — the dominant-cycle machinery assumes a measurable cycle; the spectral-dilation work assumes there isn't one.

Separately: he states market spectral power grows 6 dB per octave. That is f^−2 — **brown noise, i.e. a random walk** — not pink noise (f^−1, 3 dB/octave). Measured here: EUR/USD f^−1.835, BTC f^−1.837, synthetic random walk f^−1.848. His measurement is right; his label is wrong, and "spectral dilation" is simply integration.

### 1.5 What the finding does *not* say

This is the distinction that determines the project impact, so it is stated precisely:

> The finding is about **cycle extraction and cycle extrapolation**. It is not a finding that band-pass filters are useless.

A RoofingFilter still has a known, characterised frequency response. Its output is still a bounded, detrended, noise-reduced series. What fails is the *interpretation* of that output as "the market's cycle," and any use that depends on knowing the cycle's period or phase in order to project it forward.

An oscillator that crosses zero when recent momentum flips relative to a filtered baseline does not require a cycle to exist. An indicator that adapts its parameters to a *measured dominant cycle period* does.

---

## Part 2 — Project Impact

### 2.1 Impact summary

| Area | Impact | Action |
|---|---|---|
| Locked baselines (FAMA, FRAMA) | **None** | No change |
| Fisher Transform as Strategy 1 C1 | **None** | No change |
| Reflex as Strategy 1 C2 | **Low** — fixed-period, not dominant-cycle-adaptive | Reframe justification |
| MESA Stochastic as Strategy 2 C1 | **None** — verified fixed-period, not cycle-adaptive | Reframe justification + header note |
| CyberCycle | **High** — no evidence it measures anything beyond filtered noise | Reclassify |
| DominantCycle / adaptive-period methods | **High** — the period they adapt to is unstable and noise-indistinguishable | Reclassify, do not use for parameter adaptation |
| Week 12 Day 5 (Correlation Cycle Indicators) | **High** — tests the thing just shown absent | Revise or drop |
| Week 14 NNFX component mapping | **Medium** — organising principle should change | Reorganise by mechanism |
| Phase 2.5 Backtesting Bootcamp (W15–17) | **Additive** — surrogate testing generalises to strategies | Add as standard tool |
| Phase 4 ML / Regime Detection (W26–33) | **Redirected and strengthened** | Anchor regimes on volatility |
| Phase 3 Strategy Development (W18–25) | **Low** | Carry the reclassification forward |

### 2.2 Locked strategy decisions — do they survive?

**Strategy 1 (FAMA baseline + Fisher C1 + Reflex C2): survives intact.**

- FAMA is a trend extractor operating on an integrated process. Untouched.
- Fisher Transform is a nonlinear rescaling of normalised price position. Not cycle-based. Untouched.
- Reflex uses a fixed `Length` parameter, not a measured dominant cycle. Its justification changes from "captures cycle turning points" to "detrended momentum oscillator with characterised frequency response," but the indicator itself and its validation stand.

**Strategy 2 C1 (MESA Stochastic): survives. Verified 2026-08-03.**

Source inspection confirms the implementation takes three **fixed** integer parameters (`StochPeriod`, `HPPeriod`, `SSPeriod`) with no `DominantCycle` call and no adaptive period:

```
RoofingFilter(Price, HPPeriod, SSPeriod)
  → rolling min/max normalisation over StochPeriod
  → SuperSmoother2Pole(·, SSPeriod)
```

Despite the "MESA" name, this is **not** a maximum-entropy spectral estimator and does not measure a dominant cycle. It is a normalised band-pass oscillator. Its justification is reframed from "measures cycle position" to "measures normalised position within a band-passed series" — a meaningful signal whether or not a cycle exists.

**Additional point in its favour, surfaced by this analysis:** the stochastic stage rescales by rolling range, which is automatic gain control. Project notes already record AGC normalisation as mandatory for BTC/USD H4, where oscillator amplitude varies ~10× across regimes. MESA Stochastic satisfies that requirement structurally, and this is a genuine functional advantage independent of the cycle premise. Raw CyberCycle, by contrast, has no AGC — its output on BTC is in price units and scales with price level (measured RMS 668.9 at BTC price levels vs 0.0057 for EUR/USD).

Naming caution for the library: **"MESA" in this indicator's name does not indicate cycle measurement.** Worth a note in the file header to prevent a future reader — including a future employer reviewing the repo — from inferring a dependency that is not there.

**Nothing in this finding invalidates the FAMA/FRAMA baseline lock or the 16+ indicator library entries.** The affected set is specifically the cycle-extraction and cycle-adaptive subset.

### 2.3 Changes recommended to the roadmap

**Week 12, Day 5 — "Correlation Cycle Indicators … use autocorrelation to measure cycle dominance."**

This is the one active-phase item in direct conflict. It plans to spend time measuring a quantity this experiment found indistinguishable from noise on both assets.

Recommended: **do not drop it — repurpose it.** Ehlers' `Correlation_As_A_Cycle_Indicator.pdf` is already in project files. Implement it, then run the null test against it. Either it rejects (a genuine positive, and a significant one) or it doesn't (a second independent confirmation on a different indicator family). Both outcomes are more valuable than the original plan, and the cost is unchanged.

**Week 14 — NNFX component mapping.**

The mapping into NNFX roles should be organised by *mechanism* rather than by Ehlers' naming:

| Class | Mechanism | Evidence status |
|---|---|---|
| Trend extractors | Low-pass / adaptive low-pass | Supported |
| Band-pass oscillators | Detrend + smooth | Valid as filters; cycle interpretation unsupported |
| Normalisers | Nonlinear rescaling | Independent of cycle premise |
| Cycle-period estimators | Dominant-cycle measurement | **Unsupported on tested assets** |

This is a better organising principle for the portfolio than the article-order grouping, because it maps mechanism to justification.

**Phase 2 validation protocol — add a gate.**

The existing gate is: implement → FX validate → crypto validate → library. Recommended addition for any indicator whose justification rests on cycle extraction:

> **Null gate:** the indicator's output on real data must be distinguishable from its output on matched surrogates, or the indicator enters the library explicitly classified as a filter rather than a cycle detector.

This costs little now that the harness exists — the surrogate code is reusable and runs in ~2 minutes per asset.

**Phase 2.5 Backtesting Bootcamp (Weeks 15–17) — add surrogate testing as a standard tool.**

This is the highest-value forward extension. The same methodology generalises directly from indicators to strategies: run the strategy on 1,000 surrogate price series and ask whether its Sharpe ratio is distinguishable from the null distribution. That is a stronger overfitting check than walk-forward alone, because walk-forward tells you whether parameters generalise across time while surrogate testing tells you whether the *edge exists at all*.

This directly serves the roadmap's existing "Optimization ≠ improvement" principle, and it gives Weeks 15–17 a concrete tool rather than a warning.

**Phase 4 ML / Regime Detection (Weeks 26–33) — redirected, and strengthened.**

The measured structure is unambiguous: H(returns) ≈ 0.5, H(|returns|) = 0.658–0.766. **The exploitable memory is in volatility.** Regime detection anchored on volatility state is grounded in measured structure; regime detection anchored on cycle state is not.

This narrows the ML phase usefully. It also aligns with the existing "simple beats complex" finding — a volatility-regime classifier is a far simpler object than a cycle-state classifier, and it has measured structure behind it.

### 2.4 Impact on the portfolio narrative

This is a net gain, and the strongest single artifact produced so far.

The repo's claim changes from *"I implemented Ehlers indicators"* — which is common on GitHub — to *"I implemented Ehlers indicators, tested the premise they rest on, and found it unsupported on two assets."* The second is a much rarer claim and demonstrates exactly the skills systematic-trading employers screen for: surrogate methodology, positive controls, falsification, and willingness to publish a negative result about your own work.

Specific portfolio-relevant elements now evidenced:

- Null-hypothesis construction with multiple nested nulls
- Detection-power calibration (most retail quant work has no positive control at all)
- Cross-language port validation to numerical precision before drawing inference
- A recorded failed prediction, kept rather than dropped
- A documented self-correction (Null C mis-specification, caught and fixed mid-experiment)

**README framing recommendation:** describe the library as *a filter library with characterised frequency response, validated against null models* — not as a cycle-extraction library.

### 2.5 What deliberately does not change

- Week 11 status, ELI FAIL documentation, Reflex and MESA Stochastic validations stand as recorded.
- The 48-week structure, phase boundaries and timelines are unchanged. This adds no weeks.
- Strategy 1 remains locked.
- The existing distinction between indicator-level and strategy-level validation is unchanged and is reinforced — this experiment is squarely indicator-level and says nothing about P&L.

---

## Part 3 — Limitations restated

Carried forward from the main document so the impact assessment is not read as broader than the evidence:

- **One parameterisation** (HP=48 / SS=10 / α=0.07). Other settings untested.
- **Two assets, two timeframes.** No claim beyond EUR/USD D1 and BTC/USD H4.
- **Fixed-period cycles.** Adaptive and time-varying-frequency cycles not directly tested, though the period-instability result bears on them.
- **Persistent cycles.** A cycle appearing only in specific regimes could evade these aggregate metrics. Regime-conditional testing is not done here and is the most defensible route to challenging this result.
- **Indicator-level only.** Says nothing about strategy profitability.

---

## Part 4 — Action list

| # | Action | When | Effort |
|---|---|---|---|
| 1 | ~~Verify MESA Stochastic period handling~~ — **DONE 2026-08-03: fixed-period, survives** | — | done |
| 2 | Commit experiment code, results and both documents to repo | Now | 30 min |
| 3 | Amend Week 8 notes: CyberCycle status to record the failed cycle-existence test | Now | 20 min |
| 4 | Revise Week 12 Day 5 from "measure cycle dominance" to "implement + null-test" | Before Week 12 | 5 min |
| 5 | Add null gate to Phase 2 validation protocol | Before Week 12 | 15 min |
| 6 | Reorganise Week 14 component mapping by mechanism | Week 14 | included in W14 |
| 7 | Add surrogate strategy testing to Phase 2.5 | Roadmap edit now, use W15–17 | 15 min |
| 8 | Redirect Phase 4 regime detection to volatility regimes | Roadmap edit now | 15 min |
| 9 | Update README framing to "filter library, null-validated" | Next Day 6 | included in Day 6 |
| 10 | Re-run null test on Reflex and MESA Stochastic | Week 12–14 | ~1 hr each |
| 11 | Add header note to `MESAStochastic.c`: "MESA" is naming only; no dominant-cycle dependency | Now | 5 min |

Roadmap version after these edits: **v4.3**.
