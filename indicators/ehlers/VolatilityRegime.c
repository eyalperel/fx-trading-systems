// =============================================================
// VolatilityRegime.c — percentile-rank volatility regime
//
// Not an Ehlers indicator. Built Week 13 Day 3 because Tier 1
// needs a regime label and no published classifier fits the
// project's no-retuning constraint.
//
// WHY PERCENTILE RANK. Measured NATR distributions barely overlap
// across assets: BTC/USD H4 p10 = 0.94% sits ABOVE EUR/USD D1
// median = 0.67%. A fixed NATR threshold therefore cannot label
// both assets — at 1.5% EUR/USD is never volatile, at 0.8% it
// flips constantly. Rank is 0-100 on any distribution, so one
// threshold means the same thing on both. See the NATR commit.
//
// Rank is also distribution-free. A z-score assumes roughly
// symmetric spread and a ratio-to-mean assumes the mean is a
// meaningful centre; volatility has a hard floor at zero and a
// long right tail, so both assumptions are wrong.
//
// KNOWN CHARACTERISTICS — inherent, not defects to fix:
//   1. Blind to magnitude. If NATR doubles across the whole
//      window, ranks barely move. Rank measures relative to
//      recent, never absolute.
//   2. Always finds all three regimes. In a genuinely calm
//      stretch the calmest bars still get labelled Volatile,
//      because something has to occupy the top band.
//   3. Self-defeating at long windows. The window needed for a
//      stable estimate is long enough to contain the regime
//      change being detected, so today is ranked against a
//      mixture of the old regime and the new.
//
// Parameters (chosen before seeing results, NOT swept):
//   Window     : 250 — ~1 trading year on D1, ~6 weeks on BTC H4.
//                Below ~100 the percentile estimate is imprecise;
//                above ~500 on D1 the reference is two years stale.
//   LoPct/HiPct: 30 / 70. Near even thirds, so almost no choice is
//                being made, with a slightly wider Normal band to
//                reduce flip-flopping at the boundaries.
//
// LOOKBACK: caller needs LookBack >= Window + smoother warmup.
//   With Window 250 and Length 20 that is 270 minimum. Too small
//   and the rank is computed against a partially filled window,
//   silently (GOTCHAS 4.2, and Warning 041).
//
// Locals prefixed vr_ (GOTCHAS 1.3).
//
// Returns: regime code 0 = Calm, 1 = Normal, 2 = Volatile
//          *pRank receives the raw 0-100 rank, which is more
//          informative than the bucket and lets thresholds be
//          re-cut in analysis without re-running Zorro.
// =============================================================

var VolatilityRegime(vars NATR, int Window, var LoPct, var HiPct,
                     var* pRank)
{
    int vr_i;
    var vr_below = 0;

    // Count how many of the last Window values are below today's.
    // Start at 1 so today is never compared with itself.
    for(vr_i = 1; vr_i < Window; vr_i++) {
        if(NATR[vr_i] < NATR[0]) vr_below += 1.0;
    }

    var vr_rank = 100.0 * vr_below / (Window - 1);
    *pRank = vr_rank;

    if(vr_rank < LoPct) return 0;    // Calm
    if(vr_rank > HiPct) return 2;    // Volatile
    return 1;                        // Normal
}
