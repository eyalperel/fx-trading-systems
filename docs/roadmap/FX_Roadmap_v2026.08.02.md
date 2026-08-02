# UNIFIED FX & CRYPTOCURRENCY ALGORITHMIC TRADING ROADMAP
## 48-Week Professional Development Program
### Zorro Platform | NNFX Framework | John Ehlers Indicators | Evidence-Based 2024-2025

---

**Program Version:** 4.2 - Bi-Weekly Research Update  
**Last Updated:** August 2, 2026  
**Based On:** 2024-2025 Research + Your Specific Constraints  
**Asset Classes:** Foreign Exchange (70%) + Cryptocurrency (30%)

---

## 📋 CHANGELOG v4.1 → v4.2 (August 2, 2026)

**Bi-Weekly Research Update — Week 11 checkpoint, no changes to active roadmap phase**

Searched: ML trading strategies, algorithmic trading techniques, RL trading advances, time-series forecasting AI methods, systematic trading technology trends (August 2026 literature).

| What Changed | Location | Rationale |
|---|---|---|
| Added foundation-model time-series forecasters (e.g. Chronos-Bolt) as a candidate to evaluate in Week 31 | Phase 4, Week 31 | Not implementable as an NNFX confirmation indicator now — architecturally replaces rather than slots into the C1/C2 framework. Already tested once in the parallel ML-Mastery project; that result should be pulled forward at Week 31 rather than re-derived. No new work performed this cycle. |
| Added RL-for-trading frameworks beyond plain DQN (sentiment-aware curriculum learning, CE-PPO) as a candidate to evaluate in Week 31 | Phase 4, Week 31 | Same rationale — belongs in ML integration phase, not current indicator-library phase (Weeks 12-14) |

**What was assessed and left unchanged / ignored:**
- ❌ Quantum computing for trading — not implementable in Zorro/Python, no proven backtesting evidence
- ❌ FPGA acceleration, MacroHFT, EarnHFT, HFT microstructure models — wrong timeframe, explicitly out of scope
- ❌ LLM-agent-as-policy-backbone frameworks (FinRL-DeepSeek, agentic trading) — overly complex, unvalidatable in current toolchain
- ❌ NLP/news-sentiment signals — plausible eventually, but requires a data feed not currently available
- ❌ Blockchain/tokenization trends — not relevant to indicator or strategy development
- ✅ "Simple beats complex" principle: no evidence this cycle contradicts it — current indicator-first approach (Weeks 5-14) remains the right sequencing

**Current phase status:** Week 11 of 48 (Phase 2: Indicator Deep Dive). Reflex, MESA Stochastic implemented and validated; ELI implemented and documented as a FAIL. Strategy 1 (FAMA + Fisher C1 + Reflex C2) and Strategy 2 C1 (MESA Stochastic) locked. No roadmap structure changes this cycle — the two backlog additions above are notes for Week 31, not changes to the current Weeks 12-14 plan.

---

## 📋 CHANGELOG v4.0 → v4.1 (May 5, 2026)

**Bi-Weekly Research Update — Three targeted changes based on May 2026 literature review**

| What Changed | Location | Rationale |
|---|---|---|
| Added 3×3 WFO window grid to Week 15 Days 1 & 3 | Phase 2.5 | Mroziewicz & Ślepaczuk (arXiv 2602.10785, Feb 2026): window length stability is a stronger robustness signal than any single WFO result |
| Regime-switching strategy made mandatory in Week 24 | Phase 3 | Regime detection is standard practice in 2026 systematic trading research; Phase 2 indicators (MAMA + Cyber Cycle) already provide the raw components |
| SHAP named as primary explainability tool in Week 30 | Phase 4 | Pagliaro (Electronics 2026): SHAP is now the industry-standard tool for feature importance in regime-aware trading frameworks; already compatible with all roadmap libraries |

**What was assessed and left unchanged:**
- ❌ LSTM/deep learning: still non-performer for FX price prediction (confirmed again)
- ❌ RL for trading: HFT-focused or requires unavailable infrastructure
- ❌ LLM+RL hybrids: requires expensive real-time data feeds
- ❌ Time series foundation models: no proven FX edge, GPU infrastructure required
- ✅ "Simple beats complex" principle: confirmed by a third consecutive research cycle (March 2026 comparative study, MDPI)

---

## 📋 CHANGELOG v3.0 → v4.0

**Strategic Pivot: Indicator-First Approach**

| What Changed | Old Plan (v3.0) | New Plan (v4.0) |
|---|---|---|
| Weeks 1-4 | Build 3 strategies quickly | Build 2 strategies + master indicators |
| Weeks 5-14 | Study 102 Ehlers articles broadly | Implement 20-25 curated indicators, validated |
| Weeks 15+ | Backtesting Bootcamp (Phase 2.5) | Backtesting Bootcamp (now Phase 2.5, unchanged) |

**Rationale:** Better strategies emerge from deep indicator understanding. Building strategies before mastering the tools leads to suboptimal design decisions that require later rework.

---

## 📋 EXECUTIVE SUMMARY

### Your Mission
Develop multiple **uncorrelated trading systems** across FX and cryptocurrency markets that serve dual purposes:
1. **Generate consistent returns** with proper risk management
2. **Build professional portfolio** for employment opportunities in systematic trading

### Your Resources
- **Time:** 12 hours/week (2 hrs/day × 6 days)
- **Skills:** Python 6-7/10, Light-C 5/10, Intermediate programming
- **Capital:** $10K FX + Separate crypto allocation
- **Platform:** Zorro + MT4/MT5 (DarwinEx demo → live)
- **Framework:** NNFX methodology + John Ehlers indicators
- **Foundation:** 102 Ehlers TASC articles, established dev environment

### Critical Skill Gap Addressed
**Backtesting mastery** - Previous attempts stalled at simple backtesting. This roadmap includes dedicated "Backtesting Bootcamp" (Weeks 15-17) with hands-on validation techniques.

### Key Evidence-Based Findings (2024-2025)

**What Actually Works:**
- ✅ Simple approaches beat ML in FX (Sharpe 1.2 vs 1.0 - Macrosynergy Dec 2024)
- ✅ Walk-forward optimization (50%+ efficiency mandatory)
- ✅ Monte Carlo validation (often reveals 2-3× worse drawdowns)
- ✅ VIX-based regime detection outperforms deep learning
- ✅ Meta-labeling (10-15% F1-score improvement)
- ✅ ATR-based position sizing
- ✅ Basic DSP filters (SuperSmoother, HighPass)

**What Doesn't Work:**
- ❌ Deep learning for FX price prediction
- ❌ Complex Ehlers indicators without objective validation
- ❌ Over-optimization (kills 95% of systems)
- ❌ Most ML models (conceptual parity wins)
- ❌ Ignoring transaction costs

**Crypto-Specific Insights:**
- ✅ H4 timeframe superior to D1 for crypto (higher volatility)
- ✅ BTC + ETH should be 70-80% of crypto allocation
- ✅ Position sizing must be 5-10× smaller vs FX
- ✅ Crypto provides portfolio diversification (often uncorrelated with FX)
- ✅ 24/7 trading allows continuous strategy execution
- ⚠️ 3-5× higher volatility requires adjusted risk management
- ⚠️ Exchange risk, funding rates, and flash crash exposure

---

## 🎯 PROGRAM STRUCTURE OVERVIEW

### Timeline: 48 Weeks (Realistic for 12 hrs/week)

**PHASE 1: Foundation & Infrastructure (Weeks 1-4)**
- Environment setup, first 2 strategies, risk management basics
- InstantTrendline + DominantCycle implemented (✅ DONE)
- Week 4: Analysis framework + indicator validation methodology
- Asset: Primary FX focus

**PHASE 2: Indicator Deep Dive — Curated 20-25 Ehlers (Weeks 5-14)**
- Systematic implementation of selected best-in-class indicators
- Each week: one indicator category, fully validated before moving on
- Test on both FX and crypto (comparison analysis)
- **Gate:** Each indicator must pass objective validation before library inclusion
- Asset: 80% FX, 20% crypto testing

**PHASE 2.5: Backtesting Bootcamp (Weeks 15-17)**
- **CRITICAL PHASE** — Walk-forward optimization mastery
- Monte Carlo simulation
- Robust validation techniques
- Asset: FX primary, crypto validation

**PHASE 3: Strategy Development (Weeks 18-25)**
- Develop 5-8 uncorrelated strategy candidates using your validated indicator library
- Apply systematic validation
- Test across FX major pairs and BTC/ETH
- Asset: 70% FX, 30% crypto

**PHASE 4: ML Integration & Regime Detection (Weeks 26-33)**
- VIX-based regime filters
- Meta-labeling implementation
- Asset: Both FX and crypto

