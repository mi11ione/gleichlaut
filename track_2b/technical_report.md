# Technical report: Gleichlaut

Guarded German→French/Italian drafting of amendments to binding Swiss federal texts with Apertus.
Code places every number; frozen deterministic guards decide what is ready; nothing is published unguarded.

- **Track:** Track 2B: Gleichlaut
- **Event:** Online
- **Team:** `TEAM_NAME`: Roman `SURNAME`
- **Demo:** `VIDEO_URL`
- **Declared maturity:** feasibility study

## 1. Summary

**Promise vs reality.** The German, French and Italian versions of a Swiss federal publication are equally binding.
In the BAG Spezialitätenliste (SL), the list of medicines reimbursed by mandatory health insurance, we found by hand
**5 independent divergences in today's binding reimbursement conditions**, and **every one of them is a number**: Nemluvio
"every 8 weeks" in German and French but "ogni 4 settimane" in Italian; a 6% vs 12% surcharge for Diaphin; a French-only
"≥ 62.5 kg" condition copied across three etanercept biosimilars; a weight limit missing in French for Cresemba; a
shifted weight tier for Dupixent in French. When the German text changes, someone has to make the same change in French
and Italian, every month, without touching anything else.

**Design.** Gleichlaut drafts that change. The old French/Italian text is the starting point and stays locked outside
edit windows projected from the German diff. Numbers never reach the model: they become slot codes and code writes them
back, so the class of divergence we found cannot be introduced by the drafter. Apertus rewrites the wording of the
paragraph. A frozen stack of deterministic guards (lock, numbers/negation/modality, German left in, change not applied,
content dropped, duplication, terminology, vocabulary) marks each draft **ready** or **flagged** with reasons. Translators
receive a ready/flagged queue as XLIFF 2.1 and as FHIR in the format of BAG's own feed.

**Headline (pre-registered, held out).** On a fresh set of 166 FR/IT items mined from 2025 SL data (154 in edit
families never seen during design), with the guards and all their resources hashed **before any output existed**:
Apertus 70B drafts are exactly the official text **17.5%** of the time vs **6.0%** for the no-model baseline
(**+11.4 points, 95% CI [4.8, 18.7]**); **40%** of items come out ready, and **0 of 166** ready drafts contain a
meaning error, a stale change or untranslated German (95% upper bound 2.3%). The pre-registered pass rule is met.
Cost: **$0.0028** per item. `make run` re-executes this run offline from the recorded responses and reproduces every
number.

**Where Apertus fell short** (all measured, §3.3): free translation flips obligations; neither size obeys "edit only this
span"; neither can judge equivalence; the 8B flags 85% of SL drafts; and our first out-of-sample run with the 70B
**failed** the same pass rule (4.1% untranslated). We publish all of it.

## 2. Architecture

![Pipeline](docs/pipeline.svg)

| Module (`src/gleichlaut/`) | Role |
|---|---|
| `frozen/` | the research code, byte-identical, hash-checked: lock, slots, rules, prompt, drafting loop, guards, re-ask, scorer |
| `core.py` | executes the frozen definitions via `ast` with an injected model backend (no re-implementation) |
| `backends.py` | `openai` (any `LLM_BASE_URL`), `llamacpp` (CPU GGUF, digit mask), `cache` (hash-addressed replay) |
| `certify.py` | re-runs the frozen 166-item suite on an endpoint; the SL lane refuses an uncertified endpoint |
| `sl/`, `fed/` | ingest and mine SL snapshots and Fedlex versions into change items |
| `emit/`, `ui/` | XLIFF 2.1 and FHIR output with schema validation; static review page |
| `replay.py`, `score.py` | `make run`: verify the freeze, re-execute recorded runs, re-score, compare |

### Target architecture

Gleichlaut is deployable **on-premise** and, for the Fedlex lane and the SL review-everything fallback, **air-gapped**.
The SL default lane needs the 70B on an endpoint the user controls: own hardware (on-premise) or a Swiss-resident
provider under contract (sovereign Swiss cloud). Public AI was used **for evaluation only**; it may route requests outside
Switzerland and is not a runtime target.

| Lane | Model, where | External services at runtime | Data sent |
|---|---|---|---|
| Fedlex | Apertus 8B GGUF Q4_K_M, CPU, in process | none | none |
| SL default | Apertus 70B on a user-controlled endpoint, gated by `certify` | that endpoint only | the public German and French/Italian texts of one limitation per request |
| SL air-gapped fallback | Apertus 8B GGUF, CPU | none; every item goes to review | none |

**Dependencies.** Runtime: Python 3.12 standard library, `lxml` (XSD validation), and for the offline lane
`llama-cpp-python` and the GGUF file (Apache-2.0 weights). Build time only: the Docker base image, PyPI packages, the
pinned GGUF download (sha256-checked). No data processed at runtime is personal; all inputs are official federal
publications. Details: `docs/dependencies.md`, `docs/target-architecture.md`.

