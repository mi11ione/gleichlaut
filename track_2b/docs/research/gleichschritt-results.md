# Research record (verbatim): Gleichschritt (Fedlex lane research)

Copied from the research log `spikes/gleichschritt/results.md` (not part of this repository; sha256 of the full file when copied: `a862e1bbfabd5546e8da042e1d079f5dc37145d377c0bed5ab22ea209227c242`).

---

# Gleichschritt spike S1 (with S2 and S3): results

8 Oct 2026. Card: `loop/r8/cards/C-2B-gleichschritt.md`.

**Question.** When a Swiss provision is amended in German, can the local Apertus 8B write only the matching change into the old FR/IT/RM text and match the version the authorities actually published?

**Setup.**
- Model: Apertus v1.5 8B text, MLX 4-bit DWQ (`m1rkocasu/Apertus-v1.5-8B-text-MLX-4bit-DWQ`), greedy decoding, thinking off.
- Runs were on the M2 Air through `gpu.sh`. The run took 1906 s for 150 arm-A items (plus 14 retries) and 155 arm-B items.
- Code: `gleich.py` (model loop), `lock.py` (lock, slot guard and code lane, shared with the scorer), `score.py`.

## Verdict

**Formally PASS. Substantively weak.** Read the caveats before using the headline.

| Rule | Threshold | Measured | Result |
|---|---|---|---|
| Pass: FR/IT exact | ≥35% | **50.0%** (60/120) | pass. Without the SEFRI mass-amendment cluster: 28.0% (23/82) |
| Pass: RM exact | ≥25% | **26.7%** (8/30) | pass, barely. 7 of the 8 are the code lane; the model wrote 1/22 |
| Pass: edit-F1 A − B | ≥ +15 points | FR/IT **+40.9** (72.7 vs 31.8); RM **+27.3** (65.9 vs 38.6) | pass |
| Kill: FR/IT exact | <20% | 50% (28% without the cluster) | not fired |
| Kill: unflagged meaning flips | >5% | FR/IT 0.8% (1/120); RM 3.3% (1/30). By hand: 0/150 are real flips | not fired |
| Drop RM headline | RM <10% | overall 26.7%. **Model-written RM: 1/22 = 4.5%; Graubünden RM: 0/19 by the model** | **drop the RM headline** in substance |

The model adds little beyond the rules:
- **FR/IT.** On the 48 items the code lane handles (numbers and dates), the model and the rules are both exact on 42/48. On the other 72 items the model is exact on 18/72 (25%). Six of those 18 are SEFRI items with an extra "die" deletion; the other 12 are short or mechanical edits.
- **RM.** The model is exact on 1/22 items outside the code lane, and that one is a "." → ";" change.

## 1. Pool

Pools are built from pairs of consecutive consolidated versions, with paragraphs aligned by AKN eId (federal) or by GR-lex side-by-side rows keyed by article / paragraph / item labels (Graubünden). Footnotes are stripped. A paragraph enters only if both its DE text and its target text changed.

| Pool | Source | Scanned DE-changed paragraphs | Skipped as >60% words changed | Repealed (code lane) | DE changed but target unchanged | Used |
|---|---|---|---|---|---|---|
| Federal FR/IT, new version applicable 2025-01-01..2026-10-08 | Fedlex SPARQL + filestore XML, 26 acts | 143 | **37 (26%)** | 5 | 10 | 60 paragraphs → 60 FR + 60 IT |
| Federal RM, 2024–26 (RM consolidations are sparse; some pairs span several years) | Fedlex, 16 acts | 128 | **27 (21%)** | 4 | 8 | 10 |
| Graubünden DE/RM, change documents 2024–26 | GR-lex API (`texts_of_law/{sr}/versions/{id}`, `change_documents/{id}`) | 131 | **15 (11%)** | 9 | 1 | 20 (of 43 collected) |

- **Paragraph length** was 15–1200 characters, at most 2–4 paragraphs per act or version.
- **Correction-born pairs.** None of the federal pairs has a correction impact in its window, checked against all 321 correction impacts since 2023.
- **Repeals.** All 18 repealed paragraphs become "N …" in the target as well, so the code lane copies them, up to the official texts mixing "…" and "...". They are kept out of the model pool.
- **SEFRI cluster.** 19 of the 60 FR/IT paragraphs are the same mass amendment: the SEFRI general-education ordinance date in the vocational-training ordinances changed from 27 April 2006 to 9 April 2025. This is real data, and mass amendments are the common case, but they dominate the FR/IT pass. Results are reported with and without the cluster.

