# Who writes the FR/IT limitation texts of the SL, and where a drafting tool fits

Jurors asked who writes the French and Italian limitation texts of the Spezialitätenliste (SL) today, in which workflow and
tool, and where a drafting tool would plug in. This note answers from public sources only.

**Method.** All sources were retrieved on 2026-10-09 with `curl` (User-Agent `hackapertus-research/0.1`) and searched with a
web search engine. Every point that was open on 2026-10-09 was checked again on 2026-10-11 against public sources only
(bag.admin.ch, the public i18n files of sl.bag.admin.ch in DE/FR/IT/EN, fedlex.admin.ch, bk.admin.ch, STAR Group's public
Transit documentation), with the same User-Agent and robots.txt respected. No model APIs were used. PDFs were converted with `pdftotext -layout`. In quotes from PDFs, line breaks are
joined and line-end hyphenation is removed, and nothing else is changed. Fedlex texts are the current consolidated AKN XML,
found with the Fedlex SPARQL endpoint and downloaded from `www.fedlex.admin.ch/filestore`. Footnote markers are removed from
those quotes.

**Status labels.** **VERIFIED** means we fetched the source and the quote is exact. **VERIFIED (absence)** means we searched the
named document for the named terms and found nothing. **Not public** means no public source settles the point; the entry then
states what the public record does show, and the point is one for the office to confirm from its own files.

---

## 1. Short answer

1. **The BAG decides the limitation wording.** The marketing-authorisation holder (Zulassungsinhaberin, ZI) proposes a
   limitation in an application form that may be filled in *one* official language. In the new ePL application the ZI cannot
   edit the "new limitation" field and can only comment on it. VERIFIED (sections 2.2 to 2.5).
2. **The DE, FR and IT texts sit side by side in ePL.** The BAG-side (internal) editor has three plain text fields, "Limitierungstext
   DE / FR / IT", and the SL is published as one FHIR file per language. VERIFIED (section 4).
3. **Who translates SL limitations is not public; the federal default is.** The Sprachdiensteverordnung assigns
   translation "in der Regel" to the federal language services, and a department's units translate that department's texts
   (SpDV Art. 10, VERIFIED). The BAG has its own language service (VERIFIED). No public source says whether SL limitation texts
   follow that default or are written in FR/IT by the section's staff. Not public (section 6).
4. **There is an explicit translation-congruence check, done by the ZI.** The ePL triennial-review form asks the ZI whether the
   limitation is clearly worded "und die Übersetzungen sind kongruent". VERIFIED (section 5).
