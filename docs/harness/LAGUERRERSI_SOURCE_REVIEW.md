# Laguerre RSI — source review (code vs book)

**Date:** 2026-11-19 (planning chat). **Status:** review complete, decisions taken (user, 2026-11-19: all as proposed). No spec yet.
**File reviewed:** `indicators/ehlers/LaguerreRSI.c` (5910 bytes, mtime 2026-08-21). No dependencies: the four Laguerre
stages are computed inline. `indicators/ehlers/Laguerre.c` (the filter, Fig. 14.5) is **not** called by it (§5).
**Source:** Ehlers, J.F., *Cybernetic Analysis for Stocks and Futures* (Wiley 2004), ch. 14 "Time Warp — Without Space
Travel": text p. 220-221 and p. 225; **Fig. 14.8 "EasyLanguage Code to Compute a Laguerre RSI Indicator", p. 221**;
Fig. 14.9 (EFS version, coded by C. D. Kryza, pp. 222-224) as a cross-check. Read from the page images (book PDF pages
240-245), not only the text layer. Book PDF: `C:/books/Cybernetic Analysis for Stocks and Futures ... (John F. Ehlers) ...pdf`.
**Not the source:** `Laguerre Filters.pdf` (TASC V.43:07, 2025) has a Laguerre filter (UltimateSmoother L0, five stages)
and a Laguerre Oscillator, no RSI (searched, 2026-11-19).
**Context:** PROJECT_STATE §7 step 3, oscillator harness family (HARNESS_DESIGN D6), third indicator after Reflex and
MESAStochastic. Laguerre RSI (gamma 0.5) is the C2 candidate of Strategy 2 (§1.2), same 0-1 scale as MESA (C1, Strategy 2).
**Model:** every (b) number below is reproduced by `docs/harness/LAGUERRERSI_REVIEW_MODEL.py` (float64, independent of
the harness tooling).

Labels: (a) source states · (b) read or computed here · (c) inference.

---

## 1. Source formula (a)

Fig. 14.8, p. 221:

```
Inputs:  gamma(.5);
Vars:    L0(0), L1(0), L2(0), L3(0), CU(0), CD(0), RSI(0);

L0 = (1 - gamma)*Close + gamma*L0[1];
L1 = - gamma *L0 + L0[1] + gamma *L1[1];
L2 = - gamma *L1 + L1[1] + gamma *L2[1];
L3 = - gamma *L2 + L2[1] + gamma *L3[1];

CU = 0;
CD = 0;
If L0 >= L1 then CU = L0 - L1 Else CD = L1 - L0;
If L1 >= L2 then CU = CU + L1 - L2 Else CD = CD + L2 - L1;
If L2 >= L3 then CU = CU + L2 - L3 Else CD = CD + L3 - L2;

If CU + CD <> 0 then RSI = CU / (CU + CD);

Plot1(RSI, "RSI");
Plot2(.8);
Plot3(.2);
```

(a) Input `Close`. Only `gamma` is an input ("you can adjust the damping factor to best suit your own data", p. 221).
(a) All variables start at 0. No start-up rule (no `CurrentBar` clause). When `CU + CD = 0` there is no else: `RSI` keeps its
previous value (EasyLanguage variables persist bar to bar); before the first defined value it is the declared 0.
(a) Fig. 14.9 (EFS) has the same arithmetic, initialises every array to 0.0, and also holds `nRSI` (initial 0) when
`nCU + nCD == 0`. It agrees with Fig. 14.8 on every point above.
(a) Output 0-1; reference lines .8 / .2. Text p. 220: RSI = 100 CU/(CU + CD), i.e. the same ratio in percent.
(a) Use, p. 221 and p. 225: excursions "typically lock to lock" (Fig. 14.10); "buy after the line crosses back over the
20 percent level and sell after the price crosses back down over the 80 percent level". (c) "the price" in the sell rule is
probably a slip for "the line".
(a) Key points p. 225: the Laguerre transform delays low-frequency components much more than high-frequency ones.

## 2. Line-by-line comparison

| Stage | Source (a) | `.c` (b) | Verdict |
|---|---|---|---|
| L0 | `(1 - gamma)*Close + gamma*L0[1]` | line 94, same | Matches |
| L1..L3 | `-gamma*L(k-1) + L(k-1)[1] + gamma*Lk[1]` (current upstream first, previous second) | lines 95-97, same | Matches |
| CU / CD | adjacent pairs, `>=` to CU, else CD | lines 100-110, same | Matches |
| Output | `CU/(CU + CD)`, 0-1 | line 133 | Matches |
| Start-up | all histories 0; first bar computed | `static int lr_init`: on the first call with `Close[0] > 0` every stage and its `[1]` = Close, the bar is **not computed**, returns 0.5 (lines 77-86) | **L-1** |
| Zero denominator | holds previous RSI; initial 0 | holds `static var lr_prevRSI`; initial 0.5 (lines 128-131) | **L-2** |
| State scope | per instance (EasyLanguage vars) | L0..L3 per-call `series()` (correct); `lr_init` and `lr_prevRSI` **file statics shared by every call** | **L-3** |
| Literals | — | `(1.0 - gamma)`: one exact literal minus a variable, run time; no literal products or divisions | OK (gotchas 9d.8). gamma is the caller's: **L-4** |
| Linear stage | — | not exported | **L-5** |
| Header | — | "Returns 0.5 when CU+CD is zero" contradicts the code (holds); P-LR1 and the "2025 code is a lowpass" note unlabelled | **L-6** |
| Input | `Close` | `vars Close` (any series) | Matches |

