# Pre-registration

Each rule below is fixed **before** the run it governs. Failed runs are reported, never dropped.

- **R0 and the guard freeze** predate this repository: they were written in the research log before the fresh 2025 run
  (verbatim excerpt with the log's sha256: `docs/research/freeze-record.md`). This repository was created after that run;
  `freeze.json` and `tools/freeze.py` check that the vendored files still carry the frozen hashes.
- **R1–R7** were committed here before their runs. `run_times.json` lists the first and last model call of each run from
  the development gateway's append-only ledger next to the commit times of this file (R2: committed 18:01 UTC, first call
  18:27 UTC; R5: committed 18:20 UTC, first call 18:27 UTC, 9 Oct 2026). R1 ran on GitHub Actions CPU runners after
  its commit (results log below).

## R0. Pass rule for a drafting lane (frozen 9 Oct 2026, before the fresh 2025 run)

Applies to the full pipeline (whole-paragraph locked rewrite, frozen guard stack, at most one re-ask) on a held-out set.
Unflagged outputs are hand-checked in full; a seeded sample of 20 flagged outputs (seed 20261009) is hand-checked to
estimate wasted review.

| Metric | Threshold |
|---|---|
| Unflagged real meaning errors | ≤ 1% of items |
| Unflagged stale + untranslated outputs | ≤ 2% of items |
| Exact match vs rules-only | ≥ +5 points |
| Flagged | ≤ 70% of items |

History under this rule (all reported): dev 120 (guards v2, in-sample) pass; out-of-sample 242 (guards v2) **FAIL**
(untranslated 4.1%); fresh 2025 set of 166 (guards3, frozen before outputs existed) **PASS**.

## R1. M1/M2: is the 8B sufficient for the SL lane? (frozen 9 Oct 2026 evening, before any 8B run on the fresh set)

- Run: Apertus 8B GGUF builds (Q4_K_M first, then Q8_0) on the fresh 166 with the shipped pipeline (frozen code,
  guards3, at most one re-ask), greedy, the 8B digit/number-word logit mask on. Runner: GitHub Actions CPU (not a team
  machine).
- Labels: every unflagged non-exact output plus a seeded 20 flagged (seed 20261009); two blind Claude annotators, a third
  blind Claude annotator breaks every disagreement (majority of three); Cohen's κ reported; no human labels. (Amended
  before any R1 run: the original text had the team lead adjudicating.)
- Decision: if any 8B build meets R0 on the fresh 166, the SL default becomes the local 8B. Otherwise the 70B lane stays
  the SL default and the 8B stays the air-gapped fallback in which **every** item is marked for review.
- Kill / report rule: if Q4_K_M is more than 10 points below the MLX DWQ dev reference on exact match, report it and keep
  DWQ as the 8B dev reference.

## R2. M3: run-to-run stability of the 70B lane (frozen 9 Oct 2026 evening, before the rerun)

- Run: the same 166 items, same frozen pipeline, through the development gateway with `seed=1` (a distinct request, so
  the provider's response cache cannot answer), temperature 0, plain user messages only. Every response's `model` field
  is logged; any response not served by `swiss-ai/apertus-v1.5-70b` is discarded and counted.
- Reported (no threshold): identical final output rate; flag agreement (κ); exact, edit-F1, chrF vs rules with the
  paired cluster bootstrap; flag rate.
- Labels: unflagged non-exact outputs that differ from the original run's labelled outputs, by the R1 protocol.
- The headline claim "R0 passes on the fresh set" is stated as stable only if the rerun also meets all four criteria;
  otherwise the report states that it passed on one run and failed on the rerun, with both sets of numbers.

## R3. M6: backtest over the monthly SL snapshots (frozen 9 Oct 2026 evening, before the backtest code ran)

- Lag count: for each DE limitation change between consecutive usable snapshots (2026: 19.02, 04.03, 01.04, 01.06,
  01.07, 01.08, 01.09, 01.10, 06.10; May excluded for the publisher bug), record whether FR and IT changed in the same
  step, and if not, in which later snapshot (or never within the window). Report counts, not rates over an unknown
  population.
- Targeted run on the 5 hand-verified divergences (Nemluvio, Diaphin, etanercept ×3, Cresemba, Dupixent ×4): for each,
  record (a) whether the divergence is present in the earliest available capture (Jun 2025 XML) or first appears at a DE
  change inside the window, and (b) what the shipped guards say about the current FR/IT text against the DE (the
  numbers-not-in-DE check), and, where a DE change inside the window exists, what Gleichlaut's draft would have been.
- If no lag is found, the report says so and relies on the 5 verified divergences.

## R5. Fedlex: 8B vs 70B on the same 120 FR/IT paragraphs (frozen 9 Oct 2026 night, before any 70B Fedlex call)

Background (measured before this rule): the shipped Fedlex lane (8B MLX DWQ, code lane first, lock + slot guard +
frozen G1–G4; the guard choice was made after seeing these outputs, so DEV) flags 38/120; a blind annotation of its 25
unflagged non-exact drafts finds 0 real meaning errors but 4 with German left (EFZ for CFC/AFC) and 4 stale, i.e.
8/120 = 6.7% unflagged stale + untranslated, above R0's 2% limit. (Background line corrected from "3 stale, 7/120" to the label file's count before any 70B call.)

- Run: the same 120 FR/IT items, the same vendored research loop (`fed.lane.fed_draft`), with Apertus 70B through the
  development gateway (plain user messages, temperature 0, served model checked on every call), no digit mask (API).
