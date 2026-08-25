# Week 9 Validation Is Not Reproducible From The Repo

**Date:** 2026-08-13, Week 13 Day 3
**Status:** Open. For Week 14 consolidation.

## What was checked

Whether the Week 9 validation of FRAMA, Laguerre and DSMA read the corrupted BTC
CSV — the file that was 7,534 genuine BTC rows followed by 7,529 appended EUR/USD
rows (see `Data_Integrity_Correction_2026-08-12.md`).

## What was found instead

**No tracked file in the repo reads `FRAMA_Laguerre_DSMA_*.csv.`** No notebook, no
script, no document. Searched across `.py`, `.ipynb` and `.md`.

**Week 9 has no notebook.** Weeks 8, 10 and 11 each have one:

    Week8_CyberCycle_Validation.ipynb
    Week10_Fisher_IFT_COG_Analysis.ipynb
    Week11_MESAStochastic_Analysis.ipynb
    Week11_Reflex_Analysis.ipynb
    Week11_ELI_Analysis.ipynb

`Test_FRAMA_Laguerre_DSMA.c` exists and writes the CSV. Nothing consumes it.

## What this does and does not establish

**Does not establish that validation never happened.** It may have been done in an
untracked notebook or an unsaved session. That cannot be distinguished from here.

**Does establish:** the Week 9 validation of FRAMA, Laguerre and DSMA is not
reproducible from the repository. Three indicators are recorded as VALIDATED with no
artifact showing how.

This matters for the portfolio more than for any single result. The README's standard
is that claims trace to commits.

## Effect on P3

None. P3 cites "FRAMA (Week 9, validated)" as justification for using FRAMA as its
conditional split variable, but the actual requirement is structural — FRAMA must
share no term with the band width — and that is verifiable by reading the code.
The prediction stands; only the citation is unverifiable.

Separately, Week 13 Day 2 did establish that FRAMA is deterministic after the
INITRUN patch: byte-identical row-1 values from two independent test scripts on both
assets. That is a correctness check, not a validation of its properties.

## For Week 14

Either reconstruct the Week 9 validation as a tracked notebook, or amend the Week 9
status from VALIDATED to something accurate. Related: the exported CSVs live in
`C:/zorro/Data/` outside version control, which is the same reproducibility gap in a
different form.
