# High-Pass Filter, Roofing Filter & Decycler — Implementation Notes
**Week:** 6 (implementation) — reviewed Week 14
**Source articles:** Predictive And Successful Indicators (TASC V.32:1, 2014 —
the roofing filter's source), Whiter Is Brighter, Decyclers — TASC. *(Corrected
2026-09-28: this line previously cited "Optimal Detrending", which is not the
roofing filter's source; the project PDF of that name is* Optimum Detrending
*(1992), a different design. GAP-1.31.)*
**Implementation date:** March 2026
**Last Updated:** 2026-09-28 (Week 14 Session 1, part 4)

> **This file has no single family status.** Status is per indicator and per
> claim. The implementations and the evidence offered for them are in
> materially different condition — see the table below.

---

## Status

| Indicator | File | Implementation | Evidence |
|---|---|---|---|
| HighPassFilter | `indicators/ehlers/HighPassFilter.c` | **Correct.** Coefficients verified against the header's own reference (HPPeriod=30 → alpha1 = 0.138102, recomputed to 6 s.f.). Feedback polynomial is a perfect square → critically damped by construction | **Week 6 validation superseded.** Its four criteria cannot fail — see §5. No test in the repo could distinguish this filter from a mis-coefficiented one |
| RoofingFilter | `indicators/ehlers/RoofingFilter.c` | **Structure matches the source** — HP(48) → SS(10), both values hard-coded in Ehlers' published code. Gain computed from coefficients: peak 0.8907 at 19.15 bars, half-power band 10.40–43.57 bars. The SS stage seeds at its input's first value, so it inherits the HP's price-level seed (GAP-1.26) — confirmed on the real CSV, row 1 = 0.992166 × Close | **None valid.** Week 6 superseded, and its EUR/USD figures were computed from pre-radians-fix filters (GAP-1.35). `Test_RoofingFilter.c` has no pass criterion (GAP-1.33) and returns before computing, so the start-up transient lands in the export (GAP-1.34) |
| Decycler | `indicators/ehlers/Decycler.c` | Not re-examined in Week 14 | Week 6 only — superseded. The "4.5x closer to price" result measures the wrong quantity (§5) |

The distinction matters: **`HighPassFilter.c` is a correct implementation with no
valid evidence behind it.** Those are separate facts and the second does not
impugn the first.

Reviewed in Week 14 Session 1 part 3 (HighPassFilter; gaps GAP-1.17 to GAP-1.28)
and part 4 (RoofingFilter; gaps GAP-1.29 to GAP-1.35). Plain-language walkthrough:
`docs/learning/RoofingFilter_Explained.md`.

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
- HP → SuperSmoother pipeline (band-pass filter). The two gains multiply
- Attenuates slow movement (HP stage) and fast movement (SS stage), both
  **gradually**: HP(48) still passes 0.4186 at period 80, SS(10) passes 0.5244 at
  period 8. Only period 2 is removed exactly (SS gain 0)
- Passes a band: half-power 10.40 to 43.57 bars, peak 0.8907 at 19.15 bars
- **Produces cycle-shaped output from any broadband input.** A coin-flip walk
  comes out swinging on a ~23-bar rhythm. The output's shape says nothing about
  whether a cycle was in the input
- Use: standard preprocessor for all Week 8 oscillators

*(Corrected 2026-09-28: this list previously said "Removes both trend (HP stage)
and noise (SS stage)" and "Only dominant cycle survives". The first overstates a
gradual slope as a wall; the second is contradicted — see the coin-flip result
above, and the Cycle Premise null test, which reached the same conclusion on
market data in Week 11.)*

### Decycler
- Price - HighPassFilter(Price)
- Returns trend component with very low lag
- Use: Baseline candidate when lag reduction is critical

*(The "4.5x closer to price than SuperSmoother(P=20)" claim previously stated
here has been moved to §5 and marked as not a lag measurement.)*

---