## 3. Use of Apertus

### 3.1 Models, builds, where they run

| Use | Model / build | Where it ran for the reported numbers |
|---|---|---|
| SL drafting (default lane) | Apertus v1.5 70B, `swiss-ai/apertus-v1.5-70b` | Public AI API through a budget gateway, temperature 0, plain user messages only |
| SL drafting (8B arm), Fedlex drafting | Apertus v1.5 8B, MLX 4-bit DWQ | a laptop (Apple M2), greedy, digit logit mask |
| What ships for the 8B | Apertus v1.5 8B GGUF Q4_K_M (public build) | CPU via llama.cpp; Q4_K_M agreed with bf16 on 622 of 648 decisions in our earlier parity battery, our MLX 4-bit build on only 548 |

The 8B results are MLX DWQ results; the GGUF build that ships has not yet been run on these tasks (§6). Public AI's
`apertus-v1.5-8b` name currently serves the 70B (we measured identical greedy outputs in 760 of 792 cells and 70B-level
MMLU), so no 8B number in this report comes from that API.

### 3.2 How the model is used

One prompt (Appendix A): the old and new German, a code-derived list of the German changes, and the old French/Italian
text, all with numbers as slot codes; the model returns the amended paragraph. **8B where sufficient, 70B where needed:**
on Fedlex statutes the 8B's locked rewrite reaches FR/IT exact 50% (28% without one mass amendment) with 0 real meaning
flips in 150 hand-checked paragraphs, so the 8B suffices there. On SL limitations the 8B flags 85% of drafts, above the
70% cap, while the 70B passes; so the SL lane uses the 70B, and the 8B only as the air-gapped fallback.

### 3.3 Where Apertus fell short (and where we deliberately do not use it)

| Task | Result | Consequence |
|---|---|---|
| Free translation of the new German (8B, dev 120) | 0% exact; negation/modality/number lexicon changes in 78 of 120 outputs, none flagged ("deve" → "dovrebbe") | never translate from scratch |
| Edit only a marked span (dev 120) | span ignored in 73% (8B) and 81% (70B) of windows; exact 5.8% = rules; chrF below doing nothing | whole-paragraph rewrite + lock check |
| Judge DE/FR/IT equivalence (Fedlex, 9 known divergences) | 8B 0 of 9; 70B 0 of 9 ("they differ" in 2 of 270 answers) | no model judges; guards are code |
| Type numeric conditions | 8B operator accuracy 36%, errors correlated across languages | numbers handled by code |
| SL drafting, 8B + guards3 (dev 120) | flagged 85%; 1 unflagged direction flip ("riduzione" for "Erhöhung") | 70B for SL |
| SL drafting, 70B + guards v2 (out-of-sample 242) | **FAILED** the pass rule: 4.1% unflagged untranslated German | guards3, then a new held-out set |
| Self-correction | 8B greedy retry fixed 0 of 26; 70B re-ask fixed 3 of 98 | kept only because it is cheap |

## 4. Data

| Source | Use | Licence |
|---|---|---|
| BAG ePL FHIR feed (`epl.bag.admin.ch`), 9 monthly 2026 snapshots | 2026 change pool (dev 120, out-of-sample 242), backtest | official federal publication |
| SL XMLPublications Jun and Jul 2025 (Wayback captures) | the fresh 2025 test set (166); guard resources (Jun 2025 only) | official federal publication |
| Fedlex consolidated versions (SPARQL + AKN XML) | Fedlex lane (120 FR/IT paragraphs, 26 acts) | official texts, not protected (URG Art. 5) |

Mining: per product, texts that disappeared are paired with texts that appeared by token similarity; a change counts if
at most 60% of tokens changed (larger rewrites go to a human). The ePL export has a publisher bug: the Feb–Apr and
4 May 2026 snapshots drop every `<…>` span, so May is excluded and old-format pairs containing `<` are dropped. Fresh
set: Jun→Jul 2025 and Jul 2025→Feb 2026, 83 German changes × FR/IT = 166 items, 55 edit families, 154 items in families
never seen. No personal data.

## 5. Evaluation

Exact = equal to the official new text after whitespace/apostrophe normalisation. Edit-F1 = token edits old→draft vs
old→official. CIs: paired cluster bootstrap over German changes (FR and IT resampled together). Every unflagged non-exact
draft was read in full against the German and the official text; a seeded sample of 20 flagged drafts estimates wasted
review. Pass rule (pre-registered): unflagged real errors ≤ 1%, unflagged stale + untranslated ≤ 2%, exact ≥ rules + 5,
flagged ≤ 70%.

