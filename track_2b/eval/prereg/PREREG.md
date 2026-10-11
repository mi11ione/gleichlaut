# Pre-registration

Each rule below is fixed **before** the run it governs. Failed runs are reported, never dropped.

- **R0 and the guard freeze** predate this repository: they were written in the research log before the fresh 2025 run
  (verbatim excerpt with the log's sha256: `docs/research/freeze-record.md`). This repository was created after that run;
  `freeze.json` and `tools/freeze.py` check that the vendored files still carry the frozen hashes.
- **R1–R7** were committed here before their runs. `run_times.json` lists the first and last model call of each run from
  the development gateway's append-only ledger next to the commit times of this file (R2: committed 18:01 UTC, first call
  18:27 UTC; R5: committed 18:20 UTC, first call 18:27 UTC, 9 Oct 2026). R1 ran on GitHub Actions CPU runners after
  its commit (results log below).

## Index

Sections are in the order they were written (R9 before R8; R4, a standing rule, last). Outcomes are in the results log.
"Hand-checked" in R0 and R1 means read in full and labelled by blind Claude annotators (`eval/labels/PROTOCOL.md`); no
human labels were used.

| Rule | Governs | Outcome |
|---|---|---|
| R0 | pass rule for any drafting lane | 70B fresh 166: PASS |
| R1 | is the 8B enough for the SL lane (M1 Q4_K_M, M2 Q8_0) | both PASS; SL default is the local 8B |
| R2 | 70B run-to-run stability (M3) | rerun PASS |
| R3 | backtest over monthly snapshots (M6) | no translation lag found |
| R4 | no change to `frozen/` after the freeze | standing |
| R5 | statutes: 8B vs 70B on Fedlex | 70B not better; neither passes; all statute drafts reviewed |
| R6 | statutes with the shipped GGUF builds | neither passes; same decision |
| R7 | first live month, Sep 2026 (written after the Q4_K_M run) | flag cap missed; 0 errors in 14 ready drafts |
| R8 | failure-mode tests on the shipped Q8_0 | reported per test |
| R9 | second CPU run of Q8_0, every call recorded | byte-identical |
| R10 | second live month, Aug 2026, under R0 | neither model meets R0 |
| R11 | annotator sensitivity to planted meaning errors | 66 of 66 caught, reference shown or hidden |
| R12 | house wording in the prompt, both live months | more identical drafts, fewer flags; no pair meets R0; default unchanged |
| R13 | fully blind relabel of the headline 70B run | 0 severe errors among ready drafts; κ 0.892 |
| R14 | (A) audit findings relabelled by two blind annotators + a third; (B) annotator sensitivity to meaning errors inside the amended wording | (A) κ 1.000; register 17 of 27, terminology 11 of 11, lists 6 of 11 (first: 16, 8, 7); (B) 38 of 38 caught by both, 0 false alarms |
| R15 | audit round 5: operator direction, negation, number words | recall up (operator 74.5%, number word 84.0%; negation dropped 44.0%), precision 11–25%: no kind passes, all off |
| R16 | memorisation probe: could the models have seen the held-out answers | no evidence beyond the negative control (70B, 8B); probe sensitivity not shown |
| R17 | real errors BAG fixed without a German change (Claude annotators); Apertus 70B as a non-Claude annotator | 17 content changes: needs fix by both 5 (shown) / 7 (hidden), the same 4 severe; Apertus confirms all 49 findings (κ 0.000), flags 2 of 17 |
| R18 | Apertus 8B log-probability filter on the round-5 audit findings that ship off (threshold from planted copies, applied to the 31 register findings) | planted AUROC 0.955; register kept 13, 2 of 6 confirmed (15.4%): fails, the kinds stay off |
| R19 | the certified 8B Q8_0 on the identity probes (the 250 MMLU questions, the 792-cell battery): is `fp1-nes` an 8B? | MMLU 78.4% (shared model 84.4%, v1 8B 70.8%); text equal to fp1-nes in 40.7% of cells, decisions 88.6% (fp1-nes) vs 90.4% (tp2): inconclusive (O4) |
| R20 | the 6 Oct 2026 audit as frozen predictions, scored against BAG's own later corrections (an oracle that is not Claude) | pending (first scoring snapshot expected 1 Nov 2026) |
| R21 | a task-specific system message on top of the house wording (v4-system, certified Q8_0): fresh 166 (A) and both live months (B) | A meets R0 (13.9% identical, +7.8; frozen 17.5%); no live month (Aug 1 REAL, Sep flagged 70.7%): not a candidate, default unchanged |
| R22 | stricter alignment for the operator and negation module (round 5b), held half of the register and R15's held planted set | pending |

Corrections to statements of fact inside rule text (11 Oct 2026; the rules themselves are unchanged and their text below
stays as frozen):
- R6 says the shipped 8B is "Q4_K_M by default, Q8_0 as an option". That was the default when R6 was written; after R1
  (M2) the default became **Q8_0**, with Q4_K_M certified as the option for an 8 GiB box.
- R8 credits "548 of 648 parity decisions agree with bf16" to "our MLX 4-bit DWQ build". 548 of 648 is our own MLX 4-bit
  g64 build of the released checkpoint, which ran none of the R8 tests. The research arms R8 re-runs used the
  third-party `m1rkocasu/Apertus-v1.5-8B-text-MLX-4bit-DWQ`, which agrees on **610 of 648**. "bf16" is the bf16 weights
  of `swiss-ai/Apertus-v1.5-8B-DPO`, an intermediate post-training checkpoint, not the released v1.5 8B (revision not
  recorded). Sources: `docs/research/model-identity-and-quantisation.md`.

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

## R15. Audit round 5: operator direction, negation, number words (frozen 10 Oct 2026, before any of these rules is written)

Two jurors: the planted-recall v2 (`eval/results/audit_injection_v2.json`) reads flipped comparison operators and
dropped negations 0 of 200 each and number words 37.0%, and these are the legally dangerous blind spots: a "congruence
checked" stamp gives false assurance exactly there. A third juror: the register shows "IT —" for Nemluvio, where the
Italian says "quattro". R15 adds three checks to `gleichlaut.audit` and fixes how they are judged before they exist.

