# Week 14 — Session 1 Handoff (part 4)

**Dates:** 2026-09-25 and 2026-09-28 (one sitting, split over a weekend)
**Covered:** RoofingFilter — full recall → probe → read → gap check → fix cycle
**Not covered:** Decycler, `CyberCycle.c` statics
**Repo:** `17b9228` → *this commit*

Read parts 1–3 first. This continues part 3's section 9.

---

## 1. Carried into the sitting

Part 3 §4.3 says the high-pass "decays monotonically". Wrong — fixed in
`cc1bcdc`. Critically damped means zero sign changes, not monotonic decay: the
response grows for ~11 bars, peaks at ~4.4× the kick, then decays. Part 3 was not
rewritten (dated record). This sitting derived that behaviour (§4.6).

## 2. What reconstructed cleanly

- **The parameter rules**, once asked directly: HP(48) passes periods shorter than
  ~48, SS(10) passes periods longer than ~10.
- **The cascade.** "A rejected by HP, C by SS, ~90% of B left", and 0.9213 ×
  0.9661 by hand.
- **The SSPeriod trade-off**, both directions.
- **The identification problem, unprompted.** Asked what an empty roofing output
  would mean: "either the choice was not smart, or EUR/USD has no signal in that
  band." That is exactly why the input spectrum is the missing measurement.
- **No cycle in a coin-flip recipe**, and the link to Fourier ("like white
  light") — the right frame, refined to red noise.
- **Claim 4 prediction.** HP = SS: "not nothing, but the band idea is lost."
- **Arithmetic under guidance:** first-bar seed (99 on flat 100), the 1.19
  prediction for CSV row 1, squaring to make swings count, the 1% vs 41% shares.

## 3. What did not reconstruct

- **GAP-1.29 — RoofingFilter not recalled at all.** Closed by reconstruction from
  the two stages reviewed in part 3.
- **Rule held, not applied.** Row-B guesses (20-bar cycle: "almost nothing"
  through HP, "about half" through SS) contradicted the rule stated two minutes
  later. Measured 0.9213 and 0.9661.
- **Sampled value read as gain** (0.5 for a 2-bar average at period 4; true
  0.707).
- **All four header claims marked "supported"** in one line. Three fell to the
  gain table already on screen.
- **Both standing questions on the test file** — "don't know" until narrowed to
  counting `if`s and imagining a fresh clone.
- **Lookback transient "thrown away".** Right that the filters don't run in
  lookback; wrong conclusion — the decay needs the filter to run.
- **Repeated pole vs single pole.** Needed the two-stage table; first attempt
  off by one row.
- **Stability of run 2.** Asked for a full walkthrough rather than attempting it.

**Observation for the reviewer, not the indicator:** the second day ran many
consecutive "don't know"s. Plan §2.2 asks Claude to check when "clear" comes too
quickly; the same check applies to a run of "don't know". It was a long sitting
and the right call was to stop before Decycler, which was taken.

## 4. Findings

### 4.1 The roofing filter is a window made by two slopes

The two gains multiply — verified: predicted amplitude 1.780076, measured
1.780076, residual 1.9e-13. Peak 0.8907 at 19.15 bars; half-power band 10.40 to
43.57. Neither stage alone bounds both ends. **The parameter is not the corner:**
HP(48) half-power at 43.74, SS(10) at 10.17.

### 4.2 Its output shape carries no information about input cycles

A coin-flip walk comes out swinging in same-sign runs of 5, 8, 13, 7, 18, 9 bars.
The filter keeps a slice of a broadband input and a narrow slice *is* a wobble.
White input → 10.75-bar rhythm, red (random walk) → 23.24. **The gain peak
belongs to the filter; the zero-crossing period belongs to filter × input.** The
Cycle Premise fingerprint (19.5 / 19.8 / 20.4) clusters because its inputs share
a spectral slope, and it came from a different chain (roofing → CyberCycle).

### 4.3 Every header claim states a slope as a wall

"Removes" (HP(48) passes 0.4186 at period 80; SS(10) 0.5244 at period 8), "only
dominant cycle survives" (§4.2), "collapses to nothing" (HP = SS gives peak
0.4778; the band shrinks smoothly, half-power band first appears between ratio
1.5 and 2). Kin to the one-scalar-for-a-trade-off pattern; logged as a related
shape rather than instance 8.

### 4.4 Provenance and parameters

