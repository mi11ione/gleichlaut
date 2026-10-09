# Submission form: notes field (≤ 5000 characters; jurors read it)

Start with `make run` in track_2b/ (Docker, CPU, no network needed: it runs with --network none unless LLM_BASE_URL is set). It verifies the sha256 of the frozen code, guards and test items, re-executes our recorded Apertus 70B run end-to-end from the recorded responses (all 285 model requests rebuilt byte-for-byte and found by payload hash), re-scores every run against eval/results, emits and validates XLIFF 2.1 and FHIR, and builds a review page (out/ui/index.html). With LLM_BASE_URL set it also drafts 5 federal-statute paragraphs live.

Problem, evidenced: the DE/FR/IT versions of the BAG Spezialitätenliste are equally binding. We found by hand 5 independent divergences in today's reimbursement conditions (Nemluvio every 8 weeks vs "ogni 4 settimane"; Diaphin 6% vs 12%; a French-only 62.5 kg condition in 3 etanercept products; Cresemba; Dupixent). All 5 are numbers. Gleichlaut never lets the model write a number: numbers become slot codes and code writes them back.

Headline (pre-registered; guards and resources hashed before any output existed): on a fresh held-out set of 166 FR/IT items from 2025 SL changes (154 in unseen edit families), Apertus 70B drafts are exactly the official text 17.5% of the time vs 6.0% for rules only (+11.4, 95% CI [4.8, 18.7]); 39.8% of items come out ready, with 0 unflagged meaning errors, stale changes or untranslated German in 166 (95% upper bound 2.3%). Cost $0.0028 per item.

8B where sufficient, 70B where needed: on federal statutes the 8B's locked rewrite is enough (Fedlex lane, runs air-gapped on CPU); on SL limitations the 8B flags 85.0% of drafts (cap 70%), so the SL lane uses the 70B on a user-controlled endpoint that must pass `make certify`.

Where Apertus fell short (docs/failure-modes.md): free translation flips obligations (deve → dovrebbe); neither size obeys "edit only this span" (73% / 81% of windows ignored); neither can judge equivalence (0 of 9 known divergences); our first out-of-sample 70B run FAILED the same pass rule (4.1% untranslated German); about two thirds of flags are wasted review. Limits: no direction-flip guard; one boilerplate family carries half the ready drafts.

Evidence index: claims.tsv (every number → results file + command), eval/prereg/ (rules and hashes), eval/labels/ (hand checks), docs/provenance.md. Coding assistant: Claude Code agents; labels by Claude agents with a blind second annotator.
