# FSH stage 1 — tooling + reference models + spec draft (Fisher Transform)

Planning chat, 2026-11-19. Decisions accepted by the user: source A + F-1..F-9 (`docs/harness/FISHER_SOURCE_REVIEW.md`, `bdc83da`),
HARNESS_DESIGN **D6** (oscillator family, fourth indicator). Real variants FR10 / FR20, controls as listed. Build mode, speed over
polish; the validation gate is unchanged (CLAUDE.md). Labels: (a) source states, (b) measured/computed, (c) inference.
Run on **Opus, effort High**.

**Git:** branch `harness-fisher` (at `bdc83da`, created by the user). Do NOT commit. At the end print the `git add` / `git commit`
commands you suggest (one commit for tooling + tests + this brief, one for the spec draft), and STOP. No `.c` edit, no Zorro run.

Read first: `docs/harness/FISHER_SOURCE_REVIEW.md` (all of it), `docs/harness/FISHER_REVIEW_MODEL.py`, HARNESS_DESIGN D6 and the
three "D6 applied to ..." notes, `analysis/harness/specs/LRSI_ArticleFidelity.toml` (structure to follow), gotchas 9d.1, 9d.6,
9d.8, 9d.9.

## Source (a): Ehlers, "Using The Fisher Transform", TASC V.20:11 (2002), Fig. 5, p. 41

```
Inputs:  Price((H+L)/2), Len(10);
Vars:    MaxH(0), MinL(0), Fish(0);
MaxH=Highest(Price,Len);
MinL=Lowest(Price,Len);
Value1 = .33*2*((Price-MinL)/(MaxH-MinL)-.5)+.67*Value1[1];
If Value1 > .99 then Value1= .999;
If Value1 <-.99 then Value1=-.999;
Fish = .5*Log((1+Value1)/(1-Value1)) + .5*Fish[1];
Plot1(Fish, "Fisher");
Plot2(Fish[1], "Trigger");
```
Value1 and Fish start at 0. No start-up rule (F-5: INFO). Division by zero when MaxH = MinL is unguarded in the source; the
corrected code keeps OUR guard raw = 0 (F-4), so flat is an implementation known answer, not a source check. No trig, no `PI`.
D1: every literal is taken at its decimal value (rule 2; none equals a named constant), built from integers at run time (F-3).
**No NCL variant** (no rule-1 / rule-4 replacement exists): state this in the spec.
INFO variant source (a): *Cybernetic Analysis* (2004) Fig. 1.7, p. 7: `.5 / .5` EMA, clamp `.9999 / .9999`, log gain `.25`.

## Planning-chat numbers to reproduce (b)

Independent float64 model (`docs/harness/FISHER_REVIEW_MODEL.py` + this list). Inputs as LRS: level 1.1, amplitude 0.01, slope
1e-4, N = 3000, sines T = 5, 10, 20, 40, 100, ramp, rampdn, flat. Window: Highest / Lowest over the last Len values incl. [0];
before Len values exist the history is padded with x[0] (Zorro `series()`, gotchas 9d.6; (c) to be confirmed by trace and
start-up). Rows >= W = 700 unless stated. Reproduce with `reference.py`; report any difference > 1e-12 (values) or > 1%
relative (effects).

1. **Exact bounds:** raw in [-1, 1]; |v1| <= .999 (no value in (.99, .999)); |Fish| < ln(1999) = 7.6004023345004
   (approached, not attained). Max observed, rows >= W: FR10 T100 |Fish| 7.6004023343329665; FR20 T100 7.60040233312112.
2. **Gate margins** (model, rows >= W), T = 5, 10, 20, 40, 100:
   - range / amplitude, FR10: 1.9021130325901803, 1.902113032590269, 0.9999999999998677, 0.2928932188134059,
     0.048943483704833035; FR20: 1.9021130325902247, 1.9021130325902913, 2.0000000000000018, 0.9999999999999343,
     0.1909830056250339.
   - **new:** min |pre-clamp v1 -/+ .99|, FR10: 0.6608611703239821, 0.4309496019031033, 0.08902642427836405,
     0.0016393018220295374, 0.0011989375189954687; FR20: 0.6608611703239828, 0.4309496019031033, 0.20473557299332135,
     0.0017189627979685707, 0.0007121303005288571.
   - Gates: g = 0.01 on range / amplitude (D6 default; applies to raw, v1, Fish); **g2 = 1e-6 on the clamp distance**
     (judgement (c); applies to v1 and Fish: a rounding flip of the clamp makes Fish jump by
     atanh(.999) - atanh(.99) = 1.1535487548879537). Expected gated rows: 0.
