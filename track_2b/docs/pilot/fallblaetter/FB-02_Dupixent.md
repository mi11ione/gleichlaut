# Fallblatt 02: Dupixent (Zahl)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

| Feld | Inhalt |
|---|---|
| Präparat(e) | Dupixent |
| Limitierung(en), Kennung in der Publikation | `DUPIXENT.05P`, `DUPIXENT.05a` |
| Art der Prüfung | Zahl (Wert mit Einheit) |
| Betroffene Sprachfassung(en) | FR |
| Abweichung | Zahl, FR: DE 15 · FR 30 |
| Weicht von den beiden anderen ab | FR |
| Erstmals festgestellt | erstmals am 01.06.2026, nicht vorhanden am 01.04.2026; vorhanden in 6 von 6 geprüften Ständen ab diesem Datum |
| Blinde Einstufung | real: Bedeutung weicht ab (N02: real; N03: real) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit); keine Einstufung durch das BAG |
| Hinweis | Fall war vor Entwicklung der Prüfregel bekannt (kein unabhängiger Treffer) |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Dupixent» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund N02

- **DE:** …ierung von 300 mg alle 4 Wochen bei einem Körpergewicht von **15** - \< 60 kg, bzw. von 200 mg alle 2 Wochen bei einem Körperge…
- **FR:** …e de 300 mg toutes les 4 semaines pour un poids corporel de **30 kg** à moins de 60 kg, ou de 200 mg toutes les 2 semaines pou…
- **IT:** …Come terapia aggiuntiva con una dose di 300 mg ogni 4 settimane per un peso corporeo di **15** - \< 60 kg, o di 200 mg ogni 2 settimane per un peso corporeo di 60 kg o più, nei bambini da 6 a 11 anni di età con asma grave di tipo 2 caratterizzata dai seguenti criteri:…

Einstufung: von beiden blinden Claude-Annotatoren als real bestätigt: die Bedeutung weicht ab.

### Befund N03

- **DE:** …ierung von 300 mg alle 4 Wochen bei einem Körpergewicht von **15** - \< 60 kg, bzw. von 200 mg alle 2 Wochen bei einem Körperge…
- **FR:** …e de 300 mg toutes les 4 semaines pour un poids corporel de **30 kg** à moins de 60 kg, ou de 200 mg toutes les 2 semaines pou…
- **IT:** …Come terapia aggiuntiva con una dose di 300 mg ogni 4 settimane per un peso corporeo di **15** - \< 60 kg, o di 200 mg ogni 2 settimane per un peso corporeo di 60 kg o più, nei bambini da 6 a 11 anni di età con asma grave di tipo 2 caratterizzata dai seguenti criteri:…

Einstufung: von beiden blinden Claude-Annotatoren als real bestätigt: die Bedeutung weicht ab.

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Welcher Text ist falsch? | ☐ DE ☐ FR ☐ IT (mehrere möglich; gemessen am Entscheid des BAG) |
| Was ist zu tun? | ☐ Von Amtes wegen berichtigen ☐ Mit der Zulassungsinhaberin in der dreijährlichen Überprüfung aufnehmen ☐ An den Sprachdienst ☐ Keine Massnahme (gleichwertige Formulierung) ☐ Noch unklar – Entscheiddossier prüfen |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befunde N02, N03; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
