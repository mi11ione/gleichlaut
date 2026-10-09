# Gleichlaut

**Keeps the French and Italian of Switzerland's drug-reimbursement conditions in step with the German.** When BAG
amends a condition in German, Gleichlaut drafts the matching French and Italian change with Apertus, and it audits the
whole register for places where the languages already disagree. Numbers never pass through the model.

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
| Dupixent ×4 `DUPIXENT.02` `.02P` `.05a` `.05P` | dose tier from **15** kg | French starts at **30** kg or omits the tier |

## Two tools, one rule: the model never writes a number

**Draft.** When the German changes, Gleichlaut locks the old French/Italian outside the edit, replaces every number
with a slot code (⟨A⟩, ⟨B⟩ …) that code writes back, and lets Apertus 70B rewrite only the wording. A frozen stack of
deterministic checks (edits stay inside the change, numbers/negation/modal verbs mirror the German, no German left,
the change is applied, nothing dropped, terminology) marks each draft **ready** or **flagged**, and says why in the
reviewer's own language. One re-ask with the complaints; the new draft is kept only if every check passes.

**Audit.** Reads every current limitation in all three languages and lists the conditions whose numbers disagree. On
the 6 Oct 2026 feed it reduces 1,688 limitations to **21 lines**, which contain **all 10** known divergent limitations.

The two meet in the review register. Nemluvio's old Italian already says "every 4 weeks"; Apertus' draft writes "every
8 weeks", matching the German. BAG's own update kept the 4. The register shows the draft as a correction to check, not
as an error.

## Results (pre-registered, held out)

Test set: 166 French/Italian amendments from 2025 SL changes, 154 in edit patterns never seen during design. The checks
and all their resources were hashed before any output existed.

| | Apertus 70B + checks | Starting point a translator has today |
|---|---|---|
| Draft identical to the text BAG published | **17.5%** (+11.4 points, 95% CI [4.8, 18.7]) | 6.0% (old text + numbers updated) |
| Token edits still needed to reach BAG's text | **42.4% fewer** (95% CI [31.0, 54.1]); 59.1% fewer on ready drafts | baseline |
| Drafts ready for acceptance | **39.8%** of items | |
| Errors introduced in ready drafts (meaning / stale / German left) | **0 / 0 / 0** | |
| Same test, rerun with a new seed | +12.0 points, 41.6% ready, 0 meaning errors | |

Costs **CHF 0.0024 per draft** at a Swiss provider's published price for Apertus 70B: CHF 0.14 a month at today's
volume, CHF 1.36 at ten times. Every number here is in [claims.tsv](claims.tsv) with the file and command that
produce it.

**Model size is measured, not assumed.** On SL conditions the 8B flags 85.0% of its drafts, so this lane runs the 70B.
On 120 federal-statute amendments (Fedlex) the 70B is no better than the 8B (exact 48.3% vs 50.0%), so statutes run the
8B on a CPU. Where Apertus fell short, with counts, and why those jobs are done by code: [docs/failure-modes.md](docs/failure-modes.md).

## Where it plugs in at BAG

| BAG today ([docs/sl-process.md](docs/sl-process.md)) | Gleichlaut |
|---|---|
| ePL editor: "Limitierungstext DE / FR / IT" fields per limitation | **Draft** proposes the FR and IT fields when the DE field changes |
| Triennial review question: "…und die Übersetzungen sind kongruent?" | **Audit** answers it for the whole register in seconds |
| Federal translation tool STAR Transit | XLIFF 1.2 and 2.1, numbers protected, checks as notes |
| Monthly FHIR R5 publication (CH EPL profile) | drafts emitted as ClinicalUseDefinition in the feed's own shape |

**Shadow mode needs nobody's permission.** `gleichlaut month --from 20261001 --to 20261101 --fetch` mines the month's
German changes from the public feed, drafts them, and grades itself against what BAG publishes. First user group: BAG's
Sektion Arzneimittelaufnahmen and the ePL team. Operator runbook: [docs/operations.md](docs/operations.md).

## Run it

```bash
make run            # Docker, CPU, about 30 s on a GitHub runner, no network (--network none unless LLM_BASE_URL is set)
```

It verifies the sha256 of the frozen code, checks and test items; **re-executes the recorded Apertus runs end-to-end
from the recorded responses** (all 285 model requests of the headline run rebuilt byte-for-byte and found by hash);
re-scores every run against `eval/results/`; drafts 5 statute paragraphs live if `LLM_BASE_URL`, `LLM_API_KEY` and
`LLM_NAME` point to an Apertus endpoint; writes and validates XLIFF 1.2/2.1 and FHIR; builds the review register
(`out/ui/index.html`).

```bash
make run-offline    # adds the local CPU Apertus 8B (GGUF, sha256-pinned) for the air-gapped lane
make certify        # certify your Apertus endpoint on the frozen 166-item suite before it may draft SL conditions
make month          # one monthly cycle on the public feed (shadow mode)
make test           # the test suite
```

## Sovereign by construction

| Lane | Runs on | Leaves your network |
|---|---|---|
| Audit, checks, register, XLIFF/FHIR | any server, Python standard library + lxml | nothing |
| Federal statutes | Apertus 8B GGUF on CPU, in process | nothing |
| SL conditions | Apertus 70B on an endpoint you control (own GPUs, or a Swiss provider such as Infomaniak, Swisscom, PHOENIQS), admitted only by an endpoint-bound certificate | one public limitation text per request, numbers as slot codes |

No provider-specific code: any OpenAI-compatible Apertus endpoint works once it passes `make certify`. Build-time and
runtime dependencies: [docs/dependencies.md](docs/dependencies.md); target architecture:
[docs/target-architecture.md](docs/target-architecture.md).

## How you can check us

- **The code that produced the numbers is the code that ships:** the research code is vendored byte-identical and
  hash-checked (`eval/prereg/freeze.json`); `make run` re-runs it from the recorded model responses.
- **Every rule was written before its test:** `eval/prereg/PREREG.md`, with run timestamps from the gateway ledger.
  The first out-of-sample run failed the rule; it is reported, and the fix was tested on new data.
- **Labelling anyone can re-run:** every ready draft was read in full by a blind annotator, re-labelled by a second,
  disagreements broken by a third (agreement κ 0.532; worklists and labels in `eval/labels/`).
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
