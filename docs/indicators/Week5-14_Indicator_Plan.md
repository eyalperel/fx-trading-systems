# Week 5-14 Indicator Implementation Plan
**Created:** Week 4 Day 6  
**Program:** Unified FX & Crypto Algorithmic Trading — Phase 2  
**Purpose:** Curated selection of 26 Ehlers indicators for systematic implementation  
and validation across FX (EUR/USD D1) and crypto (BTC/USD H4) markets

---

## Infrastructure Already In Place (End of Week 4)

**Indicator library** (`/indicators/ehlers/`):
- `InstantTrendline.c` — validated, fixed version recommended (DC=20)
- `DominantCycle.c` — validated, Griffiths method
- `SuperSmoother.c` — basic version, will be replaced by Week 5 validated version

**Validation framework** (`/analysis/`):
- `analysis/scripts/indicator_metrics.py` — lag, SNR, cross-asset, validation report
- `analysis/notebooks/Indicator_Analysis_Template.ipynb` — 8-section reusable template

**Data pipelines**:
- EUR/USD D1: Zorro → CSV → Python (2015-2024, 2336 bars)
- BTC/USD H4: Zorro → CSV → Python (2020-2024, ~6000 bars)

**Key finding from Week 4:**
Fixed period outperforms adaptive on both EUR/USD D1 and BTC/USD H4 for
InstantTrendline. DominantCycle instability in Stage 3 costs more than it gains.
Same period (DC=20) works on both asset classes.

---

## Working Methodology (Every Week, Without Exception)

| Day | Focus | Rule |
|---|---|---|
| Day 1 | Read article — understand the problem it solves | No code yet |
| Day 2 | Work through the math — formulas, coefficients, why they are what they are | No code yet |
| Day 3 | Implement in Light-C — code flows from understood math | First code |
| Day 4 | Validate on EUR/USD D1 — run analysis template, interpret results | PASS/FAIL gate |
| Day 5 | Validate on BTC/USD H4 + parameter sensitivity | Cross-asset mandatory |
| Day 6 | Documentation, Git commit, weekly retrospective | Library entry |

**Critical rule:** No coding before the math is understood. Days 1-2 are always
reading and theory. This prevents bugs that are hard to diagnose and implementations
that work by accident rather than by design.

---

## PASS/FAIL Validation Criteria

An indicator **PASSES** and enters the library if ALL of:
- Visually tracks price in expected way (no obvious bugs)
- Lag ≤ comparable SMA of same period (cross-correlation measurement)
- SNR improved vs SMA of same period (quantified via indicator_metrics.py)
- Behaves consistently on both EUR/USD D1 and BTC/USD H4
- Zorro test script runs without errors or NaN values

An indicator **FAILS** if ANY of:
- Output diverges unexpectedly from price
- Worse lag than simple SMA of same period
- Produces NaN/infinite values on real data
- Zorro test script crashes

**Note for oscillator-type indicators (Weeks 8+):**
Lag vs SMA and SNR vs SMA do not apply cleanly to oscillators.
Additional metrics will be defined in Week 8: zero-crossing quality,
false signal rate, overbought/oversold accuracy.

---

## Weekly Deliverables (Same Every Week)

- `[IndicatorName].c` in `/indicators/ehlers/` (if PASS)
- `[IndicatorName]_Test.c` in `/strategies/tests/`
- Jupyter notebook in `/analysis/notebooks/[IndicatorName]_Analysis.ipynb`
- `/docs/indicators/[IndicatorName]_Notes.md` (theory + implementation notes)
- Git commit with meaningful message
- Weekly retrospective

---

## Week 5 — Smoothing Filters
**Articles:** `Moving averages and smoothing filters.pdf` + `The Ultimate Smoother.pdf`  
**Why first:** SuperSmoother is Ehlers' foundational building block. It appears
*inside* MAMA, Cyber Cycle, Roofing Filter, and most other indicators in this plan.
Understanding it deeply before building on top of it is essential.

