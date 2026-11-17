"""[imp_corrections.<id>] (Amendment 2 mechanism for HP_ArticleFidelity; precedent: [effect_corrections], 49f7fda).

An amendment may supersede ONE pre-registered [imp] model string without editing [imp] (which stays as the record).
Fields, all required: list ("must_pass" | "must_fail"), replaces (the pre-registered model string, verbatim),
model (in reference.IMP_MODELS), amendment (non-empty string), source ((a)/(b)/(c) label).
Applied in generator.to_checker_spec; one INFO line per applied correction reaches the results-file header.

Every guard is SEEN TO FIRE (CLAUDE.md 4.4). Test data: the HP spec in memory plus an invented correction onto an
existing registry model (the real Amendment 2 model is added later); nothing is written to the repo.
Regression: a spec without the section gives the same checker output as before (committed results replayed from
their raw copies; the raw copies are gitignored, so those tests skip when a copy is absent).
Run with the rest of the suite: bash analysis/harness/run_tests.sh
"""
import copy
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HARNESS)

import checker as C      # noqa: E402
import generator as G    # noqa: E402
import reference as R    # noqa: E402

SPECS = os.path.join(HARNESS, "specs")
RESULTS = os.path.join(HARNESS, "results")
HP = os.path.join(SPECS, "HP_ArticleFidelity.toml")
OLD = "hp_code(48, PI_ZORRO, F32_0707)"           # the pre-registered NCH must_pass model
NEW = "hp_code(48, PI_ZORRO, SQRT_HALF)"          # an existing registry model, used as test data only


def good_correction():
    return dict(list="must_pass", replaces=OLD, model=NEW, amendment="2", source="(b) test data")


def spec_with(corr=None):
    s = copy.deepcopy(G.load_spec(HP))
    s["imp_corrections"] = {"NCH": corr if corr is not None else good_correction()}
    return s


def codes(s):
    return [c for c, _ in G.validate_spec(s)[0]]


