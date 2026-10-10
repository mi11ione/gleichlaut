# Termbase: BAG's house renderings, mined from the register (`gleichlaut.termbase`)

The checks decide whether a French or Italian draft carries the German change. They do not decide whether it uses the
words BAG's translators use. A BAG translator who read the drafts named terminology as the second problem: the same
"Krankenversicherer" came back as "assureur-maladie", "assurance-maladie", "caisse maladie" and "assureur maladie";
"Kostengutsprache" as "autorisation de facturation"; the Italian drafts wrote "assicurazione obbligatoria di malattia"
for the OKP. The blind labels say the same: most ready drafts that still need a fix need one insurance term
(`eval/results/m1_q4_k_m.json`, `ready_minor_terminology`).

The termbase answers "what does BAG write for this German term?" from BAG's own published texts. No model, no network,
Python standard library only. It produces two files and one advisory note:

- `data/termbase/termbase_20261006.json`: per German term and target language, the house rendering, its support (in
  limitations), its share, and the minority variants the register also uses, with counts;
- `data/termbase/gleichlaut_sl_termbase_20261006.tbx`: the same as TBX-Basic (TBX v3, ISO 30042:2019, DCA style) for a
  terminology tool;
- a low-priority advisory in the XLIFF units and on the review page when a draft departs from the house rendering.

```bash
gleichlaut termbase [--hist DIR] [--date YYYYMMDD] [--json OUT] [--tbx OUT]   # mine from a snapshot (about 75 s)
gleichlaut termbase --from data/termbase/termbase_20261006.json --tbx OUT      # TBX from the shipped JSON, no snapshot
```

`--hist` defaults to `$GLEICHLAUT_HIST`, then `out/hist` (snapshots from `python -m gleichlaut.sl.ingest`). The
snapshot files are not in the repository: `data/audit/audit_texts_20261006.json` holds only the 27 limitations with an
audit finding, so mining needs the 6 Oct 2026 snapshot. The mined JSON is shipped, and the TBX is rebuilt from it
byte for byte.

## What it is mined from

