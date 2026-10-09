# Technical report: Gleichlaut

Keeping the French and Italian of Switzerland's drug-reimbursement conditions in step with the German, with Apertus.
Numbers never pass through the model; frozen deterministic checks decide what is ready.

- **Track:** Track 2B: Gleichlaut
- **Event:** Online
- **Team:** 444
- **Demo:** `VIDEO_URL` · review register: https://mi11ione.github.io/gleichlaut/
- **Declared maturity:** feasibility study

## 1. Summary

**The job.** BAG maintains the 1,688 reimbursement conditions ("limitations") of the Spezialitätenliste in German,
French and Italian under one identifier, as three text fields in its ePL editor, published monthly for the 9.08 million
people in basic insurance (22.6% of residents name French and 7.8% Italian as a main language). In 7.5 months of 2026,
216 German texts changed (28.7 a month); BAG updated French and Italian in the same month for 208 of them. BAG's own
review asks applicants whether "die Übersetzungen sind kongruent". Where they are not, the difference is a number: in
the 6 Oct 2026 register, 10 limitations carry 5 independent divergences (Nemluvio every 8 weeks vs "ogni 4 settimane";
Diaphin 6% vs 12%; a French-only "≥ 62.5 kg" condition in three etanercept biosimilars; a 16 kg limit missing in French
for Cresemba; a 15–30 kg tier missing or shifted in French for four Dupixent limitations).

**Two tools, one rule.** *Draft*: when the German changes, Gleichlaut locks the old French/Italian outside the edit,
replaces every number with a slot code that code writes back, lets Apertus rewrite the wording, and runs a frozen stack
of deterministic checks that marks the draft ready or flagged and explains why in the reviewer's language. *Audit*:
compares the numbers of every limitation across the three languages and lists the conditions that disagree. The model
never writes a number and never judges anything.

**Results.** On a pre-registered held-out set of 166 French/Italian amendments from 2025 (154 in edit patterns never
seen during design; checks and resources hashed before any output existed), Apertus 70B drafts equal BAG's published
text **17.5%** of the time against **6.0%** for the translator's current starting point (old text with numbers
updated): **+11.4 points, 95% CI [4.8, 18.7]**. They cut the token edits still needed to reach BAG's text by **42.4%**
[31.0, 54.1]. **39.8%** of drafts come out ready, with **0** meaning errors, stale changes or German left among them,
and a rerun with a new seed passes the same rule (+12.0 points, 41.6% ready). The audit reduces 1,688 limitations to
**21** lines that contain **all 10** known divergent limitations. A draft costs **CHF 0.0024** at a Swiss provider's
published price for Apertus 70B. `make run` re-executes the recorded runs offline and re-derives every number.

## 2. Architecture

![Pipeline](docs/pipeline.svg)

| Module (`src/gleichlaut/`) | Role |
|---|---|
| `frozen/` | the research code, byte-identical and hash-checked: lock, slots, rules, prompt, drafting loop, checks, re-ask, scorer |
| `core.py` | executes the frozen definitions via `ast` with an injected model backend (no re-implementation) |
| `audit.py` | numeric congruence of DE/FR/IT across the register; `audit_item` for single drafts |
| `backends.py`, `certify.py` | `openai` (any `LLM_BASE_URL`, served model checked), `llamacpp` (CPU GGUF, digit mask), `cache` (hash-addressed replay); endpoint-bound certification and drift canary |
| `sl/`, `fed/`, `cli.py month` | ingest the monthly feed or Fedlex versions, mine German changes, draft, resume |
| `emit/`, `ui/` | XLIFF 1.2 and 2.1 (validated against the OASIS XSDs), FHIR R5 (checked against the CH EPL profile), review register |
| `replay.py`, `score.py` | `make run`: verify the freeze, re-execute recorded runs, re-score, compare |

### Target architecture

On-premise for every lane; air-gapped for everything except the 70B drafting lane. The audit, the checks, the register
and the XLIFF/FHIR output are Python standard library plus `lxml`. Statutes run Apertus 8B (GGUF Q4_K_M) on CPU in
process. SL drafting runs Apertus 70B on an endpoint the user controls: own GPUs (bf16 144.6 GB) or a Swiss provider
(Infomaniak, Swisscom, PHOENIQS, Safe Swiss Cloud and OnPrem.ai serve it from Switzerland; Infomaniak CHF 0.70 / 2.50
per million input/output tokens). No provider-specific code exists: an endpoint is admitted only by a certificate bound
to its address and served model, earned by re-running the frozen 166-item suite (`make certify`); a canary detects drift.

