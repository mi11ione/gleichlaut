# Research record (verbatim): Gleichlaut S1 census, S2 window arm, S2b 8B

Copied from the research log `spikes/gleichlaut/results.md` (not part of this repository; sha256 of the full file when copied: `a034334ef11722271b74d420da0b7d9769fe9e192a1414d17e25775ae095b84d`).

---

# Gleichlaut S1: census of DE/FR/IT limitation texts (no model)

Run 9 Oct 2026 on the M4 (macdonalds.local), stdlib Python only, no LLM. All downloads used User-Agent `hackapertus-research/0.1`. Nothing ran on the M2 Air.

## Verdict

**The kill rule fires: drop the census beat.**

- Precision on a random 50-flag hand check is **6%** (3/50), Wilson 95% CI [2.1%, 16.2%]. That is far under the 30% bar.
- Counting minor discrepancies too, it is 10% (5/50), CI [4.3%, 21.4%].
- The sample has **3** confirmed discrepancies, against a bar of 10.
- A targeted sweep outside the sample brings the total to **10 confirmed discrepancies at limitation level**, which just reaches the bar. They come from only **5 independent errors**, because three are copied across etanercept biosimilars and four sit in Dupixent's weight tiers.

Real cross-language discrepancies exist, and some matter (a dosing interval, a price surcharge, weight thresholds). But a deterministic lexical census cannot find them with usable precision. Out of every 10 flags, about 8 are parser noise and 1 is formatting. So "N limitations disagree" cannot be put on screen with a defensible number.

A single hand-verified example could still open the video. That is a different beat from the census, and choosing it is a scoping decision for you.

**S3 availability: yes, with a caveat.** The official ePL keeps dated snapshots in DE/FR/IT for **9 months, Feb to Oct 2026**. There is nothing official for 2024 or 2025. The Wayback Machine holds only 2 captures of `XMLPublications.zip` in 2024–26 (Jun and Jul 2025). Details are under S3 below.

## Data

| What | Value |
|---|---|
| Source | BAG ePL FHIR NDJSON publication, `https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-latest-{de,fr,it}.ndjson` |
| Version | last-modified 5 Oct 2026 22:11 GMT; same size as the dated file `foph-sl-publication-20261006-*` |
| SHA-256 (de) | 9eec089d… |
| SHA-256 (fr) | 1de4a003… |
| SHA-256 (it) | 7f593c22… |
| Size | 6,749 bundles per language |
| Limitations | 5,010 ClinicalUseDefinition entries, **1,688 unique CUD ids** |
| Alignment | every id is present in all 3 languages; none left unaligned (alignment by CUD id is free, as the card said) |
| Distinct text triples | 1,624 |

- Every limitation is a CUD. The RegulatedAuthorization only points to it (`limitationIndication`); no limitation text sits elsewhere.
- The old `www.spezialitaetenliste.ch/File.axd?file=XMLPublications.zip` now 301-redirects to the sl.bag.admin.ch SPA, which serves HTML instead of a zip. ePL is the only live official source.
- The texts are flattened. Bullets survive only as inline `•`, `-` or `a)` characters, so list-item counts are unreliable by construction.

## Method

`scripts/census.py` extracts five kinds of facts per language and compares them across the three versions of each CUD:

- **NUM.** Numeric values: digits, cardinal and ordinal number words, and dates. "One" counts only next to a strong operator or a quantity or time unit.
- **UNIT.** The unit class attached to a value.
- **OP.** Operator classes GE, GT, LE and LT, anchored before or after a number:
  - range defaults apply;
  - a nearby verbal negation flips the operator ("n'ont pas reçu plus de" becomes LE);
  - OP means a conflict between two explicit operators; OPMISS means an operator in one language and none in another.
- **NEG.** Negation counts, with doubled negation collapsed and lexical negations counted. A flag needs a difference of at least 2, or 0 in one language against at least 1 in another.
- **ITEMS.** Counts of list items.
- **LANG.** A stop-word check that each language slot is in that language.

Tuning and evaluation were kept apart:

- The parser was tuned by reading flags from the **dev half** (CUD ids with even md5), then frozen (`census.py` sha1 `f0cb3006…`).
- OPMISS was left out of the census set before sampling, because on dev it was mostly lexicon gaps.
- `scripts/sample.py` then drew **50 flags uniformly from the held-out half** (odd md5; pool 328 flags; seed 20261009).
- I (Claude) did the hand check by reading the full DE/FR/IT texts, not just the snippets. It was not done by a model run inside the pipeline.

Each flag was labelled:
- **real**: the languages state different conditions;
- **real-minor**: a shift in a quantifier or nuance;
- **format**: a typo or formatting difference with the same condition;
- **noise**: a parser artefact.

## Census numbers (full feed, 1,688 CUDs)

| Category | Flags | CUDs flagged |
|---|---|---|
| NUM | 202 | 171 |
| OP | 174 | 124 |
| NEG | 208 | 208 |
| ITEMS | 55 | 55 |
| UNIT | 7 | 7 |
| LANG | 1 | 1 |
| **Census set (all of the above)** | **647** | — |
| OPMISS (excluded, not checked) | 370 | 285 |

