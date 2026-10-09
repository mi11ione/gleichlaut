# Research record: guard freeze and the fresh 2025 run (verbatim excerpt)

Verbatim copy of two sections of the research log `spikes/rescue70b/results.md` (not part of this repository; sha256 of
the full file at the time of copying: `a44dc89fbd0c20191e45ff14776449585b8de24e633d554f6e8280d08ec7052b`). They record, in order: the failed out-of-sample run, the design of guards3 on
those outputs, the freeze record **written before any fresh-set output existed**, and the fresh run. The hashes in the
freeze table are the ones `tools/freeze.py` checks the vendored files against.

What this does and does not prove: the research log is a plain file, so its order of writing is not cryptographically
time-stamped. What can be checked here: every hash in the freeze table matches the vendored files; the recorded fresh
responses were all produced by the frozen code (every request rebuilt byte-for-byte); and the guards3 resources are built
only from the Jun 2025 capture, which predates every new text of the fresh set.

---

# Out-of-sample test of the frozen 2b pipeline (9 Oct 2026)

## Freeze record (written before any out-of-sample output existed; `oos/` then held only `oos.py` and `items_oos.json`)

**Frozen configuration.** `gl/guards.py` as below, with V2 = True, PROP = 0.5, UNJ = (3, 1), NG = 6 and G3B = None. These values are set by `reask.py`.

**Pipeline.**
1. `gl70.py run_2b`: whole-paragraph locked rewrite, lock check, one retry.
2. `reask.py`: full guard stack, then one re-ask with the complaints. The re-ask output is kept only if it passes every guard.
3. `oos/oos.py` runs both with only paths, tag and cap substituted. The substitutions are asserted.
4. One addition in `oos.py`: a gateway BUDGET refusal during the re-ask counts as "not re-asked", so the original output is kept and stays flagged.

| File | sha256 |
|---|---|
| `gl/guards.py` | `d0d1e0d47e3828bf127e05572e055391a6eba9f9e89108b4c09e67a7fd1524f0` |
| `gl/gl70.py` | `f2a207787b2ee024f67959ba5ba3001c7da44907effc50ec3e1d5fa8940ad3b8` |
| `gl/reask.py` | `5b30a30a170117a9cc27baaeb6cf04395bf097c3475cb00d1db4e68286f84920` |
| `oos/oos.py` | `001c642780a4ab91f80f0d15ea29faedf168fe811794070c8deaf882f29d8fec` |
| `common.py` | `0ae44b4e6ba6e7fecc2d36d671a4afd5c7c6e5a60a062521339c63bdeac7c753` |
| `gleichlaut/s2/lock.py` | `1409b2ad5f5acc68bc9ace45620f86131681ec6e33d9d30d62b3ad0141f9c29f` |
| `gleichlaut/s2/gl2.py` | `08aefe04a102e13fe7d37fad2b05a47b23a96b8952a35b7e0341bba47d2f297c` |
| `oos/items_oos.json` | `2a2bfd7fa7c15c682add61b8d6c8e306a6ee5568132bdf637194526f4b552937` |

**Items.**
- The 242 items of the 362-item eligible pool not in the 120: 121 DE changes × FR/IT, with the same S2 exclusions, since `items_all.json` is the post-exclusion pool.
- **Family overlap with the 120:** 102 items fall in 15 families already seen; 140 items fall in 40 families not seen.

**Pass rule.**
- Unflagged real errors ≤ 1%.
- Unflagged stale + untranslated ≤ 2%.
- Exact ≥ rules-only + 5 points.
- Flag rate ≤ 70%.

**Settings.** Tag `gl-70b-oos`, cap $1.0.

## Run

**Integrity.** `gl/guards.py` was unchanged after the freeze: its sha256 matches the freeze record, `d0d1e0d4…24f0`. No other frozen file was edited.

**Steps.**
1. The 2b pass ran on all 242 items.
2. The full frozen guard stack then flagged 148 model items, and each was re-asked once.
3. 3 re-asks passed every guard and replaced the original. 0 were skipped for budget, and no model output contained a digit.

**Spend** (tag `gl-70b-oos`): **$0.4955** of the $1.0 cap; 2b $0.31, re-ask $0.19.

**All rescue work, total: $1.9446**:

