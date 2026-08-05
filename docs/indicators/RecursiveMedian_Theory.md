# Recursive Median Filter & Recursive Median Oscillator — Theory

**Indicators:** #22 (RM), #22b (RMO)
**Source:** Ehlers, J. F., "Recursive Median Filters," *Stocks & Commodities* V.36:03 (2018), pp. 8–11
**Week:** 12, Day 1 (theory)
**Status:** Theory complete — implementation pending (Day 3)
**Candidate role:** RMO → Strategy 2 C2 (open slot)

---

## 1. Why this indicator exists

Every filter in the library to this point is **linear**: the output is a weighted sum of
inputs, satisfying superposition —

```
filter(a·x + b·y) = a·filter(x) + b·filter(y)
```

SuperSmoother, EMA, HighPass, FAMA, FRAMA, Reflex, MESA Stochastic all qualify. That
property is what permits frequency-domain analysis, a transfer function, and an
analytically derived lag.

The Recursive Median Filter deliberately breaks linearity. The break is the point.

### 1.1 Linear filters cannot resist outliers — structurally

Consider a 5-bar SMA on clean data:

```
Input:   1.0850  1.0852  1.0851  1.0853  1.0852
SMA(5) = 1.08516
```

Inject one corrupted bar (fat-finger print, thin-liquidity spike, exchange glitch):

```
Input:   1.0850  1.0852  1.2000  1.0853  1.0852
SMA(5) = 1.07614          ← 98 pips of corruption
```

The spike's contribution equals **its weight times its magnitude**. In a 5-bar SMA that
weight is 1/5. Scale the spike 10× and the corruption scales 10×. There is no bound.

This is not a tuning problem. Any linear filter assigning non-zero weight to the
corrupted bar propagates a proportional share of the error. Lengthening the window
dilutes it (1/20 instead of 1/5) at the cost of lag, but never eliminates it.

> **Outlier sensitivity cannot be fixed within a linear filter, because linearity *is*
> the sensitivity.** Superposition guarantees proportional pass-through.

Same data, median:

```
Input:    1.0850  1.0852  1.2000  1.0853  1.0852
Sorted:   1.0850  1.0852  1.0852  1.0853  1.2000
Median  = 1.0852                        ← middle element
```

Uncorrupted — and independent of the spike's magnitude. 1.2000, 12.0000 or 1200.0000
all give the same result. The spike's **value** is discarded entirely; only its **rank**
is used, and its rank ("highest") is all the filter needs in order to ignore it.

### 1.2 Breakdown point

The statistical name for this property is the **breakdown point**: the fraction of
arbitrarily corrupted observations an estimator tolerates before its output can be
driven anywhere.

| Estimator | Breakdown point |
|---|---|
| Mean (any linear filter) | 0% — one bad point moves it arbitrarily far |
| 5-bar median | 40% — survives 2 of 5 |
| Median, asymptotic | ~50% — theoretical maximum |

Nothing exceeds 50%: past half, the corrupted points *are* the majority, and no
estimator can distinguish which group is genuine.

**Relevance to this project:** BTC/USD H4 carries flash crashes, exchange outages and
wick prints. A 40% breakdown point is the difference between an indicator that survives
March 2020 and one that emits garbage for ~40 bars while a linear filter's state decays.

### 1.3 What non-linearity costs

| Cost | Consequence |
|---|---|
| Not a convolution | **No transfer function.** "Gain at 20 bars" is undefined for the median stage. Seven weeks of DSP tooling does not apply to it. |
| Not differentiable | No Taylor expansion, no polynomial approximation, **no analytic lag** — lag must be measured empirically via cross-correlation. |
| Order-dependent | Requires an explicit sort. Cannot use the Zorro `series()` IIR pattern for this stage. |

Ehlers' design confines the non-linearity to a single stage: median rejects outliers,
then a linear EMA smooths. Everything downstream of the median remains analysable.

---

## 2. The RM construction

```
RM[0] = α · Median(Price, 5) + (1 − α) · RM[1]
```

### 2.1 The critical asymmetry — a gate in front of the state

**The median is not recursive.** It is a memoryless sliding window: five bars in, one
number out, no state. The EMA is the sole recursive element, and it operates on the
median's output — never on raw price.

This is the entire design:

| Arrangement | Outlier behaviour |
|---|---|
| Plain EMA of price | Spike enters filter **state**, multiplied by α, decays over ~1/α bars. At P=12 that is ~2.4 bars of contamination, magnitude-proportional. |
| **RM (median → EMA)** | Spike rejected **before** reaching state. The recursive element only ever sees pre-cleaned data. Filter memory cannot be poisoned by what the median discarded. |

