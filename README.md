# Gleichlaut

**When BAG changes a Swiss drug-reimbursement condition in German, Gleichlaut drafts the matching French and Italian
change with Apertus, and checks the whole register for places where the three languages already disagree.**

Why it matters: in today's published list, Nemluvio is reimbursed "every 8 weeks" in German and "ogni 4 settimane" in
Italian; Diaphin's surcharge is 6% in German and French and 12% in Italian. A reimbursement condition that says
something different in each language is a condition nobody can apply consistently.

**[Open the review register](https://gleichlaut.mi11ion.io/)** · **[watch the demo](https://gleichlaut.mi11ion.io/demo.mp4)** · [project README](track_2b/README.md) ·
[technical report](track_2b/technical_report.md) · Hack Apertus, Track 2B, team 444

- **The audit finds binding conditions that differ by language, today, with no model.** It reads all 1,688 limitations
  in German, French and Italian and turns them into 18 issues to decide. Two blind Claude annotators confirm 12
  findings that change a condition, re-confirming the census list its rules were built around: Nemluvio's interval, Diaphin's surcharge, the 16 kg limit missing in Cresemba's
  French, a French-only 62.5 kg rule in three etanercept products, Dupixent's weight tiers. On 1,000 divergences planted
  into clean texts it finds 93.0% of changed numbers.
- **Its experimental checks (off by default) found what nobody had listed.** Amvuttra's French stop rule says an NIS increase "≤ 10" points
  where German and Italian say "> 10". The Italian of Beyonttra and Vyndaqel says "on deve essere combinato" where the
  German says "darf nicht … kombiniert werden": a ban that reads as an obligation.
- **Drafting with Apertus 8B, air-gapped on an ordinary CPU.** When the German changes, Apertus pre-fills the French and
  Italian, code writes every number, and frozen checks say why a draft needs a look. On 166 held-out amendments the
  drafts need **33.1% fewer edits**, and the drafts marked ready carry **0 meaning errors** in the blind labels.
- **Apertus 70B as an option:** **42.4% fewer edits** at **CHF 0.0024 per draft** on the shared Public AI endpoint
  (which model it serves we could not verify); in an office it runs behind an endpoint certificate that binds every
  "ready" verdict to the certified endpoint and the model name it serves.
- **Every number is checkable:** `cd track_2b && make run` (Docker, CPU, about two minutes, no network) re-derives every
  figure from the recorded model responses and the committed labels.

![The review register: the German change, then the French and Italian drafts (70B lane shown). Code writes the
underlined numbers; the Italian note says the old Italian already said "every 4 weeks".](track_2b/docs/register-nemluvio.png)

How it works, in one line: numbers never reach the model (code writes them back), Apertus rewrites only the wording,
and frozen deterministic checks, not a model, decide which drafts are ready and say why in the reviewer's language.

## Scope and next steps

- **The audit ships first.** Ten of its twelve confirmed findings re-confirm a list we compiled before the audit existed;
  what the audit adds is that it re-checks the whole register every month, in seconds. The operator and negation checks
  stay off by default until their precision is tuned (6 of their 31 findings are confirmed today).
- **Drafting runs in shadow mode on the live feed every month.** On the August and September 2026 lists the checks sent
  most drafts to review (81.8–92.7%), so drafting is a review aid today. Two pre-registered prompt variants (BAG's house
  terms, then a task-specific system prompt) lowered the flag rate but did not pass our rule; the shipped default stays.
- **Labels are reproducible:** every label comes from blind Claude annotators under a published protocol, with their
  sensitivity measured (every planted error caught; 5 of 17 real errors BAG had corrected flagged); a BAG translator can re-run the same worklists with no change to the pipeline.
- **The 70B numbers come from a shared endpoint;** `make certify-endpoint` re-runs the suite on an office's own endpoint
  before any draft counts as ready.
- **Outside confirmation is scheduled:** the audit's findings are frozen and hashed as predictions, scored against BAG's
  own corrections in its next publications.

Code: Apache-2.0 (`LICENSE`). Report: CC-BY-4.0. Judges: run `make run` from inside `track_2b/`.
