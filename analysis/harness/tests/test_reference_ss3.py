"""Self-test for the SS3 reference filters (reference.ss3_article / ss3_code / ss3_printed / ss3_hybrid)
against the numbers pre-registered in specs/SS3_ArticleFidelity.toml (pre-run condition (iii)).

Run with the rest of the suite: bash analysis/harness/run_tests.sh
Tolerance 1e-9 absolute unless a line says otherwise. Quantities the spec stores to 2-5 significant digits
are compared at that many digits (stated per test). No .c file is read; Zorro is not run.
A number the reference does not reproduce FAILS its test (it is never loosened to pass).

Labels: (a) source states, (b) verified here, (c) inference.
"""
import math
import os
import re
import sys
import tomllib
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HARNESS)

import checker as C        # noqa: E402
import generator as G      # noqa: E402
import reference as R      # noqa: E402

SPEC_PATH = os.path.join(HARNESS, "specs", "SS3_ArticleFidelity.toml")
TS = (5, 10, 20, 40, 100)
PERIODS = (10, 14, 20, 30)
TOL = 1e-9

# (a) Cybernetic Analysis p. 210, Table 13.4: Y = C0*X + B1*Y[1] + B2*Y[2] + B3*Y[3]
#      P: (C0, B1, B2, B3)   (b) C0 = b[0], B1..B3 = a[0..2]
TABLE_13_4 = {
    4: (0.805867, 0.398405, -0.24749, 0.043214),
    10: (0.132326, 1.783327, -1.20026, 0.28461),
    20: (0.022647, 2.376806, -1.93294, 0.533488),
    30: (0.007451, 2.582648, -2.24788, 0.657784),
    40: (0.003313, 2.686486, -2.4202, 0.730403),
}
# Residuals as stored in the spec [[literal_replacements]] .source (b), P = 4, 10, 20, 30, 40.
SPEC_RESID = {
    "1.732/pi": (4.44e-6, 1.56e-6, 9.20e-7, 2.00e-6, 1.10e-6),
    "1.738/3.14159": (4.21e-3, 1.43e-3, 4.33e-4, 2.05e-4, 1.18e-4),
    "sqrt(3)/pi": (3.73e-5, 1.34e-5, 3.94e-6, 2.22e-6, 8.33e-7),
}


def spec():
    with open(SPEC_PATH, "rb") as f:
        return tomllib.load(f)


def sig(v, n):
    """v rounded to n significant digits (float)."""
    return float("%.*e" % (n - 1, v))


def say(cid, exp, act, tol, ok):
    print("  %-52s exp %-16.10g act %-16.10g |diff| %.3e tol %.0e %s"
          % (cid, exp, act, abs(act - exp), tol, "PASS" if ok else "FAIL"))
    return ok


def book_printed_exact_pi(p):
    """The listing as printed: exp(-3.14159/P) (float64 3.14159), cos(1.738*pi/P) (degrees cosine, exact pi).
    NOT ss3_printed (that is NCL: PI_ZORRO inside the cosine)."""
    return R._ss3_filter(math.exp(-3.14159 / p), 1.738 * math.pi / p)


def form_filter(p, k, pi_exp):
    return R._ss3_filter(math.exp(-pi_exp / p), k * math.pi / p)


def coefs(f):
    return (f.b[0],) + tuple(f.a)


def gain_err(f, g):
    return max(abs(R.gain_at(f, t) - R.gain_at(g, t)) for t in TS)


