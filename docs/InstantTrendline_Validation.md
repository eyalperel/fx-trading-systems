# InstantTrendline — Validation Notes
**Week:** 4 Day 4 | **Asset:** EUR/USD D1 | **Period tested:** 20

---

## Indicator Overview
Three-stage filter pipeline (Elliptic lowpass → Fixed 10-bar notch → Adaptive DC notch)
designed to track trend with minimal lag. Enhancement over Ehlers' original: Stage 3
uses DominantCycle measurement to adapt the notch frequency.

## Fixed vs Adaptive Comparison — EUR/USD D1 (2015-2024)

| Metric | Adaptive | Fixed (DC=20) | EMA20 |
|---|---|---|---|
| Lag (bars) | 0 | 0 | 0 |
| Correlation | 0.9749 | 0.9770 | 0.9770 |
| SNR | 4.5665 | 4.7279 | 4.0886 |
| SNR improvement vs SMA | 1.1169x | 1.1564x | baseline |

## Key Findings

**Lag:** Both versions identical at D1 timeframe. DominantCycle adaptation
provides no lag advantage on daily EUR/USD where cycles are slow and stable.

**SNR:** Fixed version is ~3.5% better at noise reduction than Adaptive.
DominantCycle's own bar-to-bar fluctuation introduces small instabilities
in Stage 3's notch angle, slightly degrading smoothness.

**Conclusion:** On EUR/USD D1, fixed period performs marginally better than
adaptive. The complexity of DominantCycle integration does not pay off at
this timeframe.

## Hypotheses for Crypto / Shorter Timeframes
- BTC/USD H4 has faster, more variable cycles — DominantCycle may adapt
  more meaningfully there
- Expected: Adaptive version shows clearer advantage on H4 crypto
- To be tested on Day 5

## NNFX Role
- Candidate: **Baseline** (smooth trendline, crossover with SmoothPrice)
- Both versions pass validation — fixed version slightly preferred for D1 FX

## Validation Verdict
- ✅ PASS (Adaptive) — approved for library
- ✅ PASS (Fixed) — approved for library
- **Recommended for D1 FX:** Fixed version (DC=20)
- **Pending:** Crypto test on Day 5