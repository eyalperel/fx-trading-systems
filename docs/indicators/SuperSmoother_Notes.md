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

More poles = steeper rolloff = more lag. Note that steeper is not uniformly
better: a steeper filter also attenuates more in the passband, so it removes more
of the slow movement you intend to keep. The -20 dB/decade-per-pole figure above
is asymptotic and does not hold near period 2, where the two-bar input average
places a zero and attenuation is far deeper than the rule predicts (SS2 measures
-134 dB at period 2 against the -40 dB/decade the rule would imply).

### DC Gain
The c0 coefficient normalizes DC gain to 1.0 — a constant price passes through
unchanged. Critical implementation note: **use /2.0 not /4.0** in the c0 formula.
The /4.0 appearing in some Ehlers publications is a transcription error.

---

## Implementation Notes (Zorro Light-C)

### Degrees vs Radians

Zorro's `cos()` takes **RADIANS** (standard C math library). Ehlers publishes
in degrees, so every formula taken from an article must be converted.

**The unit conversion, on its own:**

    360 / Period   degrees  =  2*pi / Period   radians

That is the whole rule. It carries no design constant - it is just a change
of units, the way metres and feet both measure length.

**Design constants are separate.** SuperSmoother's sqrt(2) is a Butterworth
pole placement factor belonging to this filter, not part of the conversion.
Ehlers writes `1.414 * 180 / Period` in degrees; converted, that is
`sqrt(2.0) * PI / Period` in radians. The sqrt(2) survives the conversion
because it was there before it, not because of it.

```c
cos(sqrt(2.0) * PI / Period)      // CORRECT - radians
cos(sqrt(2.0) * 180.0 / Period)   // WRONG - 57.3x too large
```

Sanity check: with Period = 20, the correct form gives cos(0.2221). The wrong
form gives cos(14.14). If the argument is bigger than about 3, the units are
wrong.

*(Corrected 2026-08-06: prose fixed, code block left inverted. Code block
corrected 2026-08-31 during Week 14 session 1 - see GAP-1.6.)*

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
The naive published 3-pole formula is reported **unstable**. Note two
limitations of that statement as previously written here: the naive formula is
not reproduced or cited anywhere in this repo, so the claim cannot be checked
from it; and the reason originally given — "net feedback > 1.0" — is not a valid
stability test. Coefficient sum below 1.0 does not imply stability:

    y[t] = 0.1*x[t] + 2.5*y[t-1] - 1.6*y[t-2]

sums to 0.9 and diverges (reaches 124 by bar 20 on a constant input of 1).

**The correct test is pole magnitude.** The poles are the roots of the feedback
polynomial; the filter is stable if and only if every root has magnitude below
1.0. For the derivation below at Period=20 the pole magnitudes are 0.626, 0.626
and 0.443 — stable with margin. The largest magnitude also sets how long the
filter carries its own past: 0.626^20 is about 0.00009, so state contamination
from a wrong seed or from statics leaking across assets is effectively gone
within ~20 bars.

Use the stable pole-combination derivation:
```c
var a1 = exp(-PI / Period);
var b1 = 2.0 * a1 * cos(sqrt(3.0) * PI / Period);   // radians - see Degrees vs Radians above
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
2. **3-pole is correct, but its advantage is narrow.** The apparent
   over-responsiveness is explained by a shifted cutoff: SS3's -3 dB point sits at
   roughly 1.57x its Period parameter, where SS2's sits at 1.0x. Compared at
   matched -3 dB placement (SS2 Period=20 vs SS3 Period=12.8, both cornering at
   ~20 bars), SS3 outperforms SS2 only at periods of roughly 3-8 bars. Above that
   it is worse: it passes more in the 10-14 bar band, attenuates 30-50 bar moves
   by a further 7-9 percentage points, and costs 5.17 bars of lag against SS2's
   4.04. The earlier claim that SS3 "beats SS2 at all frequencies" came from
   treating more attenuation as better at every period, including in the passband
   where attenuation is signal loss. See Week14_Session1_Handoff GAP-1.9.
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

**SS3 Period is not comparable to SS2 Period.** SS2's -3 dB point falls at
approximately 1.0x its Period parameter; SS3's falls at approximately 1.57x. So
SS3(20) corners near 31 bars, not 20, and is a substantially heavier filter than
SS2(20). To match SS2(20) use SS3 at about Period=13. The SS3 column above lists
the same 14-20 range as SS2 and is therefore misleading as written; it is
retained pending the SS3 retention decision (Week14_Session1_Handoff GAP-1.13).

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