# Reflex — source review (code vs article)

**Date:** 2026-11-18 (planning chat). **Status:** review complete, decisions taken (user, 2026-11-18). No spec yet.
**File reviewed:** `indicators/ehlers/Reflex.c` (931 bytes, mtime 2026-08-12), with its dependency
`indicators/ehlers/SuperSmoother2Pole.c`.
**Source:** Ehlers, J.F., "Reflex: A New Zero-Lag Indicator", *Technical Analysis of Stocks &
Commodities* V.38:02 (2020), pp. 6-8, 21; sidebar "EasyLanguage Code For Reflex Indicator"
((C) 2019). PDF in project knowledge: `Reflex_A_New ZeroLag Indicator.pdf`.
**Context:** PROJECT_STATE §7 step 3, order C, oscillator harness family (option B, decided
2026-11-18). Reflex is the C2 candidate (§1.2) and the first indicator of the family.

Labels: (a) source states · (b) read or computed here · (c) inference.

---

## 1. Source formula (a)

Input `Length` (default 20, "assumed cycle period").

```
a1 = expvalue(-1.414*3.14159 / (.5*Length));
b1 = 2*a1*Cosine(1.414*180 / (.5*Length));
c2 = b1;  c3 = -a1*a1;  c1 = 1 - c2 - c3;
Filt = c1*(Close + Close[1]) / 2 + c2*Filt[1] + c3*Filt[2];
Slope = (Filt[Length] - Filt) / Length;
Sum = 0;
For count = 1 to Length Begin
    Sum = Sum + (Filt + count*Slope) - Filt[count];
End;
Sum = Sum / Length;
MS = .04*Sum*Sum + .96*MS[1];
If MS <> 0 Then Reflex = Sum / SquareRoot(MS);
```

(a) Text: the data is "only gently smoothed", with the smoothing length "half the period of the
assumed cycle period"; MS is an EMA of the squared sum, so Reflex "is scaled in terms of standard
deviations". (a) No start-up rule is printed (no `CurrentBar` clause). (a) The same article also
gives Trendflex (horizontal line instead of the slope line); not in the library, out of scope.

## 2. Line-by-line comparison

| Stage | Source (a) | `.c` (b) | Verdict |
|---|---|---|---|
| Half length | `.5*Length`, real | `int rx_HalfLength = Length / 2;` (line 2) | **R-2** |
| SuperSmoother | `a1`, `b1`, `c1·(C+C[1])/2` as above | `SuperSmoother2Pole(Price, rx_HalfLength)` (line 5): `c1 = exp(-sqrt(2.0)*PI/Period)`, `b1 = 2·c1·cos(sqrt(2.0)*PI/Period)`, `c0 = (1 - b1 + c1²)/2`, output `c0·(P + P[1]) + c2·Filt[1] + c3·Filt[2]` | Matches: `c0·(P+P1)` = `c1_src·(P+P1)/2` since `c1_src = 1 - b1 + a1²`. `1.414` → √2 and `3.14159` → π by D1 rule 1; `PI` gap per D3. Degrees→radians correct (`1.414*180` ↔ `sqrt(2)*PI`) |
| Slope | `(Filt[Length] - Filt) / Length` | `(rx_Filt[Length] - rx_Filt[0]) / Length` (line 8) | Matches |
| Sum | `count = 1..Length`, `(Filt + count*Slope) - Filt[count]`, then `/ Length` | lines 13-15, same bounds and terms | Matches |
| MS | `.04*Sum*Sum + .96*MS[1]`, per-instance variable | `static var rx_MS`, `0.04 * ... + 0.96 * rx_MS` (lines 18-20) | **R-1**, **R-3** |
| Zero guard | `If MS <> 0 Then Reflex = Sum/sqrt(MS)` (else Reflex keeps its previous value) | `if (rx_MS > 0) rx_Reflex = ...;` else returns 0 (lines 22-24) | Equivalent (§3) |
| Start-up | not stated | inherits SS2 price seeding: `series(Price[0], 3)` and the `Init` branch | **R-4** |
| Header | — | none | **R-5** |

## 3. Zero guard — why no change (b)

MS ≥ 0 on every bar (sum of non-negative terms), so `MS <> 0` and `MS > 0` select the same bars.
MS = 0 only while every Sum so far has been exactly 0; Reflex has then never been assigned and holds
its initial value 0, which is what the `.c` returns. (c) The only other route to MS = 0 is
underflow of `.96^n` after a very long run of Sum = 0 exactly (n ≈ 18,000 bars to reach the smallest double); not a practical
case.

## 4. Deviations and decisions

| # | Deviation | Impact | Decision (2026-11-18) |
|---|---|---|---|
| **R-1** | `static var rx_MS`: one MS shared by every Reflex call. Source: MS is per instance (`MS[1]`) | (c) Two lengths, two inputs or an asset loop update the same MS: silent wrong output. Same class as gotchas 9b.1 / 9d.9 | **Fix:** per-instance series `vars rx_MS = series(0, 2);`, `rx_MS[0] = w1*Sum*Sum + w2*rx_MS[1]`. INITRUN reset no longer needed. Negative control: the shared-static version with two instances |
| **R-2** | Integer half length `Length/2`; source `.5*Length` real | Identical for even Length (default 20). Odd Length: e.g. 21 smooths at P = 10 instead of 10.5 | **Option (ii):** compute the SuperSmoother inside `Reflex.c` with a real half length (`var`), not via `SuperSmoother2Pole(int)`. Faithful for any Length; the harness checks Reflex end to end. Rejected (i) (even Length only + guard): restricts parameter sweeps. Spec tests at least one odd Length; control = integer half length |
| **R-3** | `0.04` / `0.96` are float32 literals (9d.1). D1 rule 2: weights taken literally as .04 / .96 | (b) each 2.2e-8 relative low; sum of weights 1 - 2.2e-8 | **Fix:** build at run time from integers (`var rx_w1 = 4; rx_w1 = rx_w1 / 100;`, same for 96). Corrected code starts expressions with a variable (9d.8) |
| **R-4** | Start-up undefined by the source; `.c` inherits SS2 price seed | The source gives nothing to check against | **Option (i):** start-up excluded from PASS/FAIL; start-up rows reported as INFO. Warmup ≥ 677 bars (below) |
| **R-5** | No header or citation | Record only | **Fix:** header with source, formula, deviations fixed and this review's path |

**Warmup (b):** MS is an EMA with weight 0.96; a start-up error decays as 0.96^n, below 1e-12 after
ln(1e-12)/ln(0.96) = 676.87 bars. The SuperSmoother stage decays much faster at the test lengths
(to be computed in the spec). (c) The spec's warmup is set from the larger of the two.

## 5. For the spec (not decided here)

- Reflex is linear up to Sum (FIR on a linear IIR), so Sum has a transfer function: gain and phase
  checks apply to Sum if it is exported. The MS normalisation is the nonlinear step.
- Known answers (b, algebra; to be computed in the spec): flat input → Sum = 0 → Reflex = 0;
  ramp input → Filt is a ramp in steady state, the slope line removes it → Sum = 0 → Reflex → 0.
- Property checks: Reflex unchanged under input scaling ×k and a constant offset.
- Controls: R-1 shared static (two instances), R-2 integer half length (odd Length), weights off
  in the third digit, Sum loop off by one bar.
