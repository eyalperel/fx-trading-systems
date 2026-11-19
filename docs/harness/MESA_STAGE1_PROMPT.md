# MESA stage 1 — tooling + reference models + spec draft (MESAStochastic)

Planning chat, 2026-11-18. Decisions accepted by the user: M-1..M-9 (`docs/harness/MESASTOCHASTIC_SOURCE_REVIEW.md`,
`3f0de96`), HARNESS_DESIGN **D6** (oscillator family), and for this spec: **trace tolerance 5e-5** (the D6 default 3e-5 fails
the D2 window, below), real variants L14 / L20 / L30 / S20, controls as listed. Build mode, speed over polish; the validation
gate is unchanged (CLAUDE.md). Labels: (a) source states, (b) measured/computed, (c) inference.

**Git:** branch `harness-mesa` (at `3f0de96`). Do NOT commit. At the end print the `git add` / `git commit` commands you
suggest (one commit for tooling+tests, one for the spec draft), and STOP. No `.c` edit, no Zorro run.

## Source (a): Ehlers, "Predictive And Successful Indicators", TASC V.32:1 (2014), pp. 16–25, sidebar "EasyLanguage Code To Compute The MESA Stochastic Indicator" (PDF p. 8)

```
Inputs: Length(20);   Vars: ... HP(0), Filt(0), HighestC(0), LowestC(0), Stoc(0), MESAStochastic(0);
alpha1 = (Cosine(.707*360 / 48) + Sine (.707*360 / 48) - 1) / Cosine(.707*360 / 48);
HP = (1 - alpha1 / 2)*(1 - alpha1 / 2)*(Close - 2*Close[1] + Close[2]) + 2*(1 - alpha1)*HP[1] - (1 - alpha1)*(1 - alpha1)*HP[2];
a1 = expvalue(-1.414*3.14159 / 10);  b1 = 2*a1*Cosine(1.414*180 / 10);
c2 = b1;  c3 = -a1*a1;  c1 = 1 - c2 - c3;
Filt = c1*(HP + HP[1]) / 2 + c2*Filt[1] + c3*Filt[2];
HighestC = Filt;  LowestC = Filt;
For count = 0 to Length - 1 Begin
    If Filt[count] > HighestC then HighestC = Filt[count];
    If Filt[count] < LowestC then LowestC = Filt[count];
End;
Stoc = (Filt - LowestC) / (HighestC - LowestC);
MESAStochastic = c1*(Stoc + Stoc[1]) / 2 + c2*MESAStochastic[1] + c3*MESAStochastic[2];
Plot1(MESAStochastic); Plot2(.8); Plot6(.2);
```
HP + Filt = RoofingFilter(48, 10) (verified, RFF run 1 `d1395d3`). The final smoothing reuses the SS(10) coefficients.
D1 rule 1: `.707` -> sqrt(2)/2, `1.414` -> sqrt(2), `3.14159` -> pi; degrees -> radians. Window = **Length bars** (count
0..Length-1). Scale **0–1**. No zero-range guard; no start-up rule. Library generalisation (M-7): `MESAStochastic(Price,
StochPeriod, HPPeriod, SSPeriod)`, `SSPeriod` used for both SS passes.

Library conventions (decided, M-4/M-5/M-6), which the reference model must implement for the REAL variants:
- HP history 0, input history = Price[0] (series seeding) -> first Roof = 0 (RFF O_SEED).
- Window history seeded with the first Roof value (`series()` seeding).
- Zero range (HH == LL): Stoc = 0.5 (library choice; the source divides 0/0).
- Final SS: `SuperSmoother2Pole(series(Stoc, 3), SSPeriod)`: Stoc and output histories start at the first Stoc.

## Planning-chat findings to record in the spec (b)

Independent code (numpy, float64; model as above; inputs level 1.1, sine amplitude 0.01, N = 3000, rows >= 700; Roof tables
analytic H(e^jw)). Reproduce with `reference.py`; report any difference > 1e-12 (tables) or > 1% relative (effects).

