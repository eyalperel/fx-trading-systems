# FX & Crypto Algorithmic Trading Systems

A systematic 48-week program building algorithmic trading systems using the **Zorro
platform**, **John Ehlers DSP-based indicators**, and the **NNFX (No Nonsense Forex)**
framework.

**Two parallel goals:**
1. Build genuinely profitable, walk-forward validated trading systems
2. Build a professional portfolio for employment in systematic/quantitative trading

> **What this repository is, precisely.** A **filter library with null-validated
> classification**, plus the evidence trail behind every decision. Each indicator is
> implemented in Light-C, cross-validated on two assets, and classified by what it can
> actually be shown to do — not by what its source article claims. **No strategy-level
> backtest, walk-forward optimisation, or P&L result exists yet.** That work begins in
> Phase 2.5 (Week 15). Claims here are indicator-level, and the distinction is maintained
> throughout.

---

## Current Status

**Week 12 of 48 — Phase 2: Indicator Deep Dive**

- ✅ 21 indicators implemented and validated (+ 2 documented FAIL / reclassified)
- ✅ Two strategy baselines locked; both C1 slots locked
- ⚠️ **Both C2 slots open questions** — see [Strategy Decisions](#strategy-decisions)
- ✅ Cycle premise null-tested by 3 independent mechanisms (64 tests, no rejection)
- 🔄 Weeks 13–14: complete library (C2 candidates, ATR, exit slots)
- ⏳ Weeks 15–17: Backtesting Bootcamp — **first strategy-level results**
- ⏳ Weeks 18+: strategy assembly, ML integration, live deployment

---

## The Cycle Premise Null Test

Ehlers' indicator corpus rests on the premise that price = trend + **cycle** + noise, and
that the cycle component is measurable and persistent. Weeks 11–12 tested that premise
against surrogate data rather than assuming it.

| Mechanism | Statistic | Tests | Min p | Result |
|---|---|---|---|---|
| Band-pass (Roofing → CyberCycle) | Spectral peak prominence | 48 | 0.070 | No rejection |
| Quadrature projection (Correlation Cycle) | Phase coherence | 8 | 0.379 | No rejection |
| Autocorrelation (periodogram) | Correlogram peak prominence | 8 | 0.117 | No rejection |

**Three mechanistically distinct methods. 64 tests. No rejection.**

Nulls: IID random walk, Hurst-matched fractional Brownian motion, IAAFT
phase-randomised surrogates, stochastic volatility.

### What was found instead

- **No detectable cycle** in EUR/USD D1 or BTC/USD H4. A 20-bar cycle carrying >4.4% (FX)
  / >5.0% (crypto) of return variance would have been detected at 95% power.
- **Filters manufacture the cycles they report.** The ~20-bar oscillation attributed to
  the market is the filter chain's resonance: pure Brownian motion returns 20.40 bars.
- **Phase coherence is a window artefact.** Correlation Cycle reads R = 0.9706 on
  EUR/USD — and R = 0.9705 on a random number generator. Consecutive 20-bar windows share
  19 of 20 bars, so phase regularity is manufactured by construction.
- **Real data often looks *less* cyclic than noise.** EUR/USD scores at the 5th–8th
  percentile of null distributions on two independent statistics — noise produces sharper
  spectral peaks than the market does.
- **Long memory is in volatility, not returns.** H(returns) ≈ 0.5 both assets;
  H(|returns|) = 0.658 (FX) / 0.766 (crypto). This redirected the Phase 4 regime work onto
  volatility state.

### Consequences

Indicators justified by **trend extraction, normalisation or momentum** are unaffected —
their mechanisms survive independently. Indicators justified by **cycle extraction** were
reclassified as filters. Adaptive-period methods driven by a measured dominant cycle are
**not used for parameter adaptation**.

> **Why this matters methodologically.** The original validation plan asked whether an
> indicator's reading "aligns with visually obvious cycle/trend periods." That check would
> have **passed** — on pure noise the Correlation Cycle's phase looks coherent and its
> state variable flips convincingly on a third of all bars. Without a surrogate
> comparison, the indicator appears to work.

📄 [`docs/research/`](docs/research/) — full methodology, results, and reproducible harnesses

---

## Technology Stack

| Tool | Role |
|------|------|
| **Zorro Platform** (Light-C) | Indicator implementation, backtesting, live execution |
| **Python / Jupyter / NumPy** | Statistical validation, surrogate testing, cross-asset analysis |
| **Git / GitHub** | Version control, portfolio documentation |
| **102 Ehlers TASC articles** | Primary source material |

---

## Indicator Library — Weeks 5–12

Validated on **EUR/USD D1 (2015–2024)** and **BTC/USD H4 (2020–2024)** with identical
parameters — no per-asset retuning.

| Week | Indicators | Role | Status |
|------|-----------|------|--------|
| 5 | SuperSmoother 2-Pole, 3-Pole, Ultimate Smoother | Foundation filters | ✅ Library |
| 6 | HighPassFilter, RoofingFilter, Decycler | Noise isolation / preprocessors | ✅ Library |
| 7 | MAMA, FAMA | Baseline | ✅ **Strategy 1 Baseline: FAMA** |
| 8 | CyberCycle, EBS, Bandpass | C1/C2 candidates | ⚠️ CyberCycle **reclassified as filter** (Week 11 null test) |
| 9 | FRAMA, Laguerre Filter, DSMA | Baseline, smoothing | ✅ **Strategy 2 Baseline: FRAMA** |
| 10 | Fisher Transform, Inverse Fisher, COG | C1 confirmation | ✅ **Fisher = C1, Strategy 1** |
| 11 | Reflex, MESA Stochastic, ELI | C1/C2 confirmation | ✅ **MESA Stochastic = C1, Strategy 2**. ELI ❌ documented FAIL |
| 12 | Recursive Median + RMO, Alpha-Beta Filter, Correlation Cycle | Noise reduction, C2 candidate | ⚠️ All three reclassified — see below |

### Week 12 outcomes

| Indicator | Outcome |
|---|---|
| **Recursive Median (RM)** | Validated, **use case narrowed**. Justified for crypto by "flash crash resilience" — refuted. BTC's 99th-percentile moves *don't revert* (median retracement −2.3%), so they are real price discovery. A median cannot distinguish a bad tick from a regime break and rejects both. Lag-matched, RM tracks price **worse** than a plain EMA (RMSE 993 vs 785). Appropriate only for genuinely corrupted input — tick feeds, thin venues. |
| **RMO** | **Eliminated as Strategy 2 C2** — \|ρ\| = 0.799 with MESA Stochastic against a pre-registered 0.65 threshold. 85% sign agreement. |
| **Alpha-Beta Filter** | **Renamed from "Ehlers Kalman."** No such article exists in the 102-article library; it was mis-mapped. Not a Kalman filter — no covariance propagation. "Optimal minimum-variance estimator" **retracted**. Documented range "Gain 0.6–0.9" was wrong: it *amplifies* noise above Gain 0.246 (σ 3.45 at 0.9). Output leads by exactly 1 bar — a forecast, not a smoother. |
| **Correlation Cycle** | Implemented, **classified as a filter, not a cycle detector**. Phase/state carry no cyclicality information noise doesn't also carry. |

---

## Strategy Decisions

### Strategy 1: FAMA Baseline + Fisher C1 + Reflex C2 ⚠️

| Component | Indicator | Status |
|-----------|-----------|--------|
| Baseline | FAMA | ✅ Locked |
| C1 | Fisher Transform (Period=10) | ✅ Locked |
| C2 | Reflex (Length=20) | ⚠️ **FLAGGED — open question** |
| ATR / Exit | TBD (Weeks 13–14) | — |

> **Reflex C2 audit (Week 12).** Locked in Week 11 on qualitative grounds ("different
> mathematical family"). Week 12 applied the quantitative criterion retroactively:
> **|ρ| with Fisher = 0.597 (FX) / 0.595 (BTC)** — conditional band on both assets.
> A preliminary information-gain test is contradictory: the C2 filter **adds** +6.90 bp on
> EUR/USD and **destroys** −14.93 bp on BTC/USD.
>
> That preliminary figure is a crude proxy — no entry rules, no costs, arbitrary horizon.
> It is not sufficient to unlock the slot, but it is sufficient to flag it. **Formal
> resolution deferred to Phase 2.5/3**, where strategy-level machinery exists.

### Strategy 2: FRAMA Baseline + MESA Stochastic C1 ⚠️

| Component | Indicator | Status |
|-----------|-----------|--------|
| Baseline | FRAMA | ✅ Locked |
| C1 | MESA Stochastic (20, 48, 10) | ✅ Locked |
| C2 | **OPEN** | ⚠️ No candidate accepted (Week 12) |
| Exit | TBD | — |

**Why two strategies:** FAMA (phase-locked adaptive) and FRAMA (fractal adaptive) use
fundamentally different adaptation mechanisms — diversification by mechanism, not by
parameter. Extended to C1 selection: Strategy 2 shares no confirmation indicator with
Strategy 1.

### Why both C2 slots are open

Week 12 established that **C2 selection cannot be completed at indicator level.**

Correlation was the original criterion. The Strategy 1 audit showed why that is
insufficient: Reflex and Fisher correlate at ≈0.60 on *both* assets, yet the C2 filter
adds edge on one and destroys it on the other. **Near-identical correlation, opposite
value.** Correlation cannot distinguish these cases.

The criterion was therefore revised — *before* Week 13 generated any data — into a
two-stage test:

- **C-3a** — correlation screen, demoted to a *warning* rather than a verdict
- **C-3b** — conditional information gain: does C1+C2 beat C1 alone out-of-sample, with
  costs and walk-forward, on **both** assets? **Decisive.**

C-3b is strategy-level. Phase 2 can shortlist candidates; the deciding test belongs to
Phase 3.

📄 [`docs/indicators/C2_Selection_Criteria_PreRegistered.md`](docs/indicators/C2_Selection_Criteria_PreRegistered.md)

---

## Method: Pre-Registration

Selection criteria are written and pushed to this public repository **before** the data
that tests them exists. Thresholds are not revised after seeing results.

**Worked example — Week 12.** Criteria registered in commit `e4b1f5b`, including a stated
prediction that RMO's correlation with C1 would fall in 0.40–0.65 and a 0.65 elimination
threshold. Measured two days later: **0.799**. The prediction was wrong, the threshold was
not moved, and the candidate was eliminated. The failed prediction is in the git history
with a timestamp preceding the data.

**Diagnosis of the failed prediction:** it conflated *mechanism exists* with *mechanism
operates*. RMO's non-linear median gate fires only on outliers — `corr(RM, plain EMA) =
0.9965`. On ~99% of bars the filter is effectively linear, so it behaves as a band-pass,
which is what MESA Stochastic is.

**Amendments are dated and additive.** When C-3 was revised, the original text was
preserved unedited and the amendment appended below it, so the criterion under which RMO
was eliminated remains visible. The elimination was not reopened under the new rule.

---

## Engineering Principles

- **Theory before code** — Days 1–2 of each week are pure theory. Week 12's predicted
  lag of 3.37 bars, derived before implementation, measured **3.366**.
- **Null-gate cycle claims** — any indicator justified by cycle extraction must be
  distinguishable from matched surrogates, or it enters classified as a filter
- **Mechanism determines the evidential bar** — for surviving mechanisms a good backtest
  is corroboration; for cycle-justified ones it is coincidence until surrogate-confirmed
- **Validate the instrument before the measurement** — first-difference cross-correlation
  reported *0.00 bars* of lag for an EMA with analytic lag 1.50. Any measurement method is
  checked against a known ground truth first.
- **No per-asset retuning** — parameters must generalise; retuning is overfitting
- **Multi-pair testing is confirmation, not search** — FX majors share the USD leg
  (pairwise 0.6–0.9), so 20 pairs give 3–5 effective independent samples while
  multiple-comparison inflation prices as if there were 20
- **Document failures and retractions** — ELI (FAIL), RMO (eliminated), Alpha-Beta
  (attribution retracted), CyberCycle and Correlation Cycle (reclassified)
- **Correct the sources** — three source errors documented in Week 12 alone: Ehlers'
  inverted critical-period description, the mis-attributed Kalman article, and a
  monotonicity ratchet that manufactures the trend-mode signature it claims to detect

---

## Repository Structure

```
fx-trading-systems/
├── indicators/ehlers/          # 21 DSP indicators (Light-C)
├── strategies/tests/           # Zorro test scripts — one per indicator
├── analysis/
│   ├── null_tests/             # Surrogate-data harnesses (reproducible, seeded)
│   ├── notebooks/              # Jupyter validation notebooks
│   └── scripts/                # Shared Python utilities
├── docs/
│   ├── ZORRO_LIGHTC_GOTCHAS.md # Platform reference — silent-failure modes marked
│   ├── indicators/             # Theory, criteria, findings, decisions
│   ├── research/               # Null tests and conclusions
│   ├── roadmap/                # Program roadmap (versioned)
│   └── weekly_reports/         # Weekly progress notes
└── research/articles/          # 102 Ehlers TASC articles
```

---

## Reproducibility

Null-test harnesses use fixed seeds and regenerate the published figures exactly:

```bash
cd analysis/null_tests
python run_experiment.py                 # Week 11 — spectral prominence
python phase_coherence_null_test.py      # Week 12 — phase coherence + periodogram
```

Every claim above traces to a commit. Predictions carry timestamps preceding the data
that tested them.

---

*Systematic trading is built one indicator at a time — and every claim gets tested against
the null.*
