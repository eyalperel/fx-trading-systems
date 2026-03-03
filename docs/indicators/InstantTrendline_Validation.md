## Crypto Results — BTC/USD H4 (2020-2024)

| Metric | Adaptive | Fixed (DC=20) | EMA20 |
|---|---|---|---|
| Lag (bars) | 0 | 0 | 0 |
| Correlation | 0.9966 | 0.9970 | 0.9969 |
| SNR | 12.1691 | 12.9043 | 10.9017 |
| SNR improvement vs SMA | 1.1163x | 1.1837x | baseline |

## Cross-Asset Comparison Summary

| Metric | EUR/USD D1 | BTC/USD H4 | Interpretation |
|---|---|---|---|
| Adaptive lag | 0 bars | 0 bars | Consistent |
| Fixed lag | 0 bars | 0 bars | Consistent |
| Adaptive SNR | 4.5665 | 12.1691 | BTC stronger trends |
| Fixed SNR | 4.7279 | 12.9043 | Fixed better on both |
| Fixed vs Adaptive SNR gap | 3.5% | 6.0% | Gap widens on crypto |

## Final Conclusions

1. Fixed version outperforms Adaptive on both assets for noise reduction
2. DominantCycle instability costs more than adaptive benefit at these timeframes
3. Both versions pass validation — Fixed version recommended for production use
4. Same period (DC=20) works well on both EUR/USD D1 and BTC/USD H4
5. Crypto shows higher absolute SNR due to stronger sustained trends

## Updated NNFX Role
- **Recommended version:** Fixed (DC=20)
- **Role:** Baseline candidate for both FX and crypto strategies
- **Status:** ✅ PASS — approved for library (both assets)