## 3. Key Formulas

**Correct, matching `HighPassFilter.c`:**

```
alpha1 = (cos(0.707*2*PI/HPPeriod) + sin(0.707*2*PI/HPPeriod) - 1)
         / cos(0.707*2*PI/HPPeriod)

HP[0] = (1 - alpha1/2)² × (Price[0] - 2×Price[1] + Price[2])
        + 2×(1 - alpha1) × HP[1]
        - (1 - alpha1)² × HP[2]

Roofing  = SuperSmoother2Pole(HP, SSPeriod)
Decycler = Price[0] - HP
```

**Two things are wrong in versions of this formula elsewhere in the repo.**
Both appear in `analysis/notebooks/HighPass_RoofingFilter_Analysis.ipynb`, and
the first appeared in this file until 2026-09-10:

```
cos(360/HPPeriod)          // WRONG - degrees. Zorro and numpy take radians
cos(2*PI/HPPeriod)         // WRONG - radians, but the 0.707 is missing
cos(0.707*2*PI/HPPeriod)   // CORRECT
```

The **0.707** (= √2/2) is two-pole cascade compensation. It belongs to the filter
design, not to the unit conversion, in exactly the way SuperSmoother's √2 does
(see `SuperSmoother_Notes.md`, "Degrees vs Radians"). Dropping it is not
cosmetic: at HPPeriod=48 it gives alpha1 = 0.123024 instead of 0.088513, a 39% error,
which behaves like the correct filter at HPPeriod ≈ 35.

Note that `cos(360/HPPeriod)` in degrees and `cos(2*PI/HPPeriod)` in radians are
the *same angle* — `np.radians(360/x)` evaluates to `2*PI/x` exactly. The
degrees/radians distinction and the missing 0.707 are two separate defects that
happen to sit in the same expression.

### What the second difference actually blocks

`Price[0] - 2×Price[1] + Price[2]` is a **discrete second derivative** — the
change in the change:

    (P[t] - P[t-1]) - (P[t-1] - P[t-2])

It outputs **zero on a straight line, of any slope**, and non-zero wherever the
series bends.

> **Previously stated here as: "Trend is constant-speed price movement (zero
> acceleration). Zero acceleration = zero output = trend blocked."** That is
> correct for a perfectly straight line and wrong as a general statement about
> trend. A real trend that accelerates, decelerates or turns bends the series, and
> every bend produces output. The filter does not respond to "trend" or to
> "noise" — it responds to **curvature**. Noise passes because random jitter bends
> the series at nearly every bar, not because the filter can identify noise.

Worked example — a tent, `100 101 102 103 104 105 104 103 102 101 100`:

| t | window | second difference |
|---|---|---|
| 2-5 | inside the up leg | 0 |
| 6 | 104, 105, 104 | **-2** |
| 7-10 | inside the down leg | 0 |

Ten zeros and one -2, on input containing no noise at all. The -2 is the change
in slope (+1 into the peak, -1 out of it) in price units, reported on the bar
after the turn.

### Damping and settling

The feedback polynomial is

    z² - 2b·z + b²   where b = 1 - alpha1

which is `(z - b)²` identically. Its discriminant is **zero at every HPPeriod**,
so the filter has a **repeated real pole at b**: it is **critically damped** by
construction — the fastest settling achievable with no oscillation.

**This filter does not ring.** Across 120 bars after a single bend its output
changes sign **zero** times. It is not, however, monotonic. A repeated root gives
an impulse response of the form `(A + B*n)*b^n`, so the disturbance **grows before
it decays**: at HPPeriod=48 the tent's -1.83 kick at bar 6 reaches **-7.95 at bar
16**, 4.3x larger, and only then falls away. The turning point sits at
`1/(-ln b)` = 10.8 bars. The contamination window is therefore ~10 bars longer
than the settling table below suggests, and the disturbance is largest well after
the bend that caused it. *(Corrected 2026-09-10: this passage previously said the
output "decays monotonically" -- wrong, and caught only by running the filter.)*

