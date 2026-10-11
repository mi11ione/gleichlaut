# Gleichlaut

**Keeps the French and Italian of Switzerland's drug-reimbursement conditions in step with the German.** When BAG
amends a condition in German, Gleichlaut drafts the matching French and Italian change with Apertus, and it audits the
whole register for places where the languages already disagree. Numbers never reach the model; code writes them.

Track 2B · team 444 · maturity: feasibility study · Apertus v1.5 8B (local GGUF of a third-party text-only extraction) + 70B (as served by Public AI) ·
**[open the review register](https://gleichlaut.mi11ion.io/)** · [demo video](https://gleichlaut.mi11ion.io/demo.mp4) · [technical report](technical_report.md)

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
**10** known divergent limitations (a check, not a recall measure: the rules were written around the census
that found them; recall is measured on planted faults below), plus **6** more problems: five typos next to numbers that nobody had listed, and
Keytruda's Italian field (which we had spotted by hand before), which has held the French text since 1 Aug 2026. It
also learns from BAG's own corrections: where BAG replaced a term in some texts, it flags the texts that still use the
old one. That finds four French texts naming the wrong drug class, four ungrammatical Italian ones and three French
texts still saying «communiqué» where the register now says «transmis» (11 of 11 notices confirmed; 4 change the meaning).
In all, blind Claude annotators confirm 17 of the 27 findings (63.0%): 12 change a condition (44.4%) and 5 are minor, such as typos next to numbers (the 17th is the number check's view of the
Italian typo «se mesi», which the editorial check also finds). In the review register the 27 findings and 11 terminology notices (38 in all) become 18 issues, one decision each,
3 of them probably equivalent wording and shown collapsed: sibling products that share a divergence are one issue. On two lists it was never designed on, MiGeL and the Analysenliste, **6 of 11** findings are confirmed (4 change a condition); the
Analysenliste's Italian, for example, makes a test billable after 13 repetitions where German and French say 14. Each
finding was read by two blind Claude annotators, the second in reverse order, and a third where their answers differed
(pre-registered R14: they agree whether a finding is real on all 49, κ 1.000); the confirmed counts above are their majority. A single first
annotator had given 16, 8 and 7 (agreement 44 of 49, `eval/results/audit_relabel.json`). The audit itself calls no model. Its recall,
measured independently on 1,000 divergences planted into clean limitations: 77.2% [74.5, 79.7] overall, 93.0% for a
changed number, 94.0% for a field in the wrong language, 73.0% for a changed unit, 75.0% for a deleted clause and 51.0%
for a typo next to a number. Those faults sit where the audit looks by design: a number bound to a unit (dose, interval,
weight, percentage). Planted at any number token instead, recall is 55.5% (37.0% for number words), and flipped
operators or dropped negations are not read at all (0 of 200 each). Pre-registered checks for these blind spots (R15)
find 74.5% of planted operator flips, 44.0% of dropped negations and 84.0% of changed number words, but only 6 of
their 31 register findings are confirmed (real or minor), so they ship off and the blind spots stand ([docs/audit.md](docs/audit.md)). Among the 6 are three divergences nobody had
listed: Amvuttra's French stop rule says an NIS increase "≤ 10" points where German and Italian say
"> 10", and the Italian of Beyonttra and Vyndaqel says "on deve essere combinato" (a typo for "non deve") where the
German says "darf nicht … kombiniert werden": a ban that reads as an obligation. An Apertus filter in front of these checks failed
its pre-registered rule (R18): on the register it keeps 13 of the 31 findings with only 2 confirmed among them (15.4%;
it judges Amvuttra's "≤ 10" and "> 10" the same condition), although it separates planted one-word flips from untouched
sentences well (AUROC 0.955). So the checks stay off ([eval/results/audit_apertus_filter.json](eval/results/audit_apertus_filter.json)).

The audit's counts in one table (`eval/results/audit_grouping.json`, `reconciliation`; confirmed = real or minor by the
blind Claude annotators' majority):

| | Items | Confirmed | Real (changes a condition) | Minor | Not confirmed |
|---|---|---|---|---|---|
| Findings (number, unit, language, typo) | 27 | 17 | 12 | 5 | 10 |
| Terminology notices | 11 | 11 | 4 | 7 | 0 |
| **All, in the register** | **38** | **28** | **16** | **12** | **10** |
| Experimental checks (off; shown apart) | 31 | 6 | 3 | 3 | 25 |

In the register the 38 become 18 issues (3 of them probably equivalent wording, shown collapsed); the experimental
findings are not part of the 18 and are decided and counted on their own.
A check that does not rest on Claude is pre-registered (R20): the 34 confirmed findings are frozen as predictions that BAG
will correct them and the 35 unconfirmed ones as negative predictions (`eval/predictions/audit_20261006_predictions.json`,
sha256 `09cd9df7bf3e…`), scored by `tools/check_predictions.py` against each later SL publication; nothing is claimed
before the 6-month horizon (6 Apr 2027).

The two meet in the review register. Nemluvio's old Italian already says "every 4 weeks"; the 70B draft (the register's
"fewer edits" lane) writes "every 8 weeks", matching the German, and the register shows it as a correction to check, not
as an error. The default 8B keeps the 4, and the register marks the old text as already diverging. BAG's own update kept
the 4.

## Results (pre-registered, held out)

Test set: 166 French/Italian amendments from SL changes between Jun 2025 and Feb 2026, 154 in edit patterns never seen
during design. The checks and all their resources were hashed before any output existed (the freeze predates this
repository; `eval/prereg/PREREG.md` says what can and cannot be verified from here). Could Apertus have seen BAG's answers? Asked to
continue each from its first half (PREREG R16), neither the 70B nor the 8B reproduced the next ten words of any of the
160 (nor of 62 texts first published in Aug and Sep 2026; v1.5's training-data cutoff is not documented; 3 of 120 for the 70B on texts unchanged since before 2023,
so the probe recalls little even of those).

| | Apertus 8B Q8_0, CPU, 16 GiB (default) | Apertus 8B Q4_K_M, CPU, 8 GiB | Apertus 70B, Public AI endpoint (recorded) | No-model start |
|---|---|---|---|---|
| Draft identical to the text BAG published | 17.5% (+11.4 points [4.8, 18.7]) | 16.9% (+10.8 points [4.8, 17.5]) | **17.5%** (+11.4 points [4.8, 18.7]) | 6.0% (old text, numbers updated by code) |
| Token edits still needed to reach BAG's text (a token is a word, a number or a punctuation mark) | 33.1% fewer [20.8, 43.9] | 20.9% fewer [7.6, 31.9] | **42.4% fewer** [31.0, 54.1] | baseline |
| Drafts that pass every check ("ready") | 37.3% | 36.1% | **39.8%** | |
| Errors in ready drafts (meaning / stale / German left) | **0 / 0 / 0** | 0 / 1 / 2 | **0 / 0 / 0** | |
| Ready drafts that need a fix to the amendment | 25 of 62 (22 named by the terminology note) | 33 of 60 (27 named by it) | **3 of 66** | |
| Pre-registered pass rule | **PASS** | **PASS** | **PASS** (and again on a repeat run) | |

**Would the annotators have seen a meaning error?** Measured (pre-registered R11): one meaning error of 7 kinds (dropped condition, and/or, obligation, scope, direction, negation, number) planted into each of 66 ready drafts was labelled a meaning error by both blind annotators 66 of 66 times (95% CI lower bound 94.5%), with BAG's published text shown and with it hidden alike, and 0 of the same 66 drafts left untouched were. Errors written inside the amended sentence so that they read like part of the amendment (pre-registered R14: widened or narrowed scope, a half-applied condition, a number on the wrong noun, and/or) were caught by both 38 of 38 times (lower bound 90.8%), with 0 false alarms on the same 38 drafts untouched; real errors are subtler: of 3 drafts labelled a meaning error earlier, both annotators agree on 1 ([eval/labels/PROTOCOL.md](eval/labels/PROTOCOL.md)). On 17 real errors, French or Italian texts that BAG corrected without any German change (pre-registered R17), both annotators flagged 5 with BAG's text shown and 7 without it (either: 11), and called the same 4 meaning errors each time; 10 of the 17 are one house-wording sweep that they accept as equivalent. Apertus 70B, tried as a non-Claude annotator, confirmed all 49 audit findings and flagged 2 of the 17, so it does not discriminate (κ 0.000 with the Claude majority).

The checks are tuned to flag generously, and it shows: 13 of a seeded 20 flagged 70B drafts needed no change, and 12 of
the 29 drafts identical to BAG's text were flagged.

How much rests on one pattern: a single boilerplate family (one insurance-term change across many products) supplies
half of the 70B's ready drafts. Without it, 75.8% of drafts are flagged, which would fail the 70% flag cap of our own
rule, while the exact-match gain grows to +14.4 points (report §6).

Against rules+, our strongest no-model baseline (it also copies changed names and deletes whole sentences, 10.8%
identical), the 70B still adds +6.6 points [1.8, 12.0] and 41.3% fewer edits [29.7, 53.0]. The default Q8_0 adds
the same +6.6 points [1.8, 12.0] (as many identical drafts, not all the same ones) and 31.8% fewer edits [19.3, 42.8].

Which model Public AI serves under the 70B name is inferred, not known: two backends answer it (`tp2` and `fp1-nes`;
the headline run did not log which, its seeded rerun went 202 / 81). The inference rested on MMLU: 84.4% for the shared
model against 70.8% for the v1 8B. The certified local v1.5 8B Q8_0, run on the same 250 questions and the same
792-cell battery (pre-registered R19), scores 78.4% and matches neither backend closely (decisions 88.6% with
`fp1-nes`, 90.4% with `tp2`): inconclusive under the rule stated in advance, so the 70B rows describe "the 70B as Public
AI served it" (technical report, section 3, "Models and builds").

**What it is worth at today's volume.** BAG publishes about 57.4 French and Italian limitation texts a month that
follow a German change. Starting from the old text with updated numbers, a translator makes about 2,020 word-level
edits a month to reach the published wording (35.1 per text); starting from the default 8B draft that drops by about
670 a month (23.5 per text), from the 70B by about 850 (20.3 per text). The audit adds what is not done today: a full
three-language comparison of all 1,688 conditions in about a minute, each issue with its texts side by side. A timed
pilot turns edits into hours.

The 8B runs on the CPU you already have (200.5 s per draft for the default Q8_0, 153.4 s for Q4_K_M, on a 4-core
runner). The 70B costs **CHF 0.0024 per draft** at a Swiss provider's published price: CHF 0.14 a month at today's volume, CHF 1.36 at
ten times. Every number here is in [claims.tsv](claims.tsv) with the file and command that produce it.

**Model size is measured, not assumed.** On SL conditions every build passes the same pre-registered safety rule, so
the 8B on a CPU is sufficient and is the default: nothing leaves the building. The default build is Q8_0, which passes
with no error among its ready drafts; Q4_K_M passes by one item (1.81% stale or German against the 2% limit). On
identical drafts the rates are close (17.5% for the 70B and Q8_0, 16.9% for Q4_K_M; no equivalence test, and the 8B
runs with a digit mask the 70B endpoint does not offer). On edits saved, quantisation clearly matters: Q8_0 saves 12.2 points more than Q4_K_M
(paired 95% CI [6.0, 19.9]). The 70B saves 9.3 more than Q8_0; the aggregate interval [−1.3, 20.2] includes zero, but
item by item the 70B needs fewer edits on 81 drafts and Q8_0 on 26. Q8_0's 62 ready drafts
have no meaning error, stale change or German left; 25 still need a small fix, 22 of them one insurance term. The
70B's ready drafts rarely need a fix to the amendment (3 of 66). So: Q8_0 by default (16 GiB RAM), Q4_K_M
on an 8 GiB box (`BUILD=q4_k_m`), the 70B where an endpoint you control is certified and the extra edits are
worth it (the served model behind our 70B numbers is not verified; see the report on models and builds). On 120 federal-statute amendments (Fedlex) the 70B is no better than the 8B (exact 48.3%, against 50.0% for the 8B
MLX build and 45.8% / 47.5% for the shipped Q4_K_M / Q8_0 builds). No size passes the safety rule on statutes: the GGUF
builds mark 4 drafts ready that change a provision (the vocational title "EFZ" rendered as a lower qualification, a
fuel category, a clause the German dropped). So statutes run the 8B
and every statute draft goes to review. Where Apertus fell short, with counts, and why those jobs are done by
code: [docs/failure-modes.md](docs/failure-modes.md).

## Where it plugs in at BAG

| BAG today ([docs/sl-process.md](docs/sl-process.md)) | Gleichlaut |
|---|---|
| ePL editor: "Limitierungstext DE / FR / IT" fields per limitation | **Draft** proposes the FR and IT fields when the DE field changes |
| Triennial review: applicants declare "…und die Übersetzungen sind kongruent?" | **Audit** gives BAG its own check of that declaration, for the whole register in seconds |
| Federal translation tool STAR Transit | XLIFF 1.2 and 2.1, numbers protected, checks as notes |
| Terminology (TermStar) | BAG's house renderings mined from the register itself: 64 entries as TBX, plus a terminology note on any draft that departs from them, and a note where a sentence the draft wrote departs from BAG's dominant wording of a fixed sentence such as the indication-code formula ([docs/termbase.md](docs/termbase.md)) |
| Monthly FHIR R5 publication (CH EPL profile) | drafts emitted as ClinicalUseDefinition in the feed's own shape |

**Shadow mode needs nobody's permission.** `gleichlaut month --from 20260901 --to 20261001 --fetch` mines the month's
German changes from the public feed, drafts them, and grades itself against what BAG publishes. First user group: BAG's
Sektion Arzneimittelaufnahmen and the ePL team. Operator runbook: [docs/operations.md](docs/operations.md).

**The first shadow month has run** (1 Sep → 1 Oct 2026, R7, its rule written after the Q4_K_M outputs existed; `data/shadow/`): 52 FR/IT items; 8 went
straight to a translator (rewrites, over-long texts). On this month the drafting fails the 70% flag cap of our own rule: 32 of the other 41 add a new standard
sentence ("Der Indikationscode dieser Limitierung …"), and the no-model start got 0 of 41 right. Apertus drafted 3 (8B)
to 4 (70B) identical to BAG's text, and the checks flagged 82.9–92.7% of drafts, mostly for German left in that
sentence. The 14 drafts marked ready across the three models contain no error: the blind labels find only equivalent
wording and cosmetic slips. BAG's own French for the new sentence is split (« l'assureur-maladie » 9 times,
« l'assurance maladie » 8), the kind of drift the audit exists to catch.

**A second shadow month, pre-registered before any drafting** (1 Aug → 1 Sep 2026, R10, `data/shadow/`; shadow run
`38053562475` for Q8_0, the 70B through the gateway): 38 FR/IT items; 16 went to a translator by routing, 22 were drafted
and compared with BAG's text. It is less prospective than intended: all 22 drafted items were already in our dev 120 (10)
or out-of-sample 242 (12) sets, and the 16 items new to us were all routed to a translator. **Neither model meets R0 on
this month.** Q8_0: 1 of 22 identical, +4.5 points over the no-model start (0 of 22) against the +5 bar (fails);
flagged 81.8%, above the 70% cap (fails); among its 4 ready drafts no meaning error (holds) but 1 with German left,
4.5% of items against the 2% cap (fails). 70B: 0 identical (fails), flagged 81.8% (fails), no meaning error (holds),
1 stale and 2 with German left, 13.6% (fails). The German left is BAG's own typo "GLP1-1-Analogon", carried over by
the number lock instead of being read as "GLP-1"; 14 of the 22 add the same new standard sentence as in September.
Both annotators agreed on all 7 labels.

**What the two live months say.** On new material the frozen checks send most drafts to review (81.8–92.7% flagged,
above our own 70% cap), and across both months no draft marked ready changes a condition's meaning. So on live data
today the drafting is a review aid that pre-fills French and Italian and says why each draft needs a look; the audit is
the part ready to run, as phase 1 of [docs/adoption.md](docs/adoption.md). The commonest cause in both months is one new
standard sentence that BAG itself renders two ways; checking drafts against BAG's own house formula (an advisory note
today) is the next step to pre-register.

