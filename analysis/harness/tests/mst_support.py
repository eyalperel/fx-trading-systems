"""Shared helpers for the MST tests (MESAStochastic, specs/MESA_ArticleFidelity.toml). NOT a test module.

The RFX helpers (rfx_support) are spec-agnostic (every function takes the spec path): this module binds them to the MST spec.
A perfect run = every variant's columns simulated with ITS OWN [imp].must_pass model (reference.simulate_mesa via checker.model_out).
No .c file is read, Zorro is not run. Labels: (a) source states, (b) verified here, (c) inference.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rfx_support as _X     # noqa: E402

C, G, R = _X.C, _X.G, _X.R
HARNESS = _X.HARNESS
ROOT = os.path.normpath(os.path.join(HARNESS, "..", ".."))
SPEC_PATH = os.path.join(HARNESS, "specs", "MESA_ArticleFidelity.toml")
TS = (5, 10, 20, 40, 100)
REAL = {"L14": (14, 48, 10), "L20": (20, 48, 10), "L30": (30, 48, 10), "S20": (20, 48, 20)}
CONTROLS = ("NCW", "NCA", "NCP", "NC1", "NCS")
INFO = ("NCL", "NCZ")


def load():
    return _X.load(SPEC_PATH)


def own_model_outputs():
    return _X.own_model_outputs(SPEC_PATH)


def synth_raw(outs=None):
    return _X.synth_raw(SPEC_PATH, outs)


def raw_csv_text(outs=None):
    return _X.raw_csv_text(SPEC_PATH, outs)


def evaluated():
    return _X.evaluated(SPEC_PATH)


def kind_max(vid):
    return _X.kind_max(vid, SPEC_PATH)