**Bound on the protection.** If three or more *consecutive* bars are corrupted, the
median passes them, they enter EMA state, and ordinary decay applies. Protection is
limited by the breakdown point: a 5-bar median guards against runs of up to **two**
consecutive bad bars.

### 2.2 Why 5 bars

Ehlers asserts a 5-bar window without justification. The argument he should have made:

| Window | Breakdown | Max consecutive outliers rejected | Lag on a ramp |
|---|---|---|---|
| 3 | 33% | 1 | 1 bar |
| **5** | **40%** | **2** | **2 bars** |
| 7 | 43% | 3 | 3 bars |

A 3-bar median kills only *isolated* single spikes. Real flash-crash structure is
frequently 1–2 bars. Five is the smallest window covering that case. Seven buys a third
bar of protection for a full extra bar of lag — a poor trade for the marginal event.

### 2.3 The alpha formula

Source (degrees):

```
α = (Cosine(360/P) + Sine(360/P) − 1) / Cosine(360/P)
```

**Zorro Light-C (radians — mandatory conversion):**

```c
alpha1 = (cos(2*PI/P) + sin(2*PI/P) - 1) / cos(2*PI/P);
```

> ⚠️ **No 0.707 multiplier here.** This is a single-pole filter. See §3.2.

#### What LPPeriod controls

This is Ehlers' standard one-pole critical-period constant. It places the EMA's
**−3 dB (half-power) point at period P**. Verified against the one-pole magnitude
response |H(ω)| = α / √(1 − 2(1−α)cos ω + (1−α)²):

| P | α (Ehlers) | \|H\| at period P | dB | True −3 dB α |
|---|---|---|---|---|
| 8 | 0.5858 | 0.7654 | −2.32 | 0.5266 |
| 12 | 0.4226 | 0.7321 | −2.71 | 0.4007 |
| 20 | 0.2735 | 0.7159 | −2.90 | 0.2677 |
| 48 | 0.1230 | 0.7086 | −2.99 | 0.1225 |

**Conclusion:** an asymptotically exact −3 dB design — effectively perfect for P ≳ 20,
drifting to ~0.7 dB error at P=8. Usable at the default P=12, but it is an
approximation, not an identity.

**Practical reading:** LPPeriod is the wavelength at which the filter attenuates by
half-power. Cycles longer than P pass; shorter than P are suppressed.

#### The `α ≈ 5/Period` shortcut

| P | Exact | 5/P | Error |
|---|---|---|---|
| 8 | 0.5858 | 0.6250 | +6.7% |
| 10 | 0.4905 | 0.5000 | +1.9% |
| **12** | **0.4226** | **0.4167** | **−1.4%** |
| 20 | 0.2735 | 0.2500 | −8.6% |
| 30 | 0.1902 | 0.1667 | −12.4% |
| 48 | 0.1230 | 0.1042 | −15.3% |

Tightest near P≈12 (his default), degrading badly at long periods. **Use the exact
form** — there is no computational reason not to, and at P=48 the shortcut is 15% wrong.

### 2.4 Documented error in the source

Ehlers writes that the critical period is where *"shorter wavelengths are passed by the
filter and longer wavelengths are rejected at the filter output."*

**That describes a high-pass. The RM is a low-pass** — it passes long wavelengths and
rejects short ones. The sentence is inverted.

Not a formula error; the code is correct. The description appears to have been carried
over from his one-pole *high-pass* design, which uses the identical α expression,
without re-wording for the complementary case.

### 2.5 Predicted lag — falsifiable before implementation

| Stage | Contribution | Basis |
|---|---|---|
| Median (5-bar) | 2.00 bars | On a monotonic ramp, the middle of the last five values is the value 2 bars ago |
| EMA (P=12) | 1.37 bars | (1−α)/α = 0.5774/0.4226 |
| **Total** | **≈ 3.4 bars** | |

The median's lag is **data-dependent** — 2 bars on a clean ramp, but shifting near
turning points and in choppy conditions where the middle bar's position moves. No
analytic lag exists for a non-linear filter; Day 4 cross-correlation is the real answer.

> **Prediction registered before implementation:** measured lag on trending stretches
> should fall near 3.4 bars. A result near 6 indicates a bug.

---

## 3. The Recursive Median Oscillator (RMO)

### 3.1 Purpose

