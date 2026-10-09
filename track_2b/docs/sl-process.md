# Who writes the FR/IT limitation texts of the SL, and where a drafting tool fits

Jurors asked who writes the French and Italian limitation texts of the Spezialitätenliste (SL) today, in which workflow and
tool, and where a drafting tool would plug in. This note answers from public sources only.

**Method.** All sources were retrieved on 2026-10-09 with `curl` (User-Agent `hackapertus-research/0.1`) and searched with a
web search engine. No model APIs were used. PDFs were converted with `pdftotext -layout`. In quotes from PDFs, line breaks are
joined and line-end hyphenation is removed, and nothing else is changed. Fedlex texts are the current consolidated AKN XML,
found with the Fedlex SPARQL endpoint and downloaded from `www.fedlex.admin.ch/filestore`. Footnote markers are removed from
those quotes.

**Status labels.** **VERIFIED** means we fetched the source and the quote is exact. **VERIFIED (absence)** means we searched the
named document for the named terms and found nothing. **UNVERIFIED** means we found no public source, or only a source we could
not fetch.

---

## 1. Short answer

1. **The BAG decides the limitation wording.** The marketing-authorisation holder (Zulassungsinhaberin, ZI) proposes a
   limitation in an application form that may be filled in *one* official language. In the new ePL application the ZI cannot
   edit the "new limitation" field and can only comment on it. VERIFIED (sections 2.2 to 2.5).
2. **The DE, FR and IT texts sit side by side in ePL.** The BAG-side (internal) editor has three plain text fields, "Limitierungstext
   DE / FR / IT", and the SL is published as one FHIR file per language. VERIFIED (section 4).
3. **We found no public source that says who translates.** The candidates are the BAG section's own staff, the BAG
   language service ("Sprachdienste des BAG", which does exist), external translators, or text supplied by the ZI. None of them is
   documented for SL limitations. UNVERIFIED (section 6).
4. **There is an explicit translation-congruence check, done by the ZI.** The ePL triennial-review form asks the ZI whether the
   limitation is clearly worded "und die Übersetzungen sind kongruent". VERIFIED (section 5).
5. **The SL handbook, the KVV and the KLV contain no rule on the languages of limitation texts.** VERIFIED (absence) (section 3).
6. **The federal standard CAT tool is STAR Transit,** and Transit can unpack and pack XLIFF projects. Which XLIFF versions it
   supports is UNVERIFIED, and so is the standard number "ISB A734" (section 7).

---

## 2. Who drafts the limitation text, and in which workflow

### 2.1 Legal basis: the BAG decides the limitation

- KVV Art. 73 (SR 832.102, consolidated version of 2026-08-01). VERIFIED.
  URL: https://www.fedlex.admin.ch/eli/cc/1995/3867_3867_3867/de (XML: https://www.fedlex.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/1995/3867_3867_3867/20260801/de/xml/fedlex-data-admin-ch-eli-cc-1995-3867_3867_3867-20260801-de-xml.xml)
  > "Die Aufnahme in eine Liste kann unter der Bedingung einer Limitierung erfolgen. Die Limitierung kann sich insbesondere auf die Menge oder die medizinischen Indikationen beziehen."
- KLV Art. 31 Abs. 1 (SR 832.112.31, version of 2026-08-01). VERIFIED.
  URL: https://www.fedlex.admin.ch/eli/cc/1995/4964_4964_4964/de
  > "Das BAG entscheidet nach Konsultation der Eidgenössischen Arzneimittelkommission (EAK) über: [...] c. Gesuche und die Folgen von Meldungen nach Artikel 65f KVV."

### 2.2 The application (GÄL): the ZI proposes, in one official language

Source: *Handbuch betreffend die Spezialitätenliste (SL) und die Geburtsgebrechen-Spezialitätenliste (GG-SL)*, dated
1 January 2025 (142 pages, PDF created 2025-02-21). This is the latest version we found. The BAG circular of 8 December 2025
says that "Das Handbuch [...] wird Anfang des Jahres 2026 entsprechend aktualisiert werden" (section 2.5). We found no 2026
edition, so its existence is UNVERIFIED.
URL: https://www.bag.admin.ch/dam/de/sd-web/eWqYyGMBwYb0/handbuch-betreffend-die-spezialitaetenliste-gueltig-ab-1-1-2025.pdf