Files: `pools/fed_fr_it.json`, `pools/fed_rm.json` and `pools/gr_rm.json` (each with stats and skipped lists), `items.json` (155 items), and `items_run.json` (the interleaved run order).

## 2. Results per language and arm

Column definitions:
- **exact**: equal to the official new text after whitespace and apostrophe normalisation.
- **strict**: byte-equal after whitespace normalisation. Arm A gets a deterministic ’ restoration, because the 8B always emits '.
- **edit-F1**: token edits old→output against old→official.
- **out-of-span chars**: characters changed outside the lock windows.
- **flag**: the lock still failing after the retry, or the slot guard firing.
- **flip**: per-language lexicon differences in negation, modality or numbers between the output and the official text.

| Group | Arm | n | exact | strict | edit-F1 | chrF | 0 chars outside span | out-of-span chars (mean) | flagged | flips | unflagged flips | s/paragraph |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FR | A | 60 | **50.0%** | 50.0% | 69.5 | 89.1 | 90% | 4.7 | 17% | 6.7% | 0.0% | 6.8 |
| FR | B | 60 | 0.0% | 0.0% | 32.9 | 63.0 | 12% | 65.2 | (none) | 20.0% | 20.0% | 4.5 |
| IT | A | 60 | **50.0%** | 50.0% | 75.9 | 89.8 | 93% | 1.8 | 8% | 3.3% | 1.7% | 6.7 |
| IT | B | 60 | 0.0% | 0.0% | 30.8 | 57.4 | 10% | 82.2 | (none) | 23.3% | 23.3% | 4.7 |
| FR+IT | A | 120 | **50.0%** | 50.0% | 72.7 | 89.4 | 92% | 3.2 | 12% | 5.0% | 0.8% | 6.7 |
| FR+IT | B | 120 | 0.0% | 0.0% | 31.8 | 60.2 | 11% | 73.7 | (none) | 21.7% | 21.7% | 4.6 |
| FR+IT, no SEFRI | A | 82 | 28.0% | 28.0% | 60.2 | 84.6 | 88% | 4.7 | 18% | 7.3% | 1.2% | 7.0 |
| FR+IT, no SEFRI | B | 82 | 0.0% | 0.0% | 34.9 | 58.5 | 16% | 84.0 | (none) | 31.7% | 31.7% | 4.5 |
| RM (all) | A | 30 | **26.7%** | 26.7% | 65.9 | 91.2 | 87% | 2.5 | 17% | 13.3% | 3.3% | 8.5 |
| RM (all) | B | 30 | 0.0% | 0.0% | 38.6 | 69.8 | 3% | 64.8 | (none) | 23.3% | 23.3% | 5.5 |
| RM, S2-clean | A | 11 | 36.4% | | 57.1 | 90.3 | 91% | 0.5 | 18% | 9.1% | 0.0% | 9.2 |
| RM, S2-contaminated | A | 11 | 0.0% | | 55.9 | 92.2 | 82% | 0.7 | 18% | 27.3% | 9.1% | 10.8 |

RM split by source: federal RM is 7/10 exact (6 by the code lane, 1 by the model). Graubünden RM is 1/20 (the code lane), and the model is 0/19.

**Code lane** (numbers, dates via month names, SR and article numbers; no model):

| Language | Applicable | Fully solved (exact) |
|---|---|---|
| FR | 24/60 | **21/60 (35%)** |
| IT | 24/60 | **21/60 (35%)** |
| RM | 8/30 | **7/30 (23%)** |

- The code lane also solves all 18 repeals ("N …"), which are outside the pool.
- "A+code" (the code lane first, then the model) gives the same exact rates as arm A, at 4.2 s/paragraph for FR/IT.
- On the code-lane items the model and the rules agree on exactness 42/42 (FR/IT) and 7/7 (RM).

**Lock and retry.**
- **Lock ceiling.** The official new text itself passes the lock only 45/60 (FR), 48/60 (IT) and 15/30 (RM). Two causes:
  - Translators make target-only revisions alongside the amendment, for example a whole FR sentence rewritten when only the DE date changed.
  - The windows are too tight around word-order shifts.

  So about 20% (FR/IT) and 50% (RM) of official amendments would themselves be flagged. The windows cover about 45% of the target tokens; the official edits touch about 17%.
