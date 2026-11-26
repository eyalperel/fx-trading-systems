# C1S1 read 1 — C1-only screen of the verified library on EUR/USD D1

Criteria: `docs/preregistration/C1S1_C1Screen_EURUSD_Criteria.md`. Null rows: NULL1 `201a14f904d5e559fe0163bb73cd56ba71e6d1d3b2d68dba4a46686e8a78ad40`, C1S1 `788e5fc4fd204c40ac8153109d31c003b962336c00e75bb4219dc8d2eaf405a6`. K = 6, 1,000 offsets, x2.

**Max-statistic null (best of six per offset):** median +0.0140, 95th percentile **+0.0739** (the bar).

| Id | Signals | Mean signal-R | t | Total R | Best year (R) | Total w/o best year | Own-null pct | Max-null pct | Pass | Why not |
|---|---|---|---|---|---|---|---|---|---|---|
| FSH | 914 | -0.0129 | -0.54 | -11.75 | 2016 (+6.93) | -18.68 | 70.1% | 16.2% | no | not above max-statistic 95th; mean <= 0; total without best year <= 0 |
| MSS | 505 | -0.0224 | -0.59 | -11.31 | 2017 (+8.10) | -19.41 | 55.7% | 9.4% | no | not above max-statistic 95th; mean <= 0; total without best year <= 0 |
| MAF | 205 | +0.1012 | +1.48 | +20.74 | 2010 (+6.27) | +14.47 | 98.8% | 98.6% | **PASS** |  |
| RFX | 433 | -0.0129 | -0.31 | -5.60 | 2015 (+7.33) | -12.93 | 65.0% | 16.2% | no | not above max-statistic 95th; mean <= 0; total without best year <= 0 |
| ROF | 442 | -0.0749 | -1.83 | -33.12 | 2015 (+6.22) | -39.34 | 11.2% | 0.0% | no | not above max-statistic 95th; mean <= 0; total without best year <= 0 |
| LRS | 463 | -0.0465 | -1.14 | -21.51 | 2017 (+2.97) | -24.48 | 30.0% | 1.4% | no | not above max-statistic 95th; mean <= 0; total without best year <= 0 |

**Survivors:** MAF.

Limitations (c): circular shifts are correlated draws; engine vs Zorro differ on a few halves (V1); one asset, one feed; C1-only mode is our reading of VP's C1 test (NULL1 C1).
