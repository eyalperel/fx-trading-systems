# RFX stage 1 — oscillator-family tooling + reference models + spec draft (Reflex)

Planning chat, 2026-11-18. Decisions accepted by the user: R-1..R-5 (`docs/harness/REFLEX_SOURCE_REVIEW.md`, `05be788`),
HARNESS_DESIGN **D6** (oscillator-family check set, `5087c39`). Build mode, speed over polish, but the validation gate is
unchanged (CLAUDE.md). Labels: (a) source states, (b) measured/computed, (c) inference.

**Git:** branch `harness-rfx` (at `5087c39`). Do NOT commit. At the end print the `git add` / `git commit` commands you
suggest (one commit for tooling+tests, one for the spec draft), and STOP. No `.c` edit, no Zorro run.

## Source (a): Ehlers, "Reflex: A New Zero-Lag Indicator", TASC V.38:02 (2020), pp. 6–8, 21, sidebar "EasyLanguage Code For Reflex Indicator"

```
a1 = expvalue(-1.414*3.14159 / (.5*Length));
b1 = 2*a1*Cosine(1.414*180 / (.5*Length));
c2 = b1;  c3 = -a1*a1;  c1 = 1 - c2 - c3;
Filt = c1*(Close + Close[1]) / 2 + c2*Filt[1] + c3*Filt[2];
Slope = (Filt[Length] - Filt) / Length;
Sum = 0;  For count = 1 to Length Begin Sum = Sum + (Filt + count*Slope) - Filt[count]; End;
Sum = Sum / Length;
MS = .04*Sum*Sum + .96*MS[1];
If MS <> 0 Then Reflex = Sum / SquareRoot(MS);
```
Default Length 20. D1 rule 1: `1.414` -> sqrt(2), `3.14159` -> pi; degrees -> radians. D1 rule 2: `.5`, `.04`, `.96` literal.
Half length `.5*Length` is REAL (R-2). No start-up rule printed (R-4). Article claim: "exactly in phase with the data and
has zero lag" (cycle-plus-trend model).

## Planning-chat findings to record in the spec (b)

Independent code (numpy, own model: `.5*Length` real, exact sqrt2/pi, price seed; harness inputs level 1.1, sine amplitude
0.01, ramp slope 1e-4, alternating 1.1 ± 0.01, N = 3000; least-squares fit over rows >= 700). Reproduce with `reference.py`;
report any difference > 1e-12 (tables) or > 1% relative (effects).

1. **Sum is linear** (FIR on Filt): weights (L-1)/(2L) at lags 0 and L, -1/L at lags 1..L-1. H_Sum = G·H_SS(L/2),
   G = (L-1)/(2L)(1 + z^-L) - (1/L) Σ_{k=1}^{L-1} z^-k. DC gain 0 and a double zero at DC (ramp residual 0). Simulated Sum
   vs this H: ≤ 1.3e-14 (gain, amplitude-normalised) and 1.6e-14 rad (phase), L = 20, T = 5–100.
2. **Loop end terms are identically zero:** k = L gives (F0 + L·Slope) - F_L = 0; k = 0 would give 0 too. So a loop bound
   off by one at either end changes nothing (it is not a usable control). Matches (a) "the two endpoints … are not included".
3. **Sum tables** (gain / phase rad), T = 5, 10, 20, 40, 100:
   - L14: 0.3641008319826905, 0.08821484136366424, 0.9416369733401999, 0.3541421970554636, 0.06291300715458427 /
     -0.9041809919287164, -2.105367309115726, 0.5522448949496477, 1.853766288996129, 2.627294939010228
   - L20: 0.2241997820842597, 0.6950591600191403, 0.9661158676365323, 0.6334193273159906, 0.1261374255749415 /
     -1.853589240790186, -1.303784662009623, -0.6223438049722935, 1.276992794392404, 2.398116923276429
   - L21: 0.1575089085020519, 0.598161031431481, 0.9030766266744574, 0.6793377458187358, 0.1385289322235242 /
     -2.516715492980711, -1.684589130000405, -0.8200519928703117, 1.180259661445638, 2.359782085656642
   - L30: 0.1020866755606767, 0.3992220894808521, 0.1826694165145904, 0.9957600998886519, 0.2702131435617495 /
     -2.089593977937582, -1.820435239811435, 0.5327175540190705, 0.3032513983296208, 2.013718620121099
   - Alternating input: |H_Sum| ≤ 1.3e-17 (H_SS has a zero at Nyquist): alt gain expected 0, alt phase SKIP (gate).
