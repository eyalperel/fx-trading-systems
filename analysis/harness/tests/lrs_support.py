"""Shared helpers for the LRS tests (Laguerre RSI, specs/LRSI_ArticleFidelity.toml). NOT a test module.

The RFX helpers (rfx_support) are spec-agnostic: this module binds them to the LRSI spec. A perfect run = every variant's columns simulated
with ITS OWN [imp].must_pass model (reference.simulate_lrsi via checker.model_out; NCS / NCT: reference.simulate_lrsi_shared over all
superseded calls in the generator's variant-major order, skipped inputs omitted). No .c file is read, Zorro is not run.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rfx_support as _X     # noqa: E402

C, G, R = _X.C, _X.G, _X.R
HARNESS = _X.HARNESS
ROOT = os.path.normpath(os.path.join(HARNESS, "..", ".."))
SPEC_PATH = os.path.join(HARNESS, "specs", "LRSI_ArticleFidelity.toml")
REVIEW_MODEL = os.path.join(ROOT, "docs", "harness", "LAGUERRERSI_REVIEW_MODEL.py")
TS = (5, 10, 20, 40, 100)
REAL = {"G05": (1, 2), "G07": (7, 10), "G08": (4, 5)}
CONTROLS = ("NCG", "NC25", "NCP", "NCS")
INFO = ("NCH", "NCT")


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


def review_model():
    """The planning chat's independent model (docs/harness/LAGUERRERSI_REVIEW_MODEL.py), imported without running its __main__."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("lrsi_review_model", REVIEW_MODEL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
