# SuperSmoother — Implementation Notes
**Week:** 5  
**Articles:** Moving Averages and Smoothing Filters (Ehlers TASC) + The Ultimate Smoother (Ehlers TASC)  
**Status:** VALIDATED ✅  
**Last Updated:** Week 5 Day 6

---

## Indicators in This Family

| Indicator | File | Status |
|---|---|---|
| SuperSmoother 2-pole | `indicators/ehlers/SuperSmoother2Pole.c` | ✅ Validated |
| SuperSmoother 3-pole | `indicators/ehlers/SuperSmoother3Pole.c` | ✅ Validated |
| Ultimate Smoother | `indicators/ehlers/UltimateSmoother.c` | ✅ Validated |

---

## What Problem These Solve

Every moving average faces the smoothing vs lag tradeoff:
- Smooth more → more lag
- Less lag → more noise

SuperSmoother is Ehlers' DSP-based answer: a **2-pole Butterworth IIR low-pass filter**
that achieves better noise rejection than SMA/EMA for the same lag budget.
The Ultimate Smoother extends this by correcting for the filter's own lag.

---

## Key Mathematical Concepts

### IIR vs FIR
SuperSmoother is an **IIR (Infinite Impulse Response)** filter — it feeds previous
output values back into the current output. This allows sharp frequency cutoff
with very few coefficients, unlike FIR filters (e.g. SMA) which need long windows.

### Butterworth Design
The specific coefficients use the **Butterworth design** — maximally flat passband,
no ripple, monotonic rolloff. The √2 constant in the 2-pole formula and √3 in the
3-pole formula are the Butterworth design constants for each order.

### Poles
Each pole adds -20 dB/decade of rolloff steepness:
- 2-pole: -40 dB/decade rolloff
- 3-pole: -60 dB/decade rolloff

More poles = steeper noise rejection = slightly more lag.

### DC Gain
The c0 coefficient normalizes DC gain to 1.0 — a constant price passes through
unchanged. Critical implementation note: **use /2.0 not /4.0** in the c0 formula.
The /4.0 appearing in some Ehlers publications is a transcription error.

---

## Implementation Notes (Zorro Light-C)

### Degrees vs Radians
Zorro's cos() uses **degrees**, not radians. Convert:
```
cos(sqrt(2.0) * 180.0 / Period)   // CORRECT
cos(sqrt(2.0) * PI / Period)      // WRONG
```

### Series Sizing
- 2-pole: `series(Price[0], 3)` — needs 3 elements
- 3-pole: `series(Price[0], 4)` — needs 4 elements
- Ultimate Smoother: two series, each `series(Price[0], 3)`

### Warmup Handling
Use Zorro's `Init` flag to return raw price during warmup:
```c
if(Init) { Filt[0] = Price[0]; return Filt[0]; }
```
This ensures feedback terms contain real price values by live period start.

### 3-Pole Coefficients
The naive published 3-pole formula is **unstable** (net feedback > 1.0).
Use the stable pole-combination derivation:
```c
var a1 = exp(-PI / Period);
var b1 = 2.0 * a1 * cos(sqrt(3.0) * 180.0 / Period);
var c1 = b1 + a1;
var c2 = -(b1 * a1 + a1 * a1);
var c3 = a1 * a1 * a1;
var c0 = (1.0 - c1 - c2 - c3) / 2.0;
```

---

## Validation Results

### EUR/USD D1 (2015-2024)

| Indicator | SNR (dB) | vs SMA baseline | Mean \|diff\| |
|---|---|---|---|
| SMA(20) baseline | 12.23 | — | — |
| SS 2-pole | 14.18 | +1.95 dB | 0.007876 |
| SS 3-pole | 16.14 | +3.91 dB | — |
| Ultimate Smoother | 14.45 | +2.22 dB | 0.007632 |

### BTC/USD H4 (2020-2024)

| Indicator | SNR (dB) | vs SMA baseline | Smoothing% |
|---|---|---|---|
| SMA(20) baseline | 20.75 | — | — |
| SS 2-pole | 23.04 | +2.29 dB | 32.5% |
| SS 3-pole | 24.95 | +4.20 dB | 37.1% |
| Ultimate Smoother | 23.32 | +2.57 dB | 32.1% |

### Parameter Sensitivity (SS 2-pole, EUR/USD D1)

| Period | SNR (dB) | Mean \|diff\| | Recommendation |
|---|---|---|---|
| 10 | 17.53 | 0.005354 | Too responsive for D1 |
| 14 | 19.86 | 0.004070 | ✅ Sweet spot for FX D1 |
| 20 | 14.18 | 0.007876 | ✅ More smoothing, valid |
| 30 | 18.99 | 0.004624 | More lag, diminishing returns |

---

## Key Findings

1. **DC gain fix:** c0 must use /2.0 not /4.0 — published formula has transcription error
2. **3-pole is correct:** Apparent over-responsiveness explained by shifted effective
   cutoff period — frequency response confirms SS3 beats SS2 at all frequencies
3. **Period=14 sweet spot:** Best SNR + tightest tracking for EUR/USD D1
4. **Cross-asset consistency:** Same Period=20 works on both FX D1 and Crypto H4
   without retuning — smoothing ratios nearly identical (29-37%)
5. **Ultimate Smoother:** Best lag+SNR tradeoff — zero-lag claim credible visually
   and confirmed by mean absolute difference metric

---

## Parameter Recommendations

| Asset | Timeframe | SS2 Period | SS3 Period | US Period |
|---|---|---|---|---|
| EUR/USD | D1 | 14-20 | 14-20 | 14-20 |
| BTC/USD | H4 | 14-20 | 14-20 | 14-20 |

Note: Same parameters work across both asset classes.
Shorter periods (10-14) for more responsiveness.
Longer periods (20-30) for more smoothing.

---

## NNFX Role

| Indicator | Primary Role | Secondary Role |
|---|---|---|
| SS 2-pole | C1 input preprocessing | Baseline smoothing layer |
| SS 3-pole | Max smoothing contexts | Pre-filter for oscillators |
| Ultimate Smoother | Trend following (lag-critical) | Baseline candidate |

SS2 and SS3 are the **foundation** — they appear inside MAMA, Cyber Cycle,
Roofing Filter, and most other Ehlers indicators in the Week 6-14 plan.
Understanding them deeply was the correct starting point for Phase 2.

---

## Cross-Asset Notes

- FX cycles are more stable; crypto cycles are more volatile
- Both asset classes respond identically to the same Period parameter
- BTC SNR values are higher overall due to stronger trending (2020-2024 bull run)
- No parameter adjustment needed when moving between FX and crypto