| Lane | Model, where | External services at runtime | Data sent |
|---|---|---|---|
| Audit, checks, register, XLIFF/FHIR | none | none | none |
| Federal statutes | Apertus 8B GGUF, CPU, in process; drafts go to review | none | none |
| SL conditions | Apertus 70B on a certified, user-controlled endpoint | that endpoint only | one public limitation text (DE old/new, FR or IT), numbers as slot codes |

Build time only: Docker base image (pinned by digest), PyPI, the sha256-pinned GGUF. Runtime dependencies and licences
(Apache-2.0 weights under the Apertus AUP): `docs/dependencies.md`, `docs/target-architecture.md`. Public AI served the
evaluation only.

## 3. Use of Apertus

### 3.1 Models and builds

| Use | Model / build | Where it ran for the reported numbers |
|---|---|---|
| SL drafting | Apertus v1.5 70B | Public AI through a budget gateway; temperature 0; plain user messages; served model logged |
| SL 8B arm; statute drafting | Apertus v1.5 8B, MLX 4-bit DWQ | a laptop; greedy; digit and number-word logit mask (SL) |
| 8B that ships | Apertus v1.5 8B GGUF Q4_K_M | CPU via llama.cpp; agreed with bf16 on 622 of 648 decisions in our parity battery (MLX 4-bit: 548) |

Public AI's `apertus-v1.5-8b` name serves the 70B (identical greedy outputs in 760 of 792 cells, 70B-level MMLU), so
every 8B number here comes from local runs.

### 3.2 How the model is used, and which size

One prompt (Appendix A): old and new German, a code-derived list of the German changes, and the old French/Italian
text, numbers as slot codes; the model returns the amended paragraph. The 70B wrote 0 digits in 285 calls; in 3 of 166
drafts it wrote a number word itself ("due", "quatre", "quattro"), and all 3 were flagged; the 8B cannot emit either.
**Size is measured on the same items in both directions.** SL conditions: the 8B flags 85.0% of its drafts (cap 70%),
the 70B passes, so SL uses the 70B. Federal statutes (pre-registered R5, 120 paragraphs): the 70B is no better (exact
48.3% vs 50.0%; 2 vs 0 real errors among drafts marked ready), so statutes use the 8B on CPU, and their drafts go to
review because German job titles ("EFZ") need a terminology list that only exists for the SL so far.

### 3.3 Where Apertus fell short, and what does that job instead

| Task | Result | Done instead by |
|---|---|---|
| Free translation of the new German (8B, dev 120) | 0% exact; negation/modality/number changes in 78 of 120, none flagged ("deve" → "dovrebbe") | locked rewrite of the old text |
| Edit only a marked span (dev 120) | span ignored in 73% (8B) and 81% (70B) of windows | whole-paragraph rewrite + lock check |
| Judge DE/FR/IT equivalence (9 known Fedlex divergences) | 8B 0 of 9; 70B 0 of 9 ("they differ" in 2 of 270 answers) | deterministic checks and the audit |
| Type numeric conditions | 8B operator accuracy 36%; errors correlated across languages | code (slots, audit) |
| SL drafting with the 8B (dev 120) | flagged 85.0%; 1 ready draft reverses a meaning | the 70B |
| SL drafting, 70B with the earlier checks (out-of-sample 242) | failed the rule: 4.1% of items with German left, unflagged | copied-from-German, terminology and vocabulary checks, then a new held-out set |
| Self-correction | 8B greedy retry fixed 0 of 26; 70B re-ask fixed 3 of 98 | one re-ask, kept only if every check passes |

## 4. Data

| Source | Use | Licence |
|---|---|---|
| BAG ePL FHIR R5 feed, 9 usable 2026 snapshots | 2026 change pool (dev 120, out-of-sample 242), backtest, audit (6 Oct) | official publication |
| SL XMLPublications Jun and Jul 2025 (Wayback captures) | the held-out set (166); check resources (Jun 2025 only) | official publication |
| Fedlex consolidated versions (SPARQL + AKN XML) | statute lane (120 FR/IT paragraphs, 26 acts) | not protected (URG Art. 5) |