**PHASE 5: Paper Trading & Validation (Weeks 34-40)**
- Demo account deployment
- Live forward testing
- Asset: Parallel FX and crypto systems

**PHASE 6: Live Deployment (Weeks 41-48)**
- Scale to live capital ($10K FX + crypto allocation)
- Portfolio management
- Asset: Full multi-asset portfolio

---

## 📊 ASSET ALLOCATION FRAMEWORK

### Capital Split
- **FX:** $10,000 target live capital
- **Crypto:** Separate allocation (recommend starting with $2,000-3,000)
- **Total Portfolio:** $12,000-13,000 at full deployment

### Focus Allocation (Time & Development)
- **FX:** 70% of development time
  - EUR/USD, GBP/USD, USD/JPY, AUD/USD (primary)
  - EUR/GBP, NZD/USD (secondary)
- **Crypto:** 30% of development time
  - BTC/USD (50% of crypto allocation)
  - ETH/USD (30% of crypto allocation)
  - Optional: One altcoin (20% — SOL, BNB, or XRP)

### Risk Management Adjustments

**FX Risk Parameters:**
- Position sizing: 1-2% per trade (ATR-based)
- Stop loss: 1.5× ATR (standard NNFX)
- Max open positions: 6-8 uncorrelated pairs
- Max portfolio risk: 6-8%

**Crypto Risk Parameters:**
- Position sizing: 0.2-0.4% per trade (5-10× smaller than FX)
- Stop loss: 2.0× ATR (wider due to volatility)
- Max open positions: 2-3 pairs
- Max portfolio risk: 0.8-1.2%
- **Rationale:** Crypto is 3-5× more volatile than FX

---

## 🗺️ DETAILED PHASE BREAKDOWN

---

### PHASE 1: FOUNDATION & INFRASTRUCTURE (WEEKS 1-4)

**Objective:** Establish solid technical foundation, create first working strategies, set up professional development environment, build indicator validation methodology

---

**Week 1: Getting Started** ✅ COMPLETE

**Completed:**
- ✅ Working Zorro + MT4 bridge
- ✅ First simple FX strategy backtested
- ✅ First Ehlers indicator (Zero-Lag EMA) implemented
- ✅ Git repository established
- ✅ Reading notes completed

---

**Week 2: NNFX Deep Dive + Crypto Setup** ✅ COMPLETE

**Completed:**
- ✅ NNFX framework understood and documented
- ✅ Crypto data obtained/connection tested
- ✅ Super Smoother indicator implemented
- ✅ FX vs Crypto comparison documented

---

**Week 3: Risk Management Fundamentals** ✅ COMPLETE

**Completed:**
- ✅ ATR-based position sizing for FX
- ✅ Crypto-adjusted position sizing (5-10× reduction)
- ✅ Risk management playbook created

---

**Week 4: Advanced Indicators + Analysis Framework** ← YOU ARE HERE

**Goals:**
- Complete analysis framework (reusable Jupyter template)
- Validate InstantTrendline (adaptive vs fixed cycle)
- Test InstantTrendline + DominantCycle on crypto
- Build the indicator validation methodology that will be used in Weeks 5-14

**Already Completed (Days 1-2):**
- ✅ Day 1: ATR Breakout Strategy (FX)
- ✅ Day 2: InstantTrendline indicator + DominantCycle indicator (fully adaptive, committed to Git)

---

**Day 3: Build Analysis Framework (2 hours)**

*Goal: Create the reusable Jupyter template that will be used for EVERY indicator in Weeks 5-14*

**Step 1 — Create notebook structure (30 min)**
- Open Jupyter, create `/analysis/templates/Indicator_Analysis_Template.ipynb`
- Set up notebook sections:
  ```
  1. Indicator Overview (description, formula, expected behavior)
  2. Data Loading (EUR/USD D1 + BTC/USD H4)
  3. Visual Inspection (price + indicator overlay, 2019-2024)
  4. Lag Measurement (cross-correlation with SMA baseline)
  5. Noise Reduction Score (signal-to-noise ratio)
  6. FX vs Crypto Comparison (side-by-side charts)
  7. Validation Verdict (PASS/FAIL criteria below)
  8. Notes & Parameter Recommendations
  ```

**Step 2 — Implement PASS/FAIL criteria (45 min)**

An indicator PASSES validation and enters the library if it meets ALL of:
- Visually tracks price in expected way (no obvious bugs)
- Lag ≤ comparable SMA of same period (or demonstrably lower)
- Noise reduction: SNR improved vs raw price (quantified)
- Behaves consistently on both EUR/USD D1 and BTC/USD H4
- Code runs without errors in Zorro test script

An indicator FAILS if any of:
- Output diverges unexpectedly from price
- Worse lag than simple SMA of same period
- Produces NaN/infinite values in live data
- Zorro test script crashes

**Step 3 — Build helper functions (45 min)**
```python
# In /analysis/utils/indicator_metrics.py
def calculate_lag(price, indicator_series, window=100):
    """Cross-correlation lag measurement"""

def calculate_snr(price, smoothed):
    """Signal-to-noise ratio improvement"""

def compare_fx_crypto(fx_series, crypto_series):
    """Side-by-side parameter comparison"""

def generate_validation_report(indicator_name, results_dict):
    """Auto-generate PASS/FAIL verdict with metrics"""
```

**Step 4 — Commit (30 min)**
- Save template + utility functions
- Commit: `feat: add indicator analysis template and validation framework`
- **Outcome:** Every indicator in Weeks 5-14 will use this exact template

---

**Day 4: Validate InstantTrendline — Fixed vs Adaptive (2 hours)**

*Use the new analysis framework on your already-implemented InstantTrendline*

**Step 1 — Run fixed-cycle version (30 min)**
- In your Zorro test script, temporarily disable DominantCycle integration
- Use hardcoded `period = 20` (typical default)
- Run on EUR/USD D1, export output to CSV
- Load in Jupyter, run through analysis template

**Step 2 — Run adaptive version (30 min)**
- Re-enable DominantCycle integration
- Run same date range
- Export output, load in Jupyter

**Step 3 — Comparison analysis (45 min)**
- Overlay both versions on the same price chart
- Key questions to answer:
  - Does the adaptive version respond faster to cycle changes?
  - Are there periods where fixed-cycle performs better? (document them)
  - What is the lag difference at different market phases?
- Record findings in Jupyter notebook

**Step 4 — Validation verdict + commit (15 min)**
- Apply PASS/FAIL criteria from Day 3 template
- Write conclusions in `/docs/indicators/InstantTrendline_Validation.md`
- Commit: `docs: InstantTrendline validation - fixed vs adaptive comparison`
- **Expected outcome:** Adaptive version should show 15-30% lag reduction during cycle transitions

---

**Day 5: Test on Crypto + DominantCycle Validation (2 hours)**

*Cross-asset validation for both indicators already implemented*

**Step 1 — InstantTrendline on BTC/USD H4 (45 min)**
- Run adaptive InstantTrendline on BTC/USD H4 (2020-2024)
- Export and load in Jupyter
- Compare to EUR/USD D1 results:
  - Different optimal period? (crypto likely faster cycles)
  - More/fewer false crossings?
  - How does it handle the high-volatility 2021-2022 period?

**Step 2 — DominantCycle on both assets (45 min)**
- Run DominantCycle on EUR/USD D1 → what periods does it detect? (expect 15-25 bars)
- Run DominantCycle on BTC/USD H4 → what periods? (expect shorter, more volatile)
- Plot detected cycle periods over time for both
- Document: "FX cycles are more stable; crypto cycles are shorter and more erratic"

**Step 3 — Document cross-asset findings (30 min)**
- Create `/docs/cross_asset/InstantTrendline_FX_vs_Crypto.md`
- Include: parameter recommendations per asset, known limitations
- Commit: `docs: cross-asset validation for InstantTrendline and DominantCycle`

---

**Day 6: Week 4 Review + Indicator Selection for Weeks 5-14 (2 hours)**

*This is the most strategic session of Phase 1 — selecting the 20-25 indicators to implement in Weeks 5-14*

**Step 1 — Week 4 retrospective (20 min)**
- Write `/docs/journal/Week4_Retrospective.md`
- What worked, what was harder than expected, what you learned

**Step 2 — Select the 20-25 Ehlers indicators for Weeks 5-14 (60 min)**

From your 102-article collection, select indicators that:
- Have clear mathematical formulas (implementable)
- Have distinct use cases (trend, cycle, momentum, volatility, noise reduction)
- Are referenced in NNFX-style systems
- Are not redundant with each other

**Recommended curated selection (adapt based on your articles):**

