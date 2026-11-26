# C1S2 read 1 — MAMA vs FAMA (C1-only) on AUD/USD and EUR/JPY

Criteria: `docs/preregistration/C1S2_MAF_OtherPairs_Criteria.md`. Null rows sha256 `c9160b2edb47ee3bb3614d8c7994a585d56492e704108eec70c1b51a66594a12`.

| Pair | Signals | Mean signal-R x2 | t | Total R | Best year (R) | Total w/o best year | Own-null 95th | Own-null pct | Pass | Why not | x2 no rollover: mean | x0: mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AUDUSD | 231 | -0.0638 | -1.06 | -14.74 | 2008 (+5.65) | -20.40 | +0.0655 | 25.2% | no | not above own-null 95th; mean <= 0; total without best year <= 0 | -0.0614 | -0.0459 |
| EURJPY (0 halves open across the 2017-12-12..2018-01-01 hole) | 168 | -0.0640 | -0.84 | -10.75 | 2024 (+3.16) | -13.91 | +0.0602 | 33.7% | no | not above own-null 95th; mean <= 0; total without best year <= 0 | -0.0542 | -0.0237 |

**MAF passes C1S2 (both pairs):** NO.

Limitations (c): circular shifts are correlated draws; the engine is checked against Zorro on EUR/USD trades (V1) and on these pairs' bars and indicators only (VB1 / VW1); rollover is a 2025-07-28 snapshot; one feed per pair.
