"""LRSI stage 1: reference models for the Laguerre RSI (reference.lrsi_article, simulate_lrsi, lrsi_superseded / simulate_lrsi_shared,
the analytic L0 / L3 tables) against
  * the planning chat's (b) numbers of docs/harness/LRSI_STAGE1_PROMPT.md, findings 1-10 and the control effects
    (tables: <= 1e-12 absolute; effects: <= 1% relative, the brief's limits; every pair is printed);
  * the planning chat's independent float64 model docs/harness/LAGUERRERSI_REVIEW_MODEL.py (src / cfile), bar by bar;
  * one-filter simulations of L0 and L3 (the stages must agree with the transfer functions to <= 1e-12 after W).
The superseded model is checked for its shared statics: the run's only seed lands on the FIRST call of the call order, every later call
starts from zero history, and a CU + CD = 0 row returns the last ratio of ANY slot.
Rule (CLAUDE.md 4.4): each comparison is seen to fire. No .c file is read, Zorro is not run.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lrs_support as S      # noqa: E402

C, R = S.C, S.R
TS = S.TS
N, W = 3000, 700
LVL, AMP, SLP = 1.1, 0.01, 1e-4
GAM = {"G05": 0.5, "G07": 0.7, "G08": 0.8}

# ---- planning-chat (b) values, docs/harness/LRSI_STAGE1_PROMPT.md (copied verbatim)
BRIEF_TABLE = {
    0.5: dict(gain=[0.515441182073583, 0.752937760164676, 0.9144826257394167, 0.9762503597414621, 0.9960766670440261],
              p0=[-0.5123349109077545, -0.4584578266589488, -0.286493792460628, -0.15331917019845434, -0.06258501979842945],
              p3=[-1.073070253482447, 1.1890249284130687, -2.947934343301334, -1.5444730894276493, -0.6265906978043936],
              alt=0.3333333333333333, lag=(1.0, 10.0), lag_meas=(1.0000000000002451, 9.999999999999586)),
    0.7: dict(gain=[0.29174705961302644, 0.5018320986484869, 0.7534909167069183, 0.9161156395618575, 0.9849968569076663],
              p0=[-0.7042011354674697, -0.7590908589631391, -0.5743590867142185, -0.34096299632055205, -0.14481875420461615],
              p3=[-2.416133825400453, -0.9154062977162627, 1.3201939041031179, -2.857979872282333, -1.2022268386477006],
              alt=0.17647058823529416, lag=(2.333333333333333, 19.33333333333333), lag_meas=(2.333333333333565, 19.333333333332867)),
    0.8: dict(gain=[0.18686099078895038, 0.3402202928517172, 0.5814602765397503, 0.8185547295323827, 0.9627270885276253],
              p0=[-0.7907222675568412, -0.9271383721938123, -0.8019659985004615, -0.5377451535315523, -0.24422102259248527],
              p3=[-3.021781750026053, -2.0917388903309746, -0.2730544784005824, 2.047730334420252, -1.8980427173627845],
              alt=0.11111111111111109, lag=(4.0, 31.0), lag_meas=(4.000000000000736, 31.00000000000109)),
}
BRIEF_GATE = {0.5: [1.5444174181677983, 1.5613948955003787, 1.2521910177791584, 0.42901079963528765, 0.07555156262124552],
              0.7: [0.5261922807346053, 1.5640737397439874, 1.2212991432978937, 1.1313729412971263, 0.24451738161783698],
              0.8: [0.31807224827549163, 0.8264689338118414, 1.5603221435723125, 1.4936947619025975, 0.5505114253350429]}
BRIEF_GATE_ALT = {0.5: 2.0, 0.7: 1.0588, 0.8: 0.6667}
BRIEF_INVARIANCE = {0.5: (2.8621549574836536e-13, 1.0507150705052481e-12), 0.7: (1.7408297026122455e-13, 3.647082635893639e-13),
                    0.8: (1.3777867735598193e-13, 3.011202398539581e-13)}
BRIEF_STARTUP_G05_T20 = [0.7142857142857142, 0.7148014911433533, 0.8001802080788746, 1.0]
BRIEF_MEMORY = {0.5: 61, 0.7: 120, 0.8: 196}
BRIEF_PIN = {0.5: [0, 0, 0.50, 0.70, 0.88], 0.7: [0, 0, 0.10, 0.45, 0.78], 0.8: [0, 0, 0, 0.20, 0.66]}
BRIEF_RAMP = {0.5: (3, 23), 0.7: (6, 43), 0.8: (10, 68)}
BRIEF_NCG = dict(trace=[8.587296356932228e-05, 0.0006342174551938473, 0.0007133515100741228, 0.0008146242189909225, 0.0008469690514941175],
                 startup=[0.002158791270517657, 0.0013738308618160833, 0.0048423698983621755, 0.0021575680392890706, 0.0008838074092193393],
                 gain=0.0011355290725825196, phase=0.0013338316280936402, lag=1.004008016031932)
BRIEF_NC25 = dict(trace=[0.38513302852097764, 0.3487701068339998, 0.30284144990303796, 0.2945505035341127, 0.2937768393508384],
                  gain=0.44485552574684356, phase=1.5370047327232406, lag=7.000000000000228)
BRIEF_NCP_STARTUP = [0.5979633949986088, 0.9392821926106899, 0.9233174011464185, 0.6160813372907071, 0.2142857142857142]
BRIEF_NCS_S5 = 0.5979633949986088

REPORT = []


def inputs():
    n = np.arange(N, dtype=float)
    x = {"flat": np.full(N, LVL)}
    for t in TS:
        x["s%d" % t] = LVL + AMP * np.sin(2 * math.pi * n / t)
    x["alt"] = LVL + AMP * (1.0 - 2.0 * (n % 2))
    x["ramp"] = LVL + SLP * n
    x["rampdn"] = LVL - SLP * n
    return x


X = inputs()


def sim(m, k):
    return R.simulate_lrsi(m, X[k])


def rel(a, b):
    return abs(a - b) / abs(b) if b else abs(a)


class TestAnalyticTables(unittest.TestCase):
    def test_01_l0_l3_tables_vs_brief(self):
        worst = 0.0
        for g, b in BRIEF_TABLE.items():
            for st, ph in ((0, b["p0"]), (3, b["p3"])):
                for t, ge, pe in zip(TS, b["gain"], ph):
                    worst = max(worst, abs(R.lrsi_gain(g, st, t) - ge), abs(C.wrap_phase(R.lrsi_phase(g, st, t) - pe)))
                worst = max(worst, abs(R.lrsi_gain(g, st, 2) - b["alt"]), abs(R.lrsi_lag(g, st) - b["lag"][1 if st else 0]))
                self.assertEqual(R.lrsi_alt_phase(g, st), 0.0 if st == 0 else math.pi)
        REPORT.append("finding 1 tables (gain / phase / alt gain / lag, 3 gammas x L0, L3) vs brief: max |diff| %.3e" % worst)
        self.assertLessEqual(worst, 1e-12)

    def test_02_l3_gain_equals_l0_gain_and_dc_gain_is_one(self):
        for g in GAM.values():
            for t in TS + (2, 3, 7):
                self.assertAlmostEqual(R.lrsi_gain(g, 3, t), R.lrsi_gain(g, 0, t), delta=1e-15)
            self.assertAlmostEqual(abs(R.lrsi_h(g, 3, 0.0)), 1.0, delta=1e-15)
            self.assertAlmostEqual(R.lrsi_h(g, 3, math.pi).real, -(1 - g) / (1 + g), delta=1e-15)     # alt phase pi, gain (1-g)/(1+g)

    def test_03_product_form_matches_the_one_filter_form(self):
        """The (b, a) filters (used by simulations) and the product form agree; the expanded L3 polynomial is only ~1e-12 accurate."""
        for g in GAM.values():
            for t in TS:
                self.assertAlmostEqual(R.gain_at(R.lrsi_l0_filter(g), t), R.lrsi_gain(g, 0, t), delta=1e-15)
                self.assertAlmostEqual(R.gain_at(R.lrsi_l3_filter(g), t), R.lrsi_gain(g, 3, t), delta=1e-11)
            self.assertAlmostEqual(R.ramp_lag(R.lrsi_l3_filter(g)), R.lrsi_lag(g, 3), delta=1e-11)

    def test_04_the_table_comparison_fires(self):
        self.assertGreater(abs(R.lrsi_gain(0.501, 0, 20) - BRIEF_TABLE[0.5]["gain"][2]), 1e-12)
        self.assertGreater(abs(R.lrsi_phase(0.5, 2, 20) - BRIEF_TABLE[0.5]["p3"][2]), 1e-12)        # L2 is not L3


class TestSimulationVsTransferFunctions(unittest.TestCase):
    def test_01_stages_agree_with_one_filter_simulations_after_W(self):
        worst = 0.0
        for g in GAM.values():
            for k in X:
                a = sim(R.lrsi_article(g), k)
                worst = max(worst, float(np.max(np.abs(a.l0[W:] - R.simulate(R.lrsi_l0_filter(g), X[k], seed="zero")[W:]))),
                            float(np.max(np.abs(a.l3[W:] - R.simulate(R.lrsi_l3_filter(g), X[k], seed="zero")[W:]))))
        REPORT.append("stages vs one-filter simulations, rows >= W, 3 gammas x 9 inputs: max |diff| %.3e (limit 1e-12)" % worst)
        self.assertLessEqual(worst, 1e-12)
        b = R.simulate(R.lrsi_l0_filter(0.501), X["s20"], seed="zero")                       # fires
        self.assertGreater(float(np.max(np.abs(sim(R.lrsi_article(0.5), "s20").l0[W:] - b[W:]))), 1e-6)

    def test_02_ramp_lag_measured_vs_brief(self):
        worst = 0.0
        for g, b in BRIEF_TABLE.items():
            a = sim(R.lrsi_article(g), "ramp")
            for st, arr in ((0, a.l0), (1, a.l3)):
                m = float(np.mean((X["ramp"][-100:] - arr[-100:]) / SLP))
                worst = max(worst, abs(m - b["lag_meas"][st]))
                self.assertAlmostEqual(m, b["lag"][st], delta=1e-9)
        REPORT.append("finding 1 measured ramp lag vs brief: max |diff| %.3e" % worst)
        self.assertLessEqual(worst, 1e-12)


class TestVsReviewModel(unittest.TestCase):
    """Bar-by-bar against the planning chat's independent model (src = the source, cfile = the old .c)."""

    @classmethod
    def setUpClass(cls):
        cls.M = S.review_model()

    def test_01_source_model(self):
        worst = 0.0
        for g in GAM.values():
            for k in X:
                o, L, d = self.M.src(X[k], g)
                a = sim(R.lrsi_article(g), k)
                worst = max(worst, float(np.max(np.abs(a.out - o))), float(np.max(np.abs(a.l0 - L[:, 0]))),
                            float(np.max(np.abs(a.l3 - L[:, 3]))), float(np.max(np.abs(a.den - d))))
        REPORT.append("lrsi_article vs review src (out, L0, L3, CU+CD; 3 gammas x 9 inputs, every row): max |diff| %.3e" % worst)
        self.assertLessEqual(worst, 1e-12)

    def test_02_price_seed_model_is_the_old_file_per_instance(self):
        for g in GAM.values():
            for k in X:
                c = self.M.cfile(X[k], g, seeded=True, prev=0.5)
                a = sim(R.lrsi_article(g, seed="price", hold0=0.5), k)
                self.assertLessEqual(float(np.max(np.abs(a.out - c))), 1e-12, (g, k))
            for k in ("s5", "s20", "alt", "ramp"):                    # hold never fires there: hold0 irrelevant
                self.assertLessEqual(float(np.max(np.abs(sim(R.lrsi_article(g, seed="price"), k).out
                                                        - self.M.cfile(X[k], g)))), 1e-12)

    def test_03_comparison_fires(self):
        o, _, _ = self.M.src(X["s20"], 0.5)
        z = np.zeros(N)                                    # hold0 is visible only before a first defined value: an all-zero input
        self.assertEqual(float(np.max(np.abs(R.simulate_lrsi(R.lrsi_article(0.5, hold0=0.5), z).out - self.M.src(z, 0.5, hold0=0.5)[0]))), 0.0)
        self.assertEqual(float(np.max(np.abs(R.simulate_lrsi(R.lrsi_article(0.5, hold0=0.5), z).out - self.M.src(z, 0.5)[0]))), 0.5)
        self.assertEqual(float(np.max(np.abs(sim(R.lrsi_article(0.5, hold0=0.5), "flat").out - self.M.src(X["flat"], 0.5)[0]))),
                         float(np.max(np.abs(sim(R.lrsi_article(0.5), "flat").out - self.M.src(X["flat"], 0.5)[0]))))     # NCH invisible on flat
        self.assertGreater(float(np.max(np.abs(sim(R.lrsi_article(0.5, form="tasc2025"), "s20").out - o))), 0.1)