4. **"Zero lag" (INFO, [observations] O_ZEROLAG):** G(T = L) = 1 exactly (phase 0), so Sum's phase at T = L is the
   SuperSmoother(L/2) phase: -0.5798402196411705 (L14), -0.6223438049722935 (L20), -0.6276271518404849 (L21),
   -0.66162649242601 (L30) rad. Normalisation keeps the phase, so (b) Reflex lags ≈ 0.62 rad (≈ 2 bars at L = 20) at the
   assumed cycle period; the article's zero-lag statement holds for the slope/summation stage, not for the smoothed output.
5. **Ramp ill-conditioning (D6 evidence):** article model, L20: max |Reflex| over rows >= 700 on the ramp = 2.857 (Sum ~3e-17,
   sqrt(MS) 1.3e-10 at row 700, 1.4e-16 at row 1500). Flat gave exactly 0. Flat/ramp Reflex rows are INFO only.
6. **Bound:** |Reflex| ≤ 5 exactly (MS >= 0.04·Sum²); **attained**: max over all rows, all inputs, 4 real L = 5.000000 (first
   non-zero Sum, MS = 0.04·Sum²). The bound check needs a few-ulp allowance (below).
7. **Gate margin:** min sqrt(MS)/amplitude over sine rows >= 700: L14 0.0370, L20 0.0741, L21 0.0814, L30 0.0715.
8. **Warmup:** MS memory 0.96^n < 1e-12 after 676.87 bars: W = 700.
9. **Floors, Zorro `PI` = float32(3.14159) vs pi** (gain / phase rad / trace = max |ΔReflex| rows >= 700 over the 5 sines):
   L14 4.660e-07 / 9.037e-07 / 1.242e-06; L20 5.609e-07 / 1.103e-06 / 1.570e-06; L21 5.296e-07 / 1.101e-06 / 1.554e-06;
   L30 5.380e-07 / 1.003e-06 / 1.435e-06. Floor×10 ≤ 3e-5 on all three quantities.
10. **Old float32 weights (R-3), INFO only:** float32(0.04), float32(0.96) vs exact: trace effect 4.424e-07 (L20), below the `PI`
    floor. Not a control (cannot meet 10×); record as information.
11. **Invariance (float64 model, L20, 5 sines, rows >= 700):** amplitude ×10 (0.1) max |ΔR| 7.040e-13; level 2.2 1.180e-12.

## Tooling (D6 rules 1–5)

- **Multi-output indicator calls:** generator emits `ReflexCore(S, L, &sum, &ms)` and writes three raw columns per variant
  (`sum`, `ms`, `r`). Spec grammar: a variant declares `outputs = ["sum", "ms", "r"]`; which output each check family reads is
  declared in the spec (linear checks -> `sum`; trace/bound/invariance -> `r`).
- **New quantity `trace`:** max |Zorro r - model r| over rows >= W, per sine input, rows with sqrt(ms)/amplitude < gate excluded
  (count gated rows; report). Model = the variant's article model with the same input built in Python.
- **New quantity `bound`:** max over every row of every input of |r|, PASS if ≤ bound·(1 + bound_rel_tol).
- **New quantity `invariance`:** Zorro-internal: max |r(input) - r(transformed input)| over rows >= W, all 5 sines; transforms
  `scale10` (amplitude 0.1, level 1.1) and `offset` (level 2.2, amplitude 0.01). Extra inputs built from integers at run time
  (9d.1); copies of every sine, fed to every real variant.
