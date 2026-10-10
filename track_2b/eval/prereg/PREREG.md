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
  `eval/certificates/8b-q8_0-fresh166.json`). Q4_K_M stays the default build (8 GiB box); Q8_0 is the certified option
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
