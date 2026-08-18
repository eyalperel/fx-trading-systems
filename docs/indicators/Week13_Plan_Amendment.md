# Week 13 — Plan Amendment

**Date:** 2026-08-13, Week 13 Day 3
**Governs:** `Week5-14_Indicator_Plan.md`, Week 13 section
**Type:** Additive. The plan is not rewritten; deviations are recorded here.

## Scope

The plan lists three Week 13 indicators: #24 Normalized ATR, #25 Ultimate
Channels & Bands, #26 Laguerre RSI. Week 13 as executed has four items.

**RSIH added.** The plan lists `(Yet Another) Improved RSI.pdf` in its Week 13
article set but assigns no indicator number to it — #26 is Laguerre RSI, which
comes from the book, not that article. The article was orphaned. RSIH (Ehlers,
TASC V.40:01, 2022) now occupies that slot.

**Laguerre oscillator added.** The 2025 TASC Laguerre oscillator, UltimateSmoother
-seeded, is not in the plan at all. Added as its own item, distinct from #26.

## Deviations from plan specifications

**NATR denominator.** Plan specifies `ATR / ((High+Low+Close)/3)`. Implemented as
`100 * STR / Close`. Close is the convention, so the number is comparable to any
published NATR; typical price is a defensible variant. Deliberate, not an error.

**Regime thresholds superseded by measurement.** Plan specifies absolute cuts —
low-vol FX below 0.5%, high-vol crypto above 4%. Measurement refutes this
approach: BTC/USD H4 NATR p10 = 0.94% sits above EUR/USD D1 median = 0.67%, so
the distributions barely overlap and no fixed threshold labels both assets.
Replaced with percentile rank over a 250-bar window, cut at 30/70. See commit
`3cfe801` for the measured distributions and `268d6e2` for the classifier.

## Not addressed

The plan's validation gate includes "Ultimate Bands vs Bollinger Bands: which
adapts faster?" and "update risk management module to use NormalizedATR". Neither
has been done. The Bollinger comparison is not required by P1-P4 and was not
attempted; the risk module update is downstream of Phase 3.
