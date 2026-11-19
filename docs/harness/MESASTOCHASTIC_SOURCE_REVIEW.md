# MESA Stochastic — source review (code vs article)

**Date:** 2026-11-18 (planning chat). **Status:** review complete, decisions taken (user, 2026-11-18). No spec yet.
**File reviewed:** `indicators/ehlers/MESAStochastic.c` (2064 bytes, mtime 2026-08-03), with its dependencies
`RoofingFilter.c`, `HighPassFilter.c`, `SuperSmoother2Pole.c`.
**Source:** Ehlers, J.F., "Predictive And Successful Indicators", *Technical Analysis of Stocks &
Commodities* V.32:1 (2014), pp. 16-25; sidebar "EasyLanguage Code To Compute The MESA Stochastic
Indicator" ((C) 2013), PDF p. 8. Read from the page image, not only the text layer. PDF in project knowledge:
`Predictive And Successful Indicators.pdf`.
**Context:** PROJECT_STATE §7 step 3, order C, oscillator harness family (HARNESS_DESIGN D6), second indicator
after Reflex. MESA Stochastic (20, 48, 10) is a C1 candidate (§1.2).

Labels: (a) source states · (b) read or computed here · (c) inference.

---

## 1. Source formula (a)

Input `Length` (default 20). All variables start at 0 (`Vars: alpha1(0), HP(0), ..., Filt(0), ..., Stoc(0),
MESAStochastic(0)`).

```
alpha1 = (Cosine(.707*360 / 48) + Sine (.707*360 / 48) - 1) / Cosine(.707*360 / 48);
HP = (1 - alpha1 / 2)*(1 - alpha1 / 2)*(Close - 2*Close[1] + Close[2]) +
     2*(1 - alpha1)*HP[1] - (1 - alpha1)*(1 - alpha1)*HP[2];
a1 = expvalue(-1.414*3.14159 / 10);
b1 = 2*a1*Cosine(1.414*180 / 10);
c2 = b1;  c3 = -a1*a1;  c1 = 1 - c2 - c3;
Filt = c1*(HP + HP[1]) / 2 + c2*Filt[1] + c3*Filt[2];
HighestC = Filt;
LowestC = Filt;
For count = 0 to Length - 1 Begin
    If Filt[count] > HighestC then HighestC = Filt[count];
    If Filt[count] < LowestC then LowestC = Filt[count];
End;
Stoc = (Filt - LowestC) / (HighestC - LowestC);
MESAStochastic = c1*(Stoc + Stoc[1]) / 2 + c2*MESAStochastic[1] + c3*MESAStochastic[2];
Plot1(MESAStochastic); Plot2(.8); Plot6(.2);
```

(a) HP and Filt are the Roofing Filter lines of the same article (HP-A(48) -> SuperSmoother(10)). The final
smoothing reuses the SuperSmoother(10) coefficients `c1..c3`. Only `Length` is an input; 48 and 10 are fixed.
(a) No start-up rule (no `CurrentBar` clause). No guard on `HighestC - LowestC = 0`.
(a) Output scale 0-1 (reference lines `.8` / `.2`). The text describes the conventional rule as crossing 20 / 80
(Figure 5 caption: "crosses above 20%"), i.e. a percent reading of the same levels.

## 2. Line-by-line comparison

| Stage | Source (a) | `.c` (b) | Verdict |
|---|---|---|---|
| Roofing | HP-A(48) -> SS(10) on `(HP+HP[1])/2`, histories start at 0 | `RoofingFilter(Price, HPPeriod, SSPeriod)` (line 21); verified RFF run 1 PASS (`d1395d3`), incl. zero start (O_SEED) | Matches (at 48, 10) |
| Window | `count = 0 .. Length-1`: **Length** bars | `series(..., StochPeriod + 1)`, loop `mstc_i = 1 .. StochPeriod` plus `[0]`: **StochPeriod + 1** bars (lines 21-30) | **M-1** |
| Stoc | `(Filt - LowestC)/(HighestC - LowestC)`, scale 0-1, no guard | `100.0 * (...)/(...)`, scale 0-100; `50` when `HH == LL` (lines 32-34) | **M-2**, **M-3**, **M-6** |
| Final smoothing | SS(10) coefficients on `(Stoc + Stoc[1])/2`, histories start at 0 | `SuperSmoother2Pole(series(RawStoch, 3), SSPeriod)` (lines 37-38); SS2 seeds history with its first input | Coefficients match (SS2 verified, SS2F `763601e`); seed **M-5** |
| Parameters | `Length` only; 48 / 10 fixed; final SS = roofing SS | `StochPeriod, HPPeriod, SSPeriod`; `SSPeriod` used for both SS passes | **M-7** |
| Start-up | not stated | inherited (§3) | **M-4**, **M-5** |
| Linear stage | — | not exported | **M-9** |
| Header | — | "naming caution" text, no source citation, unlabelled claims | **M-8** |

## 3. Start-up — what the code gives (b)

- HighPassFilter: HP history 0 (`d22ef57`); with input history = Price[0] (series seeding, gotchas 9d.6) the first
  HP output is 0. RoofingFilter's SS seeds at its first input, so the first Roof value is 0 (RFF O_SEED).
- The `.c` window `series(Roof, StochPeriod+1)` seeds its history with the first Roof value, 0 = the source's
  `Filt(0)` history. So GAP-1.26 (HP seeding) has no remaining effect on MESA: it was fixed upstream (**M-4**).