Deduplicating by text triple barely changes the census set: 647 → 635.

## Hand check (50 flags, held-out half)

| Label | n |
|---|---|
| real | 3 |
| real-minor | 2 |
| format | 5 |
| noise | 40 |

| Category | n | Breakdown | Strict precision (Wilson 95% CI) |
|---|---|---|---|
| NUM | 15 | 3 real, 1 minor, 4 format, 7 noise | 20% [7%, 45%] |
| OP | 10 | 0 real, 1 format, 9 noise | 0% [0%, 28%] |
| NEG | 22 | 0 real, 1 minor, 21 noise | 0% [0%, 15%] |
| ITEMS | 3 | 3 noise | — |

Per-flag labels are in `out/handcheck50.tsv`.

**Where the noise comes from**, so that S2's guard can learn from it:

- **Organ-failure words.** "insuffisance / insufficienza" was counted as a negation.
- **Lexical negation gaps.** For example: Intoleranz, Versagen, inadéquat, en l'absence de, in mancanza di, therapienaiv.
- **Digits glued to other characters.** Examples: `v1.1`, `/40 ml`, `semaine,3 mg`, `12/24/36`.
- **Unit conversions across languages.** "14 Tage" = "deux semaines"; "alle 2 Monate" = "bimestrale".
- **Articles read as "one".** For example "einer Dosierung", "une dose".
- **IT "a seconda di"** ("depending on") read as an ordinal.
- **Equivalent operator phrasings.** For example "nicht mindestens X erreichen" vs "ancora inferiore a X", "über 75" vs "plus de 75", "gleich viel oder mehr als" vs "ou plus".
- **Generic copies.** The same statin limitation repeated across many generics accounts for 6 of the 10 OP flags.

**NUM is the only category with signal**, and even its point estimate (20%) is under 30%. A NUM-only v2 that fixes the noise classes above might pass, but that is untested and post hoc.

## Targeted sweep (outside the precision sample)

This sweep only counts discrepancies. It does not feed the precision estimate.

- **Scope.** `scripts/sweep.py` took every NUM flag in both halves where a digit carries a unit, deduplicated by text triple: 25 flags. Each was checked against the full texts; labels are in `out/sweep25.tsv`.
- **Result.** 12 of the 25 were real.
- **New limitations.** Those 12 cover 7 limitations not already in the sample: BENEPALI4, ERELZI2, CRESE.Kps.IM, DUPIXENT.02, DUPIXENT.02P, DUPIXENT.05a and DUPIXENT.05P.
- **Total.** With the 3 from the sample, that makes **10 confirmed real discrepancies at limitation level**.

## The 10 clearest examples

All snippets are verbatim and shortened with "…".

1. **Nemluvio (nemolizumab), `NEMLUVIO.01`.** The maintenance interval differs.
   - DE: "…in einer Erhaltungsdosis von 30 mg als subkutane Injektion alle **acht** Wochen…"
   - FR: "…d'une dose d'entretien de 30 mg … toutes les **huit** semaines…"
   - IT: "…in una dose di mantenimento di 30 mg come iniezione sottocutanea ogni **quattro** settimane…"
2. **Diaphin (diacetylmorphine), `DIAPHIN.6-`.** The price surcharge differs.
   - DE: "…zuzüglich dem preisbezogenen Zuschlag von **6%** zuzüglich MWST."
   - FR: "…plus la prime relative au prix de **6%**, TVA en sus."
   - IT: "…più il supplemento attinente al prezzo di **12%** più la IVA."
3. **Nepexto (etanercept), `NEPEXTO`.** The French adds a weight restriction to the juvenile arthritis indication.
   - DE: "…der aktiven juvenilen chronischen Arthritis mit polyartikulärem Verlauf und Psoriasis Arthritis, wenn…" (no weight condition)
   - FR: "…de l'arthrite chronique juvénile polyarticulaire active **chez les patients pesant ≥ 62.5 kg** et de l'arthrite psoriasique…"
   - IT: "…dell'artrite giovanile poliarticolare idiopatica e dell'artrite psoriasica…" (no weight condition)
4. **Benepali (etanercept), `BENEPALI4`.** Same French-only "≥ 62.5 kg" clause, in the same position.
5. **Erelzi (etanercept), `ERELZI2`.** Same again. The error has propagated across three biosimilars.
6. **Cresemba (isavuconazole) capsules, `CRESE.Kps.IM`.** The French drops the minimum body weight.
   - DE: "…pädiatrischen Patienten ab dem Alter von 6 Jahren und mit einem Körpergewicht von **mindestens 16 kg** vergütet."
   - FR: "…chez les adultes et les patients pédiatriques à partir de 6 ans." (no weight condition)
   - IT: "…pazienti pediatrici a partire dai 6 anni di età e con un peso corporeo di **almeno 16 kg**."
