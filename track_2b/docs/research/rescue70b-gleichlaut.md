# Research record (verbatim): 70B on the dev 120 and the guard follow-up (Gleichlaut sections only)

Copied from the research log `spikes/rescue70b/results.md` (not part of this repository; sha256 of the full file when copied: `a44dc89fbd0c20191e45ff14776449585b8de24e633d554f6e8280d08ec7052b`).

---

## A. Gleichlaut S2 (120 FR/IT items, same as the 8B)

Arms:
- **(a)** `s2.py run_2` logic: window-only locked, numbers as slot codes.
- **(b)** `s2b.py` logic: whole-paragraph locked rewrite, then `lock.check`, one retry with feedback, then flag; numbers as slot codes; rule-only items skip the model. The 8B never ran this arm on SL.

Scoring: `score2.main()` unchanged, pointed at `rescue70b/gl/`.

| Arm (FR+IT, n = 120) | exact | edit-F1 | chrF | lock OK | flagged | unflagged | numbers not in DE (occurrences / items) | model-written digits |
|---|---|---|---|---|---|---|---|---|
| Rules only | 5.8% | 7.1 | 88.8 | 98% | 54% | — | 46 / 37 | — |
| 8B (a) window-only | 5.8% | 22.4 | 84.5 | 54% | 82% | 22 | 21 / 14 | 0 (logit mask) |
| **70B (a) window-only** | 5.8% | 28.2 | 84.2 | 45% | 88% | 15 | 11 / 8 | **0** of 226 windows |
| **70B (b) whole paragraph + lock + 1 retry** | **17.5%** | **58.6** | **93.2** | 78% | 46% | 65 | 9 / 7 | **0** of 113 + 43 retries |
| 70B (b), FR / IT | 15.0% / 20.0% | 55.9 / 61.4 | 93.4 / 93.0 | 72% / 85% | 50% / 42% | | | |
| 70B (b), model-touched items (n = 113) | 12.4% (rules 0.0%) | 56.1 | 92.7 | | 49% | | | |

**Kill-rule deltas against rules-only** (paired cluster bootstrap, 95% CI):

| | exact | edit-F1 | chrF |
|---|---|---|---|
| 8B (a) | +0.0 | +15.3 [+10.8, +20.0] | −4.3 [−6.3, −2.3] |
| 70B (a) | +0.0 | +21.1 [+16.4, +25.9] | −4.6 [−6.7, −2.3] |
| **70B (b)** | **+11.7 [+5.8, +18.3]** | **+51.5 [+44.3, +58.5]** | **+4.4 [+2.7, +6.1]** |

**Window obedience** (arm a). A window counts as disobeyed when the output is longer than the old window + 1.5 × the DE insertion + 30 characters. This rule reproduces the 8B's 165/226 exactly.

| | Windows within the window |
|---|---|
| 8B | 61/226 = 27.0% |
| 70B | **43/226 = 19.0%** |

The 70B restarts from the start of the paragraph just as the 8B did, and slightly more often.

**Hand check: every unflagged item, read in full against DE old/new and the official FR/IT** (`gl/handcheck.tsv`).
- **(a) 15 unflagged.**
  - 5 rule-only exact.
  - 3 meaning-equivalent: 16-fr, 16-it, 56-fr.
  - 6 garbled duplications that keep the content: 00-it, 05-it, 18-it, 46-it, 26-fr, 57-it.
  - **1 real error:** 57-fr drops "un montant déterminé par emballage remis". The 8B made the same error on this item.
- **(b) 65 unflagged.**
  - 16 exact.
  - 28 meaning-equivalent. Some are awkward ("Suivant code d'indication à transmettre", "codice indicativo"), and 25-it has grammar errors but matches the DE.
  - 3 cosmetic: product names in German spelling (14-fr, 32-fr, 52-fr).
  - **7 German left untranslated:**
    - headings: 00-fr, 00-it, 40-fr, 40-it;
    - 16-fr: the new face/scalp/adult condition is inserted in German;
    - 16-it: "im viso";
    - 33-it: "gemäss Referenzdokument …".
  - **9 stale (the DE change was silently not applied):**
    - 12-it, 21-fr, 26-fr, 35-fr: output = old text. 12-it keeps the deleted IPF diagnosis requirement; 26-fr keeps the deleted prior-approval requirement; 35-fr lacks the new indication for men.
    - 04-it and 24-fr keep "indicato/indiqué" for "vergütet".
    - 07-it: the new indication heading is missing.
    - 31-it: the old indication sentence is kept and the new prior-approval requirement is missing.
    - 44-fr: the code is removed but "le code suivant … :" is left dangling.
  - **2 real meaning errors:**
    - 21-it: "viene come terapia sostitutiva", so the reimbursement predicate is gone;
    - 24-it: "viene rimborsato nei pazienti adulti" drops the condition "come terapia sostitutiva".