- **Reference models** (restricted grammar, no eval): `reflex_article(L, half = None, w1 = 0.04, w2 = 0.96, ...)` simulated in
  Python (price seed for Filt history, MS starts 0); `reflex_superseded(Ls)` = old `Reflex.c` (integer half length via the
  SS2 code, ONE MS shared by the listed instances in call order; replay must follow the generator's call order). IMP_MODELS
  entries for every variant.
- **Start-up rows** (0–5 and up to W): INFO only (R-4); IMP replay on rows >= W.
- `[zorro].include`: `SuperSmoother2Pole.c` (needed by the superseded control) then `Reflex_Superseded.c` then `Reflex.c`
  (the last two are written in stage 2; lint may report them missing now — say so, do not create them).
- Existing specs (H1, SS2F, SS3F, HPF, RFF, USE) must regenerate BYTE-IDENTICAL scripts; their checker outputs unchanged.

## Corrected code (pre-registered lines; `.c` written AFTER the spec is committed)

```c
var ReflexCore(vars Price, int Length, var* pSum, var* pMS)
{
    var rx_half = Length;
    rx_half = rx_half/2;
    var rx_k = sqrt(2.0);
    var rx_a1 = exp(-rx_k*PI/rx_half);
    var rx_b1 = 2.0*rx_a1*cos(rx_k*PI/rx_half);
    var rx_c2 = rx_b1;
    var rx_c3 = -rx_a1*rx_a1;
    var rx_c1 = 1.0 - rx_c2 - rx_c3;
    var rx_w1 = 4;
    rx_w1 = rx_w1/100;
    var rx_w2 = 96;
    rx_w2 = rx_w2/100;
    vars rx_Filt = series(Price[0], Length + 2);
    vars rx_MS = series(0, 2);
    rx_Filt[0] = rx_c1*(Price[0] + Price[1])/2.0 + rx_c2*rx_Filt[1] + rx_c3*rx_Filt[2];
    var rx_Slope = (rx_Filt[Length] - rx_Filt[0])/Length;
    var rx_Sum = 0;
    int rx_i;
    for(rx_i = 1; rx_i <= Length; rx_i++)
        rx_Sum += (rx_Filt[0] + rx_i*rx_Slope) - rx_Filt[rx_i];
    rx_Sum = rx_Sum/Length;
    rx_MS[0] = rx_w1*rx_Sum*rx_Sum + rx_w2*rx_MS[1];
    var rx_R = 0;
    if(rx_MS[0] > 0)
        rx_R = rx_Sum/sqrt(rx_MS[0]);
    *pSum = rx_Sum;
    *pMS = rx_MS[0];
    return rx_R;
}

var Reflex(vars Price, int Length)
{
    var rx_s;
    var rx_m;
    return ReflexCore(Price, Length, &rx_s, &rx_m);
}
```
R-1 per-instance `rx_MS` series; R-2 real half length; R-3 weights from integers; both `series()` unconditional, before any
use (3.1); no expression starts with two literals (9d.8). Superseded file (stage 2): current `Reflex.c` body verbatim as
`Reflex_Superseded.c`, function `Reflex_Superseded`, locals/static renamed `rx_` -> `rxo_` (flat namespace, 1.3).
Pre-run (ii): record the current `Reflex.c` blob hash. (c) If any line above cannot compile in Light-C, STOP and report.

## Spec draft: `analysis/harness/specs/RFX_ArticleFidelity.toml`

Same structure as `USE_ArticleFidelity.toml` (incl. [corrected_code], [floor], [detect], [imp], [observations], pass condition,
pre-run i–iv). id_prefix `RFX`. **Every number stored at full precision.**

Real variants (`ReflexCore`, model `reflex_article(L)`): `L14`, `L20` (source default), `L21` (odd, R-2), `L30`.
INFO variant (D1 rule 3): `NCL` article as printed (1.414, 3.14159 built from integers), L20. (b) Sum gain 1.056e-04,
phase 2.075e-04, trace 2.955e-04 (3.5× / 6.9× / 9.9× of 3e-5): reported, never PASS/FAIL.

Negative controls (L20 unless stated; inline bodies, every expression starts with a variable, locals uniquely prefixed,
constants like 1/1000 from a variable, 9d.8):
- `NCA` a1 + 1/1000 before b1, c3, c1. (b) Sum gain 6.026e-04 (20×), phase 2.320e-03 (77×), trace 3.303e-03 (110×).
- `NC2` cosine argument in degrees (sqrt(2)·180/half). (b) Sum gain 1.710e-01, phase 1.858e-01, trace 2.647e-01.
- `NC1` L = 22 vs the L20 tables/model. (b) Sum gain 2.399e-01, phase 1.323, trace 1.742.
- `NCH` integer half length at L = 21 (SS period 10, the old R-2 behaviour) vs L21. (b) Sum gain 3.140e-02, phase 6.665e-02,
  trace 9.348e-02.
- `NCK` divisor L-1 (Sum = sum/19). (b) Sum gain 5.084820e-02 (1695×); **trace 0** (normalisation cancels a scale error):
  detected by Sum only (D6 rule 1 evidence; record in [observations]).
- `NCW` weights 0.041 / 0.959 (built from integers). (b) Sum unchanged; trace 5.096e-03 (170×).
- `NCS` real superseded file: `Reflex_Superseded` called as TWO instances, L20 then L14, each compared with its own
  `reflex_article` model. (b) trace L20 5.161e-01, L14 1.142 (shared MS, R-1).

Tolerances: Sum gain 3e-5, Sum phase 3e-5 rad, flat (Sum) 1e-9, ramp residual (Sum) 1e-9, **trace 3e-5** (new quantity;
default proposed here, recorded in HARNESS_DESIGN under D2 rule 1 when the spec is committed), **bound 5 with
bound_rel_tol 1e-12**, **invariance 1e-9**, imp 1e-9, x 1e-12; gate **g = 0.01** (judgement (c); min margin 0.037, finding 7);
**W = 700**; phase gate 0.05. Check each against the measured window (D2 rule 3); if one fails, STOP and report — do not pick
a new value. Compute every [variants.effect] with the checker's own functions. [detect.required] = every kind >= 10× its
tolerance; compare with the (b) values above. If any control has NO kind >= 10×, STOP and report.
IMP must_pass: every variant (incl. NCL, NCS with the `reflex_superseded` model) on rows >= W; must_fail: L20 replayed with the
NCW model; NCS L20 replayed with the L20 `reflex_article` model. Record fire-test values at full precision.

Pass condition: real-check count = 4 variants × [Sum: flat + 5 gains + alt gain + 5 phases (+ alt phase SKIP) + ramp residual
= 13; Reflex: 5 trace + 1 bound + 2 invariance = 8] = **84** expected — state the exact number and explain any difference.

## Done when

- `bash analysis/harness/run_tests.sh` all PASS (report TOTAL before/after; 361 at main 683b05b) incl. new tests for
  multi-output calls, trace (with a gated row), bound (fires on a 5.0000001 row), invariance (fires on an unnormalised copy),
  `reflex_article` vs findings 1–3, shared-state replay, byte-identical regeneration of the 6 existing specs.
- `python analysis/harness/generator.py analysis/harness/specs/RFX_ArticleFidelity.toml --lint-only` clean (except the
  stage-2 files, reported).
- Report: real-check count, raw column count, the Sum tables, findings 1–11 reproduced (diff vs the (b) values above), floors,
  every control's effects and [detect.required], NCL INFO values, IMP fire-test values, anything that did not fit this
  prompt. Then STOP (no commit, no `.c` edit, no generated script run).