| Tag | Spend |
|---|---|
| fx-70b | $0.0614 |
| rp-70b | $0.3946 |
| wf-70b | $0.2973 |
| gl-70b | $0.5285 |
| gl-70b-guard | $0.1673 |
| gl-70b-oos | $0.4955 |
| gateway self-test | $0.0001 |

**Hand check.**
- All 46 unflagged non-exact outputs were read in full against DE old/new and the official FR/IT (`oos/handcheck_oos.tsv`). The 47 unflagged exact outputs need no reading.
- A seeded sample of 20 flagged outputs was also read (`oos/handcheck_flagged20.tsv`).
- Scorer: `oos/oos_score.py`. It uses `score2.score_one`, plus a paired cluster bootstrap over DE pairs.

## Results

| Measure | All 242 (121 DE changes, 55 families) | **Unseen families only (140 items, 40 families)** | Seen families (102 items, 15 families) |
|---|---|---|---|
| Exact, 70B pipeline | 71 = 29.3% | 36 = 25.7% | 35 = 34.3% |
| Exact, rules only | 35 = 14.5% | 6 = 4.3% | 29 = 28.4% |
| **Δ exact [95% CI]** | **+14.9 [+9.9, +20.7]** | **+21.4 [+13.6, +30.0]** | +5.9 [+1.0, +12.7] |
| Δ edit-F1 | +54.0 [+48.7, +59.1] | +59.7 [+53.4, +66.1] | +46.2 [+37.4, +54.5] |
| Δ chrF | +3.6 [+2.9, +4.3] | +4.2 [+3.3, +5.2] | +2.7 [+1.8, +3.8] |
| **Flag rate** | **149 = 61.6%** | **99 = 70.7%** | 50 = 49.0% |
| Exact outputs that were flagged anyway | 24 | 20 | 4 |
| Unflagged | 93: 47 exact, 26 equivalent, 7 cosmetic, 2 minor, **10 untranslated, 1 real** | 41: 16 exact, 9 equivalent, 3 cosmetic, 2 minor, **10 untranslated, 1 real** | 52: 31 exact, 17 equivalent, 4 cosmetic, **0 defects** |
| **Unflagged real errors per 100** | **0.41** (1) | **0.71** (1) | 0 |
| Unflagged stale per 100 | 0 | 0 | 0 |
| **Unflagged untranslated per 100** | **4.13** (10; Wilson 95% [2.3, 7.4]) | **7.14** (10) | 0 |
| Stale + untranslated per 100 | **4.13** | **7.14** | 0 |

**The unflagged defects.** All 11 are in families not seen in the 120.

- **Real error, all077-it:** "Prima di prescrivere INEGY **è** un'altra statina e, se questa non è tollerata, con 5–10 mg…". This drops "provare con", the obligation to try another statin first. G3c allows 3 × 1 + 1 removed content words, so the single removed word "provare" passes.
- **Untranslated (10):**
  - **5 FR items of one family (dac33b61):** the new heading "Immunthrombozytopenische Purpura (ITP) – Kinder ab 6 Jahren" becomes "Pour le traitement **de l'immunothrombozytopénie (ITP)** – Enfants à partir de 6 ans des patients pédiatriques…". That is a Germanised term with the German abbreviation, spliced into the first sentence. The official text is "Purpura thrombopénique auto-immun (PTI)".
  - all020-it: "**Folgendo Indikationscode** è da trasmettere…".
  - all085-it: "**Semaglutid pro settimana**".
  - all161-it: the DE hyphenation artefacts are imported: "dermatologi-**sche**", "me-thotrexato".
  - all023-fr/it: German/English abbreviations DME/RVO instead of OMD/OVR. These two are abbreviation-only. Without them the rate is 8/242 = 3.3%, which still fails.
- **Why G1 missed them.** None of these tokens is a German function word, carries an umlaut, or ends in -ung.

**Flagged sample (20, seed 20261009).**
- **9 were good:** 2 exact and 7 equivalent, i.e. false-flag waste of 45% [Wilson 26, 66].
- **11 needed a fix:**
  - 5 stale: output = old text, or a missing new heading;
  - 3 with German left in ("Asthma", "Folgender Code ist an den Krankenversicherer zu übermitteln", "x pro", "- dar - stellt") or EN/DE abbreviations;
  - 1 old indication kept;
  - **2 real**: all163-fr deletes the code-transmission sentence the DE keeps; all121-fr turns "doit" into "devrait", driven by the DE OCR typo "soIIte".
