# Pre-existing divergence audit (`gleichlaut.audit`)

Gleichlaut's guards check that a French/Italian amendment mirrors the German change. They do not check that the old
French/Italian text was right, so a divergence that is already there is carried forward. The 5 divergences we
verified by hand in the 6 Oct 2026 SL (Nemluvio, Diaphin, etanercept ×3, Cresemba, Dupixent ×4) all predate our data.
The audit separates the two cases: **"the old French/Italian already disagrees with the German"** and **"the draft is wrong"**.

It is deterministic code: no model calls, Python standard library only.

```bash
PYTHONPATH=src python3 -m gleichlaut.audit --hist DIR --date 20261006 --out data/audit [--worklist DIR]
```

`--hist` defaults to `$GLEICHLAUT_HIST`. The command writes `data/audit/audit_20261006.json` (ranked findings, plus
the fresh-item hits) and `audit_20261006_summary.json`. From code, `audit.audit_item(x)` takes an item with `de_old`,
`tgt_old` and `lang` and returns the pre-existing numeric divergences between the old German and the old target text,
for the review page.

## What it checks

For each CUD id (ids align across the three languages) it compares the numeric values of the German text with those
of the French text, and separately with those of the Italian text.

- **Values.** Digits: `62.5` = `62,5`; `1'000` = `1 000` = `1000`; `2.50` = `2.5`. Both ends of a range count
  (`15–30`, `15 - < 60`). `6%` counts as 6. A date `dd.mm.yyyy` gives the day and the year. The cardinal number words 2–12
  of each language come from the frozen `gl2.NUMW`, and also count inside German compounds (`zweimal`,
  `vierwöchentlich`). Digits glued to letters (`FEV1`, `HER2`) are names, not values.
- **R1 list numbering.** `1) `, `2. ` at the start or after a sentence end is structure and is dropped on both sides.
- **R2 unit binding.** A value becomes a finding only if a unit or quantity noun follows it on the side where it occurs:
  mg, kg, %, ml, IE, mmol, Wochen/semaines/settimane, Jahre/ans/anni, Lebensjahr, Zyklen, doses, tablets, ×, and so on. A unit
  binds both ends of a range and every item of a list (`2, 4 und 6 Wochen`). Unbound differences (codes, SR numbers,
  table cells, years, "deux yeux") are counted but not reported.
- **R3.** Value 1 is not reported when the other text has an article or "premier/primo"; ein/un/uno carry it.
- **R4 reconciliation** before reporting:
  - `1.000` read as a decimal in one language and as a thousand in the other;
  - `0,2` glued in one language and `0, 2` in the other;
  - N days = N/7 weeks, N months = N/12 years, N g = 1000 N mg;
  - German "N. Lebensjahr" = "N-1 ans/anni";
  - an ordinal digit matched by an ordinal word (`2.` / `deuxième`);
  - a period adjective (`alle 2 Monate` = `bimestrale`, `vierteljährlich`, `semestrale`).
- **R5.** A value present in both languages but a different number of times goes to `count_only_differences`, not to
  the findings: repetition is a matter of style.
- **Ranking.** Swaps of a same-unit value come first (8 vs 4 weeks, 6% vs 12%), then one-sided bound values. Findings
  with fewer unmatched values rank higher.

Each finding carries the id, the product names, the language, `kind: numeric`, the values on each side with up to 3
context snippets, the score and rank, the design half (`dev`/`held`, by md5 of the id), a text-pair group hash, and
`known` (one of the hand-verified cases).

## How the rules were made (and what that means for the numbers)

1. The rules above were written first, using the format survey and the noise classes that S1 had already documented
   (unit conversions, articles read as "one", digits glued to names, `bimestrale`).
2. They were then adjusted by looking only at findings and unbound differences from the **dev half** (ids with even
   md5), with the 11 known ids excluded. Three generic fixes came from those 6 dev findings and 40 unbound
   differences:
   - the thousands rule made symmetric (`150.000/μL` vs `150 000/μL`, ULTOMIR);
   - period adjectives added (`alle 2 Monate` vs `bimestrale`, REKAMBYS);
   - German unit stems generalised and list propagation added (`6-monatigen`, `Behandlungsjahr`, `2, 4 und 6 Wochen`).
3. The rules were frozen (sha256 `e7b5c474…` of `audit.py` at that point) **before** recall was measured. Later edits
   touched only reporting, the worklist and the term-pair statistics.

Two consequences follow. First, dev-half findings were partly shaped by inspection: 2 dev noise findings were removed by
the fixes. Precision should therefore also be reported on the `held` half alone; the key map carries the half. Second,
the known cases were found by S1's numeric flags and a sweep over unit-carrying numbers. A numeric audit recovering them
is therefore expected and is not evidence about divergences of other kinds.

## Numbers (6 Oct 2026 snapshot, 1,688 limitations)

