# Swap Costs — Open Item for Phase 2.5

**Date:** 2026-08-13, Week 13 Day 3
**Status:** Open. No decision taken.

## The gap

C-3b requires backtests "with transaction costs". The current cost model has spreads
and commissions. **It has no swaps.**

`AssetsDarwinex.csv` was edited on 2026-08-12 to add EUR/JPY with rollover set to
`0/0`, deliberately, and recorded as such: backtests are **gross of carry**.

For an NNFX D1 system this is a real gap. Positions are held for days, so swaps
accrue on every trade. Swaps are also **asymmetric** — long and short do not pay the
same — so a system that happens to trade mostly one direction is systematically
mispriced, not just uniformly optimistic.

## Why a constant is wrong

Current swap rates are 2026 rates. The study window is 2020–2024, across which the
EUR/JPY carry inverted: the ECB moved from negative rates to a hiking cycle while
the BoJ held near zero. A single fixed swap applied across that window is a
**directional** error, not a rounding error.

## Options

**A — Zero, documented.** Current position. Results stated as gross of carry.
Understates costs; at least it is honest and unambiguous.

**B — A conservative constant.** Puts some cost on overnight holds. Wrong
period-by-period and wrong differently per pair, but closer than zero.

**C — Time-varying from rate differentials.** Correct. Requires historical policy
rates per currency plus a model of the broker markup on top. Real work.

## An idea raised, and the problem with testing it

**The idea:** if a pair's carry is strongly positive one way and negative the other,
permit trades only on the positive-carry side.

**Confound, and it is serious.** Over 2020–2024 EUR rates rose while JPY stayed near
zero, so long EUR/JPY paid positive carry — *and* EUR/JPY rose 47%. Carry and trend
pointed the same way for the whole window. A carry-direction rule tested on that
data would look excellent, and nothing in the result would distinguish "carry is
informative" from "carry happened to align with the trend".

`Data_Availability_2026-08-12.md` already flags EUR/JPY over this window as a single
near-monotonic trend with little counterexample.

**Second problem: carry trades have a characteristic failure mode.** They pay
steadily for years and then unwind violently. A rule fitted to the paying years
would be maximally exposed at the moment it breaks. Testing it honestly needs a
window containing at least one unwind.

**Third: it departs from NNFX**, which is direction-agnostic by design. Not a reason
to reject it — but it is a framework change, not a parameter choice, and should be
recorded as one.

## Not decided

Which option, and whether the carry-direction rule is worth pursuing at all. Both
belong with Phase 2.5 cost modelling, before C-3b is run — not after.