- Extrapolated, about 67 of the 149 flagged items need no change. Every exact item still in the flagged set (24) is pure review waste.

**Exploratory, post hoc (not part of the test).** A "token copied verbatim from the new DE" detector would catch 5 of the 10 untranslated items (all020-it, all023-fr/it, all085-it, all161-it). It misses the ITP hybrid term and the real error, and it wrongly flags 7 good items through product names (Zentiva, Mepha, Atozet, cabozantinib).

## Pass rule

| Criterion | Threshold | All 242 | Unseen families |
|---|---|---|---|
| Unflagged real errors | ≤ 1% | 0.41%: **pass** | 0.71%: **pass** |
| Unflagged stale + untranslated | ≤ 2% | **4.13%: FAIL** (CI lower bound 2.3%) | **7.14%: FAIL** |
| Exact ≥ rules-only + 5 | +5 | +14.9 [+9.9, +20.7]: **pass** | +21.4 [+13.6, +30.0]: **pass** |
| Flag rate | ≤ 70% | 61.6%: **pass** | **70.7%: FAIL** (marginally) |

## Verdict

**FAIL out of sample.** The frozen 70B whole-paragraph pipeline with guards v2 and one re-ask does not meet the pass rule on fresh items:
- unflagged untranslated output is 4.1% overall (7.1% on unseen families) against a 2% limit;
- on unseen families the flag rate is just over 70%.

The in-sample "0 / 0 / 0" from the guard follow-up did not transfer. Every unflagged defect is in a family the guards never saw.

What did transfer:
- The **quality gain is real and larger out of sample**: +14.9 exact overall and +21.4 on unseen families, with every CI well clear of +5.
- **Real errors stay rare:** 1/242 unflagged.
- **Stale changes are fully caught:** 0 unflagged.

So the 70B is a genuinely better drafter than rules plus the 8B. What fails is the guard layer. Untranslated detection by function words and morphology misses Germanised terms, German drug spellings, imported hyphenation artefacts and abbreviations. The flags carry about 45% waste.

**Gleichlaut 2B stays killed** under the agreed rule. Any revival needs a new untranslated guard designed on these 242 items, for example the copied-DE-token check combined with a terminology list (DME→OMD, ITP→PTI, INN spellings). That guard would then need yet another fresh set, such as the next monthly ePL snapshot, before any claim could be made.

---


# Last round: guard v2 (`g3/guards3.py`) and a fresh 2025 test set (9 Oct 2026)

## Guard v2: design on the 242 out-of-sample outputs (now the dev set)

**Structure.** `g3/guards3.py` wraps the frozen `gl/guards.py` stack (V2 = True) and adds three untranslated detectors:

| Guard | Rule |
|---|---|
| **G5 copied-from-DE** | A token the output adds (compared with the old FR/IT text, case-insensitive) that also occurs in the new DE text, is **not** on the target-language whitelist, and occurs in fewer than 5 target-language limitation texts |
| **G6 terminology** | The output adds a DE abbreviation A for which the mined DE→FR/IT map gives B ≠ A |
| **G7 out-of-vocabulary** | The output adds a word of ≥ 4 letters that appears in no target-language limitation text, is not whitelisted, and is not in the old text |

**Resources** (`g3/build_resources.py`, fully mechanical):

| Resource | Source |
|---|---|
| Whitelist | Target-language `productName` entries, Ingredient substance names (Latin INNs) and target-language ATC display names from the current BAG ePL FHIR feed. FR 5,613 tokens; IT 5,637 |
| Vocabulary | Token → number of FR (or IT) limitation texts in the **1 Jun 2025** XMLPublications capture. That capture predates every new text in both the dev and the fresh set, so no gold text leaks in |
| Terminology map | Mined from the 1,319 aligned DE/FR/IT limitation triples of the same capture: abbreviations in DE only vs target only, paired by order when the counts match. Kept if support ≥ 2, ≥ 60% dominant, and A used in < 5 target texts. FR: 68 pairs, e.g. DME→OMD, ITP→PTI, AMD→DMLA, CLL→LLC, COPD→BPCO. IT: 30 pairs, e.g. ITP→PTI, CLL→LLC, NSAID→FANS. RVO→OVR is not minable: RVO is absent from the FR texts and used in 5 IT texts |

