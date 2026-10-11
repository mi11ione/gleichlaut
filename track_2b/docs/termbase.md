# Termbase: BAG's house renderings, mined from the register (`gleichlaut.termbase`)

The checks decide whether a French or Italian draft carries the German change. They do not decide whether it uses the
words BAG's translators use. A BAG translator who read the drafts named terminology as the second problem: the same
"Krankenversicherer" came back as "assureur-maladie", "assurance-maladie", "caisse maladie" and "assureur maladie";
"Kostengutsprache" as "autorisation de facturation"; the Italian drafts wrote "assicurazione obbligatoria di malattia"
for the OKP. The blind labels say the same: most ready drafts that still need a fix need one insurance term
(`eval/results/m1_q4_k_m.json`, `ready_minor_terminology`).

The termbase answers "what does BAG write for this German term?" from BAG's own published texts. No model, no network,
Python standard library only. It produces four files and two advisory notes:

- `data/termbase/termbase_20261006.json`: per German term and target language, the house rendering, its support (in
  limitations), its share, and the minority variants the register also uses, with counts;
- `data/termbase/gleichlaut_sl_termbase_20261006.tbx`: the same as TBX-Basic (TBX v3, ISO 30042:2019, DCA style) for a
  terminology tool;
- `data/termbase/house_sentences_20261006.json`: BAG's dominant wording of frequent fixed German sentences (the closing
  code formula and its kin), mined the same way ([House sentences](#house-sentences));
- `data/termbase/shared_words_20261006.json`: the words the German and a target register share ("allergie"), used to
  word an "untranslated German" finding on such a word as probably fine;
- a low-priority advisory in the XLIFF units and on the review page when a draft departs from the house rendering, and
  one when a sentence the draft wrote departs from a house sentence.

```bash
gleichlaut termbase [--hist DIR] [--date YYYYMMDD] [--json OUT] [--tbx OUT] [--house OUT]   # mine from a snapshot (about 2 min)
gleichlaut termbase --from data/termbase/termbase_20261006.json --tbx OUT                   # TBX from the shipped JSON, no snapshot
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
translates, not against boilerplate elsewhere in the same limitation. Counts are reported in limitations. Since 10 Oct
2026 the sentence splitter does not end a sentence at the full stop of an abbreviation ("I.T. 02.06", "z.B.", "ca. 6",
"Nr.", "resp.", "u.a.", "p. ex."); re-mining with it moved a few counts by one or two limitations (IT Kostengutsprache
364 → 365) and changed no rendering.

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
reason and are neither exported nor used. A BAG Italian translator's review (11 Oct 2026, [below](#fourth-review-11-oct-2026-italian-translator))
set aside one more, IT Krankenversicherer, and moved three terms to their base form; a BAG French translator's review
(11 Oct 2026, [below](#fifth-review-11-oct-2026-french-translator)) removed two French variants that are not renderings
of the term and added a usage note. What ships: **64 house renderings (32 French, 32 Italian) and 5 variants**. Re-mining reproduces the files byte for byte. A selection, with support /
limitations whose German has the term:

| German | French (share) | Italian (share) |
|---|---|---|
| Krankenversicherer | assureur-maladie 505/890 (57%); BAG also writes « assurance maladie » (the insurance) in 266, not an admitted term | no dominant rendering (head «assicuratore» 522/889 is a fragment; «assicuratore malattie» 312, «assicurazione malattia» 288, «assicuratore malattia» 160) |
| Kostengutsprache | garantie de prise en charge 374/611 (61%) | garanzia di assunzione dei costi 365/611 (60%); variant garanzia di assunzione delle spese 91 |
| Vertrauensarzt | médecin-conseil 522/581 (90%) | medico di fiducia 519/581 (89%) |
| obligatorische Krankenpflegeversicherung | assurance obligatoire des soins 33/41 (80%) | assicurazione obbligatoria delle cure medico-sanitarie 34/41 (83%) |
| Indikationscode | code d'indication 262/345 (76%) | codice di indicazione 182/345 (53%); variant codice d'indicazione 99 |
| Zulassungsinhaberin | titulaire de l'autorisation 134/138 (97%) | titolare dell'omologazione 97/138 (70%); variant titolare dell'autorizzazione 42 |
| Fabrikabgabepreis | prix de fabrique 159/249 (64%) | prezzo di fabbrica 205/249 (82%; «prezzo di fabbrica per la consegna» in 17) |
| Mehrwertsteuer | taxe sur la valeur ajoutée 152/248 (61%) | no dominant rendering ("IVA" and "imposta sul valore aggiunto" split) |
| Poliklinik | policlinique 63/103 (61%; the register writes «policliniques»); variant polyclinique 35 | policlinico 85/103 (82%; the register writes «policlinici») |

The register itself is not uniform. For "Krankenversicherer", BAG writes "assureur-maladie" in 57% of the French texts
and "assurance maladie" in 266 limitations. The translator's complaint is partly a complaint about the register. The
termbase makes that split visible with counts and does not pretend to a uniformity that is not there.

**Entries that look wrong or incomplete** (unreviewed; check before adopting):

- Fragments, where the full phrase varies too much to keep 60% of its occurrences: FR Originalpräparat "originale"
  (BAG also writes "préparation originale"), FR Therapiebeginn "début", FR Zweitlinientherapie "traitement de deuxième"
  ("ligne" / "intention" split), FR Universitätsklinik "universitaires", FR/IT Therapielinie "lignes" / "linee",
  FR/IT Standardtherapie "standard".
- Variants that are not renderings of the term: FR Mehrwertsteuer "récupérée", "réclamée" (the verb next to it);
  IT Erstlinienbehandlung "linea di pazienti adulti".
- Rückerstattung and Vergütungskriterien both lead to "remboursement" / "rimborso". This is correct many-to-one,
  but it is not a distinction a translator can act on.

Twenty-two of the 108 term-by-language entries have no candidate that passes the exclusive-evidence test (Vergütung,
Verschreibung, Kombinationstherapie, Kostenübernahme, …). Ten more fall short of a majority. Neither group is exported.

Two terms a translator asked for are not heads, and the mining cannot support them: "Leistungserbringer" is in 14
German limitation texts and "Kostengutsprachegesuch" in 12, below the 20 of the head list. Mined anyway with the same
rules (10 Oct 2026, 6 Oct snapshot), neither yields a house rendering: no French candidate passes M2–M4 for either, nor
an Italian one for "Kostengutsprachegesuch"; Italian "fornitore di prestazioni" covers 8 of the 14 "Leistungserbringer"
limitations, under the minimum support of 10. Adding them leaves every other entry unchanged. They are not in the
termbase.

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
similarity ≥ 0.6). When the draft does write the house rendering, only fewer times than the German has the term, it says
so ("le brouillon l'écrit 1 fois, l'allemand a le terme 2 fois"); only a draft without it gets "absent du brouillon" /
"assente dalla bozza".

Recorded variants are matched spelling-tolerantly: "assurance-maladie" is BAG's recorded practice "assurance maladie" (266
limitations; since the fifth review not an admitted term, but still BAG's practice for the advisory).

When the old text already fell short of the house rendering, where the non-standard wording sits decides the note:

- **In text the draft wrote** (a sentence it inserted, or an edited sentence whose old version did not have the
  wording): a normal note, "le brouillon écrit …". That holds for a recorded variant too ("assurance-maladie" in a
  closing code sentence the draft wrote) and for a wording the register does not record ("caisse maladie", wb004-fr).
- **Carried over** (a sentence of the old text, unchanged, or an edited version of one that already had the wording:
  word similarity ≥ 0.5): a softer note, "le texte (déjà avant) écrit …", only for a spelling variant of the house
  rendering ("assureur maladie", "médecin conseil") or a wording at least 0.7 similar to it that the register does not
  record. A recorded variant carried over gets no note: that is BAG's own practice, and BAG's own amendments keep it
  (wb040-fr and wb072-it, drafts identical to BAG's published text, stay without a note).

> FR: Terme maison pour « Krankenversicherer » : « assureur-maladie » (505 limitations) ; le brouillon écrit
> « caisse maladie ».

The measurement below covers the first two kinds only (`termbase.measure()`); the softer note is counted in
`eval/results/explain_v2.json` (`emit.explain.measure_v2()`), the notes on text the draft wrote in
`eval/results/explain_v3.json` (`emit.explain.measure_v3()`). A termbase note on a wording inside a sentence the
house-sentence note already names is left out (the house note shows the whole formula). In XLIFF 2.1 the advisory is its own `<note
category="gleichlaut:termbase" priority="9">`; XLIFF 1.2 carries the same note with priority 9. On the review page it
is part of the grey line under the explanation. It is never one of the three reasons, never changes ready or flagged, the draft
or any score. A draft with no house-rendering issue gets no note. The guards and every committed result are unchanged.

## Measured on the fresh 166 (`eval/results/termbase.json`)

`termbase.measure()` runs in `make run` (`replay.compute`) and is checked against the committed file. "Explained"
means the advisory fires on the draft. "Agrees with BAG" means BAG's own published text of the same amendment
(evaluation data, never shown) contains the house rendering. Labels are the blind annotations already used for these
runs: majority of three for the 70B, `m1_<build>_fresh166.tsv` for the 8B builds.

| | 70B | 8B Q4_K_M | 8B Q8_0 |
|---|---|---|---|
| Ready drafts | 66 | 60 | 62 |
| Ready drafts with an advisory | 1 | 28 | 22 |
| Ready drafts labelled "needs a fix" / with an advisory | 3 / 1 | 33 / 27 | 25 / 22 |
| Labelled minor (one term) / explained by the advisory | 1 / 1 | 29 / 27 | 23 / 22 |
| Advisories on ready drafts where BAG's text has the house rendering | 1 of 1 | 28 of 28 | 22 of 22 |
| Advisories on ready drafts labelled "no fix needed" | 0 | 1 | 0 |
| Flagged drafts with an advisory | 18 of 100 | 38 of 106 | 31 of 104 |

On the 8B builds the advisory accounts for nearly all of the "ready but needs a fix" drafts. Almost all of them are
one German term, the OKP: "obligatorische Krankenpflegeversicherung", which the 8B renders "assurance obligatoire de
maladie" or "assicurazione obbligatoria di malattia". Not explained: wb084-fr/-it ("un SGLT-2 inhibiteur", a calque, not
a head term) and wb087-it (an elision error). The 70B's one minor case, wb032-it, is the same OKP term. The two
Q4_K_M advisory on a draft labelled "no fix" is wb032-fr ("assurance maladie obligatoire"; one of the three
annotators called it a non-standard insurance term, the majority did not). (Until 11 Oct 2026 there was a second,
wb088-it, where BAG's own text keeps "assicurazione malattia": the one disagreement with BAG, gone with the Italian
Krankenversicherer entry; see the fourth review.) Flagged drafts get
advisories more often because they already depart from the old text more: German left in the draft, rewritten
sentences. (Before the third review: 17, 37 and 31 flagged drafts. The ready-draft rows did not change: the 4 / 2 / 3 more
flagged drafts are wordings in text the draft wrote, such as "caisse maladie" or "assicurazione malattia" in a
code sentence the draft added.)

## House sentences

The same translator's third review named the fixed sentences: "Folgender Code ist an den Krankenversicherer zu
übermitteln:", its newer "Der Indikationscode dieser Limitierung ist an den Krankenversicherer zu übermitteln." and other
boilerplate have a published French and Italian wording, and the drafts write them otherwise. `gleichlaut.house` mines
those wordings from the same snapshot with the same method (module docstring, S1–S5); no wording is written by hand:

1. **Units.** The aligned sentence beads of `emit.segment.align`; the German side is the German sentence.
2. **Normalisation.** Numbers and codes become `#` (21150.07, 20481.XX), whitespace and typographic apostrophes are
   folded, spaces before `: ; ! ? »` and after `«` are dropped. A German sentence needs three words of two letters or
   more (a lone code number is not one).
3. **Support.** A German sentence in at least 10 limitations is recorded with every rendering, counted in limitations.
4. **House wording.** The most frequent rendering, when it is in at least 10 limitations and in more than half of the
   limitations with that German sentence (the termbase's rule); otherwise "no dominant rendering", not used.
5. **Variants.** The other renderings in at least 2 limitations, up to 5, with counts.

On the 6 Oct 2026 feed: 125 German sentences are in at least 10 limitations (67 French entries, 58 Italian), and **64
have a house wording (37 French, 27 Italian)**. The rest are split. Selected:

| German sentence | French | Italian |
|---|---|---|
| Folgender Code ist an den Krankenversicherer zu übermitteln: | no dominant wording: "…à l'assurance maladie:" 109, "…à l'assureur-maladie:" 109, "…à l'assurance-maladie:" 52, "…à l'assureur:" 10 of 295 | no dominant wording (80, 53, 35 … of 292) |
| Folgender Indikationscode ist an den Krankenversicherer zu übermitteln: | « Le code d'indication suivant doit être transmis à l'assureur-maladie: » 111/167 | no dominant wording (75 of 168) |
| Der Indikationscode dieser Limitierung ist an den Krankenversicherer zu übermitteln. | « Le code d'indication de cette limitation doit être transmis à l'assureur-maladie. » 36/53 | «Il codice di indicazione di questa limitazione deve essere trasmesso all'assicuratore malattie.» 45/55 |
| Folgender Indikationscode ist zu übermitteln: | « Le code d'indication suivant doit être transmis: » 27/43 | «Il seguente codice di indicazione deve essere trasmesso:» 26/43 |
| Nur bis zur Progression der Krankheit. | « Seulement jusqu'à progression de la maladie. » 35/69 | «Solo fino alla progressione della malattia.» 35/69 |

The classic closing formula has **no** house wording in either language: BAG's own French splits evenly between
"assurance maladie" and "assureur-maladie". The register cannot settle it; a terminologist can. For that sentence the
termbase note still applies to text the draft wrote ("assurance-maladie" where the termbase has "assureur-maladie").

**The note.** When a sentence of the draft, aligned to a German house sentence, is recognisably the same formula
(character similarity ≥ 0.6 after normalisation) but not the house wording, the reviewer gets one low-priority note
(`<note category="gleichlaut:house" priority="9">`, XLIFF 1.2 priority 9; on the review page in the grey line under the
explanation). A long sentence is shown as the part that differs, with two words on each side; a recorded variant says
how often BAG published it:

> FR: Phrase maison pour « Folgender Indikationscode ist an den Krankenversicherer zu übermitteln: » : « Le code
> d'indication suivant doit être transmis à l'assureur-maladie: » (111 limitations) ; le brouillon écrit « Le code
> d'indication suivant doit être communiqué à l'assureur-maladie : ».

Only sentences the draft wrote get a note. A sentence carried over unchanged from the old text is left alone: the German
did not change it, the checks keep edits inside the change, and BAG's own amendments leave such sentences as they are
(below: BAG's published text kept the old wording at every carried-over sentence of the fresh 166). A German sentence
the draft does not translate at all is the change-applied check's business, not this note's. The note never changes ready
or flagged, a draft or a score. Not in the TBX: a sentence with a number slot is translation-memory material, not a term.

**Measured** (`eval/results/explain_v3.json`, `house`). "BAG differs" means BAG's published text of the same amendment,
at the same German sentence, is not the draft's sentence (evaluation data, never shown):

| | 70B | 8B Q4_K_M | 8B Q8_0 | shadow 70B | shadow Q4_K_M | shadow Q8_0 |
|---|---|---|---|---|---|---|
| Drafts (not routed to a translator) | 166 | 166 | 166 | 44 | 44 | 44 |
| Drafts with a house-sentence note (ready) | 13 (0) | 13 (0) | 14 (0) | 28 (2) | 19 (2) | 22 (1) |
| Notes | 14 | 13 | 14 | 29 | 19 | 22 |
| … BAG differs from the draft there | 14 | 13 | 14 | 26 (3 not aligned) | 19 | 22 |
| … BAG writes the house wording there | 12 | 11 | 10 | 22 | 16 | 16 |
| Departing sentences carried over, no note / BAG kept them too | 12 / 12 | 10 / 10 | 10 / 10 | 9 / 4 | 11 / 3 | 8 / 3 |

On the fresh 166 every note points at a sentence where BAG's own text differs from the draft's, and in most of them BAG
wrote the house wording. In the shadow month the notes are mostly the newer code sentence, which the 8B drafts write with
German left in it ("Der Indikationscode de cette limitation …") or with "assurance-maladie" / "cassa malati".

## Third review: what else changed in the notes

Presentation only; verdicts, drafts and scores are unchanged. Before / after on the fresh 166 (70B, Q4_K_M, Q8_0) from
`eval/results/explain_v3.json`:

- **Internal codes out of translator notes.** The checks note used to end with the raw guard output ("Slots: neg DE
  5->4", "G3c", "[T7]"): 100 / 106 / 104 units carried codes in a translator note, now 0. The raw output is one note
  `category="gleichlaut:debug" priority="10"` (XLIFF 1.2 `from="gleichlaut-debug"`); the checks note keeps the remaining
  reasons in plain words.
- **Header equals the list.** "3 issues to check, 2 probably fine" was counted from the triage rules while the list
  showed the reworded reasons; it differed on 33 / 21 / 25 flagged drafts (Q4_K_M 20 before round 13, when the German word-order
  note became a reason to check). It is now counted from the list
  (`xliff.counts`), and the register's ▲ / ~ mark follows it: on the 70B register 49 flagged drafts to check and 51
  with every item probably fine (60 / 40 by the triage rules alone).
- **Deletions that follow the German one to one** (the German drops a sentence, the draft drops the sentence that
  translates it, wb008) are stated, not asked: "Suppression conforme à l'allemand : l'allemand retire la phrase « … » ;
  le brouillon retire la phrase correspondante « … »." 15 / 8 / 15 notes; 3 / 9 / 8 partial ones stay questions. wb008
  was not a detection bug: the mirror was found, only the wording was always a question.
- **Repetitions the German has too** ("ou d'une perte de vision" twice where the German says "eines Visusverlustes"
  twice): low priority, "l'allemand le répète aussi". 14 of 16 / 2 of 6 / 3 of 9 repetition findings.
- **German-looking target words** ("allergie", "teclistamab"): when the old text has the word or the German and target
  registers share it (`shared_words`), an "untranslated German" finding says "probablement sans problème" for those
  words. All words: 1 / 1 / 1 finding; some words: 4 / 11 / 10. The check itself is unchanged.
- **Hedged wording.** A sentence the German adds with nothing in the draft for it: "elle manque dans le brouillon"
  (7 / 8 / 9 of 10 / 13 / 13 hedged sentences); left in German: "le brouillon la laisse en allemand" (0 / 2 / 0); a
  sentence the German removes that the draft keeps: named (2 / 9 / 8). The rest stays "vérifier qu'elle est traduite".
- **Segments.** "I.T. 02.06", "z.B.", "ca. 6" no longer split a segment.

## Fourth review (11 Oct 2026, Italian translator)

A BAG Italian translator read the termbase and the register. The mining rules are unchanged; three review entries
(`termbase.REJECT`, `DROP_VARIANTS`, `LEMMA`) and a subject field were added, and the files re-mined from the 6 Oct
snapshot:

- **IT Krankenversicherer.** The translator: BAG writes «assicuratore malattie»; the head «assicuratore» is truncated,
  and «assicurazione malattia» is the insurance, not the insurer. The register (889 Italian limitations whose German has
  the term): «assicuratore malattie» 312, «assicurazione malattia» 288, «assicuratore malattia» 160,
  «assicuratore-malattie» 19. No full phrase is a majority, so by the rule for a house rendering (M6: more than half)
  there is none; the bare head is set aside as a fragment, like « début » or « standard », and the two «assicurazione»
  variants are dropped as not renderings of the term. The Italian insurer note no longer fires. French
  « assurance maladie » stayed a recorded variant then (BAG publishes it in 266 limitations); the fifth review removed it.
- **Poliklinik, Facharzt.** A termbase lists the base form: «policlinico» (the register writes «policlinici»),
  « policlinique » / variant « polyclinique », « spécialiste ». Only the shown form changed (`register_form` keeps the
  mined one); matching is inflection-tolerant and its counts are the mined ones.
- **IT Fabrikabgabepreis.** The translator proposed «prezzo di fabbrica per la consegna». The register writes it in 17
  of the 249 limitations; «prezzo di fabbrica» alone in 205 (82%). The rule keeps «prezzo di fabbrica».
- **TBX subject field.** Each concept carries `<descrip type="subjectField">` (reimbursement, pricing, prescription and
  setting, product status, therapy and clinical course: the groups the heads were picked from), which TermStar maps to
  its subject field. No definitions: they would be written by hand, and the termbase writes nothing by hand.

Numbers that changed: 65 → **64** house renderings (Italian 33 → 32), 9 → 7 variants; 8B Q4_K_M ready drafts with an
advisory 29 → 28 (wb088-it, the one advisory where BAG's text differed, is gone: 28 of 28 now agree with BAG); flagged
drafts with an advisory 21 / 39 / 34 → 18 / 38 / 31. Unchanged: the 22 of the 25 Q8_0 "ready but needs a fix" drafts
the advisory names, and 27 of the 33 for Q4_K_M.

## Fifth review (11 Oct 2026, French translator)

A BAG French translator read the termbase and the TBX (round 13). The mining rules are unchanged; three review entries
(`termbase.DROP_VARIANTS`, `PRACTICE`, `USAGE`) were added and the files re-mined from the 6 Oct snapshot:

- **FR Krankenversicherer.** « assurance maladie » is the insurance, not the insurer (as Italian «assicurazione
  malattia» in the fourth review). It is no longer an admitted term: not a variant in the JSON, not an `admittedTerm` in
  the TBX. BAG still publishes it in 266 of the 890 French limitations whose German has the term, so the entry keeps it
  as `practice` and the advisory treats it as before: a draft that introduces it, or writes it in a sentence of its own,
  gets the note; a sentence carried over unchanged from BAG's text does not. The house rendering stays
  « assureur-maladie » (505 of 890, 57%).
- **FR Mehrwertsteuer.** « remboursement de la TVA » (34 limitations) is the VAT refund, not the VAT: dropped as a
  variant. The house rendering stays « taxe sur la valeur ajoutée » (152 of 248).
- **Verordnung → « prescription » / «prescrizione».** The German word is also the ordinance (« ordonnance », OAMal).
  In the register it never is: all 125 limitations with the word mean the medical prescription ("ärztliche Verordnung",
  "die Verordnung von …", "nach Verordnung durch einen Facharzt"). The entry now carries a usage note in each language of
  the TBX (`<note>`: prescription, not ordinance) and the head regex leaves out a legal ordinance ("Verordnung über …",
  "Verordnung des EDI", "Verordnung vom …"), so a German text citing the KVV gets no « prescription » note. Neither
  changes a count on this register.
- **FR Originalpräparat → « préparation originale ».** Added only if the mining rule yields it. It does not: all 64
  French limitations write « la préparation originale », but the rendering is the head « originale » extended only
  through words that pass the exclusive-evidence test (M5 with M4), and « préparation » is more strongly associated
  with another German word ("nötig") than with "Originalpräparat". The entry stays set aside as a fragment (house=false,
  not exported); adding the phrase by hand would break "nothing written by hand".
- **TBX in the language of each element.** The notes and sources in a French or Italian `langSec` were English ("505 of
  890 limitations whose German contains the term"). They are now in the langSec's language (« 505 des 890 limitations
  dont l'allemand contient le terme (57 %) », «505 delle 890 limitazioni il cui tedesco contiene il termine (57%)»); the
  header, the subject field and the German langSec are in German, the file's `xml:lang`.

Numbers that changed: 7 → **5** variants (French 3 → 1). Unchanged: the 64 house renderings and every count in
`eval/results/termbase.json` other than the French variant count, and every termbase count in `explain_v2.json` and
`explain_v3.json` (the advisory fires on the same drafts with the same text).

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
- **Monthly update.** Re-mining a new snapshot takes about 2 minutes (`gleichlaut termbase --date YYYYMMDD`; termbase,
  house sentences and shared words). The advisories read the shipped `data/termbase/*_20261006.json`.
- **House sentences are a majority, not a style guide.** A wording used in 51% of 53 limitations is "house"; BAG's
  language service may prefer the minority. Product-family sentences (the statin boilerplate in 24 limitations) count
  like formulas. A note fires only on a sentence the draft wrote and only when it is recognisably the same formula.