class TestFindings(unittest.TestCase):
    def test_03_gate_margins(self):
        worst = 0.0
        for g, vals in BRIEF_GATE.items():
            for t, v in zip(TS, vals):
                worst = max(worst, abs(float(np.min(sim(R.lrsi_article(g), "s%d" % t).den[200:] / AMP)) - v))
            self.assertAlmostEqual(float(np.min(sim(R.lrsi_article(g), "alt").den[200:] / AMP)), BRIEF_GATE_ALT[g], delta=1e-4)
        REPORT.append("finding 3 gate margins vs brief: max |diff| %.3e; tightest 0.0756 (G05, T = 100) vs gate 0.01" % worst)
        self.assertLessEqual(worst, 1e-12)

    def test_04_bound_every_row_every_input(self):
        lo, hi = 1.0, 0.0
        for g in GAM.values():
            for k in X:
                o = sim(R.lrsi_article(g), k).out
                lo, hi = min(lo, float(o.min())), max(hi, float(o.max()))
        self.assertEqual((lo, hi), (0.0, 1.0))                     # attained exactly (pinning)

    def test_05_invariance(self):
        n = np.arange(N, dtype=float)
        for g, (sc, of) in BRIEF_INVARIANCE.items():
            mk = mf = 0.0
            for t in TS:
                b = R.simulate_lrsi(R.lrsi_article(g), X["s%d" % t]).out
                s_ = R.simulate_lrsi(R.lrsi_article(g), 1.1 + 0.1 * np.sin(2 * math.pi * n / t)).out
                o_ = R.simulate_lrsi(R.lrsi_article(g), 2.2 + 0.01 * np.sin(2 * math.pi * n / t)).out
                mk, mf = max(mk, float(np.max(np.abs(s_[W:] - b[W:])))), max(mf, float(np.max(np.abs(o_[W:] - b[W:]))))
            REPORT.append("finding 5 invariance g=%g scale10 / offset: model %r / %r, brief %r / %r" % (g, mk, mf, sc, of))
            self.assertLess(max(mk, mf), 1e-11)
            self.assertLessEqual(abs(mk - sc), 1e-12)
            self.assertLessEqual(abs(mf - of), 1e-12)

    def test_06_startup_rows_and_memory(self):
        a = sim(R.lrsi_article(0.5), "s20").out
        d = max(abs(a[r] - v) for r, v in enumerate(BRIEF_STARTUP_G05_T20))
        REPORT.append("finding 6 start-up G05 T=20 rows 0-3 %r vs brief: max |diff| %.3e" % (a[:4].tolist(), d))
        self.assertLessEqual(d, 1e-12)
        for g, last in BRIEF_MEMORY.items():
            lr = max(int(np.nonzero(np.abs(sim(R.lrsi_article(g), "s%d" % t).out - sim(R.lrsi_article(g, seed="price"), "s%d" % t).out)
                                    > 1e-12)[0].max()) for t in TS)
            self.assertEqual(lr, last, g)
        self.assertLess(max(BRIEF_MEMORY.values()) * 3.5, W)        # W = 700 = 3.6x the largest memory

    def test_07_pinning(self):
        for g, vals in BRIEF_PIN.items():
            for t, v in zip(TS, vals):
                o = sim(R.lrsi_article(g), "s%d" % t).out[200:]
                self.assertAlmostEqual(float(np.mean((o == 0) | (o == 1))), v, delta=0.005, msg=(g, t))

    def test_08_ramp_known_answers(self):
        for g, (up, dn) in BRIEF_RAMP.items():
            r = sim(R.lrsi_article(g), "ramp").out
            self.assertTrue(np.all(r[up:] == 1.0) and r[up - 1] != 1.0, g)
            f = sim(R.lrsi_article(g), "rampdn").out
            self.assertTrue(np.all(f[dn + 1:] == 0.0) and f[dn] != 0.0, g)

    def test_09_alt_alternates_between_one_third_and_two_thirds(self):
        dev = {}
        for g in GAM.values():
            o = sim(R.lrsi_article(g), "alt").out[W:]
            self.assertEqual(len(np.unique(o)), 2)
            dev[g] = max(abs(float(o.min()) - 1 / 3), abs(float(o.max()) - 2 / 3))
            self.assertLess(dev[g], 1e-12, g)
        REPORT.append("finding 9 alt out = 1/3, 2/3 rows >= W: max |diff| from 1/3, 2/3: G05 %.1e, G07 %.1e, G08 %.1e "
                      "(brief: 'exactly'; G08 is not bit-exact)" % (dev[0.5], dev[0.7], dev[0.8]))

    def test_10_flat(self):
        a = sim(R.lrsi_article(0.5), "flat")
        z = np.nonzero(a.den == 0)[0]
        self.assertEqual(int(z.min()), 69)
        self.assertTrue(np.all(a.den[69:] == 0) and np.all(a.out[68:] == 1.0))
        for g in (0.7, 0.8):
            self.assertFalse(np.any(sim(R.lrsi_article(g), "flat").den == 0), g)


