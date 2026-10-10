# Fallblatt 13: Leqvio (Zahl, redaktionell)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

| Feld | Inhalt |
|---|---|
| Präparat(e) | Leqvio |
| Limitierung(en), Kennung in der Publikation | `LEQVIO.01` |
| Art der Prüfung | Zahl (Wert mit Einheit), redaktionell (Tippfehler) |
| Betroffene Sprachfassung(en) | DE, FR, IT |
| Abweichung | Zahl, FR: DE 4 · FR 1.4<br>Zahl, IT: DE 4 · IT 1.4<br>Tippfehler, DE: «1 .4», gemeint «1.4» |
| Erstmals festgestellt | bereits im frühesten geprüften Stand 2026 vorhanden (19.02.2026); vorhanden in 9 von 9 geprüften Ständen ab diesem Datum |
| Blinde Einstufung | geringfügig: Form fehlerhaft, Bedeutung erhalten (N16: not; N17: not; E01: minor) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit, PREREG R14); keine Einstufung durch das BAG |
| Hinweis | – |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Leqvio» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund N16

- **DE:** …it einem PCSK9-Inhibitor oder ein LDL-C Wert von kleiner 1 .**4 mmol**/l erreicht werden. Die Vergütung in Kombination mit de…
- **FR:** …hypolipémiant intensif maximal avant le traitement par un inhibiteur de PCSK9 ou une valeur de LDL-C inférieure à **1.4 mmol**/l doit être atteinte. Le…
- **IT:** …trattamento con l’inibitore PCSK9 o un valore di colesterolo LDC inferiore a **1,4 mmol**/l. Si esclude il rimborso in combinazione con l’utilizzo di un…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *DE '1 .4' artefact; FR 1.4 mmol/l matches.*

### Befund N17

- **DE:** …it einem PCSK9-Inhibitor oder ein LDL-C Wert von kleiner 1 .**4 mmol**/l erreicht werden. Die Vergütung in Kombination mit de…
- **FR:** …hypolipémiant intensif maximal avant le traitement par un inhibiteur de PCSK9 ou une valeur de LDL-C inférieure à **1.4 mmol**/l doit être atteinte. Le…
- **IT:** …trattamento con l’inibitore PCSK9 o un valore di colesterolo LDC inferiore a **1,4 mmol**/l. Si esclude il rimborso in combinazione con l’utilizzo di un…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *DE '1 .4' artefact; IT 1,4 mmol/l matches.*

### Befund E01

- **DE:** …m PCSK9-Inhibitor oder ein LDL-C Wert von kleiner **1 .4 mmol**/l erreicht werden. Die Vergütung in Kombinat…
- **FR:** …hypolipémiant intensif maximal avant le traitement par un inhibiteur de PCSK9 ou une valeur de LDL-C inférieure à **1.4 mmol**/l doit être atteinte. Le…
- **IT:** …trattamento con l’inibitore PCSK9 o un valore di colesterolo LDC inferiore a **1,4 mmol**/l. Si esclude il rimborso in combinazione con l’utilizzo di un…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *'1 .4' stray space in German; cosmetic.*

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Entscheid | ☐ Abweichung bestätigt, Bedeutung betroffen ☐ Abweichung bestätigt, nur Form ☐ keine Abweichung ☐ weitere Abklärung |
| Massnahme | ☐ Korrektur im ordentlichen Verfahren (Weg durch BAG festzulegen) ☐ Korrektur bei nächster Änderung oder Überprüfung ☐ keine |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befunde N16, N17, E01; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