A single dropped factor breaks this: `z² - 2b·z + b` has
discriminant -0.36 at b=0.9, giving complex poles and an oscillating filter.
Critically damped and ringing are completely different behaviours, and on real
price both look like a squiggle around zero.

**Settling time**, HPPeriod=48 (alpha1 = 0.088513, b = 0.911487):

| residue | bars |
|---|---|
| 10% | 25 |
| **1%** | **50** |
| 0.1% | 75 |

Roughly **25 bars per factor of 10** — constant bars-per-decade, the signature of
exponential decay. These are **envelope** figures measured from the response peak,
not from the bend: add ~11 bars to get the window from the bend itself. Rule of thumb, measured at two periods (48 → 49.7 bars, 20 → 20.6
bars): **1% settling ≈ HPPeriod**. Two points, not a proof.

### Superposition

The filter is linear, so its output is **exactly** the sum of the responses to
every past bend — not an approximation, and with no cross-terms. With bends
arriving every few bars and a ~50-bar memory, a single value of the output is an
accumulation of many past bends and cannot be read as a statement about current
conditions. Nothing downstream can separate them either.

This is the mechanism behind **GAP-1.16**: `UltimateSmootherE = Price - HP(Price)`
measured 0.0000 bars of lag on a ramp because a ramp has no bends, so the
high-pass contributes nothing and the subtraction is a no-op. Zero lag was
measured in the one regime where the mechanism is switched off.

---

## 4. Parameter Guidelines

### HPPeriod
Controls the low-frequency (trend) cutoff.

| HPPeriod | Behavior | Use when |
|---|---|---|
| 20-30 | Aggressive trend removal | Short dominant cycles expected |
| 48 | Ehlers default — balanced | General purpose (recommended) |
| 60-80 | Gentle trend removal | Long dominant cycles expected |

> **Not evidence-backed.** The Week 6 sensitivity sweep (notebook cell 18) that
> was to have justified HP=48 omits the 0.707 factor, so it swept a filter the
> library does not contain, and its "Smooth Ratio" column reduces algebraically to
> a constant for every row — no SuperSmoother is computed in that loop. Its
> conclusion is printed unconditionally and does not depend on its own output.
> HP=48 is retained as Ehlers' published default, which is a citation, not a
> measurement. (GAP-1.24.)

### SSPeriod
Controls the high-frequency (noise) cutoff.

| SSPeriod | Smoothing ratio | Use when |
|---|---|---|
| 5-8 | 1.7-2.2x | Fast cycle response needed |
| 10 | 2.6x | Ehlers default — general purpose |
| 14-20 | 3.3-4.6x | Maximum smoothness needed |

> **Not evidence-backed.** SSPeriod=10 is in the same position as HPPeriod=48:
> Ehlers' published value, a citation rather than a measurement. The same Week 6
> notebook was its only support. It cannot be justified by matching a dominant
> cycle on EUR/USD D1, because the Cycle Premise null test found none. (GAP-1.30.)

> **GAP-1.27e — resolved 2026-09-28.** Both figures were computed correctly; they
> describe **two different filters**, and neither is the library's.
>
> - **2.6x** (this table) is notebook cell 19, which recomputes the filter in
>   Python without the 0.707 (alpha1 0.123024). Reproduced at 2.59 on a random
>   walk. The whole table describes that filter.
> - **10.9x** (§5, cell 15) is computed from `data/fx/` CSVs exported by the
>   **pre-radians-fix** `HighPassFilter.c` and SuperSmoother. Reproduced exactly:
>   **10.88** on those files. See §5 and GAP-1.35.
> - **Current library:** cell 15's formula on the current Zorro export gives
>   **2.17** (30 rows dropped), 2.42 (72 dropped).
>
> The ratio is the std of bar-to-bar changes — it measures **jaggedness**, not
> size. On a random walk the size ratio is only 1.12.