- First bar: every window value is 0, so `HH == LL`: the source divides 0/0; the `.c` returns the fallback.
- Final stage: the source starts `Stoc[1]` and `MESAStochastic[1..2]` at 0; the `.c` starts them at the first
  RawStoch (the fallback value). (b) Float64 model (L = 20, 48, 10; sine level 1.1, amplitude 0.01; 3000 bars; zero
  history vs first-value history): max |diff| 0.4367012995970475, last row with |diff| > 1e-12 is row 59, for
  T = 10 / 20 / 40 / 60 / 100 alike (**M-5**).

## 4. Deviations and decisions

Measured effects (b), same float64 model, rows >= 700 unless stated:

| T | \|21-bar window - article\| max | Article output min | Article output max |
|---|---|---|---|
| 10 | 1.1213252548714081e-14 | 0.15413908714843472 | 0.845860912851565 |
| 20 | 4.218847493575595e-15 | 0.016796460643083863 | 0.9832035393569165 |
| 40 | 0.062068399419046405 | -0.0275314999958112 | 1.0275314999958116 |
| 60 | 0.069859068895196 | -0.028837837356698932 | 1.0288378373566993 |
| 100 | 0.08053344297756188 | -0.029452071305994237 | 1.0294520713059907 |

| # | Deviation | Impact | Decision (2026-11-18) |
|---|---|---|---|
| **M-1** | Window StochPeriod + 1 bars; source Length bars | (b) invisible at T = 10, 20 (a 20-bar window already spans whole cycles); 6.2e-2 to 8.1e-2 at T = 40-100. (c) enough to move a 0.2/0.8 crossing | **Fix:** window of StochPeriod bars (`series(..., StochPeriod)`, `[0 .. StochPeriod-1]`). The spec must include sines with T > L. Negative control: the 21-bar window |
| **M-2** | Scale 0-100; source 0-1 | (b) Zorro callers: 4 export-only test scripts (`Test_MESAStochastic.c`, `Test_C2_LaguerreRSI.c`, `Test_LagSine.c`, `Test_RecursiveMedian.c`), no thresholds. (c) Older CSVs / notebooks hold 0-100 values | **Fix:** 0-1 as the source. Header notes that exports before the fix are x100. Same scale as Laguerre RSI (C2) |
| **M-3** | `100.0 *` literal first (gotchas 9d.8) | (b) one literal times a run-time expression, not a product of literals; 100 is exact in float32 | **Rejected** as a fold hazard. Moot after M-2 |
| **M-4** | HP seeding (GAP-1.26) not re-verified for MESA | (b) §3: fixed upstream; window history starts at 0 = source | **No change.** Close GAP-1.26 for MESA when the run passes; start-up reported as INFO |
| **M-5** | Final SS histories start at the first Stoc; source at 0 | (b) §3: up to 0.437, gone after row 59 | **Option (ii): keep;** start-up INFO only (D6 rule 6). The source start-up is itself undefined (0/0, M-6). Rejected (i), an in-file SS with zero history: a second SS copy to verify for warmup rows only |
| **M-6** | Zero range: source no guard (0/0); `.c` fallback 50 | (b) fires on the first bar and on every bar of a flat input | **Keep the guard, fallback 0.5** (mid-range: a flat market cannot produce a 0.2/0.8 crossing). Rejected: hold the previous value (can keep a stale signal alive). (c) TradeStation's own 0/0 behaviour unknown: the header calls the guard a library choice. Flat rows INFO (D6 rule 2); trace gate on the MODEL's HH - LL (D6 note) |
| **M-7** | Parameters generalised (48, 10 fixed in the source; final SS reuses the roofing SS) | `.c` matches the source at (20, 48, 10); `SSPeriod` for both passes keeps the source's sharing | **Record only** (library generalisation, as RoofingFilter) |
| **M-8** | No citation; header claims unlabelled ("unaffected by the null test", "~10x amplitude") | Record | **Fix header:** source, formula, deviations fixed, this review's path, claims labelled (a)/(b)/(c) or removed |
| **M-9** | Linear stage not exported (D6 rule 1) | Roof fidelity hidden inside the normalised output | **Fix:** `MESAStochasticCore(Price, StochPeriod, HPPeriod, SSPeriod, &roof, &stoc)`; `MESAStochastic()` a thin wrapper, callers unchanged. Bound check (D6 rule 3) on raw Stoc in [0, 1] exactly, not on the final output, which overshoots (table above: -0.0295 to 1.0295) |

**Old file:** kept as `MESAStochastic_Superseded.c` (negative control with M-1 and M-2 together), as for Reflex.

**Statics (b):** none in MESAStochastic.c, RoofingFilter.c, HighPassFilter.c or SuperSmoother2Pole.c; all state is
per-call `series()`. The Reflex R-1 class does not apply. **D6 rule 5:** not applicable (no statics); the layout still
runs several instances (e.g. L = 20 and 14) and IMP replays each against its own model. No invented shared-state control.

**Start-up counter (gotchas 9d.9):** not needed (no `CurrentBar` rule in the source).

## 5. For the spec (not decided here)

- Linear stage: Roof gets the v1 checks (flat, gains, phases, alternating input, ramp residual; D4), already
  passed in RFF; the spec states whether to re-run them through the new core or rely on RFF.
- Trace replay (D6 rule 2) on sines including T > L (40, 60, 100); W from the computed start-up memory (window
  L bars + SS memory; (b) final-seed effect gone after row 59); gate on the model's HH - LL.
- Bound: raw Stoc in [0, 1]; first-bar and flat rows give the fallback 0.5 (INFO).
- Invariance (D6 rule 4): scale x k and offset.
- Controls: old 21-bar window, the real superseded file, a coefficient off in its third digit (D2 rule 4),
  a wrong roofing period, final-seed variant (INFO).