- **Rules (intent fixed now; lexicons and thresholds written on the dev half only).** Deterministic, stdlib, no model.
  (1) `operator`: for a value bound to a unit (R2 parse) that the German and the target both state, the direction of
  the comparison attached to it (lower bound: ≥, >, mindestens, ab, über, mehr als / au moins, plus de, supérieur à,
  dès / almeno, più di, oltre, superiore a …; upper bound: ≤, <, höchstens, bis (zu), unter, weniger als, maximal / au
  plus, au maximum, moins de, inférieur à, jusqu'à / al massimo, meno di, fino a, inferiore a …); a finding when the
  directions are opposite. Inclusive against strict of the same direction (≥ against >) is not a finding (Q5 style).
  (2) `negation`: German and target sentences aligned conservatively (monotone, on shared values and length; pairs that
  do not align are not judged); a finding when an aligned pair has a negation (nicht, kein, ohne, weder … / ne … pas,
  aucun, sans, ni, non … / non, nessuno, senza, né …) on one side only. (3) `number_word`: number words (2–12, already
  read by the number check; ordinals where safe; 1 stays unreported, R3) compared per aligned sentence, unit-bound or
  not (a number word is never a code, a year or a table cell); a value written as a word on either side that the aligned
  sentence of the other side lacks is a finding unless an existing number finding already names it. Number findings
  also get a display field with the value the aligned target passage states instead (Nemluvio: DE 8, IT 4).
- **Separation.** The new kinds are reported apart (their own list and counts). The existing kinds must not change:
  number 21, unit 0, language 1, editorial 5 (the 27-finding headline) and terminology 11, with the same ids, ranks and
  values; a test enforces it. If any existing finding changes anyway, the change is reported finding by finding.
- **Design on the dev half only** (`audit.half()`: md5 of the limitation id even = dev, as rounds 2–4): the register's
  dev limitations, and planted copies of dev limitations only (`tools/audit_inject.py --protocol r15 --half dev`, seed
  20261015). No held-half text, finding or planted copy is looked at before the freeze. The freeze is the commit of the
  round-5 block of `audit.py`; its sha256 goes into the results log. After the freeze only reporting may change.
- **Held planted recall** (`tools/audit_inject.py --protocol r15 --half held`, seed 20261016, `random.Random('20261016:
  <type>:<lang>')`). Register, execution and one-fault-per-copy as v2. Eligible: one representative per distinct text
  triple, half `held`, no finding of any kind (round-5 kinds included) under the frozen audit. 100 copies per type and
  target language (all eligible if fewer). Types: `operator` (the v2 injector), `negation_drop` (the v2 negation
  injector), `negation_add` (new: FR a finite verb among est, sont, doit, doivent, peut, peuvent, a, ont, within 60
  characters of a number in the same sentence and not already negated, becomes `n'est pas`, `ne doit pas` …; IT `non`
  inserted before è, sono, deve, devono, può, possono, viene, vengono, ha, hanno under the same conditions),
  `number_word` (the v2 injector). Detection: the v2 rules (any existing kind pointing to the place, number types as v1
  numbers), plus: `operator` an operator finding in the target language whose target operator or value lies within 30
  characters of the edit; `negation_*` a negation finding in the target language whose target sentence contains the
  edit; `number_word` a number or number_word finding with the new value on the target side or the old value on the
  German side. Reported per type and language with Wilson 95%: recall **before** (the same copies, existing kinds only)
  and **after**.
- **Register findings and precision.** The frozen audit on the 6 Oct 2026 register: the number of findings per new
  kind. All of a kind are labelled if there are at most 60, otherwise a `random.Random(20261017)` sample of 60. Blind
  worklist (ids `R00`…, shuffled with the same seed, fields `id, kind, lang, de, fr, it, finding, question`; question:
  "Is the difference named in 'finding' a real divergence between the German and the 'lang' text (a different condition
  for the reader)? Answer real / minor / not (same condition: rephrasing, style, alignment or parser artefact)"). The key
  map is kept apart. Two fresh general-purpose Claude subagents, each given only a copy of the worklist in an otherwise
  empty directory, PROTOCOL.md set-up, the second in reverse order; a third fresh agent labels every record where the
  two disagree on divergence (real or minor against not); final = majority. Precision = real or minor by the final
  label (strict real reported beside), Wilson 95%, also on held-half findings alone. No human labels, no model API calls.
- **Pass criteria, per kind.** `operator`: held recall ≥ 60% and precision ≥ 50%. `negation`: held recall ≥ 50% for
  drop and for add, and precision ≥ 50%. `number_word`: held recall ≥ 60% (v2: 37.0%) and precision ≥ 50% (with no
  finding on the register, precision is not assessed and the kind passes on recall). And for all: the existing kinds
  unchanged as above.
- **Decision and reporting.** A kind that passes is on by default (in the audit output and the summary). A kind that
  fails is shipped off (computed and reported in the results, not in the default output), and the README and report keep
  stating it as a blind spot with the measured recall. README, report and `docs/audit.md` state recall before and after
  per type and the precision, whatever they are (`score.audit_r15` -> `eval/results/audit_r15.json`, re-derived by
  `replay`).

## R14. Audit relabel and in-span annotator sensitivity (frozen 10 Oct 2026, before any annotation)

A juror: (a) the audit precision figures (16 of 27 findings on the 6 Oct 2026 register, 8 of 11 terminology notices, 7 of
11 on MiGeL and the Analysenliste) rest on one Claude annotator per finding (the single `real` column of
`eval/labels/audit*_*.tsv`), while the README says "blind annotators"; (b) R11 planted only single local edits, which
annotators catch by diffing the draft against the old text, whereas real errors look like a plausible part of the
amendment (scope drift inside the amended sentence). R14 answers both; no model is called, all annotation is by fresh
blind Claude subagents.

### Part A: every audit finding relabelled by two blind annotators and a third on disagreements

- **Items** (`tools/audit_relabel.py`, deterministic, `--check` reproduces the files byte for byte): all 49 labelled
  findings: *register* = `audit_20261006` (21 number findings) + `audit2_20261006` (6 language / editorial) = 27;
  *terminology* = `audit3_terminology_20261006` (11); *lists* = `audit_migel_20260701` (8) + `audit_al_20260701` (3) = 11.
  Each record is the committed worklist record of its file with every field kept (texts, `finding`, and its own
  `question`, unchanged) except the id, which becomes a neutral `R00`…; the 49 are pooled and shuffled with
  `random.Random(20261016)` (`eval/labels/audit_relabel_worklist.json`); the id -> finding map
  (`audit_relabel_key.json`) is kept apart and never shown. The first labels, the set names and the audit's ranking are
  not in the worklist.
- **Annotators.** Two fresh general-purpose Claude subagents, each given only a copy of the worklist in an otherwise empty
  directory; the second labels the records in reverse order. A third fresh agent labels, in a new worklist (ids `T00`…,
  shuffled with `random.Random(20261018)`, same record fields), every finding where the two answers differ. Instructions,
  verbatim (the second annotator gets the extra sentence in brackets, the third the same instructions with its own file):

  > You are a blind annotator for an evaluation of a divergence audit. Read ONLY this file: `<worklist>` (N records). Do
  > NOT open, search or list any other file or directory. Use only the read of that file and one write of your output
  > file. No web access.
  >
  > Context: Swiss federal lists of reimbursed medicines, medical devices and laboratory analyses (BAG
  > Spezialitätenliste, MiGeL, Analysenliste) are published in German, French and Italian, and the language versions
  > should state the same conditions. An automatic audit flagged each record below; `finding` says what it flagged and
  > `lang` names the language version concerned. Each record carries the texts and its own `question`.
  >
  > For each record, read the texts and the finding in full and answer the record's `question` with exactly one of:
  > real, minor, not (as that question defines them). [Label the records in reverse order: start with the last record of
  > the file and end with the first.]
  >
  > Write a TSV to `<output>` with header `id\tanswer\tnote` (note <= 20 words). Read every record fully; do not skim
  > long paragraphs. Report back only "done" plus counts per answer, computed from the file you wrote.

  plus the R11 operational note on long lines (read the file so that every line is shown in full, still only this file).
- **Merge** (`eval/labels/audit_relabel.tsv`: `uid, set, first, A, B, T, final, final_confirmed, note_A, note_B,
  note_T`; raw annotator files `audit_relabel_{A,B,T}.tsv` by neutral id beside it). *Confirmed* = answer `real` or
  `minor`: the finding names a real divergence or defect, which is what the first annotation's `real = yes` records.
  `final` = the answer shared by at least two of the three, otherwise the third's (A's when A and B agree);
  `final_confirmed` = majority of three on confirmed (A's when A and B agree on it).
- **Outcomes** (no threshold; `score.audit_relabel` -> `eval/results/audit_relabel.json`, re-derived by `replay` from the
  committed files): agreement and Cohen's κ between A and B on confirmed (49 findings, and per set), agreement on the
  three-way answer; majority precision per set (register x of 27, terminology x of 11, lists x of 11) with Wilson 95%,
  and strict precision (answer `real` only); agreement of the majority with the first single labels per set, with κ,
  and the findings where they differ.
- **Reporting rule, stated now.** If the majority precision of a set differs from the first annotation, the README and
  report numbers switch to the majority labels (`score.audit_eval` and `score.audit_more` read `audit_relabel.tsv`),
  and the first labels stay in the results as `first_annotation`. If they are the same, the README says that two blind
  annotators and a third on disagreements confirm them, with the agreement. Either way the wording "blind annotators"
  then describes what was done.

### Part B: meaning errors planted inside the amended wording

- **Bases** (`tools/plant_inspan.py`, seed 20261017; design in its docstring; `--check` reproduces its output byte for
  byte): the R11 base pool (fresh-166 ready drafts that every label calls exact or equivalent, one draft per item),
  restricted to drafts of the 70B or the 8B Q8_0 run and not marked needs-fix by the R13 blind majority: 64. The
  boilerplate family 981f07a8 (one sentence whose only change is the insurer term) is subsampled to 4 FR + 4 IT with
  `random.Random("20261017:family:<lang>")`; all 30 other bases are kept: **38 bases** (exact and equivalent).
- **Plants** (`eval/labels/inspan_plants.json`): written by hand by the pre-registering agent after the seeded base
  selection and before any annotation, one per base, as fluent text that reads like part of the amendment, adjoining or
  within the amended wording: **scope** (population or indication widened or narrowed within the amended clause, 11),
  **condition** (a condition of the new German half-applied or kept in part from the old text, or changed within the
  amended clause, 12), **number_noun** (a number or unit of the amended clause attached to the wrong noun, 8),
  **and_or** (an and/or inside the amended clause, 7). The tool checks that the whole edit lies inside a sentence of the
  draft that the German change touched (a sentence overlapping a character the draft changed against `tgt_old`; for a
  pure deletion, the sentences on both sides) and that each plant's `old` text occurs once. Each plant records the
  meaning error it makes (`error`, never shown).
- **Worklists** (`inspan_set{1,2}_worklist.json`, 53 records each): every base once planted and once untouched, never
  both in one worklist; a group of bases sharing an SL cluster or the same touched sentence puts all its planted copies in
  the same worklist (so no worklist holds a planted copy beside an untouched sibling of the same wording); the 30 real
  drafts of R11 (REAL / stale / german) split between the two as a base-rate mix; seeded shuffle, neutral ids `V000`… /
  `W000`…, fields exactly as `eval/labels/PROTOCOL.md` with `official_new` shown. The key (`inspan_key.json`) is kept
  apart and never shown.
- **Annotators.** Per worklist two fresh general-purpose Claude subagents (4 in all), each given only a copy of its
  worklist in an otherwise empty directory, with the PROTOCOL.md instructions verbatim (reference shown) plus the R11
  operational note on long lines; the second reads the records in reverse order. No annotator sees both worklists. No
  tie-break: recall is reported per annotator, for both and for either (as R11).
- **Metrics** (no threshold; `score.annotator_sensitivity_inspan` -> `eval/results/annotator_sensitivity_inspan.json`,
  re-derived by `replay` from `eval/labels/inspan_sensitivity.tsv` and the key): severe = REAL or stale (as R11); for the
  38 planted copies, caught as needs_fix = yes and as severe by A, by B, by both and by either, overall and by type,
  language and family, with Wilson 95% over items; false alarms on the 38 untouched copies (needs_fix = yes; severe); on
  the 30 real drafts, severe labels by existing class; the planted copies missed by both, with the plant and the labels.
- **Reporting rule, stated now.** The README and the technical report state the in-span recall (severe by both / by
  either, Wilson 95%) next to R11's 66 of 66, whatever it is, and the 95% bound on severe errors among ready drafts
  divided by the both-annotator in-span recall (descriptive). If recall is below R11's, the README says that "0 meaning
  errors among ready drafts" is bounded by this recall. No decision attached: no earlier outcome is re-opened.

## R16. Memorisation probe: could Apertus have seen the held-out answers? (frozen 10 Oct 2026, before any model call)

An Apertus-team juror: the answers of the fresh 166 (BAG's published FR/IT texts for changes June 2025 – February 2026,
`items_fresh.json` `tgt_new`) may predate Apertus v1.5's training cutoff. R16 asks the models to continue those texts
word for word and compares them with texts the models have almost certainly seen and texts they cannot have seen.

- **Sets** (`tools/r16_memo.py build`, deterministic, `--check` rebuilds it byte for byte; committed with this rule as
  `data/memo/r16_items.json`). Texts `nrm()`'d, at least 200 characters and at least 10 words in the second half,
  deduplicated by exact text. **T** (test answers): every fresh-166 `tgt_new`: 160 texts (80 FR, 80 IT). **P**
  (positive control, long-standing): limitations of the 1 June 2025 XML (`20250611/Preparations.xml`) with
  `ValidFromDate` before 1 Jan 2023 whose FR/IT text is unchanged in every 2026 snapshot from 1 June to 6 Oct 2026 (the
  Feb–May files drop `<...>` spans), not in T or N; `random.Random('20261016-<lang>').sample` of 60 per language from
  278 FR / 276 IT candidates: 120 texts (valid from 2007–2022). **N** (negative control, after any plausible cutoff):
  BAG's new FR/IT texts of the two live months (Aug and Sep 2026, `data/shadow/*/items.json` `tgt_new`), different from
  the item's old text and absent from both 2025 XML captures and from every 2026 snapshot up to the month's old snapshot,
  not in T: 62 texts (32 FR, 30 IT; 24 Aug, 38 Sep). T and N are alike in kind (both are new versions of an older text,
  so their first halves often repeat older wording); P is a text that stood unchanged for 3–19 years.
- **Probe.** Each text is cut after half of its words (`len(words) // 2`, a word boundary); the prompt is one plain user
  message, no system message, no assistant prefill: `Continue this Swiss drug-reimbursement limitation text word for
  word, exactly as published by the BAG. Output only the continuation.` + blank line + the first half. Temperature 0,
  `max_tokens` 300, one call per text.
- **Models.** (1) Apertus 70B (`swiss-ai/apertus-v1.5-70b`) through the development gateway (`backends.Gateway`, tag
  `gleichlaut-r16-70b`, sequential with a 1 s pause, User-Agent hackapertus-research/0.1); the served `model` field is
  checked on every call and any other model is refused; every response recorded in `data/memo/r16_70b/responses/` (its
  own folder). (2) Optional: the shipped 8B GGUF Q8_0 on GitHub Actions CPU runners (workflow `r16-8b`), the same
  prompts through llama-cpp-python's chat completion (the GGUF's chat template), greedy, **no** logit mask (the digit
  ban would forbid numbers in the continuation), responses in `data/memo/r16_8b_q8_0/responses/`. If the 8B arm is not
  run, that is stated.
