# Fallblatt 08: Beyfortus (Zahl)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

| Feld | Inhalt |
|---|---|
| Präparat(e) | Beyfortus |
| Limitierung(en), Kennung in der Publikation | `BEYFORTUS.01` |
| Art der Prüfung | Zahl (Wert mit Einheit) |
| Betroffene Sprachfassung(en) | FR |
| Abweichung | Zahl, FR: DE 14 · FR — |
| Weicht von den beiden anderen ab | FR |
| Erstmals festgestellt | bereits im frühesten geprüften Stand 2026 vorhanden (19.02.2026); vorhanden in 9 von 9 geprüften Ständen ab diesem Datum |
| Blinde Einstufung | nicht bestätigt: gleiche Bedeutung (N06: not) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit); keine Einstufung durch das BAG |
| Hinweis | Prüfung selbst markiert «vermutlich gleichwertige Formulierung» (nur Triage) |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Beyfortus» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund N06

- **DE:** …en; ausgenommen sind folgende Fälle: – Geburt innerhalb von **14 Tagen** nach Verabreichung der Impfung, – Frühgeburt vor 37 W…
- **FR:** …– la naissance a lieu dans les deux semaines suivant l’administration du vaccin, – accouchement prématuré avant 37 semaines de…
- **IT:** …- la nascita avviene entro **14 giorni** dalla somministrazione del vaccino; - si verifica un parto prematuro prima della 37a settimana di età gestazionale;…

Einstufung: von beiden blinden Claude-Annotatoren nicht bestätigt: gleiche Bedeutung.

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Welcher Text ist falsch? | ☐ DE ☐ FR ☐ IT (mehrere möglich; gemessen am Entscheid des BAG) |
| Was ist zu tun? | ☐ Von Amtes wegen berichtigen ☐ Mit der Zulassungsinhaberin in der dreijährlichen Überprüfung aufnehmen ☐ An den Sprachdienst ☐ Keine Massnahme (gleichwertige Formulierung) ☐ Noch unklar – Entscheiddossier prüfen |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befund N06; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
