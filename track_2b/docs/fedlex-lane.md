# Fedlex lane (Gleichschritt)

When a federal act is amended, the consolidated German paragraph changes, and the French and Italian paragraphs must
change in step. The Fedlex lane drafts that FR/IT change. It is the "8B where sufficient" lane: Apertus 8B rewrites
the wording, and code handles numbers, dates and article/SR numbers.

## What it does

```
fed.ingest   SPARQL (consolidated versions, applicability dates) + filestore AKN XML (DE/FR/IT/RM)
fed.mine     leaves aligned by eId; DE changed -> item, unless repealed, target unchanged, DE change > 60 % (-> human),
             or the paragraph is shorter than 15 or longer than 1200 characters
fed.lane     1. code lane (lock.code_lane): every DE change is a number / date / month name -> substitute by rule, no model
             2. otherwise arm A: one prompt with DE old, DE new, the list of German changes and the old FR/IT text;
                "change only the words that correspond to the German change" (whole-paragraph locked rewrite)
             3. lock.check: no edit outside the windows projected from the DE edit spans -> else one retry that names the
                out-of-span edits -> else flag
             4. slot guard (lock.guard): the negation / modal / number deltas must mirror the German -> else flag
             5. SL guard stack v2, G1-G4 (core.guards = frozen/gl/guards.py, V2): G1 German left in the target, G2 the
                German change not applied, G3 content dropped or removed without a German reason, G4 duplication -> else flag
             ready = lock, slot guard and G1-G4 all pass
```

**Shipped guard stack.** A draft is "ready" only if the lock (after the one retry), the slot guard and G1–G4 all pass.
The research verdict (lock + slot guard only) is still computed as `status_research` / `flagged_research`, and every
reproduced results.md number uses it. G5–G7 (guards3) are not used, because their whitelist, vocabulary and term
resources are built from the SL corpus. `guards.py` has no Romansh function-word list, so an RM draft is never "ready".
**DEV caveat:** the decision to add G1–G4 to this lane was made after reading these recorded outputs (the "EFZ" item
below), so every shipped-lane number on these 120 items is in-sample.

