# SuperSmoother Family — Implementation Notes
**Week:** 5 (implementation) — reviewed Week 14
**Articles:** Moving Averages and Smoothing Filters (Ehlers TASC) + The Ultimate Smoother (Ehlers TASC)
**Last Updated:** 2026-09-10 (Week 14 Session 1, part 3)

> **This file has no single family status.** Status is per indicator and per
> claim, because the evidence differs between them. See the table below.

---

## How to Read "Validated" in This File

The Week 5 validation used an SNR metric that could not have failed. It is
defined as `var(indicator) / var(price - indicator)` — the reference is the
candidate's own output, so a filter that smooths less scores higher, and a filter
that does nothing scores infinity. See `docs/Week14_Session1_Handoff.md` §4.1.

The Week 5 *implementations* are correct. The *evidence originally offered for
them* was not. SS2 and SS3 have since been checked by frequency response and by
ramp lag, which is why they are retained as validated here. Everything in this
file sourced from the Week 5 SNR metric is marked as superseded at the point
where the numbers appear.

The Week 5 validation is also **not reproducible from a fresh clone**: the
notebook reads three CSVs from `C:/Zorro/Data/`, none of them tracked
(GAP-1.10). Superseded by decision **D-14.1** (Week 14 Session 1 part 3), which
splits correctness testing onto synthetic inputs and behaviour testing onto
small committed data slices.

---

## Indicators in This Family

| Indicator | File | Status | Evidence |
|---|---|---|---|
| SuperSmoother 2-pole | `indicators/ehlers/SuperSmoother2Pole.c` | **Validated** | Frequency response (notebook cells 11-12, independently reproduced); ramp lag 4.04 bars (`Test_USLag.c`) |
| SuperSmoother 3-pole | `indicators/ehlers/SuperSmoother3Pole.c` | **Validated, with a narrower advantage than originally claimed** | Frequency response; ramp lag 5.17 bars. See Key Finding 2 |
| Ultimate Smoother (published) | `indicators/ehlers/UltimateSmootherE.c` | **Ramp lag verified 0.0000 bars — exact on straight lines only** | `Test_USLag.c`; verified against independent scipy computation to 4 dp. Lag on curves is **unmeasured** (GAP-1.16) |
| Ultimate Smoother (Week 5) | `indicators/ehlers/UltimateSmoother_W5_Superseded.c` | **SUPERSEDED — does not implement its cited article** | Ramp lag 3.87 bars vs SS2's 4.04, i.e. removes 4.1% of the lag. See Key Finding 5 |

---

## What Problem These Solve

Every moving average faces the smoothing vs lag tradeoff:
- Smooth more → more lag
- Less lag → more noise

SuperSmoother is Ehlers' DSP-based answer: a **2-pole Butterworth IIR low-pass filter**
that achieves better noise rejection than SMA/EMA for the same lag budget.
`UltimateSmootherE.c` takes a different route to the same goal: rather than
averaging price, it computes price's fast component with a high-pass filter and
subtracts it. Smoothing by subtraction rather than by averaging.

Note that `UltimateSmoother_W5_Superseded.c` does NOT do this, despite its
original name and cited article. It adds a fraction of the residual
`Price - SuperSmoother` back to SuperSmoother — an approach that cannot separate
lag from noise, because the residual contains both summed together.

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

Note that seeding at price level is correct **for a low-pass filter**, whose
steady-state output sits at price level. It is wrong for a high-pass filter,
whose output oscillates around zero — see `HighPass_RoofingFilter_Notes.md`
and GAP-1.26.

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

## Week 5 Validation Results — SUPERSEDED

