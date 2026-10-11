# Fallblatt 15: Dupixent (redaktionell)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

| Feld | Inhalt |
|---|---|
| Präparat(e) | Dupixent |
| Limitierung(en), Kennung in der Publikation | `DUPIXENT.07`, `DUPIXENT.07P` |
| Art der Prüfung | redaktionell (Tippfehler) |
| Betroffene Sprachfassung(en) | FR |
| Abweichung | Tippfehler, FR: «de15», gemeint «de 15» |
| Weicht von den beiden anderen ab | FR |
| Erstmals festgestellt | bereits im frühesten geprüften Stand 2026 vorhanden (19.02.2026); vorhanden in 9 von 9 geprüften Ständen ab diesem Datum |
| Blinde Einstufung | geringfügig: Form fehlerhaft, Bedeutung erhalten (E02: minor; E03: minor) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit); keine Einstufung durch das BAG |
| Hinweis | – |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Dupixent» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund E02

- **DE:** …Injektion alle vier Wochen und bei Patienten mit einem Körpergewicht unter **15 kg** in einer Anfangsdosis von 200 mg als subkutane Injektion, gefolgt…
- **FR:** …uatre semaines, et chez les patients pesant moins **de15 kg** à une dose initiale de 200 mg en injection sou…
- **IT:** …sottocutanea ogni quattro settimane, e nei pazienti con peso corporeo inferiore a **15 kg** con una dose iniziale di 200 mg sotto forma di iniezione sottocutanea,…

Einstufung: von beiden blinden Claude-Annotatoren als geringfügig bestätigt: die Form ist fehlerhaft, die Bedeutung erhalten.

### Befund E03

- **DE:** …Injektion alle vier Wochen und bei Patienten mit einem Körpergewicht unter **15 kg** in einer Anfangsdosis von 200 mg als subkutane Injektion, gefolgt…
- **FR:** …uatre semaines, et chez les patients pesant moins **de15 kg** à une dose initiale de 200 mg en injection sou…
- **IT:** …sottocutanea ogni quattro settimane, e nei pazienti con peso corporeo inferiore a **15 kg** con una dose iniziale di 200 mg sotto forma di iniezione sottocutanea,…

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

Quelle: `data/audit/audit_20261006.json`, Befunde E02, E03; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