- Ziff. B.4.2.1 (submission channel). VERIFIED.
  > "Für GÄL ist ein vollständiges Gesuch per Filetransfer einzureichen. Die Zugangsdaten für die Übermittlung sind beim Sekretariat der EAK (office@eak-sl.admin.ch) anzufordern."
- Ziff. B.4.3 c and d (contents of a GÄL). VERIFIED.
  > "c) Fachinformation, aus der die von Swissmedic im Zusammenhang mit dem Vorbescheid Gutheissung angebrachten Änderungen ersichtlich sind; [...]"
  > "d) Key Facts-Formular (Anhang 3j): Dieses Formular dient als Arbeitsgrundlage. Alle verlangten Angaben müssen vollständig gemacht werden. Das Formular ist in einer Amtssprache (deutsch, französisch, italienisch) auszufüllen."
  The handbook repeats the sentence "in einer Amtssprache (deutsch, französisch, italienisch) auszufüllen" for every
  application type (about 15 times). The French edition says the same. URL:
  https://www.bag.admin.ch/dam/fr/sd-web/eWqYyGMBwYb0/handbuch-betreffend-die-spezialitaetenliste-gueltig-ab-1-1-2025.pdf
  > "[...] doit contenir toutes les indications exigées et être rempli dans une langue officielle (français, allemand, italien)."
- Key Facts form for a GÄL (Anhang 03 j, .docx). Section 6 has a single field for the proposed limitation and does not ask for
  a language. The disease name is the only field the form asks for in two languages. VERIFIED.
  URL: https://www.bag.admin.ch/dam/it/sd-web/8ljW6756-BQk/Anhang%2003%20j%20Key%20Facts%20G%C3%84L.docx
  > "6. Limitierung" / "Beantragte Limitierung (pro Gesuch maximal eine Indikation)" / "«Limitierung»" / "Begründung der Änderung/Erweiterung der Limitierung" / "Limitierungen im Ausland" / "Name Land: «Wortlaut Limitierung»"
  > "Allgemeine Bezeichnung der Krankheit Deutsch und Französisch"
- GÄL checklist (Anhang 01 j). It asks for no translations. VERIFIED (absence): no "Übersetz", "Sprach", "französ" or "italien" in
  any of the checklists 01 a, b, c, d, g, j, k, l, n, o, p, q. The checklists for 01 e, f, h, i and m were not checked.
  URL: https://www.bag.admin.ch/dam/it/sd-web/Rrzt8aAoo4Gy/Anhang%2001%20j%20Checkliste%20G%C3%84L.pdf
  > "Die Unterlagen sind als PDF-Datei mit OCR (Optische Zeichenerkennung) einzureichen - als Einzeldokumente und als Gesamtdokument."

### 2.3 The BAG writes or adapts limitations on its own initiative

- Handbook Ziff. B.14.3. VERIFIED.
  > "Schränkt Swissmedic die Indikation eines Arzneimittels ein, so passt das BAG die Limitierung des Arzneimittels unverzüglich an (Art. 65g Abs. 1 KVV)."
- Handbook Ziff. E.1.16.4 (generics; E.1.18.5 says the same for biosimilars, and the co-marketing section says the same for
  co-marketing products). The same text is copied to many SL entries. VERIFIED.
  > "Verfügt das BAG für das Originalpräparat eine neue Limitierung oder wird die bestehende Limitierung angepasst, so wird dieselbe Limitierung auch für die Generika verfügt."
- Example of a limitation written by the BAG in a triennial review, with no ZI application: the BAG letter of 11 April 2025 on
  levothyroxine. VERIFIED.
  URL: https://www.bag.admin.ch/dam/de/sd-web/Qa6mZKCC2IsF/Infoschreiben%20zur%20neuen%20Limitierung%20der%20Levothyroxin-Pr%C3%A4parate%20per%201.%20Mai%202025.pdf
  > "Entsprechend wurde für die in der Spezialitätenliste aufgeführten Levothyroxin-Präparate (ELTROXIN, EUTHYROX, NOVOTHYRAL) im Rahmen der periodischen Überprüfung der Aufnahmebedingungen für eine Umsetzung per 1. Mai 2025 eine Limitierung festgelegt."