class TestImpCorrectionsValidation(unittest.TestCase):
    def test_pre_registered_text_is_what_the_tests_assume(self):
        imp = G.load_spec(HP)["imp"]
        self.assertEqual(imp["must_pass"]["NCH"], OLD)
        self.assertIn(NEW, R.IMP_MODELS)

    def test_valid_correction_accepted_with_info_line(self):
        errs, infos = G.validate_spec(spec_with())
        self.assertEqual(errs, [])
        want = "INFO IMP correction applied: NCH must_pass: %s -> %s (Amendment 2)" % (OLD, NEW)
        self.assertIn(want, infos)
        self.assertEqual(len([i for i in infos if "IMP correction" in i]), 1)
        print("\n  %s" % want)

    def test_no_section_no_info_line(self):
        s = G.load_spec(HP)
        self.assertNotIn("imp_corrections", s)
        self.assertEqual([i for i in G.validate_spec(s)[1] if "IMP correction" in i], [])

    def test_refusals_each_fire(self):
        cases = []

        def mk(name, mut, code):
            cases.append((name, mut, code))

        def corr(**kw):
            c = good_correction()
            c.update(kw)
            return c

        mk("wrong id (not a variant)", lambda s: s["imp_corrections"].update({"NCX": corr()}), "IMP_CORRECTION_UNKNOWN_ID")
        mk("id not in the named list (P20 not in must_fail)",
           lambda s: s["imp_corrections"].update({"P20": corr(list="must_fail")}), "IMP_CORRECTION_UNKNOWN_ID")
        mk("wrong list (NCH correction names must_fail, replaces text of must_pass)",
           lambda s: s["imp_corrections"].update({"NCH": corr(list="must_fail")}), "IMP_CORRECTION_REPLACES_MISMATCH")
        mk("bad list value", lambda s: s["imp_corrections"].update({"NCH": corr(list="must_run")}), "IMP_CORRECTION_BAD")
        mk("replaces mismatch", lambda s: s["imp_corrections"].update(
            {"NCH": corr(replaces="hp_code(48, PI_ZORRO, SQRT_HALF)")}), "IMP_CORRECTION_REPLACES_MISMATCH")
        mk("replaces differs by one character", lambda s: s["imp_corrections"].update(
            {"NCH": corr(replaces=OLD + " ")}), "IMP_CORRECTION_REPLACES_MISMATCH")
        mk("unknown model", lambda s: s["imp_corrections"].update(
            {"NCH": corr(model="hp_code(48, NO_SUCH_MODEL)")}), "IMP_CORRECTION_UNKNOWN_MODEL")
        for f in ("list", "replaces", "model", "amendment", "source"):
            mk("missing field %s" % f, (lambda f: lambda s: s["imp_corrections"]["NCH"].pop(f))(f), "IMP_CORRECTION_BAD")
        mk("empty amendment", lambda s: s["imp_corrections"]["NCH"].update(amendment=" "), "IMP_CORRECTION_BAD")
        mk("amendment not a string", lambda s: s["imp_corrections"]["NCH"].update(amendment=2), "IMP_CORRECTION_BAD")
        mk("source without (a)/(b)/(c) label", lambda s: s["imp_corrections"]["NCH"].update(source="measured"),
           "IMP_CORRECTION_BAD")
        mk("unexpected key (typo)", lambda s: s["imp_corrections"]["NCH"].update(modle=NEW), "IMP_CORRECTION_BAD")
        mk("section is not a table of tables", lambda s: s.update(imp_corrections={"NCH": "x"}), "IMP_CORRECTION_BAD")
        mk("no [imp] section", lambda s: s.pop("imp"), "IMP_CORRECTION_BAD")
        for name, mut, code in cases:
            s = spec_with()
            mut(s)
            got = codes(s)
            print("  [fire] %-62s -> %s" % (name, [c for c in got if c.startswith("IMP_CORRECTION")] or got))
            self.assertIn(code, got, "%s: %s" % (name, got))
            with self.assertRaises(G.SpecError, msg=name):
                G.to_checker_spec(s)

    def test_one_failure_does_not_hide_valid_part(self):
        """A bad correction is refused; the same spec with the bad key removed is accepted (the guard is specific)."""
        s = spec_with(dict(good_correction(), model="nope"))
        self.assertTrue(codes(s))
        del s["imp_corrections"]
        self.assertEqual(codes(s), [])


class TestImpCorrectionsApplied(unittest.TestCase):
    def test_to_checker_spec_applies_only_the_named_entry(self):
        base = G.to_checker_spec(G.load_spec(HP))["imp"]
        s = spec_with()
        raw_before = copy.deepcopy(s["imp"])
        d = G.to_checker_spec(s)["imp"]
        self.assertEqual(d["must_pass"]["NCH"], NEW)
        self.assertEqual({k: v for k, v in d["must_pass"].items() if k != "NCH"},
                         {k: v for k, v in base["must_pass"].items() if k != "NCH"})
        self.assertEqual(d["must_fail"], base["must_fail"])            # NCH must_fail untouched
        self.assertEqual(d["tol"], base["tol"])
        self.assertEqual(base["must_pass"]["NCH"], OLD)
        self.assertEqual(s["imp"], raw_before, "the spec's own [imp] (the record) must not be mutated")

    def test_must_fail_list_correction(self):
        s = spec_with(dict(list="must_fail", replaces="hp_code(48, PI_ZORRO, SQRT_HALF)",
                           model="hp_code(48, PI_ZORRO, F32_0707)", amendment="2", source="(b) test data"))
        self.assertEqual(codes(s), [])
        d = G.to_checker_spec(s)["imp"]
        self.assertEqual(d["must_fail"]["NCH"], "hp_code(48, PI_ZORRO, F32_0707)")
        self.assertEqual(d["must_pass"]["NCH"], OLD)

    def test_info_line_reaches_checker_dict(self):
        d = G.to_checker_spec(spec_with())
        self.assertIn("INFO IMP correction applied: NCH must_pass: %s -> %s (Amendment 2)" % (OLD, NEW),
                      d["info_lines"])

    def test_header_line_and_row_in_results_file(self):
        raw = os.path.join(RESULTS, "HP_ArticleFidelity_20261117_raw_run1.csv")
        if not os.path.isfile(raw):
            self.skipTest("HP run 1 raw copy absent (gitignored): %s" % raw)
        cs = G.to_checker_spec(spec_with())
        with tempfile.TemporaryDirectory() as d:
            res = C.run_check(cs, raw, d, "20261117")
            txt = open(res["path"], encoding="utf-8").read()
        line = "# INFO IMP correction applied: NCH must_pass: %s -> %s (Amendment 2)" % (OLD, NEW)
        self.assertIn(line, txt)
        row = [ln for ln in txt.splitlines() if ln.startswith("HPF-NCH-imp-pass,")][0]
        self.assertIn(NEW, row)                       # the replay really used the corrected model
        self.assertNotIn(OLD, row)
        print("\n  header line present; NCH imp-pass row names the corrected model PASS")