The input is all 1,688 limitations of the 6 Oct 2026 public ePL feed. The German and each target text are aligned by
limitation id, as the audit aligns them (`audit.load`). A target field written in another language is skipped (the
audit's function-word vote). Each text pair is then cut into aligned sentence units, using the same Gale-Church
alignment the XLIFF writer uses (`emit.segment.align`). A rendering is therefore counted against the German sentence it
translates, not against boilerplate elsewhere in the same limitation. Counts are reported in limitations.

## Which German terms

There are 54 head terms (`termbase.HEADS`), chosen before mining. We listed the German content words (capitalised,
at least 7 letters) that occur in at least 20 distinct German limitation texts, sorted by document frequency. From that
list we kept the vocabulary of reimbursement and approval (Krankenversicherer, Kostengutsprache, Vertrauensarzt,
Indikationscode, Limitierung, Rückerstattung, Vergütung, Kostenübernahme, obligatorische Krankenpflegeversicherung,
Krankenkasse), pricing (Fabrikabgabepreis, Publikumspreis, Mehrwertsteuer, Preismodell, Rückvergütung,
Zulassungsinhaberin), prescribers and settings (Facharzt, Universitätsklinik, Poliklinik, Verschreibung, Verordnung,
Erstverschreibung), product status (Originalpräparat, Generikum, Referenzpräparat, Biosimilar, Fachinformation) and
lines and course of therapy (Monotherapie, Erstlinientherapie, Erhaltungstherapie, Therapiebeginn, Therapieabbruch, …).
We dropped drug, product and company names, diseases and anatomy, and general words (Behandlung, Patienten, Therapie,
Kombination). "Limitatio" occurs in only one German text and is not a head. Each head is a regex that covers its
inflected forms ("Vertrauensarztes", "Fachärztinnen", "obligatorischen Krankenpflegeversicherung").

## How a rendering is chosen

The renderings come from the data; none is written by hand. The rules are in the module docstring (M1–M8):

1. **Candidates.** Target n-grams of 1–6 tokens. They do not start or end with a function word. They do not span
   punctuation, a coordination ("et", "ou", "e", "o") or a finite, modal or auxiliary verb. Each must occur in at least
   10 limitations whose German has the term. Hyphen compounds stay whole, so "assureur-maladie" and "assureur maladie"
   are different renderings. Elided articles are split off.
2. **Association.** The occurrence-level Dice between the term in the German unit and the n-gram in the target unit.
3. **Exclusive evidence.** A rendering is kept only if the term is its strongest German associate. "consultation"
   belongs to "Konsultation", not to "Vertrauensarzt"; "richiesta di rimborso" belongs to the reimbursement sentence,
   not to "Mehrwertsteuer".
4. **Phrase.** The head is the best-associated candidate (shorter first on ties). It grows to the longest candidate
   that contains it and keeps at least 60% of its occurrences, so "prise en charge" becomes "garantie de prise en
   charge".
5. **Competing terms.** A second pass drops a candidate that contains another head's house rendering in sentences where
   that other term is in the German. Without it, "altro biosimilare" would become the rendering of "Referenzpräparat".
6. **House rendering.** A rendering is the house rendering if it occurs in at least 10 limitations and in more than half
   of the limitations whose German contains the term. Otherwise the entry says "no dominant rendering" and is neither
   exported nor used.
7. **Variants.** The same selection runs on the limitations that have the term but not the house rendering, up to 5
   variants. A variant must cover at least 2 limitations, be at least 5 times more frequent there than in limitations
   without the term, and contain no word of the German (names, INNs). Inflection-only variants are dropped
   ("spécialiste" next to "spécialistes").

## What it found (6 Oct 2026)

The mining produced 76 house renderings (40 French, 36 Italian) for the 54 heads, plus 13 recorded variants. A review
of that output (`termbase.REJECT`, `DROP_VARIANTS`; read by the team's coding agent against the register, not by a
linguist) set aside 11 renderings that are fragments of the real term (« début » for Therapiebeginn, « standard »,
« lignes », « cellules souches » …) and 4 variants that are not renderings of the term. They stay in the JSON with the
reason and are neither exported nor used. What ships: **65 house renderings (32 French, 33 Italian) and 9 variants**.
Re-mining reproduces the files byte for byte. A selection, with support / limitations whose German has the term:

| German | French (share) | Italian (share) |
|---|---|---|
| Krankenversicherer | assureur-maladie 505/890 (57%); variant assurance maladie 266 | assicuratore 522/889 (59%); variants assicurazione malattia 282, assicurazione malattie 97 |
| Kostengutsprache | garantie de prise en charge 374/611 (61%) | garanzia di assunzione dei costi 364/611 (60%); variant garanzia di assunzione delle spese 91 |
| Vertrauensarzt | médecin-conseil 522/581 (90%) | medico di fiducia 519/581 (89%) |
| obligatorische Krankenpflegeversicherung | assurance obligatoire des soins 33/41 (80%) | assicurazione obbligatoria delle cure medico-sanitarie 34/41 (83%) |
| Indikationscode | code d'indication 262/345 (76%) | codice di indicazione 182/345 (53%); variant codice d'indicazione 99 |
| Zulassungsinhaberin | titulaire de l'autorisation 134/138 (97%) | titolare dell'omologazione 97/138 (70%); variant titolare dell'autorizzazione 42 |
| Fabrikabgabepreis | prix de fabrique 159/249 (64%) | prezzo di fabbrica 205/249 (82%) |
| Mehrwertsteuer | taxe sur la valeur ajoutée 152/248 (61%) | no dominant rendering ("IVA" and "imposta sul valore aggiunto" split) |
| Poliklinik | policliniques 63/103 (61%); variant polycliniques 35 | policlinici 85/103 (82%) |

The register itself is not uniform. For "Krankenversicherer", BAG writes "assureur-maladie" in 57% of the French texts
and "assurance maladie" in 266 limitations. The translator's complaint is partly a complaint about the register. The
termbase makes that split visible with counts and does not pretend to a uniformity that is not there.

**Entries that look wrong or incomplete** (unreviewed; check before adopting):

- Fragments, where the full phrase varies too much to keep 60% of its occurrences: FR Originalpräparat "originale"
  (BAG also writes "préparation originale"), FR Therapiebeginn "début", FR Zweitlinientherapie "traitement de deuxième"
  ("ligne" / "intention" split), FR Universitätsklinik "universitaires", FR/IT Therapielinie "lignes" / "linee",
  FR/IT Standardtherapie "standard", IT Krankenversicherer "assicuratore" ("malattia" / "malattie" split).
- Variants that are not renderings of the term: FR Mehrwertsteuer "récupérée", "réclamée" (the verb next to it);
  IT Erstlinienbehandlung "linea di pazienti adulti".
- Rückerstattung and Vergütungskriterien both lead to "remboursement" / "rimborso". This is correct many-to-one,
  but it is not a distinction a translator can act on.

Twenty-two of the 108 term-by-language entries have no candidate that passes the exclusive-evidence test (Vergütung,
Verschreibung, Kombinationstherapie, Kostenübernahme, …). Ten more fall short of a majority. Neither group is exported.

## The advisory

When a draft's new German contains a term with a house rendering, the reviewer gets one note in their own language if
either of these holds:

- the draft introduces a recorded minority variant, that is, it has more occurrences of it than the old target text;
- the draft writes the house rendering (inflection-tolerant) fewer times than the German has the term, and the old text
  did not fall short in the same way. The gap is then the draft's, not the old text's.

> FR: Terme maison pour « obligatorische Krankenpflegeversicherung » : « assurance obligatoire des soins » (33
> limitations) ; le brouillon écrit « assurance obligatoire de maladie ».
> IT: Termine in uso all'UFSP per «obligatorische Krankenpflegeversicherung»: «assicurazione obbligatoria delle cure
> medico-sanitarie» (34 limitazioni); la bozza scrive «assicurazione obbligatoria di malattia».

When the note does not name a variant, it shows the draft's closest wording that is new in the draft (character
similarity ≥ 0.6), or says "absent du brouillon" / "assente dalla bozza". In XLIFF 2.1 it is its own `<note
category="gleichlaut:termbase" priority="9">`; XLIFF 1.2 carries the same note with priority 9. On the review page it
is a grey line under the explanation. It is never one of the three reasons, never changes ready or flagged, the draft
or any score. A draft with no house-rendering issue gets no note. The guards and every committed result are unchanged.

