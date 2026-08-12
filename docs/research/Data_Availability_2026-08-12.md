# Development Set — Data Availability

**Date:** 2026-08-12, Week 13 Day 2

| Instrument | Period | Span | Bars | Source |
|---|---|---|---|---|
| EUR/USD | D1 | 2015-01 → 2024-12 | 2,596 | Zorro M1, synthesized |
| BTC/USD | H4 | 2020-01 → 2024-12 | 7,534 | Kaggle CSV → T6 |
| EUR/JPY | D1 | 2020-09 → 2024-12 | 1,120 | Darwinex MT4, native D1 |
| AUD/USD | D1 | 2020-09 → 2024-12 | 1,120 | Darwinex MT4, native D1 |

Files are `EURJPY.t6` / `AUDUSD.t6` — **no year suffix**. D1 mode writes one
continuous file; M1 mode writes `NAME_YYYY.t6`. 2020-09-09 is the Darwinex feed's
depth limit, not a setting. Stooq as an alternative source is blocked ("Access
denied"); Dukascopy or HistData are the options if deeper history is needed.

## Three constraints on interpretation

1. **Resolution mismatch.** EUR/USD D1 is synthesized from M1. The other two are
   native daily bars closing at broker server time. "The same day" differs.

2. **Shared window.** Three of four instruments span 2020-09 → 2024-12 and absorb
   the same macro shocks. Closer to one regime tested three times than to four
   independent tests — which matters for Phase 2.5.

3. **EUR/JPY is one trend.** 124.8 → 183.7, near-monotonic, +47%. A trend system
   will look strong on it and the window holds little counterexample.

**WFO consequence:** ~1,120 D1 bars gives ~90-170 trades; split 3x3, each
out-of-sample segment holds ~15-25. Sharpe on 20 trades has a very wide interval.

## Asset list edit — outside version control

`C:/zorro/History/AssetsDarwinex.csv` had no EUR/JPY row. Added:

    EUR/JPY,183.685,0.01,0,0,0.01,0.06273,0,200,1000,0.5,EURJPY

- Broker symbol `EURJPY` unslashed (MT4 Market Watch); Zorro name slashed per file convention
- PIP = 0.01 — EUR/JPY quotes to three decimals
- PIPCost = (0.01 x 1000) / 159.403, USD account, LotAmount 1000
- Spread 0.01 is a working estimate, not the off-hours quote seen at edit time
- **Rollover 0/0 deliberately.** Current swaps are 2026 rates; across 2020-2024 the
  EUR/JPY carry inverted. A fixed swap would be a directional error, so backtests
  are **gross of carry**. Time-varying swaps deferred.

The shipped file is EUR-denominated (AUD/USD and EUR/USD both carry PIPCost
0.088873 = 0.10 / 1.12525), so those values are wrong for a USD account. Not
corrected — affects P&L, not downloads.

Backed up to `~/wk13_baseline/AssetsDarwinex.csv.bak`. Standing open item.

## Unchanged

Week 13 measurements remain two-asset — EUR/USD D1 and BTC/USD H4. EUR/JPY and
AUD/USD are available but **not to be measured on** until Phase 2.5 pass conditions
are written.