**House wording in the prompt, on both live months (R12, pre-registered before any run).** The drafting prompt asks for
"the established terminology" without supplying it. The variant v3-terms adds one block to it: BAG's own French/Italian
wording of the terms and fixed sentences in the new German, mined only from each month's old snapshot (1 Aug, 1 Sep), so
never from the month's published text. Guards, re-ask, routing and the frozen code are unchanged; the block changed 19 of
22 August and 40 of 40 September prompts. Q8_0 on CPU runners (shadow runs `38058301756`, `38058337474`), the 70B through
the gateway, frozen → v3-terms:

| Month, model | Identical to BAG | Points over no-model start | Flagged | Ready drafts with an error | R0 |
|---|---|---|---|---|---|
| Aug, Q8_0 (n 22) | 1 → 3 | +4.5 → +13.6 | 81.8% → 63.6% | 1 German → 1 German | fails → fails (German left 4.5%) |
| Aug, 70B (n 22) | 0 → 0 | +0.0 → +0.0 | 81.8% → 68.2% | 3 → 5 (1 REAL, 2 stale, 2 German) | fails → fails |
| Sep, Q8_0 (n 41) | 3 → 8 | +7.3 → +19.5 | 92.7% → 73.2% | 0 → 0 | fails → fails (flagged) |
| Sep, 70B (n 41) | 4 → 9 | +9.8 → +22.0 | 82.9% → 80.5% | 0 → 0 | fails → fails (flagged) |

