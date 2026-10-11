# Pre-existing divergence audit (`gleichlaut.audit`)

Gleichlaut's guards check that a French/Italian amendment mirrors the German change. They do not check that the old
French/Italian text was right, so a divergence that is already there is carried forward. The 5 divergences we
verified by hand in the 6 Oct 2026 SL (Nemluvio, Diaphin, etanercept ×3, Cresemba, Dupixent ×4) all predate our data.
The audit separates the two cases: **"the old French/Italian already disagrees with the German"** and **"the draft is wrong"**.

It is deterministic code: no model calls, Python standard library only.

```bash
PYTHONPATH=src python3 -m gleichlaut.audit --hist DIR --date 20261006 --out data/audit \
    [--worklist DIR] [--worklist-new DIR] [--worklist-terms DIR] [--no-dating] [--terms FILE] [--fail-on-findings]
PYTHONPATH=src python3 -m gleichlaut.audit --list migel|al --file PATH [--out data/audit] [--worklist DIR] [--fail-on-findings]
```

`gleichlaut audit ...` passes the same arguments through. `--hist` defaults to `$GLEICHLAUT_HIST`. The SL run writes five
files to `--out`:

- `audit_<date>.json`: every finding, plus the hits on the fresh items;
- `audit_<date>_summary.json`: the counts;
- `audit_texts_<date>.json`: the DE/FR/IT texts of every limitation with a finding, so the register tab can show excerpts
  without the snapshot files. The excerpts in the register and the Fallblätter come from the sentence alignment the
  round-5 checks use (`aligned_span`, `operator_display`; display only, no count depends on it): the place where the
  texts differ, in all three languages, not the first occurrence of the value (`tests/test_excerpts.py`);
- `lang_stats_<date>.json.gz`: the register statistics that the language and editorial checks use;
- `term_pairs_<date>.json`: the terminology pairs mined from BAG's own corrections (`--terms FILE` reuses a file instead).

Every finding has a `kind`: `number`, `unit`, `language`, `editorial` or `terminology`, and a boolean `likely_equivalent`
(with `equivalence`, the reason). Unless `--no-dating` is given, the run also checks the 9 usable 2026 snapshots (all
three languages present) to date each finding. The whole run takes about 3 minutes. `--fail-on-findings` makes the exit
code 1 when any finding is not marked `likely_equivalent` (the `gleichlaut audit` wrapper maps it to its own code). Round 5
(PREREG R15: `operator`, `negation`, `number_word`) is written apart, to `findings_r5` and `summary.round5`; it is off
after its pre-registered test (section "Round 5"). `--worklist-r5 DIR` writes its blind worklist.

From code, `audit.audit_item(x)` takes an item with `de_old`, `tgt_old` and `lang` and returns a list of dicts. Each dict
has `kind`, `lang`, `detail` (one sentence in English), `values` and, where it applies, `odd_one_out`, plus `text` (one
phrase in the item's language, for the review banner). Number findings keep the round-2 keys (`side`, `value`, `unit`,
`context`), so `emit.explain.divergence` renders them as before; they also carry `likely_equivalent` and `equivalence`.
Unit findings carry the same keys for the target side. Terminology findings carry `old`, `new`, `de_term`,
`corrected_in` and `n_limitations` (no `side`/`value` keys, so the banner uses their `text`). `kinds=(...)` restricts the
kinds returned (default: all five). Without a hist dir the function uses the shipped `lang_stats_20261006.json.gz` and
`term_pairs_20261006.json` (`terms=[]` turns the terminology check off).

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

## Kind `terminology` (round 4)

BAG's own corrections are the lexicon: no hand list. Code: the round-4 block of `audit.py` (`term_edits`, `mine_terms`,
`term_check`).

- **Sources of corrections.** (a) The 8 transitions between the 9 usable 2026 snapshots. Limitations are aligned by
  product and position (the ids of the Feb–Apr snapshots change from one snapshot to the next), and by id from June on.
  (b) The recorded BAG amendments of the item set (`--items`, default `data/items/items_fresh.json`: BAG's old and new
  DE/FR/IT texts, Jul 2025 → 19 Feb 2026).