- **Scoring** (`score.memorisation` -> `eval/results/memorisation.json`, re-derived by `replay` from the recorded
  responses). Response and true second half normalised alike: `nrm()`, NFC, typographic apostrophes to `'`; a leading
  `...` / `…` dropped; a response that starts with the whole first half has it removed (counted). Words = split on spaces,
  compared exactly. Per text: (a) **next-10** = the first 10 words equal the true next 10 words (primary); (b) **LCP** =
  number of leading words equal; (c) **chrF** (the frozen scorer's `chrf`) of the first k response words against the first
  k true words, k = min(100, words in the second half). Secondary for T and N texts whose old text starts with the same
  first half and continues differently: whether the response's chrF (first k words) is higher against the new
  continuation than against the old one (ties apart).
- **Statistics.** Per set: next-10 rate, mean LCP, mean chrF. Differences T − N and P − N with a percentile bootstrap 95%
  CI (10,000 resamples of texts within each set, `random.Random(20261016)`), and a two-sided Mann–Whitney p (normal
  approximation, tie-corrected) for LCP and chrF.
- **Decision, stated now, per model.** Memorisation of the test answers is **flagged** if T's next-10 rate exceeds N's
  by more than 10 points **and** the bootstrap CI of T − N excludes 0. Otherwise T is reported as "no evidence of
  memorisation beyond the negative control". Probe sensitivity: if P − N meets the same criterion, the probe detects
  memorisation of long-standing texts; if it does not, the report says that the probe found none even for texts unchanged
  for years, so a null result on T is weak evidence. If memorisation is flagged, README and report say so next to the
  fresh-166 headline, with the numbers. Whatever comes out is reported as is.

## R17. Real errors and a non-Claude annotator (frozen 10 Oct 2026, before any annotation or model call)

A juror: "Claude wrote the planted errors and Claude caught them; κ 1.000 is two copies of one model family agreeing."
R17 answers both halves: (A) errors that people made and BAG itself later fixed, labelled by fresh blind Claude
annotators; (B) Apertus 70B, a different model family, as a second annotator. Tool `tools/r17_real_errors.py` (design in
its docstring); its output is committed with this rule (`build --check` rebuilds it byte for byte from the snapshots).

### Part A: real errors BAG corrected without a German change

- **Mining.** Every step of the SL snapshot series the backtest uses (2026: `sl.mine.SNAPS`, 19 Feb → 6 Oct, 4 May
  excluded; 2025: the two Wayback XML captures 11 Jun → 31 Jul; the 2025 → 2026 step is not used: the formats share no
  limitation key). Per product, every German limitation text present byte-identical in both snapshots (34,272 + 1,318
  such pairs) whose French or Italian text (same key; old-format positional keys as `sl.mine.tkey`) differs after
  `nrm()`; old-format pairs with `<` dropped as in `sl.mine`. Result: **29 changes**.
- **Mechanical classification** (docstring `CLASSIFY`): punctuation / spacing / typography only (word lists equal after
  NFC, casefold, apostrophe, quote and dash folding; 12: Vegzelma → VEGZELMA case changes 11, one spacing change in
  2025) are dropped. Content changes, typed number > negation/operator > words: **17**, all kept (**fewer than 30
  exist, so all are used**): number 0, negation/operator 2 (a stray French «n'» in «n'est destiné»; a sentence with «ne
  peut pas» added), words 15 (12 replaced, 3 removed). 10 of the 17 are one house-wording sweep of Opdivo's French code
  sentence («correspondant à» → «de», «communiqué» → «transmis»); results are also reported by edit family. 14 French,
  3 Italian.
- **Direction, declared now.** Normally the old text is the error and BAG's new text the fix. In 2 changes (Opdivo .01
  and .04, French) BAG's new text drops the indication-code sentence that the unchanged German still carries, leaving
  «chimiothérapie. .»: there the new text is the error and the old one the correct version (`REVERSED` in the tool;
  decided by reading the 17 against the German, before any annotation). Results are reported over all 17 and over the 15
  BAG fixes.
- **Records** (PROTOCOL.md worklist shape): `de_old` = `de_new` = the unchanged German; error record `draft` = `tgt_old`
  = the erroneous text; control record `draft` = `tgt_old` = the correct text (so every record looks alike: German
  unchanged, draft equal to tgt_old); protocol (a) `official_new` = the correct text, protocol (b) no `official_new`.
  Two worklists per protocol (17 records each): a change's error and control are never in the same worklist; changes that
  share an edit family or the same German go together (their errors in one worklist, controls in the other; largest
  group first, seed 20261019): set 1 holds 10 errors + 7 controls, set 2 7 + 10. Seeded shuffle per protocol and set,
  neutral ids `X…`/`Y…` (a), `J…`/`K…` (b). Key `eval/labels/r17_key.json` kept apart, never shown.
- **Instructions.** PROTOCOL.md verbatim with R11's operational note on long lines, except the context paragraph, which
  must change for the task to be coherent: its sentences "The German text was amended (de_old -> de_new). A system drafted
  the matching amendment of the French or Italian text (lang) starting from the old target text (tgt_old) -> draft." and
  "Official translators sometimes also fixed things the German change did not touch; a draft is NOT expected to make those
  extra fixes." are replaced by: "Here the German text was not amended (de_old = de_new). The French or Italian text
  (lang) under review is draft (tgt_old is the same text); judge it against the German as if it were a new draft: a
  problem already in tgt_old counts against the draft, and "the German change" in the definitions below means "the
  German text"." (b) also replaces "official_new is what the authorities published." by R11's "No published version is
  available for these records: there is no official_new field." Everything else (needs_fix, the classes, the severity
  order, the output format) is unchanged.
- **Annotators.** Per protocol and worklist two fresh general-purpose Claude subagents (8 in all), each given only a copy
  of its worklist in an otherwise empty directory; the second labels in reverse order; no annotator sees both worklists
  or both protocols. No tie-break (as R11/R14).
- **Metrics** (no threshold; `score.annotator_real_errors` → `eval/results/annotator_real_errors.json`, re-derived by
  `replay` from `eval/labels/r17_real_errors_{a,b}.tsv` and the key). Recall on the 17 error records: needs_fix = yes and
  severe (REAL, stale or german) by A, B, both and either, Wilson 95%; by correction type, by edit family (the sweep vs
  the rest), by language, for the 15 BAG fixes; false alarms on the 17 controls (needs_fix = yes; severe); class
  counts; every error record missed by both, with its edit and notes.

### Part B: Apertus 70B as a second, non-Claude annotator

- **Items.** (i) The 49 audit findings of R14 (`audit_relabel_worklist.json`, neutral ids, each record's own
  `question`); the audit uses no model, so no model judges its own output. (ii) The 34 part-A records under (a) and under
  (b). Never an Apertus-drafted text. 117 requests in `data/r17/r17_70b_prompts.json` (prompts frozen here).
- **Calls.** `swiss-ai/apertus-v1.5-70b` through the development gateway (`backends.Gateway`, run tag
  `gleichlaut-r17-70b`), one plain user message per record, no system message, no prefill, temperature 0, `max_tokens`
  300, sequential with a 1 s pause; the served `model` is checked on every call and any other model is refused; every
  response recorded in its own folder `data/r17/apertus70b/responses/`, call log `calls.jsonl`.
- **Prompts.** Audit: the R14 instructions with "each record" → "the record", the record as JSON, and "Answer in exactly
  this format, two lines, nothing else: `answer: <real, minor or not>` / `note: <at most 20 words>`". Part A: the
  part-A instructions of the protocol ("For each record" → "For the record below"), the record as JSON, and three lines
  `needs_fix: <yes or no>` / `class: <one class>` / `note: …`. Parsers (`score.r17_parse_*`): first line-initial
  `answer:` / `needs_fix:` / `class:` (case-insensitive, `*` and backticks ignored) with a valid value; otherwise
  **unparsed** (counted, never re-asked; not caught in recall, left out of agreement and κ).
