# PREM1 — Is there directional predictability at 2-60 days in D1 FX (EUR/USD, AUD/USD, EUR/JPY)? — Criteria

**Status:** pre-registered 2026-11-27, before any variance ratio of these bars is computed and before any code for this step is
written. Amendments are dated and appended below, never edited in place (PROJECT_STATE §2.2).
**Decided:** planning chat 2026-11-27 (decision N4: P + W; learn mode on the variance ratio; N-a, H-a, S-a, PC-a, outcome
mapping, U1-U6; user: as recommended on each). Branch `prem1-d1fx-predictability` off `main` 0ccff4c.
Labels as `docs/sources/NNFX_Sources.md`: (a) source states, (b) measurable, (c) inference.

## Purpose

(b) Six C1 readings show no timing edge on the three D1 FX dev pairs (C1S1-C1S3); random C1 at true zero cost scores about 0
(DIAG1 A4); H(returns) about 0.50 on EUR/USD D1 (§3). (c) A price-only trend timing rule can earn before costs only if moves
at its holding horizon tend to continue. PREM1 asks that premise directly, independent of any indicator: **do these pairs'
daily returns carry directional memory at 2-60 trading days?** Premise test only: no system, no variant, no slot is selected.

## Data (carried, no decision)

- Bars: the verified 17:00 New York daily bars (R1 rule, `tools/r1_data.py`, holidays folded), cut to Zorro's logged bars:
  EUR/USD from `TPL_R1d_log_run1.csv` (as NULL1), AUD/USD and EUR/JPY from `IND_<pair>_log_run1.csv` (C1S3 VB1 PASS; EUR/JPY
  with C1S2 Amendment 1's 3 filler bars). Full history from each pair's first Zorro bar (lookback rows included).
- Returns: r_t = ln(C_t / C_{t-1}), close to close; each pair de-meaned by its own mean.
- (c) EUR/JPY's 3 flat filler bars give 0 returns inside the 2017-12 quote hole and one larger return after it; kept as is
  (they are the bars every other study used); count reported.

## Statistic (decisions H-a, S-a)

- Horizons **q = 2, 5, 10, 20, 40, 60** trading days (fixed; VR(1) = 1 by definition; q > 60 not used).
- Per pair, overlapping variance ratio with the usual small-sample correction (as in Lo & MacKinlay 1988, Review of Financial
  Studies; cited from memory, so the definition below is the binding one):
  - mu = mean(r), n = number of returns;
  - sa2 = sum_t (r_t - mu)^2 / (n - 1);
  - sc2(q) = sum_{t=q..n} (r_t + ... + r_{t-q+1} - q mu)^2 / m, m = q (n - q + 1) (1 - q / n);
  - **VR(q) = sc2(q) / sa2**.
- Pooled per q: **D(q) = mean over the 3 pairs of (VR(q) - 1)** (equal weights).
- Standardised per q by the null: z(q) = (D(q) - mean_null D(q)) / sd_null D(q). Test statistic **M = max over q of |z(q)|**
  (two-sided). **Bar = 95th percentile of M over the null draws** (each draw standardised with the same null mean / sd).
- **Flag** for horizon q: |z(q)| > bar **and** VR(q) - 1 has the sign of D(q) on >= 2 of the 3 pairs.
- Reported per pair and pooled: VR(q), its own-null 5th / 50th / 95th percentiles and percentile of the real value; z(q); M.

## Null (decision N-a)

- **Random-sign surrogate:** r*_t = s_t (r_t - mu), s_t independent fair +-1 signs, per pair independent. Keeps every |r_t| in its
  real order (sizes and volatility clustering exactly); removes any memory in direction. (c) Assumption: under the null, up
  and down moves of the same size are equally likely.
- **1,000 draws per pair**, `numpy.random.default_rng(20261127)` (one generator, pairs drawn in the order EUR/USD, AUD/USD,
  EUR/JPY within each draw); draw i of the pooled null uses draw i of each pair.
- **Information row (never decisive):** existing stochvol surrogate (`analysis/null_tests/src/surrogates.py`
  `surrogate_stochvol`, null D; H_vol and s calibrated as that module does, on each pair's returns), 1,000 draws, same
  statistic; reported next to N-a.

## Positive control (decision PC-a)

- Planted series start from a random-sign surrogate of each pair (so they keep the real sizes and clustering); the same
  strength on all three pairs; each planted draw is scored with the **full S-a test** (the null's mean / sd per q, the same bar,
  the 2-of-3 sign rule).
- **Short memory, AR(1):** x_t = phi x_{t-1} + r*_t, phi = +-0.01, +-0.02, +-0.03, +-0.05.
- **Slow momentum:** x_t = r*_t + kappa * mean(x_{t-1} .. x_{t-20}) (starting after 20 returns), kappa = +-0.02, +-0.05, +-0.10,
  +-0.20.
- 200 planted draws per level (seed `default_rng(20261128)`). **Detection rate** = share flagged (any q, with the planted sign
  on the flagged q). **Detection bound** = the smallest |level| caught >= 90% for both signs; reported as the parameter and as
  the median VR(q) it produces.
- If the ladder misses the 90% crossing for either kind, it is extended by a dated amendment **before the real read**, never
  after.

## What a result leads to (decision: outcome mapping)

- **No horizon flagged:** recorded as "no directional predictability at 2-60 days on the 3 D1 FX dev pairs, above bounds
  phi >= X / kappa >= Y". Next (separate decision): BTC/USD H4 vs stopping D1-FX price-timing.
- **Flagged, VR > 1 (trend) at q:** recorded as "trend-type predictability at q, size ...". Next (separate decision): an exit /
  holding study matched to q, or a simple momentum C1 as a new counted candidate. No tuning on PREM1's numbers.
- **Flagged, VR < 1 (reversal) at q:** recorded as "reversal-type predictability at q". Next (separate decision): whether a
  mean-reversion system (outside NNFX rules) is in scope.
- In every case: PREM1 selects no system or variant; the confirmation set stays closed; the flagged q and size are reported,
  not used to tune anything.

## Checks before the read

- **K1 generator:** a random-sign surrogate keeps |r| exactly (0 differences) and its signs are balanced (binomial test, planted
  all-positive input refused as a check); a planted AR(1) series (phi 0.3) has rho_1 near 0.3 before and near 0 after sign
  randomisation (tests).
- **K2 estimator:** VR on hand-built series: the step-1 learn-mode examples (runs series VR(2) = 1 + rho_1 within the
  small-sample correction; alternating series VR(2) about 0), and an AR(1) phi = 0.2 long series VR(2) within 0.02 of 1.2 (tests).
- **K3 bars:** each pair's bar count and first / last date equal the earlier checked studies' (EUR/USD 5,490 as NULL1;
  AUD/USD 5,890 and EUR/JPY 4,346 as C1S3's logs).
- **K4 order:** null draws, stochvol draws and the positive control are computed and their files' sha256 recorded **before**
  the real VR of any pair is computed.

## Predictions (decision U1-U6; (c), committed before any build or run)

Back-of-envelope: null sd of VR(2) - 1 about 1/sqrt(n) per pair (0.0135 / 0.0130 / 0.0152), pooled about 0.008; long horizons
(iid formula sqrt(2 (2q - 1)(q - 1) / (3 q n))) pooled about 0.041 (q = 20) / 0.058 (q = 40); bar for 6 correlated two-sided
horizons below the independent value 2.63; AR(1) 90% needs z about bar + 1.28 = 3.8, phi about 3.8 x 0.008 x 1.1 = 0.033;
momentum: rho_k about kappa / 20 for k <= 20, VR(40) - 1 about 1.48 kappa, z about 25 kappa, so kappa about 0.15.

- **U1** The random-sign generator keeps |r| exactly; planted AR(1) loses its rho_1 under it (K1).
- **U2** Pooled null sd of VR(2) - 1 in [0.007, 0.012]; bar in [2.3, 2.7].
- **U3** AR(1) bound phi_90 = 0.03 or 0.05 (sign-symmetric within one ladder step).
- **U4** Momentum bound kappa_90 = 0.20 (0.10 possible); if the ladder misses, an amendment before the read.
- **U5** No horizon flagged: real M below the bar, and every q's pooled D(q) inside its null's 5-95%.
- **U6** The stochvol information row agrees in direction with N-a (no flag).
- **Caveat (c), recorded with U4:** if U4 holds, PREM1 sees slow momentum only when it raises 20-40-day variance by about
  20-30% (VR about 1.2-1.3); a weaker trend premium stays invisible to it, as to a single NNFX read. "No flag" would mean "no
  strong price memory", not "no memory at all".

## Run order

1. Commit this file (before any code).
2. Build `tools/prem1.py` (bars per pair, returns, VR estimator, random-sign and stochvol surrogates, positive control,
   pooled test, report) + `tools/tests/test_prem1.py` (K1, K2, pooled max-statistic and the 2-of-3 rule on hand-built tables);
   commit.
3. K3; null, stochvol and positive-control runs; sha256 recorded (appended); ladder amendment if needed.
4. Read: real VRs; report `analysis/prem1/PREM1_report.md`; appended below as "PREM1 read 1".

## Count

Premise test: 6 horizons x 3 pairs in one max-statistic; no strategy, slot or C1 variant. Project-wide full-strategy variants:
2 (unchanged); C1-only readings unchanged.

## Amendments

## Record: build (run order 2) — 2026-11-27, before any run

- `tools/prem1.py`: bars (EUR/USD via `null1.load`, AUD/USD / EUR/JPY via `c1s3.load`), returns, the binding VR estimator,
  random-sign surrogate (scalar and matrix forms), stochvol information surrogate, AR(1) / momentum planting (numpy only, time
  loop vectorised over draws: no scipy in the VM shell), pooled S-a test with the 2-of-3 rule and the planted-sign filter,
  K3, null / stochvol / pc runs (exclusive create), read (sha256 prefixes checked; real VRs computed only there, K4).
- **Stochvol calibration (information row only):** H_vol = DFA(|r|) of each pair (`surrogates.dfa_hurst`), `s` from
  `surrogates.calibrate_stochvol_s(r, H_vol, H_vol, rng)` (reproduces that DFA target); own seed 20261129 (null 20261127,
  positive control 20261128).
- `tools/tests/test_prem1.py` (12 tests): **K2** hand-calculated VR(2) = 2.0 (runs series under the small-sample correction:
  sa2 = 8/7, sc2 = 24/10.5) and 0 (alternating); AR(1) phi 0.2 gives VR(2) within 0.02 of 1.2; iid near 1 at every q; drift
  invariant. **K1** |r| kept exactly in order; signs balanced; an all-positive input does not stay positive; planted AR(1) rho_1
  0.3 removed (< 0.02) by sign randomisation; matrix form keeps sizes. Planting: momentum start-up (x = r* before 20) and
  recursion; vectorised = row-wise; kappa 0.2 raises VR(40) above 1.2. Pooled test: null bar near the 6-horizon value, 5% of
  null draws above it; all-pairs move flagged; **one-pair spike blocked by the 2-of-3 rule**; reversal flagged two-sided; wrong
  planted sign not counted. Bounds: smallest level with both signs >= 90%; missed ladder returns None.
- All tools tests 205 / 205 OK. Nothing run on real or surrogate data before this commit.

## Record: K3, null, stochvol and positive-control runs (2026-11-27, before any real VR)

- Build committed 9b16750. VM shell, python 3.10, numpy only.
- **K3 PASS:** bars EUR/USD 5,490 (2005-03-29 .. 2026-05-29), AUD/USD 5,890 (2005-06-29 .. 2026-05-29), EUR/JPY 4,346
  (2010-05-23 .. 2026-01-15); zero returns 9 / 16 / 8 (EUR/JPY's include the filler bars).
- Random-sign null `analysis/prem1/results/PREM1_null_signs.csv` 3,000 rows (1,000 draws x 3 pairs), sha256
  **45a88f76e2f0f3cfe1221cfda8d8dd62c621e58e939be4d7ff413997387715cc**.
- Stochvol null `PREM1_null_stochvol.csv` 3,000 rows, sha256 **c79975a55eb86e4bfdaf2d5f716787aca6699844a3ab8a79412d2a5b46df7629**.
  Calibration (information): H_vol EUR/USD 0.821, AUD/USD 0.851, EUR/JPY 0.730; s 1.6 / 1.4 / 1.4 (EUR/USD at the module's grid
  edge 1.6: its clustering may be under-matched). (c) H_vol here is higher than §3's 0.658 (other data file and DFA run); noted.
- Positive control `PREM1_pc.csv` (16 signed levels x 200), sha256 **c6da21ff5ebfe3556e94d3ed1dc192c30b90538cc1c79610d337e2b997447cd0**.
- (b) Null statistics: bar **2.406** (stochvol 2.459); pooled null sd of D(q) at q = 2 .. 60: 0.0122, 0.0269, 0.0408, 0.0591,
  0.0846, 0.1032 (null mean D slightly negative, -0.0005 .. -0.0071: the small-sample bias of the estimator).
- (b) Detection rates (+ / -): AR(1) phi 0.01 .13 / .12, 0.02 .33 / .28, 0.03 .62 / .55, 0.05 .98 / .95; momentum kappa 0.02
  .12 / .03, 0.05 .15 / .05, 0.10 .42 / .24, 0.20 **.96 / .72**.
- **Predictions so far:** U1 met (K1 tests). U2: bar in [2.3, 2.7] **met** (2.406); pooled sd of VR(2) - 1 in [0.007, 0.012]
  **not met** (0.0122, just above). U3 phi_90 = 0.03 or 0.05: **met** (0.05). U4 kappa_90 = 0.20: **not met** (the - side reaches
  only 72% at 0.20). (c) The long-horizon null sds are larger than the iid back-of-envelope (0.059 / 0.085 vs 0.041 / 0.058):
  volatility clustering widens them; negative kappa lowers long-horizon variance, where the null is wide and VR is bounded by 0.

### Amendment 1 (2026-11-27, after the positive control, before any real VR): momentum ladder extended

- As the criteria require when the ladder misses the 90% crossing: **user decision L-a**: add kappa = +-0.30, +-0.40, 200 draws
  each, own seed 20261130 (`prem1.py pc-ext`, `LADDER_EXT`), file `PREM1_pc_ext.csv`, sha256
  **8389c725343aaa3b453a06924417eff1873db0af238667370af2f7dea08bb641**. The bound rule (smallest |level| with both signs >= 90%)
  is unchanged. Information row added: sign-specific bounds. Rejected L-b (trend side only as the rule: a rule change after
  seeing the control).
- Code: `bound` reads levels from the rates (base + extension), optional `signs`; `read` takes `pc.csv+pc_ext.csv` and one sha
  prefix per file; test extended (extension levels, sign-specific bounds); PREM1 tests 12 / 12.
- (b) Extension rates: kappa 0.30 1.00 / .98, 0.40 1.00 / 1.00. **Bounds: phi_90 = 0.05; kappa_90 = 0.30 (rule)**; information:
  kappa_90 trend side (+) 0.20, reversal side (-) 0.30.
- (b) In variance-ratio terms (median pooled VR - 1 of the planted draws): phi +0.05: +0.050 (q = 2) to +0.10 (q = 20-60);
  kappa +0.20: +0.23 (q = 20), +0.37 (q = 40), +0.42 (q = 60); kappa +0.30: +0.38 / +0.63 / +0.75; kappa -0.30: -0.22 / -0.33 / -0.36.
  (c) So PREM1 can see trend that raises 20-40-day variance by about 25-40% or more, and lag-1 memory of 5%; weaker memory stays
  invisible, as the U4 caveat said.
- Next: the read (real VRs computed only there, K4).