| Week | Category | Primary Indicators (pick 2-3) |
|---|---|---|
| 5 | Smoothing Filters | 2-Pole SuperSmoother, 3-Pole SuperSmoother, Gaussian Filter |
| 6 | High-Pass Filters | High-Pass Filter, Roofing Filter (HP+SS combination) |
| 7 | Cycle Measurement | MESA Adaptive MA (MAMA), Dominant Cycle (Autocorrelation method) |
| 8 | Cycle Oscillators | Cyber Cycle, Even Better Sinewave (EBS) |
| 9 | Adaptive Trend | FRAMA (Fractal Adaptive MA), Kaufman AMA comparison |
| 10 | Momentum | Fisher Transform, Stochastic (Ehlers version), CCI (Ehlers version) |
| 11 | Predictive | Predictive Moving Average, Zero-Lag variants |
| 12 | Noise Reduction | Kalman Filter (Ehlers formulation), Laguerre RSI |
| 13 | Volatility / Bands | Ehlers Bands, ATR variants, Normalized ATR |
| 14 | Composite / Review | MAMA/FAMA system, Consolidation + library cleanup |

**Step 3 — Document your selections (20 min)**
- Create `/docs/indicators/Week5-14_Indicator_Plan.md`
- For each selected indicator: article name, expected use case, which NNFX component it might serve
- Commit everything: `plan: Week 5-14 curated indicator roadmap selected`

**Week 4 Milestone Checklist:**
- ✅ Days 1-2: InstantTrendline + DominantCycle implemented and committed
- ✅ Day 3: Reusable analysis framework + PASS/FAIL validation criteria
- ✅ Day 4: InstantTrendline validated (fixed vs adaptive)
- ✅ Day 5: Cross-asset testing on crypto
- ✅ Day 6: 20-25 indicators selected for Weeks 5-14
- ✅ **PHASE 1 COMPLETE**

---

### PHASE 2: INDICATOR DEEP DIVE — CURATED IMPLEMENTATION (WEEKS 5-14)

**Objective:** Implement and validate 20-25 selected Ehlers indicators with rigorous objective testing on both FX and cryptocurrency markets

**Core Principles for Phase 2:**
- **One category per week** — depth over breadth
- **Validate before moving on** — if an indicator fails, document why and move to the next
- **Use the analysis template every time** — consistency is how you build a library
- **Crypto test is mandatory** — every indicator tested on BTC/USD H4
- **PASS/FAIL gate** — only validated indicators enter `/zorro/indicators/ehlers/`
- **No strategy building yet** — pure indicator research and library construction

**Weekly Structure (applies to all of Weeks 5-14):**

Every week follows this pattern:

| Day | Focus | Time |
|---|---|---|
| Day 1 | Read article(s), understand math, take notes | 2 hrs |
| Day 2 | Implement in Light-C, basic Zorro test | 2 hrs |
| Day 3 | Debug + run validation (FX) using template | 2 hrs |
| Day 4 | Crypto testing + cross-asset comparison | 2 hrs |
| Day 5 | Parameter sensitivity + edge cases | 2 hrs |
| Day 6 | Documentation, Git commit, weekly retrospective | 2 hrs |

**Deliverables each week:**
- `[IndicatorName].c` in `/zorro/indicators/ehlers/` (if PASS)
- `[IndicatorName]_Test.c` in `/zorro/strategies/tests/`
- Jupyter notebook in `/analysis/indicators/[IndicatorName]_Analysis.ipynb`
- `/docs/indicators/[IndicatorName]_Notes.md` (theory + implementation notes)
- `[IndicatorName]_FX_vs_Crypto.md` (cross-asset comparison)
- Git commit with meaningful message

---

**Week 5: Smoothing Filters**
*Articles: SuperSmoother 2-Pole, SuperSmoother 3-Pole, (optional) Gaussian Filter*

**Why these first:** SuperSmoother is Ehlers' foundational building block — it appears inside many other indicators. Understanding it deeply before building on top of it is essential.

**Day 1 — Theory (2 hours)**
- Read Ehlers' SuperSmoother article carefully
- Study the 2-pole IIR filter design: what is it minimizing?
- Compare: 2-pole vs 3-pole — what does the extra pole add?
- Key formula to understand:
  ```
  c1 = exp(-1.414 * π / Period)
  b1 = 2 * c1 * cos(1.414 * π / Period)
  Filt = b1 * Filt[1] - c1^2 * Filt[2] + ((1 - b1 + c1^2)/2) * (Price + Price[1])
  ```
- Write notes: what is the cutoff frequency? How does period affect it?
- Document in `/docs/indicators/SuperSmoother_Theory.md`

**Day 2 — Implement 2-Pole SuperSmoother (2 hours)**

⏸️ **PAUSE POINT** — implement, then verify it compiles and runs before proceeding

```c
// /zorro/indicators/ehlers/SuperSmoother2Pole.c
// Based on: Ehlers, "Cybernetic Analysis" + TASC article
// Purpose: Low-lag smoothing filter (2-pole IIR)
// Inputs: Price series, Period (default 14)
// Output: Smoothed price

var SuperSmoother2Pole(vars Price, int Period) {
    var c1 = exp(-1.414 * PI / Period);
    var b1 = 2 * c1 * cos(1.414 * 180.0 / Period);  // degrees in Zorro
    var c2 = b1;
    var c3 = -c1 * c1;
    var c0 = (1 - b1 + c1 * c1) / 4.0;
    
    // Allocate persistent storage
    var* Filt = series(0.0, 3);
    
    Filt[0] = c0 * (Price[0] + Price[1]) +
               c2 * Filt[1] +
               c3 * Filt[2];
    
    return Filt[0];
}
```

- Write `/zorro/strategies/tests/Test_SuperSmoother.c`
- Run: verify output is smooth, no NaN, reasonable values

**Day 3 — Validation on EUR/USD (2 hours)**

⏸️ **PAUSE POINT** — run full validation template, record all metrics before crypto

- Run analysis template on EUR/USD D1 (2015-2024)
- Key tests:
  - Lag comparison vs SMA(14): SuperSmoother should be faster to respond
  - Visual inspection: Should appear as smooth curve below/above price
  - Test periods: 10, 14, 20, 30 — document how smoothness vs lag changes
- Apply PASS/FAIL criteria
- If PASS: move to Day 4. If FAIL: debug before moving on.

**Day 4 — Crypto Testing (2 hours)**
- Run on BTC/USD H4 (2020-2024)
- Expected finding: same formula works, but optimal period may differ (crypto faster)
- Document recommended periods: FX (14-20) vs Crypto (8-14) — verify or refute
- Create cross-asset comparison notebook

**Day 5 — Parameter Sensitivity + 3-Pole Variant (2 hours)**
- Parameter sweep: period 5 to 50, plot SNR vs lag tradeoff curve
- Implement 3-Pole SuperSmoother variant (extra pole = more smoothing, more lag)
- Compare 2-pole vs 3-pole side-by-side
- Document when to use which

**Day 6 — Documentation + Commit (2 hours)**
- Complete Jupyter analysis notebook
- Write final `SuperSmoother_Notes.md` with:
  - When to use 2-pole vs 3-pole
  - Recommended periods per asset class
  - Role in NNFX (likely: Baseline or C1 smoothing)
  - Known limitations
- Git commit: `feat: SuperSmoother 2-pole + 3-pole validated and added to library`
- Week 5 retrospective

**Week 5 Validation Gate:**
- ✅ 2-Pole SuperSmoother: lag < SMA(same period), no artifacts
- ✅ 3-Pole variant: more smoothing confirmed, lag tradeoff documented
- ✅ Both tested on FX + Crypto
- ✅ Parameter guidelines written
- ✅ **Library entry approved**

---

**Week 6: High-Pass Filters & Roofing Filter**
*Articles: High-Pass Filter (1-pole, 2-pole), Roofing Filter (HP + SS combination)*

**Why these:** High-pass filters are the complement to SuperSmoother — they isolate the cycle component by removing the trend. The Roofing Filter combines both to create a "band-pass" effect ideal for oscillator inputs.

**Day 1 — Theory (2 hours)**
- Read High-Pass Filter article
- Study: HP filter removes low-frequency trends, passes high-frequency cycles
- Key insight: Roofing Filter = High-Pass → then → SuperSmoother
  - HP removes trend (keeps cycles)
  - SS removes noise (keeps dominant cycle)
  - Result: de-trended, de-noised cycle component
- Understand the alpha calculation for different cutoff frequencies
- Document in `/docs/indicators/HighPass_Roofing_Theory.md`

**Day 2 — Implement High-Pass Filter (2 hours)**

⏸️ **PAUSE POINT**