RM outputs a smoothed price **level** — ~1.0850 on EUR/USD, ~43,000 on BTC. Unusable as
a confirmation indicator: no zero line, no threshold, not cross-asset comparable.

The RMO high-passes the RM output:

```
RMO = (1−α₂/2)²·(RM − 2·RM[1] + RM[2]) + 2(1−α₂)·RMO[1] − (1−α₂)²·RMO[2]
```

Three simultaneous effects:

**(a) Removes DC.** `RM − 2·RM[1] + RM[2]` is a second difference. A constant returns
zero; a linear ramp *also* returns zero (first differences kill constants, second
differences kill linear trends too). Output is zero-centred regardless of price level →
**a usable zero-crossing signal**.

**(b) Cross-asset comparability.** Output is in units of price *curvature*, not price.

> ⚠️ **This is not AGC.** Unlike MESA Stochastic's rolling min/max normalisation, RMO
> has **no automatic gain control** — amplitude still scales with volatility. Project
> notes record BTC/USD H4 oscillator amplitude varying ~10× across regimes. **This is a
> real gap.** RMO may require a normalisation wrapper before it is usable as C2 on
> crypto. Flagged for Day 4.

**(c) Composite bandpass.** RM low-passes below LPPeriod=12; the high-pass cuts above
HPPeriod=30. Together: passband ≈ 12–30 bars, with a non-linear outlier gate in front.
That composite is the object being evaluated for C2.

### 3.2 The 0.707 constant

```c
alpha2 = (cos(0.707*2*PI/P) + sin(0.707*2*PI/P) - 1) / cos(0.707*2*PI/P);
```

Same α formula, but with frequency **pre-scaled by 0.707 = 1/√2**.

**Why:** this is a two-pole filter formed by cascading two identical one-pole sections.
Each attenuates by 1/√2 at its own corner; cascaded, 1/√2 × 1/√2 = 1/2 — half-power is
reached at the *wrong* frequency. Pre-scaling each section's corner by 1/√2 separates
them just enough that the **composite** response lands at −3 dB at period P.

0.707 is therefore not a magic number but the compensation factor for stacking two
identical poles. The same constant appears in `HighPassFilter`, and as `1.414 = 2/√2` in
SuperSmoother.

> ⚠️ **IMPLEMENTATION HAZARD — the most likely bug in this file.**
> `alpha1` (RM low-pass, §2.3): **single pole → NO 0.707**
> `alpha2` (RMO high-pass, §3.2): **two poles → 0.707 REQUIRED**
> Both sit in the same file, look nearly identical, and differ by one constant.
>
> Reference values (verified): `alpha1(LPPeriod=12) = 0.422650`,
> `alpha2(HPPeriod=30, with 0.707) = 0.138102`

### 3.3 Why second order — Ehlers' reason is wrong, his choice is right

**His stated justification:** second-order attenuation is required to handle "the
statistical fractal pink-noise spectral shape of market data."

**Correction (own research, Aug 2026 — see `docs/research/Cycle_Premise_Null_Test.md`):**
measured spectral slope is f^−1.835 (EUR/USD D1), f^−1.837 (BTC/USD H4), f^−1.848
(synthetic random walk). That is **brown noise, f^−2 — a random walk** — not pink noise
(f^−1). Right observation, wrong label.

**The engineering conclusion survives the correction and is strengthened by it:**

| Filter order | Roll-off | Against f^−2 |
|---|---|---|
| First | 6 dB/octave | **Break-even** — leaves a flat residual of trend leakage |
| **Second** | **12 dB/octave** | **Wins by 6 dB/octave** |

Under f^−2, low-frequency power grows faster as frequency falls than under f^−1. A
first-order high-pass would merely break even, leaving flat residual trend leakage.
Second-order genuinely suppresses it.

> **The corrected reasoning justifies the design choice more firmly than the reasoning
> Ehlers gives.** A clean instance of Phase 2 Principle 7 — the mechanism survives
> independently of the cycle premise.

His secondary claim (second-order reduces critical period ~70% vs an EMA) is the 0.707
restated.

---

## 4. Evidential status under Phase 2 Principles 6–7

**Mechanism:** outlier-robust non-linear smoothing (RM) + detrended second-order
momentum (RMO).

**Null gate (Principle 6): NOT REQUIRED.** RMO's justification does not rest on
extracting a cycle. It is a bounded, detrended momentum oscillator with a characterised
passband. A zero crossing means: *price curvature, after outlier rejection and
band-limiting, changed sign.* That is a statement about recent momentum relative to a
filtered baseline — true whether or not a persistent spectral peak exists.

