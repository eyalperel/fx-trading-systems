# FX & Crypto Algorithmic Trading Systems

A systematic 48-week program to build institutional-quality algorithmic trading systems using the **Zorro platform**, **John Ehlers DSP-based indicators**, and the **NNFX (No Nonsense Forex)** framework.

**Two parallel goals:**
1. Build genuinely profitable, walk-forward validated trading systems
2. Build a professional portfolio for employment in systematic/quantitative trading

---

## Current Status

**Week 11 of 48 — Phase 2: Indicator Deep Dive**

- ✅ Phases 1–2 (partial): Foundation + 7 indicator weeks complete
- ✅ 18 Ehlers indicators implemented and validated (+ 1 documented FAIL: ELI)
- ✅ Two strategy baselines locked
- ✅ Strategy 1 C1 + C2 locked (Fisher + Reflex); Strategy 2 C1 locked (MESA Stochastic)
- 🔄 Weeks 12–14: Complete indicator library (Strategy 2 C2, ATR, Exit slots)
- ⏳ Weeks 15–17: Backtesting Bootcamp (walk-forward, Monte Carlo)
- ⏳ Weeks 18+: Strategy assembly, ML integration, live deployment

---

## Technology Stack

| Tool | Role |
|------|------|
| **Zorro Platform** (Light-C) | Indicator implementation, backtesting, live execution |
| **Python / Jupyter** | Statistical validation, cross-asset analysis, visualization |
| **Git / GitHub** | Version control, portfolio documentation |
| **VS Code** | Primary editor |
| **102 Ehlers TASC articles** | Primary source material for all indicators |

---

## Indicator Library — Weeks 5–11

All indicators validated on **EUR/USD D1 (2015–2024, 2,596 bars)** and **BTC/USD H4 (2018–2024, 10,423 bars)** using identical parameters — no per-asset retuning.

| Week | Indicators | NNFX Role | Status |
|------|-----------|-----------|--------|
| 5 | SuperSmoother 2-Pole, 3-Pole, Ultimate Smoother | Foundation filters | ✅ Library |
| 6 | HighPassFilter, RoofingFilter, Decycler | Noise isolation / preprocessors | ✅ Library |
| 7 | MAMA, FAMA | Baseline (trend filter) | ✅ Library — **Strategy 1 Baseline: FAMA** |
| 8 | CyberCycle, EBS, Bandpass | C1/C2 candidates | ✅ Library |
| 9 | FRAMA, Laguerre Filter, DSMA | Baseline, smoothing | ✅ Library — **Strategy 2 Baseline: FRAMA** |
| 10 | Fisher Transform, Inverse Fisher (Elegant Oscillator), COG | C1 confirmation | ✅ Library — **Fisher = C1, Strategy 1** |
| 11 | Reflex, MESA Stochastic, ELI | C1/C2 confirmation | ✅ Library (Reflex, MESA Stoch) — **Reflex = C2, Strategy 1; MESA Stochastic = C1, Strategy 2**. ELI: ❌ documented FAIL (weak, unstable phase alignment — see Week 11 notes) |

---

## Strategy Decisions — Locked

### Strategy 1: FAMA Baseline + Fisher C1 + Reflex C2
| Component | Indicator | Key Metric |
|-----------|-----------|------------|
| Baseline | FAMA | 252 crossovers / 10 yrs (10.3 bars/signal) |
| C1 | Fisher Transform (Period=10) | 256 filtered signals after FAMA gate (47.1% reduction) |
| C2 | Reflex (Length=20) | 0 bars lag vs RoofingFilter, r=0.776 (FX) / r=0.599 (BTC) — genuine zero-lag |
| ATR / Exit | TBD (Week 13–14) | — |

**Why Fisher over CyberCycle for C1:** simpler implementation, no RoofingFilter preprocessor required, comparable signal quality, statistically grounded ±2.5 reversal thresholds.

