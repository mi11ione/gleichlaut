# Labelling protocol (blind Claude annotators)

Every label in this folder was written by a blind Claude agent with the instructions below; no human labels were used
(the research labels of the first fresh-166 annotation were also agent-written). The protocol is the one pre-registered
in `eval/prereg/PREREG.md` R1.

1. **Worklist.** The items to label (every ready non-exact draft, plus a seeded sample of 20 flagged drafts, seed
   20261009) are written to a JSON worklist with neutral ids (`G00`, `Q00`, …), in shuffled order, with only these
   fields: `id, lang, de_old, de_new, tgt_old, draft, official_new`. The guard verdicts, the model, the run and the other
   annotators' labels are not in it. The id → key map is kept apart and never shown (`*_worklist.json` here are those
   worklists).
2. **Two annotators.** Two fresh agents each read only the worklist and write one TSV (`id, needs_fix, class, note`).
   The second reads the records in reverse order.
3. **Tie-break.** Every record where the two disagree on `needs_fix`, on the class of a ready draft, or where one says
   `REAL`, goes to a third fresh agent in a new shuffled worklist (`*_tiebreak_worklist.json`); the final label is the
   majority of three (the third decides). Agreement on `needs_fix` and Cohen's κ are reported in the results files.
4. **Merge.** The labels are mapped back to item keys into one TSV per run (`A_*`, `B_*`, `T_*`, `final_fix`, `final`).

## Instructions given to each annotator (verbatim)

> You are a blind annotator for a translation-quality evaluation. Read ONLY this file: `<worklist>` (N records). Do NOT
> open, search or list any other file or directory. Use only the read of that file and one write of your output file.
> No web access.
>
> Context: Swiss drug-reimbursement conditions (BAG Spezialitätenliste "limitations"). The German text was amended
> (de_old -> de_new). A system drafted the matching amendment of the French or Italian text (lang) starting from the old
> target text (tgt_old) -> draft. official_new is what the authorities published. Official translators sometimes also
> fixed things the German change did not touch; a draft is NOT expected to make those extra fixes.
>
> For each record, read de_old, de_new, tgt_old, draft and official_new in full and decide:
> 1. needs_fix: "no" if a translator could accept the draft as the correct amendment (applies exactly the German change,
>    meaning-preserving; wording may differ from official_new), "yes" otherwise.
> 2. class, exactly one of: exact (equals official_new ignoring whitespace and apostrophe style); equivalent (correctly
>    applies the German change; differences are only extra fixes the official translators made or harmless wording);
>    preexisting (only problem was already in tgt_old and untouched by the German change); cosmetic (correct meaning,
>    cosmetic defect e.g. spacing, product name spelling); minor (small defect, no condition changed, no German left,
>    e.g. a calque or non-standard term); german (German words, German abbreviations, Germanised compounds or German
>    hyphenation artefacts left in the draft); stale (the German change is not or only partly applied); REAL (the draft
>    changes a condition's meaning relative to the new German: dropped/added condition, changed and/or, changed
>    obligation, wrong scope, reversed direction, wrong number). If several apply, pick the most severe:
>    REAL > stale > german > minor > cosmetic > preexisting > equivalent > exact.
>
> Write a TSV to `<output>` with header `id\tneeds_fix\tclass\tnote` (note <= 20 words). Read every record fully; do
> not skim long paragraphs. Report back only "done" plus counts per class, computed from the file you wrote.

The audit worklists (`audit*`) use the same blind set-up; each record carries the texts, the finding and its own
`question` field (whether the finding is a real divergence between the language versions).

## Re-running it

Any capable LLM agent, or a translator, can be given a worklist and the instructions above. The labels will not be
byte-identical (annotators are not deterministic), so what reproduces is the protocol and the agreement, not the file.
A BAG translator's read of the ready drafts is the obvious next annotator.