What holds: BAG's wording in the prompt gives more drafts identical to BAG's text in three of the four month-model pairs
and fewer flags in all four, and the September ready drafts still contain no error. What fails: no month and model meets
R0, so under the pre-registered decision v3-terms is not a candidate for the next held-out test and the frozen default
stays. September misses only the 70% flag cap; August Q8_0 misses only the German-left cap, on BAG's own typo
"GLP1-1-Analogon" as in the frozen run; the August 70B gets worse (a French draft left "Maximal" and dropped
"médicamenteuse", REAL for both annotators; two kept a fragment of a deleted sentence). Most other differences from BAG's
text are one insurer word: mostly the Italian termbase entry, the bare head «assicuratore», where BAG writes
«assicuratore malattie» (the shipped termbase has since dropped that entry: the register splits, no phrase is a majority;
[docs/termbase.md](docs/termbase.md#fourth-review-11-oct-2026-italian-translator)); in French BAG itself published its minority « assurance maladie ». The two blind annotators agreed on all
19 labelled drafts (`eval/results/r12_terms.json`).
Phased pilot (audit first), owners, protection needs and monthly effort: [docs/adoption.md](docs/adoption.md).
Phase-1 pilot pack in German (draft mandate, protection-needs analysis, management note, one GEVER case sheet per audit issue; owners left for BAG to fill in): [docs/pilot/](docs/pilot/README.md).

## Run it

```bash
make run            # Docker, CPU, about two minutes, no network (--network none unless LLM_BASE_URL is set)
make local-run      # the same without Docker: Python ≥ 3.9, lxml for the XSD check (1–3 min on a laptop)
```

It verifies the sha256 of the frozen code, checks and test items; **re-executes the recorded Apertus runs end-to-end
from the recorded responses** (all 285 model requests of the headline 70B run and all 294 of the recorded 8B Q8_0
CPU run rebuilt byte-for-byte and found by hash);
re-scores every run against `eval/results/`; drafts 5 statute paragraphs live if `LLM_BASE_URL`, `LLM_API_KEY` and
`LLM_NAME` point to an Apertus endpoint; writes and validates XLIFF 1.2/2.1 and FHIR; builds the review register
(`out/ui/index.html`).

```bash
make run-offline    # adds the local CPU Apertus 8B (GGUF, sha256-pinned): the air-gapped default lane, Q8_0
                    # (8.6 GB, 16 GiB RAM); BUILD=q4_k_m for the 5.1 GB build on an 8 GiB box (certified too)
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
- **Rules written before their tests:** `eval/prereg/PREREG.md`, with run timestamps from the gateway ledger. The
  first out-of-sample run failed the rule; it is reported, and the fix was tested on new data. PREREG states the
  exceptions: R0 predates this repository, R7 was written after the first shadow-month outputs were seen, and the
  default build was chosen after both 8B results.
- **Labelling you can re-run:** every ready draft was read in full and labelled twice, disagreements broken by a third
  blind Claude annotator. The headline 70B run was first labelled by a research labeller who knew each draft's guard
  verdict, so it was relabelled fully blind (pre-registered R13): the two blind annotators agree on 67 of 69 records
  (κ 0.892) and find 0 meaning errors, stale changes or German left among the ready drafts; 3 need a small fix (one
  term, two spacing slips). The worklists, the exact annotator instructions
  (`eval/labels/PROTOCOL.md`) and every label are in `eval/labels/`; a BAG translator can be the next annotator on the
  same worklists, with no change to the pipeline.
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