## 3. Start-up and behaviour — measured (b)

Float64 model, inputs as SS2F / MST: level 1.1, sine amplitude 0.01, ramp slope 1e-4, 3000 bars; gamma 0.5 / 0.7 / 0.8.
"Rows >= 200" are past every start-up effect below.

**Start-up, `.c` vs source** (max |diff|; last row with |diff| > 1e-12):

| T | gamma 0.5 | gamma 0.7 | gamma 0.8 |
|---|---|---|---|
| 5 | 0.5979633949986088; row 60 | 0.6812708208044844; row 120 | 0.7301352018278088; row 195 |
| 10 | 0.9392821926106899; row 59 | 0.5660045731216486; row 118 | 0.6546895781210033; row 191 |
| 20 | 0.9233174011464185; row 61 | 1.0; row 118 | 0.6790486110173588; row 191 |
| 40 | 0.6160813372907071; row 58 | 0.9251706928084463; row 105 | 1.0; row 193 |
| 100 | 0.2142857142857142; row 33 | 0.43561586004909875; row 91 | 0.7923391382953764; row 196 |

Zero-start memory of the last stage on a flat input (|L3 - level|/level < 1e-12 from): row 56 / 109 / 174.
(b) After the start-up rows the `.c` and the source are identical. (c) Earlier C-1..C-5 measurements read after warmup are
unaffected by L-1; not checked here.

**Sines, rows >= 200** (source model): output range, share of rows pinned at exactly 0 or 1, min (CU + CD)/amplitude:

| T | gamma 0.5 | gamma 0.7 | gamma 0.8 |
|---|---|---|---|
| 5 | 0.4339445777191289..0.5660554222808636; 0; 1.5444174181677983 | 0.3600797562272267..0.6399202437727484; 0; 0.5261922807346053 | 0.34380966903890214..0.6561903309608068; 0; 0.31807224827549163 |
| 10 | 0.158366518074627..0.841633481925382; 0; 1.5613948955003787 | 0.47873214186753515..0.5212678581324689; 0; 1.5640737397439874 | 0.3874147366738073..0.6125852633262958; 0; 0.8264689338118414 |
| 20 | 0..1; 0.50; 1.2521910177791584 | 0..1; 0.10; 1.2212991432978937 | 0.4050137059950745..0.5949862940049255; 0; 1.5603221435723125 |
| 40 | 0..1; 0.70; 0.42901079963528765 | 0..1; 0.45; 1.1313729412971263 | 0..1; 0.20; 1.4936947619025975 |
| 100 | 0..1; 0.88; 0.07555156262124552 | 0..1; 0.78; 0.24451738161783698 | 0..1; 0.66; 0.5505114253350429 |

- (b) **Pinning replaces MST finding 1.** No window, but the share of rows pinned at exactly 0 or 1 grows with T and depends
  on gamma. A pinned row only tests that the four stages are ordered; the informative rows are short T and the transitions.
  Range is not monotone in T or gamma (gamma 0.7, T = 10: 0.479..0.521).
- (b) **Well conditioned on sines:** min (CU + CD)/amplitude >= 0.0756 (gamma 0.5, T = 100). (b) RSI is continuous in
  L0..L3: at a tie `a = b` the pair contributes 0 to CU or CD whichever branch runs, so a `>=` flip by rounding cannot jump.
- (b) **Ramp is a known answer** (9c.2 turned into a check): rising ramp, RSI = 1.0 exactly from row 3 / 6 / 10 (last
  row != 1: 2 / 5 / 9); falling ramp, RSI = 0.0 exactly after row 23 / 43 / 68 (slower: the stages climb from 0 and must
  overtake each other). Not rounding noise, unlike Reflex (D6 evidence): CD = 0 exactly once the stages are ordered.
- (b) **Linear stages, ramp lag** (DC gain 1 each): L0 = EMA, lag gamma/(1 - gamma); each allpass stage adds
  (1 + gamma)/(1 - gamma). L0 / L3 measured 1.0000000000002451 / 9.999999999999586 bars (gamma 0.5; theory 1 / 10),
  2.333333333333565 / 19.333333333332867 (0.7; 19.33333333333333), 4.000000000000736 / 31.00000000000109 (0.8; 31).
- (b) **Flat:** gamma 0.5: CU + CD = 0 exactly from row 69, RSI held at 1.0 (the value before). gamma 0.7 / 0.8: never
  exactly 0, so the output is normalised rounding noise. The `.c` (seeded) gives 0.5 on every flat row (CU + CD = 0 from
  the seed on, held static 0.5).

## 4. Deviations and decisions (user, 2026-11-19: all as proposed)