**Why Reflex over MESA Stochastic for C2:** genuine mathematical diversification. Fisher and MESA Stochastic are both fundamentally range-position oscillators (normalize price's position within a recent HH/LL window); Reflex is a different family (trend-line deviation summation). Pairing two range-position indicators as C1+C2 would give correlated, not independent, confirmation.

### Strategy 2: FRAMA Baseline + MESA Stochastic C1
| Component | Indicator | Key Metric |
|-----------|-----------|------------|
| Baseline | FRAMA | Fractal-dimension adaptive — genuinely different math from FAMA |
| C1 | MESA Stochastic (StochPeriod=20, HP=48, SS=10) | Anticipatory-crossing confirmed: troughs -1.08 bars (BTC, p<0.0001), -1.61 bars (FX, p=0.0002) |
| C2–Exit | TBD (Weeks 12–14) | — |

**Why two strategies:** FAMA (phase-locked adaptive) and FRAMA (fractal adaptive) use fundamentally different adaptation mechanisms — true diversification, not parameter variation. Extended this week to C1 selection: Strategy 2 deliberately uses neither of Strategy 1's confirmation indicators, keeping the two strategies mathematically distinct end-to-end.

---

## Cross-Asset Validation Results (Week 10)

| Metric | EUR/USD D1 | BTC/USD H4 |
|--------|-----------|-----------|
| Fisher std | 1.843 | 1.899 |
| Fisher range | −7.23 / +7.41 | −7.26 / +7.59 |
| COG equilibrium | −5.5005 | −5.4983 |
| EO hard bound ±1 | ✅ 100% | ✅ 100% |
| Bars per signal | 5.4 | 5.5 |

Same Period=10 parameters generalize across a 34× price range ($3,221–$108,888) without modification.

## Cross-Asset Validation Results (Week 11)

| Metric | EUR/USD D1 | BTC/USD H4 |
|--------|-----------|-----------|
| Reflex vs RoofingFilter (lag, corr) | 0 bars, r=0.776 | 0 bars, r=0.599 |
| Reflex mean / std | -0.004 / 0.985 | +0.012 / 0.978 |
| MESA Stoch vs RoofingFilter (lag, corr) | 1 bar, r=0.758 | 1 bar, r=0.524 |
| MESA Stoch anticipatory lead (troughs) | -1.61 bars, p=0.0002 | -1.08 bars, p<0.0001 |

Both indicators generalize across assets without retuning — same parameters (Length=20 / StochPeriod=20) used throughout.

---

## Repository Structure

```
fx-trading-systems/
├── indicators/
│   └── ehlers/              # 18 Ehlers DSP indicators (Light-C) + 1 documented FAIL
├── strategies/
│   └── tests/               # Zorro test scripts — one per indicator week
├── analysis/
│   ├── notebooks/           # Jupyter validation notebooks + charts
│   └── scripts/             # Shared Python utilities (indicator_metrics.py)
├── docs/
│   ├── indicators/          # Indicator plans and notes
│   ├── roadmap/             # Program roadmap (versioned)
│   └── weekly_reports/      # Weekly progress notes (Weeks 1–11)
└── research/
    └── articles/            # 102 Ehlers TASC articles (primary source)
```

---

## Engineering Principles

- **Theory before code** — Days 1–2 of each week are pure theory, no implementation
- **No per-asset retuning** — parameters must generalize; retuning is overfitting
- **Simpler wins** — Fisher chosen over CyberCycle: fewer dependencies, same quality
- **Default parameters over optimized** — optimization improves in-sample, degrades out-of-sample
- **Validate before building on** — every indicator cross-validated on EUR/USD D1 and BTC/USD H4 before use in strategy
- **Document failures, not just successes** — a fairly-tested FAIL (ELI, Week 11) is real evidence supporting the C1/C2 decision, not wasted effort
- **Diversify by mechanism, not just parameters** — C1/C2 pairing follows the same mathematical-lineage principle as Baseline selection (Week 9)

## Zorro Light-C Gotchas (Standing Reference)

- Trig functions take **radians** — `cos(1.414*PI/Period)` not degrees
- `Period` is a reserved Zorro variable — use `BarPeriod` for bar duration
- All indicator calls must occur **before** `if(is(LOOKBACK)) return;`
- IIR state variables in included files must use `static`, not `series()`
- `#include <default.c>` must be the first line of every strategy script
- File output: use `file_append()` not `file_write()`

---

*Systematic trading is built one indicator at a time.*
