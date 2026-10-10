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
Their first labels (the `real` column of `audit*_*.tsv`) were one annotator's. Under PREREG R14 all 49 findings were
pooled under neutral ids (`audit_relabel_worklist.json`, question unchanged) and labelled again by two fresh blind
annotators, the second in reverse order, and a third on the 1 finding where their answers differed (`audit_relabel.tsv`;
confirmed = real or minor). The two agree whether a finding is real on all 49 (κ 1.000) and the majority agrees with the
first labels on 44 of 49: register 17 of 27 confirmed (first 16), terminology 11 of 11 (8), MiGeL and Analysenliste 6
of 11 (7). The reported audit precision is the majority's; the first labels stay in the results as `first_annotation`.

## Sensitivity: do the annotators catch meaning errors? (PREREG R11)

"0 meaning errors in ready drafts" is only as good as the annotators' ability to see one. R11 measures it
(`tools/plant_sensitivity.py`, seed 20261012, pre-registered and committed before any annotation). Into copies of the 66
fresh-166 ready drafts that every earlier label calls exact (19) or equivalent (47), one meaning error of the REAL class
was planted per copy; the same 66 drafts untouched and 30 real drafts labelled REAL, stale or German earlier were mixed
in, shuffled under neutral ids, a draft's planted and untouched copies never in the same worklist (two worklists of 81
records per protocol). Two fresh blind annotators per worklist labelled them with the instructions above, unchanged:
(a) as used, `official_new` shown; (b) reference hidden, no `official_new` and one sentence changed ("No published version
is available for these records: there is no official_new field."). Both got one operational note (long lines: read
the file so every line shows in full, still only this file). Severe = REAL or stale; Wilson 95% over items
(`eval/results/annotator_sensitivity.json`, re-derived by `replay` from `sensitivity_{a,b}.tsv` and
`sensitivity_key.json`).

| Planted error | n | (a) reference shown: severe by both / either [95% CI, both] | (b) reference hidden |
|---|---|---|---|
| dropped condition or clause | 13 | 13 / 13 [77.2, 100.0] | 13 / 13 [77.2, 100.0] |
| and ↔ or | 12 | 12 / 12 [75.7, 100.0] | 12 / 12 [75.7, 100.0] |
| obligation (doit/deve ↔ peut/può) | 7 | 7 / 7 [64.6, 100.0] | 7 / 7 [64.6, 100.0] |
| scope widened or narrowed | 8 | 8 / 8 [67.6, 100.0] | 8 / 8 [67.6, 100.0] |
| direction / operator flipped | 7 | 7 / 7 [64.6, 100.0] | 7 / 7 [64.6, 100.0] |
| negation dropped or added | 12 | 12 / 12 [75.7, 100.0] | 12 / 12 [75.7, 100.0] |
| a number changed | 7 | 7 / 7 [64.6, 100.0] | 7 / 7 [64.6, 100.0] |
| **all planted** | 66 | 66 / 66 [94.5, 100.0] | 66 / 66 [94.5, 100.0] |

- **False alarms on the same drafts untouched:** (a) 1 needs-fix call by one annotator (an elliptical code sentence, labelled minor), 0 severe; (b) 0 and 0,
  of 66 each. One earlier German label ("I-CANS" copied from the German) was called equivalent or cosmetic by both.
- **Every planted copy was labelled REAL** by both of its annotators in each protocol, in FR and IT, on exact and on
  equivalent bases, inside and outside the boilerplate family 981f07a8. Hiding the published text changed nothing.
- **Real errors are where annotators split.** Of the 30 real drafts, the stale ones were labelled severe by both in
  12 of 12 and the German ones in 14 of 15 under (a). Of the 3 earlier REAL labels, both
  annotators called 1 severe under (a) (either: 2) and 1 under (b) (either: 3); the other two were judged
  "minor" by one or both: a brand name replaced by the substance in clauses the German left unchanged, and "il medico"
  narrowed to "l'oculochirurgo". In the full protocol such a split goes to a third annotator.
- **What it does and does not show.** A single local edit of a known type (one word, a clause, a number) is caught
  every time, with or without the reference: the annotators diff the draft against the old text and the German change
  (several wrote small word-diff helpers over their own worklist file, a deviation from the "one read, one write"
  instruction; none read any other file), so an edit the German change does not explain stands out.
  Errors that look like a plausible part of the amendment (scope drift inside the edited sentence) are harder, as the
  real REAL items show; R14 below plants such errors. The 95% upper bound on severe errors among ready drafts (5.5% for the 70B, 5.8% for Q8_0) is
  unchanged when divided by the measured recall.

## In-span sensitivity: errors that read like part of the amendment (PREREG R14)

R11's plants were single local edits that an annotator can find by diffing the draft against the old text. R14 wrote one
meaning error by hand into each of 38 ready drafts (70B and Q8_0, labelled exact or equivalent; `tools/plant_inspan.py`,
seed 20261017, plants in `inspan_plants.json`), inside the sentence the German change touched and adjoining the amended
wording, as fluent text: scope widened or narrowed (11), a condition half-applied or changed (12), a number or unit on
the wrong noun (8), and/or (7). Planted and untouched copies in different worklists, the 30 real drafts of R11 mixed in,
two blind annotators per worklist with the instructions above (reference shown) and the same operational note
(`inspan_sensitivity.tsv`, `eval/results/annotator_sensitivity_inspan.json`).