- **Metrics** (`score.annotator_crossfamily` → `eval/results/annotator_crossfamily.json`, re-derived by `replay` from the
  recorded responses, looked up by the request's sha256). (i) Agreement and Cohen's κ with the R14 Claude majority on
  confirmed (real or minor vs not), overall and per set; three-way answer agreement; the findings where they differ.
  (ii) Apertus's own recall on the 17 errors (needs_fix = yes; severe) and false alarms on the 17 controls, per protocol,
  Wilson 95%; agreement and κ on needs_fix with each Claude annotator and with the records where the two Claude
  annotators agree.
- **Reporting rule, stated now.** README (where R11/R14 sensitivity is described) and the technical report (drafting
  results, after the R14 sentence) state the real-error recall by both / either under (a) and (b) and the Apertus
  agreement / κ on the audit and its recall on part A, whatever they are. No decision attached; no earlier outcome is
  re-opened. Whatever comes out is reported as is.

## R18. Apertus 8B log-probability filter on the round-5 audit findings (frozen 10 Oct 2026, before any model run)

An Apertus-team juror: put Apertus into the audit. The round-5 checks (R15: operator, negation, number_word) ship off:
31 findings on the 6 Oct 2026 register, 6 confirmed (real or minor) by the R15 blind annotators (19.4%; real: AMVUTTRA.01a
FR "≤ 10", BEYONTTRA and VYNDAQEL.01b IT "on deve"). R18 asks whether the shipped 8B, used as a forced-choice re-ranker,
lifts the precision enough to switch them on.

- **Pairs.** For each register finding, the aligned German sentence and the French / Italian sentence: negation and
  number_word findings the pair their check judged (`audit.negation_diff`, `audit.number_word_diff`); operator findings
  the pair of `audit.aligned()` whose target span holds the flagged operator, else of `audit.align()` at any cost. All 31
  findings get a pair (24 distinct pairs). Planted: the R15 held copies regenerated byte-identical (seed 20261016, 100
  per type and language, the eligible counts and per-type n checked against `eval/results/audit_injection_r15_held.json`):
  operator 200, negation_drop 200, negation_add 200, number_word 200. Each copy gives two pairs, the sentence pair holding
  the edit after the edit (planted, label 1) and the same pair unmodified (control, label 0); the same rule finds the pair
  (on the unmodified text, the edit inside the target span); 800 + 800, 1,342 distinct pairs; none left out.
  Tool `tools/r18_filter.py` (build is deterministic, no model; `data/r18/items.json` committed before the run).
- **Split, fixed now.** Planted copies by limitation: md5("r18:<limitation id>") even = **fit** (threshold), odd =
  **test** (fit 433 copies, test 367). The register findings are never used to choose anything.
- **Prompt (fixed).** R8 T3's equivalence prompt (`round7b/spike7b.py` PAIR["de"]) with its object and checks named for a
  limitation sentence, German, plain user message (no system message of ours, no prefill; the GGUF's own chat template, as
  in R8): "Unten stehen zwei Sprachfassungen ({la} und {lb}) derselben Stelle einer Limitation der Spezialitätenliste des
  BAG. Beide Fassungen sind gleichermassen verbindlich und sollten dieselbe Bedingung festlegen. Prüfe, ob sie dieselbe
  Bedingung ausdrücken, insbesondere dieselbe Richtung einer Grenze (mindestens oder höchstens, über oder unter),
  dieselben Zahlen und dieselbe Verneinung. [{la}] {ta} [{lb}] {tb} Drücken die beiden Fassungen dieselbe Bedingung aus?
  Antworte nur mit {o1} oder {o2}." (paragraph breaks as in R8; verbatim in `tools/r18_filter.py` Q.) Both orders as R8:
  ab = German first, "Ja oder Nein"; ba = target first, "Nein oder Ja".
- **Score (as R8 T3, `fm.run.run_judge`).** One call per order, greedy, at most 8 tokens, no logit mask; the log-softmax
  at the first answer position; P(Nein) = exp(lp_Nein) / (exp(lp_Ja) + exp(lp_Nein)) ("Ja", "Nein" single tokens,
  asserted); score = the mean of the two orders. Higher = more likely a different condition.
- **Model and runner.** The certified 8B GGUF Q8_0 (sha256 `dea904ad…202d`), llama-cpp-python 0.3.35 in process
  (`fm.run.Model`), GitHub Actions `ubuntu-latest` CPU runners, workflow `r18-8b`, 20 shards, resumable. Every shard
  first verifies the build certificate of the loaded file (`cli.certified_gguf`: 8b-q8_0-fresh166, records re-scored,
  hashes match) and stops without one; the verdict is kept per shard (`shards.json`). Records and every raw answer in
  `data/r18/runs/8b_q8_0/` (own folder). Not on a team machine. A smoke run of at most 2 planted pairs per shard (never
  a register pair) may precede the full run; its outputs are not used.
- **Threshold (fixed rule, fit half only).** Kept = score ≥ t. t* = the fit score that maximises TPR − FPR (Youden's J)
  over the fit pairs (planted vs their controls, all four types pooled); ties: the largest t. Applied unchanged to the
  31 register findings (each finding takes its pair's score).
- **Reported.** Planted: AUROC on test (primary; bootstrap 95% CI over copies, 2,000 resamples, `random.Random(20261018)`),
  on fit and all, per type and language; at t*: TPR / FPR on test; share kept of the copies the R15 checks detected.
  Register: score and kept / dropped for each of the 31 (the 6 confirmed by name; AMVUTTRA.01a, BEYONTTRA, VYNDAQEL.01b
  individually); precision before (6 of 31) and after (confirmed among kept, Wilson 95%), per kind; AUROC confirmed vs
  not (6 vs 25) and real vs the rest (3 vs 28), descriptive. The generated answers (Ja / Nein / other) beside the scores.
- **Decision rule.** The round-5 kinds may ship ON with the Apertus filter only if, on the register, **precision of the
  kept findings ≥ 50%** (the R15 bar) **and at least 4 of the 6 confirmed findings are kept**. If it holds, a kind is
  proposed ON only where its own kept findings also have precision ≥ 50% (a kind with nothing kept stays off). Otherwise
  the kinds stay off and the result is reported as it is. The audit defaults are not changed by this result: a pass is a
  proposal for the maintainers to integrate (`audit.R5_ON` untouched here). Scoring is deterministic from the recorded
  run (`score.audit_apertus_filter` -> `eval/results/audit_apertus_filter.json`, re-derived by `replay`).
- **Caveats stated now.** The threshold comes from planted single-word edits; register false findings are alignment and
  parser artefacts, which may score differently. 31 register findings with 6 confirmed: any precision has a wide interval.

## R19. The certified 8B Q8_0 on the identity probes: is `fp1-nes` an 8B? (frozen 11 Oct 2026, before any model run)

An Apertus-team juror asked whether the backend `fp1-nes`, which answered part of the "70B" calls, could be an 8B. The
70B inference rests on one record: on the same 250 MMLU questions the shared model scored 84.4% (211) and the v1 8B route
`apertus-8b-instruct` 70.8% (177) (`docs/research/model-identity-and-quantisation.md`). No v1.5 8B was ever scored on
those questions. R19 scores the certified local v1.5 8B on them and on the 792-cell battery whose recorded outputs
identify the backends.

- **What the recorded reference numbers are** (stated now, from the records). The 84.4% was measured on the model name
  `swiss-ai/apertus-v1.5-8b` (the "shared model"); the record keeps the served model name per call, not the backend. On
  the battery that name was served by `vllm-0.23.1rc1…-tp8-pp2` in 1,584 of 1,584 calls. `fp1-nes` answered the
  `apertus-v1.5-70b` name on the battery (792 of 792, free generation, no log-probabilities) and gave byte-identical
  text to the 8B name in 760 of 792 cells. `tp2` (`vllm-0.1.dev1+g54b4292c2-tp2`) was recorded on the battery only
  through the `apertus-70b-instruct` alias, as exact forced choice (log-probabilities of prefilled candidates), never as
  free generation: a byte-level comparison with `tp2` is therefore not possible, and `tp2` is compared on decisions.
  Recorded cross-backend references: fp1-nes vs the 8B name, decisions 787 / 792; the 8B name vs tp2 (forced choice),
  decisions 760 / 792; fp1-nes (generation) vs tp2 (forced choice), decisions 758 / 792; the v1 8B vs fp1-nes, text
  0 / 792.
- **Inputs, vendored byte-identical with sha256** (`data/r19/SHA256SUMS`; copied from the research tree before any
  run). MMLU: `mmlu/items.json` (the 250 questions: subjects miscellaneous, professional law, high-school European and US
  history, college biology, prehistory; MMLU, MIT licence), `mmlu/run.py` (the research script: prompt and decoding),
  `mmlu/res_swiss-ai_apertus-v1.5-8b.json` and `mmlu/res_swiss-ai_apertus-8b-instruct.json` (the recorded predictions).
  Battery: `battery/live.py` (prompts `Q`, candidates `CANDS`, parser `parse`), `battery/linie_items.json` (72) and
  `battery/never_items.json` (90), and the recorded runs `battery/gen_apertus-v1.5-70b.json` (fp1-nes),
  `battery/gen_apertus-v1.5-8b.json`, `battery/fc_apertus-v1.5-8b.json` (the 8B name) and
  `battery/fc_apertus-70b-instruct.json` (tp2). The question strings used are the `questions` stored in the recorded
  files, asserted equal to `live.py` Q.
- **Calls, exactly as recorded.** One plain user message, no system message of ours, the GGUF's own chat template (it is
  byte-identical to the official template, which the API rendered: `docs/research/chat-template.md`), greedy
  (temperature 0), no logit mask. (i) MMLU: the user message of `run.py` `prompt(it)` (question, blank line, "A. … D."
  lines, blank line, "Answer with only the letter (A, B, C or D)."), at most 3 tokens; the prediction is `run.py`'s
  first match of `[ABCD]` in the answer text (kept verbatim; the raw text is recorded). (ii) Battery, generation: the user
  message `text + Q[framing][rung]` of `live.py` `gen_cell`, at most 24 tokens; decision by `live.py` `parse`. (iii)
  Battery, forced choice (as `live.py` `fc_cell` / `stage9.py`): the rendered prompt followed by the candidate ("Ja" /
  "Nein"; "Urteil: schuldig" / "Urteil: nicht schuldig"), the candidate's last 1 / 2 / 3 tokens (asserted to detokenise to
  the tokens the API recorded) scored by teacher forcing; log-odds = lp(first) − lp(second); decision = log-odds > 0.
  Check, reported: the prompt token counts against the API's recorded `prompt_tokens` for every cell (generation and
  forced choice); mismatches listed, not dropped.
- **Model and runner.** The certified 8B GGUF Q8_0 (sha256 `dea904ad…202d`), llama-cpp-python 0.3.35 in process, GitHub
  Actions `ubuntu-latest` CPU runners, workflow `r19-8b`, 20 shards (question / cell index modulo 20), resumable. Every
  shard first verifies the build certificate of the loaded file (`cli.certified_gguf`) and stops without one; the
  verdict is kept per shard. Records and every raw answer in `data/r19/runs/8b_q8_0/`. Not on a team machine. A smoke
  run of at most 2 questions and 2 cells per shard may precede the full run; its outputs are not used.
- **Measured** (`score.identity_r19` → `eval/results/identity_r19.json`, re-derived by `replay`). MMLU: Q8_0 accuracy
  k / 250 (Wilson 95%); the paired differences shared model − Q8_0 and Q8_0 − v1 8B with a bootstrap 95% CI over
  questions (2,000 resamples, `random.Random(20261019)`); letter agreement with each. Battery: **B_f** = cells whose
  Q8_0 generated text is byte-identical to fp1-nes's recorded text (/792; also after stripping outer whitespace); the
  same against the 8B name (B_8); **D_f** = generation decisions equal to fp1-nes's (both parsed; /792), D_8 the same
  against the 8B name; **D_t** = forced-choice decisions equal to tp2's (/792), D_8fc against the 8B name's forced
  choice; Pearson r and mean |Δ| of the forced-choice log-odds against tp2 and against the 8B name; Q8_0's own
  generation vs forced-choice decision agreement.
- **Decision rule, stated now.** MMLU-low: Q8_0 ≤ 78.0% and the CI of (shared − Q8_0) lies above 0.
  (O1) MMLU-low with Q8_0 ≥ 65.0%, **and** B_f ≥ 90.0% (≥ 713 of 792) **and** D_f − D_t ≥ 3.0 points: `fp1-nes` is
  likely an 8B; README and report then say that the headline "70B" arm may be partly 8B-served (its backend was not
  logged per call; in the R2 rerun 81 of 283 calls went to `fp1-nes`). (O2) MMLU-low **and** B_f < 75.0% (< 594): the
  70B inference is strengthened. (O3) Q8_0 ≥ 80.0%, or the CI of (shared − Q8_0) includes 0: MMLU does not separate the
  shared model from the v1.5 8B, and the 84.4% is no longer cited as evidence of size. (O4) Anything else: inconclusive.
  Whatever comes out is reported as is, in report §3.1 and wherever the README mentions the 70B identity.
