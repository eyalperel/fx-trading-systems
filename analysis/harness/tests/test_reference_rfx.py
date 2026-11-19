"""RFX stage 1: the Reflex reference models (reference.py) against independent code and the planning chat's findings 1-3.

(b) Measuring tool on a known answer first (CLAUDE.md 4.5): `simulate_reflex` is compared with a plain, differently
structured EasyLanguage-style translation written in this file; the analytic Sum filter with the simulated Sum; the shared-state
model (old Reflex.c) with an independent implementation and with its own order dependence.
Each guard is seen to fire on a deliberately broken input (CLAUDE.md 4.4).
Labels: (a) source states, (b) verified here, (c) inference.
"""
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HARNESS)

import checker as C      # noqa: E402
import reference as R    # noqa: E402

TS = (5, 10, 20, 40, 100)
N, W = 3000, 700
N_ = np.arange(N, dtype=float)
SINES = {t: 1.1 + 0.01 * np.sin(2 * math.pi * N_ / t) for t in TS}

# planning chat (b) Sum tables, 2026-11-18 (docs/harness/RFX_STAGE1_PROMPT.md finding 3): gain, phase at T = 5, 10, 20, 40, 100
BRIEF = {
    14: ([0.3641008319826905, 0.08821484136366424, 0.9416369733401999, 0.3541421970554636, 0.06291300715458427],
         [-0.9041809919287164, -2.105367309115726, 0.5522448949496477, 1.853766288996129, 2.627294939010228]),
    20: ([0.2241997820842597, 0.6950591600191403, 0.9661158676365323, 0.6334193273159906, 0.1261374255749415],
         [-1.853589240790186, -1.303784662009623, -0.6223438049722935, 1.276992794392404, 2.398116923276429]),
    21: ([0.1575089085020519, 0.598161031431481, 0.9030766266744574, 0.6793377458187358, 0.1385289322235242],
         [-2.516715492980711, -1.684589130000405, -0.8200519928703117, 1.180259661445638, 2.359782085656642]),
    30: ([0.1020866755606767, 0.3992220894808521, 0.1826694165145904, 0.9957600998886519, 0.2702131435617495],
         [-2.089593977937582, -1.820435239811435, 0.5327175540190705, 0.3032513983296208, 2.013718620121099]),
}


def independent_reflex(price, length, half=None, w1=0.04, w2=0.96, div=None):
    """Differently structured translation of the EasyLanguage sidebar: whole-array Filt first, then Sum / MS per bar with
    EasyLanguage-style indexing helper Filt[k] (clamped to the seeded history). No code shared with reference.py."""
    price = [float(v) for v in price]
    n = len(price)
    h = 0.5 * length if half is None else half
    a1 = math.exp(-1.4142135623730951 * 3.141592653589793 / h)
    b1 = 2 * a1 * math.cos(1.4142135623730951 * 180 / h * math.pi / 180)          # degrees, EasyLanguage style
    c2, c3 = b1, -a1 * a1
    c1 = 1 - c2 - c3
    filt = []

    def F(i, k):
        j = i - k
        return filt[j] if j >= 0 else price[0]

    def P(i, k):
        return price[i - k] if i - k >= 0 else price[0]

    rs, sums = [], []
    ms = 0.0
    for i in range(n):
        filt.append(c1 * (P(i, 0) + P(i, 1)) / 2 + c2 * F(i, 1) + c3 * F(i, 2))
        slope = (F(i, length) - F(i, 0)) / length
        s = 0.0
        for count in range(1, length + 1):
            s = s + (F(i, 0) + count * slope) - F(i, count)
        s = s / (length if div is None else div)
        ms = w1 * s * s + w2 * ms
        sums.append(s)
        rs.append(s / math.sqrt(ms) if ms != 0 else 0.0)
    return np.array(sums), np.array(rs)


