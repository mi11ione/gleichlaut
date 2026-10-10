# Fallblatt 15: Dupixent (redaktionell)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

| Feld | Inhalt |
|---|---|
| Präparat(e) | Dupixent |
| Limitierung(en), Kennung in der Publikation | `DUPIXENT.07`, `DUPIXENT.07P` |
| Art der Prüfung | redaktionell (Tippfehler) |
| Betroffene Sprachfassung(en) | FR |
| Abweichung | Tippfehler, FR: «de15», gemeint «de 15» |
| Erstmals festgestellt | bereits im frühesten geprüften Stand 2026 vorhanden (19.02.2026); vorhanden in 9 von 9 geprüften Ständen ab diesem Datum |
| Blinde Einstufung | geringfügig: Form fehlerhaft, Bedeutung erhalten (E02: minor; E03: minor) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit, PREREG R14); keine Einstufung durch das BAG |
| Hinweis | – |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Dupixent» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund E02

- **DE:** …Injektion alle vier Wochen und bei Patienten mit einem Körpergewicht unter **15 kg** in einer Anfangsdosis von 200 mg als subkutane Injektion, gefolgt…
- **FR:** …uatre semaines, et chez les patients pesant moins **de15 kg** à une dose initiale de 200 mg en injection sou…
- **IT:** …sottocutanea ogni quattro settimane, e nei pazienti con peso corporeo inferiore a **15 kg** con una dose iniziale di 200 mg sotto forma di iniezione sottocutanea,…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *'moins de15' missing space; cosmetic.*

### Befund E03

- **DE:** …Injektion alle vier Wochen und bei Patienten mit einem Körpergewicht unter **15 kg** in einer Anfangsdosis von 200 mg als subkutane Injektion, gefolgt…
- **FR:** …uatre semaines, et chez les patients pesant moins **de15 kg** à une dose initiale de 200 mg en injection sou…
- **IT:** …sottocutanea ogni quattro settimane, e nei pazienti con peso corporeo inferiore a **15 kg** con una dose iniziale di 200 mg sotto forma di iniezione sottocutanea,…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *'moins de15' missing space; cosmetic.*

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Entscheid | ☐ Abweichung bestätigt, Bedeutung betroffen ☐ Abweichung bestätigt, nur Form ☐ keine Abweichung ☐ weitere Abklärung |
| Massnahme | ☐ Korrektur im ordentlichen Verfahren (Weg durch BAG festzulegen) ☐ Korrektur bei nächster Änderung oder Überprüfung ☐ keine |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befunde E02, E03; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
