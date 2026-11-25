"""V3 (NULL1): C1-only engine mode (Params.baseline_mode = "off"). Hand-calculated expectations, conventions of
test_reference_engine.py (ATR 0.0100; entry at bar 2's open 1.0000; stop 0.9850, TP1 1.0100)."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_reference_engine import scen, run, PRE, SIG  # noqa: E402

FLAT = (1.0000, 1.0010, 0.9990, 1.0000)


class C1Only(unittest.TestCase):
    def test_entry_far_from_baseline(self):
        # baseline 0.9000: close 1.0000 is 10 x ATR away. Full mode refuses (distance rule); C1-only enters at bar 2.
        rows = [FLAT] * 3
        far = [0.9000] * 5
        self.assertEqual(run(scen(rows, baseline=far)).halves, [])
        r = run(scen(rows, baseline=far, baseline_mode="off"))
        self.assertEqual([(h.entry_bar, h.entry, h.kind) for h in r.halves], [(2, 1.0, "c1"), (2, 1.0, "c1")])

    def test_wrong_side_and_c2_against(self):
        # baseline above price (state -1) and C2 = -1: full mode refuses a long; C1-only enters.
        rows = [FLAT] * 3
        above = [1.0500] * 5
        self.assertEqual(run(scen(rows, baseline=above, c2=[-1] * 5)).halves, [])
        self.assertEqual(len(run(scen(rows, baseline=above, c2=[-1] * 5, baseline_mode="off")).halves), 2)

    def test_no_baseline_exit(self):
        # after entry, bar 3 closes below the baseline 0.9995: full mode exits both at bar 4's open (0.9990); C1-only holds.
        rows = [FLAT, (1.0000, 1.0005, 0.9985, 0.9990), (0.9990, 0.9995, 0.9985, 0.9990), FLAT]
        bl = [0.9995] * 6
        full = run(scen(rows, baseline=bl))
        self.assertEqual({(h.exit_bar, h.reason) for h in full.halves}, {(4, "baseline")})
        off = run(scen(rows, baseline=bl, baseline_mode="off"))
        self.assertEqual({h.reason for h in off.halves}, {"end"})

    def test_c1_flip_exit_and_reverse(self):
        # C1 flips to -1 at bar 3: exit both at bar 4's open (1.0000) and enter short there (a new C1 signal).
        rows = [FLAT, FLAT, FLAT, FLAT]
        c1 = [-1, 1, 1, -1, -1, -1]
        r = run(scen(rows, c1=c1, baseline_mode="off"))
        self.assertEqual([(h.dir, h.entry_bar, h.reason, h.exit_bar) for h in r.halves[:2]],
                         [(1, 2, "c1_flip", 4), (1, 2, "c1_flip", 4)])
        self.assertEqual([(h.dir, h.entry_bar) for h in r.halves[2:]], [(-1, 4), (-1, 4)])

    def test_management_unchanged_where_baseline_never_binds(self):
        # TP1 at bar 3 (high 1.0105), runner to breakeven, trail after a close >= 1.0200, stopped by the trail.
        rows = [FLAT, (1.0000, 1.0105, 0.9995, 1.0050), (1.0050, 1.0210, 1.0040, 1.0200),
                (1.0200, 1.0300, 1.0190, 1.0290), (1.0290, 1.0295, 1.0130, 1.0150)]
        full = run(scen(rows))
        off = run(scen(rows, baseline_mode="off"))
        key = lambda r: [(h.half, h.reason, h.exit_bar, round(h.exit_price, 10)) for h in r.halves]
        self.assertEqual(key(full), key(off))
        self.assertEqual(key(off)[0][:2], (1, "tp1"))
        self.assertEqual(key(off)[1][:2], (2, "trail"))


if __name__ == "__main__":
    unittest.main()
