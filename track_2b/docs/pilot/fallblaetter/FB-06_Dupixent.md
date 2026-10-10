# Fallblatt 06: Dupixent (Zahl)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

| Feld | Inhalt |
|---|---|
| Präparat(e) | Dupixent |
| Limitierung(en), Kennung in der Publikation | `DUPIXENT.02`, `DUPIXENT.02P` |
| Art der Prüfung | Zahl (Wert mit Einheit) |
| Betroffene Sprachfassung(en) | FR |
| Abweichung | Zahl, FR: DE 15 30 · FR — |
| Erstmals festgestellt | bereits im frühesten geprüften Stand 2026 vorhanden (19.02.2026); vorhanden in 9 von 9 geprüften Ständen ab diesem Datum |
| Blinde Einstufung | real: Bedeutung weicht ab (N20: real; N21: real) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit, PREREG R14); keine Einstufung durch das BAG |
| Hinweis | Fall war vor Entwicklung der Prüfregel bekannt (kein unabhängiger Treffer) |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Dupixent» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund N20

- **DE:** … alle zwei Wochen, bei Patienten mit einem Körpergewicht ab **30 kg** bis unter 60 kg in einer Anfangsdosis von 400 mg als sub…
- **FR:** …sous-cutanée toutes les deux semaines, et pour les patients pesant moins de 60 kg à une dose initiale de 400 mg en injection sous- cutanée (deux injections…
- **IT:** …iniezione sottocutanea ogni due settimane, in pazienti con un peso corporeo da **30 kg** a meno di 60 kg a una dose iniziale di 400 mg sotto forma di iniezione…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *FR lacks 15-\<30 kg band and its distinct dosing.*

### Befund N21

- **DE:** … alle zwei Wochen, bei Patienten mit einem Körpergewicht ab **30 kg** bis unter 60 kg in einer Anfangsdosis von 400 mg als sub…
- **FR:** …sous-cutanée toutes les deux semaines, et pour les patients pesant moins de 60 kg à une dose initiale de 400 mg en injection sous- cutanée (deux injections…
- **IT:** …iniezione sottocutanea ogni due settimane, in pazienti con un peso corporeo da **30 kg** a meno di 60 kg a una dose iniziale di 400 mg sotto forma di iniezione…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *FR lacks 15-\<30 kg band; puts all \<60 kg on 400/200 mg dosing.*

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Entscheid | ☐ Abweichung bestätigt, Bedeutung betroffen ☐ Abweichung bestätigt, nur Form ☐ keine Abweichung ☐ weitere Abklärung |
| Massnahme | ☐ Korrektur im ordentlichen Verfahren (Weg durch BAG festzulegen) ☐ Korrektur bei nächster Änderung oder Überprüfung ☐ keine |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befunde N20, N21; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