# ----------------------------------------------------------------------------- no-regression replays
def _mask(text):
    """CR removed; the two lines that name the machine-local raw path / an older batch name are masked."""
    out = []
    for ln in text.replace("\r", "").split("\n"):
        ln = re.sub(r"^# raw_file=\S+ ", "# raw_file=<masked> ", ln)
        ln = re.sub(r"^# batch=\S+ ", "# batch=<masked> ", ln)
        out.append(ln)
    return "\n".join(out)


REPLAYS = (("H1_SuperSmoother2Pole", "GEN_H1_SuperSmoother2Pole_20261107", "20261107"),
           ("SS2_ArticleFidelity", "SS2_ArticleFidelity_20261112", "20261112"),
           ("SS3_ArticleFidelity", "SS3_ArticleFidelity_20261116", "20261116"),
           ("HP_ArticleFidelity", "HP_ArticleFidelity_20261117", "20261117"))


class TestNoRegression(unittest.TestCase):
    """The committed results files, replayed from their raw copies with the current checker (a spec without
    [imp_corrections]), are identical to the committed files (masked lines: raw_file path, batch name)."""

    def _replay(self, spec_name, res_name, date):
        raw = os.path.join(RESULTS, res_name + "_raw_run1.csv")
        committed = os.path.join(RESULTS, res_name + ".csv")
        if not (os.path.isfile(raw) and os.path.isfile(committed)):
            self.skipTest("raw copy or committed results absent (gitignored raw): %s" % raw)
        tspec = G.load_spec(os.path.join(SPECS, spec_name + ".toml"))
        self.assertNotIn("imp_corrections", tspec)
        with tempfile.TemporaryDirectory() as d:
            res = C.run_check(G.to_checker_spec(tspec), raw, d, date)
            new = open(res["path"], encoding="utf-8", newline="").read()
        old = open(committed, encoding="utf-8", newline="").read()
        self.assertEqual(_mask(new), _mask(old))
        print("\n  %s replay == committed results (%d lines, raw_file/batch lines masked) PASS"
              % (res_name, len(old.splitlines())))

    def test_h1(self):
        self._replay(*REPLAYS[0])

    def test_ss2f(self):
        self._replay(*REPLAYS[1])

    def test_ss3f(self):
        self._replay(*REPLAYS[2])

    def test_hp_run1(self):
        self._replay(*REPLAYS[3])

    def test_replay_guard_fires(self):
        """The comparison can fail: one extra INFO line in the replayed text is not masked away."""
        old = "a\n# raw_file=/x/y.csv sha256=1\n# batch=Z variants_run=6\n"
        new = old + "# INFO IMP correction applied: NCH\n"
        self.assertNotEqual(_mask(new), _mask(old))
        self.assertEqual(_mask(old.replace("/x/y.csv", "/other.csv").replace("Z", "Q")), _mask(old))


if __name__ == "__main__":
    unittest.main()
