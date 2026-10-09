# Research record (verbatim): equivalence judging and numeric typing

From `spikes/rescue70b/results.md` section D (sha256 `a44dc89fbd0c20191e45ff14776449585b8de24e633d554f6e8280d08ec7052b`) and `loop/learnings.md` (sha256 `b4179d1cc89d3c794ed41b53a42c0c466cf98b3cd84bfe5ca1ba5ccee7ff8dc7`).

---

## D. Fedlex 9 + 36 (round7b pairwise prompt `PAIR["de"]`, verbatim)

**Prompt and orders:** DE–FR, DE–IT and FR–IT, each in two orders. Order *ab* puts the first language first and asks "Ja oder Nein"; order *ba* puts the second language first and asks "Nein oder Ja".

**Scoring:**
- P(differs) per pair is the share of "Nein" over the two orders.
- Localisation follows round7b: score(L) = mean of the two pairs containing L minus the third pair.
- An item is flagged when the maximum score is ≥ 0.5. A hit is a flagged item whose unique argmax equals the gold language.

| Method | Hits /9 | False flags /36 | Notes |
|---|---|---|---|
| **70B pairwise, generation** | **0** | **0** | 2/270 answers are "Nein", both DE–FR in one order only: VZVM 5/2 (gold FR) and ETS Anh. IV (gold DE). The two orders agree 98.5% |
| 8B pairwise, logprob (round7b A) | 0 | 0 | AUROC 0.81 as a log-odds ranker; 6/9 unthresholded argmax (needs logprobs, which are unavailable here) |
| 8B 4-way label (round 7) | 0 | 5 | |
| Rules: slot-vote, typed slots (numbers, period, quantifier) | 1 (VZVM) | 0 | post hoc |
| Rules: slot-vote, primary | 1 (MinöStV) | 18 | |

**Verdict.** Killed. The 70B has the same "same meaning" prior as the 8B, and through generation it does not even leave a ranking. Neither "Nein" answer reaches the 0.5 localisation score; each of the two would need agreement on a second pair.

---


## S-FEDLEX-7b (8 Oct): pairwise and back-translation on the 9 + 36
- No variant passes at a fixed threshold. Pairwise "same meaning?" replaces the DE label bias with a strong "same" bias: P(differs) is e^-13…e^-26.
- **The ranking signal is real.** Pairwise A (German prompt) reaches AUROC **0.81** (0.61 for the 4-way label), and its argmax finds the wrong language in **6/9** (chance ≈ 1/3). It is order-fragile: AUROC 0.82 in one presentation order, 0.62 in the other.
- **Back-translate then judge (B):** AUROC 0.60. The 8B's back-translations *erase or invert* the errors: trimestre → "Winterhalbjahr", doit → "darf", a dropped "nicht".
- **Slot-vote decoder on 8B back-translations (Leggasi S1):** 1/9 hits at 18/36 false flags. The false flags come from German gender pairs, reworded lists, modality and dropped negation. Leggasi's kill rule (<3/9) fires for the back-translation design.
- **Implication:** the 8B can rank and localise inside a known-bad paragraph, not detect. A slot decoder must read the original FR/IT/DE with per-language lexicons rather than back-translations. A possible real divergence surfaced: MWSTG 26/3 (DE "need not be listed" vs FR/IT "must not").

## Dreiklang S1/S2 (9 Oct): KILLED
- 8B typing of number roles in SL texts, held-out half:
  - accepted precision 17.9% (bar 97%); discrepancy precision 3.9% (bar 30%); coverage 8.3%. Known-discrepancy recall 9/10, but hollow (17/20 limitations flagged).
  - Missed Nemluvio. Operator accuracy 36%, with a strong "≥" prior.
- **The 8B's errors are correlated across languages:** pairwise phi 0.51–0.61; 53/77 wrong in all three (39.5 expected); 24 identical wrong labels, so agreement is not evidence.
- Regex v2: 81–90% typing accuracy, but it is overfit and also misses the bars.
- New 8B weakness (field guide): typing numeric conditions (operator) is near chance, and its errors repeat across languages.