| | |
|---|---|
| Findings (DE↔FR / DE↔IT) | **21** (14 FR, 7 IT) on 17 limitations; 4 are same-unit swaps; 10 dev / 11 held |
| Recall, known divergent limitations | **10 of 10**; 13 of 13 hand-verified values on the right side and in the right language |
| Keytruda KN045 (bonus) | not found; it is not numeric (the IT slot carries French text) |
| Not reported | 230 count-only differences; 148 unbound value differences |
| Suppressed by R3/R4 | one 51, ordinal word 15, glued 5, unit conversion 2, period word 2, thousands 1 |
| Fresh items (166) with a pre-existing divergence in the old text | **1**: `wb004-it`, Nemluvio (DE "alle acht Wochen", old IT "ogni quattro settimane") |
| Model calls | 0 |

Ranks of the known findings: Diaphin 1, Dupixent.05P 2, Dupixent.05a 3, Benepali 5, Cresemba 9, Erelzi 12,
Nemluvio 18, Nepexto 19, Dupixent.02 20, Dupixent.02P 21.

**Nemluvio in the fresh run.** The old Italian already said "quattro". The recorded 70B draft for `wb004-it`
(`data/runs/70b_fresh166_g3_final.jsonl`) wrote "ogni otto settimane", in line with the German. BAG's own new Italian text kept
"quattro". The guards flagged the draft. Among their reasons: "changed text outside the amended part: «⟨L⟩» -> «⟨M⟩»"
(quattro → otto), and "lost words that the German change does not touch: quattro". The guards were right that the edit
went outside the amendment. With `audit_item` the review page can add that the old Italian already disagreed with the
German at that spot, so the reviewer can tell a correction from an error.

**Precision: pending blind labels.** There are fewer than 40 findings, so the worklist holds all 21 of them, shuffled
with seed 20261009. It goes to blind annotators and we did not label them ourselves. The files are `worklist.json`
(fields `id`, `de`, `target`, `lang`, `finding`, `question`) and `key_map_DO_NOT_SHOW.json` (CUD, rank, known, half).
The 10 known findings are among the 21, and each was hand-verified as real before this audit existed, so precision is
at least 10/21 = 48% whatever the labels of the other 11. Report precision on all 21, on the 11 non-known findings, and on
the held half.

### Why this differs from the S1 census (6% overall, numbers 3/15)

S1 flagged five fact types (NUM, OP, NEG, ITEMS, UNIT) and reached 3/50 = 6% precision overall. Its NUM category
reached 3/15 = 20%, with 7 of the 15 being parser noise. The audit differs in five ways:

- It checks numbers only; OP and NEG produced 0 real flags in S1.
- It reports a value only when a unit is attached (R2). S1's own sweep over unit-carrying numbers found 12 of 25 real,
  against 3 of 15 for all numbers.
- It compares sets of values, not counts (R5).
- It never reports 1 (articles).
- It reconciles the noise classes S1 listed: glued digits, unit conversions, period adjectives, and separators.

The cost is coverage: 230 count-only and 148 unbound differences are not shown. The two numbers measure different
things, so a high audit precision does not mean the census was wrong. It means the audit asks a narrower question.

## Second signal: term pairs (measured, off)

`term_pairs()` derives DE→FR/IT term pairs mechanically. A German word or hyphen compound of at least 8 letters is paired
with a target word or bigram when both appear in at least 90% of the aligned distinct text pairs, in both directions,
with support of at least 10. A text pair is flagged when one side has the term and the other does not. At this threshold:

- FR: 297 pairs, 722 exceptions on 483 ids. IT: 314 pairs, 741 exceptions on 473 ids.
- The top pairs are boilerplate associations ("versicherte" ↔ "moment", "kostengutsprache" ↔ "médecin conseil"). The
  exceptions are mostly paraphrases.

The motivating case is not mined at all. "Angiotensin-II-Antagonist" occurs in 23 German texts. The French says
"récepteurs de l'angiotensine" in 19 of them (83%, under 90%), because the error itself sits in the other 4: COVERAM-PLUS,
PERAMLIND.me, PERAMLIND.sp and PERINDAMLIND. In February 2026 there were 32 such texts.

A recurring mistranslation lowers its own co-occurrence, so a co-occurrence miner is structurally weak at exactly this
error. The signal is therefore off; the statistics are reported in the summary (`term_pairs`) for reproducibility.

## Caveats

- **Only numbers are checked.** The audit cannot see a wrong drug class, a changed operator (≥ vs >), a dropped
  negation, a German-only clause without numbers, or a language swap such as Keytruda's.
- **Same value, different unit is not caught.** The audit compares values, not value+unit, so 4 Wochen vs 4 Monate passes.
  Count-only differences can also hide a moved value.
- **Recall is measured on cases a numeric method found.** It is optimistic for divergences in general; see above.
- **Number words.** Only 2–12 (frozen `NUMW`). FR hyphenated numbers (`dix-huit`) are read as 10 and 8.
- **Duplicated boilerplate.** Three etanercept findings are one copied error; there are 21 distinct text pairs and 17
  limitations, but fewer independent errors.
- **No authority.** A finding says the languages state different numbers. Which language is right is for BAG to decide;
  it can be the German.