7. **Dupixent, adolescent atopic dermatitis, `DUPIXENT.02P`.** The French has no 15–30 kg tier, and its boundary at 60 kg differs.
   - DE: "…Körpergewicht **ab 60 kg** … ab 30 kg bis unter 60 kg … und bei Patienten mit einem Körpergewicht **ab 15 kg bis unter 30 kg** in einer Anfangsdosis von 600 mg…"
   - FR: "…pesant **plus de 60 kg** … et pour les patients pesant **moins de 60 kg** à une dose initiale de 400 mg…" (no 15–30 kg tier)
   - IT: "…superiore a 60 kg … da 30 kg a meno di 60 kg … **da 15 kg a meno di 30 kg**, alla dose iniziale di 600 mg…"
8. **Dupixent, `DUPIXENT.02`.** Identical discrepancy in the sibling CUD.
9. **Dupixent, pediatric asthma 6–11 years, `DUPIXENT.05a`.** The French lower bound is 30 kg instead of 15 kg, and the French uses ">60" against "≥60".
   - DE: "…300 mg alle 4 Wochen bei einem Körpergewicht von **15 - < 60 kg**, bzw. von 200 mg alle 2 Wochen bei einem Körpergewicht **ab 60 kg**…"
   - FR: "…300 mg toutes les 4 semaines pour un poids corporel de **30 kg à moins de 60 kg**, ou de 200 mg … **supérieur à 60 kg**…"
   - IT: "…300 mg ogni 4 settimane per un peso corporeo di **15 - < 60 kg**, o di 200 mg … di **60 kg o più**…"
10. **Dupixent, `DUPIXENT.05P`.** Identical to example 9.

**Other findings**, not counted among the 10:

- **Wrong-language slot.** In `KEYTRUDA.07---Inj-L-s---Urothelkarzinom--Monotherapie--KN045`, the Italian text is the French text: "Carcinome urothélial (monothérapie) KN045 (avec modèle de prix)…". The only LANG flag in the feed.
- **Boundary at 60 kg.** `DUPIXENT.03a` and `.03P` have DE "ab 60 kg", FR "plus de 60 kg" and "entre 30 kg et 60 kg", IT "da 60 kg". These are real-minor.
- **Quantifier.** `JORVEZA.Erh2`: DE "<15 … pro **mindestens einem** High-Power Field"; FR and IT say per HPF.
- **Nuance.** `DECADURABOL2`: IT "si siano rivelate inefficaci" against DE/FR "ausgeschöpft / épuisées".
- **Typos.** IT "pari e superiore" (`SYMDEKO-01`), IT "almeno se mesi" (`FORSTEO-2`), FR "de15 kg" (`PREVYMIS.01`).

What this means for the card:

- **Copying spreads errors.** Biosimilars and sibling CUDs copy limitation text. The "closest existing limitation" base text in step 2 of the mechanism is how real SL drafting works, but it carries errors forward. S2 should expect the official FR/IT gold to fail the lock now and then (the gold ceiling).
- **The digit-ban story is sound.** Every real discrepancy is a number or a threshold.
- **A guard needs more than counting markers.** Raw negation counts are useless as a cross-language guard (0/22). The guard in step 6 of the mechanism needs a structured comparison of negation, or should drop negation counting.

## S3: history snapshots

**Official ePL dated files.** Same path pattern as above.

- Through Aug 2026: `https://epl.bag.admin.ch/static/fhir/foph-sl-export-YYYYMMDD-{de,fr,it}.ndjson`
- From 25 Aug 2026: `https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-YYYYMMDD-{de,fr,it}.ndjson`

I scanned every day from 1 Oct 2025 to 9 Oct 2026 by HEAD request on DE. Dates that exist:

| Month | Dates (dd.mm.yyyy) | Path |
|---|---|---|
| Feb 2026 | 19.02 | old |
| Mar 2026 | 04.03 | old |
| Apr 2026 | 01.04 | old |
| May 2026 | 04.05, 05.05 | old |
| Jun 2026 | 01.06 | old |
| Jul 2026 | 01.07, 03.07, 31.07 | old |
| Aug 2026 | 01.08, 07.08, 13.08 | old |
| Aug 2026 | 25.08 | new |
| Sep 2026 | 01.09 | new |
| Oct 2026 | 01.10, 06.10 | new |

- That is **9 distinct months, Feb to Oct 2026**. FR and IT were confirmed with 200 responses for every first-of-month date, and for 19.02, 04.03 and 04.05.
- The Feb and Mar files carry last-modified 9 Apr 2026, so they were back-filled.
- Nothing exists on the 1st of any month in 2024 or 2025, on either path.

**Wayback Machine, `XMLPublications.zip`.** Within 2024–26 there are only 2 captures, both 200 and both downloadable:

- https://web.archive.org/web/20250611143650id_/https://www.spezialitaetenliste.ch/File.axd?file=XMLPublications.zip (11.3 MB)
- https://web.archive.org/web/20250731143731id_/https://spezialitaetenliste.ch/File.axd?file=XMLPublications.zip (11.4 MB)

