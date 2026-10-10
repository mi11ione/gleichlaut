# Gleichlaut

**When BAG changes a Swiss drug-reimbursement condition in German, Gleichlaut drafts the matching French and Italian
change with Apertus, and checks the whole register for places where the three languages already disagree.**

Why it matters: in today's published list, Nemluvio is reimbursed "every 8 weeks" in German and "ogni 4 settimane" in
Italian; Diaphin's surcharge is 6% in German and French and 12% in Italian. A reimbursement condition that says
something different in each language is a condition nobody can apply consistently.

**[Open the review register](https://gleichlaut.mi11ion.io/)** · [project README](track_2b/README.md) ·
[technical report](track_2b/technical_report.md) · Hack Apertus, Track 2B, team 444

- **Runs air-gapped on an ordinary CPU** with Apertus 8B: on 166 held-out amendments, with every rule fixed in advance,
  its drafts need 33.1% fewer token edits to reach BAG's published text than the old text with updated numbers, and the
  62 drafts it marks ready have **0 meaning errors**, stale changes or German left.
- **The 70B where an endpoint you control is available:** 42.4% fewer token edits, ready drafts that rarely need a fix
  to the amendment (3 of 66), at **CHF 0.0024 per draft**.
- **The audit needs no model at all:** it reduces 1,688 limitations to 27 findings (18 issues to decide), including the 10 divergences an
  earlier census had listed; within its scope (numbers bound to a unit) it finds 93.0% of planted changes.
- **Every number is checkable:** `cd track_2b && make run` (Docker, CPU, about a minute, no network) re-runs every
  recorded 70B request, re-scores the 8B runs and re-derives every figure; `make local-run` does the same without Docker.

![The review register: the German change, then the French and Italian drafts. Code writes the underlined numbers; the
Italian note says the old Italian already said "every 4 weeks" and the draft follows the German's 8.](track_2b/docs/register-nemluvio.png)

How it works, in one line: numbers never reach the model (code writes them back), Apertus rewrites only the wording,
and frozen deterministic checks, not a model, decide which drafts are ready and say why in the reviewer's language.

Code: Apache-2.0 (`LICENSE`). Report: CC-BY-4.0. Judges: run `make run` from inside `track_2b/`.
