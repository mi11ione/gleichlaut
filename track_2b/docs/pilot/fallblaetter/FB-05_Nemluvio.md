# Fallblatt 05: Nemluvio (Zahl)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

| Feld | Inhalt |
|---|---|
| Präparat(e) | Nemluvio |
| Limitierung(en), Kennung in der Publikation | `NEMLUVIO.01` |
| Art der Prüfung | Zahl (Wert mit Einheit) |
| Betroffene Sprachfassung(en) | IT |
| Abweichung | Zahl, IT: DE 8 · IT 4 |
| Erstmals festgestellt | bereits im frühesten geprüften Stand 2026 vorhanden (19.02.2026); vorhanden in 9 von 9 geprüften Ständen ab diesem Datum |
| Blinde Einstufung | real: Bedeutung weicht ab (N18: real) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit, PREREG R14); keine Einstufung durch das BAG |
| Hinweis | Fall war vor Entwicklung der Prüfregel bekannt (kein unabhängiger Treffer) |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Nemluvio» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund N18

- **DE:** …iner Erhaltungsdosis von 30 mg als subkutane Injektion alle **acht Wochen**, zur Behandlung erwachsener und jugendlicher Patient…
- **FR:** …quatre semaines jusqu'à la semaine 16, puis d'une dose d'entretien de 30 mg par la suite, en injection sous-cutanée toutes les **huit semaines**,…
- **IT:** …fino alla settimana 16 e successivamente in una dose di mantenimento di 30 mg come iniezione sottocutanea ogni **quattro settimane**, per il trattamento…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *Maintenance every eight weeks (DE) vs every four weeks (IT).*

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Entscheid | ☐ Abweichung bestätigt, Bedeutung betroffen ☐ Abweichung bestätigt, nur Form ☐ keine Abweichung ☐ weitere Abklärung |
| Massnahme | ☐ Korrektur im ordentlichen Verfahren (Weg durch BAG festzulegen) ☐ Korrektur bei nächster Änderung oder Überprüfung ☐ keine |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befund N18; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
