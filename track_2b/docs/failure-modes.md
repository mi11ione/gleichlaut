# Where Apertus fell short, and what the design does about it

Every row is a measured result; the numbers and their sources are in `technical_report.md` §5 and `claims.tsv`.
Gleichlaut uses Apertus for one job only, rewriting the wording of a French or Italian paragraph under a lock, because
that is the one job where both sizes were measured to beat a no-model baseline. Everything else is code. Read the rows
as evidence about this pipeline and these builds, not about Apertus in general. The research ran these tests on a
third-party MLX 4-bit DWQ build (`m1rkocasu/Apertus-v1.5-8B-text-MLX-4bit-DWQ`). In our parity battery it agrees on 610
of 648 decisions with bf16 weights of `swiss-ai/Apertus-v1.5-8B-DPO`, an intermediate post-training checkpoint, not the
released v1.5 8B (revision not recorded); the shipped GGUF builds agree on 622 (Q4_K_M) and 638 (Q8_0). The 548 of 648
quoted earlier belongs to our own MLX 4-bit g64 build of the released checkpoint, which ran none of these tests. After a juror from the Apertus team asked, every 8B test we had prompts and data for was
re-run on the shipped Q8_0 with the same prompts and items on CPU runners (PREREG R8,
`eval/results/failure_modes_q8_0.json`): the 8B numbers below are Q8_0, the MLX number in parentheses. The 70B rows are
whatever Public AI served under that name.