```c
// /zorro/indicators/ehlers/HighPassFilter.c
// Purpose: Remove trend component, isolate cycles
// Key parameter: HighPassPeriod (controls cutoff frequency)

var HighPassFilter(vars Price, int HighPassPeriod) {
    var Alpha1 = (cos(360.0 / HighPassPeriod) + sin(360.0 / HighPassPeriod) - 1) 
                 / cos(360.0 / HighPassPeriod);
    
    var* HP = series(0.0, 3);
    HP[0] = (1 - Alpha1/2) * (1 - Alpha1/2) * (Price[0] - 2*Price[1] + Price[2])
            + 2*(1-Alpha1)*HP[1] - (1-Alpha1)*(1-Alpha1)*HP[2];
    
    return HP[0];
}
```

- Write test script, verify it de-trends (output should oscillate around zero)

**Day 3 — Implement Roofing Filter + FX Validation (2 hours)**

⏸️ **PAUSE POINT**

```c
// /zorro/indicators/ehlers/RoofingFilter.c
// Purpose: Band-pass filter for cycle isolation
// = High-Pass then Super-Smooth

var RoofingFilter(vars Price, int HPPeriod, int SSPeriod) {
    var* hp = series(HighPassFilter(Price, HPPeriod), 2);
    var roofed = SuperSmoother2Pole(hp, SSPeriod);
    return roofed;
}
```

- Run full validation template on EUR/USD D1
- Visual check: Roofing Filter output should look like a clean oscillator
- Compare raw price, HP output, Roofing Filter output — three-panel chart

**Day 4 — Crypto Testing (2 hours)**
- Run on BTC/USD H4
- Expected: Roofing Filter reveals crypto cycles more clearly (higher cycle amplitude)
- Compare cycle frequency: FX vs Crypto
- Document findings

**Day 5 — Parameter Sensitivity (2 hours)**
- HighPassPeriod: role is to set the "slowest cycle" that passes through
- SSPeriod: role is to remove noise above a frequency
- Test combinations: HP(40)/SS(10) vs HP(20)/SS(10) vs HP(40)/SS(20)
- Document recommended defaults: HP=48, SS=10 (Ehlers common choice)

**Day 6 — Documentation + Commit (2 hours)**
- Complete analysis notebook
- Document: Roofing Filter is the ideal input preprocessor for cycle-based oscillators
- Git commit: `feat: HighPassFilter + RoofingFilter validated and added to library`
- Week 6 retrospective

**Week 6 Validation Gate:**
- ✅ HighPassFilter: output oscillates around zero, trend removed
- ✅ RoofingFilter: clean cycle isolation confirmed
- ✅ Both tested on FX + Crypto
- ✅ Role in NNFX identified (input preprocessor)

---

**Week 7: MESA Adaptive Moving Average (MAMA/FAMA)**
*Articles: MAMA, FAMA, Phase Accumulator method*

**Why MAMA:** MAMA is Ehlers' most sophisticated trend indicator — it uses the Hilbert Transform to measure instantaneous phase and adapt its speed to the market. It's directly usable as a Baseline in NNFX.

**Day 1 — Theory (2 hours)**
- Read MAMA article carefully — this is more complex than previous indicators
- Understand: MAMA tracks fast cycles, FAMA tracks slow (following MAMA)
- Key concept: Phase rate of change → adaptive alpha
- MAMA crossover with FAMA = trend signal (like a smart EMA crossover)
- Note: Requires Hilbert Transform (I and Q components)
- Document in `/docs/indicators/MAMA_Theory.md`

**Day 2 — Implement MAMA (2 hours)**

⏸️ **PAUSE POINT** — this is one of the most complex implementations

```c
// /zorro/indicators/ehlers/MAMA.c
// Implementation requires Hilbert Transform I/Q extraction
// Reference: Ehlers "MESA and Trading Market Cycles" 2nd Ed + TASC

var* MAMA_FAMA(vars Price) {
    // Returns array: [0]=MAMA, [1]=FAMA
    static var Mama = 0, Fama = 0;
    static var Period = 0, Phase = 0;
    // ... (full implementation — work through carefully with article)
    var results[2];
    results[0] = Mama;
    results[1] = Fama;
    return results;
}
```

- Work through the full Hilbert Transform section of the article step-by-step
- Implement I/Q extraction, instantaneous period measurement, then alpha calculation
- Test: MAMA should be more responsive than SMA, FAMA smoother than MAMA

**Day 3 — FX Validation (2 hours)**

⏸️ **PAUSE POINT**

- Run full validation template on EUR/USD D1
- Key validation: Does MAMA/FAMA crossover align with real trend changes?
- Measure: How many "whipsaws" vs correct trend calls over 2015-2024?
- Visual: Three-panel chart — Price, MAMA overlay, FAMA overlay

**Day 4 — Crypto Testing (2 hours)**
- Run on BTC/USD H4
- MAMA should adapt faster on crypto (higher volatility → higher phase rate)
- Compare MAMA speed FX vs Crypto quantitatively
- Document NNFX role: **MAMA/FAMA crossover as Baseline indicator**

**Day 5 — Parameter Sensitivity (2 hours)**
- FastLimit and SlowLimit parameters: test 0.5/0.05 (Ehlers default) vs alternatives
- Does changing limits improve whipsaw reduction?
- Document optimal parameters per asset class

**Day 6 — Documentation + Commit (2 hours)**
- Complete analysis notebook
- Document MAMA as **primary Baseline candidate** for NNFX strategy
- Git commit: `feat: MAMA/FAMA validated - primary Baseline candidate identified`
- Week 7 retrospective

**Week 7 Validation Gate:**
- ✅ MAMA/FAMA: crossovers align with trend changes
- ✅ Adaptive behavior confirmed (responds faster in volatile periods)
- ✅ NNFX role identified: Baseline
- ✅ Tested FX + Crypto

---

**Week 8: Cycle Oscillators**
*Articles: Cyber Cycle, Even Better Sinewave (EBS)*

**Why these:** After MAMA gives you trend, Cyber Cycle gives you the cycle component. Together they form a complete market description. EBS is Ehlers' most refined oscillator.

**Day 1 — Theory (2 hours)**
- Read Cyber Cycle article
- Key concept: uses Roofing Filter input → measures cycle state (not trend)
- Works best when market is in cycle mode (ranging), not trend mode
- Read EBS article: "Even Better Sinewave" — improves on Cyber Cycle
- Document in `/docs/indicators/CycleOscillators_Theory.md`

**Day 2 — Implement Cyber Cycle (2 hours)**

⏸️ **PAUSE POINT**

```c
// /zorro/indicators/ehlers/CyberCycle.c
// Purpose: Cycle-mode oscillator
// Input: Should use RoofingFilter output, not raw price

var CyberCycle(vars Price, int Period) {
    var Alpha = 2.0 / (Period + 1);
    var* Smooth = series(0.0, 4);
    var* Cycle = series(0.0, 4);
    
    Smooth[0] = (Price[0] + 2*Price[1] + 2*Price[2] + Price[3]) / 6.0;
    Cycle[0] = ((1 - 0.5*Alpha) * (1 - 0.5*Alpha) * (Smooth[0] - 2*Smooth[1] + Smooth[2]))
               + 2*(1-Alpha)*Cycle[1] - (1-Alpha)*(1-Alpha)*Cycle[2];
    
    return Cycle[0];
}
```

- Test: output should oscillate between approximately -1 and +1
- Verify it does NOT track trend (should return to zero when trending)

**Day 3 — Implement EBS + FX Validation (2 hours)**

⏸️ **PAUSE POINT**

- Implement Even Better Sinewave
- Run validation template on EUR/USD D1 for both
- Compare: Cyber Cycle vs EBS signal quality (false crossings, timing)

**Day 4 — Crypto Testing (2 hours)**
- Run both on BTC/USD H4
- Crypto often spends more time in cycle mode → these may be more useful
- Document: Cyber Cycle and EBS behave differently on H4 vs D1

**Day 5 — Market Mode Context (2 hours)**
- Important: cycle oscillators are only useful in ranging markets
- Test: what happens to Cyber Cycle when EUR/USD is strongly trending (2022)?
- Build simple market mode detector (trend vs cycle) using MAMA phase + Cyber Cycle
- This is a preview of Week 9's work

**Day 6 — Documentation + Commit (2 hours)**
- Git commit: `feat: CyberCycle + EBS validated - cycle oscillator library complete`
- Document: **Cyber Cycle = C1/C2 candidate** in NNFX for cycle-regime strategies
- Week 8 retrospective

**Week 8 Validation Gate:**
- ✅ Cyber Cycle: oscillates cleanly, not trend-following
- ✅ EBS: cleaner signals than Cyber Cycle confirmed (or refuted)
- ✅ NNFX role: C1/C2 in cycle-mode strategies

---

**Week 9: Adaptive Trend Indicators**
*Articles: FRAMA (Fractal Adaptive MA), Adaptive Laguerre Filter*