A change counts if at most 60% of its tokens changed (27 larger rewrites in the window go to a translator). The ePL
export dropped every `<…>` span in the Feb–Apr and 4 May 2026 snapshots; May is excluded and affected pairs are dropped.
No personal data.

## 5. Evaluation

Exact = equal to BAG's published text after whitespace/apostrophe normalisation. CIs: paired cluster bootstrap over
German changes. Every ready non-exact draft was read in full; a seeded 20 flagged drafts estimate review load. Pass rule
(pre-registered): unflagged real errors ≤ 1%, unflagged stale + untranslated ≤ 2%, exact ≥ rules + 5, flagged ≤ 70%.

| Setup (FR+IT) | Set | n | Exact | Δ vs rules [95% CI] | Flagged | Ready | Ready with real / stale / untranslated | Rule |
|---|---|---|---|---|---|---|---|---|
| Rules only (old text + numbers) | held-out | 166 | 6.0% | | | | | |
| **Apertus 70B + checks + re-ask** | **held-out** | **166** | **17.5%** | **+11.4 [4.8, 18.7]** | **60.2%** | **39.8%** | **0 / 0 / 0** | **PASS** |
| same, unseen edit patterns | held-out | 154 | 15.6% | +12.3 [5.8, 20.1] | 60.4% | 39.6% | 0 / 0 / 0 | PASS |
| same, rerun with seed 1 (R2) | held-out | 166 | 18.1% | +12.0 [5.4, 19.3] | 58.4% | 41.6% | 0 / 0 / 2 | PASS |
| Apertus 70B, earlier checks | out-of-sample | 242 | 29.3% | +14.9 [9.9, 20.7] | 61.6% | 38.4% | 1 / 0 / 10 | FAIL |
| Apertus 8B (MLX DWQ), no re-ask | dev | 120 | 15.0% | +9.2 [3.3, 15.8] | 85.0% | 15.0% | 1 / 0 / 0 | FAIL |
| Statutes: 8B | Fedlex (dev) | 120 | 50.0% | rules 35.0% | 31.7% | 68.3% | 0 / 4 / 4 | review all |
| Statutes: 70B | Fedlex (dev) | 120 | 48.3% | rules 35.0% | 23.3% | 76.7% | 2 / 1 / 5 | review all |

![Exact-match gain per arm](docs/fig_arms.svg)

**Reviewer effort.** Starting from the draft instead of the old text with updated numbers, a translator makes 42.4%
fewer token edits to reach BAG's published text (95% CI [31.0, 54.1]); 59.1% fewer on ready drafts; fewer on 114 of
166 items, more on 29. Of a seeded 20 flagged drafts, 13 needed no change: the checks are tuned to miss nothing.

**Stability.** The seeded rerun reproduced 69.9% of final outputs byte-for-byte and the ready/flagged verdict with
κ 0.963; the API itself is not deterministic at temperature 0, which is why certification re-runs the whole suite.

**Audit.** On the 6 Oct 2026 register: 21 findings in 17 limitations; all 10 known divergent limitations and all 13 of
their known values are among them; a blind annotation finds 10 of the 21 real (47.6%, Wilson [28.3, 67.6]); the other
11 are paraphrases such as "ab 18 Jahren" vs "adultes". Rules were frozen before measuring recall.

**Labels.** Every ready non-exact draft and the flagged sample were read in full by a blind annotator; a second blind
annotator re-labelled them (agreement 62 of 69, κ 0.532) and found no meaning error, stale change or German left among
the ready drafts; a third broke all 7 disagreements. Worklists and labels are in `eval/labels/`, so the labelling can be
re-run by anyone.

**Cost and scale** (recorded tokens: 285 calls; 17.15 s of model time per item, sequential):

| Volume | Items a month | Public AI (evaluation price) | Infomaniak 70B | Model time, sequential |
|---|---|---|---|---|
| 1× | 57 | $0.16 | CHF 0.14 | 0.3 h |
| 10× | 574 | $1.59 | CHF 1.36 | 2.7 h |

