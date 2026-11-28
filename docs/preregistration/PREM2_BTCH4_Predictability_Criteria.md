# PREM2 — Is there directional predictability at 2-360 H4 bars in BTC (Binance BTCUSDT 4h)? — Criteria

**Status:** pre-registered 2026-11-27, before any variance ratio of these bars is computed and before any code for this step is
written. Amendments are dated and appended below, never edited in place (PROJECT_STATE §2.2).
**Decided:** planning chat 2026-11-27 (decision N5: PREM1's method on BTC H4 before any BTC template build; G-a, H-c, S-2, P-3,
predictions U1-U9, outcome mapping O; user: as recommended on each). Branch `prem2-btc-h4` (data commit f6c8cef).
Labels as `docs/sources/NNFX_Sources.md`: (a) source states, (b) measurable, (c) inference.

## Purpose

(b) PREM1 found no directional predictability at 2-60 days on the three D1 FX dev pairs (bounds phi 0.05, kappa 0.30, trend
side 0.20). (c) A trend-timing system on BTC H4 can earn before costs only if moves at its holding horizon tend to continue.
PREM2 asks that premise on BTC before any BTC template is built: **do BTCUSDT 4h returns carry directional memory at 2-360
bars (8 hours to 60 days)?** Premise test only: no system, no variant, no slot is selected.

## Data (decision G-a)

- Bars: Binance spot BTCUSDT 4h, 111 monthly zips in `data/crypto/binance_btcusdt_4h/`, verified against Binance CHECKSUM files
  (`docs/research/Data_BTCUSDT_H4_Binance.md`, manifest `..._manifest.csv`). 20,160 bars, bar open times
  2017-08-17 04:00 .. 2026-10-31 20:00 UTC. (a) Timestamps in ms to 2024-12, us from 2025-01 (both read).
- **Alignment:** the UTC 4h grid as given (bar open 00:00, 04:00, .. 20:00 UTC); close of each bar. No re-alignment.
- Returns: r_t = ln(C_t / C_{t-1}), close to close, n = 20,159; de-meaned by its own mean (inside the estimator and null).
- **Gaps (G-a):** the 9 gaps > 4h (17 missing bars, all before 2020-03) are kept as they are: each gap-spanning return is one
  return. (b) Measured before this file (sizes only, no VR): sd of r 0.01446, median |r| 0.00498; gap returns
  2017-09-06 12:00 (8h) +0.0001, 2018-02-08 00:00 (32h) +0.0618 (4.27 sd), 2018-06-26 (12h) -0.0064, 2018-07-04 (8h) +0.0085,
  2018-11-14 (8h) -0.0140, 2019-03-12 (8h) +0.0131, 2019-05-15 (12h) +0.0057, 2019-08-15 (8h) +0.0063, 2020-02-19 08:00 (8h)
  -0.0010; together 0.10% of sum r^2 (largest |r| of the series 18.8 sd). Rejected: G-b drop them (sums across a gap still join
  non-adjacent bars), G-c flat filler bars (17 invented bars), G-d start 2020-03 (loses 2017-2020).
- (c) Quote is USDT, not USD. How Zorro treats these gaps is decided at template time, not here.

## Statistic (decisions H-c, S-2)

