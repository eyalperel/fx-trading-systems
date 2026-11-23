# Asset lists used by the NNFX template

| File | Provenance | sha256 |
|---|---|---|
| `AssetsNNFX_FX.csv` | Byte copy of `C:/Zorro/History/AssetsForex.csv` from the Zorro 3.11 install (file dated 2025-07-28), copied 2026-11-22 | `35ed8044e4b9b17b1c1d7b53cb1408fa5948c2cb8051cd7aa456e192500ab8e5` |

Decision M-D4 (`docs/template/NNFX_TEMPLATE_DECISIONS.md`): the template loads this file
explicitly with `assetList()`; Zorro's default `AssetsFix.csv` is never relied on.
Spread, commission and rollover come from here (Zorro 3.11 manual, spread.htm) and are
written into every results header (T7.1). Do not edit values in place: a changed cost
set is a new file with its own row here and is a counted variant (T11).

- (b) 28 FX pairs + USD/MXN; EUR/USD spread 0.00012 (1.2 pip), commission 0.
- (c) Account currency EUR, inferred from PIPCost (EUR/USD 0.08561 = 0.1 USD / 1.16815).
- (b) Rollover values are a single snapshot, not historical swaps (T7.3).
