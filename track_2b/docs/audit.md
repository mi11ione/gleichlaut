# Pre-existing divergence audit (`gleichlaut.audit`)

Gleichlaut's guards check that a French/Italian amendment mirrors the German change. They do not check that the old
French/Italian text was right, so a divergence that is already there is carried forward. The 5 divergences we
verified by hand in the 6 Oct 2026 SL (Nemluvio, Diaphin, etanercept ×3, Cresemba, Dupixent ×4) all predate our data.
The audit separates the two cases: **"the old French/Italian already disagrees with the German"** and **"the draft is wrong"**.

It is deterministic code: no model calls, Python standard library only.

```bash
PYTHONPATH=src python3 -m gleichlaut.audit --hist DIR --date 20261006 --out data/audit [--worklist DIR] [--worklist-new DIR] [--no-dating]
```

`--hist` defaults to `$GLEICHLAUT_HIST`. The command writes three files to `data/audit/`:

- `audit_20261006.json`: every finding, plus the hits on the fresh items;
- `audit_20261006_summary.json`: the counts;
- `lang_stats_20261006.json.gz`: the register statistics that the language and editorial checks use.

Every finding has a `kind`: `number`, `unit`, `language` or `editorial`. Unless `--no-dating` is given, the run also checks
the 9 usable 2026 snapshots (all three languages present) to date each finding. That takes about 1 minute.

From code, `audit.audit_item(x)` takes an item with `de_old`, `tgt_old` and `lang` and returns a list of dicts. Each dict
has `kind`, `lang`, `detail` (one sentence in English), `values` and, where it applies, `odd_one_out`, plus `text` (one
phrase in the item's language, for the review banner). Number findings keep the round-2 keys (`side`, `value`, `unit`,
`context`), so `emit.explain.divergence` renders them as before. Unit findings carry the same keys for the target side.
`kinds=(...)` restricts the kinds returned (default: all four). Without a hist dir the function uses the shipped
`lang_stats_20261006.json.gz`.

## Kind `number` (round 2, unchanged)

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

Each number finding carries:

- the id, the product names and the language;
- `kind: number` (`numeric` in round 2) and `fid` `N01`… (the round-2 rank);
- the values on each side, with up to 3 context snippets (also flattened into `context`);
- the score and rank;
- the design half (`dev`/`held`, by md5 of the id) and a text-pair group hash;
- `known` (one of the hand-verified cases).

The ids, ranks and values are identical to round 2 (tested). Round 3 adds five fields:

- `languages`;
- `odd_one_out`: the majority vote of the three texts. A DE-only value that the third language also lacks makes `de` the
  odd one out. A target-only value that the third language also has makes `de` the odd one out too. Otherwise the target
  is. The field is `null` when the votes are mixed;
- `explained_by`: the editorial finding that produces the number difference;
- `first_seen` and `seen_in`;
- `suggested_action` (null).

## Kind `language`

For every limitation, each of the DE, FR and IT fields is checked for being predominantly in another language X
(`lang_check`).

- **A, function words.** Closed-class word lists for de/fr/it/en are fixed in the code. A word listed for two languages
  counts for neither (`la`, `le`, `il`, `des`, `un`, `in`). A few words that are also common in another language are left
  out by hand (`se`, `non`, `da`, `ne`, `on`, `an`). Rule A requires at least 3 hits for X and at least 3× the hits of the
  field's own language. English has no register profile, so it needs at least 5 hits and at least 5×.
- **B, character trigrams.** The de/fr/it profiles are built mechanically from the register itself: the distinct texts of
  each language field, minus the texts whose function words vote for another language (majority language per field).
  Words shared by the other two fields of the same limitation are removed first: product names, INNs and codes. For an
  item, which has only two texts, the words shared with the German are removed, unless that would remove half the text
  (an untranslated copy). At least 12 trigrams must remain. Their mean log-likelihood ratio X : own language must be at
  least 0.5 nat (add-one smoothing).
- A and B must name the same X. A field with fewer than 3 function words in total is **not judged**. On 6 Oct that is
  75 DE, 48 FR and 76 IT fields: short price lines, codes and names.
- The finding gives the field (`lang`, which is also `odd_one_out`), the `detected` language, and `agrees_with`, the
  fields written in the same language. It also gives `identical_to` (exact copies), the function-word counts, the
  trigram margin and the first 160 characters.

## Kind `unit`

A value present in both the German and the target text is compared on its unit class (`unit_diff`):

- time: days, weeks, months, years, hours, minutes;
- mass: µg, mg, g, kg;
- volume: ml, dl, l.

The classes are read with strict full-word patterns, so `Lebensjahr` and `Tagesdosis` are not time units. A finding
needs a class on each side that the other side lacks, in the same dimension. `4 Wochen` vs `4 mois` and `15 kg` vs
`15 mg` are findings. `6 Monate und 6 Wochen` vs `6 mois` is a difference in one direction only. Like R5, that is not a
finding: it is listed in the summary under `unit_one_sided` as a diagnostic. A text in the wrong language (kind
`language`) is not compared.

## Kind `editorial`

Conservative typo rules, run on each of the three texts (`editorial`):