There are also older captures from 2014–2022. `Publications.xlsx` has captures from 2025-06 and 2025-07, and `Publications_Next.xlsx` from 2025-07 and 2025-11. I did not check whether they contain limitation texts. sl.bag.admin.ch and epl.bag.admin.ch have no useful captures.

**Answer: yes, ≥6 monthly snapshots are recoverable (9), all from 2026 and from the official ePL source.** None of them were downloaded. Before S3 uses them, check how many CUDs actually change between months.

## Files

| Path | Contents |
|---|---|
| `scripts/census.py` | extraction and flagging (frozen) |
| `scripts/sample.py` | draws the 50 held-out flags |
| `scripts/score.py` | hand-check labels, flag table, Wilson CIs |
| `scripts/sweep.py` | targeted NUM sweep |
| `scripts/show.py` | text viewer |
| `out/flags.tsv` | all 1,017 flags (`flags.jsonl` has the same with evidence snippets) |
| `out/handcheck50.tsv` | the 50 labelled flags |
| `out/sweep25.tsv` | the 25 labelled sweep flags |
| `out/census_summary.json`, `out/handcheck_summary.json` | summary numbers |
| `out/texts.json` | aligned DE/FR/IT texts per CUD |
| `data/sl-{de,fr,it}.ndjson` | raw feed, public BAG data, about 280 MB; no personal data |

---

# Gleichlaut S2: does the locked, digit-banned 8B add value over rules-only? (real ePL version history)

Prepared on the M4 9 Oct 2026; model run on the M2 Air through `gpu.sh` (09:29–11:16, 6,437 s, Apertus v1.5 8B text MLX 4-bit DWQ, greedy, thinking off). The Air ran byte-identical copies of `s2/s2.py`, `s2/gl2.py`, `s2/items.json` (sha1 checked). No other GPU jobs were started.

## Verdict

**KILL. Both kill rules fire.**

| Rule | Threshold | Measured | Result |
|---|---|---|---|
| Locked 8B − rules-only, exact | ≥ +5 points | **+0.0** (7/120 vs 7/120; the same 7 items, all solved by code before the model is called). Model-touched items: 0/113 vs 0/113 | **fires** |
| Locked 8B − rules-only, edit-F1 | ≥ +5 points | +15.3, paired cluster-bootstrap 95% CI [+10.8, +20.0] | passes, but hollow (below) |
| Unflagged real meaning errors, arm 2 | ≤ 1/120 | **6/120** (plus 7 unflagged items where the change was silently not applied) | **fires** |

The edit-F1 gain does not reflect usable output. Arm 2 output is *further* from the official text than doing nothing (chrF 84.5 vs 88.8 for rules-only), the free 8B scores higher edit-F1 (28.2), and 82% of arm-2 items are flagged.

**Why it failed: the 8B does not respect the window.** It was asked to output only the replacement for a ⟦marked⟧ span. In 165/226 windows (73%) it returned far more than the span (length > old window + 1.5× the DE insertion + 30 chars); in 81 windows it restarted from text before the window, usually from the start of the paragraph. Code then stitched that into the window, which duplicates whole clauses. The digit ban itself worked (0 digits generated). So this kills *window-only generation by instruction*; it does not test constrained decoding (forced copy outside the window, or the Gleichschritt S1 design of "rewrite the paragraph, then lock-check", which reached 25% exact on non-rule Fedlex items). That would need a new spike.

## Gold: real version history (preference (a) met)

- **Source.** All 9 official ePL FHIR monthly snapshots (19.02, 04.03, 01.04, 04.05, 01.06, 01.07, 01.08, 01.09, 01.10) plus the local 06.10 feed, DE/FR/IT. Streamed (≈2.5 GB transferred), only the extracted limitation texts kept (`data/hist/`, 88 MB). `s2/extract.py` reads both formats: old (Feb–May, `limitationText` inside RegulatedAuthorization) and new (ClinicalUseDefinition).
- **Ids are not stable.** A changed limitation usually gets a new CUD id (`ABEVMY.01` → `ABEVMY.01a---Kolorektalkarzinom`; Jul→Aug: 0 in-place changes, 100 new, 53 gone). Changes are therefore paired per product (MedicinalProductDefinition id, stable across snapshots): texts gone from month A and new in month B, greedily matched by token similarity, ≤60% tokens changed (`s2/mine.py`).
- **Old-format RA ids differ per language file.** FR/IT are aligned by (product, position); verified on DE-unchanged limitations Apr→Jun: identical FR 5498/5504, IT 5502/5504.
- **Publisher bug: '<…>' spans are dropped** in the 04.05 snapshot and in all old-format files (e.g. "LDL-Zielwert < 1.8 mmol/l …" is missing; restored in June). Without a filter ~80 fake "changes" enter the gold. 04.05 is excluded (Apr→Jun diffed directly) and every old-format pair containing '<' is dropped.
- **Pool.** 216 distinct real DE changes → 181 eligible (30 longer than 2,500 chars, 5 where DE changed but FR/IT did not). About 100 matched pairs rewrote >60% of tokens and are outside the pool (the 70B-lane share). The 181 fall into 100 *edit families* (identical token edit with digits masked; the largest is the SL-wide boilerplate "Folgender Code … : 21658.01" → "Der Indikationscode dieser Limitierung …"). **60 DE changes from 60 different families**, seeded, → 120 FR/IT items (`s2/items.json`, `s2/pool_stats.json`). Transitions: Feb→Mar 5, Mar→Apr 4, Apr→Jun 9, Jun→Jul 15, Jul→Aug 17, Aug→Sep 5, Sep→Oct 5.
- **Gold ceiling** (official new FR/IT passes the Gleichschritt lock): **90/120 = 75%** (FR 45/60, IT 45/60); 299/362 = 83% on the full eligible pool.