**Critical rule (unsourced):** SSPeriod must always be significantly less than
HPPeriod. If they overlap, the passband collapses and cycles are blocked.

> Still unsourced. **Measured 2026-09-28** (gain from coefficients, SSPeriod=10):
>
> | HP/SS | peak gain | half-power band |
> |---|---|---|
> | 1.0 | 0.4778 | none |
> | 1.5 | 0.6237 | none |
> | 2.0 | 0.7131 | 12.99–15.65 |
> | 4.8 | 0.8907 | 10.40–43.57 |
>
> Direction supported, wording not: nothing collapses "to nothing". The band
> shrinks smoothly and the half-power band first appears between ratio 1.5 and
> 2. "Significantly less" can now read: **below HPPeriod ≈ 1.5 × SSPeriod there is
> no half-power band; at 2 × there is a narrow one** (measured at SSPeriod=10
> only).

### Recommended defaults
| Asset | Timeframe | HPPeriod | SSPeriod |
|---|---|---|---|
| EUR/USD | D1 | 48 | 10 |
| BTC/USD | H4 | 48 | 10 |

The claim that the same parameters work on both assets rests on the cross-asset
verdict in §5, which is a hardcoded string. See below.

---

## 5. Week 6 Validation Results — SUPERSEDED

> **Retained as a record of what was measured. Not evidence of correctness.**
>
> All four Week 6 criteria are unfalsifiable, for reasons established in Week 14
> Session 1 part 3:
>
> 1. **HP mean ≈ 0** (gate: `|mean| < 0.0001`) — the 1,-2,1 numerator telescopes,
>    so the sum over N bars collapses to endpoint terms and the mean falls as 1/N
>    for *any* coefficients. At 2,566 bars the mean is ~1e-6 against a 1e-4 gate.
>    Tests the numerator's algebra; blind to every feedback term, which is where
>    all the parameters and all the plausible typos live. (GAP-1.22)
> 2. **Roofing smoother than HP** — says only that SuperSmoother smooths, which
>    it does by construction.
> 3. **Decycler closer to price than SuperSmoother** — mean absolute distance from
>    price is not a lag measurement. It is minimised by the identity filter, which
>    has zero lag *and* zero smoothing. `Decycler = Price - HP`, and HP outputs
>    nothing on unbent input, so Decycler equals price by construction and wins
>    automatically. This is the same metric that produced the false
>    `UltimateSmoother` "zero-lag" claim in Week 5, later measured at 3.87 bars.
>    (GAP-1.23)
> 4. **No NaN values** — a crash check, not a validation.
>
> The test script `strategies/tests/Test_HighPass.c` contains **no pass criterion
> at all** — it computes the indicator and appends to a CSV. It cannot fail.
> (GAP-1.19)
>
> Not reproducible from a clone: the script writes to `Data/` in the Zorro install
> directory, the notebook reads from `<repo>/data/fx/`, and no tracked file
> records the copy step between them. `data/` is gitignored by policy.
> (GAP-1.20, superseded by **D-14.1**.)

> **The EUR/USD figures below describe a filter the library does not contain.**
> (GAP-1.35, found 2026-09-28.) The notebook reads `data/fx/*_EURUSD_D1.csv`,
> dated 2026-05-04. The radians fix landed between 4 and 10 May; the Zorro
> exports were regenerated on 10 May but never copied into `data/fx/`.
>
> - `data/fx/HP_EURUSD_D1.csv` rows 1–3 (0.39169, 0.09814, 0.02575) are
>   reproduced exactly only by `cos(360/48)` taken as radians with no 0.707
>   (alpha1 0.8211, library 0.088513). The Roofing file needs the matching
>   SuperSmoother degrees bug.
> - The files hold **5,192 rows = two runs**. Run 2 uses `cos(0.707*360/48)`
>   (alpha1 −2.2903, pole 3.29) and diverges to `-nan(ind)`. The notebook would
>   crash if re-run today.
> - Cell 15's smoothing formula on run 1 alone gives **10.88**. On the current
>   library export it gives 2.17.
>
> Not checked: `Decycler_EURUSD_D1.csv` (same date, also oversized) and the BTC
> files under `data/crypto/`. Treat the Decycler and BTC figures as unverified
> for the same reason.