### 2.4 Decision step: the ZI is heard on a draft ruling

- BAG circular of 28 September 2023 on the publication process, signed by the head of the Sektion Arzneimittelaufnahmen.
  VERIFIED.
  URL: https://www.bag.admin.ch/dam/de/sd-web/dCqAUE7C2t7T/rundschreiben-des-bag-vom-28-september-2023-zur-anpassung-des-publikationsprozesses.pdf
  > "Neu wird der Zulassungsinhaberin gleichzeitig mit Zustellung des Verfügungsentwurfs das rechtliche Gehör für die Publikation gewährt."
  The circular does not say in which language(s) the draft ruling and its limitation text are sent. That is UNVERIFIED.
- Handbook Ziff. A.4.2: rulings are usually issued for the 1st of a month. VERIFIED.
  > "Aufnahmen und Änderungen in der SL werden in der Regel per 1. eines Monats verfügt. Aus administrativen Gründen ist das spätmöglichste Verfügungsdatum in der Regel der 15. des Vormonats."

### 2.5 The ePL platform: the ZI comments, the BAG controls the limitation field

- BAG ePL page. VERIFIED.
  URL: https://www.bag.admin.ch/de/elektronische-plattform-leistungen-epl
  > "Gesuche sollen zukünftig direkt auf der Plattform eingereicht werden können."
  > "Gegen Ende 2025 folgt mit der Arzneimittelaufnahme der letzte Prozess, der die SL betrifft."
  > "Die neue Spezialitätenliste ist seit dem 05. Januar 2026 unter folgender Adresse erreichbar: https://sl.bag.admin.ch/sl"
  We could not confirm whether new applications (as opposed to the triennial review) already run through ePL as of
  2026-10-09. UNVERIFIED.
- BAG circular of 8 December 2025 on the 2026 triennial review. VERIFIED.
  URL: https://www.bag.admin.ch/dam/en/sd-web/8gaPpGvrH8s7/Rundschreiben%20%C3%9Cberpr%C3%BCfung%20der%20Aufnahmebedingungen%20alle%203%20Jahre%202026_DE.pdf
  > "Die Überprüfung der Aufnahmebedingungen alle drei Jahre wird im Jahr 2026 über die ePL-Applikation erfolgen [...]"
  > "Die Stellungnahmen zu den einzelnen Kriterien werden direkt in den entsprechenden Datenfeldern eingetragen."
- ePL application UI strings (the public i18n file of the SL/ePL web app). VERIFIED.
  URL: https://sl.bag.admin.ch/assets/i18n/de.json (FR: `/fr.json`, IT: `/it.json`)
  - `sl.request.limitationChanges.infoAH`:
    > "Dieses Feld kann nicht durch Sie bearbeitet werden. Sollten Sie mit der neuen Limitierung nicht einverstanden sein, nehmen Sie bitte im Stellungnahme Feld dazu Stellung."
  - `authorType.long.AH` = "Zulassungsinhaberin". This shows that "AH" in these keys means the ZI.
  - `constants.assignWiMi` = "WiMi zuteilen" (FR: "attribuer des collaborateurs scientifiques"). Applications are assigned to
    scientific staff at the BAG.

---

## 3. What the rules say about languages

| Rule | Says about SL limitation languages | Status |
|---|---|---|
| SL handbook 2025 | Nothing. The only language rule is the "one official language" rule for the Key Facts form. Searched for: Übersetz, kongruent, Sprach, französisch, italienisch, Landessprache. | VERIFIED (absence) |
| SL handbook 2017 | Same as 2025. https://www.bag.admin.ch/dam/de/sd-web/J9UfOyX1pBDw/handbuch-betreffend-die-spezialitaetenliste-gueltig-ab-01.05.2017.pdf | VERIFIED (absence) |
| KVV, KLV (current) | Nothing. The full texts were searched for Sprache, Amtssprache, französisch, italienisch and Übersetz. The only hits are on doctors' language skills and a footnote about a French correction. | VERIFIED (absence) |
| KVV Art. 71 | Publication goes through an online platform, not the AS or SR. | VERIFIED, quote below |
| SpG Art. 10 | Simultaneous DE/FR/IT publication applies to texts published in the AS, SR or BBl. | VERIFIED, quote below |
| SpV Art. 2, Art. 4 | Federal texts that are published must be clear in all official languages. The most important web content must be in DE/FR/IT. | VERIFIED, quote below |
| VAM Art. 26 | The Fachinformation must be in all three official languages. | VERIFIED, quote below |