## Arms (same 120 items)

1. **Rules only** (`gl2.rules`): copy old FR/IT; apply number, month and ALL-CAPS-name substitutions read off the DE diff wherever they land unambiguously.
2. **Locked 8B** (`gl2.plan` + `s2.py run_2`): rule ops applied by code; every other DE op mapped to its lock window (`lock.windows`, unchanged from Gleichschritt), overlapping windows merged; the 8B writes only each window's replacement, right to left. Every number (digits, and DE/FR/IT number words 2–12) is shown as a slot code ⟨A⟩; a logit mask forbids all 1,008 digit tokens plus whole-word FR/IT number words; code writes values back and stitches. 7 items needed no model (rule-only); 113 items, 226 windows went to the model.
3. **Free 8B**: translate the new DE from scratch, no lock, no mask.

## Results

| Lang | Arm | n | exact | edit-F1 | chrF | lock OK | flagged | lexicon flip hits | unflagged hits | numbers not in DE (occurrences / items) | s/item |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FR | 1 rules | 60 | 6.7% | 8.0 | 89.0 | 97% | 53% | 34 | 2 | 22 / 18 | 0 |
| FR | 2 locked 8B | 60 | 6.7% | 21.7 | 83.8 | 53% | 87% | 43 | 0 | 8 / 6 | 33.2 |
| FR | 3 free 8B | 60 | 0.0% | 28.3 | 70.9 | 0% | — | 44 | 44 | 2 / 2 | 19.8 |
| IT | 1 rules | 60 | 5.0% | 6.2 | 88.6 | 98% | 55% | 35 | 2 | 24 / 19 | 0 |
| IT | 2 locked 8B | 60 | 5.0% | 23.1 | 85.2 | 55% | 77% | 43 | 3 | 13 / 8 | 33.9 |
| IT | 3 free 8B | 60 | 0.0% | 28.1 | 71.5 | 2% | — | 34 | 34 | 1 / 1 | 20.4 |
| FR+IT | 1 rules | 120 | **5.8%** | 7.1 | 88.8 | 98% | 54% | 69 | 4 | 46 / 37 | 0 |
| FR+IT | 2 locked 8B | 120 | **5.8%** | 22.4 | 84.5 | 54% | 82% | 86 | 3 | 21 / 14 | 33.5 |
| FR+IT | 3 free 8B | 120 | **0.0%** | 28.2 | 71.2 | 1% | — | 78 | 78 | 3 / 3 | 20.1 |
| FR+IT | official gold | 120 | 100% | 100 | 100 | 75% | — | — | — | 3 / 3 | — |
| model-touched | 1 rules | 113 | 0.0% | 1.3 | 88.1 | | | | | | |
| model-touched | 2 locked 8B | 113 | 0.0% | 17.6 | 83.5 | | 85% | | | | 35.6 |
| model-touched | 3 free 8B | 113 | 0.0% | 29.7 | 71.3 | | | | | | 20.0 |

Definitions as in Gleichschritt (`s2/score2.py`): exact after whitespace/apostrophe normalisation; edit-F1 = token edits old→output vs old→official; flagged (arm 2) = lock fails, slot guard fires, or an unknown slot code is left; arm 1 flagged = guard only; arm 3 has no guard. Rules-only on the full 181-pair pool: 42/362 = 11.6% exact.

**Numbers not in the DE.**
- Arm 2: **0 digits generated by the model** (0/226 raw generations contain a digit). The 21 occurrences (14 items) are all re-emitted via slot codes: 15 values are *old* numbers still in the old FR/IT that the DE removed or changed (e.g. the old prices 121.87, 174.92/349.84, old indication codes) because the slot table also listed old values; 1 is a stitching artefact (window began between "2" and "L" in "2L NSCLC", the model repeated the slot → "22L"). The ban stops invented digits; it does not stop the model placing a *wrong DE/old* number: in 34-fr/it it wrote "Au maximum ⟨56⟩ mg de carfilzomib/m2" where the DE deleted the dose sentence (56 occurs elsewhere in the DE; guard caught it). One number-word lexicon hit ("due au platine") is the French adjective.
- Arm 1: 46 occurrences, all stale old numbers the rules could not update.
- Arm 3: 3 (one value in no source).
- The official gold itself has 3.