class TestControlEffects(unittest.TestCase):
    """Control effects vs the G05 model (rows >= W: trace; rows < W: start-up) and the analytic linear effects, vs the brief (1%)."""

    def _cmp(self, name, model, key, brief):
        worst = 0.0
        for t, b in zip(TS, brief):
            a, g = sim(model, "s%d" % t).out, sim(R.lrsi_article(0.5), "s%d" % t).out
            v = float(np.max(np.abs(a[W:] - g[W:]))) if key == "trace" else float(np.max(np.abs(a[:W] - g[:W])))
            worst = max(worst, rel(v, b))
        REPORT.append("%s %s by T vs brief: max relative diff %.3e" % (name, key, worst))
        self.assertLessEqual(worst, 0.01)

    def test_01_ncg(self):
        m = R.lrsi_article(0.5, g_l0=0.5 + 1.0 / 1000)
        self._cmp("NCG", m, "trace", BRIEF_NCG["trace"])
        self._cmp("NCG", m, "startup", BRIEF_NCG["startup"])
        q = 0.5 + 1.0 / 1000
        gmax = max(abs(R.lrsi_gain(q, 0, t) - R.lrsi_gain(0.5, 0, t)) for t in TS)
        pmax = max(abs(R.lrsi_phase(q, 0, t) - R.lrsi_phase(0.5, 0, t)) for t in TS)
        for a, b in ((gmax, BRIEF_NCG["gain"]), (pmax, BRIEF_NCG["phase"]), (R.lrsi_lag(q, 0), BRIEF_NCG["lag"])):
            self.assertLessEqual(rel(a, b), 0.01, (a, b))
        REPORT.append("NCG gain / phase / lag analytic %r / %r / %r vs brief %r / %r / %r"
                      % (gmax, pmax, R.lrsi_lag(q, 0), BRIEF_NCG["gain"], BRIEF_NCG["phase"], BRIEF_NCG["lag"]))

    def test_02_nc25(self):
        m = R.lrsi_article(0.5, form="tasc2025")
        self._cmp("NC25", m, "trace", BRIEF_NC25["trace"])
        a = sim(m, "ramp")
        lag3 = float(np.mean((X["ramp"][-100:] - a.l3[-100:]) / SLP))
        self.assertLessEqual(rel(lag3, BRIEF_NC25["lag"]), 0.01)
        self.assertEqual(float(np.max(np.abs(a.l0 - sim(R.lrsi_article(0.5), "ramp").l0))), 0.0)      # L0 unchanged

    def test_03_ncp(self):
        self._cmp("NCP", R.lrsi_article(0.5, seed="price"), "startup", BRIEF_NCP_STARTUP)
        for t in TS:
            a, g = sim(R.lrsi_article(0.5, seed="price"), "s%d" % t).out, sim(R.lrsi_article(0.5), "s%d" % t).out
            self.assertEqual(float(np.max(np.abs(a[W:] - g[W:]))), 0.0)                                  # trace 0

    def test_04_nch_is_invisible(self):
        for k in X:
            if k == "flat":
                continue
            self.assertEqual(float(np.max(np.abs(sim(R.lrsi_article(0.5, hold0=0.5), k).out - sim(R.lrsi_article(0.5), k).out))), 0.0, k)