**Why these:** FRAMA adapts its speed based on fractal dimension — it's fast in trends, slow in chop. It's a strong alternative to MAMA as a Baseline or C1 indicator.

**Day 1 — Theory (2 hours)**
- Read FRAMA article
- Key concept: Fractal Dimension D measured over N bars → alpha = exp(-4.6*(D-1))
- D=1 (straight line trend) → alpha=1 (fast). D=2 (random walk) → alpha≈0 (slow)
- Compare to MAMA: FRAMA adapts to fractal structure, MAMA adapts to instantaneous phase
- Document: when would FRAMA outperform MAMA?

**Day 2 — Implement FRAMA (2 hours)**

⏸️ **PAUSE POINT**

```c
// /zorro/indicators/ehlers/FRAMA.c
// Purpose: Fractal-adaptive trend following
// Adapts speed based on price fractal dimension

var FRAMA(vars Price, int Period) {
    // Period should be even (split into two halves)
    int N = Period / 2;
    
    // Calculate highest/lowest for each half and full period
    var Hi1 = HH(Price, N, 0);     // upper half high
    var Lo1 = LL(Price, N, 0);     // upper half low
    var Hi2 = HH(Price, N, N);     // lower half high
    var Lo2 = LL(Price, N, N);     // lower half low
    var HiAll = HH(Price, Period, 0);
    var LoAll = LL(Price, Period, 0);
    
    var N1 = (Hi1 - Lo1) / N;
    var N2 = (Hi2 - Lo2) / N;
    var N3 = (HiAll - LoAll) / Period;
    
    var D = 0.0;
    if (N1 > 0 && N2 > 0 && N3 > 0)
        D = (log(N1 + N2) - log(N3)) / log(2);
    
    var Alpha = exp(-4.6 * (D - 1));
    Alpha = clamp(Alpha, 0.01, 1.0);
    
    var* Frama = series(Price[0], 2);
    Frama[0] = Alpha * Price[0] + (1 - Alpha) * Frama[1];
    return Frama[0];
}
```

**Day 3 — FX Validation + MAMA Comparison (2 hours)**

⏸️ **PAUSE POINT**

- Run validation template on EUR/USD D1
- Side-by-side: FRAMA vs MAMA — which is smoother during chop? Which is faster in trend?
- This directly informs which to use as Baseline in strategies

**Day 4 — Crypto Testing (2 hours)**
- Run on BTC/USD H4
- Crypto has higher fractal dimension → FRAMA should slow down more in ranging crypto
- Document findings

**Day 5 — Laguerre Filter (2 hours)**
- Implement Adaptive Laguerre Filter (simpler than FRAMA, single gamma parameter)
- Compare to FRAMA as an alternative
- When would you choose Laguerre over FRAMA?

**Day 6 — Documentation + Commit (2 hours)**
- Git commit: `feat: FRAMA + Laguerre Filter validated`
- Document: **FRAMA as Baseline candidate**, especially for chop-heavy FX environments
- Week 9 retrospective

**Week 9 Validation Gate:**
- ✅ FRAMA: adapts correctly (fast in trend, slow in range confirmed)
- ✅ Comparison with MAMA documented
- ✅ NNFX role: Baseline or C1

---

**Week 10: Momentum & Leading Indicators**
*Articles: Fisher Transform, Ehlers Stochastic, Laguerre RSI*

**Why these:** Momentum indicators with Ehlers' DSP improvements — less lag, more meaningful signals than standard RSI/Stochastic.

**Day 1 — Theory (2 hours)**
- Read Fisher Transform article
- Key insight: Transforms price into Gaussian normal distribution → extreme values are more meaningful
- Read Ehlers Stochastic article — compares to standard Stochastic
- Read Laguerre RSI — uses Laguerre polynomials for smoothing with minimal lag
- Document the mathematical relationship between all three

**Day 2 — Implement Fisher Transform (2 hours)**

⏸️ **PAUSE POINT**

```c
// /zorro/indicators/ehlers/FisherTransform.c
// Purpose: Transform price distribution → Gaussian → extreme values = signals

var FisherTransform(vars Price, int Period) {
    var MaxH = HH(Price, Period, 0);
    var MinL = LL(Price, Period, 0);
    
    var Value = 0.0;
    if (MaxH != MinL)
        Value = 2 * ((Price[0] - MinL) / (MaxH - MinL)) - 1;
    Value = clamp(Value, -0.999, 0.999);
    
    var* Fish = series(0.0, 2);
    Fish[0] = 0.5 * log((1 + Value) / (1 - Value)) + 0.5 * Fish[1];
    
    return Fish[0];
}
```

**Day 3 — Implement Laguerre RSI + FX Validation (2 hours)**

⏸️ **PAUSE POINT**

- Implement Laguerre RSI (gamma parameter: 0.5-0.8 typical)
- Run validation template on EUR/USD D1 for both indicators
- Key test: do Fisher Transform extreme values (±2.5) correctly identify turning points?

**Day 4 — Crypto Testing (2 hours)**
- Run on BTC/USD H4
- Fisher Transform on crypto: more frequent extreme values (higher volatility)
- Adjust threshold for crypto (±3.0 instead of ±2.5?)
- Document parameter adjustments

**Day 5 — Ehlers Stochastic (2 hours)**
- Implement Ehlers version of Stochastic
- Compare to Fisher Transform: which has less lag? Which has fewer false signals?
- Document NNFX role: C1 or C2 candidate

**Day 6 — Documentation + Commit (2 hours)**
- Git commit: `feat: Fisher Transform, Laguerre RSI, Ehlers Stochastic validated`
- Document: Fisher Transform = strong C1/C2 candidate for overbought/oversold signals
- Week 10 retrospective

**Week 10 Validation Gate:**
- ✅ Fisher Transform: extreme values align with turning points
- ✅ Laguerre RSI: less lag than standard RSI confirmed
- ✅ NNFX role: C1/C2

---

**Week 11: Predictive & Zero-Lag Indicators**
*Articles: Predictive Moving Average, Instantaneous Trendline (review), Zero-Lag variants*

**Why these:** These indicators attempt to reduce or eliminate lag entirely — important for getting into trends early.

**Day 1 — Theory (2 hours)**
- Read Predictive Moving Average article
- Key concept: uses future price projection to reduce lag (not look-ahead — uses price derivatives)
- Review your already-implemented InstantTrendline with fresh eyes after 5 weeks of DSP study
- Has your understanding deepened? Can you explain it better now?

**Day 2 — Implement Predictive MA (2 hours)**

⏸️ **PAUSE POINT**

- Code Predictive MA
- Test basic functionality
- Compare with InstantTrendline (you already have this — now you can compare properly)

**Day 3 — FX Validation + Comparison (2 hours)**

⏸️ **PAUSE POINT**

- Run full validation template
- Three-way comparison: SMA vs InstantTrendline vs Predictive MA
- Which has least lag? Which has most false signals?

**Day 4 — Crypto Testing (2 hours)**
- Run on BTC/USD H4
- Predictive MA on fast-moving crypto: does the prediction hold?
- Document: "In trending crypto, Predictive MA enters 1-2 bars earlier than ITL"

**Day 5 — Zero-Lag EMA Review (2 hours)**
- You implemented Zero-Lag EMA in Week 1 — revisit it with your new knowledge
- Compare scientifically: ZLEMA vs Predictive MA vs InstantTrendline
- Which would you choose for NNFX C1 slot? Document your reasoning.

**Day 6 — Documentation + Commit (2 hours)**
- Git commit: `feat: PredictiveMA validated + comparative analysis of all trend indicators`
- Create summary table: all trend indicators, lag comparison, recommended use
- Week 11 retrospective

**Week 11 Validation Gate:**
- ✅ Predictive MA: lag reduction confirmed vs SMA
- ✅ Comparative analysis table created
- ✅ C1 candidates ranked

---

**Week 12: Noise Reduction & Signal Quality**
*Articles: Ehlers Kalman Filter, Correlation Cycle Indicators*

**Why these:** Kalman Filter is the optimal minimum-variance estimator — Ehlers' trading-adapted version is simpler than the full implementation but still powerful.

**Day 1 — Theory (2 hours)**
- Read Ehlers Kalman Filter article
- Understand: Kalman balances prediction vs measurement noise
- Two parameters: Slope (trend speed estimate) and Velocity (noise level)
- Note: Ehlers simplifies the full Kalman — understand what simplifications were made
- Document in `/docs/indicators/Kalman_Theory.md`

**Day 2 — Implement Ehlers Kalman Filter (2 hours)**

⏸️ **PAUSE POINT**

