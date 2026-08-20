# C2 Selection Criteria — Review and Explanation

**Date:** 2026-08-13, Week 13 Day 3
**Purpose:** A worked walkthrough of the C2 criteria, written while preparing to
evaluate Laguerre RSI for Strategy 2's open C2 slot.

> **This document explains. It does not govern.**
> `C2_Selection_Criteria_PreRegistered.md` is the binding, pre-registered document.
> Where the two disagree, that one wins. This file exists so the criteria are
> understood, not to restate them with authority.

---

## What can be decided this week

C-3 was amended in Week 12 into two parts:

- **C-3a** — correlation with C1. A **warning**, not a verdict.
- **C-3b** — does adding C2 make the strategy measurably better? **This decides.**

C-3b requires a working backtest. None exists — no walk-forward has been run, that
is Week 15.

**So Laguerre RSI cannot be locked as C2 this week.** The most it can be is a
shortlisted candidate that passed the screens. That is the documented structural
finding from Week 12: C2 selection cannot be completed at indicator level. Phase 2
shortlists; Phase 2.5/3 decides.

---

## Where C2 sits in NNFX

All entry conditions must agree at once:

| component | role |
|---|---|
| Baseline | price above it → longs only; below → shorts only |
| C1 | generates the entry signal |
| **C2** | **must agree with C1** |
| Volume/volatility | must confirm |
| ATR | sets stop distance and position size |

    Baseline: price above → long allowed
    C1:       +0.4        → long
    C2:       +0.2        → long        ENTER

    Baseline: price above → long allowed
    C1:       +0.4        → long
    C2:       -0.1        → short       NO TRADE

**C2's value lives entirely in the bars where it disagrees.** A C2 that agrees 85%
of the time blocks almost nothing — computation added, no filtering gained. Worse,
it looks like two independent indicators agreed when really the same question was
asked twice.