| # | Deviation | Impact (b) | Decision |
|---|---|---|---|
| **L-1** | Start-up: all stages = first Close, first bar skipped, returns 0.5; source starts at 0 and computes bar 1 | Up to 1.0 for up to 196 rows (§3) | **Fix to the source:** zero histories (`series(0, 2)` already starts at 0), compute from the first call; remove `lr_init` and the `Close > 0` value guard. Same precedent as HP (GAP-1.26) and USE. The source defines its start-up, so **start-up rows are PASS/FAIL against the model**, not INFO. W from the measured memory (>= 196 at gamma 0.8; the spec measures its own) |
| **L-2** | Zero denominator: held value starts at 0.5; source 0 | Only before the first defined value; after L-1 the hold fires only on exactly equal stages (e.g. flat, gamma 0.5) | **Fix to the source:** hold the previous value, initial 0, in a per-instance `series` |
| **L-3** | `lr_init`, `lr_prevRSI` are file statics shared by every call (Reflex R-1 class) | A second instance or asset finds `lr_init` set and starts from zero history (different start-up rule per instance); on a CU + CD = 0 bar any instance returns **the last value of any instance**. Invisible to trace replay after W: shows only on start-up and CU + CD = 0 rows | **Fixed by L-1 and L-2** (no statics left). Old file kept as `LaguerreRSI_Superseded.c`, called as two instances = shared-state control (D6 rule 5); it must fail start-up (and a flat-hold check if the spec makes one) |
| **L-4** | gamma is a caller literal | 0.5 is exact in float32; 0.7 / 0.8 are not (gotchas 9d.1). Current callers pass `#define LR_GAMMA 0.5` (`Test_C2_LaguerreRSI.c`, `Test_LagSine.c`) | **Record:** the harness builds gamma at run time; header note for callers |
| **L-5** | Linear stage not exported (D6 rule 1) | Stage fidelity hidden inside the normalised output | **Fix:** `LaguerreRSICore(Close, gamma, &L0, &L3, &den)`-style core (exact outputs set by stage 1 tooling: generator limit), `LaguerreRSI()` a thin wrapper, callers unchanged. L0 and L3 have DC gain 1: v1 checks incl. ramp lag (D4 rule 1) with the known answers in §3. Export CU + CD for the gate |
| **L-6** | Header: wrong return description; unlabelled claims (P-LR1, "2025 code lowpass") | Record | **Fix header:** source and page, formula, deviations fixed, this review's path, claims labelled (a)/(b)/(c). (b) The 2025 article's L1 uses `L0[1]` in its first term, giving (1 - gamma)z^-1/(1 - gamma z^-1) = a delayed EMA (lowpass), not an allpass |
| **L-7** | — | — | **Record only:** input `Close` matches; `Laguerre.c` findings logged for its own review (§5) |

**Exact bound (D6 rule 3):** the **final output itself** is in [0, 1] exactly: CU, CD >= 0, and the held value is either a
previous ratio or the initial 0. Unlike MESA, no intermediate is needed.

**Start-up counter (gotchas 9d.9):** not needed (no `CurrentBar` rule); the zero start is the `series(0, 2)` initial history
on each instance's first call. (c) To be confirmed by the start-up checks, as in 9d.9's harness conditions.

## 5. `Laguerre.c` — logged, not reviewed

(b) Read 2026-11-19 only to establish the dependency (none). For its own review (baselines): file statics `lag_L0..L3`,
`lag_init` shared by every call (R-1 class); reads `priceHigh()/priceLow()` itself (fixed-input signature, as
UltimateChannelBands); cites Fig. 14.5 with weights 1-2-2-1 / 6 and default gamma 0.5 against the figure's .8 (its own
header says so). Not checked against the book here.

## 6. For the spec (not decided here)

- Variants: gamma 0.5 (the C2 default) and at least one other (0.8), with sines T = 5, 10, 20, 40, 100: short T for
  unpinned rows, long T for lock-to-lock behaviour.
- Linear stage: L0 and L3 get flat, gains, phases, alternating input, ramp lag (DC gain 1, D4 rule 1).
- Trace replay (D6 rule 2) rows >= W on sines; gate on the MODEL's CU + CD (margin >= 0.0756 x amplitude here).
- Start-up rows: PASS/FAIL against the source model (zero start), on sines (gotchas 9d.9; the start-up table above is
  on sines). Flat and ramp start-ups also differ here but are not relied on.
- Ramp: RSI = 1 exactly (rising) and 0 exactly (falling) after the measured transient: a known answer, PASS/FAIL.
- Bound: final output in [0, 1] exactly, every row of every input.
- Invariance (D6 rule 4): scale x k and offset.
- Flat: INFO (rounding noise at gamma 0.7 / 0.8); possibly a flat-hold check at gamma 0.5 if it is needed to detect L-3.
- Controls: the real superseded file as two instances (shared state); the price seed alone (L-1); hold initial 0.5 (L-2,
  visible only on a zero first input; may be INFO); a coefficient off in its third digit (D2 rule 4: e.g. gamma in L0 only);
  L1 with `L0[1]` in its first term (the 2025 form).