| What we asked of Apertus | What happened | Design consequence |
|---|---|---|
| **Free translation** of the new German paragraph (8B Q8_0; MLX 4-bit in parentheses) | 0 of 120 exact (0); the negation/modality/number counters fire on 70 of 120 outputs (78); in a seeded 20 of them, blind annotators found 6 real meaning changes (MLX: 2 in one hand-checked 20), e.g. French "il convient d'essayer" for "ist auszuprobieren" (must → should; MLX: Italian "deve" → "dovrebbe"): about 21 in 120 extrapolated (8), none flagged | Never translate from scratch. The old French/Italian text is the starting point and is locked outside the edit windows |
| **Edit only a marked span** ("window-only", 8B Q8_0 and 70B) | Both models ignored the span and restarted the paragraph: 8B 54% of windows (MLX 73%), 70B 81%. Exact match equal to rules-only (5.8%); chrF *worse* than doing nothing (8B 86.8, rules-only 88.8) | Whole-paragraph rewrite, then a deterministic lock check against the windows |
| **Write numbers** | Not needed: every number is a slot code ⟨A⟩ in the prompt and code writes the value back. The 8B additionally cannot emit a digit (logit mask). 0 model-written digits in every measured call, both sizes | Numbers are never the model's job, so a drafted amendment cannot introduce a model-written number (the 70B wrote 3 number words in 166 drafts, all flagged). Divergences already in the old text are carried forward |
| **Judge equivalence** of DE/FR/IT texts (Fedlex divergence finder) | Asked yes/no: 8B Q8_0 0 of 9 known divergences found (MLX 0), answering "Nein" (they differ) in 1 of 270 questions; 70B 0 of 9, "Nein" in 2 of 270. Under the "same meaning" prior the 8B's log-probabilities still rank: Q8_0 AUROC 0.77, divergent language first in 3 of 9, about the same in both presentation orders (0.74 / 0.78); MLX 0.81 and 6 of 9, but order-fragile (0.82 / 0.62). The API exposes no log-probabilities for the 70B | No model judges anything. Guards are deterministic and frozen |
| **Type numeric conditions** (operators, thresholds) for a structured comparison | 8B Q8_0 operator accuracy 39% over 831 conditions (MLX 36%), still a strong "≥" prior (≥ is the top answer for 619); its errors correlate across languages even more (53 of 77 held-out triples wrong in all three, as on MLX; phi 0.78–0.85 against 0.51–0.61) | Not used; the slot guard compares numbers, negations and modal verbs by lexicon counts |
| **Fix its own error when told** (one retry with the lock violations) | 8B Q8_0 greedy retry fixed 1 of 23 on dev 120 (MLX 0 of 26: it repeats itself) and 0 of 40 on the held-out 166, where its guarded re-ask kept 1 of 100; 70B guarded re-ask fixed 3 of 98 on the fresh set | Kept (it is cheap) but never relied on; a re-asked draft replaces the original only if it passes every guard |
| **SL drafting with the 8B** (dev 120, guards3, no re-ask) | Q8_0: 82.5% flagged, no meaning error among its 21 ready drafts (14 identical to BAG's text, 6 cosmetic or minor). MLX 4-bit: 85.0% flagged and 1 ready draft reversed a meaning ("riduzione" for "Erhöhung"; Q8_0 renders the same item correctly) | Superseded by the shipped GGUF builds with the full pipeline on the held-out 166 (PREREG R1): both pass; the default Q8_0 has 0 meaning errors, 0 stale and 0 German among its 62 ready drafts (Q4_K_M: 0 / 1 / 2), so the 8B on a CPU is the SL default |
| **SL terminology with the 8B GGUF** (held-out 166; a pipeline gap: the prompt does not supply BAG's house terms) | 29 of its 60 ready drafts use "assurance obligatoire de maladie" / "assicurazione obbligatoria di malattia" where BAG writes "…des soins" / "…delle cure medico-sanitarie" | The 70B (3 of 66 ready drafts need a fix), or a terminology list for the 8B (next step) |
| **SL drafting with the 70B, guards v2** (out-of-sample 242) | Failed the pre-registered rule: 4.1% of items left German or Germanised terms in the draft unflagged ("immunothrombozytopénie", "Semaglutid", "Folgendo", DME/RVO) | guards3 adds a copied-from-German detector, a mined abbreviation map and an out-of-vocabulary check, then was tested on a fresh set |
| **Statute drafting** (Fedlex, 120 FR/IT, shipped lane with lock + slots + G1–G4; DEV) | 8B: 0 real errors but 8 German/stale among drafts marked ready (6.7%). 70B on the same items (PREREG R5): 2 real errors and 5 German/stale, exact 48.3% vs 50.0%. The shipped GGUF builds (R6): 4 real errors each and 9–10 German/stale (all four arms labelled under one protocol: two blind annotators and a third on disagreements), exact 45.8% (Q4_K_M) / 47.5% (Q8_0) | 8B on CPU for statutes (against the shipped Q8_0 the 70B has 48.3% exact vs 47.5% and 2 real errors vs 4 among ready drafts, no safer); every statute draft goes to review. Vocational titles ("EFZ" → CFC/AFC) are the common miss: the terminology guard G6 has only SL-mined pairs |

## Known blind spots of the guards (not fixed; disclosed)

- **Direction flips** inside an edited span (increase ↔ reduction) are checked by no guard. Seen once, in an 8B MLX output.
- **A single dropped word** inside an edited window can pass the removal budget (G3c allows 3 × the German removal + 1),
  e.g. the out-of-sample "provare con" drop.
- **Over-flagging**: about two thirds of flagged drafts on the fresh set need no change (13 of a seeded 20). The
  out-of-vocabulary guard flags ordinary words that are rare in the SL corpus ("glutine", "uniforme").
- **Concentration**: one boilerplate family carries half of the ready drafts of the fresh set; without it the flag rate
  is above the 70% cap.
- **0 unflagged errors in 166** (the pre-registered rule counts errors that pass the checks; flagged drafts go to review and
  only a seeded 20 of them were read) is a point estimate: the 95% upper bound is 2.3% per item and 9.6% per German change, so 166 items
  cannot show that the pre-registered 1% limit holds; they show it was not exceeded, and only as far as the Claude annotators see errors (R17: on real errors BAG corrected
  they flagged 5 of 17 with BAG's text shown).
