# Gleichlaut

**When BAG amends a drug-reimbursement condition in German, Gleichlaut drafts the matching French and Italian change
with Apertus. Numbers reach the model only as slot codes. Frozen guards decide what is ready for a translator to accept
and what needs review. Nothing is published unguarded.**

Track 2B · declared maturity: **feasibility study** · models: Apertus v1.5 8B + 70B · [technical report](technical_report.md) · [demo video](VIDEO_URL)

## The problem, measured

BAG publishes the reimbursement conditions ("limitations") of the Spezialitätenliste, the list of medicines that
mandatory health insurance pays for (9.08 million insured), in German, French and Italian under one identifier, and its
own review checklist asks whether the translations are congruent. In the 6 Oct 2026 feed we found 5 independent
divergences in current conditions and verified each by reading the German, French and Italian texts side by side. **All of them are numbers:**

| Product (limitation) | German / French | Italian |
|---|---|---|
| Nemluvio (`NEMLUVIO.01`) | every 8 weeks | "ogni 4 settimane" (every 4 weeks) |
| Diaphin (`DIAPHIN.6-`) | surcharge 6% | 12% |
| Etanercept biosimilars ×3 | a French-only "≥ 62.5 kg" condition, copied across products | |
| Cresemba (`CRESE.Kps.IM`) | French drops "≥ 16 kg" | |
| Dupixent ×4 | French misses or shifts the 15–30 kg tier | |

German limitation texts change about 28.7 times a month. BAG's translators keep pace (our backtest found French and
Italian updated in the same monthly step for 208 of 216 changes), so the job is not speed: it is making each change
again in French and Italian, exactly, without touching anything else, and without slipping a number.

## What Gleichlaut does

1. **Mines** each German change from BAG's public monthly FHIR feed (or a Fedlex consolidated version).
2. **Locks** the old French/Italian text outside edit windows projected from the German diff, and turns every number into
   a slot code (⟨A⟩, ⟨B⟩, …) that code writes back. The 70B wrote 0 digits in 285 calls; in 3 of 166 drafts it wrote a
   number word itself, and all 3 were flagged. The 8B cannot emit either (logit mask).
3. **Drafts** the amended paragraph with Apertus: the 70B for SL limitations (the 8B flags 85.0% there, above our cap);
   the 8B for federal statutes, where the 70B measured no better on the same 120 paragraphs (exact 48.3% vs 50.0%; 2 vs
   0 real errors among drafts marked ready). Neither size passes our rule on statutes, so every statute draft is reviewed.
4. **Guards** every draft with a frozen deterministic stack: lock, numbers/negation/modality, German left in, change not
   applied, content dropped, duplication, copied-from-German, terminology, vocabulary. One re-ask with the complaints; kept
   only if every guard passes.
5. **Emits** a ready / flagged queue as **XLIFF 2.1** (translators' own tools) and as **FHIR** in the shape of BAG's own
   feed, plus a review page.

No model judges anything. Apertus rewrites wording, code does the rest.

## Results

The headline row is the pre-registered test: a fresh held-out set of 166 FR/IT items from 2025 SL changes (154 of them
in edit families never seen during design), with the guards hashed before any output existed. The other rows are the
earlier runs that led there, reported because they failed.

| | Exact = official text | Ready (unflagged) | Unflagged errors (real / stale / untranslated) | Pass rule |
|---|---|---|---|---|
| Rules only (copy + number substitution) | 6.0% | | | |
| **Apertus 70B + guards3 + one re-ask** | **17.5%** (+11.4, 95% CI [4.8, 18.7]) | **39.8%** | **0 / 0 / 0** of 166 (95% upper bound 2.3% of items; 5.5% of ready drafts) | **PASS** |
| Same pipeline, pre-registered rerun with seed 1 | 18.1% (+12.0, 95% CI [5.4, 19.3]) | 41.6% | 0 / 0 / 2 of 166 | **PASS** |
| Apertus 70B + earlier guards, out-of-sample 2026 set (242), before guards3 existed | 29.3% | 38.4% | 1 / 0 / 10 | **FAIL** |
| Apertus 8B (MLX 4-bit DWQ) + guards3, development set (120, not held out) | 15.0% | 15.0% | 1 / 0 / 0 | FAIL (85.0% flagged) |

Cost of the 70B lane: **CHF 0.0024 per item** at a Swiss provider's published price (CHF 0.14 a month at today's volume). About two thirds of flagged drafts need no change (13 of a sampled 20): the
guards are deliberately conservative. Where Apertus fell short, with counts: [docs/failure-modes.md](docs/failure-modes.md).

