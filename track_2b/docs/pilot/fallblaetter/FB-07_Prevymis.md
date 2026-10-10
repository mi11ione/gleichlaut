# Fallblatt 07: Prevymis (Zahl, redaktionell)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

| Feld | Inhalt |
|---|---|
| Präparat(e) | Prevymis |
| Limitierung(en), Kennung in der Publikation | `PREVYMIS.01` |
| Art der Prüfung | Zahl (Wert mit Einheit), redaktionell (Tippfehler) |
| Betroffene Sprachfassung(en) | FR |
| Abweichung | Zahl, FR: DE 15 · FR 5<br>Tippfehler, FR: «de15», gemeint «de 15» |
| Erstmals festgestellt | bereits im frühesten geprüften Stand 2026 vorhanden (19.02.2026); vorhanden in 9 von 9 geprüften Ständen ab diesem Datum |
| Blinde Einstufung | geringfügig: Form fehlerhaft, Bedeutung erhalten (N04: not; E04: minor) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit, PREREG R14); keine Einstufung durch das BAG |
| Hinweis | – |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Prevymis» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund N04

- **DE:** … 30 kg und für pädiatrische Patienten mit einem Gewicht von **15 kg** bis unter 30 kg für eine Verabreichung ohne Ciclosporin,…
- **FR:** …s 30 kg, ainsi que chez les patients pédiatriques pesant de15 kg à moins de 30 kg pour une administration sans ciclospori…
- **IT:** …almeno 30 kg, nonché nei pazienti pediatrici con un peso compreso tra **15 kg** e meno di 30 kg per una somministrazione senza ciclosporina, che…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *'de15' tokenisation artefact; 15 kg present in FR.*

### Befund E04

- **DE:** …mindestens 30 kg und für pädiatrische Patienten mit einem Gewicht von **15 kg** bis unter 30 kg für eine Verabreichung ohne Ciclosporin, die CMV-seropositive…
- **FR:** …, ainsi que chez les patients pédiatriques pesant **de15 kg** à moins de 30 kg pour une administration sans …
- **IT:** …almeno 30 kg, nonché nei pazienti pediatrici con un peso compreso tra **15 kg** e meno di 30 kg per una somministrazione senza ciclosporina, che…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *'de15' missing space; cosmetic typo.*

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Entscheid | ☐ Abweichung bestätigt, Bedeutung betroffen ☐ Abweichung bestätigt, nur Form ☐ keine Abweichung ☐ weitere Abklärung |
| Massnahme | ☐ Korrektur im ordentlichen Verfahren (Weg durch BAG festzulegen) ☐ Korrektur bei nächster Änderung oder Überprüfung ☐ keine |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befunde N04, E04; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
