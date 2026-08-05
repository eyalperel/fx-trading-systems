# Strategy 2 C2 Slot — Week 12 Decision Record

**Date:** 2026-08-05, Week 12 Day 4
**Governed by:** `docs/indicators/C2_Selection_Criteria_PreRegistered.md`
(registered 2026-08-05, pushed as `e4b1f5b` **before** any of the data below existed)
**Outcome:** ⛔ **NO CANDIDATE ACCEPTED. C2 REMAINS OPEN.**

---

## 1. Decision

| Candidate | Verdict | Decisive criterion |
|---|---|---|
| Recursive Median Oscillator (RMO) | **ELIMINATED** | C-3, \|ρ\| = 0.799 vs threshold 0.65 |
| Alpha-Beta Filter | **ELIMINATED** | C-1, outputs a price level, not an oscillator |
| Correlation Cycle | Not evaluated as C2 | Deferred to Day 5 null test (Principle 6) |

Per the pre-registered decision procedure, step 6: *"If none pass → leave C2 open,
document why, defer to Laguerre RSI in Week 13. An empty slot is a valid outcome and is
preferable to a C2 that duplicates C1."*

**Strategy 2 therefore stands as:**

| Slot | Component | Status |
|---|---|---|
| Baseline | FRAMA | Locked |
| C1 | MESA Stochastic (20, 48, 10) | Locked |
| C2 | **OPEN** | Deferred to Week 13 (Laguerre RSI) |

> **The threshold was not revised.** The 0.65 elimination bound was written and pushed to
> a public remote two days before the measurement. Revising it after seeing |ρ| = 0.799
> would have converted the pre-registration into decoration. It was not revised.

---

## 2. C-3 measurement — the decisive result

Pearson correlation between candidate output and MESA Stochastic output (centred at its
neutral 50), contemporaneous, full available history.

| Asset | Bars | Pearson | Spearman | Sign agreement |
|---|---|---|---|---|
| EUR/USD D1 (2015–2024) | 2,596 | **+0.799** | +0.854 | 84.7% |
| BTC/USD H4 (2020–2024) | 7,534 | **+0.682** | +0.809 | 85.1% |

**Worse of the two assets: |ρ| = 0.799.**

| Threshold | Outcome |
|---|---|
| ≤ 0.50 | PASS |
| 0.50 – 0.65 | CONDITIONAL |
| **> 0.65** | **FAIL — ELIMINATED** ← both assets |

Stability across the EUR/USD sample (five equal segments): +0.837, +0.843, +0.770,
+0.806, +0.823. Not an artefact of one period.

**The operationally meaningful number is sign agreement: ~85% on both assets.** As a
zero-crossing confirmation, RMO would agree with MESA Stochastic on roughly five bars in
six. That is not a second confirmation. It is the same signal with additional
computation, and it would manufacture the appearance of independent agreement — worse
than an empty C2 slot, which is at least honest about carrying no information.

---

## 3. Registered prediction was WRONG

**Predicted (Day 2, before implementation):** |ρ| ∈ 0.40–0.65.
**Actual:** 0.799 (FX), 0.682 (BTC). Outside the range on both assets.

### 3.1 Why the prediction failed

The prediction assumed the non-linear median front end would decorrelate RMO from MESA
Stochastic's linear roofing filter. Measured, it barely does:

```
corr(RM, plain EMA) = 0.9965 (EUR/USD D1)   0.9997 (BTC/USD H4)
```

**RM is ~99.7% correlated with a plain EMA.** Median-vs-mean divergence over the 5-bar
window averages only ~0.3 σ.

The error was conflating *mechanism exists* with *mechanism operates*. A median differs
from a mean **only when outliers are present**. On ordinary bars — the overwhelming
majority — the five recent prices are near-monotonic and the median sits close to the
mean. So on ~99% of bars:

```
RM  ≈ EMA
RMO ≈ high-pass(EMA) ≈ band-pass filter
```

and MESA Stochastic is a band-pass filter with normalisation. Passbands overlap (RMO
≈ 12–30 bars; MESA roofing ≈ 10–48 bars). Correlation follows directly.