```c
// /zorro/indicators/ehlers/EhlersKalman.c
// Simplified Kalman filter adapted for price series

var EhlersKalman(vars Price, var Gain) {
    // Gain = Kalman gain, typically 0.6-0.9
    var* Kf = series(Price[0], 2);
    var* Velocity = series(0.0, 2);
    
    var dk = Price[0] - Kf[1];
    var Smooth = Kf[1] + dk * sqrt(Gain * 2);
    Velocity[0] = Velocity[1] + (Gain * dk);
    Kf[0] = Smooth + Velocity[0];
    
    return Kf[0];
}
```

**Day 3 — FX Validation (2 hours)**

⏸️ **PAUSE POINT**

- Run validation template on EUR/USD D1
- Compare Kalman vs SuperSmoother: different noise characteristics?
- Test Gain parameter sweep: 0.1, 0.3, 0.6, 0.9

**Day 4 — Crypto Testing (2 hours)**
- Run on BTC/USD H4
- Higher Gain needed for crypto? (faster price movements)
- Document optimal Gain per asset class

**Day 5 — Correlation Cycle Indicators (2 hours)**
- If time: implement one of Ehlers' correlation-based indicators
- These use autocorrelation to measure cycle dominance
- Even a partial implementation + theory notes is valuable

**Day 6 — Documentation + Commit (2 hours)**
- Git commit: `feat: EhlersKalman validated + correlation cycle theory documented`
- Week 12 retrospective

**Week 12 Validation Gate:**
- ✅ Kalman Filter: smoother than raw price, reasonable lag tradeoff
- ✅ Gain parameter guidelines per asset class documented

---

**Week 13: Volatility Indicators & Bands**
*Articles: Ehlers Bands, Normalized ATR, Volatility-based stops*

**Why these:** NNFX requires good volatility measurement for position sizing and stop loss placement. Ehlers improvements over standard ATR provide more stable and adaptive measurements.

**Day 1 — Theory (2 hours)**
- Read Ehlers Bands article (dynamic volatility bands)
- Compare to Bollinger Bands: what's different mathematically?
- Read normalized ATR concept: ATR as percentage of price (better for cross-asset comparison)
- Document: how does Ehlers volatility measurement differ from standard ATR?

**Day 2 — Implement Normalized ATR (2 hours)**

⏸️ **PAUSE POINT**

```c
// /zorro/indicators/ehlers/NormalizedATR.c
// ATR as fraction of price — comparable across instruments and time

var NormalizedATR(int Period) {
    var atr = ATR(Period);
    var price = (priceHigh(0) + priceLow(0) + priceClose(0)) / 3.0;
    return (price > 0) ? (atr / price) : 0.0;
}
```

- Test: NormalizedATR should give similar readings for EUR/USD and BTC/USD in similar market conditions
- This is essential for the position sizing module

**Day 3 — Implement Ehlers Bands + FX Validation (2 hours)**

⏸️ **PAUSE POINT**

- Implement dynamic bands based on Ehlers' volatility measurement
- Run validation template: do bands adapt to volatility regime changes?
- Compare to Bollinger Bands (standard): which is faster to adapt?

**Day 4 — Crypto Testing (2 hours)**
- Run on BTC/USD H4
- Ehlers Bands on crypto: should be significantly wider than FX (confirm 3-5× ratio)
- NormalizedATR comparison: FX 0.5% vs Crypto 2-3% typical?

**Day 5 — Volatility Regime Indicators (2 hours)**
- Build simple volatility regime classifier using NormalizedATR
- Low vol: NATR < 0.5% (FX), < 2% (Crypto)
- High vol: NATR > 1% (FX), > 4% (Crypto)
- This is an early preview of Phase 4 regime detection work

**Day 6 — Documentation + Commit (2 hours)**
- Git commit: `feat: NormalizedATR + EhlersBands validated - volatility toolkit complete`
- Update Risk Management module to use NormalizedATR for position sizing
- Week 13 retrospective

**Week 13 Validation Gate:**
- ✅ NormalizedATR: comparable values across FX and Crypto
- ✅ Ehlers Bands: faster volatility adaptation than Bollinger Bands
- ✅ Volatility regime classifier working

---

**Week 14: Consolidation & Indicator Library Finalization**

**Objective:** Code review, library cleanup, comprehensive documentation, and strategic review before Backtesting Bootcamp

**Day 1: Full Library Code Review (2 hours)**
- Go through every indicator in `/zorro/indicators/ehlers/`
- Check: consistent function signatures, naming conventions, comments
- Standardize: every function has header comment block with Purpose, Inputs, Outputs, Reference
- Flag any that need cleanup

**Day 2: Bug Fix & Standardization (2 hours)**
- Fix any issues found in Day 1 review
- Ensure all test scripts still compile and run cleanly
- Update any indicators where understanding improved during the 10 weeks

**Day 3: Comprehensive Comparison Table (2 hours)**
- Create `/docs/indicators/Library_Overview.md`
- Master table: all 20-25 indicators, with:

| Indicator | Category | Lag vs SMA | FX Rec. Period | Crypto Rec. Period | NNFX Role | FX Quality | Crypto Quality |
|---|---|---|---|---|---|---|---|
| SuperSmoother 2P | Smooth | Lower | 14-20 | 8-14 | C1 input | ★★★★★ | ★★★★☆ |
| ... | ... | ... | ... | ... | ... | ... | ... |

**Day 4: NNFX Component Mapping (2 hours)**
- Create strategic mapping: which indicators go in which NNFX slot?
- This directly drives strategy design in Phase 3

| NNFX Component | Primary Candidate | Secondary Candidate | Notes |
|---|---|---|---|
| Baseline | MAMA/FAMA | FRAMA | MAMA for volatile, FRAMA for choppy |
| C1 (Confirmation 1) | Fisher Transform | Cyber Cycle | Fisher for trend, Cyber for cycle |
| C2 (Confirmation 2) | Laguerre RSI | EBS | |
| Volume | (TBD Week 5-14 research) | | |
| Exit | SuperSmoother crossback | | |
| ATR / Stops | NormalizedATR | Ehlers Bands | |

**Day 5: Final Crypto vs FX Summary (2 hours)**
- Create `/docs/cross_asset/Library_FX_vs_Crypto_Summary.md`
- Key findings document: what works better on which asset class
- Parameter adjustment guidelines for moving from FX to Crypto
- This document will be referenced throughout Phases 3-6

**Day 6: Phase 2 Documentation + Git Finalization (2 hours)**
- Write Phase 2 retrospective
- Create professional README for indicator library (GitHub-ready)
- Final Git commit: `docs: Phase 2 complete - indicator library finalized`
- Write Week 14 retrospective
- **Celebrate:** You now have a professional-grade indicator library

**Phase 2 Milestone Checklist:**
- ✅ 20-25 Ehlers indicators implemented and validated
- ✅ All indicators tested on FX (EUR/USD D1) and Crypto (BTC/USD H4)
- ✅ PASS/FAIL validation applied consistently
- ✅ Parameter guidelines per asset class documented
- ✅ NNFX component mapping created
- ✅ Comprehensive library overview document
- ✅ Professional README for GitHub portfolio
- ✅ **PHASE 2 COMPLETE — Indicator library ready for strategy development**

---

### PHASE 2.5: BACKTESTING BOOTCAMP (WEEKS 15-17)

**Objective:** Master robust backtesting and validation techniques — addressing the critical skill gap that has historically prevented progress

**This is the MOST IMPORTANT phase** for preventing the failure that plagues 95% of algorithmic trading systems.

**Week 15: Walk-Forward Optimization Mastery**

**Goals:**
- Understand walk-forward analysis deeply
- Implement WFO in Zorro
- Apply to both FX and crypto strategies

*Day 1: WFO Theory (2 hours)*
- Study walk-forward optimization methodology
- Read Pardo's "The Evaluation and Optimization of Trading Strategies"
- Understand in-sample vs out-of-sample
- Calculate optimal WFO parameters (window size, step size)
- **[May 2026 addition]** Window length parameterization: there is no universally optimal training/testing window split. A 2026 study (Mroziewicz & Ślepaczuk, arXiv 2602.10785) demonstrates that Sharpe stability *across* different window sizes is a stronger robustness signal than any single window's result. Plan to test a 3×3 grid in Day 3.
- Document in `/docs/backtesting/WFO_Theory.md`

*Day 2: Zorro WFO Setup — FX (2 hours)*
- Configure Zorro's walk-forward mode
- Set up anchored vs rolling windows
- Choose optimization parameters
- Test on EUR/USD strategy
- **Outcome:** First WFO test running