- **Retry.** 14 items went to a retry and 0 were fixed. 11 of the 14 retries reproduced the first output exactly, because greedy decoding ignores the feedback.
- **Apostrophe artefact.** The as-run lock counted the 8B's ’→' substitution as an out-of-span edit, giving FR/IT 21% flagged instead of 12% and IT strict-exact 13% instead of 50%. `score.py` replays the recorded outputs with the lock on normalised text, which reproduces exactly what the corrected pipeline would have produced. The "A-asrun" rows in `results/scores.json` keep the original numbers.
- **Precision when unflagged.** Of the unflagged A outputs, 57/105 FR/IT (54%) and 8/25 RM (32%) are exact. Of the flagged FR/IT outputs, 3/15 are exact.

**Meaning flips, adjudicated by hand.**
- **The guard caught all of the model's own flips.** In GR 506.060, Art. 18 Abs. 2 and Art. 28 Abs. 2, the 8B dropped "betg" ("na vegnan ademplidas"). That is the known dropped-negation failure, and the guard flagged both times.
- **The two unflagged lexicon hits are not meaning flips:**
  - The IT output has "3 m" where the official text has "tre metri".
  - In RM (GR 740.330, Art. 16), the output keeps the old clause with "pon", which the official text rewrote target-only.
- Real unflagged flips: **0/150**.

**Speed (M2 Air, MLX 4-bit, greedy).**

| Arm | FR/IT | RM |
|---|---|---|
| A | 6.7 s/paragraph (retries included) | 8.5 s/paragraph |
| B | 4.6 s/paragraph | 5.5 s/paragraph |
| A+code | 4.2 s/paragraph | |

The card's CPU Q4 timing was not done; this spike was MLX on the Air only.

## 3. S2: contamination (13-gram, `swiss-ai/apertus-pretrain-romansh`)

**Method.**
- The dataset is small: 32 files, 345 MB in total. All of it was downloaded to the scratchpad and scanned; nothing was streamed.
- Tokens are lowercased words. Each item is classed as contaminated if at least 50% of the gold's amendment-novel 13-grams are in the corpus, or, with no novel 13-gram, at least 50% of all its new-text 13-grams.

**Findings.**
- **Graubünden: contaminated.**
  - 10/15 items with novel 13-grams have the amended RM wording at ≥50%, every one at 100%. The source is `polylingual/Aligned/swiss_laws_in_ROH.jsonl.gz`, which holds GR-lex texts crawled after the 2024–25 amendments.
  - Mean new-text containment is 0.82.
  - 11/20 items are classed contaminated and 4 are too short to test.
- **Federal RM: clean.** 0/6 items have novel 13-grams in the corpus. The old texts are present (mean containment 0.77) through `Synthetic/swiss_laws_interleaved` (Fedlex, around 2023).
- **Card rule:** more than 20% contained, so restrict the headline to clean items.
  - Clean RM: 4/11 exact, all from the code lane.
  - Contamination did not help: contaminated items scored 0/11 exact, so the model does not regurgitate the memorised new text.
- Output: `results/s2_contamination.json`.

## 4. S3: were the 27 substantive corrections born in amendments?

**Scope.**
- Of the 27, 12 are FR- or IT-only errors. These are the only ones Gleichschritt could prevent; DE-wrong and all-language errors cannot be.
- 11 units in 10 notices are locatable in the AKN text. Annex tables are not.
- Each unit was traced by binary search over the consolidated XML versions (`pools/s3_history.json`).

**Classification.**

