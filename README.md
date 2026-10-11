# Gleichlaut

**Switzerland's drug-reimbursement conditions are law in three languages. Gleichlaut finds where they disagree, and
keeps them in step with Apertus.**

In today's official list, Nemluvio is reimbursed "every 8 weeks" in German and French and "ogni 4 settimane" in
Italian: at the published price, the two readings differ by **CHF 13,577 a year per patient**. Diaphin's surcharge is
6% in German and French and 12% in Italian. Gleichlaut's operator and negation module adds Amvuttra, whose French stop
rule says an NIS increase "≤ 10" points where German and Italian say "> 10": one patient's stop decision is worth
**CHF 338,743 a year** at list price ([formulas](track_2b/eval/results/stakes.json)). Same drug, same law, three
answers. Gleichlaut flags each one.

**[Open the review register](https://gleichlaut.mi11ion.io/)** · **[Watch the 2-minute demo](https://gleichlaut.mi11ion.io/demo.mp4)** ·
[Project README](track_2b/README.md) · [Technical report](track_2b/technical_report.md) · Hack Apertus, Track 2B, team 444

![The review register: the German change, then the French and Italian drafts. Code writes the underlined numbers; the
Italian note flags that the old Italian already said "every 4 weeks".](track_2b/docs/register-nemluvio.png)

## What it does

**Audit, today, with no model.** Gleichlaut reads all 1,688 limitations of BAG's Spezialitätenliste in German, French
and Italian and turns them into **18 issues** to decide, each with the three texts side by side and the conflicting
values marked. Two blind Claude annotators confirm **12 findings that change a reimbursement condition**: Nemluvio's
interval, Diaphin's surcharge, the 16 kg limit missing in Cresemba's French, a French-only 62.5 kg rule in three
etanercept products, Dupixent's weight tiers. Its operator and negation module found what nobody had listed: Amvuttra's
reversed stop rule, and an Italian typo in Beyonttra and Vyndaqel ("on deve" for "non deve") that turns a ban on
combining into an obligation. On 1,000 divergences planted into clean texts it finds **93.0%** of changed numbers.

**Drafting, with Apertus.** When BAG changes the German, Apertus drafts the French and Italian. Numbers never reach the
model: code writes them back. Frozen checks, not a model, decide which drafts are ready and explain each flag in the
reviewer's own language. On 166 held-out amendments, with every check frozen before the test:

- **Apertus 8B, on an ordinary CPU, fully offline:** **33.1% fewer edits** to reach BAG's published text, almost three
  times as many drafts word for word identical to it as the no-model start, and **0 meaning errors** in its ready drafts.
- **Apertus 70B, optional:** **42.4% fewer edits**, at **CHF 0.0024 per draft**.
- **On the live feed too:** on BAG's August and September 2026 lists, the shipped 8B's drafts needed **28.4% fewer
  edits** [14.9, 38.6] and the 70B's **51.8%** [29.7, 68.7], ready and flagged drafts alike: the same picture as the
  held-out test, on the texts BAG actually published that month.

**Every number re-runs.** `cd track_2b && make run` (Docker, CPU, a few minutes, no network) re-executes every
recorded model call and re-derives every figure; [claims.tsv](track_2b/claims.tsv) maps each number to its source.

## Why Apertus, and why this size

Keeping three binding languages in step is the job a Swiss multilingual model is for. Apertus does exactly that part,
the wording, and nothing else. We measured where it is strong and where code is stronger, and split the work
accordingly: judging equivalence, typing numeric conditions and filtering findings went to code
([docs/failure-modes.md](track_2b/docs/failure-modes.md)). The 8B passes our pre-registered rule on a CPU, so it is the
default and nothing leaves the building; the 70B buys more edits saved where an office wants it. Quantisation is
measured too: Q8_0 saves 12.2 points more edits than Q4_K_M on the same items.

## Built to be used

- **Cost against benefit:** one audit run takes about a minute of CPU and no model, and puts every binding condition
  that differs by language in front of a decision, each worth thousands of francs per patient-year; a draft costs
  nothing with the 8B on your own CPU, or CHF 0.0024 with the 70B.
- **Runs where BAG works:** one CPU server or a laptop, Docker or plain Python, Apache-2.0 code and weights. At runtime
  it reads only BAG's own public feed; with the 70B, the office's own endpoint.
- **Speaks BAG's own format:** Gleichlaut reads BAG's FHIR publication feed and writes its drafts back in that feed's own
  shape (ClinicalUseDefinition), so they land in BAG's data model, not a new one.
- **Fits the existing process:** drafts map onto the French and Italian fields of BAG's ePL editor; translators get XLIFF
  for STAR Transit and a TBX termbase mined from BAG's own wording; decisions export as CSV for the federal records
  system (GEVER); the audit answers the "translations congruent?" question of BAG's triennial review for the whole list.
- **Ready to hand over:** a German phase-1 pack with a one-page decision memo and one case sheet per issue
  ([docs/pilot/](track_2b/docs/pilot/)); `make pilot-pack` builds it, with the offline register, reproducibly.
- **Beyond the SL:** the same audit runs on MiGeL and the Analysenliste, BAG's other trilingual lists, and the drafting
  lane on federal statutes.
- **Running every month:** shadow mode drafts each new SL release on the live public feed and grades itself against
  what BAG publishes; the audit's findings are frozen as hashed predictions, scored against BAG's own next corrections.

Every rule pre-registered ([PREREG](track_2b/eval/prereg/PREREG.md)); every label under a published blind protocol
anyone can re-run. Code: Apache-2.0 (`LICENSE`). Report: CC-BY-4.0.
