# Null-Hypothesis Testing of the Ehlers Cycle Premise

Surrogate-data test of whether `RoofingFilter → CyberCycle` output on real
markets is distinguishable from its output on data containing no cycle by
construction.

**Result:** 48 tests (6 metrics × 4 nulls × 2 assets), none significant,
minimum p = 0.070. Real markets scored *lower* on spectral peak prominence
than the noise nulls.

Full method and results: `docs/research/Cycle_Premise_Null_Test.md`
Project impact: `docs/research/Cycle_Premise_Conclusions_and_Impact.md`

---

## Layout

```
src/pipeline.py       Zorro-validated port of HighPassFilter → SuperSmoother2Pole
                      → CyberCycle. Loop version (readable reference) and
                      lfilter version (~36x faster), cross-checked.
src/surrogates.py     DFA Hurst, Davies-Harte fGn, IAAFT, stochastic vol,
                      sinusoid positive control.
src/metrics.py        Six detection statistics. BURN_IN = 300.
run_experiment.py     EUR/USD D1 arm.
run_btc.py            BTC/USD H4 arm (different null calibration only).
out/                  p-values, null distributions, power curves.
```

Zorro export scripts live in `strategies/tests/`:
`Test_CyberCycle_Surrogate.c`, `Test_CyberCycle_Surrogate_BTC.c`

## Reproducing

```bash
cd analysis/null_tests
mkdir -p data out
cp /c/zorro/Data/CyberCycle_Surrogate_*.csv data/
python run_experiment.py     # ~6 min
python run_btc.py            # ~8 min
```

Seed 20260803, N = 1,000 surrogates per null. Requires numpy, scipy, pandas.

## Validation gates passed

1. **Port fidelity** — Python reproduces Zorro output to 5.01e-06, exactly the
   `%.5f` CSV rounding floor. No formula discrepancy.
2. **Reproducibility** — the May 2026 Zorro run reproduced bit-for-bit in
   August 2026.
3. **Estimator calibration** — DFA recovers known Hurst from exact fGn within
   ±0.02 across H = 0.3–0.9.
4. **Generator validation** — every null reproduces its intended statistical
   properties and matches the real return marginal exactly.
5. **Metric discrimination** — prominence spans 2.25 (white noise) to
   5,976,270 (pure sine) through the same pipeline.
6. **Detection power** — a positive control establishes that a cycle carrying
   >4.4% (FX) / >5.0% (crypto) of return variance would be found with 95%
   probability.

Gate 6 is what makes the null result meaningful rather than unfalsifiable.

## Scope

Indicator-level behavioural validation. **Not** a strategy-level or P&L
validation. Tests one parameterisation (HP=48 / SS=10 / α=0.07), two assets,
and persistent fixed-period cycles. See Limitations in the main document.
