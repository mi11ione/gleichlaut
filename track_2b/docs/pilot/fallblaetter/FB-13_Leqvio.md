# Fallblatt 13: Leqvio (Zahl, redaktionell)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

| Feld | Inhalt |
|---|---|
| Präparat(e) | Leqvio |
| Limitierung(en), Kennung in der Publikation | `LEQVIO.01` |
| Art der Prüfung | Zahl (Wert mit Einheit), redaktionell (Tippfehler) |
| Betroffene Sprachfassung(en) | DE, FR, IT |
| Abweichung | Zahl, FR: DE 4 · FR 1.4<br>Zahl, IT: DE 4 · IT 1.4<br>Tippfehler, DE: «1 .4», gemeint «1.4» |
| Weicht von den beiden anderen ab | DE |
| Erstmals festgestellt | bereits im frühesten geprüften Stand 2026 vorhanden (19.02.2026); vorhanden in 9 von 9 geprüften Ständen ab diesem Datum |
| Blinde Einstufung | geringfügig: Form fehlerhaft, Bedeutung erhalten (N16: not; N17: not; E01: minor) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit); keine Einstufung durch das BAG |
| Hinweis | – |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Leqvio» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund N16

- **DE:** …it einem PCSK9-Inhibitor oder ein LDL-C Wert von kleiner 1 .**4 mmol**/l erreicht werden. Die Vergütung in Kombination mit de…
- **FR:** …traitement par un inhibiteur de PCSK9 ou une valeur de LDL-C inférieure à **1.4 mmol**/l doit être atteinte.…
- **IT:** …trattamento con l’inibitore PCSK9 o un valore di colesterolo LDC inferiore a **1,4 mmol**/l.…

Einstufung: von beiden blinden Claude-Annotatoren nicht bestätigt: gleiche Bedeutung.

### Befund N17

- **DE:** …it einem PCSK9-Inhibitor oder ein LDL-C Wert von kleiner 1 .**4 mmol**/l erreicht werden. Die Vergütung in Kombination mit de…
- **FR:** …traitement par un inhibiteur de PCSK9 ou une valeur de LDL-C inférieure à **1.4 mmol**/l doit être atteinte.…
- **IT:** …trattamento con l’inibitore PCSK9 o un valore di colesterolo LDC inferiore a **1,4 mmol**/l.…

Einstufung: von beiden blinden Claude-Annotatoren nicht bestätigt: gleiche Bedeutung.

### Befund E01

- **DE:** …m PCSK9-Inhibitor oder ein LDL-C Wert von kleiner **1 .4 mmol**/l erreicht werden. Die Vergütung in Kombinat…
- **FR:** …traitement par un inhibiteur de PCSK9 ou une valeur de LDL-C inférieure à **1.4 mmol**/l doit être atteinte.…
- **IT:** …trattamento con l’inibitore PCSK9 o un valore di colesterolo LDC inferiore a **1,4 mmol**/l.…

Einstufung: von beiden blinden Claude-Annotatoren als geringfügig bestätigt: die Form ist fehlerhaft, die Bedeutung erhalten.

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Welcher Text ist falsch? | ☐ DE ☐ FR ☐ IT (mehrere möglich; gemessen am Entscheid des BAG) |
| Was ist zu tun? | ☐ Von Amtes wegen berichtigen ☐ Mit der Zulassungsinhaberin in der dreijährlichen Überprüfung aufnehmen ☐ An den Sprachdienst ☐ Keine Massnahme (gleichwertige Formulierung) ☐ Noch unklar – Entscheiddossier prüfen |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befunde N16, N17, E01; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
