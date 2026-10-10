# Gleichlaut

**When BAG changes a Swiss drug-reimbursement condition in German, Gleichlaut drafts the matching French and Italian
change with Apertus, and checks the whole register for places where the three languages already disagree.**

Why it matters: in today's published list, Nemluvio is reimbursed "every 8 weeks" in German and "ogni 4 settimane" in
Italian; Diaphin's surcharge is 6% in German and French and 12% in Italian. A reimbursement condition that says
something different in each language is a condition nobody can apply consistently.

**[Open the review register](https://gleichlaut.mi11ion.io/)** · **[watch the demo](https://gleichlaut.mi11ion.io/demo.mp4)** · [project README](track_2b/README.md) ·
[technical report](track_2b/technical_report.md) · Hack Apertus, Track 2B, team 444

- **The audit runs today, with no model.** It reads all 1,688 limitations in German, French and Italian and finds
  divergences nobody had listed. Amvuttra's French stop rule says an NIS increase "≤ 10" points where German and Italian
  say "> 10". The Italian of Beyonttra and Vyndaqel says "on deve essere combinato" where the German says "darf nicht …
  kombiniert werden": a ban that reads as an obligation. (These two come from operator and negation checks that ship
  off by default, because only 6 of their 31 findings are confirmed.)
- **Its main check** turns the register into 27 findings, 18 issues to decide. Two blind Claude annotators (a third on
  disagreements) confirm 17 as real, among them the 10 divergences an earlier census had listed and its rules were built
  around. On 1,000 divergences planted into clean texts it finds 93.0% of changed numbers.
- **Drafting is a review aid, air-gapped on a CPU** with Apertus 8B: Apertus pre-fills the French and Italian when the
  German changes, code writes every number, and frozen checks say why a draft needs a look. On 166 held-out amendments
  the drafts need **33.1% fewer edits**, and the drafts marked ready carry **0 meaning errors**. On two live months the
  checks flagged most drafts, so a translator still reviews nearly everything.
- **The 70B where an endpoint you control is available:** 42.4% fewer edits, at CHF 0.0024 per draft.
- **Every number is checkable:** `cd track_2b && make run` (Docker, CPU, about two minutes, no network) re-derives every
  figure from the recorded model responses and the committed labels. The details, bounds and caveats are in the
  [project README](track_2b/README.md) and the [technical report](track_2b/technical_report.md).

![The review register: the German change, then the French and Italian drafts. Code writes the underlined numbers; the
Italian note says the old Italian already said "every 4 weeks" and the draft follows the German's 8.](track_2b/docs/register-nemluvio.png)

How it works, in one line: numbers never reach the model (code writes them back), Apertus rewrites only the wording,
and frozen deterministic checks, not a model, decide which drafts are ready and say why in the reviewer's language.

Code: Apache-2.0 (`LICENSE`). Report: CC-BY-4.0. Judges: run `make run` from inside `track_2b/`.