> **The numbers below are retained as a record of what was measured in Week 5.
> They are not evidence of filter quality.**
>
> The SNR column ranks filters by how little they smooth (see "How to Read
> 'Validated'" above). The `Mean |diff|` column measures how closely the output
> tracks price, which is maximised by a filter that does nothing — it is not a
> lag measurement (GAP-1.23). Neither column can distinguish a correct
> implementation from an incorrect one.
>
> These results are also not reproducible from a clone (GAP-1.10). Superseded by
> D-14.1.

### EUR/USD D1 (2015-2024)

| Indicator | SNR (dB) | vs SMA baseline | Mean \|diff\| |
|---|---|---|---|
| SMA(20) baseline | 12.23 | — | — |
| SS 2-pole | 14.18 | +1.95 dB | 0.007876 |
| SS 3-pole | 16.14 | +3.91 dB | — |
| Ultimate Smoother | 14.45 | +2.22 dB | 0.007632 |

The `Ultimate Smoother` row predates the split between `UltimateSmootherE.c` and
`UltimateSmoother_W5_Superseded.c`. It refers to the Week 5 file, now superseded.

### BTC/USD H4 (2020-2024)

| Indicator | SNR (dB) | vs SMA baseline | Smoothing% |
|---|---|---|---|
| SMA(20) baseline | 20.75 | — | — |
| SS 2-pole | 23.04 | +2.29 dB | 32.5% |
| SS 3-pole | 24.95 | +4.20 dB | 37.1% |
| Ultimate Smoother | 23.32 | +2.57 dB | 32.1% |

### Parameter Sensitivity (SS 2-pole, EUR/USD D1)

| Period | SNR (dB) | Mean \|diff\| | Week 5 recommendation |
|---|---|---|---|
| 10 | 17.53 | 0.005354 | Too responsive for D1 |
| 14 | 19.86 | 0.004070 | Sweet spot for FX D1 |
| 20 | 14.18 | 0.007876 | More smoothing, valid |
| 30 | 18.99 | 0.004624 | More lag, diminishing returns |

> **GAP-1.28 — this table is internally inconsistent and unresolved.** The SNR
> column is non-monotonic: it rises from Period 10 to 14, collapses at 20, then
> rises again at 30. A smoothing parameter should not produce a dip flanked by
> higher values on both sides. The value at Period=20 (14.18) is also *exactly*
> the SS 2-pole entry in the EUR/USD table above, which suggests a copied cell
> rather than an independently measured one.
>
> Period=20 is the value used throughout the rest of the library. Settling this
> requires re-running the Week 5 notebook, which is not currently possible from a
> clone (GAP-1.10). Open.

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

3. **~~Period=14 sweet spot: best SNR + tightest tracking for EUR/USD D1.~~
   WITHDRAWN.** Both quantities named are superseded metrics: SNR rewards the
   filter that smooths least, and "tightest tracking" is mean absolute difference
   from price, which is minimised by a filter that does nothing. The table those
   numbers came from is additionally non-monotonic and unresolved (GAP-1.28).
   **No period recommendation for SS2 is currently evidence-backed.**

4. **Cross-asset consistency — restated, narrower than originally claimed.**
   What was written was that the same Period works on both FX D1 and crypto H4
   without retuning, on the basis of similar smoothing ratios (29-37%). Two
   limits on that: (a) the ratios come from the superseded SNR/smoothing metrics,
   so they show the filters behave similarly under a measure that cannot fail;
   (b) it holds for SS2 only. `Period` does not mean the same thing for SS2 and
   SS3 (Finding 2), so a single cross-asset Period statement cannot cover both.
   **Unresolved pending a measurement that can fail.**

5. **Ultimate Smoother — the Week 5 claim was wrong, and so was the method.**
   Mean absolute difference does not measure lag; it measures how closely the
   output tracks price, which a filter that does nothing achieves perfectly.
   Measured properly on a synthetic ramp (`Test_USLag.c`, Period=20):

   | filter | ramp lag |
   |---|---|
   | `UltimateSmootherE.c` (published) | 0.0000 bars |
   | `UltimateSmoother_W5_Superseded.c` (Week 5) | 3.8725 bars |
   | `SuperSmoother2Pole.c` | 4.0387 bars |

   The Week 5 file removes 4.1% of SuperSmoother's lag. Week 5 recorded it as
   VALIDATED and near-zero-lag. Found in Week 13
   (`UltimateSmoother_Lag_2026-08-12.md`); this file was not updated at the time.

   **These are lags on a synthetic ramp — a perfectly straight line — and
   nothing else has been measured.** The published filter is
   `Price - HighPass(Price)`, and the high-pass numerator is proportional to
   (1, -2, 1), which is a discrete second derivative. The second derivative of a
   straight line is exactly zero, so the high-pass outputs nothing on a ramp and
   US = Price exactly. That is an algebraic identity, not a tuning result, and it
   holds at every Period.

   It also holds ONLY for straight lines. Real price is not a straight line; the
   moment it bends, the second derivative is non-zero, the high-pass produces
   output, and the filter subtracts something real. **Whether `UltimateSmootherE`
   has low lag on a curve, a turn, or a cycle is a separate question that this
   measurement does not answer and that nothing in this repo currently answers.**
   (GAP-1.16.)

   Week 14 session 1 part 3 established the mechanism on the subtracted
   high-pass directly: its feedback polynomial is a perfect square, so it is
   critically damped — it never changes sign. It is not monotonic, though: the
   response grows for ~11 bars before decaying, peaking ~4.3x the initial kick,
   so a single bend disturbs the output for ~60 bars at the 1% level
   (HPPeriod=48). By
   superposition the output at any bar is the accumulated sum of every past
   bend. See `HighPass_RoofingFilter_Notes.md`.

---

## Parameter Recommendations

| Asset | Timeframe | SS2 Period | SS3 Period | US Period |
|---|---|---|---|---|
| EUR/USD | D1 | 14-20 | 14-20 | 14-20 |
| BTC/USD | H4 | 14-20 | 14-20 | 14-20 |

Note: Same parameters work across both asset classes.
Shorter periods (10-14) for more responsiveness.
Longer periods (20-30) for more smoothing.

**The periods in this table were selected using the Week 5 SNR metric**, which
ranks filters by how little they smooth (Week14_Session1_Handoff section 4.1).
They are not evidence-backed recommendations and should be treated as untested
defaults until re-derived. The `US Period` column additionally predates the split
between `UltimateSmootherE.c` and `UltimateSmoother_W5_Superseded.c` and does not
say which filter it refers to.

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

The `Ultimate Smoother` row refers to `UltimateSmootherE.c`. Its suitability as a
lag-critical baseline rests on the 0.0000-bar ramp result, which holds only on
straight-line input (GAP-1.16). Treat the role assignment as provisional.

---

## Cross-Asset Notes

- FX cycles are more stable; crypto cycles are more volatile
- Both asset classes respond identically to the same Period parameter
- BTC SNR values are higher overall due to stronger trending (2020-2024 bull run)
- No parameter adjustment needed when moving between FX and crypto

> **All four points above derive from the superseded Week 5 SNR and smoothing
> metrics** and inherit their limits — see Key Finding 4. The third point is an
> interpretation of SNR values, not a measurement of trending, and the metric
> does not measure trend strength. Retained as the Week 5 record; not currently
> evidence-backed.

---

## Changelog

| date | commit | change |
|---|---|---|
| 2026-08-06 | — | Degrees/radians prose corrected; code block left inverted |
| 2026-08-31 | 12a6c35 | Degrees/radians code block corrected; unit conversion separated from the Butterworth sqrt(2); argument-magnitude sanity check added (GAP-1.6) |
| 2026-08-31 | 191404b | 3-pole coefficient line corrected to PI (GAP-1.11) |
| 2026-08-31 | b93df97 | SS3 "beats SS2 at all frequencies" claim corrected (GAP-1.9) |
| 2026-08-31 | 758aa4b | Week 13's UltimateSmoother finding propagated into this file (GAP-1.15) |
| 2026-09-10 | *this commit* | Family status replaced with per-indicator status and named evidence; validation caveats relocated to the tables they describe; Key Finding 3 withdrawn and Key Finding 4 narrowed; GAP-1.28 recorded; cross-asset notes caveated; changelog added |