| Kind | Cases |
|---|---|
| Delta to an existing paragraph (Gleichschritt's mode) | **0** |
| New unit inserted by an amendment (new-text translation, cut from the card's scope) | **5**: AVO 93/3 (2024-01-01), MWSTG 18/3 (2025-01-01), **EnG 71a/1 (2022-10-01, Solarexpress)**, EnFV 46a/1 and 46dbis/1 (2026-01-01) |
| Original enactment | MAV 22/2 (act from 2024-08-01) |
| Wrong since the earliest XML version (older HTML versions not traced) | MinöStV 24/2b, VZVM 5/2, VZAE 82/1 |
| Not applicable (unit text unchanged or empty) | 2 (BiVo 381 table, Abk. Armenien) |

**Arm B on the 5 new units.** The fresh translation from DE carries the corrected slot in **5/5**:
- "non vengono scambiati" (AVO)
- "al beneficiario" (MWSTG)
- "produzione annuale" (EnG)
- "semestre invernale", twice (EnFV)

The wording is not publishable. It uses "comma" or "paragrafo" for capoverso, "riconciliazione" for conteggio, and "le impianti". The B-vs-official slot diff is noisy on ordinary items: negation differs in 7/120 and numbers in 14/120.

**Demo beat as specified** (at least 2 delta-mode drafts that already carry the correction): **fails, 0 eligible cases.**

## 5. Three examples

**(1) Model-written exact, with a lock false positive in the as-run lock.** cc/2013/793 Art. 7 Abs. 1, IT, 2026-01-01.
- DE: "zu 16 → 10 Prozent … zu 84 → 90 Prozent … biogene → erneuerbare Treibstoffe".
- Arm A output: "per il 10 per cento … per il 90 per cento … i carburanti rinnovabili sono equiparati all’olio diesel". This is the official text exactly, including "l’84" → "il 90" and "biocarburanti" → "carburanti rinnovabili".
- Arm B: "10 percento … gasolio … lo spirito bianco … equiparabili", which drifts in terminology throughout.
- The as-run lock flagged it only for ’→'.

**(2) A Romansh negation drop, caught by the guard.** GR 506.060 Art. 28 Abs. 2.
- DE: "wird vom Amt vorgenommen" → "kann vom Amt vorgenommen werden"; "Litera g und h" → "Litera g und Litera h".
- Official RM: "litera g e litera h … po vegnir fatga … na vegnan betg ademplidas".
- Arm A: "literas g e Litera h … po vegnir fatga … na vegnan ademplidas". The modal change is right, but the output is miscased and drops "betg".
- The slot guard flags the negation count (2→1) and the lock flags it too. Same pattern in Art. 18 Abs. 2.

**(3) The ceiling: official target-only rewriting.** cc/2009/681 Art. 12a Abs. 1, FR, 2025-05-01.
- DE changed only "26. September 2014" → "14. Juni 2024".
- Arm A changed exactly the date: "…de la modification du 14 juin 2024 le restent selon l’ancien droit dans la mesure où elles ne font pas l’objet d’un retrait…".
- The official FR rewrote the whole sentence ("Les licences valables au moment de … demeurent valables en vertu de l’ancien droit, à moins qu’elles ne soient retirées ou révoquées…").
- Exact match is impossible by design, and the lock correctly treats the official edit as out of span.

## 6. Caveats

- **The pass rides on rules and one cluster.** The FR/IT 50% includes 19 SEFRI paragraphs that are 37/38 exact. Without them the result is 28%: above the kill line, below the pass line. Every exact model-written RM item is federal; Graubünden RM by the model is 0/19.
- **Gold ceiling.** 20–25% (FR/IT) and 50% (RM) of official amendments include target-side edits outside the DE-aligned span. Exact match against the official text is therefore capped well below 100% for any locked system, and the "lock badge" would flag about a fifth of genuine official amendments.
- **The lock was fixed a priori, then post-corrected for apostrophes only.** The margin was max(3, 15% of the anchor gap) and was not tuned on gold. One tested alternative, extending windows to clause boundaries, raises gold fit to 90/93/77% but makes about 80% of the tokens editable. It was rejected and not used.
- **Lexicon-level flips are coarse.** Expletive "ne", number words and "na" in RM all trigger them. Real flips were adjudicated by hand on all 10 A-arm flip hits; n = 150 is small.
- **Arm B is maximally disadvantaged.** It sees neither the old target nor the terminology. Its exact rate of 0% is expected, and the edit-F1 gap partly measures "copying the old text". The fair rival is a fuzzy-match repair baseline, for example a copy of the old target plus a code lane: on FR/IT that baseline alone already gives 35%.
- **Small and clustered samples.** 26 federal acts for FR/IT, 11 for RM. Graubünden is 20 paragraphs from 6 versions. The GR keying by labels misses renumbered units.
- **Not done:** Qwen comparison, CPU / llama.cpp Q4 timing, GR IT items (they were collected in `pools/gr_rm.json` but not run), and federal DE/FR/IT/RM four-column items.
- **Retry is useless with greedy decoding.** A sampled retry or constrained decoding (copying from the old target outside the windows) would be the next thing to try, before any re-spike.

## Files

- `results/A.jsonl`, `results/B.jsonl`: raw outputs, first and retry generations, timings.
- `results/scores.json`: per-row metrics, the code-lane outputs, and the A-asrun vs corrected rows.
- `results/s2_contamination.json`.
- `raw/gleich_air.log`.
- `pools/*.json`, `items.json`, `items_run.json`.
- Code: `build_fed.py`, `build_gr.py`, `make_items.py`, `gleich.py`, `lock.py`, `score.py`, `s2_contam.py`, `s3_history.py`.
- `cache/`: about 167 MB of Fedlex and GR-lex responses, fetched with UA hackapertus-research/0.1 at 1.1 s or more between requests per host.