### Indicators
| # | Indicator | NNFX Role Hypothesis |
|---|---|---|
| 1 | SuperSmoother 2-pole | C1 input preprocessing / Baseline smoothing |
| 2 | SuperSmoother 3-pole | Alternative smoothing with more lag tradeoff |
| 3 | Ultimate Smoother | Zero-lag smoothing candidate |

### Theory Focus (Days 1-2)
- 2-pole IIR filter design: what is it minimizing?
- Key formula:
```
  c1 = exp(-1.414 * π / Period)
  b1 = 2 * c1 * cos(1.414 * π / Period)
  Filt = b1*Filt[1] - c1²*Filt[2] + ((1 - b1 + c1²)/2) * (Price + Price[1])
```
- What is the cutoff frequency? How does period affect it?
- 2-pole vs 3-pole: what does the extra pole add mathematically?
- Ultimate Smoother: what zero-lag claim does Ehlers make and how?

### Implementation Notes (Day 3)
- Zorro uses degrees not radians for trig — verify cos() call units
- SuperSmoother needs `series(0.0, 3)` for 3 bars of history
- 3-pole version needs `series(0.0, 4)`

### Validation Focus (Days 4-5)
- SuperSmoother should have less lag than SMA of same period
- Test periods: 10, 14, 20, 30 — plot SNR vs lag tradeoff curve
- Expected: FX optimal period 14-20, Crypto optimal 8-14 (verify or refute)
- 3-pole: more smoothing confirmed, lag tradeoff documented
- Parameter sensitivity: how does performance degrade outside optimal range?

### Validation Gate
- ✅ 2-Pole: lag < SMA(same period), no artifacts, FX + Crypto tested
- ✅ 3-Pole: more smoothing confirmed, lag tradeoff documented
- ✅ Parameter guidelines written per asset class
- ✅ Ultimate Smoother: zero-lag claim verified or refuted

---

## Week 6 — High-Pass Filters & Roofing Filter
**Articles:** `Optimal Detrending.pdf` + `Whiter Is Brighter.pdf` + `Decyclers.pdf`  
**Why:** High-pass filters isolate the cycle component by removing trend.
The Roofing Filter (HP + SS) is the standard input for cycle oscillators (Week 8).
Must be understood before oscillators can be implemented correctly.

### Indicators
| # | Indicator | NNFX Role Hypothesis |
|---|---|---|
| 4 | High-Pass Filter (2-pole) | Trend removal / oscillator input preprocessing |
| 5 | Roofing Filter (HP + SS) | Band-pass / standard oscillator preprocessor |
| 6 | Decycler | Trend isolation alternative |

### Theory Focus (Days 1-2)
- HP filter removes low-frequency trends, passes high-frequency cycles
- Roofing Filter = High-Pass → then → SuperSmoother:
  - HP removes trend (keeps cycles)
  - SS removes noise above cutoff (keeps dominant cycle only)
  - Result: de-trended, de-noised cycle component
- Alpha calculation: controls cutoff frequency
- Decycler = Price - HighPass(Price) (inverse relationship to HP)
- Why is the Roofing Filter the correct input for oscillators?

### Implementation Notes (Day 3)
- HP Filter output should oscillate around zero (not track price)
- Roofing Filter depends on Week 5's SuperSmoother — import it
- Decycler: `Decycler = Price - HighPassFilter(Price, Period)`

### Validation Focus (Days 4-5)
- HP Filter: output oscillates around zero — verify visually
- Roofing Filter: output looks like a smooth oscillator — three-panel chart
- Parameter combinations: HP(40)/SS(10) vs HP(20)/SS(10) vs HP(40)/SS(20)
- Ehlers default HP=48, SS=10 — verify on real data
- Crypto: Roofing Filter should reveal crypto cycles with higher amplitude

### Validation Gate
- ✅ HighPassFilter: oscillates around zero, trend removed
- ✅ RoofingFilter: clean cycle isolation confirmed
- ✅ Decycler: trend isolation working
- ✅ All tested on FX + Crypto
- ✅ NNFX role confirmed: input preprocessor for Week 8 oscillators

---