- KVV Art. 71 Abs. 1 Bst. a and Abs. 4. VERIFIED.
  > "Das BAG veröffentlicht: a. die Spezialitätenliste (Art. 52 Abs. 1 Bst. b KVG);"
  > "Die Veröffentlichungen erfolgen über eine öffentlich zugängliche Online-Plattform."
- Sprachengesetz (SpG, SR 441.1) Art. 10 Abs. 1. VERIFIED. URL: https://www.fedlex.admin.ch/eli/cc/2009/821/de
  > "Die Erlasse des Bundes und andere Texte, die nach dem Publikationsgesetz vom 18. Juni 2004 oder aufgrund anderer Bestimmungen des Bundesrechts in der Amtlichen und der Systematischen Sammlung des Bundesrechts oder im Bundesblatt zu veröffentlichen sind, werden in Deutsch, Französisch und Italienisch veröffentlicht, soweit das Gesetz nichts anderes vorsieht."
  We found no provision that publishes the SL in the AS, SR or BBl. So we could not establish that SpG Art. 10 applies, or that
  the FR/IT limitation texts are legally equally authentic. Both are UNVERIFIED.
- Sprachenverordnung (SpV, SR 441.11) Art. 2 Abs. 1 and Art. 4 Abs. 1. VERIFIED. URL: https://www.fedlex.admin.ch/eli/cc/2010/355/de
  > "Die zu veröffentlichenden Texte des Bundes sind in allen Amtssprachen sachgerecht, klar und bürgerfreundlich sowie nach den Grundsätzen der sprachlichen Gleichbehandlung der Geschlechter zu formulieren."
  > "Die Einheiten der Bundesverwaltung stellen die wichtigsten Inhalte ihrer Internetseiten in Deutsch, Französisch und Italienisch zur Verfügung."
  The SpV has no article that assigns the translation of an office's documents to a particular service (VERIFIED (absence):
  searched all articles for Übersetz, Sprachdienst and Terminolog). Art. 3 covers Romansh only.
- Arzneimittelverordnung (VAM, SR 812.212.21) Art. 26 Abs. 2. VERIFIED. URL: https://www.fedlex.admin.ch/eli/cc/2018/588/de
  > "Die Fachinformation und die Packungsbeilage von Human- und Tierarzneimitteln müssen in den drei Amtssprachen abgefasst werden."
- Swissmedic, "Fachinformation in drei Amtssprachen" (presentation of 9 November 2018). The ZI is responsible for the three
  language versions of the Fachinformation. This matters because SL limitations often reuse the Swissmedic indication wording,
  so the ZI already holds an FR/IT Fachinformation. VERIFIED.
  URL: https://www.swissmedic.ch/dam/swissmedic/de/dokumente/stab/veranstaltung/hmg/fachinformationindreiamtssprachen.pdf.download.pdf/07_italienische%20FI_Anna%20Barbara%20Stalder.pdf
  > "Dreisprachigkeit Fachinformation eigenverantwortlich durch Zulassungsinhaberin umzusetzen" / "Kein Gesuch an Swissmedic"
  Whether the BAG reuses the ZI's FR/IT Fachinformation wording when it writes FR/IT limitations is UNVERIFIED.

---

## 4. The tool: where the FR/IT texts live