## Hand check

Done by me (Claude) reading the window outputs and the official texts, not by a model.

- **All 22 unflagged arm-2 items** (this replaces the 20-item sample, which would have drawn from the same 22):
  - 5 rule-only exact.
  - 2 meaning-equivalent (35-it paraphrase; 16-it word order).
  - 2 harmless duplication (38-it, 41-it repeat "fino alla progressione della malattia.").
  - **7 stale: the DE change was silently not applied**: 03-it, 05-it, 46-it omit the new code-transmission sentence; 08-fr/it omit the new "monotherapy" restriction (and insert a duplicated fragment); 26-it keeps the prior-approval requirement the DE deleted; 56-it keeps "deve essere inviato il seguente codice:" with the code removed.
  - **6 real meaning errors**:
    - 15-it replaces the risk-factor list ("fattori di rischio cardiovascolare, quali diabete mellito, insufficienza renale") with a duplicated paragraph;
    - 16-fr adds "chez l'adulte" but omits the new face/scalp restriction;
    - 19-fr loses "remboursé jusqu'à progression de la maladie";
    - 56-fr cuts "à partir du moment de l'administration";
    - 57-fr deletes "un montant déterminé par emballage remis";
    - 00-it loses the subject "Il titolare dell'omologazione" of the refund obligation and leaves the heading in German.

  None of the 6 is a negation/operator reversal, which is why the lexicon guard misses them. All drop or corrupt a condition.
- **Flagged arm-2 items (98).**
  - **85 scope blow-ups**, classified by the length rule above, 12 read (seeded). All 12 are unusable duplications; several also drop conditions (48-it loses the "TPS ≥ 50%" threshold and leaves a malformed slot "⟨ B �"; 10-fr, 54-fr drop clauses).
  - **The other 13 were read in full**:
    - 2 exact (27-fr/it, lock false positive);
    - **8 real meaning errors**, all caught:
      - 03-fr replaces "du moment de l'administration" instead of appending;
      - 13-fr/it drop the "dermatologist with proven CTCL expertise" route;
      - 33-fr keeps the old risk criterion and drops "ans";
      - 34-fr/it invent a 56 mg/m² maximum;
      - 36-fr drops "dans un établissement spécialisé";
      - 37-fr deletes the csDMARD prior-therapy condition and keeps the refund paragraph the DE deleted;
    - 3 garble or stale (33-it leaves "Referenzdokument Prophylaktische Impfungen" in German; 36-it; 57-it omits the new melanoma exception).
- **Arm 3, 20 of 78 lexicon hits (seeded sample).**
  - **2 real flips**:
    - 29-it "la terapia **dovrebbe** essere interrotta" for "deve";
    - 54-fr "devraient être traités jusqu'à" → "ne doivent être traités que".
  - 2 real-minor: 08-fr "pourcentage déterminé" for "part fixe"; 57-fr "moment de l'administration" for "de la remise".
  - 16 equivalent or lexicon noise (decimal comma 1,8 vs 1.8, "è da comunicare" vs "deve essere comunicato", reordering).
  - Extrapolated: roughly 8 real flips in 120 (wide interval), none flagged.

## Comparison with Gleichschritt (Fedlex)

| | Fedlex S1 | SL S2 |
|---|---|---|
| Rules-only exact | 35% | 5.8% (11.6% on the full pool). SL changes are mostly wording, not numbers |
| Locked 8B exact on items the rules can't solve | 25% (full-paragraph rewrite, then lock check) | 0% (window-only generation by instruction) |
| Gold ceiling | 80% | 75% |
| Free 8B exact | 0% | 0% |
| Free 8B real flips | 20–23% | about 7% (2/20 sampled hits × 78 hits ≈ 8/120), plus 2 minor |

## What this means for the card

- The 2B "the model writes only the changed words" claim is not supported on SL text with this mechanism: the model does not write only the changed words, and code stitching turns that into duplicated clauses.
- The digit ban is real and cheap (0 model-written digits), but it is not a meaning guard. Wrong-but-present numbers, dropped conditions and stale text pass the lexicon guard.
- The only clean wins are the 7 rule-only items, which need no model.
- If the card is revived, the next spike should be: (1) forced-copy constrained decoding (old target outside the window as a hard prefix and suffix, model free only inside), or the S1 full-rewrite + lock design, on the same 120 items; (2) a structured condition guard (dropped clause detection, not marker counts).

## Files (`spikes/gleichlaut/s2/`)

| Path | Contents |
|---|---|
| `extract.py`, `mine.py`, `build_items.py`, `showdiff.py` | snapshot extraction, change mining, item selection |
| `changes_de.json`, `pool_stats.json`, `items.json`, `items_all.json` | 216 DE change pairs, pool stats, the 120 items, the full 362-item pool |
| `gl2.py`, `lock.py` (= gleichschritt/lock.py, sha1 64cf4c1d…) | rules arm, windows, slots, stitching, number counters |
| `s2.py`, `deploy.sh`, `fetch.sh` | Air runner and transfer scripts |
| `score2.py`, `showrow.py`, `showwin.py` | scorer and hand-check viewers |
| `results/arm2.jsonl`, `results/arm3.jsonl`, `results/gl2_air.log` | raw outputs (per window: masked output, slots, timings), Air log |
| `results/scores.json`, `results/review.tsv` | per-row metrics, kill deltas with CIs, review sheet |
| `../data/hist/*.json` | extracted DE/FR/IT limitation texts per snapshot (public BAG data) |