## Measured on the fresh 166 (`eval/results/termbase.json`)

`termbase.measure()` runs in `make run` (`replay.compute`) and is checked against the committed file. "Explained"
means the advisory fires on the draft. "Agrees with BAG" means BAG's own published text of the same amendment
(evaluation data, never shown) contains the house rendering. Labels are the blind annotations already used for these
runs: majority of three for the 70B, `m1_<build>_fresh166.tsv` for the 8B builds.

| | 70B | 8B Q4_K_M | 8B Q8_0 |
|---|---|---|---|
| Ready drafts | 66 | 60 | 62 |
| Ready drafts with an advisory | 1 | 29 | 22 |
| Ready drafts labelled "needs a fix" / with an advisory | 3 / 1 | 33 / 27 | 25 / 22 |
| Labelled minor (one term) / explained by the advisory | 1 / 1 | 29 / 27 | 23 / 22 |
| Advisories on ready drafts where BAG's text has the house rendering | 1 of 1 | 28 of 29 | 22 of 22 |
| Advisories on ready drafts labelled "no fix needed" | 0 | 2 | 0 |
| Flagged drafts with an advisory | 17 of 100 | 37 of 106 | 31 of 104 |

On the 8B builds the advisory accounts for nearly all of the "ready but needs a fix" drafts. Almost all of them are
one German term, the OKP: "obligatorische Krankenpflegeversicherung", which the 8B renders "assurance obligatoire de
maladie" or "assicurazione obbligatoria di malattia". Not explained: wb084-fr/-it ("un SGLT-2 inhibiteur", a calque, not
a head term) and wb087-it (an elision error). The 70B's one minor case, wb032-it, is the same OKP term. The two
Q4_K_M advisories on drafts labelled "no fix" are wb032-fr ("assurance maladie obligatoire"; one of the three
annotators called it a non-standard insurance term, the majority did not) and wb088-it (BAG's own
text keeps "assicurazione malattia", the minority variant; this is the one disagreement with BAG). Flagged drafts get
advisories more often because they already depart from the old text more: German left in the draft, rewritten
sentences.

## Caveats

- **The termbase reflects what BAG publishes, not what BAG's terminologists prescribe.** Where the register is split
  (Krankenversicherer at 57%), the "house" rendering is a majority, not a rule. An admitted variant may be the newer
  preferred term (IT "titolare dell'omologazione" against "…dell'autorizzazione").
- **Precision is measured only for the terms that fired.** Almost all advisories are about the OKP. For the other heads,
  the entries are spot-checked (list above), not labelled. Fragments such as "standard" or "début" can fire on a draft
  that writes the phrase differently but correctly. That is one reason the note is advisory and low priority.
- **The co-occurrence statistics cannot separate terms that always occur together in the same sentence.** The
  second-pass rule handles the cases seen here, not every case.
- **TBX.** The file is TBX-Basic in TBX v3 core structure (namespace `urn:iso:std:iso:30042:ed-2`, `type="TBX-Basic"`,
  `style="dca"`). `termbase.validate_tbx` checks well-formedness and the structure used (header, conceptEntry ids,
  langSec / termSec order, one preferred term per target language, administrativeStatus values). It does not check
  against the official RNG/Schematron, which needs a network fetch. TermStar NXT and other STAR tools import TBX; whether
  a given installation reads TBX v3 or expects the 2008 `martif` dialect is unverified. The ePL / STAR team would test
  one import before adopting it.
- **Monthly update.** Re-mining a new snapshot takes about 75 s (`gleichlaut termbase --date YYYYMMDD`). The advisory
  reads `data/termbase/termbase_20261006.json`.