Strategy 2 is FRAMA baseline + MESA Stochastic C1 + C2 open. So every comparison
below is against **MESA Stochastic**, not Fisher (which is Strategy 1's C1).

---

## C-1 — Directional signal

Must produce an unambiguous up/down state via zero crossing or fixed threshold.

    bar:     1      2      3      4      5
    value:  -0.4   -0.1   +0.3   +0.8   +0.5
    state:  DOWN   DOWN    UP     UP     UP

Every bar gets a clear answer. Compare with what fails — the Alpha-Beta Filter,
eliminated on C-1 in Week 12:

    bar:     1       2       3       4
    value:  1.2035  1.2041  1.2038  1.2044
    state:   ?       ?       ?       ?

Those are price levels. No zero to cross, no natural threshold. A confirmation
indicator that cannot answer "agree or not" without extra machinery is not one.

**Fail → eliminated.** Definitional.

---

## C-2 — Mechanistic distinctness from C1

Must differ from C1 in **filter class**, not merely in parameters.

Same mechanism, different speed — not two confirmations:

    Indicator A:  EMA period 10
    Indicator B:  EMA period 30

Genuinely different mechanisms:

    Indicator A:  averages a window   (linear)
    Indicator B:  median of a window  (non-linear)

### Why the median is non-linear

Linear means two things hold. Scaling:

    2, 4, 9   →  average 5,  median 4
    4, 8, 18  →  average 10, median 8      both doubled

Addition — and here the median fails:

    Set A: 2, 4, 9   →  average 5, median 4
    Set B: 7, 1, 1   →  average 3, median 1
    A+B:   9, 5, 10  →  average 8, median 9

    A's average + B's average = 8   matches
    A's median  + B's median  = 5   does NOT match 9

An average applies fixed weights to every element. A median **sorts, then selects**
— which element it picks depends on the values themselves. That is why a linear
filter has a frequency response you can compute once, and a median does not.

Practical consequence: `RecursiveMedian.c` could not use the `series()` IIR pattern
(GOTCHAS 3.4) and needed an explicit sorting network — where a wrong comparator
order silently corrupted ~10% of bars (GOTCHAS 9).

### C-2 is a weak test

RMO **passed** C-2 on theory. Then measurement showed:

    corr(Recursive Median, plain EMA) = 0.9965 on EUR/USD

The median only behaves differently when an outlier is present. The rest of the
time it is an ordinary linear filter. Distinct in principle, near-identical in
practice. C-2 catches obvious duplicates and nothing subtler.

**Fail → eliminated.**

---

## C-3a — Correlation screen (a warning)

How closely the candidate's output tracks C1's output, bar by bar, both assets.

    MESA Stoch:   -0.5   -0.2   +0.3   +0.6   +0.1
    Candidate:    -0.4   -0.3   +0.2   +0.7   +0.2      moves together, ~0.95

    MESA Stoch:   -0.5   -0.2   +0.3   +0.6   +0.1
    Candidate:    +0.2   -0.6   +0.4   -0.1   +0.5      unrelated, ~0

| \|rho\| | Verdict |
|---|---|
| <= 0.50 | Clean |
| 0.50 – 0.65 | Flagged — investigate and document why |
| > 0.65 | Flagged strongly — C-3b must pass decisively |

**Sign agreement is the more readable number.** RMO measured rho = 0.799 with 84.7%
sign agreement: it would vote with C1 on five bars in six.

### Why C-3a was demoted from decisive to warning

74% agreement leaves 26% of bars where C2 disagrees. Whether C2 earns its slot
depends on whether *those* bars are informative — which correlation does not
measure.

Two candidates, both 74%:

- **A** — disagreements scattered at random. Blocks winners and losers alike. Net
  effect over many trades: nothing.
- **B** — disagreements cluster on bad trades. Blocks losers, passes winners.

Identical correlation. A is worthless, B is valuable. Correlation measures *how
often* they differ, never *which bars*.

---

## C-3b — Conditional information gain (DECISIVE)

Run the strategy twice:

    Version 1:  Baseline + C1        →  risk-adjusted return
    Version 2:  Baseline + C1 + C2   →  risk-adjusted return

Requirements: out of sample, with costs, and better on **every** development asset.
Improvement on one and degradation on another is a fail — that is parameter luck.

### Why costs must be included

    Version 1 — C1 only, 100 trades
      gross profit           $10,000
      costs 100 x $20        -$2,000
      net                     $8,000

    Version 2 — C1+C2, C2 blocks 30 trades, 70 remain
      gross profit            $7,600     (removed some winners too)
      costs 70 x $20         -$1,400
      net                     $6,200     Version 1 wins

    Version 2 again, C2 blocking genuinely bad trades
      gross profit            $9,000
      costs 70 x $20         -$1,400
      net                     $7,600     still loses to $8,000

Fewer trades means lower costs, so C2 starts with a $600 head start from trade-count
reduction alone. **A C2 blocking 30 trades at random collects the same $600.**
Without costs in the comparison, filtering skill cannot be told apart from trading
less. See the separate note on swaps — the cost model is currently incomplete.

---

## C-4 — Lag (see Amendment 3)

Candidate's lag must not exceed C1's lag + 2.0 bars at comparable smoothing.

Why lag matters for a C2 specifically — it must agree or disagree **on the bar C1
fires**:

    bar:        1      2      3      4      5
    C1:        -0.2   +0.4   +0.6   +0.5   +0.3    turns up at bar 2
    C2 (fast): -0.1   +0.2   +0.5   +0.4   +0.2    turns up at bar 2
    C2 (slow): -0.4   -0.3   -0.1   +0.2   +0.4    turns up at bar 4

The slow C2 blocks the bar-2 entry not because it disagrees but because it has not
caught up. It delays rather than filters.

### Three problems found while reviewing C-4 — all now Amendment 3

**1. It referenced the wrong strategy.** C-4 as written compares against Fisher
Transform, which is Strategy 1's C1. This document governs Strategy 2, whose C1 is
MESA Stochastic. Amendment 3 revises it to reference the C1 of the strategy whose
slot is being filled.

**2. Lag against price does not answer the question.** Two candidates can share a
lag figure and mean opposite things:

    C1:  -0.2   +0.4   +0.6   +0.5
    X:   -0.4   -0.3   -0.1   +0.2     turns up 2 bars after C1 — delayed copy
    Y:   -0.4   -0.3   -0.5   -0.6     never turns up — measuring something else

X postpones entries without filtering. Y genuinely disagrees. Same lag-vs-price.

Amendment 3 adds **C-4b, a lag profile**: cross-correlate candidate against C1 at
shifts 0–10 and record where correlation peaks. Nothing in the filters is changed —
it is arithmetic on two exported columns, sliding one against the other:

    C1:  -0.5  -0.2  +0.3  +0.6  +0.4  -0.1  -0.4  -0.3
    C2:  -0.3  -0.4  -0.5  -0.2  +0.3  +0.6  +0.4  -0.1

    shift 0:  0.30
    shift 1:  0.61
    shift 2:  0.98   <- peak, so C2 is C1 delayed by two bars
    shift 3:  0.55

**3. "At comparable smoothing" was undefined.** Lag and smoothness trade off, so any
indicator looks fast if its smoothing is turned down:

    Period 5:   lag 1.2 bars    output wiggles a lot
    Period 40:  lag 9.5 bars    output very smooth

Method adopted (ours, not the document's): match variance reduction, then measure
lag at the matched setting.

---

## C-5 — Cross-asset stability

Identical parameters on both assets, with crossings per 100 bars differing by no
more than 2x.

    EUR/USD D1:   14 crossings / 100 bars
    BTC/USD H4:   22 crossings / 100 bars     ratio 1.6x   pass

    EUR/USD D1:    8 crossings / 100 bars
    BTC/USD H4:   35 crossings / 100 bars     ratio 4.4x   fail

### Why crossing count reveals speed

    Slow (crosses every 12):  + + + + + + + + + + + +  - - - - - - - - - - - -
    Fast (crosses every 3):   + + +  - - -  + + +  - - -  + + +  - - -  + + +

The slow one filters out short-term wiggles and only flips when something
substantial changes. The fast one flips on every small move. If Period 20 produces
the slow picture on one asset and the fast picture on the other, then "20" delivers
heavy smoothing in one place and light smoothing in the other. Same number,
different behaviour — effectively two indicators.

### Two different claims, deliberately

- **Identical parameters** is the INPUT — strict and binary. Either you retuned or
  you did not.
- **Within 2x** is the OUTPUT — how much behaviour may differ before it is a
  failure.

The room is on the results, not the settings, and it has to be: assets genuinely
differ, so demanding identical output would demand identical assets. RSIH measured
p5/p95 at -0.555/+0.517 on EUR/USD and -0.545/+0.656 on BTC — nearly the same, which
is the expected shape of a pass.

The 2x figure has no derivation in the document. For scale: the volatility regime
classifier produced Normal-state run lengths of 3.42 and 3.43 across a D1 FX pair
and an H4 crypto series, a ratio of 1.003. So 2x is generous relative to what a
well-behaved component achieves.

**Noted, not proposed as a change:** crossing count is one narrow measure. An
indicator could match on crossings while differing in amplitude or in how long it
holds each state.

**Fail → conditional.** A per-asset parameter set is permitted but counts against.

---

## C-6 — Outlier resistance (weak evidence)

March 2020 BTC crash. Signal state must not persist more than 5 bars beyond what a
plain EMA of equivalent smoothing produces.

    Plain EMA:   negative for 12 bars
    Candidate:   negative for 15 bars     difference 3    pass

    Plain EMA:   negative for 12 bars
    Candidate:   negative for 31 bars     difference 19   fail

An indicator stuck in one state long after the event is still digesting a single
bar. It then **votes the same way regardless of what price is doing** — not
blocking everything (a stuck-negative C2 waves shorts through), but uninformative
for as long as it stays stuck.

**The criteria file states its own limitation:** one event is not a distribution. A
pass shows the candidate handled *that* crash, not that it handles crashes. For
Recursive Median the pass was expected by construction — a median mathematically
cannot be dragged far by one outlier — so the test could not fail for the right
reasons. It is reclassified in the file itself as an **implementation bug-detector**.

**Fail → investigate the implementation before calling it a design failure.**

---

## Summary

| | Testable this week | Decides? |
|---|---|---|
| C-1 | Yes, from theory | Eliminates |
| C-2 | Yes, from theory | Eliminates |
| C-3a | Yes, measured | Warning only |
| C-3b | **No — needs a backtest** | **DECISIVE** |
| C-4 / C-4b | Yes, measured | Conditional |
| C-5 | Yes, measured | Conditional |
| C-6 | Yes, measured | Weak evidence |

C-7 was withdrawn via Amendment 2.

**Outcome available this week: shortlist or eliminate. Not lock.**