- **Every planted copy was labelled severe (REAL or stale) by both of its annotators**: 38 of 38 [Wilson 95% lower bound
  90.8], every type, FR and IT, in and outside the family 981f07a8; the 5 plants that keep part of the old text (a deleted
  condition or the replaced term) were called stale by one or both annotators, the other 33 REAL by both. **False alarms** on the 38 untouched copies: 0 needs-fix, 0 severe.
- The annotators' notes name the edit and why it departs from the German (for example "Added 'in monoterapia o'
  option", "Exon 19 and 21 swapped"): placed inside the amended wording, a clear meaning error is still caught. Where
  annotators split is the real drafts: of the 3 earlier REAL labels among the mixed-in real drafts, both call 1 severe
  (either: 3); the others turn on whether a wording change changes a condition, which is what the third annotator of
  the full protocol decides.

## Real errors, and an annotator from another model family (PREREG R17)

R11 and R14 planted errors that a Claude agent wrote, and Claude agents caught them. R17 uses errors that people made.
It takes every place in the SL snapshot series (2026, plus the two 2025 captures) where BAG changed a French or Italian
limitation while the German stayed byte-identical (`tools/r17_real_errors.py`). That gives 29 changes. 12 are
typography only (11 of them Vegzelma → VEGZELMA). That leaves **17 content changes, and all are used** (fewer than 30
exist): negation/operator 2, words 15, number 0. Ten of the 17 are one house-wording sweep of Opdivo's French code
sentence («correspondant à … communiqué» → «de … transmis»). In two Opdivo French changes, BAG's *new* text is the
defective one: it drops the German's code sentence and leaves «. .». This was declared before any annotation, so those
two count as errors in the new text.

Each change became two records. The error record holds the text that disagrees with the German; the control holds the
correct text. Both show the German unchanged and draft = tgt_old, and the two records of a change never share a
worklist. The context paragraph of the instructions was adapted: the German is unchanged, and the draft is judged
against it as if it were new. The rest of the instructions was given verbatim. Two fresh blind annotators labelled each
worklist, under (a) the reference shown and (b) the reference hidden (`r17_real_errors_{a,b}.tsv`,
`eval/results/annotator_real_errors.json`).

| 17 real errors | (a) reference shown | (b) reference hidden |
|---|---|---|
| needs fix, both / either [95% CI, both] | 5 / 5 [13.3, 53.1] | 7 / 11 [21.6, 64.0] |
| severe (REAL, stale, german), both / either | 4 / 4 | 4 / 5 |
| the 10 wording-sweep changes, needs fix by either | 0 | 5 |
| the 7 other changes, needs fix by both | 5 | 6 |
| false alarms on the 17 controls: needs fix / severe, by either | 1 / 1 | 10 / 4 |
| κ on needs fix between the two | 0.892 | 0.531 |

- **What they catch.** Both annotators label the same 4 errors severe under both protocols: «au moment de la remise»
  for the administration time with the VAT sentence missing (Keytruda), «di prima linea» added in Italian (Jemperli),
  and the two dropped code sentences. Under both protocols, both also call for a fix to the stray French «n'» in «n'est
  destiné» (Resolor). They accept the house-wording sweep as equivalent when BAG's text is shown.
- **What they miss.** Italian «assicurazione malattie» for «assicuratore malattia» (Resolor) is called equivalent in
  both protocols, and «dell'indicazione» for «di indicazione» under (a). Recall over all 17 content changes is low (5
  of 17 with the reference) because most of BAG's corrections are wording preferences, not meaning errors.
- **Without the reference, BAG's corrected texts draw calls too.** 10 of 17 controls get a needs-fix call from at least
  one annotator under (b), and most notes name a defect that is still in BAG's current text: Opdivo .04 FR has no
  «avancé» for «fortgeschrittenem» in either version; the Opdivo .07 FR heading drops «adjuvant»; the Italian reads
  «locale avanzato». So under (b), a needs-fix call on the sweep does not tell the error from its control.

**Apertus 70B as a second, non-Claude annotator** (`eval/results/annotator_crossfamily.json`). It was called through
the development gateway: 117 requests, all served by `swiss-ai/apertus-v1.5-70b`, temperature 0, fixed answer format,
0 unparsed. It answered the same question as the Claude annotators.

- **Audit findings (the audit uses no model).** Apertus calls all 49 findings real (36) or minor (13), so it confirms
  every one. That agrees with the R14 Claude majority on 34 of 49, which is exactly the share the majority confirms:
  κ 0.000. The three-way answer agrees on 25 of 49. It never answers "not", so it cannot check the 15 findings the
  Claude majority rejects.
- **The 17 real errors.** Apertus flags 2 with the reference shown (the Opdivo .04 dropped sentence REAL; the Resolor
  French minor, for the insurer word) and 1 hidden (the Resolor Italian, for "German left", which is wrong). It flags 0
  of 17 controls under either protocol. Agreement on needs fix with each Claude annotator is 31 and 30 of 34 under (a)
  (κ 0.532, 0.452) and 17 and 15 under (b) (κ −0.059).
- **What it shows.** On these tasks the 70B does not discriminate. It says yes to every audit finding and no to almost
  every draft, so it can neither confirm nor contradict the Claude labels. The κ 1.000 between the two Claude
  annotators remains agreement within one model family, as the juror said. Its value is bounded by part A: the Claude
  annotators catch the real meaning errors listed above, and they disagree with each other where the call is a matter
  of wording.

## Re-running it

Any capable LLM agent, or a translator, can be given a worklist and the instructions above. The labels will not be
byte-identical (annotators are not deterministic), so what reproduces is the protocol and the agreement, not the file.
A BAG translator's read of the ready drafts is the obvious next annotator.