- Horizons **q = 2, 5, 10, 20, 40, 60, 120, 240, 360 H4 bars** (fixed). The first six equal PREM1's in bars (an H4 template's
  holding range, (c)); 120 / 240 / 360 = 20 / 40 / 60 calendar days (PREM1's clock time; BTC has no trading-day calendar).
  Rejected: H-a day-equivalents only; H-b bar counts only; 168 / 336 / 504 (FX trading-day clock).
- Estimator: PREM1's binding overlapping variance ratio, unchanged (`tools/prem1.py vr`):
  - mu = mean(r), n = number of returns; sa2 = sum_t (r_t - mu)^2 / (n - 1);
  - sc2(q) = sum_{t=q..n} (r_t + ... + r_{t-q+1} - q mu)^2 / m, m = q (n - q + 1) (1 - q / n);
  - **VR(q) = sc2(q) / sa2**.
- One series, no pooling: z(q) = (VR(q) - mean_null VR(q)) / sd_null VR(q). Test statistic **M = max over the 9 q of |z(q)|**
  (two-sided). **Bar = 95th percentile of M over the null draws** (each draw standardised with the same null mean / sd).
- **Thirds:** the returns split by count into three consecutive equal parts (6,719 / 6,720 / 6,720 returns: base n // 3, the remainder of 2
  added one each to the last two parts; boundary dates recorded at build). VR_k(q) is the same estimator on third k's returns alone.
- **Flag** for horizon q: |z(q)| > bar **and** VR_k(q) - 1 has the sign of VR(q) - 1 in **>= 2 of the 3 thirds** (S-2; the
  single-series analogue of PREM1's 2-of-3 pairs rule: (c) guards against one episode, e.g. 2017-18, driving a flag).
  Rejected: S-1 bar only; S-3 thirds as information only.
- Reported per q: VR(q), its null 5th / 50th / 95th percentiles and the real value's percentile, z(q), the three VR_k(q); M.

## Null (carried from PREM1 N-a)

- **Random-sign surrogate:** r*_t = s_t (r_t - mu), s_t independent fair +-1. Keeps every |r_t| in its real order; removes any
  memory in direction. (c) Assumption: under the null, up and down moves of the same size are equally likely.
- **1,000 draws**, `numpy.random.default_rng(20261201)`. The thirds of a null draw are its own thirds (same split).
- **Information row (never decisive):** stochvol surrogate (`analysis/null_tests/src/surrogates.py surrogate_stochvol`,
  H_vol = DFA(|r|), s from `calibrate_stochvol_s`, as PREM1), 1,000 draws, own seed 20261203, same statistic and flag rule.

## Positive control (decision P-3)

- Planted series start from random-sign surrogates of the real returns; each planted draw is scored with the **full test**
  (null mean / sd per q, the same bar, the thirds rule). A flag counts only on a q whose sign equals the planted sign.
- **AR(1):** x_t = phi x_{t-1} + r*_t; phi = +-0.02, +-0.03, +-0.05, +-0.08.
- **Momentum, L = 20 bars:** x_t = r*_t + kappa * mean(x_{t-1} .. x_{t-20}) (from t = 20); kappa = +-0.05, +-0.10, +-0.20,
  +-0.30, +-0.40.
- **Momentum, L = 120 bars:** the same with mean(x_{t-1} .. x_{t-120}) (from t = 120); kappa = +-0.10, +-0.20, +-0.30, +-0.40,
  +-0.60.
- 200 planted draws per signed level (28 levels), `default_rng(20261202)`. **Detection rate** = share flagged (any q, planted
  sign). **Detection bound** = smallest |level| caught >= 90% for both signs, per kind (AR(1), mom L20, mom L120); reported as
  the parameter and as the median VR(q) it produces; trend-side (+) bounds reported as information.
- If a ladder misses the 90% crossing for either sign, it is extended by a dated amendment **before the real read**, never
  after; extension seed 20261204.

## What a result leads to (decision O)

- **No flag:** recorded as "no directional predictability at 2-360 H4 bars on BTCUSDT, above bounds phi >= X, kappa >= Y
  (L = 20), kappa >= Z (L = 120)". Next (separate decision): no BTC trend template build; the project's direction (stop
  price-timing on the dev set, or a question on a property that does persist, e.g. volatility).
- **Trend flag (VR > 1) at some q <= 60:** recorded as "trend-type predictability at q, size ...". Next (separate decision):
  BTC H4 template build with the existing verified slots: R1-style mechanics gate, then a pre-registered PERF read. No C1
  period chosen from q.
- **Trend flag only at q = 120-360:** recorded as above. Next (separate decision, before any build): a BTC **D1** template is
  the matched build, not H4 ((c) an H4 template holds about 2-60 bars).
- **Reversal flag (VR < 1):** recorded as "reversal-type predictability at q". Next (separate decision): whether a
  mean-reversion system (outside NNFX rules) is in scope.
- **|z| > bar but the thirds rule fails:** recorded as "episode-driven, not flagged", naming the third that drives it; treated
  as no flag for the build decision.
- In every case: PREM2 selects no system or variant; the confirmation set stays closed; the flagged q and size are reported,
  not used to tune anything.

## Checks before the read

- **K1 generator:** reused PREM1 tests (|r| kept exactly; planted AR(1) phi 0.3 loses rho_1 under sign randomisation); plus the
  L = 120 momentum start-up and recursion (vectorised = row-wise).
- **K2 estimator:** PREM1's hand-calculated VR tests pass unchanged; thirds split hand-checked on a small series (counts,
  remainder to the last parts); single-series flag rule on hand-built tables (bar-only spike in one third blocked; all thirds
  agreeing flagged; reversal flagged two-sided; wrong planted sign not counted).