*Day 3: WFO Results Analysis — FX (2 hours)*
- Analyze walk-forward efficiency
- Calculate WFO efficiency metric
- Identify stability across windows
- Target: >50% efficiency (industry standard)
- **Critical:** If <50%, strategy is overfit
- **[May 2026 addition] Parameterized WFO window grid:** Run the WFO using a 3×3 combination of training and testing window lengths:
  - Training windows: 6 months, 12 months, 18 months
  - Testing windows: 2 months, 3 months, 6 months
  - Record Sharpe ratio for each of the 9 combinations
  - A robust strategy should show stable Sharpe across most cells; large variance across the grid signals curve-fitting to a particular window size, not a genuine edge
  - Document the grid result in `/docs/backtesting/WFO_Window_Grid.md`

*Day 4: WFO Implementation — Crypto (2 hours)*
- Apply WFO to BTC/USD strategy
- Adjust window sizes for crypto (shorter history)
- Compare FX vs crypto WFO stability

*Day 5: Multi-Asset WFO (2 hours)*
- Run WFO on portfolio of FX pairs
- Run WFO on BTC/USD + ETH/USD
- Correlation of out-of-sample periods
- Document portfolio-level stability

*Day 6: WFO Documentation (2 hours)*
- Create WFO analysis template
- Document best practices
- Add to portfolio methodology section
- Write Week 15 retrospective

**Week 15 Milestone:**
- ✅ WFO theory mastered
- ✅ WFO implemented for FX strategies
- ✅ WFO implemented for crypto strategies
- ✅ >50% efficiency achieved on at least one strategy
- ✅ Portfolio-level WFO analysis

---

**Week 16: Monte Carlo Simulation**

**Goals:**
- Understand Monte Carlo methods for trading
- Implement MC simulation
- Validate strategy robustness

*Day 1: Monte Carlo Theory (2 hours)*
- Study MC simulation for trading systems
- Understand trade resampling methods
- Learn confidence interval calculation
- Document in `/docs/backtesting/MonteCarlo_Theory.md`

*Day 2: MC Implementation — FX (2 hours)*
- Code Monte Carlo simulation in Python
- Resample trade sequences
- Generate 1000+ equity curve variants
- Calculate confidence intervals

*Day 3: MC Analysis — FX (2 hours)*
- Analyze MC results for EUR/USD strategy
- Calculate percentile ranges (5th, 25th, 50th, 75th, 95th)
- Compare worst-case vs backtest
- **Reality Check:** Often reveals 2-3× worse drawdowns

*Day 4: MC Implementation — Crypto (2 hours)*
- Apply MC to BTC/USD strategy
- Account for higher crypto volatility in resampling
- Compare to FX MC results

*Day 5: Portfolio MC Simulation (2 hours)*
- Run MC on combined FX + crypto portfolio
- Analyze diversification benefits
- Worst-case portfolio scenarios

*Day 6: MC Documentation (2 hours)*
- Create MC analysis template
- Document interpretation guidelines
- Portfolio documentation update

**Week 16 Milestone:**
- ✅ Monte Carlo theory understood
- ✅ MC simulation implemented
- ✅ Confidence intervals calculated for strategies
- ✅ Worst-case scenarios identified
- ✅ Realistic expectation setting

---

**Week 17: Comprehensive Validation Framework**

**Goals:**
- Combine WFO + MC + additional validation
- Create master validation checklist
- Test strategies against robust criteria

*Day 1: Validation Framework Design (2 hours)*
- Design comprehensive validation process
- Combine WFO, MC, and other tests
- Create validation scorecard
- Define pass/fail criteria

*Day 2: Transaction Cost Analysis (2 hours)*
- Implement realistic spread costs
- Add slippage modeling
- Include commission/fees
- **Crypto:** Add funding rate for perpetuals

*Day 3: Robustness Testing (2 hours)*
- Parameter sensitivity analysis
- Test ±20% parameter variations
- Measure performance degradation
- Document robust parameter ranges

*Day 4: Market Regime Testing (2 hours)*
- Test strategies in different regimes: trending, ranging, high volatility, low volatility
- Document regime performance

*Day 5: Multi-Asset Validation (2 hours)*
- Validate FX strategies across all major pairs
- Validate crypto strategies on BTC/ETH
- Cross-pair stability analysis

*Day 6: Master Validation Documentation (2 hours)*
- Create master validation checklist
- Generate validation report template
- Add to professional portfolio
- **PHASE 2.5 COMPLETE**

---

### PHASE 3: STRATEGY DEVELOPMENT (WEEKS 18-25)

**Objective:** Develop 5-8 uncorrelated strategy candidates using your validated indicator library, tested rigorously across FX and cryptocurrency markets

> **Note:** This phase is now significantly stronger than in v3.0 because you enter it with a deep, validated indicator library and clear NNFX component mappings from Phase 2 Week 14.