**Dev results** (cached outputs, `g3/eval_dev.py`):

| Set | Flag rate before → after | Defects newly caught | False flags |
|---|---|---|---|
| Dev, 242 out-of-sample outputs | 61.6% → **67.4%** | **9/10 untranslated**: all020-it, all023-fr, all085-it, the 5 ITP FR items, all161-it | 5 equivalent items, all non-SL wording: "codice indicativo" ×4, the typo "rivascularizzazione" |
| Original 120 | 67.5% → 71.7% | — | 4 equivalent items, 1 minor item |

**Still unflagged on dev.**
- **all023-it (RVO):** by the June 2025 IT corpus, RVO is established IT SL usage (5 texts; OVR in 0), so that dev label was arguably too strict.
- **The real error all077-it:** one verb phrase dropped. Not targeted by this round.

## Fresh test set: 2025 Wayback captures (`fresh/build_fresh.py`, `fresh/items_fresh.json`)

**Sources.**
- XMLPublications releases 01.06.2025 and 01.07.2025: Wayback captures of 2025-06-11 and 2025-07-31, `Preparations.xml`. Each `<Limitation>` carries DE/FR/IT side by side.
- The ePL FHIR snapshot of 19 Feb 2026, the earliest 2026 snapshot.

**Pairs mined.**
- Jun → Jul 2025 yields only 7 usable DE changes.
- Jul 2025 → Feb 2026 is therefore added, with products matched by unique DE product name (6,281 matched).

**Same rules as S2.**
- Per-product greedy pairing; ≤ 60% of tokens changed; DE ≤ 2,500 characters; target missing or unchanged excluded.
- '<' pairs dropped where the Feb 2026 old-format FHIR export is involved.

**Emulating the FHIR exporter on the XML side.** Without this, 75% of unchanged texts look changed.
- HTML block tags become a space; inline tags are dropped, so `m<sup>2</sup>` → "m2".
- Square brackets are dropped.
- Pairs whose DE, or whose FR/IT, differ only in punctuation or spacing are excluded as export artefacts. That removes 69 DE pairs (7 Jun→Jul, 62 Jul→Feb), e.g. "[auf IGA Skala]", a trailing "." after the code, "m 2".
- After this, 3,394/3,871 Jul 2025 texts reappear unchanged in Feb 2026.

**Result.** **166 FR/IT items** (83 FR + 83 IT) from 83 DE changes in 55 families: 12 items Jun→Jul 2025 and 154 Jul 2025→Feb 2026.

**Family overlap with everything used so far** (the 2026 pool of 362 = the 120 + the 242):
- 3 of the 55 families, covering 12 items, were seen before; 2 of those items fall in families of the original 120.
- **154 items (52 families) are in families never seen.**

## Freeze record (written before any fresh output existed; `fresh/` held no outputs and the `gl-70b-v2` tag had $0 spend)