Source is *Predictive And Successful Indicators* (TASC V.32:1, 2014, code © 2013),
which hard-codes 48 and 10. The header cites "Optimal Detrending"; the project PDF
is *Optimum Detrending* (1992), a different design (GAP-1.31). SSPeriod=10 is in
the same position as HPPeriod=48 — a citation — and was never flagged
(GAP-1.30). The measurement that would justify them is the input spectrum, and it
exists: the null test found no peak on EUR/USD D1.

### 4.5 The SuperSmoother inherits the high-pass seed

`SuperSmoother2Pole` seeds at its input's first value; in `RoofingFilter.c` that
input is `hp`, which starts at `P0·(1 − alpha1²)` = 1.091382 on flat 1.10.
Confirmed on the real export: row 1 HP = Roofing = 1.19306 = 0.992166 × Close.

### 4.6 A repeated pole decays as (n+1)·bⁿ — part 3's seed figure was 3.4× low

Two one-pole stages in a row (b = 0.5, kick 1): stage 2 / stage 1 = 1, 2, 3, 4, 5.
With the real b, `(n+1)·bⁿ` peaks at bar 10, height 4.3541 — the carried
correction, derived. From a seed the factor is `b·(1 + alpha1·(n+1))`. At bar 30
the HP is **0.2328**, not the 0.068 part 3 wrote into the notes (GAP-1.32, now
corrected). Roofing falls below 1% of the seed only at bar 72.

### 4.7 The test cannot fail and puts the transient in its output

`Test_RoofingFilter.c` has one `if`, about lookback; everything else is
`file_append` (GAP-1.33). The `return` precedes the filters (GOTCHAS §4.1, which
postdates the file), so the transient lands in CSV rows 1 to ~72 — confirmed:
row 30 = 0.28310 / 0.31283, row 72 HP = −0.00100 (GAP-1.34). Also: `static int
barCount` never reset at INITRUN (§9b.1); `file_append` with no delete (§6.3).

### 4.8 The Week 6 notebook measured a filter the library does not contain

**The most consequential finding of the sitting.** GAP-1.27e (2.6× vs 10.9×)
resolved, and it opened GAP-1.35:

| figure | source | filter | reproduced |
|---|---|---|---|
| 10.9× | cell 15, `data/fx/` CSVs dated 4 May | pre-radians-fix HP (`cos(360/48)` as radians, no 0.707, alpha1 0.8211) and SS | **10.88** on run 1 |
| 2.6× | cell 19, recomputed in Python | no degrees bug, **0.707 missing** (alpha1 0.123024) | 2.59 in simulation |
| — | current library, `C:/Zorro/Data/` (10 May) | correct | 2.17 real CSV |

`data/fx/HP_EURUSD_D1.csv` holds 5,192 rows = **two runs**: run 1 as above; run 2
with `cos(0.707·360/48)` (alpha1 −2.2903, pole 3.29) diverging to `-nan(ind)`. The
notebook would crash if re-run. The radians fix reached the code and the Zorro
folder but never `data/fx/` — **same class as GAP-1.15**, now affecting data, not
prose. Every EUR/USD figure in the Week 6 notebook (HP mean, 10.9×, Decycler 4.5×)
describes the pre-fix filter.

Part 3 wrote "cell 19 unaffected in structure": true of its loop, but cell 19
also lacks the 0.707.

The method that found it is worth keeping: predict a value from first
principles, check it against the actual file, and when it misses, identify which
coefficient version reproduces the file's first rows exactly.

### 4.9 Constant

`SuperSmoother2Pole.c` uses √2 (per part 1 and `SuperSmoother_Notes.md`); Ehlers
publishes 1.414. Differences in the 4th decimal. The real CSV cannot distinguish
them. Not a defect; the learning doc states it.

## 5. Gaps

| ref | finding | status |
|---|---|---|
| GAP-1.27e | 2.6× vs 10.9× | **resolved** — two different filters, neither the library (§4.8) |
| GAP-1.29 | RoofingFilter mechanism not recalled | closed — reconstructed |
| GAP-1.30 | SSPeriod=10 unjustified, never flagged | recorded in notes |
| GAP-1.31 | Provenance: "Optimal Detrending" cited; source is *Predictive And Successful Indicators* | notes fixed; **`RoofingFilter.c` header and `Week5-14_Indicator_Plan.md` still carry it** |
| GAP-1.32 | Part 3's seed transient 0.068 at bar 30 used bⁿ; true 0.2328 | FIXED in notes |
| GAP-1.33 | `Test_RoofingFilter.c` has no pass criterion | open |
| GAP-1.34 | `Test_RoofingFilter.c` returns before computing; transient in export rows 1–72 | open — confirmed on real CSV |
| GAP-1.35 | Week 6 EUR/USD inputs are pre-radians-fix output, two runs, second diverges | recorded; **Decycler and BTC files not checked** |