1. **Roof tables** (gain / phase rad), T = 5, 10, 20, 40, 100:
   - Roof(48,10) (L14, L20, L30): 0.2232924637311758, 0.681218960159867, 0.8900165495219456, 0.7405714692715452,
     0.31520956783497034 / -1.7262724708581954, -1.0206179300609166, -0.05338683922280491, 0.7699840012152294,
     1.8340513846256814. Alt gain 6.0342470785651366e-18. (Self-check: T = 20 matches PROJECT_STATE §5
     0.8900165495219391 to 6.5e-15.)
   - Roof(48,20) (S20): 0.05743161850487488, 0.23365848260774144, 0.6487070206488769, 0.7198621609155487,
     0.3149734799160282 / -2.073211124216958, -1.8117540367506384, -0.8564295844658563, 0.3805302637414841,
     1.6917733148668452. Alt gain 1.5107043619184777e-18.
   - Alt phase SKIP (gate 0.05); ramp residual 0 (HP second difference); flat 0.
2. **Roof floors, Zorro `PI` = float32(3.14159) vs pi:** (48,10) gain 5.278e-07, phase 1.328e-06; (48,20) gain 4.409e-07,
   phase 1.567e-06. Floor×10 <= 3e-5 on both.
3. **Trace floors (`PI` gap), max |Δout| rows >= 700**, T = 5, 10, 20, 40, 100:
   - L14: 3.2793504878281254e-07, 8.784203028855408e-07, 1.0646457658802788e-06, 1.7297547684202996e-06, **3.875320166324414e-06**
   - L20: 3.279350517804147e-07, 8.784203039402527e-07, 8.397692353168118e-07, 1.4513032355889521e-06, 3.2572078335624255e-06
   - L30: 3.2793505710948523e-07, 8.784203059386542e-07, 8.397692369821463e-07, 8.660523195258563e-07, 2.4668033711261472e-06
   - S20: 1.0819927825922449e-07, 2.4112161933764753e-07, 1.0047369309873488e-06, 1.6674523009574393e-06, 2.3008172037042307e-06
   **Trace tolerance 5e-5 (this spec):** largest floor 3.875e-06 (L14, T = 100); floor×10 = 3.88e-05 > the D6 default 3e-5,
   so the default fails D2 rule 3. 5e-5: floor margin 12.9×, NCA (smallest control) 7.94e-04 = 15.9×. Floor guard tol/10 = 5e-6.
   Record under D2 rule 1 as this spec's value with this reason; the D6 default stays 3e-5. (b) The floor peaks at T = 100
   because HH − LL is smallest there (finding 4): normalisation amplifies the `PI` gap.
4. **Gate margin** min (HH − LL)/amplitude, model, rows >= 700, T = 5, 10, 20, 40, 100:
   - L14: 0.41939132667745976, 1.3582805947183891, 1.3727194518603654, 0.39414032769408464, 0.028396521846796308
   - L20: 0.4193913266775104, 1.3582805947184167, 1.7774970167172783, 0.7290686557558217, 0.057985539938341026
   - L30: 0.419391326677519, 1.3582805947184744, 1.7774970167172863, 1.2560128828930173, 0.12688319427320272
   - S20: 0.10731137419782429, 0.45381612166435187, 1.2926137863010458, 0.6705343068945032, 0.05928624057810884
   **Gate g = 0.01** (judgement (c), D6 default); tightest margin 0.0284 (L14, T = 100). Expected gated rows: 0.
5. **Bound (raw Stoc):** every real variant, every input, every row: Stoc in [0, 1] exactly (min 0.0, max 1.0 attained).
   Final output is NOT bounded: article model output range rows >= 700, L20: [-0.0295, 1.0295] at T = 100 (review §4).
6. **Invariance** (float64 model, 5 sines, rows >= 700): scale10 (amplitude 0.1) / offset (level 2.2) max |Δout|:
   L14 2.124e-13 / 3.649e-13; L20 1.064e-13 / 2.658e-13; L30 5.324e-14 / 1.245e-13; S20 5.068e-14 / 1.223e-13.
7. **Start-up (INFO, M-5):** L20, T = 20, rows 0–3: out 0.5, 0.5632987004029524, 0.6999002012721725, 0.8320600073104027;
   Stoc 0.5, 1.0, 1.0, 1.0 (row 0 is the zero-range fallback). Source zero final seed (NCZ) vs library seed: max |diff|
   0.4367012995970475, last row with |diff| > 1e-12 = 59 (same for all 5 sines). **W = 700** (family default; >= 10× the
   measured start-up memory).
8. **M-1 shows only at T > L:** the 21-bar window (NCW) vs article, L20: <= 7.2e-14 at T = 5/10/20 (a 20-bar window spans
   whole cycles), 6.2e-2 / 8.1e-2 at T = 40 / 100. Record as [observations] O_WINDOW.
