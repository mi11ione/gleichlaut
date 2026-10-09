# Where Apertus fell short, and what the design does about it

Every row is a measured result; the numbers and their sources are in `technical_report.md` §5 and `claims.tsv`.
Gleichlaut uses Apertus for one job only, rewriting the wording of a French or Italian paragraph under a lock, because
that is the one job where both sizes were measured to beat a no-model baseline. Everything else is code.

| What we asked of Apertus | What happened | Design consequence |
|---|---|---|
| **Free translation** of the new German paragraph (8B) | 0 of 120 exact; lexicon-level flips of negation/modality/numbers in 78 of 120 outputs, none flagged; real meaning flips such as Italian "deve" → "dovrebbe" (must → should) | Never translate from scratch. The old French/Italian text is the starting point and is locked outside the edit windows |
| **Edit only a marked span** ("window-only", both sizes) | Both models ignored the span and restarted the paragraph: 8B 73% of windows, 70B 81%. Exact match equal to rules-only (5.8%); chrF *worse* than doing nothing | Whole-paragraph rewrite, then a deterministic lock check against the windows |
| **Write numbers** | Not needed: every number is a slot code ⟨A⟩ in the prompt and code writes the value back. The 8B additionally cannot emit a digit (logit mask). 0 model-written digits in every measured call, both sizes | Numbers are never the model's job. The class of divergence we found in the live SL (all numbers) is excluded by construction |
| **Judge equivalence** of DE/FR/IT texts (Fedlex divergence finder) | 8B 0 of 9 known divergences found, with a "same meaning" prior; 70B 0 of 9, answering "Nein" (they differ) in only 2 of 270 questions | No model judges anything. Guards are deterministic and frozen |
| **Type numeric conditions** (operators, thresholds) for a structured comparison | 8B operator accuracy 36% (strong "≥" prior); its errors correlate across languages (53 of 77 wrong in all three) | Not used; the slot guard compares numbers, negations and modal verbs by lexicon counts |
| **Fix its own error when told** (one retry with the lock violations) | 8B greedy retry fixed 0 of 26 (it repeats itself); 70B guarded re-ask fixed 3 of 98 on the fresh set | Kept (it is cheap) but never relied on; a re-asked draft replaces the original only if it passes every guard |
| **SL drafting with the 8B** (whole paragraph + guards3, dev 120, MLX 4-bit DWQ) | Quality gain is real (+9.2 exact), but 85% of drafts are flagged (cap 70%) and 1 unflagged draft reverses a meaning ("riduzione" for "Erhöhung") | SL default is the 70B on a certified endpoint; the 8B is the air-gapped fallback in which every item goes to review. GGUF 8B on the fresh set (M1) decides whether this changes |
| **SL drafting with the 70B, guards v2** (out-of-sample 242) | Failed the pre-registered rule: 4.1% of items left German or Germanised terms in the draft unflagged ("immunothrombozytopénie", "Semaglutid", "Folgendo", DME/RVO) | guards3 adds a copied-from-German detector, a mined abbreviation map and an out-of-vocabulary check, then was tested on a fresh set |

## Known blind spots of the guards (not fixed; disclosed)

- **Direction flips** inside an edited span (increase ↔ reduction) are checked by no guard. Seen once, in an 8B output.
- **A single dropped word** inside an edited window can pass the removal budget (G3c allows 3 × the German removal + 1),
  e.g. the out-of-sample "provare con" drop.
- **Over-flagging**: about two thirds of flagged drafts on the fresh set need no change (13 of a seeded 20). The
  out-of-vocabulary guard flags ordinary words that are rare in the SL corpus ("glutine", "uniforme").
- **Concentration**: one boilerplate family carries half of the ready drafts of the fresh set; without it the flag rate
  is above the 70% cap.
- **0 errors in 166** is a point estimate; the 95% upper bound is 2.3%.
