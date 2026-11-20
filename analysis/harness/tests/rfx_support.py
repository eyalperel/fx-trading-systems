"""Shared helpers for the RFX tests (Reflex, specs/RFX_ArticleFidelity.toml). NOT a test module.

Builds, from the spec itself, the checker dict, the exact inputs and the OWN-MODEL outputs of every variant (what a
perfect Zorro run would export, floating-point noise aside), plus a synthetic Raw object / raw CSV text. The slot order of
the shared-state (superseded) replay is derived here from the variant order of the spec, independently of the checker's
own grouping helper. No .c file is read, Zorro is not run.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import os
import sys

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

SPEC_PATH = os.path.join(HARNESS, "specs", "RFX_ArticleFidelity.toml")
_cache = {}


def load(path=SPEC_PATH):
    """-> (spec dict as in the TOML, checker spec dict, inputs {id: array}), cached per path."""
    if path not in _cache:
        sp = G.load_spec(path)
        cs = G.to_checker_spec(sp)
        _cache[path] = dict(spec=sp, cs=cs, x=C.make_inputs(cs), outs={})
    c = _cache[path]
    return c["spec"], c["cs"], c["x"]


def own_model_outputs(path=SPEC_PATH):
    """{variant id: {output: {input: array}}}: every variant simulated with ITS OWN [imp].must_pass model."""
    spec, cs, x = load(path)
    c = _cache[path]
    if c["outs"]:
        return c["outs"]
    models = {v["id"]: R.IMP_MODELS[spec["imp"]["must_pass"][v["id"]]]() for v in cs["variants"]}
    shared = {}
    shared_types = (R.SharedModel, R.LrsiShared, R.FisherShared)   # Reflex shared MS (RFX); Laguerre RSI lr_init / lr_prevRSI (LRS);
    #                                                                Fisher ft_Value1 / ft_Fish (FSH)
    sim_of = {"SharedModel": R.simulate_shared, "LrsiShared": R.simulate_lrsi_shared, "FisherShared": R.simulate_fisher_shared}
    for v in cs["variants"]:                         # slot order = the generator's call order (variant-major, skipped inputs omitted)
        m = models[v["id"]]
        if isinstance(m, shared_types):
            for i in C.variant_inputs(cs, v):
                shared.setdefault((type(m).__name__, m[0]), []).append((v["id"], i, m[0][m.index]))
    sims = {}
    for (kind, _), slots in shared.items():
        sim = sim_of[kind]
        outs = sim([s[2] for s in slots], [x[s[1]] for s in slots])
        for s, o in zip(slots, outs):
            sims[(s[0], s[1])] = o
    out = {}
    for v in cs["variants"]:
        m = models[v["id"]]
        ov = {}
        for o, i, _ in C.variant_columns(cs, v):
            mo = sims[(v["id"], i)] if isinstance(m, shared_types) else C.model_out(m, x[i])
            ov.setdefault(o, {})[i] = getattr(mo, o)
        out[v["id"]] = ov
    c["outs"] = out
    return out


def synth_raw(path=SPEC_PATH, outs=None):
    """A checker.Raw whose columns are the own-model outputs (a perfect run). `outs` replaces own_model_outputs()."""
    spec, cs, x = load(path)
    outs = outs if outs is not None else own_model_outputs(path)
    raw = C.Raw()
    raw.header = C.header_of(cs)
    n = cs["n_bars"]
    raw.nrows = n
    raw.cols = {"n": np.arange(n, dtype=float), "clock_close": np.full(n, 1.1)}
    for i in C.input_names(cs):
        raw.cols["x_" + i] = np.array(x[i])
    for v in cs["variants"]:
        for o, i, col in C.variant_columns(cs, v):
            raw.cols[col] = np.array(outs[v["id"]][o][i])
    return raw


def raw_csv_text(path=SPEC_PATH, outs=None):
    """The synthetic raw file as CSV text (full precision, as the checker's load_raw reads it)."""
    raw = synth_raw(path, outs)
    lines = [",".join(raw.header)]
    cols = [raw.cols[h] for h in raw.header]
    for r in range(raw.nrows):
        lines.append(",".join(repr(float(c[r])) if h != "n" else str(int(c[r])) for h, c in zip(raw.header, cols)))
    return "\n".join(lines) + "\n"


def evaluated(path=SPEC_PATH):
    """(rows, nc) of checker.evaluate on the synthetic own-model raw file, cached."""
    c = _cache[path] if path in _cache else (load(path) and _cache[path])
    if "eval" not in c:
        spec, cs, x = load(path)
        c["eval"] = C.evaluate(cs, synth_raw(path))
    return c["eval"]


def kind_max(vid, path=SPEC_PATH):
    """{kind: max abs_diff over that variant's check rows (an info variant's rows are INFO; the info-* rows and SKIP rows are not included)} (the effect of a control)."""
    rows, _ = evaluated(path)
    out = {}
    for r in rows:
        if r["role"] in ("imp", "floor") or r["result"] == "SKIP":
            continue
        parts = r["check_id"].split("-", 2)
        if parts[1] != vid:
            continue
        k = C._kind(r["check_id"])
        if k == "info":                      # the INFO rows of the normalised output (flat / ramp / start-up), not a check kind
            continue
        out[k] = max(out.get(k, 0.0), r["abs_diff"])
    return out
