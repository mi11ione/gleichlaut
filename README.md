# Gleichlaut

**When BAG changes a Swiss drug-reimbursement condition in German, Gleichlaut drafts the matching French and Italian
change with Apertus, and checks the whole register for places where the three languages already disagree.**

Why it matters: in today's published list, Nemluvio is reimbursed "every 8 weeks" in German and "ogni 4 settimane" in
Italian; Diaphin's surcharge is 6% in German and French and 12% in Italian. A reimbursement condition that says
something different in each language is a condition nobody can apply consistently.

**[Open the review register](https://gleichlaut.mi11ion.io/)** · **[watch the demo](https://gleichlaut.mi11ion.io/demo.mp4)** · [project README](track_2b/README.md) ·
[technical report](track_2b/technical_report.md) · Hack Apertus, Track 2B, team 444

- **The audit runs today, with no model.** It reads all 1,688 limitations in German, French and Italian and turns them
  into 27 findings; blind annotators confirm 16 of them as real, among them the 10 divergences an earlier census had
  listed (Nemluvio, Diaphin). In the register they become 18 issues, one decision each. On 1,000 divergences planted into clean texts it finds
  93.0% of changed numbers, 73.0% of changed units and 75.0% of deleted clauses.
- **Drafting is a review aid, air-gapped on a CPU** with Apertus 8B. When the German changes, Apertus pre-fills the French
  and Italian, code writes every number, and frozen checks say why a draft needs a look. On 166 held-out amendments
  (83 German changes) its drafts need 33.1% fewer word edits, about 670 a month at today's volume, and its 62 ready
  drafts have **0 meaning errors**. On two live months no ready draft changed a meaning either, but neither month met
  our pre-registered rule: the checks flagged 81.8–92.7% of drafts, so a translator reviews nearly everything.
- **The 70B where an endpoint you control is available:** 42.4% fewer word edits, at **CHF 0.0024 per draft**.
- **Every number is checkable:** `cd track_2b && make run` (Docker, CPU, about a minute, no network) re-runs every
  recorded 70B request and every recorded request of the 8B Q8_0 CPU run, re-scores the 8B runs and re-derives every figure; `make local-run` does the same without Docker.

![The review register: the German change, then the French and Italian drafts. Code writes the underlined numbers; the
Italian note says the old Italian already said "every 4 weeks" and the draft follows the German's 8.](track_2b/docs/register-nemluvio.png)

How it works, in one line: numbers never reach the model (code writes them back), Apertus rewrites only the wording,
and frozen deterministic checks, not a model, decide which drafts are ready and say why in the reviewer's language.

Code: Apache-2.0 (`LICENSE`). Report: CC-BY-4.0. Judges: run `make run` from inside `track_2b/`.