## 6. Commit

*This commit:*

- `docs/learning/RoofingFilter_Explained.md` — new
- `docs/learning/roofing_playground.py` — new; ten sections, every number in the
  explainer
- `docs/learning/RoofingFilter_Playground_Manual.md` — new; five experiments,
  each run before writing
- `docs/indicators/HighPass_RoofingFilter_Notes.md` — 97+/25−: source, status row,
  §2 corrections, §4 SSPeriod and GAP-1.27e, critical rule measured, §5 GAP-1.35
  box, §7 seed figure and real-CSV confirmation, changelog
- this handoff

No measured Week 6 value was changed. Code untouched.

## 7. Corrections to material produced in session

Claude produced these; all caught before commit.

- Called 48 and 10 "just numbers I picked" — they were recalled Ehlers values,
  unverified at the time. Verified later against the article.
- Gain measured by driving sines and taking (max − min)/2: 0.0000 at period 2 (a
  period-2 sine is zero at integer bars) and a non-monotonic HP curve. Replaced
  by gain from coefficients.
- Cascade amplitude read as 1.7775 by the same method; least-squares gives 1.780.
- Nearly reported the roofing gain peak (19.15) as confirming the null test's
  fingerprint. Refuted by running white vs red input.
- Used 1.414 all sitting where the library uses √2.
- Hinted that one smoothing ratio measured size and the other jaggedness. Both
  measure jaggedness.
- A pandas command assumed a numeric CSV; the file contained `-nan(ind)`.
- Estimated the notes diff at "70–80 lines" without computing; actual 97+/25−.
- Drafted "HPPeriod ≥ 2 × SSPeriod for any half-power band", stronger than the
  measurement; tightened before sending.
- Carried from part 3 and found here: the 0.068 seed figure (GAP-1.32).

Relied on part 1/3 descriptions of `HighPassFilter.c` and `SuperSmoother2Pole.c`
seeding without reading either file this sitting. Confirmed by the real CSV.

The pattern is part 3's: figures stated before computing. Every one of these was
caught by running something.

## 8. Deliberately not done, all unblocked

- **`RoofingFilter.c` header** — provenance (GAP-1.31), the four claims,
  "Validated: EUR/USD D1, BTC/USD H4". Live code; comment-only, but same
  discipline as `HighPassFilter.c`'s header deferred in part 3.
- **`Test_RoofingFilter.c`** — move the filters above the lookback `return`,
  reset statics at INITRUN, add a pass criterion. Gain from coefficients at period
  20 (0.890038) and period 2 (0) needs no data and would catch a swapped
  parameter or missing 0.707.
- **The seeding fix** (GAP-1.26) — changes all downstream output.
- **`data/fx/`** — regenerate, or leave and put a header on the Week 6 notebook
  and `Week6_Notes.docx`. Records are not rewritten (part 2 §6); a header note
  is the judgement call.
- **Check `Decycler_EURUSD_D1.csv` and `data/crypto/` BTC files** for the same
  defect. One `head -3` each and the `oldbug` comparison.
- **`HighPass_Explained.md` Part 3** — two of its "still don't understand" items
  are now closed. Could point to the roofing doc.
- **D-14.1 implementation** — slices, export script, synthetic test file.

## 9. Next sitting starts here

**Chat title:** `Week 14 Session 1 (part 5) — Foundation Filters`

1. **Decycler.** First question, before anything else: `Decycler.c` is
   `Price − HighPass(Price)` and so is `UltimateSmootherE.c`. **Are they the same
   filter under two names?** Part 2 found this exact naming problem. GAP-1.23
   applies: "4.5× closer to price" is not a lag result — and after §4.8 it was
   also computed on pre-fix data.

   **Prediction to register before opening the file** (inference, `Decycler.c`
   unseen): if it calls `HighPassFilter()` with the library seed, its first
   output is `Price − 0.992166·Price = alpha1²·Price` ≈ **0.0094** on EUR/USD —
   near zero, not near price — and it climbs to price level over ~70 bars. A
   smoother that starts at zero is the low-pass version of the GAP-1.26 problem.
   Check against `C:/Zorro/Data/Decycler_EURUSD_D1.csv` row 1.

2. **`CyberCycle.c` statics missing the `cc_` prefix** (GOTCHAS 1.3) — unconfirmed
   after four sittings.

The Decycler review is also where GAP-1.35's unchecked Decycler file gets
checked.