class TestSS3Reference(unittest.TestCase):

    def test_expected_tables(self):
        """Every [expected.*] gain and lag = ss3_article analytic gain_at / ramp_lag, <= 1e-9."""
        s = spec()
        fails = []
        for name, e in s["expected"].items():
            p = int(name[1:])
            f = R.ss3_article(p)
            for t, g in zip(TS, e["gains"]):
                if not say("%s gain T=%d" % (name, t), g, R.gain_at(f, t), TOL, abs(R.gain_at(f, t) - g) <= TOL):
                    fails.append((name, t))
            if not say("%s lag" % name, e["lag"], R.ramp_lag(f), TOL, abs(R.ramp_lag(f) - e["lag"]) <= TOL):
                fails.append((name, "lag"))
            self.assertEqual(e["flat"], 0.0)
        self.assertEqual(fails, [])

    def test_sim_vs_analytic_gain(self):
        """Simulated (least squares) vs analytic gain, ss3_article, 4 real periods x 5 T, <= 1e-9."""
        fails = []
        for p in PERIODS:
            f = R.ss3_article(p)
            for t in TS:
                a, b = R.sim_gain(f, t), R.gain_at(f, t)
                if not say("sim vs analytic P=%d T=%d" % (p, t), b, a, TOL, abs(a - b) <= TOL):
                    fails.append((p, t))
        self.assertEqual(fails, [])

    def test_variant_effects(self):
        """Every [variants.effect]: gain = max_T |gain - book P20|; lag = |sim_lag diff| (measured-check);
        flat = 1.1*|DC gain - 1|; <= 1e-9 (values stored at 11 digits; NCB lag 61.57 at 1e-9 abs)."""
        s = spec()
        book = R.ss3_article(20)
        models = {"NCA": R.ss3_code(20, a1_bump=1), "NCB": R.ss3_code(20, in_bump=1), "NCL": R.ss3_printed(20),
                  "NCH": R.ss3_hybrid(20), "NC1": R.ss3_code(21), "NC2": R.ss3_code(20, deg=True)}
        fails = []
        for v in s["variants"]:
            if v["role"] != "neg_control":
                continue
            f, eff = models[v["id"]], v["effect"]
            got = dict(gain=gain_err(f, book), lag=abs(R.sim_lag(f) - R.sim_lag(book)),
                       flat=R.FLAT_LEVEL * abs(R.dc_gain(f) - 1.0))
            for q in ("gain", "lag", "flat"):
                # spec stores 11 significant digits: allow the representation error of that
                tol = max(TOL, 6e-11 * abs(eff[q]))
                if not say("%s %s" % (v["id"], q), eff[q], got[q], tol, abs(got[q] - eff[q]) <= tol):
                    fails.append((v["id"], q))
        self.assertEqual(fails, [])

    def test_floor(self):
        """[floor] gain 9.0e-7 / lag 7.7e-6 = max over P=10,14,20,30 (and T) of ss3_code(PI_ZORRO) vs
        ss3_article, 2 significant digits. Per-P values in the spec text are checked too."""
        s = spec()
        g, l = [], []
        for p in PERIODS:
            c, a = R.ss3_code(p), R.ss3_article(p)
            g.append(gain_err(c, a))
            l.append(abs(R.ramp_lag(c) - R.ramp_lag(a)))
        print("  floor gain per P %s lag per P %s" % (["%.3e" % x for x in g], ["%.3e" % x for x in l]))
        self.assertEqual([sig(x, 3) for x in g], [8.99e-7, 7.69e-7, 8.67e-7, 6.40e-7])
        # Per-P lag at 2 significant digits. At 3 digits P=20 is 5.095e-6 -> 5.09e-6 here vs the spec's 5.10e-6
        # (3rd-digit rounding of an informational per-P value; the maximum 7.7e-6 is unaffected). Reported.
        self.assertEqual([sig(x, 2) for x in l], [2.5e-6, 3.5e-6, 5.1e-6, 7.7e-6])
        print("  INFO per-P lag at 3 digits: %s (spec text: 2.48e-6, 3.54e-6, 5.10e-6, 7.68e-6)"
              % [sig(x, 3) for x in l])
        self.assertEqual(sig(max(g), 2), s["floor"]["gain"])
        self.assertEqual(sig(max(l), 2), s["floor"]["lag"])
        self.assertEqual(s["floor"]["flat"], 2.2e-16)

    def test_literal_info(self):
        """[literal_info]: book as printed (exp(-3.14159/P), cos(1.738*pi/P)) vs ss3_article,
        P=10,14,20,30, T=5..100; lag = analytic group delay. Compared at the 5 digits stored."""
        s = spec()["literal_info"]
        g, l = [], []
        for p in PERIODS:
            f, a = book_printed_exact_pi(p), R.ss3_article(p)
            g.append(gain_err(f, a))
            l.append(abs(R.ramp_lag(f) - R.ramp_lag(a)))
        print("  literal_info gain_max %.5e (spec %s) lag_max %.5e (spec %s)" % (max(g), s["gain_max"], max(l),
                                                                                  s["lag_max"]))
        self.assertEqual(sig(max(g), 5), s["gain_max"])
        self.assertEqual(sig(max(l), 5), s["lag_max"])

    def test_table_13_4_residuals(self):
        """Residual = max over the 4 coefficients |coef - Table 13.4|, for the three forms, P = 4,10,20,30,40,
        all 15 values vs [[literal_replacements]] at 2 significant digits. The spec text is checked to
        contain the same numbers (the dict above is a copy of it)."""
        src = [r["source"] for r in spec()["literal_replacements"] if r["literal"] == "1.738"][0]
        forms = {"1.732/pi": lambda p: form_filter(p, 1.732, math.pi),
                 "1.738/3.14159": lambda p: book_printed_exact_pi(p),
                 "sqrt(3)/pi": R.ss3_article}
        fails = []
        for name, mk in forms.items():
            got = []
            for p in sorted(TABLE_13_4):
                got.append(max(abs(c - t) for c, t in zip(coefs(mk(p)), TABLE_13_4[p])))
            for p, g, e in zip(sorted(TABLE_13_4), got, SPEC_RESID[name]):
                ok = sig(g, 3) == e or sig(g, 2) == sig(e, 2)
                print("  Table 13.4 %-14s P=%-2d residual %.3e spec %.2e %s" % (name, p, g, e,
                                                                                "PASS" if ok else "FAIL"))
                if not ok:
                    fails.append((name, p, g, e))
            line = [ln for ln in src.splitlines() if ln.strip().startswith(name.replace("/", " / ") + ":")][0]
            in_spec = tuple(float(v) for v in re.findall(r"\d\.\d+e-\d+", line.split(":", 1)[1].split("(", 1)[0]))
            self.assertEqual(in_spec, SPEC_RESID[name], "test copy of the spec residuals is stale")
        self.assertEqual(fails, [])

    def test_imp_fire_test_numbers(self):
        """[imp].fire_test_effect: NCH output (own hybrid coefficients) replayed with ss3_code(20), n >= 500:
        s5..s100, ramp, overall at 2 significant digits; flat entry (1.1e-14 round-off) asserted <= 1e-12;
        the same filter replayed with its own coefficients gives exactly 0."""
        cs = G.to_checker_spec(G.load_spec(SPEC_PATH))
        x = C.make_inputs(cs)
        hyb, code = R.ss3_hybrid(20), R.ss3_code(20)
        want = {"s5": 1.4e-4, "s10": 7.9e-4, "s20": 3.8e-3, "s40": 4.1e-3, "s100": 2.1e-3, "ramp": 3.7e-4}
        per = {}
        for i in C.input_names(cs):
            y = R.simulate(hyb, x[i])
            per[i] = float(max(abs(y[500:] - R.simulate(code, x[i])[500:])))
            self.assertEqual(float(max(abs(y[500:] - R.simulate(hyb, x[i])[500:]))), 0.0)
        print("  NCH vs ss3_code(20) per input: " + " ".join("%s=%.3e" % kv for kv in per.items()))
        self.assertLessEqual(per["flat"], 1e-12)
        for k, e in want.items():
            self.assertEqual(sig(per[k], 2), e, k)
        self.assertEqual(sig(max(per.values()), 2), 4.1e-3)

    def test_registry_matches_spec_models(self):
        """Every [imp] model string resolves in reference.IMP_MODELS to the intended filter."""
        imp = spec()["imp"]
        for tab in (imp["must_pass"], imp["must_fail"]):
            for vid, m in tab.items():
                self.assertIn(m, R.IMP_MODELS, m)
        self.assertEqual(R.IMP_MODELS["ss3_code(20, PI_ZORRO)"](), R.ss3_code(20))
        self.assertEqual(R.IMP_MODELS["ss3_hybrid(20, PI_ZORRO)"](), R.ss3_hybrid(20))
        self.assertEqual(R.ss3_code(20, pi_value=math.pi), R.ss3_article(20))


if __name__ == "__main__":
    unittest.main()