| File | sha256 |
|---|---|
| `g3/guards3.py` | `113aa7a12d6c9406bbac193d7b5946dd6d7ae56e805a5fbc03f3fbd467f6fdfd` |
| `g3/whitelist_fr.json` | `ea60777e147b2cc847d7ffe058496685e9474a292a8fa99a170e89386f7bc425` |
| `g3/whitelist_it.json` | `8160299dedf70fdcdffa336329568298edcd362cfcb62cabf962ac69b6167e5f` |
| `g3/vocab_fr.json` | `869f28c6caaf5d7cbb70f07ea601f4c0df0a697d76c4001aed29b7e6d1da5e72` |
| `g3/vocab_it.json` | `8286a7ef52d379a868a2ea3d869d5e89e2b6275ed274c43181e88d559cec1c2d` |
| `g3/terms_fr.json` | `4ee58c230d0c03f5d8753f33e9aabacb96dbf74b37ac2291a3e79b602c3ec993` |
| `g3/terms_it.json` | `cad76b00259a70cbf8469a8ee0a1b43e1d4799d29db954fccafa5e7002a38a57` |
| `gl/guards.py` (unchanged since the first freeze) | `d0d1e0d47e3828bf127e05572e055391a6eba9f9e89108b4c09e67a7fd1524f0` |
| `gl/gl70.py` | `f2a207787b2ee024f67959ba5ba3001c7da44907effc50ec3e1d5fa8940ad3b8` |
| `gl/reask.py` | `5b30a30a170117a9cc27baaeb6cf04395bf097c3475cb00d1db4e68286f84920` |
| `fresh/run_v2.py` | `d5460bba8d10ed5d47c78941b7035631e4f8e0572845a6d984d698afb22139ab` |
| `fresh/items_fresh.json` | `157ca97a6ccf207e3f570e66a79b4da543cab69f3bb88b01da5bc741a5df9b02` |
| `common.py` | `0ae44b4e6ba6e7fecc2d36d671a4afd5c7c6e5a60a062521339c63bdeac7c753` |
| `gleichlaut/s2/lock.py` | `1409b2ad5f5acc68bc9ace45620f86131681ec6e33d9d30d62b3ad0141f9c29f` |
| `gleichlaut/s2/gl2.py` | `08aefe04a102e13fe7d37fad2b05a47b23a96b8952a35b7e0341bba47d2f297c` |

**Pipeline.** `fresh/run_v2.py` runs `gl70.run_2b`, then `reask.py`. Substitutions: tag `gl-70b-v2`, cap $1.0, `import guards` → `guards3`, a budget refusal counts as "not re-asked", and paths.

**Pass rule.**
- Unflagged real errors ≤ 1%.
- Unflagged stale + untranslated ≤ 2%.
- Exact ≥ rules-only + 5 points.
- Flag rate ≤ 70%.

## Run on the fresh set

**Integrity.** After the run, every frozen file still matches its sha256 in the freeze record.

**Steps.**
1. The 2b pass ran on all 166 items.
2. guards3 flagged 98 model items, and each was re-asked once.
3. 3 re-asks passed every guard. 0 were skipped for budget, and no model output contained a digit.

**Spend** (tag `gl-70b-v2`): **$0.4609** of the $1.0 cap; 2b $0.27, re-ask $0.19.

**All rescue work, total: $2.4055** of the $3 budget:

| Tag | Spend |
|---|---|
| fx-70b | $0.0614 |
| rp-70b | $0.3946 |
| wf-70b | $0.2973 |
| gl-70b | $0.5285 |
| gl-70b-guard | $0.1673 |
| gl-70b-oos | $0.4955 |
| gl-70b-v2 | $0.4609 |
| gateway self-test | $0.0001 |

**Hand check.**
- All 49 unflagged non-exact outputs were read in full against DE old/new and the official FR/IT (`fresh/handcheck_fresh.tsv`). The 17 unflagged exact outputs need no reading.
- A seeded sample of 20 flagged outputs was also read (`fresh/handcheck_flagged20.tsv`).
- Scorer: `fresh/score_fresh.py`, the same as the earlier out-of-sample scorer.

| Measure | All 166 (83 DE changes, 55 families) | **Unseen families (154 items, 52 families)** | Excluding the largest family 981f07a8 (132 items, 54 families) |
|---|---|---|---|
| Exact, 70B pipeline vs rules only | 29 vs 10: 17.5% vs 6.0% | 24 vs 5: 15.6% vs 3.2% | 29 vs 10 |
| **Δ exact [95% CI]** | **+11.4 [+4.8, +18.7]** | **+12.3 [+5.8, +20.1]** | +14.4 [+6.8, +22.7] |
| Δ edit-F1 | +54.1 [+46.8, +61.2] | +56.2 [+48.8, +63.3] | — |
| Δ chrF | +6.8 [+5.4, +8.2] | +7.1 [+5.7, +8.5] | — |
| **Flag rate** | **100 = 60.2%** | **93 = 60.4%** | **100 = 75.8%** |
| Exact outputs that were flagged anyway | 12 | 10 | — |
| Unflagged outputs | 66: 17 exact, 48 equivalent, 1 pre-existing | 61: 14 exact, 47 equivalent | 32 |
| **Unflagged real errors per 100** | **0** (Wilson upper bound 2.3) | **0** (upper bound 2.4) | 0 |
| **Unflagged stale + untranslated per 100** | **0** | **0** | 0 |