- **K3 bars:** 20,160 bars, first / last open time and the 9 gaps equal the data record; timestamp units ms / us both parsed
  (bar count per unit 16,146 / 4,014).
- **K4 order:** null draws, stochvol draws and the positive control are computed and their files' sha256 recorded **before**
  the real VR is computed.

## Predictions (U1-U9; (c), committed before any build or run)

Back-of-envelope: random-sign sd of VR(q) - 1 about 2x iid (PREM1 measured about 1.56x from heavy tails; BTC tails assumed
heavier): about 0.014 (q = 2), 0.08 (q = 20-40), 0.15 (q = 60), 0.30 (q = 360); 9-horizon bar a little above PREM1's 2.41;
90% detection needs z about bar + 1.28 = 3.8: phi about 3.8 x 0.014 = 0.05; momentum VR(2L) - 1 about 1.5 kappa for any L:
L = 20 at q = 40 z about 19 kappa, kappa about 0.20; L = 120 at q = 240 z about 8 kappa, kappa about 0.45 before the thirds
rule's cost (largest at long q, where each third holds about 19 blocks of 360).

- **U1** K1: the random-sign generator keeps every |r| in order exactly; planted AR(1) phi 0.3 loses its rho_1 (< 0.02).
- **U2** Null sd of VR(2) - 1 in [0.010, 0.020]; bar in [2.3, 2.8].
- **U3** phi_90 = 0.05 or 0.08.
- **U4** kappa_90 (L = 20) = 0.20 or 0.30.
- **U5** kappa_90 (L = 120) = 0.40 or 0.60; if either momentum ladder misses 90%, an amendment before the read.
- **U6** No horizon flagged: real M below the bar (about 60%; a trend flag at q >= 120 is the likeliest alternative).
- **U7** VR(q) - 1 within +-0.05 of 0 at q = 2-10, and positive at q = 120-360 (unflagged).
- **U8** At q >= 120 the first third (2017-20) has the largest |VR_k - 1| of the three thirds.
- **U9** The stochvol information row agrees with the random-sign result (flag or no flag).
- **Caveat (c), recorded with U4 / U5:** "no flag" would mean no memory above the measured bounds; weaker memory stays
  invisible, as in PREM1.

## Run order

1. Commit this file (before any code).
2. Build `tools/prem2.py` (bar loader from the zips, returns, thirds, single-series test, null / stochvol / pc runs, read;
   reusing `tools/prem1.py`'s estimator, surrogates and planting) + `tools/tests/test_prem2.py` (K1, K2); commit.
3. K3; null, stochvol and positive-control runs (exclusive create); sha256 recorded (appended); ladder amendment if needed.
4. Read: real VRs; report `analysis/prem2/PREM2_report.md`; appended below as "PREM2 read 1".

## Count

Premise test: 9 horizons on one series in one max-statistic; no strategy, slot or C1 variant. Project-wide full-strategy
variants: 2 (unchanged); C1-only readings unchanged.

## Amendments

## Record: build (run order 2) — 2026-11-27, before any run

- **Provenance:** `tools/prem2.py` and `tools/tests/test_prem2.py` were written outside the planning chat, after the criteria
  commit 1fcbe7c (b: file times 22:10:58 / 22:11:33 UTC vs commit 22:09:38 UTC); no `analysis/prem2/` output existed. Reviewed
  line by line against this file in the planning chat (2026-11-27) before any run: QS, seeds, N, the three ladders, G-a loader
  (ms / us, grid and order guards), thirds split, standardisation from the full series, S-2 flag rule with episode rows, planted-
  sign filter, K4 (real VRs in `read` only), exclusive-create outputs, sha prefixes, `pc-ext` refused without an amendment: all
  as above.
- One change from the review: K3 also requires the 9 gap lengths (8, 32, 12, 8, 8, 8, 12, 8, 8 h) and 17 missing bars
  (`k3_check`; previously printed only); test `K3Check` (record passes; each of the 7 items, changed alone, fails).
- Not changed (recorded): the report names no driving third for an episode row and gives median planted VRs for the + sign
  only; the read write-up covers both from the printed thirds columns.
- Estimator, surrogates and planting are `tools/prem1.py`'s, unchanged. Tests: PREM2 19 / 19; all tools tests 224 / 224 OK (VM
  shell, python 3.10). Nothing run on real or surrogate BTC data before this commit.