**Terms.** *SL*: the Spezialitätenliste. *Limitation*: one reimbursement condition text. *Ready*: the draft passed every
guard and goes to a translator for acceptance; *flagged*: a guard named a problem. *Exact*: identical to the text BAG
later published. *Stale*: the German change was not (fully) applied. *guards3*: the frozen guard stack (G1–G7). *Edit
family*: changes with the same edit pattern (e.g. one boilerplate rewrite applied to many products).

## Run it

```bash
make run            # Docker, CPU, a few minutes, no network needed (runs with --network none unless LLM_BASE_URL is set)
```

`make run` verifies the sha256 of the frozen code, guard resources and test items; **re-executes the recorded 70B runs
end-to-end from the recorded responses** (every one of the 285 model requests of the headline run is rebuilt
byte-for-byte and found by its payload hash); re-guards and re-scores every recorded run and checks the results;
drafts 5 Fedlex paragraphs live if `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_NAME` point to an Apertus endpoint; emits and
validates XLIFF 2.1 and FHIR; and builds the review page (`out/ui/index.html`).

```bash
make run-offline    # adds the local CPU Apertus 8B (GGUF Q4_K_M, ~5 GB, sha256-pinned) for the air-gapped lane
make certify        # certify the endpoint in LLM_BASE_URL on the frozen 166-item suite before it may serve the SL lane
make test           # unit and reproduction tests
```

## Deployment

| Lane | Runs on | External services at runtime |
|---|---|---|
| Fedlex statutes (every draft reviewed) | Apertus 8B GGUF on CPU, in process | none |
| SL limitations (default) | Apertus 70B on an endpoint the user controls (own hardware or a Swiss-resident provider), gated by `make certify` | that endpoint only |
| SL air-gapped fallback | Apertus 8B GGUF on CPU; every item goes to review | none |

On-premise or air-gapped; build-time and runtime dependencies are separated in
[docs/dependencies.md](docs/dependencies.md). Public AI was used for evaluation only (it may route outside Switzerland).

## Honesty section

- 0 of 166 is a point estimate; the 95% upper bound is 2.3%.
- No guard checks direction flips (increase ↔ reduction); a single dropped word inside an edited window can pass.
- Half of the ready drafts come from one boilerplate family; without it the flag rate is 75.8%, above our own cap.
- The 8B SL numbers are from an MLX 4-bit build on dev items; the GGUF build that ships has not yet been run on the
  fresh set (the CPU workflow is in `.github/workflows/m1.yml`).
- Our first out-of-sample run failed the same rule. We kept the rule, fixed the guards, and tested on new data.
- The guards check that an amendment mirrors the German change; a divergence already present in the old French/Italian is
  carried forward. All 5 divergences we found predate our data window, so we cannot show Gleichlaut would have prevented them.
- No translation lag was found (backtest); translator minutes saved have not been measured.
- On federal statutes the 8B leaves German or a stale part in 8 of 120 drafts it marks ready (6.7%, above our 2% limit).
- Every number in this README is in [claims.tsv](claims.tsv) with the file and command that produce it.

## Repository

| Path | Contents |
|---|---|
| `src/gleichlaut/frozen/` | the research code that produced the numbers, byte-identical (sha256 in `eval/prereg/freeze.json`) |
| `src/gleichlaut/` | pipeline runner, backends, certification, replay, mining, emit, UI |
| `data/` | test items, recorded runs and responses, guard resources, schemas, backtest summaries (< 100 MB) |
| `eval/` | pre-registration, hand-check labels, results, certificates |
| `docs/` | architecture, target architecture, dependencies, provenance, failure modes, sources |

## Declarations

Coding assistant: the code was written with Claude Code agents (Anthropic) under the team lead's direction. Hand checks
of model outputs were made by Claude Code agents and re-labelled blind by a second agent; disagreements go to the team
lead. Apertus is the only model at runtime. Code Apache-2.0; report CC-BY-4.0; SL and Fedlex texts are official federal
publications.