3. **Fish range** rows >= W (review §3, rows >= 200, should be unchanged): FR10 ±0.943519 at T = 10, ±2.614129 at T = 20,
   ±7.421263 at T = 40; T = 5 asymmetric -0.333957..+0.352907.
4. **Ramps (L10 and L20):** raw = +1 / -1 exactly (rising / falling) from row 1; v1 = +.999 / -.999 exactly from row 12 (L10);
   Fish -> ±ln(1999), within 1e-12 from row 53 (L10). Measure the L20 rows.
5. **Flat:** guard fires on every row; raw = v1 = Fish = 0 exactly.
6. **Invariance** (rows >= W, 5 sines), scale10 (amp 0.1) / offset (level 2.2), max |dFish|: FR10 2.6565416533230746e-12 /
   5.31930055558405e-12; FR20 5.32018873400375e-13 / 1.0578204978628492e-12.
7. **Start-up memory** (INFO, F-5): Value1 .67^n < 1e-12 from n = 69; Fish .5^n from n = 40; plus the Len window. W = 700
   (family default). Measure and record the start-up rows vs the model as INFO.
8. **Floor.** No `PI`, no float32 literal in the corrected code: (c) Zorro vs the model expected at rounding level (LRS ~5e-16).
   IMP replays the exported %.15f x, whose rounding is divided by the range (down to ~4.9e-4) and amplified by atanh' (up to
   ~50 near .99): (c) IMP residual up to ~1e-11. Measure both.

## Tolerances (pre-registered here; check each against D2 rule 3)

- **trace 1e-9** on raw, v1 and Fish (not the D6 default 3e-5). Reason: no `PI` gap, expected floor <= ~1e-11; 3e-5 would leave
  NC32 (the float32 literals of the current file, F-3, effect 1.288113e-05) undetectable, so F-3 would be unverified. If the
  measured floor x 10 > 1e-9, STOP and report.
- bound: tol_abs 1e-12 on raw and v1; Fish one-sided relative allowance 1e-12 on ln(1999) (D6 default).
- `ramp_exact` 1e-12 (raw = ±1, v1 = ±.999 exactly; Fish vs the model's ramp value, also report |Fish - ln(1999)|).
- invariance 1e-9 (floor 5.3e-12 x 10 = 5.3e-11).
- flat 1e-12 (all three = 0). trigger 0 (exact: trig[n] must equal out[n-1] bit for bit). imp 1e-9. x 1e-12. start-up INFO.

## Tooling (extensions only)

- **Five columns per call:** `FisherCore(S, Len, &raw, &v1, &rng, &trig)` returns `out` (Fish); raw columns `raw`, `v1`, `rng`,
  `trig`, `out` per variant (generalise the LRS four-column pattern, local-scalar out-parameters, `62b4e97`).
- **Trace on several outputs** with per-output gates: raw (range gate), v1 and out (range + clamp-distance gate). Gates on the
  MODEL's values; gated rows counted; all rows of a sine gated = ERROR.
- **Bounds:** two-sided on raw ([-1, 1]) and v1 ([-.999, .999]); |out| < ln(1999) with relative allowance.
- **New kind `trigger`:** trig[n] == out[n-1] exactly for n >= 1, every input (Zorro-internal, no model).
- **`flat_zero`** on raw, v1, out (one check per variant).
- `ramp_exact` on raw and v1 (rising and falling) and on out vs the model.
- **Reference models** (restricted grammar, no eval): `fisher_article(L, a = [33,100], b = [67,100], thr = [99,100],
  cl = [999,1000], k = [1,2], literals = "exact" | "float32")` — rationals given as integer pairs; `literals = "float32"`
  reproduces the current file's literals (NC32). `fisher_superseded(L)` = the old file incl. its FILE STATICS (`ft_Value1`,
  `ft_Fish`, global `ft_Trigger`) shared by every call, in the generator's ACTUAL call order (RFX / LRS shared-state replay),
  with float32 literals.
- `[zorro].include`: `FisherTransform_Superseded.c`, `FisherTransform.c` (stage 2; lint may report them missing — say so, do not
  create them). `[lint].no_static` on the corrected `FisherTransform.c` (the LRS lint; must fire on the superseded body: 2 hits,
  `ft_Value1`, `ft_Fish`).