## Week 7 — MESA Adaptive Moving Average (MAMA/FAMA)
**Article:** `MESA Adaptive Moving Averages.pdf`  
**Why:** MAMA is Ehlers' most sophisticated trend indicator. Uses Hilbert Transform
to measure instantaneous phase and adapt speed to the market. Primary Baseline
candidate. Most complex implementation in the plan — two full days of theory required.

### Indicators
| # | Indicator | NNFX Role Hypothesis |
|---|---|---|
| 7 | MAMA | Baseline (primary candidate) |
| 8 | FAMA | Baseline companion — MAMA/FAMA crossover = trend signal |

### Theory Focus (Days 1-2)
- MAMA tracks fast cycles, FAMA tracks slow (following MAMA)
- Key concept: Phase rate of change → adaptive alpha
  - High phase rate → high alpha → fast MAMA
  - Low phase rate → low alpha → slow MAMA
- MAMA/FAMA crossover = trend signal (smart EMA crossover)
- Requires Hilbert Transform: I (in-phase) and Q (quadrature) components
- Understand I/Q extraction fully before attempting implementation
- FastLimit (0.5) and SlowLimit (0.05): what do these bound?

### Implementation Notes (Day 3)
- Most complex implementation in Weeks 5-14
- Sequence: I/Q extraction → instantaneous period → alpha → MAMA → FAMA
- Verify each stage independently before proceeding to next
- Do not rush — each stage must work before the next is built

### Validation Focus (Days 4-5)
- MAMA more responsive than SMA, FAMA smoother than MAMA — verify
- Does MAMA/FAMA crossover align with real trend changes on EUR/USD?
- Crypto: MAMA should adapt faster (higher volatility → higher phase rate)
- FastLimit/SlowLimit parameter sensitivity

### Validation Gate
- ✅ MAMA/FAMA: crossovers align with trend changes
- ✅ Adaptive behavior confirmed (faster in volatile periods)
- ✅ NNFX role confirmed: Baseline primary candidate
- ✅ Tested FX + Crypto, comparison with InstantTrendline documented

---

## Week 8 — Cycle Oscillators
**Articles:** `Adaptive Trends And Oscillators.pdf` + `Measuring Market Cycles.pdf`
+ `The Bandpass Indicator.PDF`  
**Why:** Cyber Cycle gives the cycle component to complement MAMA's trend.
Together they describe the full market. C1/C2 candidates for ranging markets.
**Important:** Standard validation metrics (lag vs SMA, SNR vs SMA) do not apply
to oscillators. Extended metrics must be defined this week.

### Indicators
| # | Indicator | NNFX Role Hypothesis |
|---|---|---|
| 9 | Cyber Cycle | C1/C2 — cycle-mode oscillator |
| 10 | Even Better Sinewave (EBS) | C1/C2 — refined, fewer false signals |
| 11 | Bandpass Indicator | C1/C2 — alternative cycle oscillator |

### Theory Focus (Days 1-2)
- Cyber Cycle: uses Roofing Filter input — measures cycle state, not trend
- Works best in cycle mode (ranging), produces false signals in trend mode
- EBS: Ehlers' improvement on Cyber Cycle — what specifically is improved?
- Bandpass: frequency-domain approach — how does it differ from Cyber Cycle?
- Market mode detection: MAMA phase + Cyber Cycle amplitude

### Implementation Notes (Day 3)
- Cyber Cycle input = RoofingFilter output (Week 6), not raw price
- Output should oscillate approximately ±1
- Verify: does NOT track trend (returns to zero during trending periods)

### Validation Focus (Days 4-5)
- Extended oscillator metrics (new this week):
  - Zero-crossing quality: do crossings align with cycle turns?
  - False signal rate: how many crossings during strongly trending markets?
  - Amplitude consistency: does ±1 range hold across volatility regimes?
- Test Cyber Cycle during EUR/USD 2022 strong downtrend — should show high false signals
- Build simple market mode detector: MAMA phase + Cyber Cycle amplitude
- Crypto: often more time in cycle mode → these may be more useful here