The code is the research code. `src/gleichlaut/fed/research/` holds byte-identical copies of the Gleichschritt files
(sha256 in `SHA256SUMS`, checked at import). `fed/lane.py` executes the prompt, cleaner, change list and the loop
(`run_A`) from `gleich.py` via `ast`, with only the model call injected. That works with any backend in
`gleichlaut.backends`, and the lane lifts the LlamaCpp digit ban for its calls, because the Fedlex prompt carries numbers
verbatim and the research run had no ban. The lock is `core.lock`: `gleichschritt/lock.py` is byte-identical to `frozen/s2/lock.py`.
The lock check runs on apostrophe-normalised text, and the 8B's `'` is restored to `’`. This is the corrected pipeline
that `score.py:corrected()` replays and that the reported numbers describe.

Scope: FR/IT. `gleich.py` also names Romansh ("Romansh (Rumantsch Grischun)"), so RM items run, but RM is exploratory only.

## Numbers (recorded run, re-scored)

`PYTHONPATH=src python3 -m gleichlaut.fed.score` executes the research scorer on the copied runs and writes
`eval/results/fedlex.json` (headline, the 12-row results table, 162 checks against `spikes/gleichschritt/results.md`,
replay summary) and `eval/results/fedlex_scores.json` (per-row scores). Its `scores.json` is byte-identical to the
research one (sha256 `43b17070…`). **162/162 quoted numbers reproduce.**

| What | Value | Where in `eval/results/fedlex.json` |
|---|---|---|
| FR/IT exact vs the official new text, arm A = shipped lane (A+code) | **50.0 %** (60/120); FR 50.0 %, IT 50.0 % | `headline`, `derived["FR/IT exact (A)"]` |
| ... without the SEFRI mass amendment (19 paragraphs, 37/38 exact) | **28.0 %** (23/82) | `derived["FR/IT exact without SEFRI (A)"]` |
| Code lane alone (no model) | 35 % (FR 21/60, IT 21/60) | `derived["code lane FR"]`, `code_lane` |
| Model-lane items (not number/date changes) | 18/72 exact, 6 of them SEFRI | `derived["FR/IT model-lane exact (A)"]` |
| Free translation (arm B, the naive approach) | 0 % exact; lexicon flips FR 20.0 %, IT 23.3 %, none flagged | `summary["fr+it|B"]`, `headline` |
| Flagged (lock after retry, or slot guard), FR/IT | arm A 12.5 % (15/120); shipped A+code 10.8 % | `summary` |
| Unflagged lexicon flips, FR/IT | arm A 1/120; A+code 2/120 | `derived`, `summary` |
| Real unflagged meaning flips, by hand | 0/150 (results.md: all 10 A-arm flip hits read by hand) | not recomputable; see below |
| Unflagged precision, FR/IT | 57/105 exact | `derived` |
| Edit-F1, FR/IT, A vs B | 72.7 vs 31.8 | `summary` |
| Speed, MLX 4-bit on the M2 Air | arm A 6.7 s/paragraph, A+code 4.2 s (FR/IT) | `summary[...]["secs"]` |
| RM (exploratory) | 26.7 % exact (8/30), but the model wrote 1/22 exactly; Graubuenden RM 0/19 by the model | `derived` |

**Shipped lane on the same recorded outputs, DEV** (`eval/results/fedlex.json["shipped lane = A+code + lock + slot + G1–G4 (DEV: guard choice made after seeing these outputs)"]`):

| | n | exact | flagged | ready | ready and exact | exact but flagged | newly flagged by G1–G4 (of them exact) |
|---|---|---|---|---|---|---|---|
| FR | 60 | 30 | 19 | 41 | 28 | 2 | 10 (0) |
| IT | 60 | 30 | 19 | 41 | 29 | 1 | 15 (1) |
| FR+IT | 120 | 60 | **38** | 82 | 57 | 3 | **25 (1)** |

G1–G4 raise the share flagged from 13/120 (research verdict, A+code) to 38/120. They cost one exact draft, and ready precision rises from 58/107 (54%) to 57/82 (70%). The hits are mostly G2 (27 items), then G3 (10), G1 (2) and G4 (2). The 25 drafts
that are still ready but not exact are in a blind annotation worklist; the labels are not done yet.

The two A+code unflagged lexicon hits are not meaning flips. We read both: IT "3 m" where the official text writes
"tre metri", and the cc/2009/681 Art. 12a date-only change, where the official FR also rewrote the sentence (an extra
expletive "ne").

## Replay test (the rigour step)

No prompts were recorded in the Air run. The raw generations were. `tests/test_fedlex.py::test_replay_recorded_raw_outputs`
runs the extracted `run_A` with a fake `ask` that returns the recorded `raw1` (and `raw2` when the loop asks again), and requires:

- **every recorded field of all 150 A records is rebuilt exactly**: cleaned output, lock check with its out-of-span list,
  the retry decision (25 as-run retries), the retry output and check, and the flags. The first prompt equals `PA` filled
  from the item, and every retry prompt equals that prompt plus `RETRY` filled from the recorded `check1`;
- **the shipped lane** (code lane, then the corrected arm A, then the slot guard) on the same recorded raws gives
  exactly the research scorer's `A+code` rows (output, flag, guard) for all 150;
- **arm B**: `run_B` rebuilds all 155 recorded outputs.

The prompt text is therefore proven equal by source identity (byte-identical `gleich.py`, sha-checked), not by comparing
against recorded text. The cleaner, lock, retry logic and scorer are proven equal by the replay. One residue remains. In 6 of the 12
shipped-lane retries, the retry complaint under the normalised lock is worded differently from the as-run complaint that
produced the recorded `raw2`, so those 6 retries replay a generation from a slightly different prompt. The research
scorer makes the same substitution. No retry ever fixed an item (0/14 under the corrected lock; greedy decoding repeats
itself in 11 of the 14).

## Live slice (`make run` step 4)

`lane.live_slice(ask)` drafts the 5 items in `data/items/fedlex_live5.json` with whatever backend `make run` provides
(LLM_BASE_URL or the CPU GGUF). For each item it prints DE old/new, the old target, the draft, the lock and slot-guard
verdict, whether the draft equals the official text, the recorded MLX-DWQ 8B result on the same item, and the seconds taken.

Selection rule (`lane.LIVE_RULE`, enforced by a test): the federal FR/IT items the model must draft. That means
`code_lane()` produces nothing and the item is not in the SEFRI cluster. They are sorted by `len(de_old)+len(de_new)+len(tgt_old)`,
then key, and picked greedily, shortest first, alternating FR, IT, FR, IT, FR, one per act. Short paragraphs keep a CPU run fast.

| # | Item | Change | Recorded 8B (MLX DWQ) |
|---|---|---|---|
| 1 | cc/2016/615 Art. 19 Abs. 4 lit. c, FR | "Allgemeinbildung: 20 %;" -> "Erfahrungsnote: 30 %." | ready, not exact ("expérience" for "note d’expérience") |
| 2 | cc/2009/681 Art. 4 Abs. 1 lit. c, IT | "." -> "; und" | ready, exact |
| 3 | cc/2011/251 Art. 2 Abs. 1 lit. e, FR | "Restaurationsangestellte EBA" -> "Köchin EFZ / Koch EFZ" | **wrong; lock + slot guard pass it, the shipped G2 flags it** ("change not applied"): keeps "employée en restauration", writes "EFZ" |
| 4 | cc/2018/732 Art. 9 Abs. 2, IT | "Dienstbüchlein einzutragen" -> "Ausweis über die Erfüllung der Militärdienstpflicht anzuzeigen" | ready, not exact (keeps "iscritta" although the German verb changed; "certificato" for "attestato") |
| 5 | cc/2000/15 Art. 9 lit. p, FR | "." -> ";" | ready, exact |

The slice is chosen to be honest, not flattering: 2/5 exact in the recorded run. Item 3 is a wrong draft that the research
verdict passes and the shipped G1–G4 flag. Items 1 and 4 are ready but not exact. Each row prints the lock, slot-guard and G1–G4 verdicts.
G1 does not catch "EFZ" because it ignores all-caps tokens; G2 catches it, because the new job title was never written.

## Mining a new consolidated version

`PYTHONPATH=src python3 -m gleichlaut.fed.mine cc/2011/28` mines the newest consecutive version pair, and
`... cc/2011/28 2024-04-01 2026-01-01` mines a given pair. Both are offline by default: they read the research cache
(`spikes/gleichschritt/cache`, plus the older fedlex/leggasi caches), and a cache miss returns nothing. `--online` (or
`GLEICHLAUT_FEDLEX_ONLINE=1`) fetches with UA hackapertus-research/0.1 at 1.1 s or more between requests, writes to
`~/.cache/gleichlaut/fedlex`, and takes filestore documents from `www.fedlex.admin.ch/filestore`.
The research crawl fetched its 443 filestore documents from `fedlex.data.admin.ch/filestore`, which robots.txt disallows; the shipped code fetches from `www.fedlex.admin.ch/filestore` instead. `--smoke` re-mines all 120 research FR/IT
items from the cache and requires them to be identical; it reproduces 120/120 over 26 version pairs.

## Caveats (from `spikes/gleichschritt/results.md`)

- **The SEFRI cluster carries the pass.** 19 of the 60 FR/IT paragraphs are one mass amendment (a date change in the
  vocational ordinances), 37/38 exact. Without it the exact rate is 28 %, between the kill line (20 %) and the pass line (35 %).
  The model adds little over the rules: code lane and model agree on all 42 code-lane exacts, and outside the code lane
  the model is exact on 18/72.
- **Gold ceiling.** The official new text itself passes the lock in only 45/60 (FR) and 48/60 (IT) cases (15/30 RM),
  because translators revise beyond the German change. Any locked system is capped well below 100 % exact, and the
  lock would flag about a fifth of genuine official amendments.
- **"Ready" is not "correct".** The research verdict had only the lock and the slot guard (negation / modal / numbers),
  so a draft that never applied the change could pass (live item 3). "0/150 real flips" covers negation, modality and
  numbers only. The shipped lane adds G1–G4, but that choice is DEV (in-sample, see above), and 25 shipped-ready drafts
  still differ from the official text; whether they are acceptable is open until they are annotated.
- **RM is weak.** The model wrote 1/22 RM items exactly, and 0/19 for Graubuenden. The Graubuenden RM texts are in the
  Romansh pretraining data (S2 contamination), and that did not help. RM is reported as exploratory, outside Gleichlaut's FR/IT scope.
- **The build differs.** The numbers are from the third-party MLX 4-bit DWQ build (`m1rkocasu/Apertus-v1.5-8B-text-MLX-4bit-DWQ`)
  on a laptop GPU. `make run` ships a GGUF build on CPU: Q8_0 by default, Q4_K_M certified for an 8 GiB box. Both were
  later measured on the same 120 items (PREREG R6: exact 47.5% Q8_0, 45.8% Q4_K_M; report §3.2). The live slice prints
  the recorded MLX result next to each live draft so that differences are visible. Quantisation can change outputs: our
  own MLX g64 4-bit build (not the DWQ build used here) distorted verdicts on another task; in the parity battery it
  agrees with the bf16 DPO checkpoint on 548 of 648 decisions, the DWQ build on 610.
- **Retry count, corrected.** As run on the Air, the lock (raw text, which counted the 8B's ’ -> ' as an edit) sent 25 items
  to a retry. Under the corrected, apostrophe-normalised lock that the reported numbers use, 14 would have been retried
  (12 of them in the shipped lane; the other 2 go to the code lane). No retry fixed anything: 0/25 as run, 0/14 corrected.
  Greedy decoding repeats the first answer (22/25 and 11/14 identical).
- **results.md wording.** The Air run retried 25 items as-run (`raw/gleich_air.log`: 25 FLAG lines). The "14 retries"
  in results.md is the count under the corrected lock. The setup sentence "150 arm-A items (plus 14 retries)" should
  read 25 for the timing. The RM edit-F1 gap is +27.24 exactly; "+27.3" subtracts the rounded values. Both are in
  `eval/results/fedlex.json["notes"]`, and neither moves a headline.
- **Small samples.** 26 acts for FR/IT, items clustered by act, and n = 150 for the flip adjudication.


## 8B vs 70B on the same items (PREREG R5)

The 70B ran the same shipped lane on the same 120 FR/IT paragraphs through the development gateway (82 model calls, all
served by `swiss-ai/apertus-v1.5-70b`; $0.03). Every unflagged non-exact draft of each run was labelled by a blind Claude
annotator (`eval/labels/fedlex_shipped_unflagged.tsv`, `eval/labels/fedlex70b_shipped_unflagged.tsv`).

| | exact | flagged | ready | ready drafts with a real error | with German left / stale |
|---|---|---|---|---|---|
| 8B (MLX DWQ, recorded) | 60 | 38 | 82 | 0 | 4 / 4 |
| 70B | 58 | 28 | 92 | 2 | 5 / 1 |

Neither meets the pass rule; under the pre-registered decision the Fedlex lane stays on the 8B and every draft goes to
review. Numbers: `eval/results/fedlex_compare.json` (`score.fedlex_compare`).
