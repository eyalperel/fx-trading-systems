"""Tests for tools/compare_equivalence.py: can the S4 comparator fail? (decision 4, 2026-11-23)

A perfect fake Zorro log is built from the committed expected files (what a correct template would
write); each test plants one defect and the run verdict must change. The real expected directory
is used, so these tests also check that the expected files parse.
"""
import copy
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))
import compare_equivalence as C  # noqa: E402

EXP = os.path.join(ROOT, "analysis", "template", "equivalence", "expected")


def perfect_log(counts, exp, break_controls=True):
    """The log a correct template would write; controls broken (as the mutants should be)."""
    log = dict(half={}, info={}, cnt={}, open_last={}, errors=[], last_bar=99)
    for name, c in counts.items():
        log["info"][name] = dict(rows=c["bars"], **C.SETUP)
        log["cnt"][name] = (int(c["same_bar_conflicts"]), int(c["be_adverse_exits"]))
        halves = []
        for j, e in enumerate(exp[name]):
            g = dict(group=j // 2 + 1, half=e["half"], dir=e["dir"], kind=e["kind"], entry_day=e["entry_day"],
                     entry=e["entry"], exit_day=e["exit_day"], exit=e["exit"], reason=e["reason"], flags=0)
            doc = C.DOC_DIFF.get((name.split("_C")[0], e["half"]))
            if doc is not None:
                g["reason"], g["exit"] = doc
            halves.append(g)
        if break_controls and int(c["mutation"]) != 0:
            halves = halves[:-1]   # a mutant changes the trades
        log["half"][name] = halves
    return log


class Comparator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.counts, cls.exp = C.read_expected(EXP)

    def verdict(self, log):
        return C.evaluate(log, self.counts, self.exp)[1]

    def log(self, **kw):
        return perfect_log(self.counts, self.exp, **kw)

    def test_64_scenarios_4_controls(self):
        self.assertEqual(len(self.counts), 64)
        self.assertEqual(sum(1 for c in self.counts.values() if int(c["mutation"]) != 0), 4)

    def test_perfect_log_passes(self):
        rows, ok, ctl = C.evaluate(self.log(), self.counts, self.exp)
        self.assertTrue(ok)
        self.assertEqual(sum(1 for r in rows if r[2] == "DOC"), 4)
        self.assertTrue(all(v > 0 for v in ctl.values()))

    def test_controls_not_detected_fails_run(self):
        self.assertFalse(self.verdict(self.log(break_controls=False)))

    def test_exit_price_beyond_tolerance_fails(self):
        lg = self.log()
        lg["half"]["A2"][0]["exit"] += 2 * C.PRICE_TOL
        self.assertFalse(self.verdict(lg))

    def test_exit_price_within_tolerance_passes(self):
        lg = self.log()
        lg["half"]["A2"][0]["exit"] += C.PRICE_TOL / 2
        self.assertTrue(self.verdict(lg))

    def test_entry_price_fails(self):
        lg = self.log()
        lg["half"]["P1M"][1]["entry"] -= 2 * C.PRICE_TOL
        self.assertFalse(self.verdict(lg))

    def test_wrong_reason_fails(self):
        lg = self.log()
        lg["half"]["B1"][1]["reason"] = "be"
        self.assertFalse(self.verdict(lg))

    def test_wrong_day_fails(self):
        lg = self.log()
        lg["half"]["C1"][0]["exit_day"] = "2024-03-13"   # expected 2024-03-12
        self.assertFalse(self.verdict(lg))

    def test_wrong_kind_fails(self):
        lg = self.log()
        lg["half"]["E1"][2]["kind"] = "c1"
        self.assertFalse(self.verdict(lg))

    def test_missing_half_fails(self):
        lg = self.log()
        lg["half"]["R1"] = lg["half"]["R1"][:3]
        self.assertFalse(self.verdict(lg))

    def test_extra_trade_on_no_trade_scenario_fails(self):
        lg = self.log()
        lg["half"]["D7a"] = copy.deepcopy(lg["half"]["D7b"])
        self.assertFalse(self.verdict(lg))

    def test_end_trade_compared_on_entry_only(self):
        lg = self.log()
        h = [g for g in lg["half"]["P1"] if g["reason"] == "end"][0]
        h["exit"] += 0.01
        h["reason"] = "end"
        self.assertTrue(self.verdict(lg))
        h["entry"] += 0.01
        self.assertFalse(self.verdict(lg))

    def test_docdiff_engine_outcome_in_zorro_fails(self):
        lg = self.log()
        lg["half"]["A3HF"][0]["reason"], lg["half"]["A3HF"][0]["exit"] = "stop", 0.9850
        self.assertFalse(self.verdict(lg))

    def test_reason_other_fails(self):
        lg = self.log()
        lg["half"]["A1"][0]["reason"] = "other"
        self.assertFalse(self.verdict(lg))

    def test_counts_fail(self):
        for k in (0, 1):
            lg = self.log()
            c = list(lg["cnt"]["A3"])
            c[k] += 1
            lg["cnt"]["A3"] = tuple(c)
            self.assertFalse(self.verdict(lg), k)

    def test_setup_and_rows_fail(self):
        for key, val in (("Hedge", "0"), ("TICKS", "0"), ("Fill", "1"), ("rows", "3")):
            lg = self.log()
            lg["info"]["A2"][key] = val
            self.assertFalse(self.verdict(lg), key)

    def test_open_at_end_error_row_missing_info_fail(self):
        lg = self.log()
        lg["open_last"]["A2"] = 1
        self.assertFalse(self.verdict(lg))
        lg = self.log()
        lg["errors"].append("ERROR,SYN_A2,20240308,no sizing")
        self.assertFalse(self.verdict(lg))
        lg = self.log()
        del lg["info"]["A2"]
        self.assertFalse(self.verdict(lg))

    def test_read_log_parses_template_rows(self):
        import tempfile
        rows = ["kind,asset,a,b,c,d,e,f,g,h,i,j,k,l,m,n",
                "INFO,SYN_A2,0,rows=14,vol=0,btf=1,cont=1,mut=0,list=29,Fill=3,Hedge=2,TICKS=1,BarOffset=1020",
                "HALF,SYN_A2,1,1,1,c1,20240308,1.000000000000000,20240308,1.010000000000000,tp1,524290,8,8",
                "CNT,SYN_A2,9,0,0", "CNT,SYN_A2,10,0,0",
                "OPEN,SYN_A2,9,1,2,0,1.0,0.985", "OPEN,SYN_A2,10,1,2,0,1.0,1.0"]
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("\n".join(rows) + "\n")
        lg = C.read_log(f.name)
        os.unlink(f.name)
        self.assertEqual(lg["info"]["A2"]["Hedge"], "2")
        self.assertEqual(lg["half"]["A2"][0]["entry_day"], "2024-03-08")
        self.assertEqual(lg["half"]["A2"][0]["reason"], "tp1")
        self.assertEqual(lg["cnt"]["A2"], (0, 0))
        self.assertEqual(lg["open_last"], {"A2": 1})


if __name__ == "__main__":
    unittest.main()