9. **D6 rule 5 not applicable:** no statics in MESAStochastic.c, RoofingFilter.c, HighPassFilter.c, SuperSmoother2Pole.c
   (all state per-call `series()`). Record in the spec; no shared-state control. The layout still runs every variant as its own
   instance every bar; IMP replays each against its own model.

## Tooling (D6 rules 1–4, extensions only)

- **Three outputs per call:** `MESAStochasticCore(S, L, HP, SS, &roof, &stoc)` returns `out`; raw columns `roof`, `stoc`, `out`
  per variant (same local-scalar out-parameter pattern as `62b4e97`). Linear checks read `roof`; trace and invariance read `out`;
  bound reads `stoc`.
- **Three-parameter variants** (`params = [L, HP, SS]`).
- **Two-sided bound:** `bound = [0.0, 1.0]`, PASS if every row lies in [lo − tol_abs, hi + tol_abs] with tol_abs = 1e-12 (spec
  value). The Reflex form (|r| <= b·(1 + rel)) must still work unchanged.
- **Trace gate on the model's range:** gate quantity = model (HH − LL)/amplitude (the model exposes its range per row); rows below
  g excluded and counted. A sine with every row gated = ERROR (as RFX).
- **Reference models** (restricted grammar, no eval): `mesa_article(L, hp, ss, win = None, scale = 1.0, fallback = 0.5,
  da_final = 0.0, literals = "exact" | "printed", final_seed = "first" | "zero")` simulated in Python with the library
  conventions above; `mesa_superseded(L, hp, ss)` = old file (window L+1, scale 100, fallback 50, same seeds). Roof part via
  the existing RFF cascade model (must agree with it to <= 1e-12). IMP_MODELS entries for every variant.
- Start-up rows (< W): INFO only; IMP replay on rows >= W.
- `[zorro].include`: `HighPassFilter.c`, `SuperSmoother2Pole.c`, `RoofingFilter.c`, `MESAStochastic_Superseded.c`,
  `MESAStochastic.c` (the last two are written in stage 2; lint may report them missing now — say so, do not create them).
- Existing specs (H1, SS2F, SS3F, HPF, RFF, USE, RFX) must regenerate BYTE-IDENTICAL scripts; their checker outputs unchanged.

## Corrected code (pre-registered lines; `.c` written AFTER the spec is committed)

```c
var MESAStochasticCore(vars Price, int StochPeriod, int HPPeriod, int SSPeriod, var* pRoof, var* pStoc)
{
    vars mstc_Roof = series(RoofingFilter(Price, HPPeriod, SSPeriod), StochPeriod);
    var mstc_HH = mstc_Roof[0];
    var mstc_LL = mstc_Roof[0];
    int mstc_i;
    for(mstc_i = 1; mstc_i < StochPeriod; mstc_i++) {
        if(mstc_Roof[mstc_i] > mstc_HH) mstc_HH = mstc_Roof[mstc_i];
        if(mstc_Roof[mstc_i] < mstc_LL) mstc_LL = mstc_Roof[mstc_i];
    }
    var mstc_Stoc = 1;
    mstc_Stoc = mstc_Stoc/2;
    if(mstc_HH != mstc_LL)
        mstc_Stoc = (mstc_Roof[0] - mstc_LL)/(mstc_HH - mstc_LL);
    vars mstc_S = series(mstc_Stoc, 3);
    var mstc_Out = SuperSmoother2Pole(mstc_S, SSPeriod);
    *pRoof = mstc_Roof[0];
    *pStoc = mstc_Stoc;
    return mstc_Out;
}

var MESAStochastic(vars Price, int StochPeriod, int HPPeriod, int SSPeriod)
{
    var mstc_r;
    var mstc_s;
    return MESAStochasticCore(Price, StochPeriod, HPPeriod, SSPeriod, &mstc_r, &mstc_s);
}
```
M-1 window StochPeriod bars; M-2 scale 0–1; M-6 fallback 0.5 built from a variable; both `series()` calls unconditional, before
any use (3.1); no expression starts with two literals (9d.8). Superseded file (stage 2): current `MESAStochastic.c` body verbatim
as `MESAStochastic_Superseded.c`, function `MESAStochastic_Superseded`, locals renamed `mstc_` -> `mstco_` (flat namespace, 1.3).
Pre-run (ii): record the current `MESAStochastic.c` blob hash. (c) If any line above cannot compile in Light-C, STOP and report.

## Spec draft: `analysis/harness/specs/MESA_ArticleFidelity.toml`

