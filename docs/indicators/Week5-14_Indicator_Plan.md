# Week 5-14 Indicator Implementation Plan
**Created:** Week 4 Day 6  
**Purpose:** Curated selection of 26 Ehlers indicators for systematic 
implementation and validation across FX and crypto markets

---

## Working Methodology (Every Week)

| Day | Focus |
|---|---|
| Day 1 | Read article — understand the problem it solves |
| Day 2 | Work through the math — formulas, coefficients, why they are what they are |
| Day 3 | Implement in Light-C — code flows naturally from understood math |
| Day 4 | Validate (FX) — run analysis template, interpret results |
| Day 5 | Validate (Crypto) + parameter sensitivity |
| Day 6 | Documentation, Git commit, weekly retrospective |

**Rule:** No coding before the math is understood.  
**Gate:** Every indicator must pass PASS/FAIL validation before entering the library.

---

## Week 5 — Smoothing Filters
*Foundation week — SuperSmoother appears inside most other Ehlers indicators*

| # | Indicator | Article | NNFX Role |
|---|---|---|---|
| 1 | SuperSmoother 2-pole | Moving averages and smoothing filters.pdf | C1 input / Baseline smoothing |
| 2 | SuperSmoother 3-pole | Moving averages and smoothing filters.pdf | Alternative smoothing |
| 3 | Ultimate Smoother | The Ultimate Smoother.pdf | Zero-lag smoothing candidate |

---

## Week 6 — High-Pass & Roofing Filter
*Removes trend to isolate cycles — prerequisite for oscillators*

| # | Indicator | Article | NNFX Role |
|---|---|---|---|
| 4 | High-Pass Filter | Optimal Detrending.pdf | Trend removal / oscillator input |
| 5 | Roofing Filter | Whiter Is Brighter.pdf | Band-pass / oscillator preprocessor |
| 6 | Decycler | Decyclers.pdf | Trend isolation alternative |

---

## Week 7 — MESA Adaptive Moving Average
*Primary Baseline candidate — Hilbert Transform based*

| # | Indicator | Article | NNFX Role |
|---|---|---|---|
| 7 | MAMA | MESA Adaptive Moving Averages.pdf | Baseline (primary candidate) |
| 8 | FAMA | MESA Adaptive Moving Averages.pdf | Baseline companion (crossover signal) |

---

## Week 8 — Cycle Oscillators
*Measures cycle state — C1/C2 candidates for ranging markets*

| # | Indicator | Article | NNFX Role |
|---|---|---|---|
| 9 | Cyber Cycle | Adaptive Trends And Oscillators.pdf | C1/C2 cycle mode |
| 10 | Even Better Sinewave | Measuring Market Cycles.pdf | C1/C2 refined oscillator |
| 11 | Bandpass Indicator | The Bandpass Indicator.PDF | C1/C2 alternative |

---

## Week 9 — Adaptive Trend Indicators
*Trend followers that adapt to market conditions*

| # | Indicator | Article | NNFX Role |
|---|---|---|---|
| 12 | FRAMA | Fractal Adaptive Moving Averages.pdf | Baseline alternative to MAMA |
| 13 | Laguerre Filter | Laguerre Filters.pdf | C1 / Baseline simple adaptive |
| 14 | Deviation-Scaled MA | The Deviation-Scaled Moving Average.pdf | C1 / volatility-adaptive trend |

---

## Week 10 — Momentum & Transform Indicators
*Leading indicators for overbought/oversold — C1/C2 candidates*

| # | Indicator | Article | NNFX Role |
|---|---|---|---|
| 15 | Fisher Transform | Using The Fisher Transform.PDF | C1/C2 overbought/oversold |
| 16 | Inverse Fisher Transform | The Inverse Fisher Transform.pdf | Signal quality booster |
| 17 | Center of Gravity | The Center Of Gravity Oscillator.pdf | C1/C2 zero-lag oscillator |

---

## Week 11 — Zero-Lag & Predictive Indicators
*Lag reduction — compare against InstantTrendline already in library*

| # | Indicator | Article | NNFX Role |
|---|---|---|---|
| 18 | Reflex | Reflex_A_New Zero-Lag Indicator.pdf | C1 zero-lag candidate |
| 19 | Predictive MA | Predictive And Successful Indicators.pdf | C1 predictive candidate |
| 20 | Ehlers Leading Indicator | Moving Averages Part 2 Ehlers Leading Indicator (ELI).pdf | C1 comparison with ITrend |

---

## Week 12 — Noise Reduction & Signal Quality
*Filters that improve signal quality rather than just smoothing*

| # | Indicator | Article | NNFX Role |
|---|---|---|---|
| 21 | Ehlers Kalman Filter | Every Little Bit Helps.pdf | Baseline / C1 smoothing |
| 22 | Recursive Median Filter | Recursive Median Filters.pdf | Noise reduction / outlier handling |
| 23 | Correlation Cycle Indicator | Correlation As A Cycle Indicator.pdf | Cycle confirmation |

---

## Week 13 — Volatility & Stops
*Essential for position sizing and stop placement in NNFX*

| # | Indicator | Article | NNFX Role |
|---|---|---|---|
| 24 | Normalized ATR | Setting stops — a new approach.pdf | ATR / position sizing |
| 25 | Ultimate Channels & Bands | Ultimate Channels And Ultimate Bands.pdf | Volatility bands / stops |
| 26 | Laguerre RSI | (Yet Another) Improved RSI.pdf | C2 / exit signal |

---

## Week 14 — Consolidation
*No new indicators — library review, NNFX component mapping, documentation*

- Full library code review and standardization
- Comprehensive comparison table (all 26 indicators)
- NNFX component mapping document
- Cross-asset parameter guidelines
- Professional GitHub README

---

## Selection Criteria
Each indicator was selected because it:
- Has a clear mathematical formula in an available Ehlers article
- Fills a distinct role not covered by other selections
- Is referenced in NNFX-style systems or has clear trading application
- Is not redundant with already-implemented indicators

## Already in Library (Pre-Week 5)
- InstantTrendline (fixed version recommended)
- DominantCycle (Griffiths method)
- SuperSmoother (basic version from Week 2)
- Zero-Lag EMA (Week 1)