### EUR/USD D1 (2015-2024, 2566 bars) — pre-fix filters, see box above
- HP mean: -0.000001 (oscillates around zero)
- Roofing Filter: 10.9x smoother than raw HP
- Decycler: 4.5x closer to price than SuperSmoother
- NaN values: 0

### BTC/USD H4 (2020-2024, 7504 bars)
- HP mean: -0.0365 — **originally recorded as ✅ with the annotation "negligible
  vs ~$50K price."** The stated criterion is `|mean| < 0.0001`. 0.0365 exceeds it
  by 365x. The criterion was not met and was set aside in prose rather than
  failed. (GAP-1.27d)
- Roofing Filter: 11.7x smoother than raw HP
- Decycler: 4.6x closer to price than SuperSmoother
- NaN values: 0

### Cross-asset verdict
Notebook cell 15 prints `CROSS-ASSET VERDICT: ✅ PASS — same parameters work on
both`. There is no comparison, threshold or boolean behind that line — it is a
hardcoded string, and the "key findings" figures beneath it (10.9x, 11.7x, 4.5x,
4.6x) are typed literals in an f-string rather than the computed variables shown
in the table above them. No metric in that section could have produced a fail.
(GAP-1.25)

This is the evidence behind `HighPassFilter.c`'s header line
`// Validated: EUR/USD D1, BTC/USD H4`. BTC/USD H4 data *was* processed, in this
notebook. The verdict it produced was unconditional. No BTC test script exists in
`strategies/tests/`. (GAP-1.18)

---

## 6. NNFX Component Mapping

| Indicator | NNFX Role | Notes |
|---|---|---|
| HighPassFilter | Input preprocessor | Feed into oscillators |
| RoofingFilter | Input preprocessor | Standard oscillator input (Week 8) |
| Decycler | Baseline candidate | Best when lag reduction > smoothness |

The Decycler row's justification — lag reduction — rests on the MAD result in §5,
which does not measure lag. Its actual lag on non-straight-line input is
unmeasured, for the same reason as GAP-1.16. Treat as provisional.

`HighPassFilter.c` is consumed by `RoofingFilter.c`, `Decycler.c`,
`DominantCycle.c`, `RecursiveMedian.c`, `UltimateSmootherE.c` and
`UltimateSmoother_W5_Superseded.c`. Anything established about it propagates to
all six.

---

## 7. Implementation Notes

- Trig args are **RADIANS** — `cos(0.707*2π/HPPeriod)`, not `cos(360/HPPeriod)`. Zorro Light-C
  uses the standard C math library. Ehlers publishes EasyLanguage in degrees; all
  formulas must be converted. *(Corrected 2026-08-06 — this line previously asserted the
  opposite. See Week3_Summary.md for the original bug.)*

  > **This dated marker is the only working instance of backward correction
  > propagation in the repository** — a fix that reached the document making the
  > original claim, said what it previously said, and named where the bug came
  > from. GAP-1.15 asks for a mechanism that does this routinely. This is the
  > template. Note it did not reach §3's formula block four sections above, which
  > kept the degrees form until 2026-09-10.

- RoofingFilter depends on HighPassFilter and SuperSmoother2Pole
- Include order in test scripts: HighPassFilter.c → SuperSmoother2Pole.c → RoofingFilter.c
- Relative #include paths inside indicator files don't resolve from strategy
  subfolders — put all includes in the test script
- Callers must invoke `HighPassFilter()` unconditionally every bar: `series()`
  allocates by call order