class TestSimulateReflex(unittest.TestCase):
    def test_01_matches_an_independent_translation(self):
        x = 1.1 + 0.01 * np.sin(2 * math.pi * np.arange(400) / 7.0) + 1e-4 * np.arange(400) + 0.003 * np.cos(np.arange(400) ** 1.3)
        worst = 0.0
        for L in (5, 14, 20, 21):
            o = R.simulate_reflex(R.reflex_article(L), x)
            s, r = independent_reflex(x, L)
            worst = max(worst, np.max(np.abs(o.sum - s)), np.max(np.abs(o.r[60:] - r[60:])))        # rows < 60: r = noise / noise (finding 5)
        print("\n  simulate_reflex vs independent translation: largest |diff| %.3e (L = 5, 14, 20, 21)" % worst)
        self.assertLess(worst, 1e-12)

    def test_02_guard_fires_on_broken_models(self):
        x = SINES[20][:600]
        s, r = independent_reflex(x, 21)
        o_ok = R.simulate_reflex(R.reflex_article(21), x)
        self.assertLess(np.max(np.abs(o_ok.r - r)), 1e-12)
        for name, m in (("integer half length", R.reflex_article(21, half=10.0)),
                        ("weights 0.041/0.959", R.reflex_article(21, w1=0.041, w2=0.959)),
                        ("degrees in the cosine", R.reflex_article(21, deg=True)),
                        ("a1 + 1/1000", R.reflex_article(21, a1_add=0.001))):
            d = np.max(np.abs(R.simulate_reflex(m, x).r[300:] - r[300:]))
            print("  [fire] %-24s max |r - independent| %.3e" % (name, d))
            self.assertGreater(d, 1e-4, name)
        # divisor L-1: a pure scale error on Sum; the MS normalisation cancels it in r (NCK: trace 0) but not in Sum
        o_k = R.simulate_reflex(R.reflex_article(21, div=20), x)
        self.assertLess(float(np.max(np.abs(o_k.r[300:] - r[300:]))), 1e-12)
        self.assertGreater(float(np.max(np.abs(o_k.sum[300:] - o_ok.sum[300:]))), 1e-5)

    def test_03_first_bar_known_answer(self):
        """(b) n = 0: Filt history = x[0]; with a flat start Filt[0] = x0*(c1 + c2 + c3) = x0, Sum = 0, MS = 0, Reflex = 0."""
        o = R.simulate_reflex(R.reflex_article(20), np.full(50, 1.1))
        self.assertLess(float(np.max(np.abs(o.sum))), 1e-15)
        self.assertLess(float(np.max(np.abs(o.r))), 1e-15 / 1e-9 + 1e3)    # r can be noise/noise: only Sum is asserted
        self.assertEqual(float(o.ms[0]), 0.0 if o.sum[0] == 0.0 else float(o.ms[0]))

    def test_04_flat_input_gives_exactly_zero_in_the_article_model(self):
        o = R.simulate_reflex(R.reflex_article(20), np.full(N, 1.1))
        self.assertEqual(float(np.max(np.abs(o.r))), 0.0)
        self.assertEqual(float(np.max(np.abs(o.sum))), 0.0)