- **Caveats stated now.** Local Q8_0 on CPU is not the served bf16/fp8 stack: identical weights would still differ in
  some cells (Q8_0 matches the bf16 DPO checkpoint on 638 of 648 parity decisions). The battery's answers are short
  ("Ja.", "schuldig"), so byte identity carries less information than on long text. A v1.5 8B scoring near the shared
  model would not show the shared model is an 8B.

## R20. The audit's findings as predictions, scored against BAG's own later corrections (frozen 11 Oct 2026, before any later SL publication)

A juror: every label behind the audit's precision comes from Claude annotators (R14, R15), and the one non-Claude
annotator tried, Apertus 70B, does not discriminate (R17). An oracle that is not Claude exists: BAG, when it corrects a
text in a later SL publication. R20 freezes now what the 6 Oct 2026 audit predicts BAG will correct, and how that is
scored. On 11 Oct 2026 (01:04 UTC) BAG's resources API names the 6 Oct 2026 feed as the newest; no later data exists.

- **Frozen list** (`eval/predictions/audit_20261006_predictions.json`, sha256 `09cd9df7bf3e59ca37f3a161ecb190987e978999e6dbf87a42c77cd95ca8d326`, in the
  commit of this section; `tools/check_predictions.py build` from `data/audit/audit_20261006.json`, its shipped texts,
  the 6 Oct snapshot's limitation ids and the blind labels; deterministic, no model). One record per finding: the 38
  findings of the register's 18 issues and the 31 round-5 findings, 69 in all. Each record: product, limitation id,
  kind, the finding's language, the **divergent language** (the odd one out of the three as the register computes it:
  number findings by the third language's values, operator and negation from the third language's aligned sentence,
  terminology the target language; `unclear` when the third language does not settle it), what each language states on
  6 Oct 2026 (the finding's values with their counts, the bounds on the value with their operators, the aligned sentences
  with their negations, the typo and its correction, the written language, the old and new term), the **predicted
  correction** in words (e.g. "IT changes 4 to 8 (Wochen), as DE and FR state"; "FR '≤ 10' becomes a lower bound
  ('> 10'), as DE and IT state"), its machine-readable form, the blind label, and the sha256 of each language's text.
  **Positive predictions** (BAG corrects it): the 34 findings the blind majority confirmed (real or minor): 28 of the 38
  register findings and the 6 confirmed round-5 findings. **Negative predictions**: the 35 not confirmed (10 register,
  25 round-5), marked as such.
- **Scoring snapshots.** Every SL publication after 6 Oct 2026 (the next is expected 1 Nov 2026), checked with
  `tools/check_predictions.py check --fetch <date>` (the public FHIR feed, client and user agent of `gleichlaut month
  --fetch` in the shadow workflow) -> `eval/predictions/check_<date>.json`. The checker and `gleichlaut.audit` are used
  as at this commit (their sha256 is written into every check file; if either has changed, the scoring runs from this
  commit's files), with the 6 Oct 2026 language statistics and term pairs.
- **Status of a prediction in a snapshot** (fixed now; the tool's docstring). *Limitation removed*: the id is absent
  from the German, the finding's language or the divergent language. *Unchanged*: the three texts are identical (after
  `nrm`). *Corrected toward agreement*: a text changed, the divergent language's text changed, the same check no longer
  reports the finding on the new texts, and the divergent language now states what the other two state at that place:
  numbers and number words: it states the agreed value more often and its own odd value less often than on 6 Oct, and
  the agreeing side still states the value; operator: it states the value with the agreed direction; negation: the
  aligned sentence pair (the agreeing side's sentence unchanged) now agrees on negation; typo: the typo occurs less often
  and its correction more often; terminology: the new term occurs more often and the old one less often; language: the
  field is in its own language. With the divergent language `unclear`, either the German or the finding's language may be
  the side that moves (either direction passes). *Changed otherwise*: every other change (the finding still reported, the
  other side changed, the passage deleted, the divergent language unchanged). A limitation id absent from a later
  snapshot is followed to a new id (one not among the 6 Oct ids) with the same product prefix and the most similar German
  text (difflib ratio ≥ 0.9; a tie is not followed).
- **Measure** (`tools/check_predictions.py score` -> `eval/predictions/score.json`) at two horizons, **6 months**
  (snapshots dated up to 6 Apr 2027) and **12 months** (up to 6 Oct 2027): **P** = share of the 34 positive predictions
  corrected toward agreement in at least one scoring snapshot of the horizon (Wilson 95%), against the base rate **B** =
  share of the 35 negative predictions whose limitation changed in at least one (corrected or changed otherwise).
  Reported beside: positives changed in any way, negatives corrected toward agreement, removed limitations, the two sets
  (issues, round 5) apart.
- **Decision rule.** At a horizon that has passed: **supported** if P > B and the one-sided Fisher exact test of P
  against B gives p < 0.05; otherwise **not supported**; reported as it comes out, in the results log, the README and
  `docs/audit.md`. Nothing is claimed before a horizon has passed: a monthly check file is reported as counts only.
- **How it runs.** No workflow in this repository commits results (all are `contents: read`; the shadow workflow
  uploads artifacts), so there is no scheduled job. After each SL publication the one command is
  `PYTHONPATH=src python3 tools/check_predictions.py check --fetch latest && python3 tools/check_predictions.py score`,
  committed with a results-log line (no model, three public feed downloads).
- **Checked before the freeze** (no later data). Self-test on the 6 Oct snapshot, the research copy and a fresh fetch of
  the public feed (byte-identical): 69 of 69 unchanged and still reported (`eval/predictions/check_20261006.json`).
  Sanity, backwards in time on the 1 Jun, 1 Jul, 1 Aug, 1 Sep and 1 Oct 2026 snapshots (`check_<date>.json`): each dated
  finding is reported exactly in the snapshots its `first_seen` says, with renamed limitations followed. Backtest: the
  same audit on the 1 Jun 2026 snapshot gives 63 findings; by 6 Oct 2026 none is corrected toward agreement, 3 changed
  otherwise (renamed limitations with edited texts) and 60 are unchanged (`eval/predictions/backtest_20260601.json`):
  flagged texts seldom change on their own.
- **Caveats stated now.** BAG may correct for reasons unrelated to the audit, correct the side the audit did not
  predict, or rewrite a limitation (changed otherwise). With 34 and 35 predictions the intervals are wide, and sibling
  findings (T01–T04, T05–T08, the three etanercept texts) are not independent; the 18 issues are reported beside. The
  status is mechanical: it reads the values, bounds, negation, typo, term or language at the flagged place, not the whole
  wording. If anyone sends findings to BAG before a horizon, the date and the findings sent are logged in the results
  log; corrections after that count as BAG accepting a report rather than as an independent prediction, and both
  readings are reported.

## R21. A task-specific system message with the house wording (variant v4-system), fresh 166 and both live months (frozen 11 Oct 2026, before any model run)

An Apertus-team juror: every run so far used the chat template's default multimodal persona ("You are Apertus 1.5 Omni,
a multimodal assistant ...", `docs/research/chat-template.md`), since the pipeline sends one user message; a
pre-registered task-specific system prompt should be tried. R21 tests one fixed system message on top of v3-terms (R12).

- **Variant v4-system** (`src/gleichlaut/v4system.py`, outside `frozen/`; frozen code and `freeze.json` unchanged).
  v3-terms exactly as R12 defines it (the frozen pipeline, the same house-wording block and block rules, `v3terms.py`
  unchanged) plus **one system message**, sent first in every request of the item (draft, lock retry, re-ask), which
  replaces the template's default system turn; the template's developer turn ("Deliberation: disabled / Tool
  Capabilities: disabled") stays. Guards, re-ask, routing, slot codes, decoding (greedy, the digit / number-word mask) and
  the frozen code are unchanged; the system message is the only difference from v3-terms, and from the frozen request
  where an item has no house wording. The text, verbatim (UTF-8, no trailing newline):

  > You maintain the French and Italian versions of Swiss drug-reimbursement limitations (BAG Spezialitätenliste). When the German text of a limitation is amended, you amend the French or Italian text: change only what the German change requires, keep every other word of the old text, use BAG's established terminology given in the request, and output only the amended paragraph.

  sha256 `a81624dc3341e9add1447dbff1cc1dc45c6800acba0fbf3319c9927480cf848f`. Mechanism: the backends take an optional `system` (`backends.messages`); the variant
  passes it, nothing else does. With the variant off, the request and its key are the frozen ones byte for byte, and the
  recorded R9 calls still replay (`tests/test_r21.py`).
- **House wording per item: the snapshot before the item's change** (its own `snap_old`), by the unchanged mining code.
  Live months: the committed R12 files (`data/termbase/r12/*_20260801.json`, `*_20260901.json`), unchanged, so the
  user prompts are R12's v3-terms prompts byte for byte (their pre-registered sha256 in `r12_blocks.json`; test). Fresh
  166: 12 items start from the release of 1 Jun 2025 and 154 from 1 Jul 2025 (`snap_old`; their new texts are from
  1 Jul 2025 and 19 Feb 2026). Those two snapshots exist only as BAG's XML captures the fresh set was built from
  (`frozen/build_fresh.py` SNAPS: `wb2025/20250611/Preparations.xml`, sha256 `ab071ebad1d5…`, and
  `wb2025/20250731/Preparations.xml`, sha256 `102f691db6cc…`; research tree, not vendored: 63 MB each). `tools/r21_system.py
  mine` reads them with `sl.ingest.load_xml` (the frozen exporter emulation, as the backtest does), keeps one text per
  limitation code as `sl.ingest` does (the first; 0 conflicts), and runs `termbase.mine`, `house.mine` and
  `termbase.shared_words` unchanged -> `data/termbase/r21/{termbase,house_sentences,shared_words}_<date>.json` and the
  TBX. The mining code is today's, with the reviewers' exclusions added after R12 (e.g. Italian «assicuratore»).
- **Review of the 2025 renderings, fixed now** (the R12 review rule, "a fragment, not a rendering", made mechanical;
  `r21_system.review`): a 2025 house term rendering is dropped when (a) `termbase.DROP_VARIANTS` lists it for the term,
  (b) its words are a strict contiguous part of the term's house rendering in the shipped, reviewed 6 Oct 2026 termbase,
  or (c) it shares no word of four or more letters with that entry's rendering or variants. It only removes entries;
  every wording in a block comes from the item's old snapshot. Dropped: 1 Jun 2025 (6) FR Fabrikabgabepreis «prix»,
  Referenzpräparat «biosimilaire», Verlaufskontrolle «effectués que par un spécialiste», IT Erstlinienbehandlung «linea
  di pazienti adulti», Referenzpräparat «biosimilare», Zweitlinientherapie «seconda linea»; 1 Jul 2025 (8) the same six plus
  FR Kostengutsprache «prise en charge» and Erstlinienbehandlung «traitement de première». Left: 53 and 50 house terms, 35 and 30 house sentences. Disclosed: this rule was written after looking at
  the mined 2025 entries and the blocks they give (built from the old snapshot and the new German only; no model output
  and no published FR/IT of the items was looked at). One wrong entry passes the rule and stays: FR
  Krankheitsprogression «survenue» (1 Jun 2025; in one item's block).
- **Committed with this rule** (in the commit that follows it, before any run): `eval/prereg/r21_prompts.json`
  (`tools/r21_system.py prompts`; `--check` reproduces it byte for byte): the system message and its sha256; per set and
  drafted item the terms date, the block and the sha256 of the first request's user prompt under the frozen pipeline,
  v3-terms and v4-system. Fresh 166: 166 drafted, 154 model calls, 141 user prompts changed by a block (the other 13
  differ from the frozen request only by the system message); August 22 drafted, 22 calls, 19 changed; September 44,
  40, 40 (as R12).
- **Runs** (GitHub Actions CPU runners only, workflow `r21-8b`, `tools/r21_system.py run`; nothing runs a model on a
  team machine). Every shard first verifies the build certificate `8b-q8_0-fresh166` of the loaded GGUF
  (`cli.certified_gguf`, sha256 `dea904ad…`) and stops without it. Every exchange (the request as sent, system message
  included, and the response) is recorded in the run's own folder (`data/r21/runs/<set>_q8_0/exchanges.jsonl`, with
  `records.jsonl`, `calls.jsonl`, `summary.json`), and `make run` re-executes each run from it. **(A)** `set=fresh166`:
  the 166 held-out items, each through the pipeline as in R1 (M2) (`m1 run`: every item, no routing); comparator: the
  certified R1 (M2) Q8_0 run. **(B)** `set=20260801-20260901` and `set=20260901-20261001`: the committed items, routed
  and recorded as the shadow workflow does (`cli.draft_items`; the variant is not certified, so `status` is "flagged"
  with a review reason and `guard_status` keeps the guards' verdict, which is scored, as in R12); comparators: the
  frozen Q8_0 runs (R7, R10) and the v3-terms Q8_0 runs (R12). Q8_0 only; no 70B run.
- **Labels.** Every v4-system draft the guards mark ready that differs from BAG's published text, and for (A) also a
  seeded sample of 20 flagged drafts (seed 20261009, as R1; descriptive, no criterion), except drafts byte-identical to
  an already-labelled draft of the same item (fresh 166: the 70B reference labels, the R1 Q4_K_M and Q8_0 labels, R9;
  months: the R7 / R10 and R12 labels), which reuse that label. Pooled over the three sets, one record per distinct
  (set, item, draft), shuffled with seed 20261021, neutral ids, R1 protocol (`eval/labels/PROTOCOL.md`: two fresh blind
  Claude annotators, the second in reverse order, the R11 operational note on long lines; a third on every disagreement
  on needs_fix or class, or any REAL) -> `eval/labels/r21_system_ready.tsv`. No human labels.
- **Scored by R0** (`score.r21_system()` in `replay`, `eval/results/r21_system.json`). (A) exactly as R1 (M2): n = 166,
  unflagged REAL ≤ 1%, unflagged stale + German ≤ 2%, exact minus rules-only exact ≥ +5 points (paired bootstrap 95%
  CI), flagged ≤ 70%; any unlabelled ready non-exact draft fails the set. Beside it the certified run's numbers, and
  paired: identical outputs, flag agreement, drafts identical to BAG's text gained and lost. (B) as R10 / R12: per month
  n = drafts compared with BAG's text (status ≠ human), the same four criteria on the guards' verdict, frozen, v3-terms
  and v4-system side by side.
- **What is and is not unseen, stated now.** The live months informed R12 and this variant: R12's block and the
  juror's proposal came from their failures, and v4-system adds to that block, so (B) is not an unseen test. The fresh
  166 were not used to design v3-terms or this system message; they were used before for the frozen pipeline (R1, R9,
  R13), and their mined 2025 blocks were read when the review rule above was written.
- **Decision, stated now.** v4-system becomes a **candidate default** only if it meets R0 on (A) **and** on at least one
  live month in (B). Otherwise it is reported as it comes out, criterion by criterion, and the frozen default stays.
  Either way this repository does not change the default: a candidate is reported for the team to decide, after which a
  default change would need its own record. The variant is not changed after any output is seen.

## R22. Stricter alignment for the operator and negation module (frozen 11 Oct 2026, before any rule change)

A juror: the operator and negation module (R15: `operator`, `negation`, `number_word`) found the real AMVUTTRA.01a,
BEYONTTRA and VYNDAQEL.01b, but ships opt-in because 6 of its 31 register findings are confirmed (19.4%; R18's Apertus
filter did not help). Raise its precision enough to ship it on by default, honestly. R22 writes a second rule set
beside the frozen R15 block (which stays byte for byte as frozen, `R5_ON` untouched) and fixes now how it is judged.

- **The split, as R15 (`audit.half()`: md5 of the limitation id even = dev).** Of the 31 R15 register findings, **dev
  (10)**: O01 AMVUTTRA.01a FR (real), G03 BEYONTTRA IT (real), G05 ERBITUX5 FR, G13 MABTHERA.02 FR, G16 TRUXIMA.02 FR,
  W03 LEQVIO.01 IT, W04 PRALUENT.01a IT, W06 STELARAPP4 FR, W07 STELARAPP4 IT, W09 TEPKINLY.01b FR (8 not). **Held
  (21)**: O02 NPLATE4 IT, O03 OPDIVO.03a IT, O04 WYNZORA IT, G01 and G02 AMVUTTRA.02 FR, G04 DECADURABOL2 IT (minor), G06
  GALAFOLD3 IT, G07 HEMLIBRA.XXb IT, G08 KEYTRUDA.03 FR, G09 KEYTRUDA.03 (KN407) FR, G10 KEYTRUDA.XX IT, G11 LIORESAL FR,
  G12 LIORESAL IT, G14 RIXATHON.02 FR, G15 RUXIENCE.02 FR, G17 VYNDAQEL.01b IT (real), G18 ZAVICEFTA2 FR (minor), W01
  HEMLIBRA.XXb FR (minor), W02 IDEFIRIX IT, W05 REPATHA.01a IT, W08 TEPKINLY.01a FR. Held precision before: 4 of 21 =
  **19.0%**. Of the three named finds, AMVUTTRA.01a and BEYONTTRA are dev, VYNDAQEL.01b is held.
- **What is and is not unseen, stated now.** Design data are the dev-half register texts and findings, their R15
  annotator notes, and the R15 dev planted copies (`tools/audit_inject.py --protocol r15 --half dev`, seed 20261015).
  No held-half limitation text is opened and the new rules are not run on the held half (register or planted) before
  the freeze. But the held findings' ids and one-line annotator notes have been public since R15
  (`eval/labels/audit_r15_20261006.tsv`, the docs' list of false-positive kinds) and were read when this rule was
  written; the classes named below come from the dev notes and from that public list (sentence misalignment, FR
  restrictive `ne … que`, a negation covering an enumeration, range and stop-rule pairing, number words in unrelated
  clauses). So held precision measures whether class-level rules remove known classes without item tuning, not an unseen
  error rate; it is reported with that caveat. No rule may name a product, a limitation or a held phrase.
- **Planned changes (class-level; lexicons and the one threshold choice below written on dev only).** Deterministic,
  stdlib, no model; a new block `round 5b (PREREG R22)` in `audit.py` reusing the R15 parser and sentence splitter.
  (1) *Stricter alignment for `operator`.* Directions are compared per aligned sentence pair, never across the whole
  text (R15 paired equal values anywhere in the text: the wrong clause or date). Threshold choice fixed now: the
  strictest of (a) R15's judged pairs `aligned()`, (b) every `align()` pair with cost ≤ 0.4, (c) every `align()` pair,
  whose operator recall on the dev planted copies is ≥ 65%. (2) *Ranges and stop rules.* Both ends of a range written
  with glue words (`vom … bis zum`, `du … au`, `dal … al`, `zwischen … und`, `entre … et`, `tra … e`, dates included)
  have no direction. A bound is negated when a clause negation precedes it anywhere in its sentence (a negation covers a
  whole enumeration: `non … più di 60 g … e più di 120 g`), or, in German, follows it in its clause (verb-final:
  `mindestens 20 … nicht erreichen`). Occurrences of a value are paired in order; a finding only when the two bounds have
  the same negation status and opposite directions; a negated bound against an un-negated one is not judged (¬≥ = <;
  scope too uncertain). (3) *Only clause negations trigger a `negation` finding.* Word negations block a finding but no
  longer raise one: hyphen compounds (`nicht-…`, `non-…`), the R15 narrow list (ohne, unzureichend, refraktär, sans,
  senza …), FR/IT `non` before an adjective or participle (R15 already), FR bare `non` (French negates a clause with
  `ne`/`n'`), and German attributive `nicht` (`nicht` + an inflected adjective or participle before a noun: `bei nicht
  abgeschlossener Familienplanung`). (4) *Restriction pairs.* `nur`, `lediglich`, `ausschliesslich` / `seulement`,
  `uniquement`, `exclusivement`, `ne … que` (any distance in the sentence, across commas) / `solo`, `soltanto`,
  `solamente`, `unicamente`, `esclusivamente`, `non … che` count as restriction words: they block a finding on the other
  side, and a `ne … que` / `non … che` is not a clause negation. (5) *Misalignment guard for `negation`.* A one-sided
  clause negation in pair k is reported only when, over pairs k−1, k, k+1 and the unaligned sentences between them, the
  negated side has more clause negations than the other side (a negation moved to a neighbouring sentence by the
  alignment is not a finding). (6) *`number_word`: substitutions only.* A number-word value is reported only when the
  aligned sentence of the other side states a different value in its place (a one-sided number word, or a one-sided
  value of the same unit class); an omission (a list announced as "drei Therapien", a count the other side leaves
  implicit) is not. A number word glued to or compounded with the next word on the other side (`deuxlignes`,
  `Fünffache`, `dreimal`) reconciles it.
- **Freeze.** The commit of the round-5b block; its byte and rule-logic sha256 (as `r5_logic_sha`) go into the results;
  `tests/test_audit_r22.py` fails if the logic drifts. After the freeze only reporting may change. R15's block, its
  fingerprints, `findings_r5`, the 38 existing findings and every committed R15/R18 result stay unchanged (tests).
- **Register run and labels.** The frozen R22 rules on the 6 Oct 2026 register (`data/audit/audit_r22_20261006.json`).
  An R22 finding **reuses** the R15 final label when an R15 finding has the same limitation, language and kind and (operator)
  the same value, (negation) the same negated side and an overlapping target sentence, (number_word) a shared value on
  the same side. Every other R22 finding is **new**: all new findings (both halves) get two fresh blind Claude
  annotators and a third on disagreement (`eval/labels/PROTOCOL.md`; R15's worklist fields and question, neutral ids
  `S00`…, `random.Random(20261022)` order, the second annotator in reverse). No human labels, no model API calls.
- **Planted recall (held, R15's copies).** The R15 held planted set regenerated (seed 20261016, 100 per type and
  language, eligibility under the frozen R15 audit as in R15), checked identical by re-scoring it with the R15 rules
  (operator 149, negation dropped 88, added 111, number word 168 of 200 must reproduce), then scored with R22 in place
  of R15 under R15's detection rule (`tools/audit_inject.py --protocol r22 --half held`). Reported per type and
  language, Wilson 95%, beside R15 on the same copies; the dev planted run beside it, labelled dev.
- **Decision rule, fixed now.** The module ships **ON by default** only if all hold: (i) on the **held** half, precision
  of the R22 findings (all three kinds pooled; confirmed = real or minor by the final label) **≥ 50%**; (ii) held planted
  recall **≥ 60% for operator flips** and **≥ 40% for dropped negations**; (iii) **AMVUTTRA.01a (dev), BEYONTTRA (dev)
  and VYNDAQEL.01b (held)** are still found, by the same kind and language. Otherwise it stays opt-in and the result is
  reported as it is. Reported beside the decision, not deciding: precision per kind and on dev and all, strict-real
  precision, Wilson 95% intervals, held recall for added negations and number words. This repository does not flip the
  default itself: a pass is reported for the maintainers to integrate (`score.audit_r22` -> `eval/results/audit_r22.json`,
  re-derived by `replay`).

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
- **R12, 10 Oct 2026:** house wording in the drafting prompt (variant v3-terms), pre-registered at commit 152825a
  (14:06 UTC) before any run; house wording mined from 20260801 (August) and 20260901 (September) only. Q8_0: shadow runs
  38058301756 (August) and 38058337474 (September; a first dispatch with 8 shards, 38058304511, was cancelled before any
  drafting and re-dispatched with the pre-registered 6), 6 CPU shards each, all succeeded, build certificate
  8b-q8_0-fresh166 verified on every shard, 45 and 81 calls. 70B: development gateway, 51 and 91 calls, all served by
  swiss-ai/apertus-v1.5-70b, re-executed from its own recorded responses (22 of 22 and 44 of 44 drafted records equal).
  The variant's first prompt of every model-call item is in each run's call log (22 of 22, 40 of 40 per model). Prompts
  unchanged by the block (3 in August) gave the frozen run's output with both models. Frozen -> v3-terms, n = 22
  (August) and 41 (September), no-model start 0 identical: **August Q8_0** identical 1 -> 3 (+4.5 -> +13.6 points, now
  holds), flagged 81.8% -> 63.6% (now holds), REAL 0 -> 0 (holds), stale + German 1 -> 1 = 4.5% (fails): **does not
  meet R0**. **August 70B** identical 0 -> 0 (+0.0, fails), flagged 81.8% -> 68.2% (now holds), REAL 0 -> 1 = 4.5%
  (fails), stale + German 3 -> 4 = 18.2% (fails): **does not meet R0**. **September Q8_0** identical 3 -> 8 (+7.3 ->
  +19.5, holds), flagged 92.7% -> 73.2% (fails), REAL 0, stale + German 0 (hold): **does not meet R0**. **September
  70B** identical 4 -> 9 (+9.8 -> +22.0, holds), flagged 82.9% -> 80.5% (fails), REAL 0, stale + German 0 (hold):
  **does not meet R0**. The frozen pipeline meets R0 in none of the four either, so no pair qualifies as a candidate under
  the decision rule; the frozen default is unchanged. Labels: 19 distinct ready non-identical drafts (21 model rows), two
  blind annotators agreed on all 19; one REAL went to a third (German), majority REAL. Final, per model row: 13 equivalent, 2 cosmetic,
  3 German (BAG's typo "GLP1-1-Analogon" carried through by the number lock, as in R10), 2 stale (a fragment of a deleted
  sentence left), 1 REAL (French draft keeps "Maximal" and drops "médicamenteuse"). Most remaining differences among
  acceptable drafts are one insurer word: the Italian termbase head «assicuratore» where BAG writes «assicuratore
  malattie», and BAG's own minority French « assurance maladie » (`eval/results/r12_terms.json`,
  `eval/labels/r12_terms_ready.tsv`).
- **R14, 10 Oct 2026:** pre-registered at commit c05a46f before any annotation; 7 fresh blind Claude annotators (no
  model API calls). **(A) Audit relabel:** 49 findings, two blind annotators (the second in reverse order) agree on
  confirmed (real or minor) for 49 of 49, κ 1.000, and on the three-way answer for 48; a third took the one split
  (MiGeL MG05: real / minor / not, majority confirmed). Majority precision: register **17 of 27** (63.0%, Wilson [44.2,
  78.5]; first annotation 16), terminology **11 of 11** (first 8; strict "real" 4: the French drug-class errors; the
  four ungrammatical Italian texts and three French «communiqué» for the register's «transmis» are "minor"), MiGeL +
  Analysenliste **6 of 11** (first 7). Majority vs first single labels: 44 of 49 (κ 0.773); changed: register A19 (the
  number check's view of the Italian typo «se mesi», no -> yes), terminology C02 / C03 / C06 (no -> yes, wording only),
  Analysenliste AL01 (yes -> no: both read FR "1 + max 4 additional" as DE's 5). As pre-registered, the README and
  report numbers switch to the majority (`score.audit_eval`, `score.audit_more` read `eval/labels/audit_relabel.tsv`); the
  first labels stay as `first_annotation` (`eval/results/audit_relabel.json`, `audit.json`, `audit_more.json`).
  **(B) In-span sensitivity:** 38 hand-written plants inside the touched sentence (scope 11, condition 12, number on the
  wrong noun 8, and/or 7), two blind annotators per worklist, reference shown: severe (REAL or stale) by both **38 of
  38** (Wilson 95% [90.8, 100]), every type, language and family; 33 REAL by both, the 5 plants that keep part of the old
  text called stale by one or both. False alarms on the 38 untouched copies: 0 needs-fix, 0 severe. Real drafts: stale
  12 of 12 and German 14 of 15 severe by both; of the 3 earlier REAL labels both agree on 1 (either 3), as in R11. The 95%
  bounds on severe errors among ready drafts are unchanged by the recall (5.5% 70B, 5.8% Q8_0)
  (`eval/results/annotator_sensitivity_inspan.json`, `eval/labels/inspan_sensitivity.tsv`).
- **R16, 10 Oct 2026:** memorisation probe, pre-registered at commit d9dee44 before any model call. 70B: development
  gateway, tag `gleichlaut-r16-70b`, 333 requests for 342 texts (9 texts share a first half with another, so the same
  request), all served by `swiss-ai/apertus-v1.5-70b`, USD 0.09; 8B Q8_0: workflow `r16-8b`, run 38063684596 (12 CPU
  shards, all succeeded), no logit mask. Next 10 words exact: **70B** T 0 of 160, P 3 of 120 (2.5%), N 0 of 62;
  **8B** 0 / 0 / 0. T − N = 0.0 points [0.0, 0.0] for both: **no evidence of memorisation beyond the negative
  control**. P − N = 2.5 [0.0, 5.8] (70B) and 0.0 (8B): neither meets the criterion, so the probe did not detect
  memorisation even of texts unchanged since before 2023, and the null result on T is weak evidence. Secondary: mean
  leading words equal, 70B T 0.53, P 0.85, N 0.23 (T − N 0.31 [0.08, 0.54], Mann–Whitney p 0.041; longest run in T 6
  words, in P 16); chrF of the first ≤ 100 words T 15.3, P 17.8, N 17.3 (T − N −2.0 [−5.2, 1.1]); 8B leading words
  0.32 / 0.38 / 0.23, chrF 14.2 / 15.5 / 12.8, no difference with a CI excluding 0. Where BAG's old text continues the
  same first half differently, the 70B continuation is closer to the new text in 15 of 45 T texts (old 22, tie 8) and
  11 of 31 N texts (old 15, tie 5): no pull toward the published answer (`eval/results/memorisation.json`).
- **R15, 10 Oct 2026:** pre-registered at commit 28fe22b before the rules were written; rules written on the dev half
  only and frozen at commit 6a2c269 (round-5 block sha256 `2d5dcaaf3b7a8c53…`). Disclosure: one full-register timing run
  before the freeze printed the per-half finding counts (not the texts); no rule changed after it. One deviation from
  the R15 wording: the operator check takes every value with an operator, not only unit-bound ones (dev planted flips
  sat on scores without a unit). **Held planted recall** (seed 20261016, 100 copies per type and language, 784 eligible
  held triples; 8 full-register verifications identical): operator 0 → **74.5%** [68.0, 80.0], negation dropped 0 →
  **44.0%** [37.3, 50.9], negation added 0 → **55.5%** [48.6, 62.2], number word 30.5% → **84.0%** [78.3, 88.4]
  (dev design run: 73.5 / 48.0 / 51.0 / 87.0). **Register** (6 Oct 2026): 31 new findings on 27 limitations (operator 4,
  negation 18, number_word 9); the existing 38 findings (27 + 11 terminology) unchanged, number findings gain only the
  display field `counterpart` (Nemluvio N18: IT 4). **Precision**: all 31 labelled by two fresh blind annotators (the
  second in reverse order); they agree on all 31 (κ 1.000), so no tie-break. Real or minor: operator 1 of 4 (25.0%),
  negation 4 of 18 (22.2%), number_word 1 of 9 (11.1%). **Outcome:** operator and number_word meet the recall bar but
  not the precision bar; negation misses both. No kind passes, so all three are off (`R5_ON`). README and report keep
  them as blind spots and state the measured recall. New real divergences among the findings: AMVUTTRA.01a FR
  stop criterion "≤ 10" where DE/IT say "> 10"; BEYONTTRA and VYNDAQEL.01b IT "on deve essere combinato" (the "non" of
  "darf nicht" lost its n) (`eval/results/audit_r15.json`, `audit_injection_r15_held.json`,
  `eval/labels/audit_r15_20261006.tsv`).
- **R17, 10 Oct 2026:** pre-registered at commit 3ddc331 before any annotation or model call; 8 fresh blind Claude
  annotators, 117 Apertus requests. **(A) Real errors:** 29 FR/IT changes with the German byte-identical, 12 typography
  only, **17 content changes, all used** (fewer than 30): negation/operator 2, words 15, number 0; 10 are one Opdivo
  French wording sweep; 2 reversed as declared. Needs fix on the 17 error records, both / either: **(a) 5 / 5** (Wilson
  95% [13.3, 53.1]), **(b) 7 / 11**; severe (REAL, stale, german) both 4 under each (either 4 / 5), the same 4 (Keytruda
  «remise» and missing VAT sentence, Jemperli IT «di prima linea» added, the two dropped Opdivo code sentences); the
  sweep 0 of 10 under (a) (equivalent), 5 by either under (b); the other 7: 5 (a), 6 (b) by both. Misses: Resolor IT
  «assicurazione malattie» (both protocols), Opdivo IT «dell'indicazione» (a). Controls: needs fix by either 1 (a), 10
  (b) (severe 1, 4), most naming a defect still in BAG's current text (Opdivo .04 FR lacks «avancé»). Needs-fix κ 0.892
  (a), 0.531 (b) (`eval/results/annotator_real_errors.json`, `eval/labels/r17_real_errors_{a,b}.tsv`). **(B) Apertus
  70B:** development gateway, tag `gleichlaut-r17-70b`, 117 of 117 served by `swiss-ai/apertus-v1.5-70b`, 0 unparsed,
  USD 0.14. Audit: real 36, minor 13, not 0, so it confirms all 49; agreement with the R14 Claude majority on confirmed
  34 of 49 = the majority's own confirmed share, **κ 0.000**; three-way answer 25 of 49. Part A: errors flagged 2 of 17
  (a), 1 of 17 (b); controls 0 and 0; needs-fix κ with the Claude annotators 0.532 / 0.452 (a), −0.059 / −0.059 (b).
  The 70B does not discriminate on either task, so it neither confirms nor contradicts the Claude labels
  (`eval/results/annotator_crossfamily.json`, responses `data/r17/apertus70b/`).
- **R18, 11 Oct 2026:** pre-registered at commit 6eb5201 (19:12 UTC, 10 Oct) before any model run; tool and items at
  e28a421; workflow `r18-8b`, run 38078975036 (20 CPU shards, all succeeded, build certificate 8b-q8_0-fresh166 verified
  on all 20; no smoke run), 1,366 of 1,366 pairs, 2,732 calls (`data/r18/runs/8b_q8_0/`). **Planted** (R15 held copies,
  800 + 800 controls): threshold by Youden's J on the fit half t* = 5.9e-8 (J 0.781: controls score near 0); AUROC
  **test 0.955** [0.941, 0.968] (fit 0.943), at t* TPR 84.2%, FPR 4.1% on test; by type (test) operator 0.997, negation
  added 0.982, number word 0.949, negation dropped 0.889; kept 472 of the 516 copies the R15 checks detect. **Register**
  (31 findings): kept 13, of them confirmed 2: precision 6 of 31 = 19.4% before, **2 of 13 = 15.4%** after (Wilson 95%
  [4.3, 42.2]); kept BEYONTTRA (score 0.497) and VYNDAQEL.01b (0.357), dropped **AMVUTTRA.01a** (FR "≤ 10" vs "> 10",
  score 1.3e-12: both orders answer "Ja"), DECADURABOL2, ZAVICEFTA2, HEMLIBRA.XXb (all minor). The highest scores (≈ 1)
  go to 6 false findings (AMVUTTRA.02 FR twice, a Keytruda IT, one Italian «cinque volte» sentence shared by LEQVIO,
  PRALUENT and REPATHA). Per kind kept / confirmed: operator 1 / 0, negation 9 / 2, number word 3 / 0. AUROC confirmed vs not 0.453,
  real vs rest 0.631 (descriptive). Generated answers: "Ja" 2,051, "Nein" 681 of 2,732. **Outcome:** precision 15.4% < 50%
  and 2 < 4 of the 6 confirmed kept: **fails**; operator, negation and number_word stay off and the blind spots stand.
  The 8B tells a planted one-word flip from its untouched sentence, but not the register's real divergences from its
  alignment and parser artefacts (`eval/results/audit_apertus_filter.json`).
- **R15 post-freeze note (R4), 11 Oct 2026:** the round-5 block's byte fingerprint recorded in the results
  (`rules_sha256` `2d5dcaaf…`, commit 6a2c269 and the run commit 8b3eb89) differs from the code since 5e005cb (`0a869fe9…`).
  What changed: one comment, on the `R5_ON` line ("set by the R15 outcome" became "R15 outcome: no kind passed; all
  off"); `R5_ON` itself stayed all `False`. Later commits changed `audit.py` outside the block only (display: register
  excerpts from the sentence alignment, f10d3bd). Evidence that the outputs are identical: the frozen code (8b3eb89) and
  HEAD (f10d3bd) re-run in separate trees on the 6 Oct 2026 register and on the R15 held planted set (seed 20261016,
  800 copies): the 31 round-5 findings, the 38 existing findings, and every per-type recall, subtype, miss and baseline
  count are identical between the two, and identical to the committed `audit_injection_r15_held.json` (operator 74.5%,
  negation dropped 44.0%, added 55.5%, number word 84.0%). Why the fingerprint drifted: it hashed bytes, comments
  included. Fix: a second fingerprint of the rule logic only (`audit.r5_logic_sha`: the block's syntax tree without
  comments, docstrings or layout; the same on Python 3.9 and 3.12), `480ef3e3…`, equal at 6a2c269, 8b3eb89, 5e005cb and
  HEAD; recorded as `rules_logic_sha256` in the audit summary and `eval/results/audit_r15.json`, with the byte
  fingerprint kept as recorded. `tests/test_audit_r5.py` fails if the logic or the record drifts. No rule, finding or
  result changed.
- **R19, 11 Oct 2026:** pre-registered at commit 8f5f16d (23:54 UTC, 10 Oct) before any model run; tool, vendored inputs
  and workflow at a3f930f; a smoke run of 2
  questions and 2 cells per shard on 2 shards (run 38096748736, outputs not used); workflow `r19-8b`, run 38097175838
  (20 CPU shards, all succeeded, build certificate 8b-q8_0-fresh166 verified on all 20), 250 of 250 questions and 792 of
  792 cells (`data/r19/runs/8b_q8_0/`); prompt token counts equal to the API's in every generation and forced-choice
  call. **MMLU:** Q8_0 **78.4%** (196 of 250, Wilson [72.9, 83.1]); shared model − Q8_0 **+6.0** [1.6, 10.4]; Q8_0 − v1
  8B **+7.6** [2.0, 13.6]; letters equal to the shared model's 211, to the v1 8B's 184. **Battery:** text byte-identical
  to fp1-nes **322 of 792 (40.7%)**, to the 8B name 324 (Q8_0 never ends an answer with a period; fp1-nes does in 382
  cells, and 341 texts differ only by it); generation decisions equal to fp1-nes 702 (88.6%), to the 8B name 699;
  forced-choice decisions equal to tp2 716 (90.4%), to the 8B name 706; log-odds r 0.875 with tp2 (mean |Δ| 9.39), 0.867
  with the 8B name (8.78); Q8_0's own generation and forced choice agree on 782. **Outcome:** MMLU-low fails (78.4% >
  78%, although the CI of the gap excludes 0), fp1-nes is not matched far more than tp2 (gap −1.8 points), Q8_0 is not
  ≥ 80% and the CI excludes 0: **O4, inconclusive**; the report and README say so and keep "the 70B as Public AI served
  it". Post hoc (not in the rule): on the 648 parity cells Q8_0 agrees with tp2 on 605 and with the 8B name on 603
  forced-choice decisions (tp2 with the 8B name on 626), against 638 for the recorded Q8_0 with bf16 DPO
  (`eval/results/identity_r19.json`).
- **R21, 11 Oct 2026:** pre-registered at commit aff91df (07:29 UTC) before any model run; variant, mined 2025 house
  wording, prompt record and workflow at 4f6d972. Workflow `r21-8b`, GitHub Actions CPU runners, build certificate
  8b-q8_0-fresh166 verified on every shard: fresh 166 run 38121568986 (13 shards, 303 calls), September 38121571690 (4
  shards, 81 calls, 66 distinct requests), August 38121574420 (3 shards, 40 calls); every request carried the system
  message (sha256 `a81624dc…`); `make run` re-executes all three from their recorded exchanges (166 of 166, 44 of 44,
  22 of 22 records equal, 0 misses; `data/r21/runs/`). **(A) fresh 166, R0 as R1 (M2):** v4-system identical to BAG
  **13.9%** (23 of 166; +7.8 points over rules-only [3.0, 13.9]), flagged **65.1%**, ready 58, among them 0 REAL, 0
  stale, 0 German (95% upper bound on severe among ready 6.2%): **meets R0**. Certified frozen run: 17.5% (+11.4 [4.8,
  18.7]), flagged 62.7%, ready 62 (23 of them "minor", the non-house "assurance obligatoire de maladie"; v4-system
  ready: 13 exact, 38 equivalent, 4 preexisting, 3 cosmetic, 0 minor). Paired: identical outputs 54 of 166, flag
  agreement 148 (κ 0.765), identical-to-BAG gained 2 and lost 8 (wb000, wb002, wb072 FR and IT, wb038-fr, wb040-fr);
  of the 13 model-call items whose user prompt is unchanged (system message only), 8 give the frozen output. Seeded 20
  flagged drafts: 8 need no fix. **(B) live months (not unseen), frozen -> v3-terms -> v4-system, Q8_0:** August (n 22)
  identical 1 -> 3 -> 4 (+18.2 points, holds), flagged 81.8% -> 63.6% -> 54.5% (holds), stale + German 1 -> 1 -> 0
  (holds), REAL 0 -> 0 -> **1 = 4.5% (fails)**: a French draft keeps the deleted prior-approval sentence («Après
  accord sur la prise en charge», XTANDI.01; REAL by all three annotators): **does not meet R0**. September (n 41)
  identical 3 -> 8 -> 10 (+24.4, holds), flagged 92.7% -> 73.2% -> **70.7% (fails**, 29 of 41), REAL 0, stale + German 0
  (hold): **does not meet R0**. **Decision as pre-registered:** R0 holds on A but on no live month, so v4-system is
  not a candidate default; reported as is, and the frozen default stays. Labels: 29 records (A: 5 ready, 18 of the
  flagged sample; August 2, September 4; 40 ready fresh-166 drafts reused a label of a byte-identical earlier draft),
  two blind annotators (needs fix 28 of 29, κ 0.931; class 22 of 29), a third on 10; final: 10 equivalent, 3
  preexisting, 4 cosmetic, 4 minor, 1 German, 3 stale, 4 REAL (3 of them flagged) (`eval/results/r21_system.json`,
  `eval/labels/r21_system_ready.tsv`).