## Record: K3, null, stochvol and positive-control runs (2026-11-27, before any real VR)

- Build committed 7f918f7. VM shell, python 3.10, numpy only.
- **K3 PASS:** 111 files, 20,160 bars, 2017-08-17 04:00 .. 2026-10-31 20:00 UTC, units (ms, us) 16,146 / 4,014; 9 gaps at the
  recorded times and lengths, 17 missing bars; 20,159 returns; thirds 6,719 / 6,720 / 6,720 starting (bar open of the first
  return's close bar) 2017-08-17 08:00, 2020-09-13 00:00, 2023-10-08 00:00.
- Random-sign null `analysis/prem2/results/PREM2_null_signs.csv` (1,000 draws x 4 rows: full + thirds), sha256
  **28048eb9b0123dcebf2e7202cf2466ea82445c206b9a65b8e8e5fca293079d02**.
- Stochvol null `PREM2_null_stochvol.csv`, sha256 **0c8247cfcf3774ce67a639c44e5244bd9e92f451425d66dceae5884a07de5442**.
  Calibration (information): H_vol 0.845, s 1.6 (the module's grid edge, as EUR/USD in PREM1: (c) clustering may be
  under-matched).
- Positive control `PREM2_pc.csv` (28 signed levels x 200), sha256
  **56c55d0f1b15c62e89f148d778bcb06096fdf28b8f42db9d267b96e2cdcc9bc4**.
- (b) Null statistics: bar **2.592** (stochvol 2.610); null sd of VR(q) - 1 at q = 2 .. 360: 0.0136, 0.0321, 0.0490, 0.0667,
  0.0902, 0.1061, 0.1417, 0.1876, 0.2233 (1.94x iid at q = 2 falling to 1.45x at q = 360); null mean VR - 1 within +-0.007.
  Stochvol sd equal at q = 2 (0.0139), 12-20% narrower from q = 5 (0.178 at q = 360).
- (b) Detection rates (+ / -): AR(1) phi 0.02 .165 / .165, 0.03 .400 / .355, 0.05 .865 / .865, 0.08 1.00 / 1.00;
  mom L20 kappa 0.05 .140 / .025, 0.10 .345 / .105, 0.20 .900 / .620, 0.30 1.00 / .935, 0.40 1.00 / 1.00;
  mom L120 kappa 0.10 .115 / .015, 0.20 .410 / .035, 0.30 .705 / .105, 0.40 .940 / .255, 0.60 1.00 / .645.
  Thirds rule: 1 of 5,600 planted draws had an episode-only row and no flag.
- **Predictions so far:** U1 met (K1 tests). U2 met (sd 0.0136 in [0.010, 0.020]; bar 2.592 in [2.3, 2.8]). U3 met (phi_90
  0.08). U4 met (kappa_90 L20 0.30; trend side 0.20). **U5 not met:** L120 ladder misses 90% on the - side (.645 at 0.60);
  trend side 0.40. (c) As in PREM1: negative momentum lowers long-horizon variance, VR is bounded by 0 and the null is widest
  there (kappa -0.60: median VR(240) - 1 = -0.34 vs null sd 0.19).

### Amendment 1 (2026-11-27, after the positive control, before any real VR): L = 120 ladder extended

- As the criteria require when a ladder misses the 90% crossing: **user decision L-a**: add kappa = +-0.80, +-1.00, +-1.20 for
  momentum L = 120, 200 draws each, extension seed 20261204 (`prem2.py pc-ext`, `LADDER_EXT`), file `PREM2_pc_ext.csv`. The
  bound rule (smallest |level| with both signs >= 90%) is unchanged. (c) The planted equal-weight process stays stationary
  for |kappa| below about 4.6, so 1.20 is safe. Rejected: L-b (trend side as the rule for L = 120: a rule change after seeing
  the control); L-c (report no bound).
- Code: `LADDER_EXT` set; test `test_amendment1_extension` (base + extension levels read together). Tests: PREM2 20 / 20; all
  tools tests 225 / 225 OK.
- Amendment 1 committed 2265174. Extension run `PREM2_pc_ext.csv` (6 signed levels x 200), sha256
  **5e7f58ace12e75a5bc71b7dd8a4c3ad74b2d0918cc1a41cfe26af0470faa5434**.
- (b) Extension rates (+ / -): mom L120 kappa 0.80 1.00 / .945, 1.00 1.00 / .980, 1.20 1.00 / 1.00. **Bounds (rule, both signs):
  phi_90 = 0.08; kappa_90 L20 = 0.30; kappa_90 L120 = 0.80.** Information, trend side (+): 0.08 / 0.20 / 0.40.
- (b) In variance-ratio terms (median VR - 1 of the planted draws): L20 kappa +0.20: +0.23 (q = 20), +0.37 (q = 40), +0.47
  (q = 120); L120 kappa +0.40: +0.56 (q = 120), +0.98 (q = 240); L120 kappa -0.80: -0.44 / -0.59 / -0.64 (q = 120 / 240 / 360).
  (c) So PREM2 sees trend that raises 3-7-day variance by about 25-40% (L20 trend side), trend that raises 20-40-day variance by
  about 55-100% (L120 trend side), and long-horizon reversal only when it removes about 45-65% of the variance.
- U5 after the extension: L120 bound 0.80, outside the predicted 0.40 / 0.60 (not met; recorded). Next: the read.

## PREM2 read 1 (2026-11-28) — one horizon flagged: reversal at q = 2

`python tools/prem2.py read data/crypto/binance_btcusdt_4h <R>/PREM2_null_signs.csv <R>/PREM2_null_stochvol.csv
<R>/PREM2_pc.csv+<R>/PREM2_pc_ext.csv 28048eb9b0123dce,0c8247cfcf3774ce,56c55d0f1b15c62e,5e7f58ace12e75a5
analysis/prem2/PREM2_report.md` (<R> = analysis/prem2/results; inputs committed 9253b78; all four sha prefixes verified).
Report `analysis/prem2/PREM2_report.md`.

**Random-sign null (decisive), (b):** bar 2.592; real **M = 3.228**; **flagged: q = 2 (VR < 1, reversal)**; episode-driven: none.

| q | VR | null 5th / 50th / 95th | pct | z | third 1 | third 2 | third 3 |
|---|---|---|---|---|---|---|---|
| 2 | 0.9563 | 0.9775 / 1.0004 / 1.0228 | 0.0% | -3.23 | 0.9407 | 0.9653 | 0.9916 |
| 5 | 0.9737 | 0.9493 / 1.0003 / 1.0570 | 21.3% | -0.82 | 0.9542 | 0.9964 | 0.9966 |
| 10 | 0.9505 | 0.9249 / 1.0004 / 1.0885 | 14.9% | -1.04 | 0.9399 | 0.9720 | 0.9516 |
| 20 | 0.9542 | 0.8956 / 0.9985 / 1.1188 | 24.8% | -0.70 | 0.9400 | 0.9784 | 0.9739 |
| 40 | 0.9872 | 0.8674 / 0.9928 / 1.1624 | 46.8% | -0.15 | 0.9754 | 1.0259 | 0.9909 |
| 60 | 1.0068 | 0.8430 / 0.9898 / 1.1908 | 56.7% | +0.07 | 0.9950 | 1.0583 | 1.0101 |
| 120 | 1.0750 | 0.7967 / 0.9881 / 1.2566 | 73.2% | +0.53 | 1.0574 | 1.1671 | 1.0868 |
| 240 | 1.1744 | 0.7205 / 0.9759 / 1.3224 | 84.9% | +0.95 | 1.1413 | 1.3543 | 1.2096 |
| 360 | 1.2775 | 0.6779 / 0.9711 / 1.3879 | 90.3% | +1.27 | 1.2263 | 1.6184 | 1.2289 |

Stochvol (information): bar 2.610, real M 3.111, flagged q = 2, episode none. Bounds as Amendment 1: phi_90 0.08; kappa_90
L20 0.30 (trend side 0.20); L120 0.80 (trend side 0.40).

**Information (computed after the read from the committed null's third rows; not part of the decisive test), (b):** q = 2 per
third against that third's own null: third 1 (2017-08 .. 2020-09) VR 0.9407, z -2.58 (0.4th pct); third 2 (2020-09 .. 2023-10)
0.9653, z -1.93 (2.5th pct); third 3 (2023-10 .. 2026-10) 0.9916, z -0.56 (28.7th pct). Lag-1 autocorrelation of the de-meaned
returns rho_1 = -0.0438.

**Correction to Amendment 1 (found at the read), (b):** the stationarity note covered only negative kappa. For the planted
momentum process the coefficients sum to kappa, so **kappa >= +1 is a unit root / explosive** (median planted VR(360) 127 at
+1.00, 137 at +1.20). The +1.00 / +1.20 rows are therefore not meaningful as stationary memory. The bounds are unaffected:
L120 = 0.80 is set by the - side (stationary), and the + side was already >= 90% from 0.40.

**Predictions:** U1-U4 met; U5 not met (L120 bound 0.80); **U6 not met** (a flag, at q = 2, reversal: the 60% call was wrong,
and the likeliest alternative named, a trend flag at q >= 120, did not occur either); **U7 met** (VR - 1 -0.044 / -0.026 /
-0.050 at q = 2 / 5 / 10, inside +-0.05; positive at q = 120 / 240 / 360: +0.075 / +0.174 / +0.278, unflagged); **U8 not met**
(at q >= 120 the largest |VR_k - 1| is third 2, 2020-23, not third 1); **U9 met** (stochvol also flags q = 2 only).

**Reading.**
1. Per the outcome mapping: recorded as "**reversal-type predictability at q = 2 H4 bars (8 h) on BTCUSDT: VR(2) = 0.956
   (rho_1 about -0.044), z -3.23 vs bar 2.59; same sign in all three thirds**". No trend horizon flagged, above bounds kappa
   0.20 (L20, trend side) and 0.40 (L120, trend side).
2. (b) The effect shrinks across the thirds: z -2.58 / -1.93 / -0.56; in the last three years it is inside its own null's
   5-95%. (c) It passes the pre-registered thirds rule (sign), but its size is mostly from 2017-2023; whether it still exists
   now is not shown by this test.
3. (c) Size: one-bar reversal of about 4.4% of the previous 4h move. With sd of a 4h return 1.45%, the expected next-bar move
   is of order 0.04 x 1.45% = about 0.06% per bar before costs, against round-trip spot trading costs of the same order or
   larger (fee level not checked here: to be taken from a source if it matters). Not evidence of a tradable edge.
4. (b) Long horizons: VR rises to 1.17 / 1.28 at q = 240 / 360 (85th / 90th pct), not flagged; (c) a trend premium of that
   size, if real, is below the L120 trend-side bound (about +56-98% variance) and cannot be told from noise here.
5. Next (separate decision, per the mapping): whether a short-horizon mean-reversion study is in scope (outside NNFX rules);
   no trend flag, so the mapping gives no BTC H4 or D1 trend template build. Nothing selected or tuned.

**Count:** premise test, no strategy / slot / C1 variant. Project-wide full-strategy variants: 2 (unchanged).
