# Disagreements and their resolution (blind third annotator)

Two annotators labelled the fresh-166 hand-check sample (49 unflagged non-exact drafts + 20 flagged, seed 20261009):
the research labels (first annotator, `fresh166_unflagged.tsv`, `fresh166_flagged20.tsv`) and a blind second Claude
agent that saw only the texts, in shuffled order, without the guard verdicts or the first labels
(`fresh166_second_annotator.tsv`; worklist `fresh166_second_annotator_worklist.json`). Agreement on "needs a fix":
62 of 69, Cohen's κ 0.532 (`eval/results/agreement_fresh166.json`).

**On the 49 drafts the guards passed, the second annotator found no meaning error, no stale change and no untranslated
German.** It marked 3 of them as needing a small fix (below). The 7 disagreements:

| Item | Set | First | Second | Note |
|---|---|---|---|---|
| wb032-it | unflagged | equivalent | needs fix, minor | "assicurazione malattia obbligatoria" for OKP instead of the usual "assicurazione obbligatoria delle cure medico-sanitarie" (terminology) |
| wb085-fr | unflagged | equivalent | needs fix, cosmetic | "SGLT - 2" spacing artefact |
| wb085-it | unflagged | equivalent | needs fix, cosmetic | same |
| wb004-fr | flagged | good | needs fix, minor | calque "Suivant code à transmettre" |
| wb076-fr | flagged | good | needs fix, german | "un GLP-1-analogue" (Germanised compound) |
| wb045-fr | flagged | bad (REAL) | no fix | the draft changes "et" → "ou" outside the German edit. The old French has "(OMD) **et** d'une perte de vision…" where the German has "(DME) **oder** eines Visusverlustes…": the draft aligns French with German. The lock flagged it as an edit outside the change. Decide: an error against the official text, or a correct fix of a pre-existing divergence that belongs in review |
| wb047-fr | flagged | bad (REAL) | no fix | same pattern as wb045-fr |

Context for wb045/wb047: in the current feed (6 Oct 2026) four ranibizumab limitations (BYOOVIZ3, LUCENTIS3, RANIVISIO2,
XIMLUCI.02) read "(DME) oder eines Visusverlustes…" in German and "(OMD) et d'une perte de vision…" in French. The
sentence enumerates reimbursed indications, where "and" and "or" plausibly mean the same; we do **not** count this as a
divergence. The draft's "et" → "ou" is an unrequested edit outside the German change, which the lock correctly flagged.

Effect on reported numbers, whichever way these go: none on the pass rule (no severe class among unflagged drafts in
either annotation). wb032-it / wb085 would move 3 unflagged drafts from "equivalent" to "minor/cosmetic"; the flagged-sample
waste estimate (13 of 20 need no change) would be 13 ± 2.

## Resolution

A blind third Claude annotator (worklist `fresh166_tiebreak_worklist.json`, labels `fresh166_tiebreak.tsv`; it saw only the
texts, shuffled) labelled the 7 items and sided with the second annotator on "needs a fix" in 7 of 7. Final labels are
the majority of three. No human labels were used. Result: 3 of the 66 ready drafts need a small fix (wb032-it terminology,
wb085-fr/it spacing; none severe); 13 of the 20 sampled flagged drafts need no change (`eval/results/agreement_fresh166.json`).