- Existing specs (H1, SS2F, SS3F, HPF, RFF, USE, RFX, MST, LRSI) must regenerate BYTE-IDENTICAL scripts; checker outputs unchanged.

## Corrected code (pre-registered; `.c` written in stage 2, AFTER the spec is committed)

```c
var FisherCore(vars Price, int Len, var* pRaw, var* pV1, var* pRng, var* pTrig)
{
    vars fi_V = series(0, 2);
    vars fi_F = series(0, 2);
    var fi_a = 33;   fi_a = fi_a/100;
    var fi_b = 67;   fi_b = fi_b/100;
    var fi_t = 99;   fi_t = fi_t/100;
    var fi_c = 999;  fi_c = fi_c/1000;
    var fi_h = 1;    fi_h = fi_h/2;
    var fi_hi = MaxVal(Price, Len);
    var fi_lo = MinVal(Price, Len);
    var fi_rng = fi_hi - fi_lo;
    var fi_raw = 0;
    if(fi_rng > 0) {
        fi_raw = Price[0] - fi_lo;
        fi_raw = fi_raw/fi_rng;
        fi_raw = fi_raw - fi_h;
        fi_raw = fi_raw*2;
    }
    fi_V[0] = fi_a*fi_raw + fi_b*fi_V[1];
    var fi_nt = 0;   fi_nt = fi_nt - fi_t;
    var fi_nc = 0;   fi_nc = fi_nc - fi_c;
    if(fi_V[0] > fi_t)  fi_V[0] = fi_c;
    if(fi_V[0] < fi_nt) fi_V[0] = fi_nc;
    var fi_u = 1;
    var fi_num = fi_u + fi_V[0];
    var fi_den = fi_u - fi_V[0];
    fi_F[0] = fi_h*log(fi_num/fi_den) + fi_h*fi_F[1];
    *pRaw  = fi_raw;
    *pV1   = fi_V[0];
    *pRng  = fi_rng;
    *pTrig = fi_F[1];
    return fi_F[0];
}

var FisherTransform(vars Price, int Len)
{
    var fi_w1;
    var fi_w2;
    var fi_w3;
    var fi_w4;
    return FisherCore(Price, Len, &fi_w1, &fi_w2, &fi_w3, &fi_w4);
}
```
F-1 per-instance state (both `series()` calls unconditional and first, 3.1; zero start = the source's Value1(0) / Fish(0));
F-2 `Price` is a parameter (callers pass `series((priceHigh() + priceLow())/2)`); F-3 every constant built from integers; F-4
guard kept; every expression starts with a variable (9d.8; `fi_raw*2` is variable-first). (b) The model computes raw as
`2*((x - lo)/rng - .5)`; the code's step order is the same arithmetic in the same order: IMP must pass at 1e-9.
(c) If any line above cannot compile in Light-C, STOP and report.
**Callers (F-2):** grep the repo for `FisherTransform(` and `ft_Trigger`; list every caller with file:line in the report. Do not
edit them (stage 2 updates them).
**Superseded file (stage 2):** current `FisherTransform.c` body as `FisherTransform_Superseded.c`, function
`FisherTransform_Superseded(vars Price, int Period)`; the ONLY behavioural edit is the input: line 42's `series((priceHigh() +
priceLow()) * 0.5)` replaced by the `Price` parameter (needed to feed synthetic inputs; statics, literals, guard, clamp, trigger
global unchanged). Locals / statics / global prefix `ft_` -> `fto_` (flat namespace, 1.3). Pre-run (ii): record the current
`FisherTransform.c` blob hash.

## Spec draft: `analysis/harness/specs/FSH_ArticleFidelity.toml`

Same structure as `LRSI_ArticleFidelity.toml` (incl. [corrected_code], [floor], [detect], [imp], [observations], pass condition,
pre-run i–iv, the restart-Zorro rerun rule). id_prefix `FSH`. **Every number stored at full precision.**

Real variants (`FisherCore`, model `fisher_article`): `FR10` (Len 10, the C1 slot value), `FR20` (Len 20).
INFO variant: `NCB` the book (Fig. 1.7), Len 10: a = b = [1,2], thr = cl = [9999,10000], k = [1,4]. Effect vs FR10 (Fish), T = 5,
10, 20, 40, 100: 7.980366e-02, 3.066436e-01, 9.611960e-01, 2.628208e+00, 2.709052e+00. Reported, never PASS/FAIL.

Negative controls (vs the FR10 model; inline bodies, every expression starts with a variable, locals uniquely prefixed). Effects
(b), max |diff| rows >= W, T = 5, 10, 20, 40, 100 (Fish / v1 / raw):
- `NCW` .331 in place of .33 (third-digit copy error, D2 rule 4): Fish 1.147197e-03, 3.620501e-03, 2.325973e-02, 1.300183e+00,
  1.304496e+00; v1 9.973904e-04, 1.694092e-03, 2.730223e-03, 1.063930e-02, 1.075769e-02; raw 0. Ramp v1 still .999.
- `NCC` clamp set value = trigger (.99 / .99): Fish 0, 0, 0, 2.162821e+00, 2.307098e+00; v1 0, 0, 0, 9.0e-03, 9.0e-03; raw 0.
  Ramp: v1 = .99, Fish -> 5.2933048247244905 (ramp_exact also fires).
- `NCK` log gain .25 (the book's): Fish 1.764535e-01, 4.717597e-01, 1.307064e+00, 3.710631e+00, 3.800201e+00; v1, raw 0.
  Ramp Fish -> 3.8002011672502.
- `NCL` window Len + 1 (11): Fish 8.232304e-14, 5.173639e-14, 1.959533e-01, 3.303457e-01, 1.210467e+00; v1 6.700196e-14,
  3.086420e-14, 1.344059e-01, 1.594356e-01, 1.663479e-01; raw 2.101652e-13, 9.348078e-14, 3.262379e-01, 3.774946e-01,
  3.890338e-01. **(b) Invisible at T <= L** (MST finding 1); seen only at T = 20 / 40 / 100.
- `NC32` the current file's float32 literals (.33, .67, .99, .999), per-instance state: Fish 1.395721e-08, 5.860322e-08,
  5.316101e-07, 1.242011e-05, 1.288113e-05; v1 1.253569e-08, 2.932536e-08, 6.981766e-08, 8.570537e-08, 8.566314e-08; raw 0.
  At trace tol 1e-9: 1.3e4x. This control is what makes F-3 a checked fix.
- `NCS` the real superseded file, called as TWO instances per input, both Len 10 (D6 rule 5). Compute its effects with the
  shared-state replay **in the generator's actual call order** and report, per (instance, input), which rows differ from the FR10
  model and by how much. (b) Planning chat, two instances (L10, L20) sharing state on one sine: 0.707983 / 2.692527 / 2.695127
  (T = 20 / 40 / 100, rows >= 200); (c) with every call of the run chained through one state the effect should be large on
  every sine, on rows >= W (unlike LRS: the shared state here is the IIR state itself, not a one-shot seed). If NCS differs from
  the model only on rows < W or only on flat, STOP and report (do not change the layout or add a check).

[detect.required] = every kind >= 10x its tolerance; compare with the (b) values above. If any control has NO kind >= 10x, STOP.
IMP must_pass: every variant (incl. NCB with its model, NCS with `fisher_superseded`) on rows >= W; must_fail: FR10 replayed with
the NCW model; NCS replayed with the FR10 `fisher_article` model. Record fire-test values at full precision.

Pass condition: real-check count = 2 variants x [raw: 5 trace + 1 bound + 2 ramp_exact = 8; v1: 5 trace + 1 bound + 2 ramp_exact
= 8; out: 5 trace + 2 invariance + 1 bound + 2 ramp_exact + 1 trigger = 11; flat_zero 1] = **56** expected — state the exact
number and explain any difference. Start-up rows: INFO.

## Done when

- `bash analysis/harness/run_tests.sh` all PASS (report TOTAL before/after; 657 at `f3f85ef`) incl. new tests for five-column calls,
  trace on several outputs with per-output gates, the clamp-distance gate (with a gated row), bounds on raw / v1 / out, `trigger`
  (fires on a one-row shift), `flat_zero` (fires on 1e-9), `fisher_article` vs findings 1–8, `fisher_superseded` with shared
  statics, the no-static lint on the superseded body (2 hits), byte-identical regeneration of the 9 existing specs.
- `python analysis/harness/generator.py analysis/harness/specs/FSH_ArticleFidelity.toml --lint-only` clean (except the stage-2
  files, reported).
- Report (write it as `docs/harness/FSH_STAGE1_REPORT.md`): real-check count, raw column count, findings 1–8 reproduced (diff vs
  the (b) values above), floors and the tolerance window per quantity, every control's effects and [detect.required], the NCS
  per-(instance, input) result, NCB INFO values, IMP fire-test values, the caller list (F-2), anything that did not fit this
  prompt. Then STOP (no commit, no `.c` edit, no generated script run).
