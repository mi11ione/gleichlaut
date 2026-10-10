# Fallblatt 04: Cresemba (Zahl)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

| Feld | Inhalt |
|---|---|
| Präparat(e) | Cresemba |
| Limitierung(en), Kennung in der Publikation | `CRESE.Kps.IM` |
| Art der Prüfung | Zahl (Wert mit Einheit) |
| Betroffene Sprachfassung(en) | FR |
| Abweichung | Zahl, FR: DE 16 · FR — |
| Erstmals festgestellt | bereits im frühesten geprüften Stand 2026 vorhanden (19.02.2026); vorhanden in 9 von 9 geprüften Ständen ab diesem Datum |
| Blinde Einstufung | real: Bedeutung weicht ab (N09: real) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit, PREREG R14); keine Einstufung durch das BAG |
| Hinweis | Fall war vor Entwicklung der Prüfregel bekannt (kein unabhängiger Treffer) |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Cresemba» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund N09

- **DE:** …ter von 6 Jahren und mit einem Körpergewicht von mindestens **16 kg** vergütet.
- **FR:** …concomitante chez les adultes et les patients pédiatriques à partir de 6 ans.
- **IT:** …moderata a grave negli adulti e nei pazienti pediatrici a partire dai 6 anni di età e con un peso corporeo di almeno **16 kg**.

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *FR omits minimum body weight 16 kg for paediatric patients.*

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Entscheid | ☐ Abweichung bestätigt, Bedeutung betroffen ☐ Abweichung bestätigt, nur Form ☐ keine Abweichung ☐ weitere Abklärung |
| Massnahme | ☐ Korrektur im ordentlichen Verfahren (Weg durch BAG festzulegen) ☐ Korrektur bei nächster Änderung oder Überprüfung ☐ keine |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befund N09; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