**What the unflagged outputs are.**
- **48 equivalent.** The output applies exactly the DE change. Where the gold differs, the official FR/IT also fixed pre-existing discrepancies the DE never touched. Examples: "inhibiteur de l'enzyme de conversion" → "antagoniste des récepteurs" across the Grundversicherung family; "indiqué" → "remboursé" in VENCLYXTO; a product-name typo; "cassa malati" → "assicuratore malattia".
- **1 pre-existing case (wb079-it).** The old IT slot already contained French ("Prix de facturation par application et patient …"). The output applies the DE price change correctly; only the gold also fixes the French. Counted strictly as untranslated it would be 1/166 = 0.6%, which still passes.
- **Concentration.** 34 of the 66 unflagged outputs come from one boilerplate family (981f07a8: "Grundversicherung" → "obligatorischen Krankenpflegeversicherung", 17 DE changes × FR/IT). The other 32 cover 17 families.

**Flagged sample (20, seed 20261009).**
- **13 needed no change:** 4 exact and 9 equivalent, i.e. false-flag waste of 65% [Wilson 43, 82].
  - G7 contributes waste on ordinary words absent from the SL corpus: "glutine", "latticini", "oftalmochirurghi", "uniforme".
- **7 needed a fix:**
  - wb013-it: German left in;
  - wb010-fr, wb011-fr, wb057-fr: stale;
  - **3 real meaning changes, all caught:** wb047-fr and wb045-fr change "et" to "ou", which the DE does not; wb060-it also changes a second "del trattamento" that the DE leaves.

## Pass rule

| Criterion | Threshold | All 166 | Unseen families | Excluding the dominant family |
|---|---|---|---|---|
| Unflagged real errors | ≤ 1% | 0%: **pass** (upper CI bound 2.3) | 0%: **pass** | 0%: pass |
| Unflagged stale + untranslated | ≤ 2% | 0% (0.6% counting the pre-existing case): **pass** | 0%: **pass** | 0%: pass |
| Exact ≥ rules-only + 5 | +5 | +11.4: **pass** (CI lower bound 4.8) | +12.3 [+5.8, +20.1]: **pass** | +14.4: pass |
| Flag rate | ≤ 70% | 60.2%: **pass** | 60.4%: **pass** | **75.8%: fail** |

## Final verdict for Gleichlaut-70B

**PASS under the agreed rule, but narrow and fragile.** On a fresh set mined from 2025 data, with 154/166 items in families never seen before and the guard and all its resources frozen before any output existed, the 70B whole-paragraph pipeline with guard v2 (guards3) and one re-ask meets all four criteria:
- **0 unflagged real errors, 0 stale and 0 untranslated** in 166;
- exact +11.4 over rules-only;
- a 60.2% flag rate.

The same holds on unseen families alone.

**Caveats that belong in any claim.**

1. **Concentration.** Half the unflagged outputs are one boilerplate family. Without that family, the pipeline still leaks nothing (0/32), but the flag rate is 75.8%, so translators would review three quarters of the items.
2. **Zero errors is a point estimate.** The Wilson upper bound for 0/166 is 2.3%, so the data cannot demonstrate a true unflagged error rate ≤ 1% with 95% confidence. The exact gain's CI lower bound is 4.8, just under +5.
3. **Flags are noisy.** About 65% of flagged items need no change. 12 exact outputs are flagged, and the out-of-vocabulary guard flags ordinary FR/IT words absent from the SL corpus.
4. **Dropped-word meaning errors are still caught only incidentally.**
   - On dev, all077-it (dropping "provare con") went unflagged.
   - Here the three meaning changes in the sample ("et"→"ou", an extra replacement) were flagged by other guards, not by a check designed for them.
   - A 166-item sample cannot rule out that class at the 1% level.

**What this supports.** A 2B claim of the form: *the 70B drafts the FR/IT amendment; deterministic guards pass about 40% of items as ready, with no unflagged errors found in 166 fresh items; translators review the flagged 60%, about two thirds of which need no change.* It does not support "the model writes the amendment and humans rarely look".

Gleichlaut-70B is the only 2B card that survives the rescue round, and only in this guarded, review-heavy form.