5. **The SL handbook, the KVV and the KLV contain no rule on the languages of limitation texts.** VERIFIED (absence) (section 3).
6. **The federal standard CAT tool is STAR Transit,** mandated by the ISB ICT standard A734 (VERIFIED). Transit unpacks XLIFF
   projects and packs the translation back (VERIFIED); packing its own projects as XLIFF needs STAR CLM (VERIFIED). STAR's public
   documentation names no XLIFF version: not public (section 7).

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
says that "Das Handbuch [...] wird Anfang des Jahres 2026 entsprechend aktualisiert werden" (section 2.5). As of 2026-10-11 the
1 January 2025 edition is still the current one. VERIFIED (absence): the BAG page "Antragsprozesse Arzneimittel"
(https://www.bag.admin.ch/de/antragsprozesse-arzneimittel) lists "Handbuch betreffend die Spezialitätenliste gültig ab 1.1.2025"
as its current handbook, and lists 2017 and older editions as "Vorgängerversionen". The BAG page "Mitteilungen zur SL" says
"Entsprechende Anpassung im Handbuch betreffend die Spezialitätenliste (SL) sind im Verlauf des Jahres 2026 geplant". The
Key Facts forms for GÄL and IND were re-issued on 1 July 2026. The GÄL form still has the single limitation field described below.
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
  The circular does not say in which language(s) the draft ruling and its limitation text are sent. Not public. What the
  public record shows:
  - SL rulings follow the federal administrative procedure act. The KVG excludes the ATSG for "Tarife, Preise und
    Globalbudget (Art. 43–55)" (KVG Art. 1 Abs. 2 Bst. b, SR 832.10, version of 2026-07-01,
    https://www.fedlex.admin.ch/eli/cc/1995/1328_1328_1328/de), and the SL is Art. 52 Abs. 1 Bst. b. The VwVG applies to
    rulings of "Departemente [...] und die ihnen unterstellten Dienstabteilungen" (VwVG Art. 1 Abs. 2 Bst. a, SR 172.021). VERIFIED.
  - VwVG Art. 33a Abs. 1 (version of 2022-07-01, in force on 2026-10-11). VERIFIED.
    URL: https://www.fedlex.admin.ch/eli/cc/1969/737_757_755/de
    > "Das Verfahren wird in einer der vier Amtssprachen geführt, in der Regel in der Sprache, in der die Parteien ihre Begehren gestellt haben oder stellen würden."
    Since the ZI files its application in one official language (section 2.2), the legal default is a procedure, and so a
    draft ruling, in that one language. Whether the BAG also sends the FR/IT limitation with it is not public.
  - The ePL ruling screen is a template ("Verfügungs-/Mitteilungsentwurf"; "Es konnten nicht alle dynamischen Felder ersetzt
    werden") with no language field. VERIFIED (absence) in https://sl.bag.admin.ch/assets/i18n/de.json, keys
    `sl.request.disposition.*`.
- Handbook Ziff. A.4.2: rulings are usually issued for the 1st of a month. VERIFIED.
  > "Aufnahmen und Änderungen in der SL werden in der Regel per 1. eines Monats verfügt. Aus administrativen Gründen ist das spätmöglichste Verfügungsdatum in der Regel der 15. des Vormonats."

### 2.5 The ePL platform: the ZI comments, the BAG controls the limitation field

- BAG ePL page. VERIFIED.
  URL: https://www.bag.admin.ch/de/elektronische-plattform-leistungen-epl
  > "Gesuche sollen zukünftig direkt auf der Plattform eingereicht werden können."
  > "Gegen Ende 2025 folgt mit der Arzneimittelaufnahme der letzte Prozess, der die SL betrifft."
  > "Die neue Spezialitätenliste ist seit dem 05. Januar 2026 unter folgender Adresse erreichbar: https://sl.bag.admin.ch/sl"
  As of 2026-10-11 the page still says "sollen zukünftig". New applications are filed by file transfer, not in ePL.
  VERIFIED. URL: https://www.bag.admin.ch/de/antragsprozesse-arzneimittel
  > "Neuerung zur elektronischen Gesuchseinreichung Neu sind die Gesuchsunterlagen mit Filetransfer einzureichen. Die Zugangsdaten für die Übermittlung der entsprechenden Dokumente sind beim Sekretariat der EAK office@eak-sl.admin.ch zu verlangen."
  The ePL app already defines every application type: `sl.requestTypes.NAO` = "Neuaufnahmegesuch Originalpräparat
  (ordentliches und beschleunigtes Verfahren)", `sl.requestTypes.GAEL` = "Gesuch um Änderung / Einschränkung der
  Limitierung", `sl.requestTypes.IND`, and `sl.request.submit` = "Gesuch einreichen" (https://sl.bag.admin.ch/assets/i18n/de.json).
  VERIFIED. So the screens exist, but the public instructions still route applications through file transfer. The BAG
  circular of 9 July 2026 on the indication code confirms that the SL itself runs in ePL: "Mit der elektronische Plattform
  Leistungen (ePL), welche per 05. Januar 2026 freigeschaltet wurde [...]" (https://www.bag.admin.ch/dam/de/sd-web/Ubznn2-8HnZN/Informationsschreiben%20zur%20%C3%9Cbermittlung%20des%20Indikationscode%20vom%209.%20Juli%202026.pdf). VERIFIED.
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
| SpDV Art. 10, Art. 11 | Translation for the administration is done "in der Regel" by the federal language services; a department's units translate its texts; external translators only through the responsible unit. Says nothing specific about the SL. | VERIFIED, quote in section 6 |
| VAM Art. 26 | The Fachinformation must be in all three official languages. | VERIFIED, quote below |

- KVV Art. 71 Abs. 1 Bst. a and Abs. 4. VERIFIED.
  > "Das BAG veröffentlicht: a. die Spezialitätenliste (Art. 52 Abs. 1 Bst. b KVG);"
  > "Die Veröffentlichungen erfolgen über eine öffentlich zugängliche Online-Plattform."
- Sprachengesetz (SpG, SR 441.1) Art. 10 Abs. 1. VERIFIED. URL: https://www.fedlex.admin.ch/eli/cc/2009/821/de
  > "Die Erlasse des Bundes und andere Texte, die nach dem Publikationsgesetz vom 18. Juni 2004 oder aufgrund anderer Bestimmungen des Bundesrechts in der Amtlichen und der Systematischen Sammlung des Bundesrechts oder im Bundesblatt zu veröffentlichen sind, werden in Deutsch, Französisch und Italienisch veröffentlicht, soweit das Gesetz nichts anderes vorsieht."
  No provision publishes the SL in the AS, SR or BBl: KVV Art. 71 Abs. 4 sends it to an online platform (above). Whether
  SpG Art. 10 nevertheless applies, and whether the DE, FR and IT limitation texts are equally authentic, is a legal question
  that no statute, ordinance, handbook passage or court decision we found answers. Not public. What the record shows: the
  SL handbook, the KVV and the KLV contain no language rule for limitation texts (VERIFIED (absence), table above), and the
  BAG publishes all three versions side by side in separate per-language files (section 4).
- Sprachenverordnung (SpV, SR 441.11) Art. 2 Abs. 1 and Art. 4 Abs. 1. VERIFIED. URL: https://www.fedlex.admin.ch/eli/cc/2010/355/de
  > "Die zu veröffentlichenden Texte des Bundes sind in allen Amtssprachen sachgerecht, klar und bürgerfreundlich sowie nach den Grundsätzen der sprachlichen Gleichbehandlung der Geschlechter zu formulieren."
  > "Die Einheiten der Bundesverwaltung stellen die wichtigsten Inhalte ihrer Internetseiten in Deutsch, Französisch und Italienisch zur Verfügung."
  The SpV has no article that assigns the translation of an office's documents to a particular service (VERIFIED (absence):
  searched all articles for Übersetz, Sprachdienst and Terminolog). Art. 3 covers Romansh only. That assignment is in a separate
  ordinance, the Sprachdiensteverordnung (SpDV), quoted in section 6.
- Arzneimittelverordnung (VAM, SR 812.212.21) Art. 26 Abs. 2. VERIFIED. URL: https://www.fedlex.admin.ch/eli/cc/2018/588/de
  > "Die Fachinformation und die Packungsbeilage von Human- und Tierarzneimitteln müssen in den drei Amtssprachen abgefasst werden."
- Swissmedic, "Fachinformation in drei Amtssprachen" (presentation of 9 November 2018). The ZI is responsible for the three
  language versions of the Fachinformation. This matters because SL limitations often reuse the Swissmedic indication wording,
  so the ZI already holds an FR/IT Fachinformation. VERIFIED.
  URL: https://www.swissmedic.ch/dam/swissmedic/de/dokumente/stab/veranstaltung/hmg/fachinformationindreiamtssprachen.pdf.download.pdf/07_italienische%20FI_Anna%20Barbara%20Stalder.pdf
  > "Dreisprachigkeit Fachinformation eigenverantwortlich durch Zulassungsinhaberin umzusetzen" / "Kein Gesuch an Swissmedic"
  Whether the BAG reuses the ZI's FR/IT Fachinformation wording when it writes FR/IT limitations is not public. What the
  record shows: the handbook requires the Fachinformation with every GÄL (Ziff. B.4.3 c, section 2.2), so the FR/IT
  Fachinformation is in the dossier when the BAG writes the limitation.

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
- **What ePL exports, publicly and internally.** VERIFIED for the public side, not public for the internal side.
  - Public: the "Aktuelle und archivierte Daten" page offers Excel ("Aktueller Datenstamm", "Aktuelle Änderungen"), FHIR
    ("FHIR herunterladen") and, until mid-2026, XML: "Die aktuellen Daten im XML Format sind nur noch bis zum 30. Juni 2026
    (Datenstamm 01. Juni 2026) verfügbar, danach werden diese nur noch im FHIR Format angeboten." A preliminary tab
    publishes the next month's list: "Die Vorabdaten sind jeweils vom 25. des Monats bis Ende des Monat hier herunterladbar."
    (keys `resources.currentAndArchivedData.*` in https://sl.bag.admin.ch/assets/i18n/de.json). The BAG ePL page confirms:
    "Die monatlichen Excel- und FHIR-Dateien werden wie gewohnt jeweils am ersten eines Monats auf der Spezialitätenliste
    publiziert" (https://www.bag.admin.ch/de/elektronische-plattform-leistungen-epl).
  - Internal: the BAG-side app has an "Import / Export" screen (`admin.importExport.title`, `.exportTab`, `.importTab`) and a
    CSV export of the price-reduction list ("Hier können Sie die Preissenkungsliste als csv-Datei exportieren",
    `admin.export.deductionList.description`). Which formats the internal export offers for unpublished limitation texts is
    not public; the i18n files name none.
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
incongruent translations through this field is not public: the BAG publishes no statistics on the triennial-review
answers, and the 2026 review circular (section 2.5) gives none.

---

## 6. Who translates? (the gap)

- **The BAG has its own language service.** It is mentioned in a 2017 BAG checklist on translating evaluation reports, not in
  connection with the SL. VERIFIED.
  URL: https://www.bag.admin.ch/dam/de/sd-web/LVtKzwf5Pzd6/2017-checklist-qualitaetssicherung-uebersetzungen-evaluationsberichte.pdf
  > "In einigen Fällen organisiert die Fachstelle Übersetzungsdienstleistungen direkt über die Sprachdienste des BAG (SpD, Kompetenzzentrum und Referenzstelle für sprachliche Belange)."
  This is not the SL "kongruent" checklist. It is a separate translation-QA checklist with criteria such as
  "Bedeutung (Aussagen und Sinn des Ausgangstextes sind exakt wiedergegeben)".
- **The federal rule on who translates.** Sprachdiensteverordnung (SpDV, SR 172.081), version of 2022-07-01, Art. 10 Abs. 1
  and 2 and Art. 11 Abs. 1. VERIFIED.
  URL: https://www.fedlex.admin.ch/eli/cc/2012/771/de
  > "Die Übersetzungen und die anderen Sprachdienstleistungen für die Bundesverwaltung werden in der Regel von den Sprachdiensten der Bundesverwaltung erbracht."
  > "Die Einheiten, die in einem Departement Sprachdienstleistungen erbringen, übersetzen und revidieren in der Regel die Texte ihres Departements."
  > "Bei Arbeitsüberlastung oder Dringlichkeit und wenn alle internen Möglichkeiten ausgeschöpft sind, können einzelne Übersetzungsaufträge [...] im Einvernehmen mit der Einheit, die für die Erbringung der betreffenden Sprachdienstleistung zuständig ist, oder über diese an externe Übersetzerinnen und Übersetzer [...] vergeben werden."
  The ISB standard A734 (section 7) describes the same arrangement: "Die Sprachdienste der Departemente stellen Übersetzungen
  bzw. Revisionen ins Französische, Italienische, Deutsche und - teilweise - ins Englische sicher". A Federal Chancellery
  author in LeGes 2020/3 adds that, under the internal MT guidance, texts "die veröffentlicht oder in Arbeitsprozessen durch
  andere Personen weiterverwendet werden sollen [...] sind durch die Sprachdienste der Bundesverwaltung zu übersetzen"
  (https://leges.weblaw.ch/legesissues/2020/3/maschinelle-ubersetz_f92b5ffeea.html). VERIFIED.
- **Federal arrangement for translation into DE/FR/IT.** Federal Chancellery page "Übersetzung". VERIFIED.
  URL: https://www.bk.admin.ch/de/uebersetzung
  > "Für Übersetzungen in die drei Amtssprachen Deutsch, Französisch und Italienisch sind in der Bundesverwaltung die folgenden Stellen zuständig: die zentralen Sprachdienste der Bundeskanzlei, mit Querschnittsaufgaben für die ganze Bundesverwaltung die zentralen Sprachdienste der Departemente die Übersetzerinnen und Übersetzer einzelner Ämter"
- **Not public: who produces the FR/IT limitation text.** What the public record shows: the default for any federal text is
  the language services (SpDV Art. 10, above), and the BAG has its own (2017 checklist, above). The handbook does not require
  the ZI to submit FR/IT (section 2.2), the ZI cannot edit the field in ePL (section 2.5), and the BAG-side editor has the three
  fields (section 4). No public source says whether SL limitations follow the SpDV default or are written in FR/IT by the
  section's scientific staff. VERIFIED (absence): no key about translation or a translation workflow in any of the four ePL
  i18n files (de, fr, it, en.json; the only hits are the two "kongruent" keys of section 5); no hit for Übersetz, Sprachdienst
  or Sprache in the BAG pages "Antragsprozesse Arzneimittel", "Mitteilungen zur SL", "Veröffentlichungen des BAG zur
  Spezialitätenliste" and "Referenzdokumente zur Spezialitätenliste", other than the site's language menu.
- **Not public: the language of the draft ruling (Verfügungsentwurf).** The legal default is the language of the application
  (VwVG Art. 33a Abs. 1, section 2.4). Whether the draft ruling carries the limitation in that language only or in all three is
  not public.

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
- **ISB ICT standard A734 "Übersetzungslösung BUND".** Version 1.0, status "Genehmigt", "IKT-Beschluss Bund: 9. Juni 2020 /
  Inkraftsetzung: 15. Juni 2020", published by the Federal Chancellery. VERIFIED.
  URL: https://www.bk.admin.ch/dam/de/sd-web/eGerKT54ncdB/a734_1-0_genehmigt.pdf
  > "Es MUSS folgendes Standardprodukt eingesetzt werden: − CAT-Tool Star Transit der Firma Star AG, Software, Translation, Artwork, Recording"
  The document names no XLIFF version (VERIFIED (absence): no hit for XLIFF; formats appear only as "standardisierten
  Funktionen und Formaten rund um die Übersetzung"). Whether a
  later version has replaced 1.0 is not public; the bk.admin.ch link above still serves version 1.0, and the document provides
  for a review "spätestens vier Jahre nach der Genehmigung".
- **XLIFF in Transit NXT.** Transit NXT User's Guide, "Valid from Transit NXT Service Pack 18", revised 2025-08. VERIFIED.
  URL: https://www.star-group.net/-downloads-/document/1958/TransitNXT_Usage_UsersGuide_ENG.pdf
  > "Transit supports an array of exchange formats, including the localization interchange file format XLIFF and third-party formats such as sdlppx/sdlrpx, wszx and mqout/mqback."
  > "You unpack the XLIFF file in the same way as a Transit project [...]. Transit creates the project with settings defined in the XLIFF file (e.g. source and target language)."
  > "When you have translated the language files, you pack the translation as an XLIFF file and send it back to the client"
  Release notes: https://www.star-group.net/-downloads-/file/1933/Transit-TermStar-NXT-Release-Notes.htm. VERIFIED.
  > "Transit now allows to unpack zipped XLIFF projects to a single Transit project and to pack the translation as zipped XLIFF projects."
  - **Not public: which XLIFF versions (1.2 and/or 2.x) Transit accepts.** None of STAR's current public documents names a
    version: the User's Guide (SP18, 2025-08), the Reference Guide (SP18, 2025-08), the Product Guide (SP18, 2026-01), the
    Feature Guide (SP18, 2026-04), "Tips & Tricks for All File Formats" (SP18, 2026-01) and the release notes. VERIFIED
    (absence): searched for "XLIFF" with "1.2", "2.0", "2.1", "version" and "OASIS". The ISB standard A734 names none either.
    What the documents do say, in the file-format reference
    (https://www.star-group.net/-downloads-/document/2024/TransitNXT_Usage_TipsAndTricksForAllFileFormats_ENG.pdf, "XLIFF"):
    > "Available as: Standard function for Transit Freelance Pro and Professional" / "File extensions: *.xliff *.zip" / "Project packages in XLIFF format already contain the language pairs for translation. This means that you do not have to import them"
    Gleichlaut names its files `*.xlf`; a hand-off renames them to `*.xliff` or zips them, since the documented
    extensions are `*.xliff` and `*.zip`. The version question is settled only by a test file in the federal Transit setup.
  - **Packing a Transit project as XLIFF needs STAR CLM.** Feature Guide SP18, released 2026-04, page 8, table "Project
    exchange in XLIFF format". VERIFIED.
    URL: https://www.star-group.net/-downloads-/document/1927/TransitNXT_FeatureGuide_ENG.pdf
    > "Pack project as XLIFF file" — Professional column: "CLM"; legend: "CLM = combined with STAR CLM"
    > "Unpack XLIFF file as project" and "Send back translation as XLIFF file": standard in Freelance Pro and Professional
    The Product Guide SP18 (2026-01) says the same: "Pack Transit projects as XLIFF files" — "CLM"
    (https://www.star-group.net/-downloads-/document/1929/TransitNXT_ProductGuide_ENG.pdf). So Transit on its own receives
    XLIFF and returns the translated XLIFF; it does not start an XLIFF exchange from its own project. That is the direction
    Gleichlaut needs: Gleichlaut writes the XLIFF, Transit unpacks it and packs the translation back.

---

## 8. Effort and staffing

- GPK-S follow-up report "Spezialitätenliste der OKP", 14 November 2023. VERIFIED.
  URL: https://www.parlament.ch/centers/documents/de/Bericht%20der%20GPK-S%20(definitiv)%20vom%2014.11.2023%20D.pdf
  > "Die Zahl der Mitarbeitenden der betroffenen Sektionen ist von 11,8 Vollzeitstellen (VZÄ) im Jahr 2014 auf rund 25 VZÄ im Jahr 2023 gestiegen"
  This figure covers all SL work of the sections concerned, not limitation-text or translation work.
- **Not public: any number on people or hours spent on SL limitation texts or their translation.** The public figures are
  the ~25 FTE above for all SL work of the sections, and (for the federal administration as a whole) about 330 FTE in the
  language services (LeGes 2020/3, https://leges.weblaw.ch/legesissues/2020/3/maschinelle-ubersetz_f92b5ffeea.html: "In den
  Sprachdiensten der Bundesverwaltung arbeiten circa 420 Sprachfachleute (zumeist Übersetzer/innen) auf circa 330
  Vollzeitstellen"). No limitation-specific figure is in the handbook, the GPK-S report or EFK-22608
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
- **Not public: whether insurers (santésuisse, curafutura, SVK members) or Vertrauensärzte rely specifically on the FR or IT
  wording.** What the record shows: the BAG publishes a separate FR and IT file of every limitation (section 4), its ePL page
  names insurers as a target group ("Für Krankenkassen: Klare Grundlage für die Vergütung und Kostenkontrolle"), and the
  ePL project plans that "Drittparteien wie Krankenversicherer die Daten der Listen per Schnittstelle (API) elektronisch beziehen
  können" (https://www.bag.admin.ch/de/elektronische-plattform-leistungen-epl). VERIFIED. No public statement says which
  language version insurers apply.

---

## 10. Public record of translation errors

- **No public record of one.** We found no BAG erratum, no parliamentary question and no court decision about a wrong FR or IT
  translation of an SL limitation. Searches covered BVGer/BGer with "französische Fassung" and Limitierung, "version
  française"/"texte allemand" with "liste des spécialités", Interpellation/Fragestunde with Spezialitätenliste and Übersetzung,
  and the BAG page "Mitteilungen zur SL" (https://www.bag.admin.ch/de/mitteilungen-zur-spezialitaetenliste-sl, searched for
  Korrektur, Berichtigung, Übersetzung, französisch, italienisch and Fehler; no hits; VERIFIED (absence) for that page, re-checked
  2026-10-11).
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
   step today is not public (section 6); the federal default is the language services (SpDV Art. 10). A pilot therefore
   first confirms whether the drafts go to scientific staff, to the BAG Sprachdienste or, through them, to external translators.
2. **Secondary: the congruence question in the triennial review.** The ePL form already asks the ZI whether "die Übersetzungen
   sind kongruent". A checker that flags FR/IT segments that do not reflect the DE text (missing negation, changed number,
   dropped clause) serves both sides: the ZI answering the question, and the BAG staff reviewing the answers. No new process is
   needed: the question is already in the live ePL app strings, and the 2026 review ran in ePL.
3. **Tertiary: hand-off to a language service through Transit.** If translation goes to a federal language service, the
   standard tool is Transit (ISB A734), which unpacks XLIFF projects and packs the translation back; starting an XLIFF
   exchange from a Transit project needs STAR CLM, so the XLIFF has to come from outside, as Gleichlaut's does. Drafts would be
   delivered as XLIFF (renamed `*.xliff` or zipped, the extensions STAR documents) with the DE-old/DE-new context attached.
   STAR's documentation names no XLIFF version, so one test file of each version (1.2 and 2.1) goes through the service's
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
