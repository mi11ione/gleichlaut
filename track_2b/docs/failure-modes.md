# Where Apertus fell short, and what the design does about it

Every row is a measured result; the numbers and their sources are in `technical_report.md` §5 and `claims.tsv`.
Gleichlaut uses Apertus for one job only, rewriting the wording of a French or Italian paragraph under a lock, because
that is the one job where both sizes were measured to beat a no-model baseline. Everything else is code. Read the rows
as evidence about this pipeline and these builds, not about Apertus in general: several 8B rows were measured on our own
MLX 4-bit build, which agrees with the bf16 weights on 548 of 648 decisions in our parity battery (the shipped GGUF
builds: Q4_K_M 622, Q8_0 638), and the 70B rows on whatever Public AI served under that name.

| What we asked of Apertus | What happened | Design consequence |
|---|---|---|
| **Free translation** of the new German paragraph (8B, MLX 4-bit build) | 0 of 120 exact; the negation/modality/number counters fire on 78 of 120 outputs; a seeded read of 20 of them found 2 real meaning flips (Italian "deve" → "dovrebbe", must → should), about 8 in 120 extrapolated, none flagged | Never translate from scratch. The old French/Italian text is the starting point and is locked outside the edit windows |
| **Edit only a marked span** ("window-only", 8B MLX 4-bit and 70B) | Both models ignored the span and restarted the paragraph: 8B 73% of windows, 70B 81%. Exact match equal to rules-only (5.8%); chrF *worse* than doing nothing | Whole-paragraph rewrite, then a deterministic lock check against the windows |
| **Write numbers** | Not needed: every number is a slot code ⟨A⟩ in the prompt and code writes the value back. The 8B additionally cannot emit a digit (logit mask). 0 model-written digits in every measured call, both sizes | Numbers are never the model's job, so a drafted amendment cannot introduce a model-written number (the 70B wrote 3 number words in 166 drafts, all flagged). Divergences already in the old text are carried forward |
| **Judge equivalence** of DE/FR/IT texts (Fedlex divergence finder) | Asked yes/no: 8B (MLX) 0 of 9 known divergences found, with a "same meaning" prior; 70B 0 of 9, answering "Nein" (they differ) in only 2 of 270 questions. The 8B's log-probabilities carry a real signal (AUROC 0.81, the divergent language ranked first in 6 of 9) but flip with presentation order (0.82 vs 0.62), and the API exposes no log-probabilities for the 70B | No model judges anything. Guards are deterministic and frozen |
| **Type numeric conditions** (operators, thresholds) for a structured comparison | 8B (MLX 4-bit) operator accuracy 36% (strong "≥" prior); its errors correlate across languages (53 of 77 wrong in all three) | Not used; the slot guard compares numbers, negations and modal verbs by lexicon counts |
| **Fix its own error when told** (one retry with the lock violations) | 8B (MLX 4-bit) greedy retry fixed 0 of 26 (it repeats itself); 70B guarded re-ask fixed 3 of 98 on the fresh set | Kept (it is cheap) but never relied on; a re-asked draft replaces the original only if it passes every guard |
| **SL drafting with the 8B** (MLX 4-bit DWQ, dev 120, no re-ask) | 85% flagged and 1 ready draft reversed a meaning ("riduzione" for "Erhöhung") | Superseded by the shipped GGUF build with the full pipeline on the held-out 166 (PREREG R1): it passes (0 meaning errors among ready drafts, 3 stale or German of 166), so the 8B on a CPU is the SL default |
| **SL terminology with the 8B GGUF** (held-out 166) | 29 of its 60 ready drafts use "assurance obligatoire de maladie" / "assicurazione obbligatoria di malattia" where BAG writes "…des soins" / "…delle cure medico-sanitarie" | The 70B (3 of 66 ready drafts need a fix), or a terminology list for the 8B (next step) |
| **SL drafting with the 70B, guards v2** (out-of-sample 242) | Failed the pre-registered rule: 4.1% of items left German or Germanised terms in the draft unflagged ("immunothrombozytopénie", "Semaglutid", "Folgendo", DME/RVO) | guards3 adds a copied-from-German detector, a mined abbreviation map and an out-of-vocabulary check, then was tested on a fresh set |
| **Statute drafting** (Fedlex, 120 FR/IT, shipped lane with lock + slots + G1–G4; DEV) | 8B: 0 real errors but 8 German/stale among drafts marked ready (6.7%). 70B on the same items (PREREG R5): 2 real errors and 5 German/stale, exact 48.3% vs 50.0%. The shipped GGUF builds (R6): 4 real errors each and 9–10 German/stale (all four arms labelled under one protocol: two blind annotators and a third on disagreements), exact 45.8% (Q4_K_M) / 47.5% (Q8_0) | 8B on CPU for statutes (the 70B buys nothing); every statute draft goes to review. Vocational titles ("EFZ" → CFC/AFC) are the common miss: the terminology guard G6 has only SL-mined pairs |

## Known blind spots of the guards (not fixed; disclosed)

- **Direction flips** inside an edited span (increase ↔ reduction) are checked by no guard. Seen once, in an 8B output.
- **A single dropped word** inside an edited window can pass the removal budget (G3c allows 3 × the German removal + 1),
  e.g. the out-of-sample "provare con" drop.
- **Over-flagging**: about two thirds of flagged drafts on the fresh set need no change (13 of a seeded 20). The
  out-of-vocabulary guard flags ordinary words that are rare in the SL corpus ("glutine", "uniforme").
- **Concentration**: one boilerplate family carries half of the ready drafts of the fresh set; without it the flag rate
  is above the 70% cap.
- **0 errors in 166** is a point estimate; the 95% upper bound is 2.3%.
