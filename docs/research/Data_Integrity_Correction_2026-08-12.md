# Data Integrity Correction — 2026-08-12

**Date:** 2026-08-12, Week 13 Day 2
**Status:** Correction of record. Additive; supersedes nothing by deletion.
**Commits:** `9642f95`, `2a5eca5`, `10d91a4`, `c201161`, `08b5db6` — measured
effects and mechanisms are in those messages.

---

## 1. The Week 13 Day 2 brief stated a false premise

The brief recorded that `Laguerre.c` static variables contaminated BTC warmup,
making BTC measurements untrustworthy. The conclusion was correct; the mechanism
was not.

Laguerre is computed before the `is(LOOKBACK)` guard, so carried-over state decays
across 100 warmup bars to ~1e-21 of its initial magnitude. No Laguerre measurement
was ever affected.

The actual defect was an asset name: `Asset = "BTC/USD"` does not exist —
`AssetsFix.csv` names crypto without a slash. Zorro substituted the default asset
and wrote EUR/USD data into a BTC-named file. A separate defect, found while
verifying the first, affected FRAMA on 29 of 7,534 BTC rows.

Both development-set CSVs have been regenerated from patched code and verified
against the May 2026 baselines. Nothing downstream moved materially.

## 2. Effect on Week 13 predictions

**P1–P4 stand unamended.** No prediction references Laguerre, static state, or BTC
data integrity. Row counts match what the predictions assume: 2,596 (EUR/USD D1)
and 7,534 (BTC/USD H4).

One dependency is flagged rather than resolved. **P3 uses FRAMA** as its
conditional split variable, citing it as "Week 9, validated." That validation may
have read the corrupted BTC CSV — 7,534 genuine rows followed by 7,529 appended
EUR/USD rows. P3's requirement is structural (FRAMA shares no term with the band
width), so the prediction is not at risk, but the citation is unverified.

**Open, and a prerequisite for P3:** confirm which row ranges the Week 9 and
Week 12 notebooks actually read.

## 3. Measurement basis unchanged

Week 13 measurements remain two-asset — EUR/USD D1 and BTC/USD H4 — and must be
recorded as such. EUR/JPY has no history in `Zorro/History/`; `AUDUSD.t6` is a
44 KB stub.