- **BAG internal editor (ePL).** It has three separate plain text fields, one per language. VERIFIED.
  URL: https://sl.bag.admin.ch/assets/i18n/de.json
  > `sl.internal.editMedicinalProduct.limitations.limitationDescriptionDe` = "Limitierungstext DE"
  > `sl.internal.editMedicinalProduct.limitations.limitationDescriptionFr` = "Limitierungstext FR"
  > `sl.internal.editMedicinalProduct.limitations.limitationDescriptionIt` = "Limitierungstext IT"
  > `admin.manage.limitations.create.description.fr` = "Beschreibung Französisch"; `...description.it` = "Beschreibung Italienisch"
  > `admin.manage.limitations.costApproval` = "KoGu" (a limitation can be flagged as requiring prior cost approval)
  These keys sit under `sl.internal.*` and `admin.*`, that is, the BAG-side screens. We found no key that marks a translation
  status or a translation workflow ("Übersetzung", "translation", "language"). VERIFIED (absence) in de.json.
- **Publication: one FHIR file per language.** VERIFIED.
  `GET https://epl.bag.admin.ch/api/sl/public/resources/current` with `Accept-Language: fr` returned
  > `"fhir":{"fileUrl":"sl/publication/fhir/foph-sl-publication-20261006-fr.ndjson","lastUpdated":"2026-10-06"}`
  (and `-de`, `-it` for the other languages). In the first bytes of the FR file
  (https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-fr.ndjson), a limitation
  (`ClinicalUseDefinition`, `indication.diseaseSymptomProcedure.concept.text`) reads:
  > "Substitution préparation originale/générique Aucune nouvelle garantie de prise en charge n'est nécessaire pour le traitement par ABIRATERON ACCORD s'il existe déjà une gar[antie ...]"
  The IT file reads:
  > "Sostituzione preparato di riferimento/biosimilare Per tutte le indicazioni che necessitano di una garanzia di assunzione dei costi, non è richiesta una nuova garanzia di assunzione dei costi per il trattamento co[n ...]"
- **FHIR specification.** The limitation wording is a single string per resource, and each language goes in its own file. VERIFIED.
  URL: https://fhir.ch/ig/ch-epl/StructureDefinition-fullLimitationText.html
  > "Extension for representing the full wording of the limitations used by FOPH" (value type `string`)