Criterion C-2 (mechanistic distinctness) passed on theory. The theory was correct but
described a **dormant** mechanism — one that fires on a small minority of bars and leaves
the filter behaving linearly the rest of the time.

### 3.2 A second prediction, registered mid-analysis, was confirmed

After the FX result and **before** running BTC, the following was registered: if the
dormancy explanation is right, BTC (more outliers) should show *lower* |ρ| than FX,
predicted 0.60–0.75.

**Actual BTC: 0.682.** Confirmed. This supports the diagnosis: the median stage does
decorrelate, it simply does not fire often enough to matter.

---

## 4. Generalisable lesson for future C2 selection

> **Any candidate that reduces to a linear band-pass of price will correlate strongly
> with MESA Stochastic, because that is what MESA Stochastic is.**

Overlapping passbands dominate. Decorrelation must come from a mechanism that operates
**on most bars**, not a gate that activates on rare ones. Candidate sources of genuine
decorrelation:

- **Different input:** volume, true range, realised volatility — not close price
- **Different transform applied every bar:** rank, sign, up/down decomposition, threshold-crossing counts
- **Different question:** trend strength or regime state rather than filtered position

**Applied to Week 13's Laguerre RSI:** RSI's up/down decomposition is a non-linear
operation performed on *every* bar, not a dormant gate. On that structural ground it is
a better prospect than RMO was. This is a hypothesis, not a result — it must be measured
against the same C-3 threshold, unrevised.

---

## 5. Full criteria table — RMO

| # | Criterion | Result | Verdict |
|---|---|---|---|
| C-1 | Directional signal | Zero-crossing, unambiguous | ✅ PASS |
| C-2 | Mechanistic distinctness from C1 | Non-linear front end, no AGC — but mechanism dormant on ~99% of bars | ⚠️ PASS on theory, hollow in practice |
| C-3 | \|ρ\| with C1 ≤ 0.50 | **0.799 / 0.682** | ⛔ **FAIL — decisive** |
| C-4 | Lag | 3.366 bars ramp steady-state (predicted 3.37) | ✅ PASS |
| C-5 | Cross-asset stability | 9.33 vs 9.07 crossings/100 bars = **1.03×** (threshold 2×) | ✅ **STRONG PASS** |
| C-6 | Outlier resistance | See `RecursiveMedian_Findings.md` — mechanism active but counterproductive on clean OHLC | ⚠️ Reclassified |
| C-7 | Survives Week 11 null finding | Momentum mechanism, no cycle assumed | ✅ PASS |

**Six of seven pass. The one that fails is the one that matters**, and it was designated
decisive before any data existed.

Worth recording: **C-5 was a strong pass and was not expected to be.** Identical
parameters (LP=12, HP=30) produced a 1.03× signal-frequency ratio across daily FX and
4-hour crypto with no retuning. RMO generalises cross-asset better than anticipated. It
is simply redundant against the C1 already locked.

---

## 6. What is NOT concluded

- **RMO is not "a bad indicator."** It is redundant *against MESA Stochastic
  specifically*. Against a different C1 — one not built on a roofing filter — it might
  well pass. It is not being removed from the library.
- **Strategy 1 is unaffected.** FAMA / Fisher / Reflex remain locked and untouched.
- **This is an indicator-level decision.** No strategy-level backtest has been run. The
  correlation measured is between indicator outputs, not between trading signals with
  entry rules, position sizing and costs applied. That distinction holds throughout
  Phase 2 and is not weakened here.

---

## 7. Provenance

| Artefact | Commit | Timing |
|---|---|---|
| Criteria registered (thresholds, predictions) | `e4b1f5b` | Before implementation |
| Implementation | `d3e2a3d` | Before measurement |
| This decision record | (this commit) | After measurement |

The 0.65 threshold and the 0.40–0.65 prediction are both in `e4b1f5b`, timestamped on
GitHub before the data existed. The prediction is publicly wrong. That is the point of
registering it.
