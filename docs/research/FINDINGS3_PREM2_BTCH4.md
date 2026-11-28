# FINDINGS 3 — BTC H4 has no trend memory to time either; trend-timing closed on the dev set (2026-11-27 .. 11-28)

**Status:** write-up of one pre-registered premise test (PREM2) and its cost gate; no new test. Numbers are copied from the
run record `docs/preregistration/PREM2_BTCH4_Predictability_Criteria.md` (read 1, cost-gate record) and the report
`analysis/prem2/PREM2_report.md`. Follows `FINDINGS2_C1S3_DIAG1_PREM1.md`.
Labels as `docs/sources/NNFX_Sources.md`: (a) source states, (b) measurable, (c) inference.

## Short answer

(b) Binance BTCUSDT 4h returns (2017-08 .. 2026-10, 20,159 returns) show no directional memory of the trend type at any of 9
horizons from 8 hours to 60 days above the detection bounds. One horizon is flagged, and it is the opposite of trend: a small
one-bar **reversal** (VR(2) = 0.956, lag-1 autocorrelation -0.044, z -3.23 vs bar 2.59), the same sign in all three thirds of
the history but fading (third z -2.58 / -1.93 / -0.56). It earns about 0.02% per bar gross against 0.15-0.20% round-trip spot
costs. (c) With PREM1 (D1 FX), all four dev markets lack the premise a trend-following C1 needs, at the horizons tested and
above the bounds. That is "no evidence of strong trend memory", not "evidence of none": bounds below.

## The study

| Item | Result (b) |
|---|---|
| Question | Do BTCUSDT 4h returns carry directional memory at q = 2, 5, 10, 20, 40, 60, 120, 240, 360 bars (8 h .. 60 days)? |
| Method | PREM1's overlapping variance ratio; single series; random-sign null (keeps every \|r\| in order), 1,000 draws; two-sided max\|z\|; flag also needs the same sign of VR - 1 in >= 2 of 3 equal thirds |
| Data | 111 Binance monthly zips, CHECKSUM-verified; 9 gaps kept as single returns (0.10% of sum r^2) |
| Bar / real M | 2.592 / **3.228** (stochvol information row: 2.610 / 3.111) |
| Flagged | **q = 2, reversal** (VR 0.9563; thirds 0.941 / 0.965 / 0.992). No other q; no episode-only row |
| Long horizons | VR 1.075 / 1.174 / 1.278 at q = 120 / 240 / 360 (73rd / 85th / 90th pct): not flagged |
| Bounds (90%, both signs) | AR(1) phi 0.08; momentum L20 kappa 0.30 (trend side 0.20: +23-37% variance at q = 20-40); L120 kappa 0.80 after Amendment 1 (trend side 0.40: +56% / +98% at q = 120 / 240) |
| Cost gate | Binance spot 0.10% per fill (regular user; 0.075% with BNB); flagged effect +0.023% gross per bar: **fail** |

## What the evidence supports

1. (b) No trend horizon flagged on BTC H4, from the H4 template's own holding range (2-60 bars) to PREM1's clock time
   (20-60 days). Per the pre-registered mapping: no BTC trend template build (H4 or D1).
2. (b) The only flag is a one-bar reversal of about 4% of the previous move; it is strongest in 2017-2020 and inside its own
   null's 5-95% in 2023-2026.
3. (b) Gross, the reversal is about one-seventh to one-ninth of a regular user's round-trip fee. (c) Not a tradable edge for a
   spot strategy that trades every bar.
4. (c) PREM1 and PREM2 together: on EUR/USD, AUD/USD, EUR/JPY D1 and BTC H4, any tilt in direction at short horizons is toward
   reversal, not continuation, and no trend memory reaches the bounds. The C1 timing failures (FINDINGS1-2) fit this.

## What it does not show

- Trend memory below the bounds (e.g. VR(240) 1.17, if real) is invisible to this test, as to any single NNFX read.
- One history, one venue, quote USDT not USD; the random-sign null assumes up and down moves of the same size are equally
  likely.
- The reversal after very large moves (> 3 sd: +0.67% gross on 396 events, full series) was found after the read (4
  threshold looks) and is not significant in 2023-26 (n 31): an untested hypothesis, valid only on new data.

## Predictions and corrections

- Predictions U1-U4, U7, U9 met; U5 (L120 bound 0.80, not 0.40 / 0.60), U6 (no flag: 60% call, wrong), U8 (largest long-q
  |VR - 1| in 2020-23, not 2017-20) not met.
- Correction: Amendment 1's stationarity note missed that planted momentum with kappa >= +1 is a unit root / explosive; the
  +1.00 / +1.20 rows are not meaningful; bounds unaffected.
- Process note: `tools/prem2.py` and its tests were written outside the planning chat after the criteria commit; reviewed line
  by line before any run (build record).

## Counts

PREM2: 9 horizons on one series in one max-statistic; 4 post-read threshold looks (information). No strategy, slot or C1
variant. Project-wide full-strategy variants: 2 (unchanged). Confirmation set untouched.

## Next (separate decision, N7)

The trend-timing line closes on the dev set. Open directions (none chosen): (c) volatility, the one property that persists in
every dev market measured (H(|r|) 0.66-0.85), e.g. volatility-based sizing or regime filters; or stopping price-timing research
on this dev set.
