# Gleichlaut

**When BAG changes a Swiss drug-reimbursement condition in German, Gleichlaut drafts the matching French and Italian
change with Apertus, and checks the whole register for places where the three languages already disagree.**

Why it matters: in today's published list, Nemluvio is reimbursed "every 8 weeks" in German and "ogni 4 settimane" in
Italian; Diaphin's surcharge is 6% in German and French and 12% in Italian. A reimbursement condition that says
something different in each language is a condition nobody can apply consistently.

**[Open the review register](https://gleichlaut.mi11ion.io/)** · **[watch the demo](https://gleichlaut.mi11ion.io/demo.mp4)** · [project README](track_2b/README.md) ·
[technical report](track_2b/technical_report.md) · Hack Apertus, Track 2B, team 444

**Declared maturity:** the audit is a deployable prototype; drafting is a feasibility study running in shadow mode.

## What it found in today's list

The audit reads all 1,688 limitations in German, French and Italian and turns them into **18 issues** to decide. Two
blind Claude annotators confirm **12 findings that change a condition**, 10 of them re-confirming the census list its
rules were built around: Nemluvio's interval, Diaphin's surcharge, the 16 kg limit missing in Cresemba's French, a
French-only 62.5 kg rule in three etanercept products, Dupixent's weight tiers. Its experimental checks (off by default)
found what nobody had listed: Amvuttra's French stop rule says an NIS increase "≤ 10" points where German and Italian
say "> 10", and the Italian of Beyonttra and Vyndaqel says "on deve essere combinato" where the German says "darf nicht
… kombiniert werden", a ban that reads as an obligation.

![The review register: the German change, then the French and Italian drafts (70B lane shown; the default 8B keeps the
old 4). Code writes the underlined numbers; the Italian note says the old Italian already said "every 4 weeks".](track_2b/docs/register-nemluvio.png)

## Purposeful use of AI

- **Apertus does the one job that needs a multilingual model:** rewording the French and Italian when the German
  changes. Numbers never reach it (code writes them back), and frozen deterministic checks, not a model, decide which
  drafts are ready and say why in the reviewer's language. The audit itself is plain code: it needs no model.
- **Size, chosen by measurement:** the 8B on an ordinary CPU passes our pre-registered rule and is the default; the 70B
  saves more edits (42.4% against 33.1%, on the shared Public AI endpoint) and is an option; on federal statutes neither
  size passes the rule, so statute drafts all go to review, from the 8B.
- **Where Apertus fell short, and what does that job instead:** judging whether two texts mean the same, typing numeric
  conditions, free translation and filtering audit findings were all tested and handed to code
  ([docs/failure-modes.md](track_2b/docs/failure-modes.md)). No other model runs at runtime.

## Technical rigour

- **Reproducible:** `cd track_2b && make run` (Docker, CPU, about two minutes, no network) re-runs every recorded model
  request and re-derives every number; [claims.tsv](track_2b/claims.tsv) maps each number to its results file.
- **Evaluated, not demoed:** on 166 held-out amendments, with the checks frozen before the test, the 8B's drafts equal
  BAG's published text **+11.4 points** more often than the no-model start [4.8, 18.7], need **33.1% fewer edits**, and
  its ready drafts carry **0 meaning errors** in the blind labels (the annotators caught every planted error and flagged
  5 of 17 real errors BAG had corrected).
- **Optimisation shown:** quantisation is measured on the same items: Q8_0 saves 12.2 points more edits than Q4_K_M.
- **Failures reported:** every rule is pre-registered with an index ([PREREG](track_2b/eval/prereg/PREREG.md)),
  including the runs that failed. Code was written with Claude Code agents; labels come from blind Claude annotators
  under a published protocol a BAG translator can re-run.

## Value, cost & scalability

- **Users:** BAG's Sektion Arzneimittelaufnahmen, which keeps the list, and the federal language service that translates it.
- **Problem evidenced:** the 12 confirmed findings above are in binding texts today.
- **Cost:** the audit takes about a minute of CPU a month; an 8B draft takes 200.5 s on a 4-core CPU you already have;
  a 70B draft costs **CHF 0.0024** at a Swiss provider's price, CHF 0.14 a month today and CHF 1.36 at ten times the
  volume.

## Sovereign deployability

- **Self-hosted on one CPU server** (16 GiB RAM for the default build), as Docker or plain Python; Apache-2.0 code and
  weights; no commercial provider required.
- **External services the running solution contacts:**
  - BAG's public SL feed (`epl.bag.admin.ch`), one GET per language per month to fetch the published list; nothing is
    sent. Offices that copy the snapshots in contact nothing.
  - Optional: the office's own certified 70B endpoint, which receives one public limitation text per request.
  - At build time only: one download of the sha256-pinned model file from Hugging Face.

## Implementation feasibility

- **No change in how BAG works:** drafts fill the French and Italian fields of the ePL editor; translators get XLIFF for
  STAR Transit; decisions export as CSV for the federal records system (GEVER); the audit answers the "translations
  congruent?" question of BAG's triennial review for the whole list.
- **Phase 1 needs no purchase and no model:** a German pilot pack with a one-page decision memo, a protection-needs
  analysis and one case sheet per issue is in [docs/pilot/](track_2b/docs/pilot/); `make pilot-pack` builds it
  offline and reproducibly.
- **What remains:** the section's go decision and the security officer's sign-off for phase 1. For drafting, a live
  month under our own rule: on the August and September 2026 lists the checks sent most drafts to review, so today it
  is a review aid.
- **Others with the same need:** the audit already runs on MiGeL and the Analysenliste, BAG's other trilingual lists.

Code: Apache-2.0 (`LICENSE`). Report: CC-BY-4.0. Judges: run `make run` from inside `track_2b/`.