Same structure as `RFX_ArticleFidelity.toml` (incl. [corrected_code], [floor], [detect], [imp], [observations], pass condition,
pre-run i–iv). id_prefix `MST`. **Every number stored at full precision.**

Real variants (`MESAStochasticCore`, model `mesa_article`): `L14` (14,48,10), `L20` (20,48,10, source default), `L30` (30,48,10),
`S20` (20,48,20).
INFO variant (D1 rule 3): `NCL` article as printed (.707, 1.414, 3.14159 built from integers) in HP, roofing SS and final SS,
(20,48,10). (b) Roof gain 9.933e-05, phase 2.500e-04; trace 6.170885774015034e-05, 0.00016529770445106173,
0.00015804592943119422, 0.00027308494704969544, 0.0006127120163363919 (max 12×): reported, never PASS/FAIL.
INFO variant: `NCZ` source zero final seed (start-up only, finding 7).

Negative controls (vs the L20 model unless stated; inline bodies, every expression starts with a variable, locals uniquely
prefixed, constants like 1/1000 from a variable, 9d.8). Trace effects (b), T = 5, 10, 20, 40, 100:
- `NCW` window L+1 (M-1), 0–1 scale: 7.149836278586008e-14, 1.1213252548714081e-14, 4.218847493575595e-15,
  0.062068399419046405, 0.08053344297756188 (1611× at T = 100). Roof unchanged.
- `NCA` final-SS a1 + 1/1000 before b1, c3, c1 (third-digit copy error, D2 rule 4; Roof untouched): 0.0003776379364223148,
  0.0007941933349498442, 0.00038501894107612067, 0.00032719020964688816, 0.0003437934243362452 (15.9×).
- `NCP` real core called with HP = 40, compared with the (20,48,10) model and tables: trace 0.00733852860393025,
  0.018739743054289437, 0.05133688574154027, 0.18557033447408722, 0.4581797762979168; Roof gain 7.543e-02, phase 1.662e-01.
- `NC1` real core called with L = 22, compared with the L20 model: 1.2012613126444194e-13, 2.1760371282653068e-14,
  8.104628079763643e-15, 0.12681299399496013, 0.1561225037567811. Roof unchanged.
- `NCS` real superseded file `MESAStochastic_Superseded(S, 20, 48, 10)` vs the L20 model: 63.80040995412725, 83.74023037230494,
  97.33715039633475, 101.56627378951627, 101.85048633300102; bound fires (Stoc max 100.00000000000001).

Tolerances: Roof gain 3e-5, Roof phase 3e-5 rad, flat (Roof) 1e-9, ramp residual (Roof) 1e-9, **trace 5e-5**, **bound [0, 1]
tol_abs 1e-12**, invariance 1e-9, imp 1e-9, x 1e-12; gate **g = 0.01**; **W = 700**; phase gate 0.05. Check each against the measured
window (D2 rule 3); if one fails, STOP and report — do not pick a new value. Compute every [variants.effect] with the checker's own
functions. [detect.required] = every kind >= 10× its tolerance; compare with the (b) values above. If any control has NO kind
>= 10×, STOP and report.
IMP must_pass: every variant (incl. NCL, NCZ, NCS with the `mesa_superseded` model) on rows >= W; must_fail: L20 replayed with the
NCA model; NCS replayed with the L20 `mesa_article` model. Record fire-test values at full precision.

Pass condition: real-check count = 4 variants × [Roof: flat + 5 gains + alt gain + 5 phases (+ alt phase SKIP) + ramp residual
= 13; out: 5 trace + 2 invariance = 7; stoc: 1 bound] = **84** expected — state the exact number and explain any difference.

## Done when

- `bash analysis/harness/run_tests.sh` all PASS (report TOTAL before/after; 460 at main `8402fe3`) incl. new tests for three-output
  calls, three-parameter variants, two-sided bound (fires on a 1.0000001 row and on a -1e-9 row), trace gate on the model range
  (with a gated row), `mesa_article` vs findings 1–8, `mesa_superseded`, byte-identical regeneration of the 7 existing specs.
- `python analysis/harness/generator.py analysis/harness/specs/MESA_ArticleFidelity.toml --lint-only` clean (except the stage-2
  files, reported).
- Report: real-check count, raw column count, the Roof tables, findings 1–9 reproduced (diff vs the (b) values above), floors,
  every control's effects and [detect.required], NCL / NCZ INFO values, IMP fire-test values, anything that did not fit this
  prompt. Then STOP (no commit, no `.c` edit, no generated script run).