| rule | pattern | example |
|---|---|---|
| E1 | stray space inside a decimal, before a unit | `1 .4 mmol/l` → `1.4` |
| E2 | preposition or article glued to a number before a unit (closed list per language) | `de15 kg` → `de 15` |
| E3 | number glued to a day, week, month or year word | `4Wochen` → `4 Wochen` |
| E4 | one edit from a number word 2..12, right before a unit word. The corrected word trigram (previous word, number word, unit word) is in ≥ 5 register texts; the observed one is in ≤ 2 | `almeno se mesi` → `sei mesi` |
| E5 | a word after a number that is in < 3 register texts and follows a number in < 2, one edit from a unit word that follows a number in ≥ 20 texts | `6 Monte` → `Monate` |

`15mg` (no space before a unit) is a common style and is not flagged. Each finding gives the rule, the surface, the
suggestion and the context. `others_have_value` lists the other languages that state the corrected value. When both do,
`odd_one_out` is the typo's language.

## Every finding

All findings carry `kind`, `fid` (`N`/`U`/`L`/`E` + rank within the kind), `languages`, `odd_one_out`, `context`,
`half`, `first_seen`, `seen_in` and `suggested_action` (a placeholder, always `null`).

**Dating.** The 9 usable 2026 snapshots are 19 Feb, 4 Mar, 1 Apr, 1 Jun, 1 Jul, 1 Aug, 1 Sep, 1 Oct and 6 Oct. The
4 May snapshot has German only. The earlier snapshots are re-checked with the rules and the 6 Oct register statistics,
so a defect is dated by when it is present, not by when a count crossed a threshold. A finding counts as present when
the same id or the same context shows the same defect. Up to April the feed used per-language `RA:` ids, and FR/IT are
aligned to DE by (product, position), as in `sl.mine.tkey`. Those snapshots list each limitation once per product
(5,841 entries), so their per-snapshot counts are not comparable with the June+ ones.

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

**Round 3 (language, unit, editorial): pre-registered.** The rules in the round-3 block of `audit.py` were written in
full before they were run on any snapshot or item. They are the function-word lists, the profile construction, every
threshold, the unit classes and E1–E5. sha256 of `audit.py` at that point: `b201922d…`. The thresholds (3 / 3×, 5 / 5×,
12 trigrams, 0.5 nat, E4 5 / 2, E5 20) are a-priori choices, not fitted. The following were **not** used to write them:
the round-2 blind labels (`data/labels/audit_20261006.tsv` was not opened), the known cases, Keytruda and Myoview.
Disclosures:

- **One change before the first register run.** A smoke test on synthetic strings, including the Myoview sentence quoted
  in the feedback, showed that the most frequent function word of three languages was missing from the lists: `de` (fr),
  `ein` (de), `una` (it). They were added (sha256 `5414d0e8…`), and nothing else changed. Myoview is therefore not an
  independent test of the language rule: it informed that fix. Keytruda was not run before the fix.
- **After the first run, only reporting changed.** That covers the dating (aligning the old-format snapshots, dating with
  the 6 Oct statistics, content keys), the `odd_one_out` / `explained_by` / `others_have_value` fields, the
  `unit_one_sided` diagnostic, the worklist and the output format. The detection code in the round-3 block is identical
  to `5414d0e8…` apart from the added diagnostic function (checked by diff). No threshold was changed after any output
  was seen.

Two consequences follow for round 2. First, dev-half findings were partly shaped by inspection: 2 dev noise findings were removed by
the fixes. Precision should therefore also be reported on the `held` half alone; the key map carries the half. Second,
the known cases were found by S1's numeric flags and a sweep over unit-carrying numbers. A numeric audit recovering them
is therefore expected and is not evidence about divergences of other kinds.

## Numbers (6 Oct 2026 snapshot, 1,688 limitations)

| | |
|---|---|
| Findings by kind | **number 21** (14 FR, 7 IT; unchanged), **unit 0**, **language 1** (IT), **editorial 5** (1 DE, 3 FR, 1 IT); 27 findings on 20 limitations |
| Recall, known divergent limitations (number) | **10 of 10**; 13 of 13 hand-verified values on the right side and in the right language |
| Keytruda KN045 | **found** (`L01`): the IT field is identical to the FR text (function words fr 39 / it 1, trigram margin 2.16 nat); first seen **1 Aug 2026**, present in 4 snapshots (Aug, Sep, 1 Oct, 6 Oct) |
| Other language findings | none on 6 Oct, and none in any of the 9 snapshots (`language_any_snapshot`). On 6 Oct no other field passes even rule A alone |
| Number findings explained by a typo | 4 of 21: LEQVIO FR+IT (`N16`, `N17` ← German `1 .4`), PREVYMIS FR (`N04` ← `de15`), FORSTEO IT (`N13` ← `se mesi`) |
| Odd one out (number) | the target in 13 findings; **German** in 8, where FR and IT agree against DE: CERDELGA, EMGALITY, GALAFOLD and LEQVIO, FR+IT each. For LEQVIO the cause is the German typo |
| Not reported | 230 count-only differences; 148 unbound value differences; 13 one-directional unit differences (`unit_one_sided`) |
| Fresh items (166) with a language or number problem in the old texts | **2**: `wb004-it` (Nemluvio, number) and `wb079-it` (Myoview, the old "Italian" is French). No fresh item has a unit or editorial finding |
| Model calls | 0 |