| Setup (FR+IT) | Set | n | Exact | Δ exact vs rules [95% CI] | Flagged | Ready | Unflagged real / stale / untranslated | Pass rule |
|---|---|---|---|---|---|---|---|---|
| Rules only (copy old text + number substitutions) | fresh | 166 | 6.0% | n/a | n/a | n/a | n/a | n/a |
| **Apertus 70B + guards3 + re-ask** | **fresh (held out)** | **166** | **17.5%** | **+11.4 [4.8, 18.7]** | **60.2%** | **39.8%** | **0 / 0 / 0** | **PASS** |
| same, unseen families only | fresh | 154 | 15.6% | +12.3 [5.8, 20.1] | 60.4% | 39.6% | 0 / 0 / 0 | PASS |
| same, without the largest boilerplate family | fresh | 132 | 22.0% | +14.4 [6.8, 22.7] | 75.8% | 24.2% | 0 / 0 / 0 | FAIL (flag rate) |
| Apertus 70B + guards v2 + re-ask | out-of-sample | 242 | 29.3% | +14.9 [9.9, 20.7] | 61.6% | 38.4% | 1 / 0 / 10 | **FAIL** |
| Apertus 70B + guards v2 + re-ask | dev (in-sample) | 120 | 17.5% | +11.7 [5.8, 18.3] | 67.5% | 32.5% | 0 / 0 / 0 | (in-sample) |
| Apertus 8B (MLX DWQ) + guards3, no re-ask | dev | 120 | 15.0% | +9.2 [3.3, 15.8] | 85.0% | 15.0% | 1 / 0 / 0 | FAIL (flag rate) |
| Apertus 8B window-only | dev | 120 | 5.8% | +0.0 | 81.7% | n/a | 6 real errors unflagged | killed |
| Apertus 8B free translation | dev | 120 | 0.0% | −5.8 | none | n/a | 78 lexicon flips unflagged | killed |

![Exact-match gain per arm](docs/fig_arms.svg)

![Outcome of each draft](docs/fig_outcomes.svg)

Review effort: of a seeded 20 flagged drafts on the fresh set, 13 needed no change (65% wasted review, Wilson
[43.3, 81.9]); 7 needed a fix, including all 3 real meaning changes in the sample, which the guards had caught.
Throughput and cost of the 70B lane: 285 calls for 166 items, $0.4602 in total ($0.0028 per item), 17.15 s of model time
per item (sequential).

**Scale.** The SL changes about `NN` German limitations a month (backtest, §4), i.e. about `NN` FR/IT items. At 1× that
is about `$X` a month for the 70B lane; at 10× about `$Y`, with model time parallelisable across requests. The cost is
negligible against translator time; the binding constraint is review effort (60% flagged), not compute.

## 6. Limitations

- **0 of 166 is a point estimate**; the 95% upper bound on unflagged errors is 2.3%, so the data cannot show a true rate
  ≤ 1% with 95% confidence. The exact gain's CI lower bound (4.8) sits just under +5.
- **Direction flips are not guarded**, and a single dropped word inside an edited window can pass (§3.3).
- **One boilerplate family** carries half of the ready drafts; without it the flag rate is 75.8%.
- **About two thirds of flags are wasted review** (13 of 20 sampled).
- **The 8B SL numbers are MLX DWQ on dev items**; the shipped GGUF build has not been run on the fresh set (M1, prepared
  as a CPU workflow, not yet run). The 70B has not been self-hosted; Public AI served it.
- **Labels** were made by Claude Code agents during the research and re-labelled blind by a second Claude agent
  (agreement in §5 `NN`); the team lead's adjudication of disagreements is pending.
- **API non-determinism.** The same request at temperature 0 did not always return the same text (docs/provenance.md §3).

## 7. Reproducibility

`make run` (Docker, CPU, `--network none` unless `LLM_BASE_URL` is set): verifies the sha256 of the frozen code, guard
resources and items; re-executes the recorded 70B runs end-to-end from recorded responses (every model request rebuilt
byte-for-byte and found by its payload hash: 285 of 285 for the headline run); re-guards and re-scores every recorded
run and compares with `eval/results/`; runs a 5-item live slice if `LLM_BASE_URL` is set; emits and validates XLIFF and
FHIR; builds the review page. `make run-offline` adds the local CPU GGUF lane. `claims.tsv` maps every number in this
report to a results file and the command that produced it; CI fails on drift.

**Coding assistants and labellers.** The code was written with Claude Code agents (Anthropic) under the team lead's
direction; hand checks were made by Claude Code agents; a second, blind Claude agent re-labelled the fresh-set sample.
No other model was used at runtime or as a judge. What was checked by hand: every unflagged non-exact draft of every
reported run, and 20 flagged drafts per held-out run.

## 8. Next steps

A shadow-mode pilot with BAG's SL team on the monthly feed; the same workflow for MiGeL and the Analysenliste; a
direction-flip guard; a Swiss-hosted 70B endpoint certified with `make certify`; Romansh for Fedlex (exploratory: 1 of
22 model-written Romansh paragraphs exact).

## License

Creative Commons Attribution 4.0 (CC-BY-4.0). Code: Apache-2.0.

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