### Validation Gate
- ✅ Cyber Cycle: oscillates cleanly, not trend-following
- ✅ EBS vs Cyber Cycle: signal quality comparison documented
- ✅ NNFX role: C1/C2 in cycle-regime strategies
- ✅ Market mode detector prototype working

---

## Week 9 — Adaptive Trend Indicators
**Articles:** `Fractal Adaptive Moving Averages.pdf` + `Laguerre Filters.pdf`
+ `The Deviation-Scaled Moving Average.pdf`  
**Why:** FRAMA adapts via fractal dimension — fast in trends, slow in chop.
Direct comparison with MAMA (Week 7) drives final Baseline selection for Phase 3.

### Indicators
| # | Indicator | NNFX Role Hypothesis |
|---|---|---|
| 12 | FRAMA | Baseline alternative — especially for chop-heavy FX |
| 13 | Laguerre Filter | C1 or Baseline — simple single-parameter adaptive |
| 14 | Deviation-Scaled MA | C1 — volatility-adaptive trend |

### Theory Focus (Days 1-2)
- FRAMA: alpha = exp(-4.6*(D-1)) where D is fractal dimension
  - D=1 (trend) → alpha=1 (fast). D=2 (random walk) → alpha≈0 (slow)
- FRAMA vs MAMA: fractal structure vs instantaneous Hilbert phase — when does each win?
- Laguerre Filter: gamma controls memory depth
  - High gamma → long memory → smooth but lagging
  - Low gamma → short memory → responsive but noisy
- Deviation-Scaled MA: adapts speed based on recent price deviation

### Implementation Notes (Day 3)
- FRAMA: Period must be even (splits into two halves for fractal calculation)
- Uses HH() and LL() Zorro functions
- Laguerre: simpler implementation, good entry point for adaptive mechanics

### Validation Focus (Days 4-5)
- FRAMA vs MAMA: which is smoother in chop? Which is faster in trend?
- This comparison directly informs Baseline selection in Week 18
- Crypto: higher fractal dimension → FRAMA slows more in ranging crypto (verify)
- Laguerre gamma sweep: 0.3, 0.5, 0.7, 0.9
- Recommended: FX gamma 0.7-0.8, Crypto 0.5-0.7 (verify or refute)

### Validation Gate
- ✅ FRAMA: fast in trend, slow in range confirmed
- ✅ MAMA vs FRAMA comparison documented — Baseline candidate ranked
- ✅ Laguerre: gamma guidelines per asset class
- ✅ NNFX role: Baseline or C1

---

## Week 10 — Momentum & Transform Indicators
**Articles:** `Using The Fisher Transform.PDF` + `The Inverse Fisher Transform.pdf`
+ `The Center Of Gravity Oscillator.pdf`  
**Why:** Fisher Transform converts price to Gaussian distribution where extremes
have clear statistical meaning. More rigorous than arbitrary RSI overbought levels.

### Indicators
| # | Indicator | NNFX Role Hypothesis |
|---|---|---|
| 15 | Fisher Transform | C1/C2 — statistically meaningful overbought/oversold |
| 16 | Inverse Fisher Transform | Signal booster — rescales any oscillator to ±1 |
| 17 | Center of Gravity Oscillator | C1/C2 — zero-lag oscillator |

### Theory Focus (Days 1-2)
- Fisher Transform: transforms price to Gaussian normal distribution
  - Extreme values (±2.5) have known statistical probability — not arbitrary
  - Formula: Fisher = 0.5 * ln((1+x)/(1-x)) where x is normalized price [-1,1]
- Inverse Fisher Transform: sigmoid function rescales any oscillator to (-1, +1)
  - Makes signals more decisive — applies to ANY oscillator as wrapper
- Center of Gravity: weighted sum approach — how does it achieve zero lag?

### Implementation Notes (Day 3)
- Fisher Transform: clamp input to ±0.999 to avoid log(0) division error
- Inverse Fisher: design as a general wrapper function applicable to any series
- Center of Gravity: straightforward weighted sum implementation

### Validation Focus (Days 4-5)
- Fisher Transform: do extreme values (±2.5) align with price turning points?
- Crypto threshold: ±3.0 instead of ±2.5? (higher volatility)
- Inverse Fisher applied to Cyber Cycle: does signal quality improve?
- Center of Gravity: zero-lag claim — verify with cross-correlation

