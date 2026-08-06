# High-Pass Filter, Roofing Filter & Decycler
**Week:** 6  
**Source articles:** Optimal Detrending, Whiter Is Brighter, Decyclers — TASC  
**Implementation date:** March 2026  
**Status:** ✅ VALIDATED — approved for library

---

## 1. What Problem These Solve

SuperSmoother (Week 5) removes noise and keeps trend. But for cycle-based
oscillators (Week 8: Cyber Cycle, EBS), trend is the problem — it causes
oscillators to drift and produce misleading readings.

These three indicators solve the complementary problem: isolating the cycle
component by removing trend and/or noise.

---

## 2. The Three Indicators

### HighPassFilter
- Removes trend (everything slower than HPPeriod)
- Output oscillates around zero
- Still contains noise above the cutoff
- Use: input preprocessing for oscillators

### RoofingFilter
- HP → SuperSmoother pipeline (band-pass filter)
- Removes both trend (HP stage) and noise (SS stage)
- Only dominant cycle survives
- Use: standard preprocessor for all Week 8 oscillators

### Decycler
- Price - HighPassFilter(Price)
- Returns trend component with very low lag
- 4.5x closer to price than SuperSmoother(P=20)
- Use: Baseline candidate when lag reduction is critical

---

## 3. Key Formulas
```
alpha1 = (cos(360/HPPeriod) + sin(360/HPPeriod) - 1) / cos(360/HPPeriod)

HP[0] = (1 - alpha1/2)² × (Price[0] - 2×Price[1] + Price[2])
        + 2×(1 - alpha1) × HP[1]
        - (1 - alpha1)² × HP[2]

Roofing = SuperSmoother2Pole(HP, SSPeriod)
Decycler = Price[0] - HP
```

**Why second difference blocks trend:**
Trend is constant-speed price movement (zero acceleration).
`Price[0] - 2×Price[1] + Price[2]` measures acceleration.
Zero acceleration = zero output = trend blocked.
Cycles have non-zero acceleration = they pass through.

---

## 4. Parameter Guidelines

### HPPeriod
Controls the low-frequency (trend) cutoff.

| HPPeriod | Behavior | Use when |
|---|---|---|
| 20-30 | Aggressive trend removal | Short dominant cycles expected |
| 48 | Ehlers default — balanced | General purpose (recommended) |
| 60-80 | Gentle trend removal | Long dominant cycles expected |

### SSPeriod
Controls the high-frequency (noise) cutoff.

| SSPeriod | Smoothing ratio | Use when |
|---|---|---|
| 5-8 | 1.7-2.2x | Fast cycle response needed |
| 10 | 2.6x | Ehlers default — general purpose |
| 14-20 | 3.3-4.6x | Maximum smoothness needed |

**Critical rule:** SSPeriod must always be significantly less than HPPeriod.
If they overlap, the passband collapses and cycles are blocked.

### Recommended defaults
| Asset | Timeframe | HPPeriod | SSPeriod |
|---|---|---|---|
| EUR/USD | D1 | 48 | 10 |
| BTC/USD | H4 | 48 | 10 |

Same parameters work on both assets — no retuning needed.

---

## 5. Validation Results

### EUR/USD D1 (2015-2024, 2566 bars)
- HP mean: -0.000001 ✅ (oscillates around zero)
- Roofing Filter: 10.9x smoother than raw HP ✅
- Decycler: 4.5x closer to price than SuperSmoother ✅
- NaN values: 0 ✅

### BTC/USD H4 (2020-2024, 7504 bars)
- HP mean: -0.0365 (negligible vs ~$50K price) ✅
- Roofing Filter: 11.7x smoother than raw HP ✅
- Decycler: 4.6x closer to price than SuperSmoother ✅
- NaN values: 0 ✅

---

## 6. NNFX Component Mapping

| Indicator | NNFX Role | Notes |
|---|---|---|
| HighPassFilter | Input preprocessor | Feed into oscillators |
| RoofingFilter | Input preprocessor | Standard oscillator input (Week 8) |
| Decycler | Baseline candidate | Best when lag reduction > smoothness |

---

## 7. Implementation Notes

- Trig args are **RADIANS** — `cos(2π/HPPeriod)`, not `cos(360/HPPeriod)`. Zorro Light-C
  uses the standard C math library. Ehlers publishes EasyLanguage in degrees; all
  formulas must be converted. *(Corrected 2026-08-06 — this line previously asserted the
  opposite. See Week3_Summary.md for the original bug.)*
- RoofingFilter depends on HighPassFilter and SuperSmoother2Pole
- Include order in test scripts: HighPassFilter.c → SuperSmoother2Pole.c → RoofingFilter.c
- Relative #include paths inside indicator files don't resolve from strategy
  subfolders — put all includes in the test script
- Warmup: skip first 30 bars for clean analysis

---

## 8. Files

| File | Path |
|---|---|
| HighPassFilter.c | indicators/ehlers/ |
| RoofingFilter.c | indicators/ehlers/ |
| Decycler.c | indicators/ehlers/ |
| Test_HighPass.c | strategies/tests/ |
| Test_RoofingFilter.c | strategies/tests/ |
| Test_Decycler.c | strategies/tests/ |
| HighPass_RoofingFilter_Analysis.ipynb | analysis/notebooks/ |