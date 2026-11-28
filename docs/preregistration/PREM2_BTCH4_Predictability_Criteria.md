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