**Evidential bar (Principle 7):** mechanism survives → a good backtest is
**corroboration**, not coincidence.

### 4.1 Permitted and forbidden uses

| Use | Status |
|---|---|
| Sign of RMO as directional confirmation | ✅ Supported |
| Zero crossing as signal event | ✅ Supported |
| RMO **period** used to project a future turn | ❌ **Forbidden** — cycle extrapolation, unsupported (Week 11) |
| RMO **phase** used for timing | ❌ **Forbidden** — same reason |

### 4.2 Honest tension, to be stated in the library entry

RMO's passband is ~12–30 bars. The Week 11 null test found the RoofingFilter→CyberCycle
chain resonating at ~20 bars on **pure Brownian motion**. RMO will likewise oscillate at
roughly that period on random data.

**This is expected and is not a defect**, provided the claim remains "sign of filtered
momentum" and never "the market's cycle." A reviewer will ask; the answer must be in the
documentation. **Use the sign. Do not use the phase.**

---

## 5. C2 candidacy — pre-registered prediction

Comparison against the locked Strategy 2 C1:

| | MESA Stochastic (C1, locked) | RMO (C2 candidate) |
|---|---|---|
| Front end | Linear (HP 48 + SS 10) | **Non-linear** (5-bar median) |
| Detrend | Roofing filter, HP=48 | 2nd-order HP, P=30 |
| Normalisation | **Rolling min/max (AGC)** | **None** |
| Passband | ~10–48 bars | ~12–30 bars |
| Output | Bounded 0–1 | Unbounded, zero-centred |

Two decorrelating differences (non-linear front end, absence of AGC) against overlapping
passbands.

> **Prediction registered before data:** |ρ| between RMO and MESA Stochastic in the
> **0.4–0.65** range on both assets — straddling the pre-registered 0.5 acceptance
> threshold. Genuinely could go either way.

If |ρ| > 0.5, the pre-registered criterion rejects RMO for C2. The correct response is
to record that outcome and evaluate alternatives (Kalman, or Week 13's Laguerre RSI) —
not to revise the threshold after seeing the data.

---

## 6. Implementation notes carried to Day 3

1. **Radians, not degrees** — all trig arguments converted.
2. **`alpha1` has no 0.707; `alpha2` does.** Highest-probability bug. Verify against
   §3.2 reference values.
3. **Median stage requires an explicit 5-element sort** — cannot use the `series()` IIR
   pattern (non-linear, order-dependent).
4. **IIR state in included files requires `static` variables** — applies to `RM[1]`,
   `RMO[1]`, `RMO[2]`.
5. **Namespace is flat across included files** — prefix all locals `rm_` / `rmo_`
   (`cc_` is taken by CyberCycle).
6. **Seed static state explicitly on first call** — zero-initialised statics need a
   price-seeding guard.
7. **Compute before the `if(is(LOOKBACK)) return;` guard** — otherwise zero warmup.
8. Defaults from source: `LPPeriod = 12`, `HPPeriod = 30`.

---

## 7. Open questions for Days 3–4

| # | Question | Resolved by |
|---|---|---|
| 1 | Does measured lag match the predicted ~3.4 bars? | Day 4 cross-correlation |
| 2 | Is \|ρ\| with MESA Stochastic below 0.5? | Day 4 — **decides the C2 slot** |
| 3 | Does the absence of AGC break RMO on BTC/USD H4? | Day 4 crypto validation |
| 4 | Can the existing `HighPassFilter` be reused for the RMO second stage? | Day 3 — check signature accepts an arbitrary series |
| 5 | Does RM demonstrably outperform a plain EMA through the 2020-03 BTC crash? | Day 4 flash-crash test |
| 6 | Do `LPPeriod=12` / `HPPeriod=30` generalise cross-asset without retuning? | Day 4 both assets |

---

## 8. References

- Ehlers, J. F. (2018). "Recursive Median Filters." *Stocks & Commodities* 36:03, 8–11.
- Slutsky, E. (1937). "The Summation of Random Causes as the Source of Cyclic
  Processes." *Econometrica* 5(2).
- Own research (Aug 2026): `docs/research/Cycle_Premise_Null_Test.md`;
  `docs/research/Cycle_Premise_Conclusions_and_Impact.md`.
- Roadmap `FX_Roadmap_v2026.08.03.md` (v4.3), Phase 2 Principles 6–7.