---

# Gleichlaut S2b: 8B whole-paragraph locked rewrite (Gleichschritt arm A), plus the frozen guards3

Run on the M2 Air through `gpu.sh` (12:53 to 14:12 on 9 Oct 2026, 4,384 s), on the same 120 items. Script `s2/s2b.py` (sha1 a28fe9b2…): `gleich.py` arm A with SL wording.
- The 8B sees DE_old, DE_new, the code-derived change list and the old FR/IT, and writes the full new paragraph.
- **The digit ban composes.** Every number in all three texts is a slot code, the logit mask forbids digit tokens and FR/IT number words, and code writes the values back.
- After generation: lock check, one retry with feedback, then flag.
- The 7 rule-only items skip the model.
- guards3 (`rescue70b/g3/guards3.py`, sha256 113aa7a1…, unmodified, hash asserted at import) was applied afterwards with the 70B pipeline's `full_check` (`s2/g3_apply.py`). **There was no re-ask**, because no new GPU jobs were allowed. The comparable 70B row is therefore "2b + guards", not "+ re-ask".

## Verdict

1. **S2b as run (lock, slot guard and one retry) fails the error rule.**
   - Exact is +9.2 points over rules-only [95% CI +3.3, +15.8], and chrF is +3.0 [+1.9, +4.1], so the quality rule passes.
   - But **4/120 outputs carry unflagged real meaning errors** (limit 1/120), and 33 more are unflagged stale or German-left.
2. **With guards3, the errors are fixed but the flag rate is not.**
   - Unflagged real errors: 1/120 (0.8%, Wilson upper bound 4.6%).
   - Unflagged stale or untranslated: 0/120.
   - Exact: +9.2 points.
   - **Flag rate: 85% (102/120), above the 70% cap.**
   - Only 17/120 (14%) outputs are both unflagged and correct, against 39/120 (32.5%) for the 70B with guards and re-ask on the same items. The 8B is not close enough to make Gleichlaut fully local.
   - The one leak is a direction flip: 35-it "Trattamento alla **riduzione** della densità minerale ossea" for "Erhöhung" (increase). It is the kind of error a reviewer most needs to catch, and no guard checks for it.

## Table (FR+IT, n = 120; rules-only exact 7/120 = 5.8%)

| Stage | Exact | Δ exact vs rules [95% CI] | Flagged | Unflagged | Unflagged real errors | Unflagged stale | Unflagged untranslated |
|---|---|---|---|---|---|---|---|
| S2 window-only (for reference) | 7 = 5.8% | +0.0 | 82% | 22 | 6 | 7 | 0 |
| **S2b as run** | 18 = 15.0% | **+9.2 [+3.3, +15.8]** | 62 = 52% | 58: 14 exact, 7 equivalent | **4** (3.3%; Wilson [1.3, 8.3]) | **22** | **11** |
| **S2b + guards3 (no re-ask)** | 18 = 15.0% | +9.2 [+3.3, +15.8] | **102 = 85%** | 18: 12 exact, 5 equivalent or cosmetic | **1** (0.8%; Wilson [0.1, 4.6]) | 0 | 0 |
| 70B 2b + guards v2 (no re-ask), same 120 | 21 = 17.5% | +11.7 | 72% | — | 0 | 0 | 0 |
| 70B + guards v2 + re-ask, same 120 | 21 = 17.5% | +11.7 | 67.5% (71.7% with guards3) | 39 | 0 | 0 | 0 |
| 70B + guards3 + re-ask, fresh 2025 set (n = 166) | 17.5% | +11.4 [+4.8, +18.7] | 60.2% | 66 | 0 | 0 | 0 |

**Other S2b metrics:**
- **Overlap:** edit-F1 is 40.3 against 7.1 for rules (+33.2 [+25.9, +41.0]); chrF is 91.8 against 88.8.
- **Lock:** 87 of 113 model outputs passed on the first try, 26 were retried and 0 of the retries fixed the problem. As in Gleichschritt, a greedy retry repeats itself.
- **Per language:** exact is FR 7/60 and IT 11/60; guards3 flags 51/60 in each.
- **Digits:** 0 model-written digits in all raw generations. Numbers not in the DE: 14 occurrences in 14 items, all old values still present in the old FR/IT.
- **Speed:** 38.8 s per model item with MLX on the Air. CPU / GGUF is still not measured.
- **Wasted flags:** guards3 flags 6 of the 18 exact outputs and 2 of the 7 equivalent ones.

## Kill and pass rules