class TestSupersededSharedStatics(unittest.TestCase):
    """simulate_lrsi_shared: the old file's lr_init / lr_prevRSI shared by every call slot in call order."""

    BASE_NO_FLAT = ["s5", "s10", "s20", "s40", "s100", "alt", "ramp", "rampdn"]

    def test_01_only_the_first_call_of_the_run_seeds(self):
        M = S.review_model()
        outs = R.simulate_lrsi_shared([0.5, 0.5], [X["s5"], X["s10"]])
        self.assertLessEqual(float(np.max(np.abs(outs[0].out - M.cfile(X["s5"], 0.5, seeded=True)))), 1e-12)     # seeded instance
        self.assertLessEqual(float(np.max(np.abs(outs[1].out - M.cfile(X["s10"], 0.5, seeded=False)))), 1e-12)   # zero start
        self.assertEqual((outs[0].out[0], outs[0].l0[0], outs[0].den[0]), (0.5, X["s5"][0], 0.0))
        swapped = R.simulate_lrsi_shared([0.5, 0.5], [X["s10"], X["s5"]])                                         # the seed follows the order
        self.assertEqual(float(np.max(np.abs(swapped[1].out - sim(R.lrsi_article(0.5), "s5").out))), 0.0)

    def test_02_the_hold_is_shared(self):
        """Two zero-start slots: B on the falling ramp, then A on flat (gamma 0.5): from row 69 A has CU + CD = 0 and returns B's last
        ratio (0.0), not its own held 1.0."""
        outs = R.simulate_lrsi_shared([0.5, 0.5, 0.5], [X["s5"], X["rampdn"], X["flat"]])       # s5 takes the seed
        a = outs[2].out
        self.assertTrue(np.all(a[69:] == 0.0))
        self.assertTrue(np.all(sim(R.lrsi_article(0.5), "flat").out[69:] == 1.0))

    def test_03_ncs_layout_actual_call_order(self):
        """Amendment 1 A: NCS then NCT, both gamma 0.5, each on every base input except flat. The seed lands on NCS s5; its start-up effect
        vs the G05 model is the brief's 0.5979633949986088 (= NCP, T = 5); every other pair is bit-identical."""
        xs = [X[k] for k in self.BASE_NO_FLAT] * 2
        outs = R.simulate_lrsi_shared([0.5] * len(xs), xs)
        names = [("NCS", k) for k in self.BASE_NO_FLAT] + [("NCT", k) for k in self.BASE_NO_FLAT]
        res = {}
        for (vid, k), o in zip(names, outs):
            d = np.abs(o.out - sim(R.lrsi_article(0.5), k).out)
            nz = np.nonzero(d)[0]
            res[(vid, k)] = (float(d[:W].max()), float(d[W:].max()), int(nz.max()) if len(nz) else -1,
                             int(np.nonzero(d > 1e-12)[0].max()) if np.any(d > 1e-12) else -1)
        s5 = res[("NCS", "s5")]
        REPORT.append("NCS s5 start-up (actual call order) %r vs brief %r: rel %.3e; last row |diff| > 0: %d, > 1e-12: %d (brief: 60)"
                      % (s5[0], BRIEF_NCS_S5, rel(s5[0], BRIEF_NCS_S5), s5[2], s5[3]))
        self.assertLessEqual(rel(s5[0], BRIEF_NCS_S5), 0.01)
        self.assertEqual(s5[1], 0.0)
        self.assertEqual(s5[3], 60)
        for kk, v in res.items():
            if kk != ("NCS", "s5"):
                self.assertEqual(v[:2], (0.0, 0.0), kk)
        # the first-call-on-flat layout (stage-1 STOP): seed on flat, no sine differs -> the reason for Amendment 1 A
        xs = [X[k] for k in ["flat"] + self.BASE_NO_FLAT] * 2
        outs = R.simulate_lrsi_shared([0.5] * len(xs), xs)
        self.assertEqual(max(float(np.max(np.abs(o.out - sim(R.lrsi_article(0.5), k).out)))
                             for o, k in zip(outs, (["flat"] + self.BASE_NO_FLAT) * 2) if k != "flat"), 0.0)