class TestFindings1to3(unittest.TestCase):
    def test_01_sum_is_the_fir_on_filt(self):
        """Finding 1: Sum = sum_k w_k Filt[n-k], w_0 = w_L = (L-1)/(2L), w_1..w_{L-1} = -1/L."""
        L = 20
        x = SINES[10]
        filt = R.simulate(R.ss2_article(L / 2.0), x)
        w = np.array([(L - 1.0) / (2 * L)] + [-1.0 / L] * (L - 1) + [(L - 1.0) / (2 * L)])
        fir = np.array([sum(w[k] * (filt[n - k] if n - k >= 0 else x[0]) for k in range(L + 1)) for n in range(len(x))])
        o = R.simulate_reflex(R.reflex_article(L), x)
        d = float(np.max(np.abs(o.sum[L + 2:] - fir[L + 2:])))
        print("\n  Sum vs FIR(Filt): max |diff| %.3e" % d)
        self.assertLess(d, 1e-14)
        self.assertGreater(float(np.max(np.abs(o.sum[L + 2:] - fir[L + 2:] * 1.01))), 1e-5)         # guard fires

    def test_02_transfer_function_matches_simulation(self):
        spec = dict(w=W, n_bars=N, amp=0.01, level=1.1, ts=TS)
        worst_g = worst_p = 0.0
        for L in (14, 20, 21, 30):
            f = R.reflex_sum_filter(L)
            for t in TS:
                o = R.simulate_reflex(R.reflex_article(L), SINES[t])
                worst_g = max(worst_g, abs(C.m_gain(spec, o.sum, t) - R.gain_at(f, t)))
                worst_p = max(worst_p, abs(C.wrap_phase(C.m_phase(spec, o.sum, t) - R.phase_at(f, t))))
        print("\n  Sum simulated vs H_Sum (4 L x 5 T): max |gain| %.3e, max |phase| %.3e" % (worst_g, worst_p))
        self.assertLess(worst_g, 1e-13)
        self.assertLess(worst_p, 1e-13)
        # guard fires: the transfer function of another length is far away
        self.assertGreater(abs(C.m_gain(spec, R.simulate_reflex(R.reflex_article(20), SINES[20]).sum, 20)
                               - R.gain_at(R.reflex_sum_filter(22), 20)), 1e-3)

    def test_03_dc_gain_zero_and_double_zero(self):
        for L in (14, 20, 21, 30):
            f = R.reflex_sum_filter(L)
            self.assertLess(R.dc_gain(f), 1e-15)
            self.assertLess(abs(R.ramp_residual(f, 1.1, 1e-4)), 1e-15)
        # guard: the same arithmetic does NOT vanish for a filter that has no double zero (plain SuperSmoother, DC gain 1)
        self.assertGreater(abs(R.ramp_residual(R.ss2_article(10), 1.1, 1e-4)), 1e-4)

    def test_04_loop_end_terms_are_identically_zero(self):
        """Finding 2: k = L gives (F0 + L*Slope) - F_L = 0 and k = 0 gives 0, so a loop bound off by one changes nothing."""
        L = 20
        x = SINES[20]
        m = R.reflex_article(L)
        c1, c2, c3 = R._reflex_coefs(m)
        F = [x[0]] * (L + 2)
        worst_terms = worst_sum = 0.0
        for n in range(len(x)):
            F.append(c1 * (x[n] + (x[n - 1] if n else x[0])) / 2.0 + c2 * F[-1] + c3 * F[-2])
            t = len(F) - 1
            slope = (F[t - L] - F[t]) / L
            terms = [(F[t] + k * slope) - F[t - k] for k in range(0, L + 1)]
            worst_terms = max(worst_terms, abs(terms[0]), abs(terms[L]))
            worst_sum = max(worst_sum, abs(sum(terms[1:L + 1]) - sum(terms[0:L + 1])), abs(sum(terms[1:L + 1]) - sum(terms[1:L])))
        print("\n  loop end terms: max |term k=0|, |term k=L| %.3e; Sum unchanged by either bound: %.3e" % (worst_terms, worst_sum))
        self.assertEqual(worst_terms, 0.0)
        self.assertEqual(worst_sum, 0.0)

    def test_05_tables_match_the_planning_chat_values(self):
        worst = 0.0
        for L, (g, p) in BRIEF.items():
            f = R.reflex_sum_filter(L)
            for t, gv, pv in zip(TS, g, p):
                worst = max(worst, abs(R.gain_at(f, t) - gv), abs(R.phase_at(f, t) - pv))
        print("\n  Sum tables vs the planning chat's (b) values: max |diff| %.3e" % worst)
        self.assertLess(worst, 1e-13)
        f = R.reflex_sum_filter(20)
        self.assertGreater(abs(R.gain_at(f, 20) - BRIEF[21][0][2]), 1e-3)                              # guard fires

    def test_06_phase_at_T_eq_L_is_the_supersmoother_half_phase(self):
        """Finding 4: G(T = L) = 1, so Sum's phase at T = L is the SuperSmoother(L/2) phase."""
        for L in (14, 20, 21, 30):
            z = np.exp(-1j * 2 * math.pi / L)
            G = (L - 1.0) / (2 * L) * (1 + z ** L) - sum(z ** k for k in range(1, L)) / L
            self.assertLess(abs(G - 1), 1e-14)
            self.assertAlmostEqual(R.phase_at(R.reflex_sum_filter(L), L), R.phase_at(R.ss2_article(L / 2.0), L), places=13)

    def test_07_bound_and_where_it_is_attained(self):
        """Finding 6: MS >= 0.04 Sum^2 so |r| <= 5; attained on the first non-zero Sum row. Float32 weights break it."""
        worst = 0.0
        for L in (14, 20, 21, 30):
            for k in ("flat", "ramp"):
                x = np.full(N, 1.1) if k == "flat" else 1.1 + 1e-4 * N_
                worst = max(worst, float(np.max(np.abs(R.simulate_reflex(R.reflex_article(L), x).r))))
            for t in TS:
                worst = max(worst, float(np.max(np.abs(R.simulate_reflex(R.reflex_article(L), SINES[t]).r))))
        print("\n  max |Reflex| over all rows, inputs, 4 L: %.12f" % worst)
        self.assertLessEqual(worst, 5.0 * (1 + 1e-12))
        self.assertGreater(worst, 5.0 - 1e-9)
        o = R.simulate_reflex(R.reflex_article(20, w1=R.F32_004, w2=R.F32_096), SINES[20])
        self.assertGreater(float(np.max(np.abs(o.r))), 5.0 * (1 + 1e-9))                               # guard fires


