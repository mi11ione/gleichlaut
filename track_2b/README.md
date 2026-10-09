# Gleichlaut

**Keeps the French and Italian of Switzerland's drug-reimbursement conditions in step with the German.** When BAG
amends a condition in German, Gleichlaut drafts the matching French and Italian change with Apertus, and it audits the
whole register for places where the languages already disagree. Numbers never reach the model; code writes them.

Track 2B · team 444 · maturity: feasibility study · Apertus v1.5 8B + 70B ·
**[open the review register](https://mi11ione.github.io/gleichlaut/)** · [technical report](technical_report.md) ·
[demo video](VIDEO_URL)

## The job

BAG maintains the conditions under which basic insurance pays for a medicine, the 1,688 "limitations" of the
Spezialitätenliste, in German, French and Italian under one identifier: three text fields per limitation in its ePL
editor, published monthly. In 7.5 months of 2026, 216 German texts changed (28.7 a month), and BAG updated French and
Italian in the same month for 208 of them. Keeping pace is routine, skilled work. Where it slips, it slips in numbers.
In today's register:

| Limitation | German | Diverging language |
|---|---|---|
| Nemluvio `NEMLUVIO.01` | maintenance every **8** weeks | Italian: every **4** weeks |
| Diaphin `DIAPHIN.6-` | surcharge **6**% | Italian: **12**% |
| Etanercept ×3 `NEPEXTO` `BENEPALI4` `ERELZI2` | no weight limit for juvenile arthritis | French adds **≥ 62.5** kg |
| Cresemba `CRESE.Kps.IM` | body weight **≥ 16** kg | French drops the limit |
| Dupixent ×4 `DUPIXENT.02` `.02P` `.05a` `.05P` | a dose tier starting at **15** kg | French omits the 15–30 kg tier (`.02`, `.02P`) or starts it at **30** kg (`.05a`, `.05P`) |

## Two tools, one rule: numbers are code's job

**Draft.** When the German changes, Gleichlaut locks the old French/Italian outside the edit, replaces every number
with a slot code (⟨A⟩, ⟨B⟩ …) that code writes back, and lets Apertus rewrite only the wording. A frozen stack of
deterministic checks (edits stay inside the change, numbers/negation/modal verbs mirror the German, no German left,
the change is applied, nothing dropped, terminology) marks each draft **ready** or **flagged**, and says why in the
reviewer's own language. One re-ask with the complaints; the new draft is kept only if every check passes.

**Audit.** Reads every current limitation in all three languages and lists numbers that disagree, fields written in the
wrong language and typos next to numbers. On the 6 Oct 2026 feed it reduces 1,688 limitations to **27 findings**: all
**10** known divergent limitations, plus **6** more problems: five typos next to numbers that nobody had listed, and
Keytruda's Italian field (which we had spotted by hand before), which has held the French text since 1 Aug 2026. It
also learns from BAG's own corrections: where BAG replaced a term in some texts, it flags the texts that still use the
old one. That finds four French texts naming the wrong drug class and four ungrammatical Italian ones (8 of 11 findings
confirmed). On two lists it was never designed on, MiGeL and the Analysenliste, **7 of 11** findings are real; the
Analysenliste's Italian, for example, makes a test billable after 13 repetitions where German and French say 14. Every
count here was confirmed by blind Claude annotators (`eval/labels/`); the audit itself calls no model.

The two meet in the review register. Nemluvio's old Italian already says "every 4 weeks"; Apertus' draft writes "every
8 weeks", matching the German. BAG's own update kept the 4. The register shows the draft as a correction to check, not
as an error.

## Results (pre-registered, held out)

Test set: 166 French/Italian amendments from SL changes between Jun 2025 and Feb 2026, 154 in edit patterns never seen
during design. The checks and all their resources were hashed before any output existed (the freeze predates this
repository; `eval/prereg/PREREG.md` says what can and cannot be verified from here).

| | Apertus 8B Q4_K_M, CPU, 8 GiB | Apertus 8B Q8_0, CPU, 16 GiB | Apertus 70B, certified endpoint | No-model start |
|---|---|---|---|---|
| Draft identical to the text BAG published | 16.9% (+10.8 points [4.8, 17.5]) | 17.5% (+11.4 points [4.8, 18.7]) | **17.5%** (+11.4 points [4.8, 18.7]) | 6.0% (old text, numbers updated by code) |
| Token edits still needed to reach BAG's text | 20.9% fewer [7.6, 31.9] | 33.1% fewer [20.8, 43.9] | **42.4% fewer** [31.0, 54.1] | baseline |
| Drafts ready for acceptance | 36.1% | 37.3% | **39.8%** | |
| Errors in ready drafts (meaning / stale / German left) | 0 / 1 / 2 | **0 / 0 / 0** | **0 / 0 / 0** | |
| Ready drafts that still need any fix | 33 of 60 (mostly one insurance term) | 25 of 62 (mostly the same term) | **3 of 66** | |
| Pre-registered pass rule | **PASS** | **PASS** | **PASS** (and again on a rerun with a new seed) | |

Against rules+, our strongest no-model baseline (it also copies changed names and deletes whole sentences, 10.8%
identical), the 70B still adds +6.6 points [1.8, 12.0] and 41.3% fewer edits [29.7, 53.0].

The 8B runs on the CPU you already have (153.4 s per draft for Q4_K_M, 200.5 s for Q8_0, on a 4-core runner). The 70B
costs **CHF 0.0024 per draft** at a Swiss provider's published price: CHF 0.14 a month at today's volume, CHF 1.36 at
ten times. Every number here is in [claims.tsv](claims.tsv) with the file and command that produce it.

**Model size is measured, not assumed.** On SL conditions every build passes the same pre-registered safety rule, so
the 8B on a CPU is sufficient and is the default: nothing leaves the building. Quantisation matters as much as size: the
8B at Q8_0 matches the 70B on identical drafts (17.5% each) and has no error in any ready draft. The 70B
saves more edits, 9.3 points more than Q8_0 (paired 95% CI [−1.3, 20.2], not significant) and 21.5 more than Q4_K_M
([8.7, 34.9]), and its ready drafts rarely need a fix to the amendment (3 of 66). So: Q4_K_M on an 8 GiB box, Q8_0
where 16 GiB is available (`BUILD=q8_0`), the 70B where an endpoint you control is available and the extra edits are
worth it. On 120 federal-statute amendments (Fedlex) the 70B is no better than the 8B (exact 48.3% vs 50.0%, measured
with the 8B MLX build), so statutes run the 8B. Where Apertus fell short, with counts, and why those jobs are done by
code: [docs/failure-modes.md](docs/failure-modes.md).

## Where it plugs in at BAG

| BAG today ([docs/sl-process.md](docs/sl-process.md)) | Gleichlaut |
|---|---|
| ePL editor: "Limitierungstext DE / FR / IT" fields per limitation | **Draft** proposes the FR and IT fields when the DE field changes |
| Triennial review: applicants declare "…und die Übersetzungen sind kongruent?" | **Audit** gives BAG its own check of that declaration, for the whole register in seconds |
| Federal translation tool STAR Transit | XLIFF 1.2 and 2.1, numbers protected, checks as notes |
| Monthly FHIR R5 publication (CH EPL profile) | drafts emitted as ClinicalUseDefinition in the feed's own shape |

**Shadow mode needs nobody's permission.** `gleichlaut month --from 20260901 --to 20261001 --fetch` mines the month's
German changes from the public feed, drafts them, and grades itself against what BAG publishes. First user group: BAG's
Sektion Arzneimittelaufnahmen and the ePL team. Operator runbook: [docs/operations.md](docs/operations.md).

## Run it

```bash
make run            # Docker, CPU, about a minute, no network (--network none unless LLM_BASE_URL is set)
make local-run      # the same without Docker: Python ≥ 3.9, lxml for the XSD check (67 s on a laptop)
```

It verifies the sha256 of the frozen code, checks and test items; **re-executes the recorded Apertus runs end-to-end
from the recorded responses** (all 285 model requests of the headline run rebuilt byte-for-byte and found by hash);
re-scores every run against `eval/results/`; drafts 5 statute paragraphs live if `LLM_BASE_URL`, `LLM_API_KEY` and
`LLM_NAME` point to an Apertus endpoint; writes and validates XLIFF 1.2/2.1 and FHIR; builds the review register
(`out/ui/index.html`).

```bash
make run-offline    # adds the local CPU Apertus 8B (GGUF, sha256-pinned): the air-gapped default lane
                    # BUILD=q8_0 for the 8.6 GB build on a 16 GiB box (certified too, see Results)
make certify        # build certificate for the pinned 8B GGUF from its recorded held-out run (seconds, offline)
make certify-endpoint # certify your own Apertus 70B endpoint on the frozen 166-item suite
make month          # one monthly cycle on the public feed with the local 8B (shadow mode); make month-70b uses your endpoint
make audit          # the audit of today's register: streams ~270 MB of public feed once, no model (~1 min)
make test           # the test suite (about 6 min; make local-test without Docker)
```

## Sovereign by construction

| Lane | Runs on | Leaves your network |
|---|---|---|
| Audit, checks, register, XLIFF/FHIR | any server, Python standard library + lxml | nothing |
| Federal statutes | Apertus 8B GGUF on CPU, in process | nothing |
| SL conditions, default | Apertus 8B GGUF on CPU, in process (passes the pre-registered rule) | nothing |
| SL conditions, fewer edits | Apertus 70B on an endpoint you control (own GPUs, or a Swiss provider such as Infomaniak, Swisscom, PHOENIQS), admitted only by an endpoint-bound certificate | one limitation text per request (in shadow mode a published one; in pre-publication use BAG's draft German, which is why the endpoint must be one BAG controls), numbers as slot codes |

No provider-specific code: any OpenAI-compatible Apertus endpoint works once it passes `make certify-endpoint`. Build-time and
runtime dependencies: [docs/dependencies.md](docs/dependencies.md); target architecture:
[docs/target-architecture.md](docs/target-architecture.md).

## How you can check us

- **The code that produced the numbers is the code that ships:** the research code is vendored byte-identical and
  hash-checked (`eval/prereg/freeze.json`); `make run` re-runs it from the recorded model responses.
- **Every rule was written before its test:** `eval/prereg/PREREG.md`, with run timestamps from the gateway ledger.
  The first out-of-sample run failed the rule; it is reported, and the fix was tested on new data.
- **Labelling you can re-run:** every ready draft was read in full by a blind Claude annotator, re-labelled by a second,
  disagreements broken by a third (agreement κ 0.532). The worklists, the exact annotator instructions
  (`eval/labels/PROTOCOL.md`) and every label are in `eval/labels/`; no human labels were used, and a BAG translator's
  read of the ready drafts is the first thing a pilot should add.
- **Every number is traceable:** `claims.tsv` maps every number in this README, the report and the form notes to a
  results file; CI fails on drift.

Known limits, measured: no check targets direction flips (increase ↔ decrease); "ready" means the amendment is right,
not the whole text (18 ready French drafts keep an old drug-class mistranslation that BAG fixed in the same update);
the 95% bound on errors in ready drafts is 9.6% counted per German change. Full list: report §6.

## Repository

| Path | Contents |
|---|---|
| `src/gleichlaut/frozen/` | the research code that produced the numbers, byte-identical |
| `src/gleichlaut/` | drafting pipeline, checks, audit, certification, monthly cycle, replay, XLIFF/FHIR, review register |
| `data/` | test items, recorded runs and responses, check resources, schemas, audit and backtest results |
| `eval/` | pre-registration, labels, results, certificates |
| `docs/` | process map, operations, architecture, dependencies, provenance, failure modes, sources |

Code written with Claude Code agents under the team's direction; labels by blind Claude annotators; Apertus is the only
model at runtime. Code Apache-2.0, report CC-BY-4.0; SL and Fedlex texts are official federal publications.