- Labels: every unflagged non-exact 70B draft, by a blind annotator with the protocol used for the 8B drafts.
- Decision: the Fedlex default becomes the 70B only if it meets R0 on these items (with the in-sample caveat stated);
  otherwise the Fedlex lane stays 8B and every Fedlex draft goes to review ("ready" = pre-checked, not publishable).
  Either way, both rows are reported side by side.

## R6. Fedlex with the shipped 8B GGUF builds (frozen 10 Oct 2026, before any GGUF Fedlex run)

R5 compared the 70B with the 8B MLX DWQ build. The 8B that ships is a GGUF (Q4_K_M by default, Q8_0 as an option), so
the statute claim must be measured on it.

- Run: the same 120 FR/IT Fedlex items, the shipped Fedlex lane unchanged (`fed.lane.fed_draft`: code lane, else arm A;
  lock + slot guard + G1–G4; no digit mask, as in R5), GGUF Q4_K_M and Q8_0, greedy, on GitHub Actions CPU runners
  (`m1` workflow, `suite=fed`). Not on a team machine.
- Labels: every ready non-exact draft, by the R1 protocol (two blind Claude annotators, a third breaks disagreements).
- Reported (no new threshold): exact, flagged, ready classes, next to the R5 rows (8B MLX, 70B).
- Decision: as R5. Every statute draft goes to review unless a GGUF build meets R0 on these items (in-sample caveat). If a
  GGUF build is more than 10 points below the 8B MLX build on exact, the README and report say that statutes were
  measured on the MLX build and report the GGUF as weaker; they do not claim the GGUF for statutes.

## R7. The first shadow month (01.09.2026 → 01.10.2026) with all three models (frozen 10 Oct 2026, after the Q4_K_M run, before the Q8_0 and 70B runs)

The shadow workflow drafted the month's 52 FR/IT items from the public feed with the default Q4_K_M build (run
38002803918; `data/shadow/20260901-20261001/q4_k_m/`): 8 routed to a translator, 41 compared with BAG's published text,
3 identical, 4 ready, 37 flagged. Its outputs were looked at before this rule was written.

- Runs: the same items (`data/shadow/20260901-20261001/items.json`), the same routing and pipeline: Q8_0 through the
  shadow workflow (`build=q8_0`, CPU runners, `--network none`), and the 70B through the development gateway
  (`tools/run_shadow70b.py`; temperature 0, plain user messages, served model checked on every call).
- Labels: every ready draft that differs from BAG's published text, of all three runs, pooled and shuffled, by the R1
  protocol (two blind Claude annotators, a third breaks disagreements).
- Reported (no threshold: one month, 41 compared items): identical, ready, flagged, and the classes of ready drafts, per
  model, side by side.
- Use: descriptive. It does not change the defaults set under R1. Any ready draft labelled REAL, stale or German is named
  in the report next to the R1 result.

## R9. Second CPU run of the certified Q8_0 build, with call recording (frozen 10 Oct 2026, before the run)

The R1 (M2) Q8_0 run logged token counts and timings per call but not the requests or the response texts, so `make run`
could re-score it but not re-execute it. This run records every call.

- Run: the same 166 items, the same frozen pipeline (guards3, at most one re-ask), the same GGUF Q8_0 file (sha256 as in
  R1), greedy, the digit / number-word mask on, on GitHub Actions CPU runners (`m1` workflow, `build=q8_0`, `suite=sl`,
  `name=rerun`). Every call is written as a hash-addressed entry keyed on the request sent (model, message, max_tokens,
  temperature; the mask acts on generation and is not part of the request) into `data/cache/responses_8b/q8_0/`; the
  records go to `data/runs/8b_q8_0_fresh166_g3_rerun.jsonl`. The certified run is not overwritten.
- Labels: every ready non-exact draft not identical to an already-labelled output, by the R1 protocol.
- Reported (no new threshold): identical final outputs vs the certified run, flag agreement (κ), and whether R0 holds on
  the rerun. `make run` re-executes the rerun from the recorded calls.
- Use: descriptive. It does not change the R1 decision or the certificate; a rerun that fails R0 is reported next to the
  R1 result, as R2 does for the 70B.

## R8. The failure-mode tests on the shipped 8B build (frozen 10 Oct 2026, before any of these runs)

A juror from the Apertus team noted that several rows of "where Apertus fell short" (`docs/failure-modes.md`, report
§3.3) were measured on our MLX 4-bit DWQ build (548 of 648 parity decisions agree with bf16), not on the GGUF Q8_0 that
ships (638 of 648). R8 re-runs every one of those tests whose prompts and data we have on the shipped build.