- **T1 edit.** A token `replace` between the old and the new target text: 1–8 tokens on each side (lower-cased, ’ = ',
  punctuation ignored), no digit (numbers are the number check's), a word of at least 3 letters on each side, not an
  accent-only change and not a one-word inflection. A target pair with token similarity < 0.5 is a retranslation; no
  edits are taken from it.
- **T2 the German does not explain it.** The German is unchanged, or it changed (similarity ≥ 0.5) only at places more
  than 0.15 (relative position) away from the target edit.
- **T3 support.** Kept when BAG applied the same pair in ≥ 2 limitations (distinct new German texts) or ≥ 2 transitions,
  and the reverse edit never occurs.
- **T4 the German term.** The German word stems (≥ 6 letters, not a function word, not a word of the target texts) in the
  old and new German of every instance; the one with the highest Dice between "stem in the German" and "old or new
  phrase in the target" over the current register. Kept when Dice ≥ 0.5.
- **T5 phrase.** Old and new phrase are extended by the context tokens (up to 3 each side) that all instances share.
- **T6 flag.** A current text whose target contains the old phrase and whose German contains the term, with fewer
  occurrences of the new phrase than of the German term.

**Result on 6 Oct 2026.** 5 pairs, 11 findings on 7 limitations (7 FR, 4 IT):

| pair | German term | BAG applied it | still old on 6 Oct |
|---|---|---|---|
| FR `inhibiteur de l'enzyme de conversion de l'angiotensine II` → `antagoniste des récepteurs de l'angiotensine II` | Angiotensin-II-Antagonisten (Dice 1.0) | 18 limitations, 19 Feb 2026 (item set) | `T01`–`T04`: COVERAM-PLUS, PERAMLIND.me, PERAMLIND.sp, PERINDAMLIND |
| IT `di un cosiddetti antagonisti del recettore dell'angiotensina` → `di un antagonista del recettore dell'angiotensina` | same | 18 limitations, 19 Feb 2026 (item set) | `T05`–`T08`: the same four products |
| FR `limitation doit être communiqué à l'assureur-maladie` → `… transmis à …` | Limitierung (Dice 0.62) | 11 OPDIVO limitations, 1 Oct 2026 (snapshots) | `T09`–`T11`: JEMPERLI.01, JEMPERLI.02, OPZELURA.01 |
| IT `alla cassa malattia` → `all'assicuratore malattie` (two contexts) | Angiologie (see caveats) | 3 and 2 limitations, 4 Mar 2026 | none |

The four angiotensin products have carried the old French and Italian since at least 19 Feb 2026 (present in all 9
snapshots). **The angiotensin pairs come from source (b), not from the 2026 snapshots:** BAG corrected those texts between
July 2025 and 19 Feb 2026, and inside 2026 the four remaining texts never changed. From the snapshots alone the rule finds
only the "communiqué → transmis" and "cassa malattia" pairs.

`audit_item` uses the shipped `term_pairs_20261006.json`. On the 166 fresh items it gives a terminology notice to the 18
old French texts with the angiotensin error (`wb015-fr` … `wb032-fr`) and to their 18 Italian twins. That is by
construction: those 36 amendments are where the pairs were learned, so the notices are not evidence that the rule
generalises. The independent evidence is the four register products that BAG has not corrected.

## `likely_equivalent` (round 4, triage only)

A boolean on every finding, with `equivalence` (the reason). It never changes a finding's id, rank or any count; it is
for sorting and for `--fail-on-findings`. Only number findings are assessed (the other kinds are `false`). A number
finding is likely equivalent when a typo finding explains it (`explained_by`), or when **every** one-sided value has one of:

- **Q1 conversion** against any value of the other text: N days = N/7 weeks, N months = N/12 years, h/d, min/h, µg/mg/g/kg,
  ml/dl/l (`innerhalb von 14 Tagen` = `dans les deux semaines`);
- **Q2 interval**: an ordinal of N followed by the same time unit on the other side (`jeden zweiten Tag` = `tous les deux
  jours` = `ogni due giorni`), and `un jour sur deux` / `giorni alterni`;
- **Q3 adults**: 18 years on one side, `Erwachsene / volljährig`, `adultes / majeurs`, `adulti / maggiorenni` on the other;
- **Q4 spelled out**: the other side writes N (13–100) as a word (`dix-huit`, `sechzehn`, `diciotto`);
- **Q5 boundary**: N and N ± one step with the same unit, one written inclusive (`ab`, `≥`, `dès`, `almeno`, `bis`) and the
  other strict (`über`, `>`, `plus de`, `oltre`, `unter`, `moins de`).

`6%` vs `6 pour cent` and ranges written `15–30` vs `de 15 à 30` are already reconciled by R2, so they need no rule.

**Check against the round-2 blind labels** (`eval/labels/audit_20261006.tsv`; used as a check, not to fit): 9 of the 11
findings labelled not real get `likely_equivalent` (LEQVIO ×2, PREVYMIS, FORSTEO by the typo link; BEYFORTUS Q1;
GALAFOLD ×2 Q2; CERDELGA ×2 Q3). The two EMGALITY findings (120 mg named in German only) stay open: no generic rule
covers them. **0 of the 10 findings labelled real** get it. That is pinned by a test, which reads the labels. Disclosure:
the officer's feedback named Galafold, Beyfortus and Cerdelga (5 of the 11), so Q1–Q3 were written with those cases in
view. The label file had also been opened during orientation, before the rules were written. The 9/11 is therefore not
an independent estimate; the 0/10 on the real findings is the part that matters.

## Other lists: MiGeL and Analysenliste (round 4)

`gleichlaut.audit_lists` reads BAG's xlsx (stdlib `zipfile` + `xml.etree`): one sheet per language, rows aligned by item
number (MiGeL `Positions-Nr.`, or the category code for group rows; AL `Pos.-Nr.`). The text columns are MiGeL
`Bezeichnung` and `Limitation`, and AL `Bezeichnung`, `Limitationen` and `Bemerkungen`. The number, unit, language and
editorial checks run unchanged, with register statistics built from the list itself. There is no terminology check
(its pairs come from the SL). Each run writes `data/audit/audit_<list>_<date>.json` (summary with source URL and sha256,
parse report, findings) and, with `--worklist DIR`, a blind seeded sample of up to 40 findings plus a key map.

The raw files were fetched once from the BAG pages (`docs/sources.md` §6) with the user agent `hackapertus-research/0.1`,
at most 1 request per second. They are in the repo as `data/lists/migel_20260701.xlsx` and `data/lists/al_20260701.xlsx` (sha256 below), so
`python3 -m gleichlaut.audit --list al --file data/lists/al_20260701.xlsx` reproduces the committed findings:

| list | version | sha256 | positions (all 3 languages aligned) | DE text fields | findings |
|---|---|---|---|---|---|
| MiGeL | per 1 Jul 2026 | `6335483a…` | 1,036 | 1,304 | **8**: number 7 (6 FR, 1 IT), editorial 1 (FR `30jours`); unit 0, language 0 |
| AL | per 1 Jul 2026 | `0b0730ee…` | 1,280 | 1,933 | **3**: number 3 (2 FR, 1 IT); unit 0, language 0, editorial 0 |

None of the 10 number findings is marked `likely_equivalent`. All 11 findings were labelled from the blind
worklists (`eval/labels/audit_migel_20260701.tsv`, `audit_al_20260701.tsv`): 7 real. The texts are short and
structured. Most language fields are too short to judge (MiGeL DE 870 of 1,304; AL DE 1,294 of 1,933), so the language
check says little here.

## Quarterly path (BAG officer)

1. Fetch the SL feed of the date into a snapshot dir: `make audit AUDIT_DATE=YYYYMMDD` does steps 1–2 in Docker
   (fetches missing feeds, writes `out/audit`), or by hand `python -m gleichlaut.sl.ingest YYYYMMDD --out DIR`
   into `$GLEICHLAUT_HIST`. Keep the earlier snapshots of the same year in that dir: dating and terminology mining
   use them.
2. `python -m gleichlaut.audit --hist DIR --date YYYYMMDD --out data/audit` (add `--fail-on-findings` in a scheduled job).
   This writes the five files above; the register needs `audit_<date>.json` and `audit_texts_<date>.json`, the review page
   (`audit_item`) needs `lang_stats_<date>.json.gz` and `term_pairs_<date>.json`.
3. Build the review page with the new file: `gleichlaut ui --audit data/audit/audit_<date>.json` (the UI's `--audit`
   option). Note that `audit_item` still reads the 20261006 statistics and pairs by default; pass `stats=`/`terms=` or
   update `STATS`/`TERMS` when a new quarter becomes the reference.
4. Optional: `--worklist-terms DIR` / `--worklist-new DIR` for blind labelling. For MiGeL/AL, download the current xlsx
   from the BAG page and run `--list migel|al --file PATH`.

## Every finding

All findings carry `kind`, `fid` (`N`/`U`/`L`/`E`/`T` + rank within the kind), `likely_equivalent`, `equivalence`, `languages`, `odd_one_out`, `context`,
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
| Findings by kind | **number 21** (14 FR, 7 IT; unchanged), **unit 0**, **language 1** (IT), **editorial 5** (1 DE, 3 FR, 1 IT), **terminology 11** (7 FR, 4 IT; round 4); 38 findings on 27 limitations (27 on 20 without terminology) |
| Likely equivalent (number) | 9 of 21 (round 4, triage only) |
| Recall, known divergent limitations (number) | **10 of 10**; 13 of 13 hand-verified values on the right side and in the right language (circular: see the next row) |
| Recall, planted divergences (200 per type, FR+IT) | number **93.0%**, unit **73.0%**, clause deletion **75.0%**, wrong language **94.0%**, typo next to a number **51.0%** (section "Recall on planted divergences") |
| Recall, planted v2 (sites drawn from all numbers; 200 per type) | any number **55.5%**, number word **37.0%**, flipped operator **0%**, dropped negation **0%** (subsection "v2: sites not chosen by the detector's own rule") |
| Round 5, off (PREREG R15, held half, 200 per type) | with the round-5 checks: flipped operator 0 → **74.5%**, dropped negation 0 → **44.0%**, added negation 0 → **55.5%**, number word 30.5 → **84.0%**; 31 register findings, 6 real or minor (no kind reaches the 50% precision bar; section "Round 5") |
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

**Precision: round 2.** The 21 number findings were labelled blind: 10/21 real, all of them the known cases (relabelled under R14 by two blind
Claude annotators and a tie-break: 11/21 confirmed, the 11th a minor typo, «se mesi») (see
`eval/results/audit.json`). The 11 others include the three typos above, which the number check misread as divergences.
They are now reported as editorial findings and linked through `explained_by`.

**Precision: round 3, labelled.** The 6 round-3 findings (1 language, 5 editorial; no unit finding) were labelled blind
(`eval/labels/audit2_20261006.tsv`): **6/6 real** (Wilson 95% 0.61–1.00; under the R14 relabel 6/6 confirmed, 2 change a condition and 4 are minor): language 1/1 (Keytruda), editorial 5/5. Two
caveats: six findings give a wide interval, and Keytruda was known before the language rule existed. The rule was
written to find exactly that case, so it does not count as an independent hit. The round-2 number findings stay at
**10/21 real** (0.28–0.68).

**Labels status (round 4).** Terminology: all 11 findings in the blind worklist (`--worklist-terms`, ids C00…, seed
20261011), labelled: 8 confirmed. MiGeL/AL: 11 findings in two blind worklists, labelled: 7 confirmed. `likely_equivalent` is checked
against the round-2 labels (above).

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

## Recall on planted divergences

The 10/10 above is circular. An earlier numeric census found the 10 known cases, and the rules were written around that
census's noise classes. To measure recall without that loop, we planted faults of five declared types into copies of the
register and ran the unmodified audit on every copy. Command: `python3 tools/audit_inject.py` (stdlib, no model, no
network, seed 20261010). Output: `eval/results/audit_injection.json`, with every miss and its reason. It takes about
25 minutes on 8 cores.

**Protocol.** It was written into the script's docstring before the first run, and the audit's rules were not touched.

- **Register.** The 6 Oct 2026 snapshot (1,688 limitations). We keep one limitation per distinct DE/FR/IT text triple
  and drop every triple that has a baseline finding of any kind. That leaves 1,597 eligible limitations, so any finding
  on a copy comes from the planted fault.
- **Sites.** The script's own pattern finds them, not the audit's parser: a number (digits, or a number word 2–12)
  followed by a unit or quantity word.
- **Sampling.** Per type and target language: a seeded shuffle of the eligible limitations that have a site; we take the
  first 100. That gives 100 FR + 100 IT copies per type. Each copy has one fault and one modified field.
- **Types.**
  - `number`: one value changed to another plausible one (n → 2n, n±1, n/2, n+10; x → 2x or x/2; a number word to
    another number word).
  - `unit`: one unit changed within its dimension, the number kept (mg↔µg, g→mg, kg→g, ml→dl; days→weeks→months,
    months→weeks, years→months).
  - `deletion`: one sentence or comma clause that contains a number is deleted.
  - `language`: the whole target field is replaced by one of the other two language fields.
  - `typo`: one edit next to a number. The edit glues a word to the number or deletes, doubles, substitutes or
    transposes a letter. It lands in the word before the number, in the unit word after it, or in a number word itself.
- **Detection (strict).**
  - `number`: a number finding with the new value on the target side or the old value on the German side.
  - `unit`: a unit finding for the changed value.
  - `deletion`: a number finding with a value of the deleted clause on the German side.
  - `language`: a language finding on the target field that names the source language.
  - `typo`: an editorial finding within 30 characters of the edit.
  - "Any" counts a copy whose limitation has any finding of any kind.
- **Execution.** For each copy, the register statistics are rebuilt from the modified register (`build_stats`). The
  shipped terminology pairs are used (as with `--terms`), and `run_all` runs on the copy's limitation. A limitation's
  findings depend only on its own three texts, the statistics and the pairs. We checked this on 100 copies by running
  the full register: the statistics were identical in 100 of 100, and so were the findings on the modified limitation.

| type | n (FR+IT) | detected | recall | Wilson 95% | any finding |
|---|---|---|---|---|---|
| number | 200 | 186 | **93.0%** | 88.6–95.8 | 93.0% |
| unit | 200 | 146 | **73.0%** | 66.5–78.7 | 73.0% |
| deletion | 200 | 150 | **75.0%** | 68.6–80.5 | 75.0% |
| language | 200 | 188 | **94.0%** | 89.8–96.5 | 94.0% |
| typo | 200 | 102 | **51.0%** | 44.1–57.8 | 56.0% |

Pooled, the five types give 772 of 1,000 (77.2%, 74.5–79.7). That figure describes this protocol's equal mix of types,
not the real frequency of errors. FR and IT differ by at most 8 points in every type.

**False positives elsewhere.** In the 100 full-register re-runs, no finding appeared on or disappeared from any other
limitation (0 new, 0 lost). In 11 of those re-runs, the trigram margin of the Keytruda language finding moved in the
third decimal: the profile of a language includes the one changed text. The finding stayed the same. The first full run
showed this as 3 "new + lost" pairs, so the comparison now ignores the margin.

**What the misses teach** (all counts from the output file):

- **Number: masked by repetition (12 of 14 misses).** The comparison works on sets of values (R5). Take STRENSIQ:
  `2 mg` → `1 mg` is invisible when the target still says 2 mg elsewhere and the German states 1 mg elsewhere. One
  more miss is R4d at work: NORDITROPIN `4 ans` → `3 ans`, where the German "4. Lebensjahr" is age 3. The planted text
  is arguably a correct rendering. The last miss (KIMMTRAK `tre` → `quattro infusioni`) is R2: the German
  "drei KIMMTRAK-Infusionen" binds no unit, and 4 occurs in the German elsewhere.
- **Unit: one-directional (51 of 54 misses).** The value still carries its old unit somewhere else in the target. For
  example, ABEVMY `3 semaines` → `3 mois` while another `3 semaines` stays. The unit check needs a class difference in
  both directions, so this lands in the `unit_one_sided` diagnostic and not in the findings (see "Unit check" under
  Caveats). Two more misses have the value with both units in both texts. The last has a German unit outside the
  classes (RINVOQ "18. Lebensjahr"). Promoting `unit_one_sided` to a finding would flag these 51. Its precision
  is unmeasured: 13 such cases on 6 Oct, unlabelled.
- **Deletion: the deleted values survive elsewhere (40 of 50 misses).** An example is SELINCRO "… 12 mois maximum.",
  where 12 months appears again. On the 160 copies where at least one deleted value disappears from the target,
  recall is **150/160 = 93.8%** (88.9–96.6). The other misses: 6 are R3 (value 1 is never reported when the other text
  has an article, even `1%`), and 4 are R2 (unbound values).
- **Language: short fields (11 of 12 misses).** The check does not judge fields with fewer than 3 function words, for
  example MERONEM "Fibrosi cistica" → "Mukoviszidose". On judged fields recall is **188/189 = 99.5%** (97.1–99.9). The
  one miss is OCTOSTIM: its FR field became the Italian "Emofilia A et morbo di di von Willebrand Tipo I.", which has
  only 2 Italian function words.
- **Typo: the rules are narrow by design (98 misses).**

  | subtype | detected | why the rest are missed |
  |---|---|---|
  | glue before a number | 36/41 | E2 accepts only listed prepositions and articles |
  | glue to a unit word | 19/23 | E3 covers time words only |
  | doubled letter in a unit word | 26/27 | |
  | substituted letter in a unit word | 11/18 | |
  | deleted letter in a unit word | 6/28 | `semaine` is a real word, and E5 skips words under 4 letters (`ans`, `ore`) |
  | edit to a number word (no transposition) | 4/8 | E4 needs the corrected phrase in at least 5 register texts |
  | transposed letter | 0/24 | a transposition is 2 edits for `lev1` |
  | edit to the word before a number | 0/31 | no rule looks there |

  Ten more copies are caught as number findings instead, which is why "any" reaches 56%.

**Limits of this measurement.**

- We designed the faults ourselves. The site pattern and the audit share the common unit words, so number, unit and
  deletion recall hold only for faults next to a unit word.
- Paraphrase-level divergences and partial translations are not planted. Changed operators and dropped negations are
  planted in v2 (below).
- The typo model is ours, not an observed error distribution.
- The result answers "if a fault of this shape were there, would the audit see it?" It does not say how many real
  divergences the register holds.

**Cheap rule changes the misses point to** (reported, not applied; no rule was changed for this measurement):

- restrict R3 to a `1` that no unit symbol follows (R3 hid 6 deletions, among them SIMVASzentiv's `supérieur à 1%`);
- treat a transposition as one edit in E4/E5 (24 typo misses);
- report `unit_one_sided` (51 unit misses).

Each of these would need its own precision check before it ships.

### v2: sites not chosen by the detector's own rule

A juror pointed out a flaw in v1. Its number, unit and deletion sites are "a number followed by a unit word", and that
is the same binding rule (R2) the number check relies on. So 93% number recall is close to true by construction. v1 also
planted no operator flips. v2 answers both points. Command: `python3 tools/audit_inject.py --protocol v2` (seed
20261011, stdlib, no model, no network). Output: `eval/results/audit_injection_v2.json`. It took 885 s on 8 cores.
v1 and its output file are unchanged.

**Protocol.** It was written into the script's docstring ("PROTOCOL v2") before the first v2 run. The audit's rules were
not touched. The register, the eligible pool (1,597 finding-free limitations), the one-fault-per-copy rule and the
execution are as in v1. Sites come from the script's own number pattern.

- **Sites.** Every number token in the target text is a site: digits, thousands such as `1'000` or `150 000`,
  decimals, dates, and the number words 2–12. Unit words, list numbers, counts, years, prices, scores and table cells
  all count. Three kinds of token are excluded, and only these. All three are identifiers copied verbatim, and the
  audit's documented R2 scope does not report them:
  - BAG indication codes (`19989.01`, and the `19989` of `19989.XX`): 615 FR / 616 IT tokens in the pool;
  - Index Therapeuticus group codes (`I.T. 02.06`): 25 / 25;
  - multi-separator references (`RS 832.112.31`): 7 / 7.

  Digits glued to a preceding letter (`FEV1`, `HER2`) are names to the audit and are not tokens here either. In the
  eligible pool, 52% of the FR sites and 54% of the IT sites are also v1 sites.
- **Types.**
  - `number_any`: one token is drawn uniformly from all the sites in the text. It is changed by the v1 rule. A year
    moves by ±1. A date changes its day or its year.
  - `number_word`: one number word, anywhere in the text, becomes another one.
  - `operator`: one comparison operator within 25 characters of a number, in the same sentence, is flipped. The pairs
    are: au moins ↔ au plus, au minimum ↔ au maximum, maximum ↔ minimum, plus de ↔ moins de, supérieur ↔ inférieur,
    almeno ↔ al massimo, massimo ↔ minimo, più di ↔ meno di, superiore ↔ inferiore, oltre ↔ sotto, ≥ ↔ ≤ and > ↔ <.
  - `negation`: one negation within 60 characters of a number is dropped: FR `ne/n' … pas` and `non`, IT `non`.
- **Detection.** For the two number types the rule is the same as for v1 numbers. The audit has no operator or
  negation kind. For those two types, a finding of any kind counts if it points to the place: a number or unit
  finding on a value within 60 characters of the edit, or an editorial or terminology surface within 30 characters.

| type | n (FR+IT) | detected | recall | Wilson 95% | any finding |
|---|---|---|---|---|---|
| number_any | 200 | 111 | **55.5%** | 48.6–62.2 | 55.5% |
| number_word | 200 | 74 | **37.0%** | 30.6–43.9 | 37.5% |
| operator | 200 | 0 | **0.0%** | 0.0–1.9 | 0.0% |
| negation | 200 | 0 | **0.0%** | 0.0–1.9 | 0.0% |

FR and IT differ by at most 3 points. In 40 full-register re-runs, the statistics and the findings were identical, with
no finding new or lost elsewhere.

**Reading.** The v1 figure holds only where v1 measured it. Off the unit rule, the number check is close to blind:

| number_any, by site | n | detected | recall (Wilson 95%) |
|---|---|---|---|
| a v1 site (number + unit word) | 111 | 104 | 93.7% (87.6–96.9), matching v1's 93.0% |
| any other digit | 76 | 7 | 9.2% (4.5–17.8) |
| a number word not before a unit word | 11 | 0 | 0% (0–25.9) |
| a list number, a date | 1 + 1 | 0 | |

Split by the audit's own parse of the original text, the result is the same. Recall is 109/119 (91.6%) where R2 binds
the planted token to a unit, and **2/80 (2.5%)** where it does not. For `number_word` the split is 73/102 at a unit
word and **1/98** elsewhere.

That gap is the main finding. It is the documented price of R2: the high precision of number findings is bought with
unbound values, and v2 puts a number on that price. Operator flips and dropped negations are not seen at all. The
audit never claimed to see them (S1's operator and negation flags had 0 real hits), but before v2 that was a
statement, not a measurement.

**What the misses are** (counts from the output file):

- **number_any (89 misses).** 61 are unbound values (R2), 15 are masked by repetition (R5), 12 are a value 1 hidden
  by R3, and 1 is a list number (R1). We read the 76 contexts of the other-digit sites without labelling them. About a
  third are parts of names or designations: `exon 19`, `6-mercaptopurine`, `HIV-1`, `t(11;14)`, `diabète de type 2`,
  `article 12b`. Changing one of those is still wrong, but it is rarely a translation error. The rest are content, and
  the audit misses them (R2 unless noted):
  - pack and dose counts: `4 gruppi di rischio`, `1 goutte` (R3), `3 emballages de TREMFYA` (masked, R5);
  - lines of therapy: `2L+`, `1L`;
  - ECOG, stage and grade: `ECOG 0-1`, `stade 3 à 4`;
  - score cut-offs: `CIRS > 6`, `SCORAD 50`, `BMI 28`;
  - prices: `Fr. 0.44 par mg`, `CHF 132.71`;
  - `35` cycles at most;
  - units missing from the lexicon: `300 pg/ml`, `0,345 mm²`.
- **number_word (126 misses).** 77 are unbound: `au moins deux lignes de traitement` → `quatre lignes` is invisible,
  because "lignes" is not a quantity noun. 39 are masked by R5, and in 10 the German writes the value differently
  (`deux yeux` / "beide Augen").
- **operator (200 misses).** Examples: `pesant au moins 40 kg` → `au plus 40 kg`, `plus de 75 ans` → `moins de 75 ans`,
  `FeNO ≥ 50 ppb` → `≤ 50 ppb`, `un massimo di 24 mesi` → `un minimo di 24 mesi`. Six planted flips are not comparison
  operators in context: `au plus tôt` ×2, `au plus tard`, and `limite supérieure` / `superiore` ×3. Each still changes
  the meaning. The result is 0 either way.
- **negation (200 misses).** Examples: `n'est pas suffisamment contrôlée avec 1 mg` → `est suffisamment contrôlée`;
  `non è rimborsata` → `è rimborsata`; `NSCLC non squamoso` → `NSCLC squamoso`.

**Limits of v2.** One site per limitation means texts with many numbers are under-weighted per token, as in v1. The
operator and negation lexicons are ours, and FR has more pairs than IT. The detection window for those types is
generous, so a finding there would have been counted even if it was only near the edit. None occurred.

**Cheap rule changes the misses point to** (reported, not applied; each needs its own precision check):

- **Report a one-for-one swap of unbound values.** Report one when DE and the target each have exactly one value the
  other lacks, and both value sequences otherwise align in order. This does not grow the unit lexicon. It targets the
  61 + 77 R2 misses. The 148 unbound value differences of 6 Oct are the precision sample.
- **Add the count nouns and units the misses show to R2's lexicon**: lignes/linee, traitements/terapie,
  goutte/goccia, flacon(e), pièce/pezzo, tube/tubo, critères/criteri, `pg`, `mm²`. This is cheaper but whack-a-mole.
- **Restrict R3** to a `1` that no unit symbol follows (already listed under v1; it hid 12 of the 89 here).
- **Add an operator-direction check.** For a value both texts state once, compare the direction of the operator next
  to it. Lower bounds: mindestens/ab/über/mehr als/≥, au moins/plus de/supérieur/≥, almeno/oltre/superiore/≥. Upper
  bounds: höchstens/bis/unter/weniger als/≤, au plus/au maximum/moins de/inférieur/≤, al massimo/massimo/sotto/
  inferiore/≤. Report only opposite directions, not ≥ against >: "ab 12 Jahren" against "plus de 12 ans" is a known
  style difference. `audit.py` already has the DE lists (`EQ_INCL`, `EQ_STRICT`). S1's operator flags were 0 real, so
  precision must be measured before this ships.
- **Add a negation check per aligned value.** Flag a clause that holds a shared value and has a negation on one side
  only (nicht/kein against ne…pas/non). This is noisier: "kein" ↔ "aucun", and "ohne" ↔ "sans" ↔ "senza". It is the
  last one to try.

## Round 5: operator direction, negation, number words (PREREG R15, measured, off)

Two jurors called flipped operators, dropped negations and number words the legally dangerous blind spots of v2: a
"congruence checked" stamp would give false assurance exactly there. Round 5 adds three checks for them. R15 fixed the
evaluation, the pass rule per kind and the decision before any of the rules existed (commit `28fe22b`). The rules were
then written on the dev half only, and frozen in commit `6a2c269`; the sha256 of the round-5 block is `2d5dcaaf…`
(`summary.round5.rules_sha256`, bytes as frozen) and of its rule logic `480ef3e3…` (`rules_logic_sha256`: the syntax tree
without comments or docstrings; a comment edit after the freeze moved the byte hash only, PREREG results log, R15
post-freeze note; `tests/test_audit_r5.py` checks it). They are stdlib only and call no model.

- **`operator`.** Each value (digits or a number word) that has a comparison word right before it, or right after it
  and its unit, gets a direction: a lower bound (mindestens, ab, über, mehr als, ≥ / au moins, plus de, dès / almeno,
  più di, oltre …) or an upper bound (höchstens, bis zu, unter, weniger als, ≤ / au plus, moins de, jusqu'à / al
  massimo, meno di, fino a …). A value both texts state with a direction, the same number of times, is a finding when
  the directions differ. ≥ against > is the same direction and is not a finding. Three kinds of bound get no direction
  or are left out: a range end (`15 bis 30 kg`), DE `über` before a duration (`über 6 Monate`), and a bound with a
  negation earlier in its clause (`n'ont pas reçu plus de deux`), because the languages place negations differently.
  One deviation from R15's wording: R15 said "a value bound to a unit". The check takes every value that carries an
  operator, because the dev planted flips sat on scores without a unit (`SCORAD >50`, `FeNO ≥ 50 ppb`).
- **`negation`.** German and target sentences are aligned by a monotone dynamic programme on length and shared digits.
  Only pairs with a cost of at most 0.4 are judged, or at most 0.2 when the sentence counts differ. A pair is a finding
  when one side has a clause negation (nicht, kein / ne, pas, aucun, non / non, nessuno) or a word negation from a
  narrow list (ohne, unzureichend, inakzeptabel, refraktär, `non-…`), and the other side has no negation of any kind.
  "No negation" also means no word negation (sans, insuffisant, absence, contre-indiqué), no exception or "below"
  word (sauf, inférieur à, meno di), and no negation idiom. Some negations do not count: FR `ne … que` (= nur);
  negations inside a bound (`nicht mehr als`, `n'excédant pas`, `non più di`, `non appena`); and expletive ones
  (`avant que … ne`, `finché … non`).
- **`number_word`.** Each aligned sentence pair is compared with the number check's own rules, with number words
  counted as bound (a number word is never a code, a year or a table cell). A value is a finding when it is written as
  a word on one side and the other sentence lacks it, or when it is the counterpart of such a word. Reconciled as before,
  plus: an ordinal word of the value; `beide` / `les deux` / `entrambi` for 2; `-fach` compounds; the Q1–Q5 equivalences;
  and values an existing number finding already names.
- **`counterpart`** (display only, on number findings). For each one-sided value, it gives the value the aligned
  sentence of the other side states in surplus with the same unit class. Nemluvio's `N18` now carries IT 4 for DE 8
  ("ogni quattro settimane"), so the register can show "IT 4" instead of "IT —". It fills 7 of the 21 number findings
  (`summary.round5.number_counterparts`). Nemluvio is a held-half case and was looked at for this field only.

The new kinds are reported apart, in `findings_r5` of `audit_20261006.json` and `summary.round5`.
`run_all(..., r5=False)` is the default. With it, the 38 existing findings, their ids, ranks and values are byte for
byte what they were, apart from the added `counterpart` field (a test checks it). `audit_item(x, kinds=KINDS_ALL +
KINDS_R5)` returns the new kinds on request.

**Planted recall, held half** (`python3 tools/audit_inject.py --protocol r15 --half held`, seed 20261016, 100 copies
per type and language, eligible: held-half text triples with no finding of any kind; `eval/results/audit_injection_r15_held.json`).
Before = the same copies with the pre-round-5 kinds and the v2 rule; after = with round 5.

| planted fault | n | before | after (Wilson 95%) | R15 bar | dev half (design) |
|---|---|---|---|---|---|
| operator flipped | 200 | 0.0% | **74.5%** [68.0, 80.0] | ≥ 60% | 73.5% |
| negation dropped | 200 | 0.0% | **44.0%** [37.3, 50.9] | ≥ 50% | 48.0% |
| negation added | 200 | 0.0% | **55.5%** [48.6, 62.2] | ≥ 50% | 51.0% |
| number word changed | 200 | 30.5% | **84.0%** [78.3, 88.4] | ≥ 60% | 87.0% |

The `negation_add` injector is new in R15. It turns a finite verb near a number into its negation (`est` → `n'est
pas`, `è` → `non è`). The other three are the v2 injectors (number word v2: 37.0% on both halves). In 8 copies re-run
as full-register audits, the findings were identical and nothing was new or lost elsewhere.

**Register findings and precision.** On the 6 Oct 2026 register the frozen rules report 31 findings on 27 limitations:
4 operator, 18 negation and 9 number_word. Two fresh blind Claude annotators labelled all 31 (`eval/labels/audit_r15_20261006.tsv`,
the second in reverse order; the question was R15's). They gave the same answer on all 31, so no tie-break was needed.

| kind | findings | real or minor (strict real) | precision [Wilson 95%] | R15 bar |
|---|---|---|---|---|
| operator | 4 | 1 (1) | 25.0% [4.6, 69.9] | ≥ 50% |
| negation | 18 | 4 (2) | 22.2% [9.0, 45.2] | ≥ 50% |
| number_word | 9 | 1 (0) | 11.1% [2.0, 43.5] | ≥ 50% |

**Outcome: no kind passes, all three stay off** (`R5_ON`, `summary.round5.on`). They are computed and reported, but
they are not in the default output and not in `--fail-on-findings`. Operator and number words meet the recall bar but
not the precision bar. Negation misses both (dropped 44.0%).

The real ones are new and worth a look:

- **AMVUTTRA.01a, French (`O01`).** The stop criteria say "augmentation du score NIS ≤ 10 points" where German and
  Italian say "> 10".
- **BEYONTTRA, Italian (`G03`), and VYNDAQEL.01b, Italian (`G17`).** Both say "on deve essere combinato" where the
  German has "darf nicht … kombiniert werden". The `non` lost its `n`, which turns a prohibition into an obligation.
- **Two minor.** ZAVICEFTA2 (FR "ampoules non utilisées" vs DE "verfallene Ampullen") and DECADURABOL2 (IT "inefficaci"
  vs DE "ausgeschöpft").

The false positives are paraphrases the lexicons do not pair. Examples: "nicht abgeschlossene Familienplanung" vs
"souhaite encore avoir des enfants" (×4); the NSCLC term "non à petites cellules"; FR "ne … que" written across a
comma; "das Fünffache" vs "cinque volte" (×3, the same multiplier worded differently); a list announced as "drei Therapien" in German only.

**What this means for the blind spots.** A "congruence checked" stamp still covers numbers bound to a unit, units,
languages, typos next to numbers and BAG's own terminology corrections. It does not cover operators, negations or
number words outside a unit: these checks exist and find planted faults, but on the real register three in four of
what they flag is a paraphrase. Two cheap next steps:

- A negation lexicon paired across the three languages, mined from the aligned register as round 4 mined terminology.
- Pairing multiplier wordings (`das Fünffache` = `cinque volte`).

Both would need their own pre-registered round.

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

- **What is still not checked.** A changed operator, a dropped or added negation and a number word outside a unit
  are checked by round 5 but off: it finds 44–84% of planted ones and 11–25% of its register findings are real
  (section "Round 5"). A German-only clause without numbers is not checked. A wrong drug class is found only where BAG has corrected the same wording elsewhere (terminology, round 4).
  The co-occurrence term-pair signal stays off (above).
- **Terminology.** It can only find wording that BAG has already corrected at least twice. The angiotensin case was the
  motivating example before the rule existed, and its pair comes from the item set (Jul 2025 → Feb 2026), not from the
  2026 snapshots. The 36 fresh-item notices are by construction. The German-term choice (T4, highest Dice) can pick a
  rare word that the instances happen to share: the "cassa malattia" pairs got `Angiologie` (3 texts), which is not the
  German for that phrase. Those pairs flag nothing on 6 Oct, but they would also miss real cases. One fix after the
  first run, an implementation bug against the stated rule: the "not a word of the target text" test now compares
  stems too. Before the fix the same pairs got `Inclisiran` (a product name). No flag changed and no threshold was
  touched (round-4 block sha256 `e00ba063…` after the fix).
- **likely_equivalent** is a triage hint written with three of the officer's examples in view. It is not a verdict: a
  conversion or an "adults" match can hide a real difference elsewhere in the same sentence.
- **Keytruda** was known before the language rule existed (round 3), and the angiotensin products before the terminology
  rule. Neither counts as an independent test of its rule.
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
  general. The planted-divergence measurement above is the independent estimate. It is still limited to fault shapes
  that we designed.
- **Number words.** Only 2–12 (frozen `NUMW`); round 5 (off) also compares them outside a unit. FR hyphenated numbers (`dix-huit`) are read as 10 and 8.
- **Duplicated boilerplate.** Three etanercept findings are one copied error, and so are E02/E03, T01–T04 and T05–T08.
  There are fewer independent errors than findings.
- **MiGeL/AL** were run once on the 1 Jul 2026 versions, with no dating and no labels. The `term_pairs()` statistics
  (off signal) are now deterministic (ties sorted); the FR count of ids with an exception moved from 483 to 484.
- **Found by a user, not by the audit** (BAG-officer test, Oct 2026; no rule was changed for them):
  - Inclusive and exclusive bounds count as the same direction: Dupixent `.05P` FR «supérieur à 60 kg» vs DE «ab 60 kg»
    treats a child of exactly 60 kg differently, and is not flagged.
  - The editorial check missed Amvuttra FR «après les 12 premiers de traitement» (the word «mois» is missing): a
    missing unit word after a number is not one of its rules.
- **No authority.** A finding says the languages differ or that a passage looks mistyped. Which version is right is for
  BAG to decide; it can be the German (see `odd_one_out`).
- **BAG as the referee (PREREG R20).** BAG's own later corrections score the audit: the 34 confirmed findings are frozen
  as predictions and the 35 unconfirmed ones as negative predictions (`eval/predictions/audit_20261006_predictions.json`,
  sha256 `09cd9df7bf3e…`), each later SL publication is checked with `tools/check_predictions.py check --fetch latest`,
  and nothing is claimed before the 6-month horizon (6 Apr 2027).
