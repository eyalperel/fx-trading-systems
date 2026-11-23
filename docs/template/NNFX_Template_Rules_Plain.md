---
title: "NNFX Template — The Rules in Plain Words"
subtitle: "Variant 0, as decided 2026-11-22"
---

**What this is.** A plain-language summary of the NNFX template's rules,
assuming every slot (baseline, C1, C2, volume, exit) has an indicator in it.
The full record, with sources and reasoning, is `NNFX_TEMPLATE_DECISIONS.md`
(decisions T1–T11, commit `e1c0cb8`). Where the two differ, the decisions file wins.
The tags in square brackets point to the decision behind each rule.

# When

Once a day, on the daily chart, after the candle has closed. Nothing happens
inside a candle except stops and take-profits being hit. [T4, T5]

# Every day, in this order

## 1. Manage open trades first

- **Stop:** 1.5 × ATR from the entry price.
- **First target:** half the position closes as soon as price touches
  +1 × ATR. From the next day, the other half's stop moves to the entry
  price, so it can no longer lose. [T5]
- **Trailing stop:** once a candle *closes* 2 × ATR or more in profit, the
  stop follows 1.5 × ATR behind the best close so far. It moves only on a new
  best close, and never moves back. [T5]
- **Close whatever is left** if:
    - C1 flips against the trade,
    - the exit indicator says exit, or
    - a candle closes across the baseline against you.

  You get out at the next day's open. [T1, T5]
- The volume indicator never closes a trade. [T2]

## 2. Look for a new trade (three ways in)

### A. C1 gives a new signal

Enter if, on that same candle: [T3, T6]

- price is on the right side of the baseline,
- C2 agrees,
- volume says yes,
- price is no more than 1 × ATR from the baseline.

If any one of these says no, or is undecided, there is no trade.

### B. Price closes across the baseline

Enter if C1 already points that way, C2 agrees, volume says yes, and price is
within 1 × ATR. [T10]

- If C2 or volume is not ready yet, keep checking each day. Enter when they
  agree, as long as price has not closed back across the baseline, C1 has not
  flipped, and price is still within 1 × ATR.
- *Strategy 1 only:* skip it if C1's signal is 7 or more candles old
  ("bridge too far").
- *Pullback:* if the crossing candle closed more than 1 × ATR past the
  baseline, wait exactly one candle. If price is back within 1 × ATR and
  everything agrees, enter. Otherwise forget that cross.

### C. Continuation

You exited a trade for any reason other than a baseline close, and price has
never closed back across the baseline since. If C1 gives a fresh signal in the
same direction and C2 agrees, re-enter. Volume and the 1 × ATR distance are
ignored here. [T9]

## 3. Entering

- A market order at the **next day's open**. [T4]
- The ATR from the signal candle is used for the whole trade. [T4]
- Risk is 2% of the account, split into **two halves of 1%**: one half takes
  the first target, the other half is the runner. [T8]

# Testing conventions (how we keep ourselves honest)

- If the stop and the first target were both hit inside one candle, assume
  the stop was hit first. [T5]
- Every result is shown at normal spread and at 2× spread. A result that only
  works at normal spread is rejected. [T7]
- Results are reported in **R** (profit ÷ risk). Continuation trades are
  reported separately. [T8, T9]
- Every number is a named setting. Each one is tested at a few nearby values,
  one at a time, to check the result is not a fluke of one setting. This is a
  robustness check, not a way to pick the best value. [T11]

# Not in variant 0 yet

- News rules (no current news calendar).
- Dead-market mode (optional, off).
- The one-candle rule: its source, NNFX Podcast Ep 39, still has to be found. [T6]
- The same-currency rule: needed only once several pairs run together. [T8]