The editorial findings, with their first snapshot (all present since 19 Feb 2026):

| fid | limitation | text | defect | the other two languages say |
|---|---|---|---|---|
| E01 | LEQVIO.01 | DE | `kleiner 1 .4 mmol/l` | 1.4 (fr, it) |
| E02 | DUPIXENT.07 | FR | `moins de15 kg` | 15 (de, it) |
| E03 | DUPIXENT.07P | FR | `moins de15 kg` (same text as E02) | 15 (de, it) |
| E04 | PREVYMIS.01 | FR | `pesant de15 kg à moins de 30 kg` | 15 (de, it) |
| E05 | FORSTEO-2 | IT | `almeno se mesi` | 6 (de, fr) |

E02 and E03 (Dupixent 6 months to 5 years, FR) were not among the round-2 findings. The French text has no number to
compare, so the number check could not see them.

Ranks of the known findings: Diaphin 1, Dupixent.05P 2, Dupixent.05a 3, Benepali 5, Cresemba 9, Erelzi 12,
Nemluvio 18, Nepexto 19, Dupixent.02 20, Dupixent.02P 21.

**Nemluvio in the fresh run.** The old Italian already said "quattro". The recorded 70B draft for `wb004-it`
(`data/runs/70b_fresh166_g3_final.jsonl`) wrote "ogni otto settimane", in line with the German. BAG's own new Italian text kept
"quattro". The guards flagged the draft. Among their reasons: "changed text outside the amended part: «⟨L⟩» -> «⟨M⟩»"
(quattro → otto), and "lost words that the German change does not touch: quattro". The guards were right that the edit
went outside the amendment. With `audit_item` the review page can add that the old Italian already disagreed with the
German at that spot, so the reviewer can tell a correction from an error.

**Myoview (`wb079-it`).** The old Italian text "Prix de facturation par application et patient 230.27 (Division 7.5)."
is French. It has 3 French function words (`de`, `par`, `et`), and its trigram margin confirms French. `audit_item`
returns a `language` finding with `odd_one_out: it`. The defect was corrected by the amendment of 19 Feb 2026, the item's own
new text. Since then the Italian `MYOVIEW2` has read "Prezzo di fatturazione…". The register check (2026 snapshots)
therefore cannot show it; it appears only in the fresh set's old text (snapshot 1 Jul 2025).

**Precision: round 2.** The 21 number findings were labelled blind: 10/21 real, all of them the known cases (see
`eval/results/audit.json`). The 11 others include the three typos above, which the number check misread as divergences.
They are now reported as editorial findings and linked through `explained_by`.

**Precision: round 3, pending blind labels.** All 6 new findings (1 language, 5 editorial; there is no unit finding) go
to blind annotators, shuffled with seed 20261010. We did not label them. The worklist has fields `id` B00…, `kind`,
`lang`, the full `de`/`fr`/`it` texts, `finding` and `question`. The key map holds the CUD, `fid`, rule, half and first
snapshot. Both are written by `--worklist-new DIR`. Report precision per kind. Six findings give a wide interval, and
Keytruda was known before the rules existed.

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

- **What is still not checked.** A wrong drug class, a changed operator (≥ vs >), a dropped negation, and a German-only
  clause without numbers. The term-pair signal for drug classes is off (above).
- **Unit check.** It needs a difference in both directions. A value that keeps its unit in one place and changes it in
  another (`unit_one_sided`, 13 cases on 6 Oct) is not reported, and neither is a difference that changes both value and
  unit (`28 Tage` vs `4 mois`: that is a number finding, or a conversion). The classes cover time, mass and volume only,
  not IU or mmol. With 0 findings on the register, the check is tested on synthetic cases only.
- **Language check.** Fields with fewer than 3 function words (about 200 short price lines and codes) are not judged. A
  partly translated text (half French, half Italian) passes when the own language still has a third of the function
  words. English is checked by function words alone. The rule finds what it was built for; one register case is no
  measure of recall.
- **Editorial rules.** They are deliberately narrow. E4 and E5 depend on register counts: E4 needs the corrected phrase in
  at least 5 texts. FORSTEO's `almeno sei mesi` is in 5 texts in August, but only 4 in June and July, so E4 would not have
  fired with those months' own statistics. Misspellings that are not next to a number are not looked for.
- **Recall of the number check is measured on cases a numeric method found.** It is optimistic for divergences in
  general.
- **Number words.** Only 2–12 (frozen `NUMW`). FR hyphenated numbers (`dix-huit`) are read as 10 and 8.
- **Duplicated boilerplate.** Three etanercept findings are one copied error, and so are E02/E03. There are fewer
  independent errors than findings.
- **No authority.** A finding says the languages differ or that a passage looks mistyped. Which version is right is for
  BAG to decide; it can be the German (see `odd_one_out`).