### Validation Gate
- ✅ Fisher Transform: extreme values align with turning points
- ✅ Inverse Fisher: signal quality improvement confirmed
- ✅ Center of Gravity: lag measurement documented
- ✅ NNFX role: C1/C2

---

## Week 11 — Zero-Lag & Predictive Indicators
**Articles:** `Reflex_A_New Zero-Lag Indicator.pdf` + `Predictive And Successful
Indicators.pdf` + `Moving Averages Part 2 Ehlers Leading Indicator (ELI).pdf`  
**Why:** After 6 weeks of DSP study, zero-lag claims can now be evaluated
rigorously. Compare against InstantTrendline already in library.

### Indicators
| # | Indicator | NNFX Role Hypothesis |
|---|---|---|
| 18 | Reflex | C1 — most recent Ehlers zero-lag work (2020) |
| 19 | Predictive MA | C1 — price derivatives for lag reduction |
| 20 | Ehlers Leading Indicator (ELI) | C1 — direct comparison with InstantTrendline |

### Theory Focus (Days 1-2)
- Reflex (2020): Ehlers' most recent smoothing work — what new approach?
- Predictive MA: extrapolation from price derivatives — not look-ahead
- ELI: what mathematical trick reduces lag?
- Review InstantTrendline theory with fresh eyes after 6 weeks of DSP study
  — can you explain the 3-stage pipeline more clearly now?

### Implementation Notes (Day 3)
- Reflex: newer indicator, implement carefully from article
- Predictive MA: requires price velocity/acceleration calculation
- ELI: compare implementation signature against InstantTrendline

### Validation Focus (Days 4-5)
- Three-way comparison: SMA vs InstantTrendline vs each new indicator
- Which achieves least lag? Which has most false signals?
- Crypto: Predictive MA on fast-moving BTC — does prediction hold?
- Final C1 candidates ranked by lag + signal quality

### Validation Gate
- ✅ Reflex: lag reduction vs SMA confirmed
- ✅ Predictive MA: comparison with ITrend documented
- ✅ ELI: ranked vs InstantTrendline
- ✅ Comprehensive C1 candidate ranking table created

---

## Week 12 — Noise Reduction & Signal Quality
**Articles:** `Recursive Median Filters.pdf` + `Correlation As A Cycle Indicator.pdf`
**Note (2026-08-05):** `Every Little Bit Helps.pdf` was previously listed here as the
source for indicator #21. That article is about averaging open+close to reduce noise at
Nyquist — it contains no Kalman or state-estimation content. **Indicator #21 has no
Ehlers source article.** See "Provenance correction" below.
**Why:** These improve signal quality through fundamentally different mechanisms than
smoothing. Median handles outliers non-linearly. Correlation Cycle uses autocorrelation
rather than band-pass filtering.

### Provenance correction — indicator #21 (2026-08-05)

The filter previously labelled "Ehlers Kalman Filter" is an **α–β (g–h) filter**, a
constant-gain position+velocity tracker from radar tracking literature. It is the
steady-state limit of a Kalman filter under fixed noise covariances, but the covariance
propagation — the part that makes Kalman adaptive and optimal — is absent.

- **Renamed** `EhlersKalman` → `AlphaBetaFilter`
- **Claim retracted:** "optimal minimum-variance estimator." A fixed-gain tracker is
  optimal only if the chosen gain matches the true process/measurement noise ratio.
- **Citation:** α–β filter literature (Kalata tracking index; Benedict–Bordner), not Ehlers.

### Indicators
| # | Indicator | NNFX Role Hypothesis |
|---|---|---|
| 21 | Alpha-Beta Filter (was "Ehlers Kalman") | Baseline / predictive — 1-bar lead, NOT a smoother |
| 22 | Recursive Median Filter + RMO | RM: outlier-robust smoothing. **RMO: Strategy 2 C2 candidate** |
| 23 | Correlation Cycle Indicator | Null-gate test subject (Principle 6) — see roadmap v4.3 |