| Rule | S2b as run | S2b + guards3 |
|---|---|---|
| Exact ≥ rules + 5, or (edit-F1 gain and chrF ≥ rules) | +9.2 exact (CI lower bound 3.3); edit-F1 +33.2 with chrF +3.0: **pass** | same: **pass** |
| Unflagged real errors ≤ 1/120 (≤ 1%) | 4/120: **fires** | 1/120 = 0.8%: **pass** (upper bound 4.6%) |
| Unflagged stale + untranslated ≤ 2% (70B rule) | 33/120 = 27.5%: fail | 0: **pass** |
| Flag rate ≤ 70% (70B rule) | 52%: pass | **85%: fail** |

## Hand check (`s2/results/handcheck2b.tsv`)

I (Claude) read **all 44 unflagged non-exact S2b outputs** against DE old/new and the official FR/IT; the 14 unflagged exact outputs need no reading. These 44 include all 6 non-exact outputs that guards3 leaves unflagged. No flagged-sample check was done for S2b, because only unflagged outputs were requested.

**4 real meaning errors:**
- **35-it:** "riduzione" (reduction) for "Erhöhung der Knochenmineraldichte" (increase). guards3 does not flag it.
- **13-it:** the qualifying training site becomes "con i relativi reparti di ematologia o oncologia, o dermatologia", so dermatology alone suffices. The DE requires dermatology plus medical oncology, medical oncology, or haematology. guards3 flags it.
- **31-fr and 31-it:**
  - The DE replaced the XTANDI mHSPC indication sentence with a cost-approval clause.
  - The outputs keep the indication and add only "après consultation du médecin traitant" or "Dopo consultazione del medico di fiducia".
  - So the cost-approval requirement is missing, and FR says *treating* physician.
  - guards3 flags both.

**22 stale.** The change was not applied, or only partly:
- 00, 07 and 40 (FR and IT), 12-fr: new indication heading missing.
- 21, 24 (FR and IT), 04-fr: "indiqué/indicato" not changed to "remboursé/rimborsato".
- 22, 26 (FR and IT), 30-fr: deletion not applied; 26 keeps a prior-approval requirement the DE removed.
- 23-fr, 44-it: code boilerplate only half applied.
- 32-it, 52-it: product name not inserted.
- 45-it: "adulti" restriction missing.

All 22 are flagged by guards3 (G2).

**11 German left in:**
- whole German sentences: 03-it;
- German words or phrases: "als Monotherapie" (08-fr/it), "sofern" (01-fr/it), "gemäss Referenzdokument" (33-fr/it), "Der Indikationscode" (23-it), "Folgore Indikationscode" (18-it), "im face ou sur la tête" (16-fr);
- the hybrid "revaskolarizzazione" (15-it).

All 11 are flagged by guards3 (G1/G5/G7).

**7 equivalent or cosmetic:**
- 13-fr and 16-it: correct rewrites;
- 15-fr: comma;
- 35-fr: awkward but correct;
- 36-it: "neurologo";
- 32-fr and 52-fr: brand left in DE spelling.

guards3 flags 2 of these 7.

**Guard behaviour on 8B outputs.** Of the 37 defective S2b-unflagged outputs, guards3 catches 36. The miss is the only direction flip: the guards check presence and absence of content, not polarity of meaning.

## Caveats

- **Partly in-sample.** guards v1/v2 were designed after reading the 70B hand check on these same 120 items (guards3 = v2 + detectors designed on the 242-item dev set). The 8B outputs are new to the guards, but the items and DE edits are not. The 70B's clean result came from a fresh 2025 set that the 8B has not been run on.
- **No re-ask.** The 70B gained about 4 points of flag rate from one guarded re-ask. A greedy 8B retry fixed 0/26 here, so a re-ask is unlikely to close the 15-point gap to the 70% cap, but this was not measured.
- **Small n.** 1/120 real errors has an upper bound of 4.6%; the exact gain's CI lower bound (3.3) is under +5.

## What this means for the card

- The whole-paragraph design rescues the 8B's *quality* (+9 exact, +3 chrF, 0 model digits), where window-only generation failed outright.
- With guards3 the leaks shrink to one, but the 8B produces far fewer ready outputs than the 70B. Translators would review 85% of items, and 1 of the 18 that pass contains a reversed meaning.
- "Gleichlaut fully local on CPU" is **not supported**. The sovereign story stays: the 70B on Swiss infrastructure drafts, guards3 checks, and local CPU is not enough.
- If revisited, the cheapest next test is the 8B on the fresh 2025 set with guards3 and one sampled (non-greedy) re-ask, plus a polarity check for increase/decrease-type antonyms. That test needs GPU time.

## Files (`spikes/gleichlaut/s2/`)

`s2b.py` (Air runner), `g3_apply.py` (frozen guards3 + full_check), `show2b.py` (viewer), `results/arm2b.jsonl`, `results/gl2b_air.log`, `results/g3_rows.json` (per-item flags and guard components), `results/worklist2b.json`, `results/handcheck2b.tsv` (labels and notes), `score2.py` (now also scores arm 2b).
