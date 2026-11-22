# NNFX reference engine (Phase 1 step 4, stage S2)

`reference_engine.py` is an independent Python implementation of the template rules
(`docs/template/NNFX_TEMPLATE_DECISIONS.md`, T1-T11 and M-D1..M-D4). In stage S4 the Zorro
template's trade list must match it on the same inputs. It works in price, pips and R;
swap and integer-lot sizing are outside it (probes P5, P6 in
`docs/template/ZORRO_TRADE_MECHANICS.md`).

Tests: `python -m unittest discover -s analysis/template/tests` (30 tests: scenarios A1-F2
reviewed 2026-11-22, signal definition, config agreement with `NNFX_Config.h`).
Expected values in the tests are hand-calculated; they define the rules, not the engine.
Until the S4 criteria are committed they may be corrected freely; after that only by a
dated amendment.

## Mutation check (2026-11-22): can the tests fail?

Each mutant is one planted bug in a copy of the engine; the suite (config-agreement test
excluded, since the copy has no config path) must fail.

| # | Planted bug | Result |
|---|---|---|
| M0 | none (control) | OK (as required) |
| M1 | TP1 checked before the stop | caught (1 failure) |
| M2 | gap past the stop fills at the stop, not the open | caught (2) |
| M3 | breakeven placed even when the close is beyond entry (M-D3) | caught (1) |
| M4 | trail recomputed on every close, not only on a new best | survived: **equivalent** (the stop only tightens, so the result is the same) |
| M5 | continuation not waiving volume / distance | caught (2) |
| M6 | C1 moving to 0 exits the trade | caught (1) |
| M7 | bridge-too-far uses > 7 instead of >= 7 | caught (1) |
| M8 | pullback window not closed after a failed candle | survived: **equivalent** (the k > wait rule closes it); redundant line removed |
| M9 | spread not charged | caught (1) |

7 of 7 non-equivalent mutants caught.