### Theory Focus (Days 1-2)
- α–β: position+velocity tracking; what the Kalman "simplification" actually discards
  - Relation α = √(2β) is the critical-damping condition — legitimate, not a typo
  - How does it differ from SuperSmoother mathematically?
- Recursive Median: non-linear — breakdown point, why linearity *is* outlier sensitivity
  - Flash crash resilience: critical for crypto
- Correlation Cycle: autocorrelation as a mechanism distinct from band-pass filtering

### Implementation Notes (Day 3)
- **α–β Gain: usable range [0.02, 0.20].** Above Gain ≈ 0.246 the filter *amplifies*
  noise (output σ > input σ). Above Gain = 0.5, α = √(2·Gain) exceeds 1 and the position
  update overshoots the measurement every bar. The previously documented "0.6–0.9
  typical" is wrong — at 0.9 it amplifies noise 3.45× and overshoots a step by 124%.
- **α–β leads by exactly 1.000 bar on a ramp**, at all gains. Structural: the recursion
  omits the prediction step and adds velocity post-hoc, double-counting it. Output is a
  one-step-ahead **forecast**, not a current-state estimate. Will overshoot at turning
  points. Do not document as a smoother.
- Recursive Median: non-linear — explicit 5-element sort, cannot use `series()` IIR pattern
- RM `alpha1` has **no** 0.707 (single pole); RMO `alpha2` **requires** it (two poles)
- Correlation Cycle: requires autocorrelation calculation

### Validation Focus (Days 4-5)
- **α–β Gain sweep: 0.02 / 0.05 / 0.10 / 0.20** (revised — old 0.1/0.3/0.6/0.9 spans the
  noise-amplifying region and is not informative)
- α–β vs EMA: at comparable settings a plain EMA smooths harder (σ 0.50 vs 0.69). The
  α–β buys a 1-bar lead, not smoothness. Test whether that lead has value.
- Recursive Median: flash crash test — 2020-03 BTC crash data specifically
- **RMO vs MESA Stochastic |ρ| — decides the Strategy 2 C2 slot.** Pre-registered
  threshold ≤ 0.5; pre-registered prediction 0.4–0.65
- RMO has **no AGC** — check amplitude stability on BTC/USD H4 (~10× regime variation)

### Validation Gate
- ✅ α–β: characterised (noise gain, lead, overshoot); honest role documented
- ✅ Recursive Median: outlier resistance confirmed vs plain EMA
- ✅ RMO: C2 decision made against pre-registered criteria — accept or reject on record
- ✅ Correlation Cycle: implemented + null-tested (Principle 6)

---

## Week 13 — Volatility Indicators & Bands
**Articles:** `Setting stops — a new approach.pdf` + `Ultimate Channels And
Ultimate Bands.pdf` + `(Yet Another) Improved RSI.pdf`  
**Why:** NNFX requires robust volatility measurement for position sizing and
stop placement. Normalized ATR enables cross-asset comparison on same scale.

### Indicators
| # | Indicator | NNFX Role Hypothesis |
|---|---|---|
| 24 | Normalized ATR | ATR / position sizing — cross-asset comparable |
| 25 | Ultimate Channels & Bands | Dynamic volatility bands / stop placement |
| 26 | Laguerre RSI | C2 / exit signal — low-lag RSI alternative |

### Theory Focus (Days 1-2)
- Normalized ATR: ATR as fraction of price
  - EUR/USD ATR 0.0060 vs BTC ATR 1500 — incomparable raw
  - Normalized: EUR/USD ~0.5%, BTC ~3% — directly comparable
  - Essential for cross-asset position sizing module
- Ultimate Bands: how do Ehlers bands adapt vs Bollinger Bands mathematically?
- Laguerre RSI: Laguerre polynomials reduce lag vs standard RSI

### Implementation Notes (Day 3)
- Normalized ATR: `NormATR = ATR(Period) / ((High + Low + Close) / 3)`
- Ultimate Bands: likely depends on SuperSmoother (Week 5)
- Laguerre RSI: uses L0-L3 Laguerre polynomial chain