class TestModelGuards(unittest.TestCase):
    def test_01_bad_hooks_raise(self):
        with self.assertRaises(ValueError):
            R.lrsi_article(0.5, form="2025")
        with self.assertRaises(ValueError):
            R.lrsi_article(0.5, seed="first")

    def test_02_article_model_grammar(self):
        self.assertEqual(R.lrsi_article_model("lrsi_article(7/10)"), R.lrsi_article(0.7))
        for bad in ("lrsi_article(0.7)", "lrsi_article(10/7)", "lrsi_article(0/2)", "lrsi_article(1/0)", "lrsi_article(1/2,seed=price)", None):
            self.assertIsNone(R.lrsi_article_model(bad), bad)
        self.assertIsInstance(R.osc_article_model("lrsi_article(1/2)"), R.LrsiModel)

    def test_03_registry(self):
        for k in ("lrsi_article(1/2)", "lrsi_article(7/10)", "lrsi_article(4/5)", "lrsi_article(1/2,hold0=1/2)",
                  "lrsi_article(1/2,g_l0=1/2+1/1000)", "lrsi_article(1/2,form=tasc2025)", "lrsi_article(1/2,seed=price)"):
            self.assertIsInstance(R.IMP_MODELS[k](), R.LrsiModel, k)
        self.assertEqual(R.IMP_MODELS["lrsi_superseded(1/2,1/2)[1]"](), R.LrsiShared(gs=(0.5, 0.5), index=1))
        self.assertEqual(R.IMP_MODELS["lrsi_article(1/2,g_l0=1/2+1/1000)"]().g_l0, 0.5 + 1.0 / 1000)


def tearDownModule():
    print()
    for line in REPORT:
        print("  " + line)


if __name__ == "__main__":
    unittest.main()
