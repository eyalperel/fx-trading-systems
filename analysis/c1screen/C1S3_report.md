# C1S3 read 1 — FSH, MSS, RFX, ROF, LRS (C1-only), pooled AUD/USD + EUR/JPY

Criteria: `docs/preregistration/C1S3_FiveC1_Pooled_Criteria.md`. Null rows sha256 `e609197f389b280a1c459e469bac2c011c99990db27a2724a8e924d7a23f8567`. Pairing `analysis/c1screen/C1S3_pairing.csv`.

**Pooled max-statistic null (best of 5 per draw), x2:** median -0.0035, **95th percentile +0.0344** (the bar).

| Id | Signals (AUD / JPY) | Pooled mean x2 | t | Total R | Best year (R) | Total w/o best year | AUD/USD mean | EUR/JPY mean | Own-null median (5th / 95th) | Own-null pct | Max-null pct | Pass | Why not | x2 no roll | x0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FSH | 999 / 685 | -0.0186 | -1.04 | -31.29 | 2024 (+11.37) | -42.66 | -0.0123 | -0.0277 | -0.0277 (-0.0560 / +0.0026) | 68.6% | 22.4% | no | not above max-null 95th; pooled mean <= 0; AUDUSD mean <= 0; EURJPY mean <= 0; pooled total without best year <= 0 | -0.0150 | +0.0063 |
| MSS | 537 / 375 | -0.0423 | -1.48 | -38.60 | 2024 (+5.73) | -44.33 | -0.0486 | -0.0334 | -0.0294 (-0.0750 / +0.0144) | 32.0% | 1.4% | no | not above max-null 95th; pooled mean <= 0; AUDUSD mean <= 0; EURJPY mean <= 0; pooled total without best year <= 0 | -0.0367 | -0.0152 |
| RFX | 479 / 331 | -0.0031 | -0.10 | -2.51 | 2015 (+14.43) | -16.94 | +0.0270 | -0.0467 | -0.0285 (-0.0770 / +0.0200) | 81.3% | 51.1% | no | not above max-null 95th; pooled mean <= 0; EURJPY mean <= 0; pooled total without best year <= 0 | +0.0015 | +0.0230 |
| ROF | 431 / 320 | -0.0431 | -1.34 | -32.38 | 2015 (+14.29) | -46.67 | +0.0067 | -0.1102 | -0.0289 (-0.0805 / +0.0222) | 32.9% | 1.2% | no | not above max-null 95th; pooled mean <= 0; EURJPY mean <= 0; pooled total without best year <= 0 | -0.0380 | -0.0161 |
| LRS | 475 / 338 | -0.0463 | -1.56 | -37.65 | 2015 (+8.61) | -46.26 | -0.0419 | -0.0525 | -0.0291 (-0.0743 / +0.0170) | 24.2% | 0.7% | no | not above max-null 95th; pooled mean <= 0; AUDUSD mean <= 0; EURJPY mean <= 0; pooled total without best year <= 0 | -0.0415 | -0.0202 |

**Survivors:** 0.

Limitations (c): circular shifts are correlated draws; the engine is checked against Zorro on EUR/USD trades (V1) and on these pairs' bars and indicators only (VB1 / VW2); rollover is a 2025-07-28 snapshot; one feed per pair.