- **Build and runner.** GGUF Q8_0 (sha256 `dea904ad…202d`, URL and hash in `.github/workflows/m1.yml`),
  llama-cpp-python 0.3.35 in process (`backends.LlamaCpp`, the GGUF's own chat template, greedy, temperature 0), on
  GitHub Actions `ubuntu-latest` CPU runners (`fm` workflow), sharded and resumable, every raw response kept. Not on a
  team machine. A smoke run of at most 2 items per test may precede the full run; its outputs are not used.
- **Same prompts, same loops.** The loops run from the research source itself (by `ast`, as `core.py` does), with only
  the model call and token counting injected (token budgets use the GGUF tokenizer's counts where the original used the
  MLX tokenizer's). Research files that are not yet in this repository are vendored byte-identical with their sha256
  (`src/gleichlaut/fm/research/`).
- **Digit / number-word logit mask:** on only where the original 8B arm had it: window-only edit (`frozen/s2/s2.py:134`
  passes the language to `gen`, which adds the mask, s2.py:58-66) and the whole-paragraph rewrite with retry
  (`frozen/s2/s2b.py:55-58`). Off for free translation (s2.py:150 calls `gen` without a language), equivalence judging
  and operator typing (forced-choice log-probabilities without any mask in `round7b/spike7b.py` and
  `dreiklang/scripts/s1.py`).

| Test | Items | Prompt and loop (source) | Measured (no threshold) | MLX 4-bit result it sits beside |
|---|---|---|---|---|
| T1 free translation of the new German | dev 120 (`data/items/items_dev.json`) | `PF`, `run_3`: `frozen/s2/s2.py:108-110`, `145-152` | exact, edit-F1, chrF (`frozen/s2/score2.py:44-68`, arm 3, as `score.score_naive`) against rules-only; the lexicon flip counter (score2.py:50: items whose negation/modal/number counts differ from BAG's text). Labels: a seeded 20 of the flagged-by-counter items (`random.Random(20261009)`, keys sorted) by the R1 protocol, classes real flip / minor / equivalent; real flips extrapolated to all counter hits | 0.0% exact, edit-F1 28.2, chrF 71.2; counter on 78 of 120; 2 real flips in a seeded 20 |
| T2 window-only edit (span obedience) | dev 120, 226 windows | `PW`, `run_2`: s2.py:94-106, `118-142` | windows disobeyed: output longer than the old window + 1.5 × the German insertion + 30 characters (the rule of `docs/research/rescue70b-gleichlaut.md` A; on the recorded runs it gives exactly 165/226 for the 8B MLX and 183/226 for the 70B); exact, edit-F1, chrF, flagged (score2 arm 2) | 165 of 226 (73%); exact 5.8%, chrF 84.5, flagged 81.7% |
| T3 equivalence judging, yes/no | the 9 known Fedlex divergences + 36 controls (`round7/fedlex_items.json`, vendored) | `PAIR["de"]`, `pair_score`: `round7b/spike7b.py:67-72`, `94-103` (= `rescue70b/fx/fx.py:11-14`, `24-25`): DE–FR, DE–IT, FR–IT, both orders, 270 prompts | (a) generation, at most 8 tokens, parsed and localised as `fx.py:17-19`, `31-48`: hits /9, false flags /36, "Nein" answers /270; (b) the log-probabilities of "Ja"/"Nein" at the first answer position of the same call (the forced choice of spike7b.py:100), scored by `round7b/analyze7b.py`: hits /9 and false flags /36 at 0.5, item AUROC (both orders and each order), argmax localisation /9 | 8B (logprob): 0 / 0, AUROC 0.81 (0.82 / 0.62 by order), argmax 6 of 9; 70B (generation): 0 / 0, 2 "Nein" of 270 |
| T4 operator typing of numeric conditions | Dreiklang: 885 prompts over 40 limitations × 3 languages (vendored with gold) | `INSTR`, `TAIL`, `PREFIX`, `OPTIONS`, `score_item`: `dreiklang/scripts/s1.py:16-42`, `67-117` (41 options as summed token log-probabilities after "Antwort:") | operator and subject accuracy of the top option over all 831 gold conditions; `correlation.py` on held-out (triples wrong in all three languages, identical wrong labels, phi), with τ re-fitted on dev by `analyze.py:fit_tau` (the original protocol) | operator 296 of 831 = 35.6%, subject 71.6%; 53 of 77 wrong in all three, 24 identical |
| T5 greedy self-correction retry | dev 120 | `PA`, `RETRY`, `run`: `frozen/s2/s2b.py:72-86`, `98-123` | first drafts failing the lock check, and how many the one retry fixes; also exact and flagged with guards3, no re-ask (the S2b row), ready non-exact drafts labelled by the R1 protocol | retry fixed 0 of 26; flagged 85.0%, 1 ready draft reverses a meaning |

- **Already recorded on the shipped build (seen before this rule, re-scored, no new run):** the R1 Q8_0 run on the
  fresh 166 retried 40 first drafts and the retry fixed 0; the guarded re-ask was sent for 100 and kept 1
  (`data/runs/8b_q8_0_fresh166_g3_final.jsonl`). Reported next to T5.
- **Not re-run:** the 70B rows (served by Public AI, not a build we choose), and the back-translation and 4-way label
  variants of the equivalence test (not in the table).
- **Labels:** by `eval/labels/PROTOCOL.md` (two blind Claude annotators on a shuffled worklist with neutral ids, a third
  on every disagreement; no human labels).
- **Reporting rule:** each Q8_0 number is reported side by side with the MLX number. In the headline table of
  `docs/failure-modes.md` and report §3.3 a row's MLX number is replaced by the Q8_0 number (MLX kept in parentheses)
  only where the shipped build was measured; rows not measured keep their MLX label. No threshold, no decision attached:
  whatever the shipped build does, better or worse, is what the table says. Scoring is deterministic from the recorded
  outputs (`replay` writes `eval/results/failure_modes_q8_0.json`).

## R10. A second, prospective shadow month (01.08.2026 → 01.09.2026) under R0 (frozen 10 Oct 2026, before any drafting)

A juror asked for a second month on data the team has not drafted, under a rule written in advance. Written before
the month's items were mined in a run directory, before any model saw them, and before anyone read their published
FR/IT.

- **Month.** The most recent pair of consecutive first-of-month BAG SL feeds not drafted yet (`gleichlaut feeds`,
  10 Oct 2026: 20260801, 20260901, 20261001 published; 20261006 is a mid-month feed, not a month, and is left to the
  scheduled run): **from 20260801 to 20260901**. Items: what the shadow workflow's plan job mines from the two public
  feeds (`gleichlaut month --fetch --dry-run`), unchanged, copied to `data/shadow/20260801-20260901/items.json`.
- **Seen items.** The dev 120 contain 10 items from this snapshot pair and the out-of-sample 242 may contain some. Items
  whose (lang, de_old, de_new) equals an item of `data/items/items_{dev,oos,fresh}.json` are counted as "seen"; every
  number below is reported for the whole month and, beside it, for the unseen remainder. The verdict line is the whole
  month (the same item definition as R7).
- **Models, frozen pipeline.** No change to the pipeline, guards, routing or prompts (frozen code as of this commit).
  (a) Apertus 8B GGUF Q8_0, the default build, through the shadow workflow (`gh workflow run shadow.yml -f
  from=20260801 -f to=20260901 -f build=q8_0`; GitHub Actions CPU, offline image, `--network none`, build certificate
  gate) → `data/shadow/20260801-20260901/q8_0/`. (b) Apertus 70B through the development gateway
  (`tools/run_shadow70b.py 20260801-20260901`: plain user messages, temperature 0, served model checked on every call),
  responses recorded only in the run's own `70b/responses/` → `data/shadow/20260801-20260901/70b/`. (c) The no-model
  start (rules only, `gl2.rules`) on the same items. Nothing runs a model on a team machine.
- **Labels.** Every ready draft of (a) and (b) that differs from BAG's published text, pooled and shuffled, by the R1
  protocol (`eval/labels/PROTOCOL.md`: two blind Claude annotators, the second in reverse order; a third on every
  disagreement or any REAL) → `eval/labels/shadow_20260801_20260901_ready.tsv`. No flagged sample (as R7).
- **Reported, per model, side by side with rules-only.** Items, routed to a translator, compared, identical, ready,
  flagged, ready classes; and the four R0 criteria, with n = the month's drafts compared with BAG's text (status ≠
  human, as R7): unflagged REAL ≤ 1% of n; unflagged stale + German ≤ 2% of n; exact (identical) minus rules-only
  exact ≥ +5 points on the same n; flagged ≤ 70% of n. Each criterion is stated as holds / fails; a model "meets R0
  this month" only if all four hold. Also reported: the share sent to review counting the routed items as flagged.
- **Use.** Descriptive: one month, no change to the defaults set under R1, no change to the pipeline after seeing it. A
  failed criterion is reported as failed in the README, the technical report and here. Scored by
  `score.shadow_month("20260801-20260901")` in `replay` (`eval/results/shadow_20260801_20260901.json`).

## R11. Annotator sensitivity: planted meaning errors, reference shown and hidden (frozen 10 Oct 2026, before any annotation)

A juror: "'0 meaning errors in ready drafts' is a model's opinion until the annotators' error-catching rate is measured".
R11 measures how often the blind Claude annotators of `eval/labels/PROTOCOL.md` catch a known meaning error.

- **Items** (`tools/plant_sensitivity.py`, seed 20261012; its output is committed with this rule:
  `eval/labels/sensitivity_key.json` and `sensitivity_{a,b}_set{1,2}_worklist.json`; `--check` reproduces them byte for
  byte). Bases: the 66 fresh-166 items (33 FR, 33 IT) with a ready draft (70B, 8B Q8_0 or Q4_K_M run) that every existing
  label calls exact (19) or equivalent (47) with no fix needed, one draft per item. Each base appears twice: once with
  **one** planted meaning error, once untouched (true negative). Real items: 30 existing labelled drafts of other
  fresh-166 items whose final label is REAL (3), stale (12) or German (15).
- **Planted types** (definitions and patterns in the tool's docstring), mirroring the REAL class of the protocol: dropped
  condition or clause (13), and/or swap (12), negation dropped or added (12), scope widened or narrowed (8), obligation
  changed (doit/deve <-> peut/può, 7), direction or operator flipped (au moins <-> au plus, almeno <-> al massimo, à partir
  de -> jusqu'à, 7), a number of the draft changed (7). Each base gets the applicable type with the lowest count in its
  language. Confound, stated now: 34 of the 66 bases are the short boilerplate family 981f07a8, whose texts only offer
  drop, and/or and negation sites, so those three types sit almost only there; results are also reported by family.
- **Worklists.** Two sets per protocol; a base's planted and untouched copies are never in the same set (set 1: 33
  planted, 33 untouched, 15 real; set 2 the complement), no item twice in one worklist; seeded shuffle, neutral ids,
  fields as in the protocol. The key (id -> item, planted or not, type, edit) is kept apart and never shown.
- **Protocols.** (a) *as used*: the PROTOCOL.md instructions verbatim, records with `official_new`. (b) *reference
  hidden*: records without `official_new`; instructions identical except that the sentence "official_new is what the
  authorities published." is replaced by "No published version is available for these records: there is no official_new
  field." Both carry the same operational note after the instructions: "Some lines of the file are longer than 2,000
  characters; if your file viewer truncates long lines, read the file so that every line is shown in full (for example
  with cat or python3), still only this file."
- **Annotators.** Per protocol and set, two fresh general-purpose Claude subagents (8 in all), each given only a copy of
  its worklist in an otherwise empty directory; the second reads the records in reverse order. No annotator sees both
  sets or both protocols. No tie-break: recall is reported per annotator, for both and for either. No model API calls.
- **Metrics** (no threshold; deterministic from the committed merged labels `eval/labels/sensitivity_{a,b}.tsv` by
  `score.annotator_sensitivity` -> `eval/results/annotator_sensitivity.json`, re-derived by `replay`): per protocol,
  overall and per type, language, base class (exact / equivalent) and family (981f07a8 / other): planted n; caught as
  needs_fix = yes and as severe (REAL or stale) by annotator A, by B, by both and by either; false alarms on the 66
  untouched drafts (needs_fix = yes; severe); on the 30 real items, severe labels and agreement with the existing final
  label. Wilson 95% intervals over items.
- **Reporting rule.** README and technical report state, next to the "0 meaning errors" claim, the share of planted
  meaning errors labelled severe by both / by at least one annotator under (a) and under (b), whatever they are (the
  final label of the full protocol, majority of three, lies between the two). Also reported, descriptive: the 95% upper
  bound on severe errors among ready drafts divided by the both-annotator severe recall of (a). No decision attached:
  R0 and R1 outcomes are not re-opened by this rule.

## R12. House terminology in the drafting prompt (variant v3-terms) on both live months (frozen 10 Oct 2026, before any run)

An Apertus-team juror: the prompt asks for "the established terminology" without supplying it; 22 of the 25 Q8_0 ready
drafts needing a fix fail on one house term, and the new standard sentence sank both live months; that gap is in the
pipeline, not in Apertus. R12 supplies BAG's own house wording in the prompt and re-runs both live months.

- **Variant v3-terms** (`src/gleichlaut/v3terms.py`, outside `frozen/`; frozen code and hashes untouched, `freeze.json`
  unchanged). The frozen pipeline exactly as shipped (whole-paragraph locked rewrite, lock check and retry, frozen guard
  stack guards3, one re-ask kept only if every check passes, slot codes, routing) EXCEPT one added block in the drafting
  prompt, inserted between the list of German changes and the old target text: the header "BAG's established {L}
  wording in the Spezialitätenliste for terms and sentences of the German (new) text, taken from BAG's published {L}
  texts. Where the amended part contains them, use exactly this {L} wording:" and one line per entry. The lock retry and
  the re-ask format the same template, so they carry the block too. An item whose new German has no house term and no
  house sentence gets the frozen prompt byte for byte.
- **Block entries** (rules in the module docstring): (T) every termbase entry of the item's language with a house
  rendering whose German term (`termbase.HEAD_RX`) occurs in `de_new`, as "German term -> house rendering"; (S) every
  sentence of `de_new` (`emit.segment.sentences`) whose normalised key has a house sentence (`gleichlaut.house`) in that
  language, as «German sentence» -> «house wording», numbers filled in order from the German sentence (left out when the
  counts differ). Both sides are written with the prompt's own slot codes (no digit reaches the model). Entries with no
  dominant rendering are not used. Order: first occurrence in `de_new`.
- **Mining source per month (no leakage).** The house wording is mined by the unchanged mining code (`gleichlaut
  termbase --date D`, which also writes the house sentences) from the month's OLD snapshot only: **1 Aug -> 1 Sep 2026:
  snapshot 20260801; 1 Sep -> 1 Oct 2026: snapshot 20260901** (the `gleichlaut.sl.ingest` output of BAG's public feeds of
  those dates, in the research hist directory the shadow runs used), never from a snapshot that contains the month's
  published FR/IT. Files: `data/termbase/r12/{termbase,house_sentences,shared_words}_<D>.json` and the TBX (64 house
  terms and 60 house sentences per snapshot). Disclosed: the mining rules (`termbase.HEADS`, `REJECT`, `DROP_VARIANTS`,
  the house-sentence thresholds) were fixed on the 6 Oct 2026 snapshot; they choose German terms and remove fragment
  renderings, and no wording in a block comes from any snapshot but the month's old one. One review exclusion was added to
  `termbase.REJECT` before any run, by the existing review rule (a fragment, not a rendering): it "Verlaufskontrolle" ->
  «effettuati», a house entry only in the 20260901 snapshot; the shipped 6 Oct termbase is unchanged by it. The French
  new standard sentence ("Der Indikationscode dieser Limitierung ist an den Krankenversicherer zu übermitteln.") has no
  dominant French rendering in either old snapshot (10 of 23 and 20 of 46 limitations), so French items get its terms,
  not the sentence; Italian items get the sentence (house in both).
- **Committed with this rule:** `eval/prereg/r12_blocks.json` (`tools/r12_terms.py blocks`; `--check` reproduces it byte
  for byte): per month and drafted item, the block, its entries and the sha256 of the exact first prompt of the frozen
  pipeline and of the variant. Aug: 22 drafted, 22 model calls, 19 prompts changed; Sep: 44 drafted, 40 model calls,
  40 prompts changed.
- **Runs** (same items `data/shadow/<from>-<to>/items.json`, same routing). (a) Apertus 8B GGUF Q8_0 through the shadow
  workflow on GitHub Actions CPU runners (`gh workflow run shadow.yml -f from=<from> -f to=<to> -f build=q8_0 -f
  variant=v3-terms -f shards=6`; offline image, `--network none`, build certificate gate; the committed items, no feed
  re-mined) -> `data/shadow/<from>-<to>/v3_terms_q8_0/`. (b) Apertus 70B through the development gateway
  (`tools/run_shadow70b.py <from>-<to> --variant v3-terms`: plain user messages, temperature 0, served model checked on
  every call; responses only in the run's own `v3_terms_70b/responses/`, never `data/cache/responses`) ->
  `data/shadow/<from>-<to>/v3_terms_70b/`. Nothing runs a model on a team machine. The variant is not certified, so its
  records carry status "flagged" with a review reason; `guard_status` keeps the frozen guards' ready / flagged verdict, and
  R12 scores that verdict (for the frozen runs status and guard_status are the same).
- **Labels.** Every v3-terms draft that the guards mark ready and that differs from BAG's published text, both months and
  both models, pooled, one record per distinct (item, draft), shuffled with seed 20261015, neutral ids, R1 protocol
  (`eval/labels/PROTOCOL.md`: two fresh blind Claude annotators, the second in reverse order, the R11 operational note on
  long lines; a third on every disagreement on needs_fix or class, or any REAL) -> `eval/labels/r12_terms_ready.tsv`.
  The frozen runs keep their R7 / R10 labels; nothing is relabelled.
- **Reported, per month and per model, frozen beside v3-terms:** items, compared n (drafts with BAG's published text,
  status != human), identical, ready, flagged, ready classes, and the four R0 criteria with n = compared: unflagged REAL
  <= 1%; unflagged stale + German <= 2%; identical minus rules-only identical >= +5 points on the same n; flagged <= 70%;
  each holds / fails, "meets R0" only if all four hold. The frozen columns are computed by the same code from the R7 / R10
  records and labels (R7 gave no R0 verdict; it is computed here only for the side-by-side). Also reported: prompts
  changed; for unchanged prompts, whether the output equals the frozen run's; the number of v3 drafts identical to BAG's
  text that the frozen run did not get, and the reverse.
- **Decision, stated now.** If v3-terms meets R0 on a live month where the frozen variant failed, it is reported as a
  candidate for the next held-out test; it does not replace the frozen default without a new held-out run. If it does
  not, that is reported as failed, criterion by criterion. Either way the shipped default stays the frozen pipeline; the
  variant is not changed after any output is seen. Scored by `score.r12_terms()` in `replay`
  (`eval/results/r12_terms.json`).

## R13. Fully blind relabel of the headline 70B fresh-166 run (frozen 10 Oct 2026, before any annotation)

A juror: the first labels of the headline run (`eval/labels/fresh166_unflagged.tsv`, `fresh166_flagged20.tsv`) are the
research labeller's, who knew each draft's guard verdict, while the 8B runs (R1) were labelled fully blind under
`eval/labels/PROTOCOL.md`. R13 labels the same 70B drafts under that protocol.

- **Items.** Every ready (unflagged) non-exact draft of the 70B fresh-166 run (`data/runs/70b_fresh166_g3_final.jsonl`,
  flag re-computed with guards3, exact by the frozen scorer: 49 drafts) plus the same seeded 20 flagged drafts as R1
  (`random.Random(20261009).sample` of the sorted flagged keys; the same 20 as `fresh166_flagged20.tsv`): 69 records.
  The draft is the run's final output; nothing is re-run, no model is called.
- **Worklist** (`tools/blind_relabel_70b.py`, deterministic, `--check` reproduces it byte for byte): neutral ids
  `H00`…, order shuffled with `random.Random(20261013)`, fields only `id, lang, de_old, de_new, tgt_old, draft,
  official_new` (`official_new` = BAG's published text). Ready and flagged drafts are mixed and not marked; the guard
  verdicts, the model, the run and the research labels are not in it. The id -> key map (`fresh166_blind_key.json`) is
  kept apart and never shown.
- **Protocol** exactly `eval/labels/PROTOCOL.md`: two fresh general-purpose Claude subagents, each given only a copy of
  the worklist in an otherwise empty directory, with the verbatim instructions plus the one operational note of R11 (long
  lines: read the file so that every line is shown in full, still only this file); the second reads the records in
  reverse order. A third fresh blind agent labels, in a new worklist (ids `T00`…, shuffled with
  `random.Random(20261014)`, same fields), every record where the two disagree on `needs_fix`, disagree on the class of
  a ready draft, or where either says `REAL`. No human labels, no model API calls.
- **Merge** (`eval/labels/fresh166_blind.tsv`, the R1 layout `key, A_fix, A_class, B_fix, B_class, T_fix, T_class,
  final_fix, final, note_A`; the raw annotator files by neutral id are committed beside it): `final_fix` = majority of
  three on needs_fix (A's when A and B agree); `final` = the class shared by at least two of the three, otherwise the
  third's; with no third label, the agreed class, or for a flagged draft whose two classes differ without a REAL, the
  more severe of the two (REAL > stale > german > minor > cosmetic > preexisting > equivalent > exact).
- **Outcomes** (no threshold; deterministic from the committed files by `score.blind_relabel_70b` ->
  `eval/results/fresh166_blind.json`, re-derived by `replay`): (1) agreement on needs_fix and Cohen's κ between the two
  blind annotators over the 69 records; (2) severe errors (REAL, stale, german) among the ready drafts by the blind
  majority, as counts and keys with notes, and the resulting R0 rows for the 166 items; (3) agreement of the blind
  majority with the existing research labels: needs_fix over 69 (research: equivalent / preexisting / good = no fix) with
  κ, class over the 49 ready drafts, and the severe sets.
- **Reporting rule, stated now.** The headline numbers (R0 pass on the fresh 166, 0 meaning / 0 stale / 0 German among
  ready drafts by the research labels) are not replaced. If the blind majority finds any severe error among the ready
  drafts, it is reported next to the headline 0 in the README and the technical report, with its key and class, whatever
  it is; if it finds none, that is stated beside the headline as the blind confirmation.

## R4. Post-freeze changes

No change to `frozen/` after this commit. Any guard change needs a new held-out run before a claim; anything measured on
data the change was designed on is labelled "dev" in every table.

## Results log (appended after each run; rules above unchanged)

- **R2 (M3), 9 Oct 2026:** rerun with seed 1 passes R0 (+12.0, 58.4% flagged, 0 / 0 / 2 of 166); 69.9% identical outputs,
  flag κ 0.963 (`eval/results/m3.json`).
- **R5, 9 Oct 2026:** Fedlex 70B not better than 8B (exact 48.3% vs 50.0%); neither passes R0; statutes stay on the 8B and
  every statute draft goes to review (`eval/results/fedlex_compare.json`).
- **R3 (M6), 9 Oct 2026:** no lag found (French and Italian updated in the same step for 208 of 216 German changes);
  all 10 divergent limitations predate the window (`data/backtest/`).
- **R1 (M1), 9 Oct 2026:** Apertus 8B GGUF Q4_K_M on CPU (GitHub Actions, 8 shards), same pipeline, fresh 166: exact
  16.9% (+10.8 [4.8, 17.5]), flagged 63.9%, ready drafts 0 meaning / 1 stale / 2 German (1.81%) by two blind
  annotators and a third tie-breaker: **PASS**. Decision as pre-registered: the SL default becomes the local 8B
  (`eval/results/m1_q4_k_m.json`).
- **R1 (M2), 10 Oct 2026:** Apertus 8B GGUF Q8_0 on CPU (GitHub Actions, 8 shards), same pipeline, fresh 166: exact
  17.5% (+11.4 [4.8, 18.7]), flagged 62.7%, ready drafts 0 meaning / 0 stale / 0 German (two blind annotators, needs-fix
  κ 0.789, a third broke 7 disagreements): **PASS** (`eval/results/m1_q8_0.json`, build certificate
  `eval/certificates/8b-q8_0-fresh166.json`). Q4_K_M stays the default build (superseded on 10 Oct 2026, see "Default build" below) (8 GiB box); Q8_0 is the certified option
  for a 16 GiB box (`BUILD=q8_0`). Paired against the 70B (`eval/results/size_compare.json`): exact 17.5% each, edits
  saved 33.1% vs 42.4% (difference 9.3 points, 95% CI [−1.3, 20.2]).
- **R6, 10 Oct 2026:** the shipped Fedlex lane with the GGUF builds on the 120 Fedlex items (GitHub Actions CPU, 8 shards
  each): exact 45.8% (Q4_K_M) and 47.5% (Q8_0) against 50.0% for the 8B MLX build, within the 10-point margin; ready
  drafts 4 real / 4 stale / 6 German (Q4_K_M) and 4 / 3 / 6 (Q8_0), by two blind annotators and a third on 6
  disagreements (`eval/labels/fedlex_gguf_unflagged.tsv`). Neither passes R0. Decision as pre-registered: statutes run
  the shipped 8B GGUF and every statute draft goes to review (`eval/results/fedlex_compare.json`).
- **R7, 10 Oct 2026:** the first shadow month, 01.09 → 01.10.2026 (52 items, 41 compared with BAG's text, 8 routed to a
  translator). Identical drafts 3 / 3 / 4 and flagged 90.2% / 92.7% / 82.9% (Q4_K_M / Q8_0 / 70B); no-model start 0 of
  41. Ready drafts 4 / 3 / 7, none with an error (10 non-identical ready drafts, blind labels: 6 cosmetic, 4 equivalent;
  the two annotators agreed on all 10). 32 of the 41 items add one new standard sentence
  (`eval/results/shadow_20260901_20261001.json`).
- **R5 relabel, 10 Oct 2026:** after a juror noted that the R5 arms (8B MLX, 70B) were labelled by one annotator while
  the R6 arms had two plus a tie-breaker, the R5 ready drafts were relabelled under the R6 protocol, pooled and blind
  (`eval/labels/fedlex_r5_relabel_unflagged.tsv`). 8B MLX unchanged (0 real, 8 stale or German); 70B 2 real and 5 stale
  or German (was 6). Neither passes R0; the decision is unchanged. The first labels stay in the results as
  `first_annotation`.
- **Default build, 10 Oct 2026:** R1 decides that the SL default is the local 8B; it does not name a build. After M2,
  with both builds passing R1, the default changed from Q4_K_M (chosen when only M1 existed) to Q8_0: 0 / 0 / 0 among
  its ready drafts against 0 / 1 / 2, and 12.2 more points of edits saved ([6.0, 19.9], `eval/results/size_compare.json`).
  This choice was made after seeing both results; Q4_K_M stays certified for an 8 GiB box.
- **R9, 10 Oct 2026:** the certified Q8_0 build again on the fresh 166 (GitHub Actions CPU, 8 shards, run 38042349395),
  every call recorded: 166 of 166 final outputs and 294 of 294 raw responses byte-identical to the certified run, flag
  agreement 166 of 166 (κ 1.000); R0 holds on the rerun (the same numbers as R1 (M2); no new labels were needed, every
  ready draft is exact or identical to an already-labelled output). `make run` re-executes it from
  `data/cache/responses_8b/q8_0/`: 294 requests rebuilt and found, 0 misses, 0 records differing
  (`eval/results/m2_rerun.json`).
- **R8, 10 Oct 2026:** the failure-mode tests on the shipped Q8_0 GGUF, GitHub Actions CPU runners (`fm` workflow, run
  38043642490, 58 shards, all succeeded; a smoke run 38042995294 of 1 item per test before it, not used). Q8_0 beside
  the MLX 4-bit run, each scored by its research scorer, which reproduces every recorded MLX and 70B number from the
  recorded outputs (`eval/results/failure_modes_q8_0.json`). T1 free translation: 0 of 120 exact (MLX 0), chrF 73.5
  (71.2), counter hits 70 (78); blind labels of the seeded 20: 6 real meaning changes (MLX hand check: 2 of 20), 2 minor,
  12 equivalent (annotators agreed on 19; the third decided a three-way split as REAL), about 21 in 120 extrapolated (8).
  T2 window-only: 121 of 226 windows disobeyed = 54% (MLX 165 = 73%; 70B 81%), exact 5.8% = rules, chrF 86.8 against
  88.8 for rules-only, 0 model-written digits. T3 yes/no equivalence: generation 0 of 9, 0 of 36 false flags, "Nein" in 1
  of 270 (70B: 0, 0, 2); log-probabilities 0 hits and 0 false flags at 0.5, item AUROC 0.77 (0.74 / 0.78 by order),
  argmax 3 of 9 (MLX 0.81, 0.62 / 0.82, 6 of 9). T4 typing: operator accuracy 327 of 831 = 39.4% (MLX 35.6%), "≥" the
  top operator for 619; held-out triples wrong in all three languages 53 of 77 (53), phi 0.78–0.85 (0.51–0.61). T5:
  greedy retry fixed 1 of 23 (MLX 0 of 26); the S2b row on dev 120: flagged 82.5% (85.0%), exact 17.5% (15.0%), 21
  ready drafts, none with a meaning error (two blind annotators agreed on all 7 non-exact: 5 cosmetic, 1 minor,
  1 equivalent; MLX: 1 REAL among 18). Already recorded (R1): retry 0 of 40, re-ask kept 1 of 100. As pre-registered, the
  8B numbers in `docs/failure-modes.md` and report §3.3 are now Q8_0 with MLX in parentheses; free translation is worse
  on the shipped build by this read, span obedience, operator typing and the S2b row are better, the yes/no answer is the
  same, and the log-probability ranking is weaker but no longer order-dependent.
- **R11, 10 Oct 2026:** annotator sensitivity, 8 fresh blind Claude annotators (two per worklist, two worklists per
  protocol). Of 66 planted meaning errors, both annotators labelled 66 REAL under (a) reference shown and 66 under (b)
  reference hidden (Wilson 95% [94.5, 100] each; every type 7–13 of 7–13); false alarms on the 66 untouched drafts: 0
  severe in either protocol, 1 needs-fix call (minor) under (a). Real items: stale 12 of 12 and German 14 of 15 severe by
  both; of the 3 earlier REAL labels both agree on 1 (either: 2 under (a), 3 under (b)). The 95% bounds on severe errors
  among ready drafts are unchanged by the recall (5.5% 70B, 5.8% Q8_0) (`eval/results/annotator_sensitivity.json`).
- **R10, 10 Oct 2026:** the second shadow month, 01.08 → 01.09.2026, pre-registered (commit 70b75e9, 12:52 UTC)
  before the plan job mined it. Q8_0: shadow run 38053562475 (6 CPU shards, all succeeded, build certificate
  8b-q8_0-fresh166 verified on every shard, 44 calls); 70B: development gateway, 48 calls, all served by
  swiss-ai/apertus-v1.5-70b. 38 items, 16 routed to a translator (6 over 2500 characters, 10 rewrites over 60%), 22
  drafted and compared. Seen check: all 22 drafted items are in the dev 120 (10) or the out-of-sample 242 (12); the 16
  unseen items were all routed, so the unseen remainder has no drafts and no R0 numbers. R0 on the month (n = 22,
  no-model start 0 identical): **Q8_0 does not meet R0**: unflagged REAL 0 (holds), stale + German 1 = 4.5% (fails,
  ≤ 2%), exact 1 = +4.5 points (fails, ≥ +5), flagged 81.8% (fails, ≤ 70%). **70B does not meet R0**: REAL 0 (holds),
  stale + German 3 = 13.6% (fails), exact 0 = +0.0 (fails), flagged 81.8% (fails). Counting routed items, 30 of 34
  (88.2%) go to review with either model. Labels: 7 ready non-exact drafts (6 distinct texts; one identical draft shared
  by both models labelled once), two blind annotators agreed on all 7, no REAL, so no tie-break: Q8_0 1 german, 1
  cosmetic, 1 equivalent; 70B 2 german, 1 stale, 1 equivalent. The German left is BAG's typo "GLP1-1-Analogon" carried
  through by the number lock. 14 of the 22 add the new standard sentence also seen in September
  (`eval/results/shadow_20260801_20260901.json`). Nothing in the pipeline or the defaults changes.
- **R13, 10 Oct 2026:** the headline 70B fresh-166 run relabelled fully blind under `eval/labels/PROTOCOL.md`
  (pre-registered in commit 7551fd6 before any annotation): 69 records (49 ready non-exact + the R1-seeded 20 flagged),
  two fresh blind annotators (the second in reverse order), a third on 6 records. Needs-fix agreement 67 of 69, κ 0.892.
  Severe errors (REAL / stale / German) among the ready drafts by the blind majority: **0** (R0 holds with the blind labels:
  0 / 0 of 166; 95% upper bound 5.5% of the 66 ready drafts). Ready drafts needing a fix: 3 (one non-standard insurer term,
  "SGLT - 2" spacing twice). Agreement with the research labels on needs-fix 62 of 69 (ready 46 of 49, flagged sample 16
  of 20: 13 of the 20 flagged need no fix by each, 2 different each way); 35 of the 49 ready drafts are "preexisting" by
  the blind majority where the research labels say "equivalent" (both: no fix). The headline is unchanged
  (`eval/results/fresh166_blind.json`, `eval/labels/fresh166_blind.tsv`).