| Kill rule | Threshold | 8B (a) | 70B (a) | 70B (b) |
|---|---|---|---|---|
| Exact vs rules-only | ≥ +5 pts | +0.0, fires | +0.0, fires | **+11.7, passes** |
| …or edit-F1 gain and chrF ≥ rules-only | both | edit-F1 +15.3 but chrF −4.3, fires | edit-F1 +21.1 but chrF −4.6, fires | passes |
| Unflagged real meaning errors | ≤ 1/120 | 6/120, fires | 1/120, passes (but 6 garbled duplications) | **2/120, fires** (plus 9 stale and 7 German-left, all unflagged) |
| **Verdict** | | KILL | KILL | **KILL** (narrowly on the error count; clearly if stale texts count) |

**What would be needed to revive (b).** None of this was tested.
- Detecting German left in the FR/IT output is a trivial lexical check; it would catch the 7 German-left items.
- A "was each DE op realised?" check would catch most of the 9 stale items.
- Neither check catches 21-it or 24-it, a dropped word inside an otherwise-correct sentence. The structured condition guard from the 8B write-up is still the missing piece.


# Follow-up: deterministic guards for A(b), the whole-paragraph arm (9 Oct 2026)

**Scope.**
- Guards were run on the 120 cached outputs. One optional 70B re-ask was sent through the gateway (tag `gl-70b-guard`, cap $0.5, spent **$0.1673**).
- **Total spend for all rescue work: $1.4491** (fx 0.0614 + rp 0.3946 + wf 0.2973 + gl 0.5285 + gl-guard 0.1673, plus the gateway self-test $0.0001).
- Code: `gl/guards.py`, `gl/guard_eval.py`, `gl/reask.py`. Outputs: `gl/reask/arm2b.jsonl` and `gl/reask/scores.json`. Labels for the re-asked outputs: `gl/reask/handcheck_reask.tsv`.

## Guards (deterministic, stdlib, on top of the existing lock check, slot guard and unknown-slot check)

| Guard | Rule |
|---|---|
| **G1 untranslated** | Tokens the output *adds* relative to the old FR/IT (multiset difference) that are German. "German" means one of: a German-only function word (der, die, das, und, oder, mit, von, für, bei, auf, im, zur, nach, nicht, ist, wird, gemäss, …), an umlaut or ß, or a lowercase -ung/-ungen ending. ALL-CAPS product names are ignored |
| **G2 stale change** | For each DE op, its lock window in the old FR/IT must contain target edits mirroring it. If DE adds k content tokens, the target must add ≥ 0.5·k content tokens in that window; the same holds for removals. Content tokens are words of ≥ 4 letters outside the DE/FR/IT stoplists, case-insensitive. Numbers are excluded because the existing slot guard already mirrors them |
| **G3a dropped outside** | Content tokens of the old FR/IT outside every DE-op window must survive in the output |
| **G3c unjustified removal** | In each window, content tokens the target removes may number at most 3 × the DE op's removed content tokens + 1. The factor 3 allows for German compounds |
| **G4 duplication** | A 6-gram that occurs ≥ 2 times in the output and more often than in the old text |

**Design history** (so that every number below is read as in-sample):
- **v1** was G1 + G2 (any added or removed content) + G3a. It was designed after reading the 2b hand check.
- Two principled bug fixes came before evaluation: case-only DE edits (Ezetimib → EZETIMIB) no longer count as content, and numbers are left to the slot guard. The second fix removes the 27-fr/it lock false positives.
- An in-window *net-loss* variant of G3 was tried and dropped. It caught nothing that G2 did not, and it flagged 13–15 equivalent items because German compounds give fewer DE content tokens than the FR/IT phrases.
- **v2** adds the proportional G2, G3c and G4. It was designed after the out-of-sample check below exposed v1's misses.

## Results on the 120 items

| Stage | Flagged | Unflagged real errors | Unflagged stale | Unflagged untranslated | Unflagged other | Exact (all 120) |
|---|---|---|---|---|---|---|
| 2b as run (lock + slot guard + 1 lock retry) | 55/120 = 46% | **2** | **9** | **7** | 16 exact, 28 equivalent, 3 cosmetic | 21 = 17.5% |
| + guards v1 | 74/120 = 62% | 0 | 0 | 0 | 16 exact, 28 equivalent, 2 cosmetic | 17.5% |
| + guards v2 | 86/120 = 72% | 0 | 0 | 0 | 16 exact, 16 equivalent, 2 cosmetic | 17.5% |
| **+ guards v2 + one 70B re-ask** (the re-ask output is kept only if it passes every guard) | **81/120 = 67.5%** | **0** | **0** | **0** | 14 exact, 21 equivalent, 2 cosmetic, 2 minor heading defects | **21 = 17.5%** |

