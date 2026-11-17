"""Pre-run condition (iii) for HPF: reference.py reproduces the numbers pre-registered in specs/HP_ArticleFidelity.toml.

Sections: expected tables, [floor], every [variants.effect], [literal_info], [imp].fire_test_effect (+ registry).
Tolerance: <= 1e-9 absolute, relative 1e-9 for |value| > 1 (CLAUDE.md / task rule). Quantities the spec stores to FEWER
digits (the per-P floor text and the fire-test text, 4 significant digits) are compared at the digits stored, and the
largest absolute difference is still printed. No .c file is read; Zorro is not run.
Measurements use the checker's own functions (checker.check_rows / m_gain / m_phase / m_startup / m_ramp_res), as the
spec says. A number the reference does not reproduce FAILS its test (never loosened to pass).
Each section prints "(iii) <section>: largest deviation ..." for the amendment record.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import math
import os
import re
import sys
import unittest

import numpy as np

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HARNESS)

import checker as C      # noqa: E402
import generator as G    # noqa: E402
import reference as R    # noqa: E402

SPEC_PATH = os.path.join(HARNESS, "specs", "HP_ArticleFidelity.toml")
TS = (5, 10, 20, 40, 100)
PERIODS = (20, 30, 48, 125)
KINDS = ("flat", "gain", "phase", "resid", "startup")
TOL = 1e-9
SQ = math.sqrt(2.0) / 2.0
DEV = {}                      # section -> largest deviation seen (printed at the end)


def dev(expected, actual):
    """Deviation under the rule: absolute, or relative when |expected| > 1."""
    d = abs(actual - expected)
    return d / abs(expected) if abs(expected) > 1 else d


def within(expected, actual, tol=TOL):
    return dev(expected, actual) <= tol


def note(section, expected, actual, tol=TOL):
    """Record the deviation for the section and return True when within tol."""
    d = dev(expected, actual)
    DEV[section] = max(DEV.get(section, 0.0), d)
    return d <= tol


def sig(v, n):
    return float("%.*e" % (n - 1, v))


def load_spec():
    with open(SPEC_PATH, "rb") as f:
        return tomllib.load(f)


def floats(text):
    return [float(v) for v in re.findall(r"\d\.\d+e[-+]\d+", text)]


@unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
class TestHPReferenceVsSpec(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = load_spec()
        cls.cs = G.to_checker_spec(G.load_spec(SPEC_PATH))
        cls.x = C.make_inputs(cls.cs)
        cls.names = C.input_names(cls.cs)
        imp = cls.spec["imp"]["must_pass"]
        # per variant: own-model output on every input (the model strings are the registry's), then the checker's rows
        cls.y, cls.rows, cls.kind_max = {}, {}, {}
        for v in cls.cs["variants"]:
            f = R.IMP_MODELS[imp[v["id"]]]()
            yv = {i: R.simulate(f, cls.x[i], seed=v["seed"]) for i in cls.names}
            rows = C.check_rows(cls.cs, v, cls.x, yv)
            cls.y[v["id"]], cls.rows[v["id"]] = yv, rows
            m = {}
            for r in rows:
                k = C._kind(r["check_id"])
                m[k] = max(m.get(k, 0.0), r["abs_diff"])
            cls.kind_max[v["id"]] = m

    @classmethod
    def tearDownClass(cls):
        print()
        for sec in ("expected", "floor", "effects", "literal_info", "imp_fire_test"):
            if sec in DEV:
                print("(iii) %-13s largest deviation %.3e" % (sec, DEV[sec]))

    # ---- the comparison rule itself is seen to fire
    def test_rule_fires(self):
        self.assertTrue(within(0.5, 0.5 + 9e-10))
        self.assertFalse(within(0.5, 0.5 + 2e-9))
        self.assertTrue(within(4.7, 4.7 * (1 + 9e-10)))          # relative above 1
        self.assertFalse(within(4.7, 4.7 * (1 + 2e-9)))
        print("\n  [fire] comparison rule: 2e-9 abs / 2e-9 rel rejected, 9e-10 accepted")

    # ---- expected tables
    def test_expected_tables(self):
        """Every [expected.P*]: gains = gain_at, phases = phase_at (analytic hp_article), flat 0, resid = ramp_residual."""
        fails = []
        for name, e in self.spec["expected"].items():
            p = int(name[1:])
            f = R.hp_article(p)
            self.assertEqual(e["article"], "hp_article(%d)" % p)
            for t, g in zip(TS, e["gains"]):
                if not note("expected", g, R.gain_at(f, t)):
                    fails.append((name, "gain", t))
            for t in TS:
                if not note("expected", e["phases"][str(t)], R.phase_at(f, t)):
                    fails.append((name, "phase", t))
            if not note("expected", e["resid"], R.ramp_residual(f, self.cs["level"], self.cs["slope"])):
                fails.append((name, "resid"))
            self.assertEqual(e["flat"], 0.0)
        print("\n  expected tables: 4 x (5 gains + 5 phases + resid) = 44 values, fails %s" % fails)
        self.assertEqual(fails, [])

    def test_expected_table_guard_fires(self):
        """A table value off by 1e-6 is rejected."""
        f = R.hp_article(48)
        g = self.spec["expected"]["P48"]["gains"][2]
        self.assertFalse(within(g + 1e-6, R.gain_at(f, 20)))

    # ---- floor
    def _floor_measured(self):
        """Per real P: simulated corrected model, checker measurements vs the EXACT article (analytic gain_at /
        phase_at, simulate(article, seed zero) for start-up). resid and flat from the checker rows."""
        out = {}
        for p in PERIODS:
            f, a = R.hp_code(p, k=SQ), R.hp_article(p)
            yv = self.y["P%d" % p]
            g = max(abs(C.m_gain(self.cs, yv["s%d" % t], t) - R.gain_at(a, t)) for t in TS)
            ph = max(abs(C.wrap_phase(C.m_phase(self.cs, yv["s%d" % t], t) - R.phase_at(a, t))) for t in TS)
            st = max(C.m_startup(self.cs, yv[i], R.simulate(a, self.x[i], seed="zero")) for i in ("flat", "ramp"))
            out[p] = dict(gain=g, phase=ph, startup=st, resid=self.kind_max["P%d" % p]["resid"],
                          flat=self.kind_max["P%d" % p]["flat"])
        return out

    def test_floor(self):
        """[floor] = max over the 4 real P of the measured quantity; per-P text numbers at 4 significant digits."""
        fl = self.spec["floor"]
        m = self._floor_measured()
        fails = []
        for q in KINDS:
            want = max(m[p][q] for p in PERIODS)
            print("  floor %-8s spec %.10g  measured %.10g  dev %.3e" % (q, fl[q], want, dev(fl[q], want)))
            if not note("floor", fl[q], want):
                fails.append(q)
        src = fl["source"]
        for q in ("gain", "phase", "startup"):
            line = [seg for seg in src.replace("\n", " ").split(";") if re.search(r"\b%s " % q, seg)][0]
            text = floats(line)
            self.assertEqual(len(text), 4, line)
            for p, t in zip(PERIODS, text):
                a = m[p][q]
                DEV["floor"] = max(DEV.get("floor", 0.0), abs(a - t) if sig(a, 4) != t else 0.0)
                if sig(a, 4) != t:
                    fails.append((q, p, a, t))
        print("  per-P floor text (gain, phase, startup x 4 P) compared at 4 significant digits")
        self.assertEqual(fails, [])

    def test_floor_guard_fires(self):
        m = self._floor_measured()
        want = max(m[p]["gain"] for p in PERIODS)
        self.assertTrue(within(self.spec["floor"]["gain"], want))
        # the floors are ~4e-7, so the 1e-9 window is ~0.25 % of the value: a 5e-9 change is the smallest clear fire
        self.assertFalse(within(self.spec["floor"]["gain"] + 5e-9, want))

    # ---- variant effects
    def test_variant_effects(self):
        """Every control's [variants.effect] (5 kinds) = max over that kind's checks of |actual - table|, simulated
        with the control's own model and measured with the checker's check_rows (rounded tables, as the spec says)."""
        fails, n = [], 0
        for v in self.spec["variants"]:
            if v["role"] != "neg_control":
                continue
            m = self.kind_max[v["id"]]
            for q in KINDS:
                n += 1
                got = m.get(q, 0.0)
                if not note("effects", v["effect"][q], got):
                    fails.append((v["id"], q, v["effect"][q], got))
        print("\n  variant effects: 8 controls x 5 kinds = %d values, fails %s" % (n, fails))
        self.assertEqual(n, 40)
        self.assertEqual(fails, [])

    def test_variant_effect_guard_fires(self):
        """An effect altered by 1% (NCB gain) is rejected; so is a swapped control."""
        got = self.kind_max["NCB"]["gain"]
        eff = [v for v in self.spec["variants"] if v["id"] == "NCB"][0]["effect"]["gain"]
        self.assertTrue(within(eff, got))
        self.assertFalse(within(eff * 1.01, got))
        self.assertFalse(within(eff, self.kind_max["NCA"]["gain"]))

    # ---- literal_info
    def test_literal_info(self):
        """[literal_info]: hp_code(P) (float32 0.707, Zorro PI) vs hp_article(P), analytic, P = 20,30,48,125,
        sine periods 5..100; the phase is wrapped."""
        li = self.spec["literal_info"]
        g, ph = [], []
        for p in PERIODS:
            f, a = R.hp_code(p), R.hp_article(p)
            g.append(max(abs(R.gain_at(f, t) - R.gain_at(a, t)) for t in TS))
            ph.append(max(abs(C.wrap_phase(R.phase_at(f, t) - R.phase_at(a, t))) for t in TS))
        print("\n  literal_info gain_max %.10e (spec %.10e)  phase_max %.10e (spec %.10e)"
              % (max(g), li["gain_max"], max(ph), li["phase_max"]))
        self.assertTrue(note("literal_info", li["gain_max"], max(g)))
        self.assertTrue(note("literal_info", li["phase_max"], max(ph)))
        # the P = 48 numbers quoted in the same source text = NCH gain / phase effect (checker's own fit)
        t48 = floats(li["source"])
        eff = [v for v in self.spec["variants"] if v["id"] == "NCH"][0]["effect"]
        self.assertEqual(sig(self.kind_max["NCH"]["gain"], 4), t48[0])
        self.assertEqual(sig(self.kind_max["NCH"]["phase"], 4), t48[1])
        self.assertTrue(within(eff["gain"], self.kind_max["NCH"]["gain"]))

    def test_literal_info_guard_fires(self):
        """The corrected k (sqrt(2)/2) removes the literal difference: the same measurement gives ~1e-7, not 7.6e-5."""
        li = self.spec["literal_info"]
        g = max(abs(R.gain_at(R.hp_code(p, k=SQ), t) - R.gain_at(R.hp_article(p), t)) for p in PERIODS for t in TS)
        self.assertFalse(within(li["gain_max"], g))

    # ---- IMP fire test numbers
    def _sim(self, f, seed):
        return {i: R.simulate(f, self.x[i], seed=seed) for i in self.names}

    def _maxdiff(self, a, b, start=0):
        return max(float(np.max(np.abs(a[i][start:] - b[i][start:]))) for i in self.names)

    def test_imp_fire_test_effect(self):
        """[imp].fire_test_effect text numbers (4 significant digits): P48 vs float32-0.707 replay (overall and n >= 500),
        NCH vs corrected replay, control discrimination for the 8 controls, own-model replays exactly 0."""
        txt = self.spec["imp"]["fire_test_effect"].replace("\n", " ")
        p48 = self._sim(R.hp_code(48, k=SQ), "zero")
        f32 = self._sim(R.hp_code(48), "zero")
        m1 = re.search(r"float32-0\.707 replay ([\d.e+-]+) overall \(([\d.e+-]+) over n >= 500\)", txt)
        m2 = re.search(r"corrected-model replay \(price seed\) ([\d.e+-]+)", txt)
        self.assertIsNotNone(m1)
        self.assertIsNotNone(m2)
        got = {"P48 overall": (float(m1.group(1)), self._maxdiff(p48, f32)),
               "P48 n>=500": (float(m1.group(2)), self._maxdiff(p48, f32, 500)),
               "NCH vs corrected": (float(m2.group(1)),
                                    self._maxdiff(self._sim(R.hp_code(48), "price"),
                                                  self._sim(R.hp_code(48, k=SQ), "price")))}
        ctl = {"NCA": (R.hp_code(48, k=SQ, alpha_bump=1), "zero", 48), "NCB": (R.hp_code(48, k=SQ, in_bump=1), "zero", 48),
               "NCF": (R.hp_code(48, k=SQ, fb2_bump=1), "zero", 48), "NCZ": (R.hp_code(48, k=SQ, num="1st"), "zero", 48),
               "NCS": (R.hp_code(48, k=SQ), "price", 48), "NCH": (R.hp_code(48), "price", 48),
               "NC1": (R.hp_code(49, k=SQ), "zero", 48), "NC2": (R.hp_code(20, k=SQ, deg=True), "zero", 20)}
        seg = txt.split("each > 1e-9 = must_pass discriminates):")[1]
        for k, (f, seed, pe) in ctl.items():
            m = re.search(r"%s ([\d.e+-]+)" % k, seg)
            self.assertIsNotNone(m, k)
            y = self._sim(f, seed)
            got["control " + k] = (float(m.group(1)), self._maxdiff(y, self._sim(R.hp_code(pe, k=SQ), "zero")))
            self.assertEqual(self._maxdiff(y, self._sim(f, seed)), 0.0, "own-model replay of %s is not 0" % k)
            self.assertGreater(got["control " + k][1], 1e-9, "%s: must_pass would not discriminate" % k)
        fails = []
        for k, (stored, actual) in got.items():
            DEV["imp_fire_test"] = max(DEV.get("imp_fire_test", 0.0), abs(actual - stored))
            ok = sig(actual, 4) == stored
            print("  %-18s spec %-10g actual %.10g  |diff| %.3e %s" % (k, stored, actual, abs(actual - stored),
                                                                    "PASS" if ok else "FAIL"))
            if not ok:
                fails.append(k)
        self.assertEqual(len(got), 3 + 8)
        self.assertEqual(fails, [])

    def test_imp_fire_test_guard_fires(self):
        """The two must_fail replays are above 1e-9 (the fire test) and a model with the right k is not."""
        p48 = self._sim(R.hp_code(48, k=SQ), "zero")
        self.assertGreater(self._maxdiff(p48, self._sim(R.hp_code(48), "zero")), 1e-9)
        self.assertLessEqual(self._maxdiff(p48, self._sim(R.hp_code(48, k=SQ), "zero")), 1e-9)

    def test_registry_matches_spec_models(self):
        """Every [imp] model string resolves in reference.IMP_MODELS; the corrected-line model is hp_code(k = sqrt(2)/2)."""
        imp = self.spec["imp"]
        for tab in (imp["must_pass"], imp["must_fail"]):
            for vid, m in tab.items():
                self.assertIn(m, R.IMP_MODELS, m)
        self.assertEqual(R.IMP_MODELS["hp_code(48, PI_ZORRO, SQRT_HALF)"](), R.hp_code(48, k=SQ))
        self.assertEqual(R.IMP_MODELS["hp_code(48, PI_ZORRO, F32_0707)"](), R.hp_code(48))
        self.assertNotEqual(R.hp_code(48, k=SQ), R.hp_code(48))
        self.assertEqual(len(imp["must_pass"]), 12)
        self.assertEqual(len(imp["must_fail"]), 2)


if __name__ == "__main__":
    unittest.main()
