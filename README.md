# FX & Crypto Algorithmic Trading Systems

Building algorithmic trading systems using the **Zorro platform**, **John Ehlers DSP-based
indicators**, and the **NNFX (No Nonsense Forex)** framework.

**Goal:** profitable, walk-forward validated trading systems.

> **Where this stands.** This is a **DSP filter library**. Each indicator is implemented in
> Light-C and measured — frequency response, lag, bandwidth — on multiple assets using the
> same parameters throughout. An indicator is described by what it does, not by what its
> source article says it detects.
>
> **No strategy has been backtested yet.** Everything here is indicator-level.

---

## Current Status

**Phase 2 — Indicator Deep Dive**

- ✅ 22 indicators implemented and measured (+ 1 documented FAIL)
- ✅ Two strategy baselines locked; both C1 slots locked
- ⚠️ **Both C2 slots open** — decided at strategy level, see [Strategy Decisions](#strategy-decisions)
- 🔄 In progress: finish the library — remaining C2 candidates, ATR, exit logic
- ⏳ Next: **Backtesting Bootcamp** — first strategy-level results
- ⏳ Then: strategy assembly, ML integration, live deployment

---

## How Indicators Are Evaluated

Two rules govern what enters the library and what makes it into a strategy.

**1. An indicator is judged by what it does, not by what the article claims.**
Lag, frequency response and bandwidth are measurable. The author's explanation of *why* it
should work is not, and does not affect the decision. If an article claims cycle detection
and the code is a linear filter, the library entry says filter.

**2. Whether a component adds anything is a strategy-level question.**
Correlation and lag can flag a candidate as redundant, but they can't prove it adds value.
We need a backtest. For example, does a given C1 + C2 beat C1 alone?

---

## Instrument Universe

The goal is to trade many instruments. The risk is that testing many instruments turns into
shopping for one that works. So the instruments are split in two, and the split is fixed in
advance.

| Set | Instruments | Role |
|---|---|---|
| **Development** | EUR/USD D1, BTC/USD H4, EUR/JPY D1, AUD/USD D1 | Where every decision gets made |
| **Confirmation** | Remaining majors and crosses, plus XAU/USD, XAG/USD, WTI/USD | Where decisions get checked |

Say you are choosing a C1 confirmation indicator. Test the candidate on the development set.
If it fails there, drop it. If it passes, run it on the confirmation set without changing
anything — same parameters, no retuning. If it fails there, drop it too.

**Why not just test everything.** Most FX pairs move together — EUR/USD, GBP/USD and AUD/USD
all trade against the dollar, and they correlate at 0.6 to 0.9. So twenty pairs are not
twenty separate tests. They are closer to four. Test enough of them and something will pass
by luck. Metals and oil are in the confirmation set because they move for different reasons,
so they are a real check.

A component might work on FX and not on commodities. That would be worth knowing — but it
has to be a question asked up front and not in retrospect.

*EUR/JPY, AUD/USD, XAU, XAG and WTI aren't set up in Zorro yet. Until they are, measurements
are two-asset.*

---

## Technology Stack

| Tool | Role |
|------|------|
| **Zorro Platform** (Light-C) | Indicator implementation, backtesting, live execution |
| **Python / Jupyter / NumPy** | Statistical validation, surrogate testing, cross-asset analysis |
| **Git / GitHub** | Version control, portfolio documentation |
| **102 Ehlers TASC articles** | Primary source material |

---

## Indicator Library

Validated on **EUR/USD D1 (2015–2024)** and **BTC/USD H4 (2020–2024)** with identical
parameters — no per-asset retuning.

| Indicators | Role | Status |
|-----------|------|--------|
| SuperSmoother 2-Pole, 3-Pole, Ultimate Smoother | Foundation filters | ✅ Library |
| HighPassFilter, RoofingFilter, Decycler | Noise isolation / preprocessors | ✅ Library |
| MAMA, FAMA | Baseline | ✅ **Strategy 1 Baseline: FAMA** |
| CyberCycle, Elegant Oscillator (EBS) | C1/C2 candidates | ✅ Library — both classified as band-pass filters |
| FRAMA, Laguerre Filter, DSMA | Baseline, smoothing | ✅ **Strategy 2 Baseline: FRAMA** |
| Fisher Transform, Inverse Fisher, COG | C1 confirmation | ✅ **Fisher = C1, Strategy 1** |
| Reflex, MESA Stochastic, ELI | C1/C2 confirmation | ✅ **MESA Stochastic = C1, Strategy 2**. ELI ❌ documented FAIL |
| Recursive Median + RMO, Alpha-Beta Filter, Correlation Cycle | Noise reduction, C2 candidate | ⚠️ See below |
| InstantTrendline, DominantCycle | Early implementations | ✅ Library |

### Recent outcomes

| Indicator | Outcome |
|---|---|
| **Recursive Median (RM)** | The article says to use it on crypto because it ignores flash crashes. But BTC's big moves don't bounce back — they're real, not bad data. RM throws them out anyway, and tracks price worse than a plain EMA. **Only useful when the data itself is dirty.** |
| **RMO** | **Dropped as a C2 candidate.** Correlation with MESA Stochastic was 0.799. The limit, set in advance, was 0.65. |
| **Alpha-Beta Filter** | Doesn't smooth. It leads price by one bar, and above a gain of 0.246 it adds noise instead of removing it. |
| **Correlation Cycle** | A linear filter. Implemented and measured. |

---

## Strategy Decisions

### Strategy 1: FAMA Baseline + Fisher C1 + Reflex C2 ⚠️

| Component | Indicator | Status |
|-----------|-----------|--------|
| Baseline | FAMA | ✅ Locked |
| C1 | Fisher Transform (Period=10) | ✅ Locked |
| C2 | Reflex (Length=20) | ⚠️ **FLAGGED — open question** |
| ATR / Exit | TBD | — |

> **Why Reflex is flagged.** It was picked for being a different kind of filter than Fisher.
> Later measurement showed correlation with Fisher is about 0.60 on both assets — high
> enough to worry about, not high enough to disqualify.
>
> A rough test of whether it actually helps gave opposite answers on the two assets: it
> improved EUR/USD and hurt BTC/USD. That test was crude — no entry rules, no costs — so it
> isn't grounds to remove Reflex. It is grounds to stop treating the slot as settled until
> there's a real backtest.

### Strategy 2: FRAMA Baseline + MESA Stochastic C1 ⚠️

| Component | Indicator | Status |
|-----------|-----------|--------|
| Baseline | FRAMA | ✅ Locked |
| C1 | MESA Stochastic (20, 48, 10) | ✅ Locked |
| C2 | **OPEN** | ⚠️ No candidate accepted |
| Exit | TBD | — |

**Why two strategies:** FAMA (phase-locked adaptive) and FRAMA (fractal adaptive) use
fundamentally different adaptation mechanisms — diversification by mechanism, not by
parameter. Extended to C1 selection: Strategy 2 shares no confirmation indicator with
Strategy 1.

### Why both C2 slots are open

The original plan was to pick C2 by correlation: if it correlates too much with C1, it's
redundant.

Reflex showed the flaw. Same correlation with Fisher on both assets — around 0.60 — but it
helped on one and hurt on the other. Correlation can't tell those two cases apart, so it
can't be the deciding test.

The criterion was rewritten before any new data was produced, and now has two stages:

- **C-3a — correlation.** A warning, not a verdict.
- **C-3b — does adding C2 make the strategy better?** Backtest the strategy with C1 alone,
  then again with C1 + C2, on data the parameters were never fitted to, with spreads and
  commissions included. If the C1 + C2 version doesn't come out ahead on every development
  instrument, C2 is out. **This decides.**

C-3b needs a working backtest, which doesn't exist yet. That's why both slots are open.

📄 [`docs/indicators/C2_Selection_Criteria_PreRegistered.md`](docs/indicators/C2_Selection_Criteria_PreRegistered.md)

---

## Method: Pre-Registration

Selection criteria go into this repository **before** the data that tests them exists. Once
results come in, the thresholds don't move.

**The RMO case is the worked example.** The criteria were committed with a prediction: RMO's
correlation with C1 would land between 0.40 and 0.65, and anything above 0.65 was out. It
measured 0.799 two days later. The prediction was wrong, the threshold stayed, and RMO was
dropped. Both the prediction and its timestamp are in the git history.

**Why the prediction was wrong.** RMO's median filter only does something when there's an
outlier. The rest of the time it behaves like an ordinary linear filter — which is exactly
what MESA Stochastic is. So they measured almost the same thing.

**When a criterion changes, the old one stays visible.** Amendments are dated and added below
the original text, never in place of it. Decisions already made under the old rule are not
revisited.

---

## Engineering Principles

- **Theory before code.** The first two days of each week are theory only. One indicator's
  lag was worked out on paper as 3.37 bars before anything was written; it measured 3.366.
- **Judge an indicator by what it does**, not by what its article claims it detects.
- **Combinations decide.** Indicator-level metrics narrow the field; the backtest picks the
  winner.
- **Decisions are made on the development set only.** The confirmation set checks them.
- **Test the measuring tool first.** An EMA has a known lag of 1.50 bars. One method for
  measuring lag reported 0.00 for it — so that method was broken, not the EMA. Any tool used
  for measurement gets checked against a known result before it's trusted.
- **Same parameters everywhere.** If an indicator needs different settings per asset, that's
  overfitting.
- **Failures stay documented.** ELI failed. RMO was dropped. The Alpha-Beta claims were
  retracted. Recursive Median's crypto rationale didn't survive testing.
- **The sources contain errors.** One week alone turned up three, including one indicator
  that manufactures the very signal it claims to detect.

---

## Research

**Testing the cycle premise.** Most of Ehlers' work assumes price contains a repeating cycle
worth extracting. That assumption was tested rather than accepted.

The method: take the real price history and shuffle the daily moves into a random order. The
same numbers are still there — so the average move, the spread of moves, the biggest gain and
the worst loss are all identical. Those depend on which numbers you have, not what order they
come in. A cycle is the opposite: it exists only in the ordering. Shuffle the order and any
cycle is destroyed, while everything that doesn't depend on order survives. That gives you a
version of the market with the cycle removed and nothing else changed.

Do that a thousand times. Then run a cycle detector on the real data and on all thousand
shuffled versions. If the real data has a cycle, it should score higher than the shuffled
ones.

It didn't. Across 64 tests on EUR/USD and BTC/USD, the real data scored no better. The
detector was checked first on artificial data with a cycle deliberately added, so we know it
works: it catches a cycle that accounts for more than about 5% of price movement.

A plain shuffle also destroys volatility clustering — the tendency of big moves to come in
bursts — which a critic could argue is what the detector was really missing. So three harder
comparisons were run alongside it, including one built to reproduce volatility clustering
with no cycle at all. The result held. Details in [`docs/research/`](docs/research/).

**This covers two assets and one set of settings.** It doesn't prove cycles never exist, and
it doesn't make these filters useless — a filter still does what it does, whatever the reason
it was built. It isn't used to accept or reject indicators here.

One result did carry forward: **volatility persists, direction doesn't.** Big moves cluster;
up and down don't.

**Shuffle testing will be more useful on strategies than on indicators.** Run a strategy on a
thousand shuffled histories and see whether its real result stands out. A walk-forward test
doesn't ask that.

---

## Repository Structure

```
fx-trading-systems/
├── indicators/ehlers/          # DSP indicators (Light-C)
├── strategies/tests/           # Zorro test scripts — one per indicator
├── analysis/
│   ├── null_tests/             # Surrogate-data harnesses (reproducible, seeded)
│   ├── notebooks/              # Jupyter validation notebooks
│   └── scripts/                # Shared Python utilities
├── docs/
│   ├── ZORRO_LIGHTC_GOTCHAS.md # Platform reference — silent-failure modes marked
│   ├── indicators/             # Theory, criteria, findings, decisions
│   ├── research/               # Surrogate testing and scope decisions
│   ├── roadmap/                # Program roadmap (versioned)
│   └── weekly_reports/         # Weekly progress notes
└── research/articles/          # 102 Ehlers TASC articles
```

---

## Reproducibility

Surrogate harnesses use fixed seeds and regenerate the published figures exactly:

```bash
cd analysis/null_tests
python run_experiment.py                 # spectral prominence
python phase_coherence_null_test.py      # phase coherence + periodogram
```

Every claim above traces to a commit. Predictions carry timestamps preceding the data
that tested them.

---

*Systematic trading is built one indicator at a time — and every component has to earn
its slot.*