**Guard v1 against the 18 known-bad unflagged items.**
- G1 caught all 7 German-left items.
- G2 caught all 9 stale items and **both real errors**: 21-it and 24-it, where DE adds "vergütet" and the target adds no content.
- Cost: 1 cosmetic item newly flagged, and 0 of the 44 exact or equivalent items.

**Re-ask.**
- 86 flagged model items were re-asked once with their concrete complaints (lock violations, slot-guard deltas, German words, unmirrored DE ops, removed words, repeated n-grams).
- Only **7/86 came back clean**:
  - 16-fr, 16-it: German translated;
  - 21-fr, 24-fr: "est remboursé";
  - 35-fr: the missing sentence for men added;
  - 00-it ("Biliario (BTC)") and 40-fr ("HCC cancer hépatocellulaire (HCC)"): minor heading defects, neither German nor a meaning change.
- All 7 were hand-checked. No digits were written in any re-ask. The re-ask produced no new exact outputs.
- Of the final unflagged set, 7 outputs changed in the re-ask; the other 32 were already labelled in the original hand check.

**What the 81 flagged items are.**
- Known good: 7 exact (5 model outputs, plus 27-fr/it, the rule-only items the lock check rejects) and 12 equivalent.
- Known bad: 2 real errors, 6 stale, 3 German-left and 1 cosmetic.
- 50 were flagged by the original lock/slot stack and never labelled.

**Pass rule** (coordinator):

| Criterion | Threshold | Result |
|---|---|---|
| Unflagged real errors | ≤ 1/120 | **0/120: pass** |
| Unflagged stale + untranslated | ≤ 2 | **0: pass** |
| Exact vs rules-only | ≥ +5 pts | 17.5% vs 5.8% = **+11.7 [+5.8, +18.3]: pass**. Edit-F1 +53.6 and chrF +4.8 against rules-only after the re-ask |
| Flag rate (translator review cost) | (reported) | **67.5%** (81/120). The rules-only arm still needs 113/120 by hand. So the 70B plus guards delivers **39/120 = 32.5%** of items ready to accept (14 exact, 21 equivalent, 4 cosmetic/minor). Translators review 81 |

## Out-of-sample check (cached outputs the 2b guards were not designed on)

| Guard version | 8B window arm, 22 unflagged (6 real, 7 stale, 2 harmless duplications) | 70B window arm, 15 unflagged (1 real, 6 garbled duplications) | False flags on exact/equivalent there |
|---|---|---|---|
| v1 (designed on 2b only) | real **2/6**, stale **4/7** | real **0/1**, garble **0/6** | 0 |
| v2 (designed after seeing this table) | real 6/6, stale 6/7 (misses 08-it) | real 1/1, garble 6/6 | 0; the 2 harmless duplications also pass |

**Reading.**
- v1's in-sample 18/18 overstated it: on outputs it was not tuned to, v1 caught 6/20.
- v2 catches 19/20 bad outputs across all three cached sets with no false flags on exact or equivalent items there. However, v2 was shaped by those same sets, so **no clean held-out estimate exists**.
- The misses all share one pattern: a condition dropped *inside* an edited window, or a duplicated clause that hides a drop. That is exactly what a token-count guard can only approximate.

## Final verdict for Gleichlaut S2 with the 70B

**Conditional pass, in-sample only.** With guards v2 and one re-ask, the 70B whole-paragraph arm meets every part of the pass rule on the 120 items:
- 0 unflagged real errors;
- 0 unflagged stale or untranslated items;
- exact +11.7 over rules-only.

The cost is a flag rate of **67.5%**. About a third of the items come out ready to accept, and two thirds go to translators.

This is not yet a clean pass:
- The guards (v1, then v2) were designed on these same outputs and on the cached window-arm outputs.
- The only uncontaminated signal was poor: v1 caught 6 of 20 bad outputs out of sample.

**Next decisive test.** Run 2b + guards v2 (frozen as committed) + re-ask on fresh SL changes: the 242 unused items of the 362-item pool, or the next monthly snapshot. Then hand-check every unflagged output.
- Estimated cost: about $0.5 for 2b at the measured $0.0017 per call, plus the re-ask at about $0.002 per flagged item.
- Pass if the same rule holds (≤ 1 real, ≤ 2 stale + untranslated per 120, exact ≥ rules + 5) with a flag rate ≤ 70%.
- If it fails, Gleichlaut 2B stays killed.

---