class TestSharedStateAndGrammar(unittest.TestCase):
    def old_independent(self, price, length, ms):
        """The old Reflex.c for ONE call per bar, written separately: SS2 (integer half, Zorro PI), float32 weights."""
        filt = R.simulate(R.ss2_code(length // 2), price)
        F = [filt[0]] * (length + 2) + list(filt)
        out = []
        for n in range(len(price)):
            t = n + length + 2
            slope = (F[t - length] - F[t]) / length
            s = 0.0
            for i in range(1, length + 1):
                s += (F[t] + i * slope) - F[t - i]
            s /= length
            ms = R.F32_004 * s * s + R.F32_096 * ms
            out.append(s / math.sqrt(ms) if ms > 0 else 0.0)
        return np.array(out)

    def test_01_single_slot_equals_an_independent_old_reflex(self):
        o = R.simulate_shared([20], [SINES[10][:800]])[0]
        d = float(np.max(np.abs(o.r - self.old_independent(SINES[10][:800], 20, 0.0))))
        self.assertLess(d, 1e-12)

    def test_02_two_slots_share_one_ms_and_order_matters(self):
        x1, x2 = SINES[10][:900], SINES[20][:900]
        a = R.simulate_shared([20, 14], [x1, x2])
        b = R.simulate_shared([14, 20], [x2, x1])                      # the same two calls, other order
        alone = R.simulate_shared([20], [x1])[0]
        self.assertGreater(float(np.max(np.abs(a[0].r[700:] - alone.r[700:]))), 0.01)              # shared MS changes it
        self.assertGreater(float(np.max(np.abs(a[0].r[700:] - b[1].r[700:]))), 0.01)               # call order matters
        # the replay of the right order reproduces itself exactly (guard for the order test above)
        again = R.simulate_shared([20, 14], [x1, x2])
        self.assertEqual(float(np.max(np.abs(a[0].r - again[0].r))), 0.0)

    def test_03_old_file_has_the_integer_half_length(self):
        """R-2: L = 21 smooths at period 10 in the old file; reflex_code(21, half=10) is the same filter stage."""
        o_old = R.simulate_shared([21], [SINES[10]])[0]
        o_nch = R.simulate_reflex(R.reflex_code(21, half=10.0, w1=R.F32_004, w2=R.F32_096), SINES[10])
        self.assertLess(float(np.max(np.abs(o_old.sum[30:] - o_nch.sum[30:]))), 1e-6)             # start-up seed differs only early
        self.assertGreater(float(np.max(np.abs(o_old.sum[700:] - R.simulate_reflex(R.reflex_code(21), SINES[10]).sum[700:]))), 1e-4)

    def test_04_article_model_grammar(self):
        self.assertEqual(R.reflex_article_model("reflex_article(20)"), R.reflex_article(20))
        for bad in ("reflex_article(0)", "reflex_article(20);", "reflex_article(20.5)", "reflex_article( 20)", "x", None, "__import__('os')",
                    "reflex_article(20)+1", "reflex_article(99999)"):
            self.assertIsNone(R.reflex_article_model(bad), bad)

    def test_05_imp_registry_entries_resolve(self):
        for k in ("reflex_code(14)", "reflex_code(20)", "reflex_code(21)", "reflex_code(30)", "reflex_code(22)", "reflex_article(20)",
                  "reflex_nca(20)", "reflex_nc2(20)", "reflex_nch(21)", "reflex_nck(20)", "reflex_ncw(20)", "reflex_printed(20)",
                  "reflex_superseded(20,14)[0]", "reflex_superseded(20,14)[1]"):
            m = R.IMP_MODELS[k]()
            self.assertIsInstance(m, (R.ReflexModel, R.SharedModel), k)
        self.assertEqual(R.IMP_MODELS["reflex_superseded(20,14)[1]"](), R.SharedModel(Ls=(20, 14), index=1))
        self.assertEqual(R.reflex_code(20).pi_exp, R.PI_ZORRO)
        self.assertEqual(R.F32_004, float(np.float32(0.04)))


if __name__ == "__main__":
    unittest.main()