**Strategy Development Principles:**
- Use the NNFX component mapping from Week 14 as your starting point
- Focus on **simplicity** (complex doesn't mean better)
- Ensure strategies are **uncorrelated** (different market inefficiencies)
- Test across **both FX and crypto**
- Apply **full validation framework** from Phase 2.5
- Target realistic performance (Sharpe 0.8-1.5, not 3.0+)

**Week 18: Trend Strategy (MAMA-Based)**

**Strategy Concept:** MAMA/FAMA Baseline + Fisher Transform C1 + Laguerre RSI C2

*Day 1: Strategy Design (2 hours)*
- Design using validated NNFX component map
- Entry: MAMA crosses FAMA (Baseline signal) + Fisher Transform confirms (C1) + Laguerre RSI not extreme (C2)
- Exit: MAMA/FAMA crossback
- Stop: 1.5× NormalizedATR
- Document in `/docs/strategies/Strategy1_MAMA_Trend.md`

*Day 2-3: Implementation & FX Testing (4 hours)*
- Code full strategy in Light-C
- Apply WFO + MC validation
- **Target:** WFO efficiency >50%

*Day 4: Crypto Adaptation (2 hours)*
- Adapt for BTC/USD H4
- Adjust stop multiplier (crypto)
- Backtest 2020-2024

*Day 5: Optimization & Validation (2 hours)*
- Full validation checklist
- Sensitivity analysis
- Regime testing

*Day 6: Documentation (2 hours)*
- Strategy documentation + performance summary
- Git commit: `feat: Strategy1 MAMA trend validated`

**Week 18 Milestone:**
- ✅ Strategy 1 (MAMA Trend) implemented and validated
- ✅ FX + Crypto tested

---

**Week 19: Mean Reversion Strategy**

**Strategy Concept:** FRAMA Baseline + Cyber Cycle C1 + EBS C2

*Day 1: Strategy Design (2 hours)*
- Design cycle/mean-reversion strategy using cycle indicators from library
- Entry: Price deviates from FRAMA + Cyber Cycle at extreme + EBS confirms
- Stop: 2.0× NormalizedATR
- **Note:** Expected to work better in ranging markets

*Day 2-4: Implementation & Testing (6 hours)*
- Code strategy, test on range-bound pairs (EUR/GBP, USD/JPY)
- WFO + MC validation
- Crypto test

*Day 5: Validation + Correlation (2 hours)*
- Full validation checklist
- Correlation with Strategy 1: should be low or negative

*Day 6: Documentation (2 hours)*
- Git commit: `feat: Strategy2 mean reversion validated`

---

**Week 20: Cycle-Based Strategy**

**Strategy Concept:** DominantCycle adaptive timing + Bandpass oscillator

*Day 1-6: Full cycle* — follow Week structure template
- Use DominantCycle (already in library) to adapt all parameters
- Cyber Cycle for entries, timed by DominantCycle period
- Full validation + crypto test

---

**Week 21: Momentum/Breakout Strategy**

**Strategy Concept:** ATR Channel Breakout + Fisher Transform Confirmation

*Day 1-6: Full cycle* — follow Week structure template
- Test on volatile pairs (GBP/JPY, EUR/JPY, BTC/USD)
- Expected: performs well on crypto

---

**Week 22: FX-Specific Hybrid Strategy**

**Strategy Concept:** Multi-indicator FX-optimized system

*Day 1-6: Full cycle*
- Combine SuperSmoother trend direction + Roofing Filter cycle timing + Kalman Filter noise filter
- Optimized for FX characteristics only
- Not designed for crypto

---

**Week 23: Crypto-Specific Strategy**

**Strategy Concept:** Designed for 24/7 high-volatility H4 crypto

*Day 1-6: Full cycle*
- Leverage 24/7 market
- Wider stops (NormalizedATR × 2.5)
- Tested on both BTC/USD and ETH/USD
- Include flash crash period analysis (May 2021, Nov 2022)

---

**Week 24: Regime-Switching Strategy [REQUIRED — May 2026 update]**

**[May 2026 update]** This week was previously a three-way optional choice. Regime detection has converged to standard practice in systematic trading research by 2026 (multiple peer-reviewed sources), and the Ehlers two-mode market model built throughout Phase 2 (MAMA/FAMA for trend detection + Cyber Cycle amplitude for cycle detection) already gives you the raw material. This week now has a fixed objective.

**Strategy Concept:** Automatic trend/cycle mode switching using the Phase 2 indicator library

*Day 1-6: Full cycle — follow Week structure template*
- **Regime signal:** MAMA/FAMA spread width → wide = trend mode, narrow = cycle mode
- **Trend mode:** MAMA/FAMA direction signal active; Cyber Cycle signals suppressed
- **Cycle mode:** Cyber Cycle Trigger/Cycle crossover active; MAMA/FAMA direction suppressed
- **Switching logic:** Hysteresis band around the spread threshold (prevents rapid switching)
- Build the market mode detector prototype first (connects directly to Week 8 validation work)
- Test on EUR/USD D1 (FX primary) and BTC/USD H4 (crypto — expected to spend more time in cycle mode)
- Full validation + WFO window grid (using the 3×3 methodology from Week 15)

*Previous options for reference (defer to later or abandon):*
- *Volume-Based Strategy: defer to post-Phase 3 if volume data quality is confirmed good*
- *Multi-Timeframe Strategy: fold into Week 22 (FX-Specific Hybrid) if time allows*

---

**Week 25: Portfolio Optimization & Strategy Selection**

*Day 1: Performance Review (2 hours)*
- Rank all 7-8 strategies by Sharpe, WFO efficiency, MC worst-case, correlation

*Day 2: Portfolio Construction (2 hours)*
- Select 4-6 best strategies
- Ensure low inter-strategy correlation (<0.3)
- Balance FX and crypto strategies

*Day 3: Portfolio Backtesting (2 hours)*
- Backtest combined portfolio
- Portfolio-level Sharpe, drawdown

*Day 4: Risk Management (2 hours)*
- Portfolio-level limits
- Correlation monitoring
- Drawdown triggers

*Day 5-6: Deployment Planning + Documentation (4 hours)*
- Phase 3 summary, deployment plan, Git finalization

**Phase 3 Milestone:**
- ✅ 4-6 final strategies selected from validated library
- ✅ Portfolio optimized and documented
- ✅ **PHASE 3 COMPLETE**

---

### PHASE 4: ML INTEGRATION & REGIME DETECTION (WEEKS 26-33)

*(Unchanged from v3.0 — see original document)*

**ML Philosophy (Evidence-Based 2024-2025):**
- ❌ Don't use ML for: Price prediction, complex deep learning
- ✅ Do use ML for: Regime detection, meta-labeling, feature engineering
- Key Insight: Simple regime filters beat ML prediction (Sharpe 1.2 vs 1.0)

**Weeks 26-33 follow the original detailed plan:**
- Week 26: ML Foundations & Setup
- Week 27: VIX-Based Regime Detection
- Week 28: Meta-Labeling Implementation
- Week 29: Advanced Regime Classification
- Week 30: Feature Importance & Model Interpretability — **[May 2026 addition] use SHAP (SHapley Additive exPlanations) as the primary tool.** Python `shap` library is compatible with scikit-learn, LightGBM, and XGBoost — all already in the roadmap. SHAP quantifies each feature's marginal contribution to model output, enabling portfolio-quality documentation of *why* the regime classifier makes each decision. This is also a strong professional portfolio signal (see Pagliaro 2026, Electronics 15(6)).
- Week 31: Integration with AI/ML Project — **[Aug 2026 addition] candidates to evaluate:** foundation-model time-series forecasters (e.g. Chronos-Bolt; already tested once in the parallel ML-Mastery project — pull that result forward rather than re-testing from scratch) and RL-for-trading frameworks beyond plain DQN (sentiment-aware curriculum learning, CE-PPO). Neither slots into the NNFX C1/C2 confirmation architecture — both would sit alongside or replace it, so evaluate here, not in Phase 2.
- Week 32: Production ML Pipeline
- Week 33: Phase 4 Consolidation

*(Refer to v3.0 for full day-by-day breakdown)*

---

### PHASE 5: PAPER TRADING & VALIDATION (WEEKS 34-40)

*(Unchanged from v3.0)*

- Week 34: Paper Trading Setup (FX + Crypto deployed)
- Weeks 35-37: Live Paper Trading (monitoring focus)
- Week 38: Analysis & Refinement
- Week 39: Stress Testing & Edge Cases
- Week 40: Go/No-Go Decision

*(Refer to v3.0 for full day-by-day breakdown)*

---

### PHASE 6: LIVE DEPLOYMENT (WEEKS 41-48)

*(Unchanged from v3.0)*

- Week 41: Initial Live Deployment (one strategy each, minimum sizing)
- Week 42: Gradual Scale-Up
- Week 43: Portfolio Expansion
- Week 44: Capital Scale-Up
- Week 45: Full Strategy Deployment
- Week 46: Scale to Target Capital ($10K FX + crypto)
- Week 47: Optimization & Refinement
- Week 48: Program Completion & Future Planning

*(Refer to v3.0 for full day-by-day breakdown)*

---

## 📈 SUCCESS METRICS

### Performance Targets (Realistic)
**After 48 Weeks:**
- Live Sharpe Ratio: 0.8-1.5 (realistic, not 3.0+)
- Maximum Drawdown: <20%
- Win Rate: 35-55% (not 70%+)
- Profit Factor: 1.3-2.0
- Monthly Return: 1-3% (12-36% annually)

**Portfolio Composition:**
- 4-6 uncorrelated strategies deployed
- 70% FX, 30% Crypto allocation achieved
- Statistical edge validated through live trading

**Professional Development:**
- GitHub portfolio with 20-25 validated indicators
- 4-6 validated trading strategies built on top of that library
- Indicator library as standalone portfolio project
- Employable skillset in systematic trading

---

## 💡 KEY PRINCIPLES

### Trading Principles
1. **Simple beats complex** (Macrosynergy 2024)
2. **Walk-forward >50% efficiency mandatory**
3. **Monte Carlo reveals truth** (often 2-3× worse)
4. **Transaction costs matter** (model realistically)
5. **Crypto ≠ FX** (different volatility, different rules)

### Phase 2 Indicator Principles (NEW in v4.0)
1. **Validate before building** — no indicator enters the library without passing criteria
2. **One category per week** — depth leads to better strategies
3. **NNFX mapping first** — always ask "which slot does this fill?"
4. **Cross-asset always** — FX behavior ≠ Crypto behavior, document differences
5. **The library IS the product** — it's a standalone portfolio piece

### Development Principles
1. **Document everything** (portfolio + debugging)
2. **Version control is non-negotiable** (Git daily)
3. **Test across assets** (FX and crypto)
4. **Validate thoroughly** (WFO + MC + regime)
5. **Trust the process** (don't curve-fit)

---

## 📚 RESOURCE MASTER LIST

*(Unchanged from v3.0)*

### Books (Priority Order)
- Howard Bandy — "Quantitative Trading Systems"
- John Ehlers — "Cybernetic Analysis for Stocks and Futures"
- John Ehlers — "Rocket Science for Traders"
- Robert Pardo — "The Evaluation and Optimization of Trading Strategies"
- Marcos López de Prado — "Advances in Financial Machine Learning"

### Tools & Platforms
- Zorro 2.70+: Primary development platform
- MT4/MT5: FX execution via DarwinEx
- Binance API: Crypto execution
- Python 3.11: Analysis, ML, feature engineering
- Jupyter: Analysis notebooks
- Git/GitHub: Version control

---

## 🚨 CRITICAL RISK WARNINGS

*(Unchanged from v3.0 — all original warnings apply)*

---

## 🎓 PROFESSIONAL PORTFOLIO NOTES

### What This Roadmap Adds to Your Portfolio (v4.0 improvements)

The indicator-first approach means your portfolio now has **two distinct professional artifacts**:

1. **Indicator Library** (Weeks 4-14 output): A curated, validated Ehlers DSP indicator library with documented performance characteristics per asset class. This is independently valuable and shows systematic research methodology.

2. **Trading Strategies** (Weeks 18-25 output): Strategies explicitly built using the indicator library, with clear documented reasoning for every component choice. Reviewers can trace the logic from DSP theory → indicator → strategy component → validation.

This chain of evidence — theory → implementation → validation → strategy application — is exactly what separates professional systematic traders from hobbyists.

---

**Document Version:** 4.0 - Indicator-First Revised  
**Created:** February 2026  
**Revised From:** v3.0 (November 2025)  
**For:** Gusbi — FX & Cryptocurrency Trading Systems Development  
**Platform:** Zorro + MT4/MT5 + Binance  
**Framework:** NNFX + John Ehlers DSP + Evidence-Based ML

---

*You've got this. The library you're building in Weeks 5-14 will be the foundation everything else stands on.*

🚀