At this volume a per-token Swiss endpoint costs CHF 0.14 a month; dedicated 70B hardware pays only across many lists
(MiGeL and the Analysenliste carry limitation columns in the same three languages).

## 6. Design limits we measured

- **Ready means the amendment is right, not the whole text.** 18 ready French drafts keep an old drug-class
  mistranslation ("inhibiteur de l'enzyme de conversion" for angiotensin-II receptor antagonists) that BAG corrected in
  the same update; the checks compare an amendment with its German change by design, and the audit's numeric scope does
  not cover drug-class names yet.
- **Bounds counted honestly.** 0 errors in 66 ready drafts is 0 in 36 German changes and 18 edit families: 95% upper
  bounds 5.5% per draft, 9.6% per change, 17.6% per family. One boilerplate family supplies half of the ready drafts;
  without it 75.8% are flagged.
- **No check targets direction flips** (increase ↔ decrease); a single dropped word inside an edited window can pass.
- **The held-out gold overlaps the dev pool's inputs:** 22 of the 166 published 2025 texts reappear as old texts in
  the 2026 dev items; the check resources come only from the Jun 2025 capture.
- **The 5 divergences predate our window** (all present at the earliest capture, Jun/Jul 2025), so the backtest cannot
  say where they arose; the audit finds them today.

## 7. Reproducibility

`make run` (Docker, CPU, `--network none` unless `LLM_BASE_URL` is set; about 30 s on a GitHub runner) verifies the
sha256 of the frozen code, check resources and items; re-executes the recorded 70B runs end-to-end from the recorded
responses (every request rebuilt byte-for-byte and found by its payload hash: 285 of 285 for the headline run, 283 of
283 for the rerun, 242 of 242 for dev); re-scores every recorded run against `eval/results/`; drafts 5 statute
paragraphs live if `LLM_BASE_URL` is set; writes and validates XLIFF and FHIR; builds the register. `claims.tsv` maps
every number in this report to a results file; CI fails on drift. Pre-registrations: `eval/prereg/PREREG.md` (R0–R5)
with run timestamps from the gateway ledger. The first out-of-sample run failed its rule; it is reported.

**Coding assistants and labellers.** Code written with Claude Code agents (Anthropic) under the team's direction;
labels by blind Claude annotators. Apertus is the only model at runtime, and no model judges outputs.

## 8. Integration and next steps

BAG writes limitation texts itself (KVV Art. 73) in an ePL editor with one field per language; applicants answer the
"kongruent" question in the triennial review; the federal translation tool is STAR Transit (`docs/sl-process.md`).
Gleichlaut maps onto each: Draft proposes the FR/IT fields when the DE field changes, Audit answers the congruence
question for the whole register, and translators receive XLIFF 1.2/2.1. Shadow mode (`gleichlaut month`) runs on the
public feed every month and grades itself against BAG's publication, so a pilot with the Sektion Arzneimittelaufnahmen
and the ePL team needs no new process. Next: drug-class terms in the audit, a direction-flip check, MiGeL and the
Analysenliste, and a Swiss 70B endpoint certified with `make certify`.

## License

Report CC-BY-4.0. Code Apache-2.0.

## Appendix A: the drafting prompt (verbatim, `frozen/s2/s2b.py`)

```
A Swiss reimbursement limitation (Spezialitätenliste, BAG) was amended in German. Apply exactly the same amendment to the {L} version.
Change only the words that correspond to the German change. Copy every other word and punctuation mark of the old {L} text unchanged. Use the established {L} terminology of the Spezialitätenliste. Numbers are written as slot codes such as ⟨A⟩: copy the slot codes, never write digits or numbers in words.

German (old): {de_old}
German (new): {de_new}
Changes in German:
{changes}

{L} (old): {tgt_old}

Output only the amended {L} text, nothing else.
```

## References

Sources for every external fact: `docs/sources.md` and `docs/sl-process.md` (BFS su-d-01.08.01.01; BAG T 7.01; KVV
Art. 73; SL handbook 2025; CH EPL IG 1.0.1; OASIS XLIFF 1.2/2.1; apertus-ai.org provider list; Infomaniak price page;
Apertus AUP v1.5).