### Warmup — insufficient as configured

The notebook discards `WARMUP = 30` bars. From a price-level seed the high-pass
needs **71 bars** to fall below 1% of the seed and **99** to reach 0.1%; the
roofing output needs 72 and 100. Thirty is short by more than half.

This compounds with the initialisation. `HighPassFilter.c` uses
`series(Price[0], 3)`, seeding the HP state at **price level** (~1.10 on
EUR/USD), while the filter's steady-state output oscillates around **zero**. The
startup transient is therefore not a small seeding error but a decay from ~1.10
to ~0. At bar 30 the HP output on flat price 1.10 is **0.2328** — about 21% of
the seed — against a typical scale of ~0.001. The retained data begins with a
transient far larger than the signal. *(Corrected 2026-09-28: this previously
gave `0.911487³⁰ = 0.0621`, "about 0.068". That is the single-pole decay `b^n`;
this filter has a **repeated** pole, which decays as `(n+1)·b^n` for a kick and
about `b·(1 + alpha1·(n+1))·b^n` from a seed, 3.4x larger at bar 30. GAP-1.32.)*

**Confirmed on the real export.** `Test_RoofingFilter.c` places
`if(is(LOOKBACK)) return;` *before* computing the filters (against GOTCHAS §4.1),
so the filters get no warm-up and their first call is CSV row 1. The current
`C:/Zorro/Data/RoofingFilter_EURUSD_D1.csv` shows HP = Roofing = 1.19306 on row 1
(= 0.992166 × Close 1.20248, as `1 − alpha1²` predicts), 0.28310 / 0.31283 on row
30, and only reaches normal scale (HP −0.00100) near row 72. (GAP-1.34.)

The `.c` comment `// Initialize at Price[0] level to avoid startup transient` is
correct reasoning for a low-pass filter and backwards for a high-pass: for a
zero-mean output, seeding at price level *creates* the transient it means to
avoid. (GAP-1.26)

Not yet fixed. Changing the seed alters every downstream output and needs its own
before/after verification.

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
| RoofingFilter_Explained.md, roofing_playground.py, RoofingFilter_Playground_Manual.md | docs/learning/ |

**Naming:** the file is `HighPassFilter.c`; this document, the handoffs and
`docs/methods/Lag_Cancellation_Derivation.md` refer to it as "HighPass". Noted
before it becomes the `UltimateSmoother` / `UltimateSmootherE` problem.
(GAP-1.21.)

---

## Changelog

| date | commit | change |
|---|---|---|
| 2026-08-06 | — | §7 degrees/radians line corrected; §3 formula block left in the degrees form |
| 2026-09-10 | `ec12066` | §3 formula corrected to radians with the 0.707 restored; wrong forms retained as explicit counterexamples. "Zero acceleration = trend blocked" corrected to curvature. Damping, settling and superposition added. Family status replaced with per-indicator status and named evidence. §5 retitled superseded, its four criteria caveated, BTC threshold breach stated. §4 SSPeriod contradiction and unsourced "critical rule" flagged. Warmup insufficiency and seeding defect recorded. Changelog added. No measured value changed |
| 2026-09-10 | `cc1bcdc` | §3 damping: "decays monotonically" corrected to grows-then-decays, no sign changes |
| 2026-09-28 | *this commit* | RoofingFilter reviewed (part 4). Source corrected (GAP-1.31). Status row filled. §2 "removes" / "only dominant cycle survives" corrected. §4: SSPeriod flagged unjustified (GAP-1.30); GAP-1.27e resolved — 2.6x and 10.9x are two different filters; critical rule measured. §5: EUR/USD inputs identified as pre-radians-fix output (GAP-1.35). §7: seed transient at bar 30 corrected 0.068 → 0.2328 (GAP-1.32); warm-up figures recomputed from a price-level seed; transient confirmed in the real export (GAP-1.34). No Week 6 value changed |