- **Data-quality observation.** The "current changes" Excel for French (`foph-sl-current-changes-20261001-fr.xlsx`) is
  byte-identical to the German one: both have MD5 `4eee37edf1c9415ce69779018d6cb4f4`, and the French file has German headers
  ("Limitierungstext alt", "Limitierungstext neu") and German limitation texts. VERIFIED (downloaded from
  https://epl.bag.admin.ch/static/sl/publication/excel/current-changes/foph-sl-current-changes-20261001-fr.xlsx and `-de.xlsx`).
  So the monthly change list, which shows old and new limitation text side by side, is published in German only.
- **ePL vision (BAG presentation to industry, 27 June 2024).** VERIFIED.
  URL: https://ywesee.com/uploads/Main/ePL.pdf
  > "Steuerung aller Prozesse der Spezialitätenliste über die neue Plattform, u.a. ▪ Aufnahme: Vom Gesucheingang bis hin zur Publikation der Entscheidung"

---

## 5. The "kongruent" checklist (triennial review, answered by the ZI)

The checklist is a question in the expediency (Zweckmässigkeit) chapter of the ePL triennial review ("3-Jährliche
Überprüfung", key `sl.requestTypes.3JUE`). The ZI enters its answers there (section 2.5: "Die Stellungnahmen zu den einzelnen
Kriterien werden direkt in den entsprechenden Datenfeldern eingetragen"). VERIFIED.
URL: https://sl.bag.admin.ch/assets/i18n/de.json (also `fr.json`, `it.json`)

- `sl.request.expediency.changes.formulationLimitation`
  - DE: > "Falls eine Limitierung vorhanden ist, ist diese wissenschaftlich eindeutig und klar verständlich formuliert und die Übersetzungen sind kongruent?"
  - FR: > "S'il y a une limitation, est-elle formulée de manière scientifique et claire et les traductions sont-elles congruentes ?"
  - IT: > "Se è presente una limitazione, è formulata in modo scientificamente chiaro e comprensibile e le traduzioni sono coerenti?"
- Help text, `sl.request.expediency.info.changes.formulationLimitation` (DE):
  > "Sollte gegebenenfalls der Text der Limitierung verständlicher formuliert werden, um Missverständnisse zu vermeiden? Ist gegebenenfalls eine Übersetzung missverständlich formuliert?
  > Inhaltliche Limitierungsanpassungen oder -erweiterungen müssen in Form eines Gesuches Änderung der Limitierung (GÄL) oder Gesuch um Erweiterung der Indikation (IND) eingereicht werden. Eine Änderung der Indikation ist dem BAG zu melden."
- Neighbouring questions in the same block include `...hasMedicalDemandChanged` ("Gibt es Änderungen hinsichtlich des
  medizinischen Bedarfes?") and `...otherRelevantChanges`. The statement label is
  `sl.request.expediency.statement.formulationLimitation` = "Formulierung Limitierung".

What this shows: the BAG asks the ZI to self-check whether the FR/IT versions match the DE limitation every three years.
Wording problems can be raised as a statement, but changes of substance need a GÄL or IND. VERIFIED. How often ZIs report
incongruent translations through this field is not public. UNVERIFIED.

---

## 6. Who translates? (the gap)

- **The BAG has its own language service.** It is mentioned in a 2017 BAG checklist on translating evaluation reports, not in
  connection with the SL. VERIFIED.
  URL: https://www.bag.admin.ch/dam/de/sd-web/LVtKzwf5Pzd6/2017-checklist-qualitaetssicherung-uebersetzungen-evaluationsberichte.pdf
  > "In einigen Fällen organisiert die Fachstelle Übersetzungsdienstleistungen direkt über die Sprachdienste des BAG (SpD, Kompetenzzentrum und Referenzstelle für sprachliche Belange)."
  This is not the SL "kongruent" checklist. It is a separate translation-QA checklist with criteria such as
  "Bedeutung (Aussagen und Sinn des Ausgangstextes sind exakt wiedergegeben)".
- **Federal arrangement for translation into DE/FR/IT.** Federal Chancellery page "Übersetzung". VERIFIED.
  URL: https://www.bk.admin.ch/de/uebersetzung
  > "Für Übersetzungen in die drei Amtssprachen Deutsch, Französisch und Italienisch sind in der Bundesverwaltung die folgenden Stellen zuständig: die zentralen Sprachdienste der Bundeskanzlei, mit Querschnittsaufgaben für die ganze Bundesverwaltung die zentralen Sprachdienste der Departemente die Übersetzerinnen und Übersetzer einzelner Ämter"
- **UNVERIFIED: who produces the FR/IT limitation text.** No public source says whether it is the scientific staff of the
  Sektion Arzneimittelaufnahmen, the BAG Sprachdienste, external translators, or a FR/IT text supplied by the ZI. The handbook
  does not require the ZI to submit FR/IT (section 2.2), and the ZI cannot edit the field in ePL (section 2.5). Both point to the
  BAG side, but this is an inference, not a documented fact.
- **UNVERIFIED: the language of the draft ruling (Verfügungsentwurf).** We do not know whether the draft ruling the ZI is heard on
  contains the limitation in DE only or in all three languages.

---

## 7. The federal translation tool

- **Transit is the federal CAT tool.** Interview with the head of the EFD language services, ZHAW blog, 5 November 2024.
  VERIFIED.
  URL: https://blog.zhaw.ch/languagematters/2024/11/05/uebersetzerinnen-zukunft-bundesverwaltung/
  > "Vor ein paar Jahren wurde für alle Sprachdienste der Bundesverwaltung das Übersetzungstool Transit eingeführt."
  > "Ausserdem besitzt die Bundesverwaltung DeepL Pro-Lizenzen für alle Mitarbeitenden."
- **The decision to standardise, and the MT plug-in.** Bericht DeepL-Test, Arbeitsgruppe "Maschinelle Übersetzung" z. H. der
  KOSD, 19 November 2019. VERIFIED.
  URL: https://www.newsd.admin.ch/newsd/message/attachments/59735.pdf
  > "Im Rahmen der strukturellen Reformen 2018 hat der Bundesrat am 29. August 2018 neben der Beschaffung eines Standardprodukts für die computerunterstützte Übersetzung (CAT-Tool) die BK beauftragt, die «computerunterstützte Übersetzung sowie die eng damit zusammenhängenden Teilaufgaben (wie automatische Übersetzung, Terminologieverwaltung, ‹translation memory› u. ä) als Standardeinsatzgebiet [...] zu standardisieren»."
  > "Das CAT-Tool, das für die ganze Bundesverwaltung beschafft wurde und spätestens ab 2022 in allen Departementen im Einsatz ist, verfügt über die Möglichkeit, DeepL Pro oder einen anderen MÜ-Dienstleister einzubinden."
  > "Das Plug-In konnte nur im EDA mit SDL Trados Studio und im UVEK mit Star Transit getestet werden."
- **UNVERIFIED: "ISB A734" as the standard number.** Searches for "A734" with Bundesverwaltung, Transit or Übersetzung returned
  nothing relevant. The standardisation itself is documented (Federal Council decision of 29 August 2018, above), but the
  standard ID is not.
- **XLIFF in Transit NXT.** Transit NXT User's Guide, "Valid from Transit NXT Service Pack 18", revised 2025-08. VERIFIED.
  URL: https://www.star-group.net/-downloads-/document/1958/TransitNXT_Usage_UsersGuide_ENG.pdf
  > "Transit supports an array of exchange formats, including the localization interchange file format XLIFF and third-party formats such as sdlppx/sdlrpx, wszx and mqout/mqback."
  > "You unpack the XLIFF file in the same way as a Transit project [...]. Transit creates the project with settings defined in the XLIFF file (e.g. source and target language)."
  > "When you have translated the language files, you pack the translation as an XLIFF file and send it back to the client"
  Release notes: https://www.star-group.net/-downloads-/file/1933/Transit-TermStar-NXT-Release-Notes.htm. VERIFIED.
  > "Transit now allows to unpack zipped XLIFF projects to a single Transit project and to pack the translation as zipped XLIFF projects."
  - **UNVERIFIED: which XLIFF versions (1.2 and/or 2.x) Transit accepts.** Neither the user guide nor the release notes name a
    version.
  - **UNVERIFIED: whether Transit can export its own projects as XLIFF.** This claim appears only in ProZ forum posts
    (https://www2.proz.com/forum/transit_support/344081-is_it_still_not_possible_to_create_xliff_files.html, 2020). The page
    returned a Cloudflare challenge to our client, so we could not fetch or quote it. In practice, XLIFF is a project exchange
    format that Transit "unpacks", not a file type it imports.

---

## 8. Effort and staffing

- GPK-S follow-up report "Spezialitätenliste der OKP", 14 November 2023. VERIFIED.
  URL: https://www.parlament.ch/centers/documents/de/Bericht%20der%20GPK-S%20(definitiv)%20vom%2014.11.2023%20D.pdf
  > "Die Zahl der Mitarbeitenden der betroffenen Sektionen ist von 11,8 Vollzeitstellen (VZÄ) im Jahr 2014 auf rund 25 VZÄ im Jahr 2023 gestiegen"
  This figure covers all SL work of the sections concerned, not limitation-text or translation work.
- **UNVERIFIED: any public number on people or hours spent on SL limitation texts or their translation.** None was found in the
  handbook, the GPK-S report or EFK-22608
  (https://www.efk.admin.ch/wp-content/uploads/publikationen/berichte/bildung_und_soziales/gesundheit/22608/22608be-endgueltige-fassung-v04.pdf;
  searched for Stellen, VZÄ, Übersetz and Sprach).

---

## 9. Who reads the texts downstream (insurers, Vertrauensärzte)

- Handbook Ziff. J.1.1.1 and J.1.1.4. The limitation is the boundary of mandatory reimbursement, and use outside it is decided by
  the insurer with the Vertrauensarzt. VERIFIED.
  > "Die Vergütungspflicht erstreckt sich grundsätzlich nur auf Arzneimittel, die in der SL aufgeführt sind und innerhalb der Limitierungen der SL angewendet werden."
  > "Es obliegt dem Krankenversicherer, nach Rücksprache mit dem Vertrauensarzt solche Einzelfälle gemäss den geltenden Verordnungsbestimmungen zu beurteilen."
  > "Die Schweizerische Gesellschaft der Vertrauens- und Versicherungsärzte (SGV; vgl. https://www.vertrauensaerzte.ch/) stellt standardisierte Kostengutspracheformulare zur Verfügung."
- ePL page. VERIFIED.
  > "Für Krankenkassen: Klare Grundlage für die Vergütung und Kostenkontrolle."
- **UNVERIFIED: that insurers (santésuisse, curafutura, SVK members) or Vertrauensärzte rely specifically on the FR or IT wording.**
  It is plausible, because insurers and doctors in Romandie and Ticino work in their own language and FR/IT FHIR files exist, but
  we found no public statement on it.

---

## 10. Public record of translation errors

- **UNVERIFIED (none found).** We found no BAG erratum, no parliamentary question and no court decision about a wrong FR or IT
  translation of an SL limitation. Searches covered BVGer/BGer with "französische Fassung" and Limitierung, "version
  française"/"texte allemand" with "liste des spécialités", Interpellation/Fragestunde with Spezialitätenliste and Übersetzung,
  and the BAG page "Mitteilungen zur SL" (https://www.bag.admin.ch/de/mitteilungen-zur-spezialitaetenliste-sl, searched for
  Korrektur, Berichtigung, Übersetzung, französisch, italienisch and Fehler; no hits).
- The only public acknowledgement of the risk is the BAG's own ePL help text (section 5): "Ist gegebenenfalls eine Übersetzung
  missverständlich formuliert?" VERIFIED.

---

## Where a drafting tool plugs in

This section relies only on what is documented above.

1. **Primary insertion point: the BAG's internal limitation editor in ePL, before the draft ruling goes out.** The BAG decides
   and writes the limitation (KVV Art. 73, handbook B.14.3, E.1.16.4, the levothyroxine example). ePL stores DE, FR and IT in three
   separate fields ("Limitierungstext DE/FR/IT"), and the ZI cannot edit the field. When a staff member changes the DE text, the
   tool would propose the matching minimal edit to the existing FR and IT texts, for a human to accept, before the draft ruling
   and the hearing (circular of 28.09.2023). The handbook's copy rule for generics, biosimilars and co-marketing products
   (E.1.16.4) multiplies each change across many entries, which is where consistent drafting pays off most. Who does the FR/IT
   step today is unknown (section 6), so a pilot must first establish whether the drafts go to scientific staff, to the BAG
   Sprachdienste or to external translators.
2. **Secondary: the congruence question in the triennial review.** The ePL form already asks the ZI whether "die Übersetzungen
   sind kongruent". A checker that flags FR/IT segments that do not reflect the DE text (missing negation, changed number,
   dropped clause) serves both sides: the ZI answering the question, and the BAG staff reviewing the answers. No new process is
   needed: the question is already in the live ePL app strings, and the 2026 review ran in ePL.
3. **Tertiary: hand-off to a language service through Transit.** If translation goes to a federal language service, the
   standard tool is Transit, which unpacks and packs XLIFF projects. Drafts would have to be delivered as XLIFF with the
   DE-old/DE-new context attached. The supported XLIFF version is UNVERIFIED and would have to be tested with the service's
   Transit setup before any pilot.
4. **Unlikely: the applicant's dossier.** The ZI may file the Key Facts form in a single language, and its proposed limitation
   is only a working basis. An applicant-side FR/IT drafter therefore has no formal slot. It could at most help a ZI check the
   BAG's FR/IT text during the hearing.

**Pilot partner.** The BAG Sektion Arzneimittelaufnahmen (Direktionsbereich Kranken- und Unfallversicherung, contact
office@eak-sl.admin.ch per https://www.bag.admin.ch/de/mitteilungen-zur-spezialitaetenliste-sl; the 2023 circular is signed by
its head) owns the limitation texts. The ePL project team (epl@bag.admin.ch, per the ePL page) owns the editor where the tool
would plug in. If the FR/IT step turns out to sit with the BAG Sprachdienste, they and the Federal Chancellery's Kompetenzzentrum
Sprachtechnologien (named in the 2019 DeepL report as the body building language technology for the administration) are the
partners for the Transit/XLIFF route. Every one of these roles is documented. Whether any of them would take part is not.