### Validation Focus (Days 4-5)
- Normalized ATR: FX ~0.5%, Crypto ~2-3% in normal conditions — verify
- Volatility regime classifier:
  - Low vol FX: NATR < 0.5% | High vol FX: NATR > 1%
  - Low vol Crypto: NATR < 2% | High vol Crypto: NATR > 4%
- Ultimate Bands vs Bollinger Bands: which adapts faster?
- Laguerre RSI lag vs standard RSI confirmed
- Update risk management module to use NormalizedATR

### Validation Gate
- ✅ NormalizedATR: comparable FX/Crypto values confirmed
- ✅ Ultimate Bands: adaptation vs Bollinger Bands documented
- ✅ Laguerre RSI: lag improvement confirmed
- ✅ Volatility regime classifier operational
- ✅ Risk management module updated

---

## Week 14 — Consolidation & Library Finalization
**No new indicators — review, mapping, documentation, GitHub preparation**

- **Days 1-2:** Full library code review — standardize headers, naming, comments
- **Day 3:** Master comparison table — all 26 indicators, lag, SNR, periods, NNFX role
- **Day 4:** NNFX component mapping document — drives Phase 3 strategy design
- **Day 5:** Cross-asset summary — what works better on FX vs Crypto, parameter guidelines
- **Day 6:** Professional GitHub README, Phase 2 retrospective, final commit

**NNFX Component Map (to be filled with evidence by Week 14):**

| NNFX Slot | Primary Candidate | Secondary Candidate | Evidence Source |
|---|---|---|---|
| Baseline | MAMA/FAMA | FRAMA | Week 7 + 9 comparison |
| C1 | Fisher Transform | Cyber Cycle | Week 8 + 10 |
| C2 | Laguerre RSI | EBS | Week 8 + 13 |
| ATR/Stops | NormalizedATR | Ultimate Bands | Week 13 |
| Exit | SuperSmoother crossback | — | Week 5 |

---

## Summary Table

| Week | Category | Count | Key Articles |
|---|---|---|---|
| 5 | Smoothing Filters | 3 | Moving averages and smoothing filters, The Ultimate Smoother |
| 6 | High-Pass / Roofing | 3 | Optimal Detrending, Whiter Is Brighter, Decyclers |
| 7 | MAMA/FAMA | 2 | MESA Adaptive Moving Averages |
| 8 | Cycle Oscillators | 3 | Adaptive Trends And Oscillators, Measuring Market Cycles, The Bandpass Indicator |
| 9 | Adaptive Trend | 3 | Fractal Adaptive MAs, Laguerre Filters, The Deviation-Scaled MA |
| 10 | Momentum / Transforms | 3 | Using The Fisher Transform, The Inverse Fisher Transform, Center of Gravity |
| 11 | Zero-Lag / Predictive | 3 | Reflex, Predictive And Successful Indicators, ELI |
| 12 | Noise Reduction | 3 | Every Little Bit Helps, Recursive Median Filters, Correlation As A Cycle Indicator |
| 13 | Volatility / Stops | 3 | Setting stops, Ultimate Channels And Bands, (Yet Another) Improved RSI |
| 14 | Consolidation | 0 | — |
| **Total** | | **26** | |

---

## Connection to Phase 3 (Weeks 18-25)

The NNFX component mapping from Week 14 directly drives strategy design:

- **Strategy 1 (Week 18):** MAMA Baseline + Fisher Transform C1 + Laguerre RSI C2
- **Strategy 2 (Week 19):** FRAMA Baseline + Cyber Cycle C1 + EBS C2
- **Strategy 3 (Week 20):** DominantCycle adaptive + Bandpass oscillator
- **Strategy 4 (Week 21):** ATR breakout + Fisher Transform confirmation
- **Strategy 5 (Week 22):** SuperSmoother trend + Roofing Filter cycle + Kalman filter
- **Strategy 6 (Week 23):** Crypto-specific — NormalizedATR × 2.5 stops, BTC/ETH

The chain: **theory → implementation → validation → strategy application**
is what separates professional systematic trading from guesswork.