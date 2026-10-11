# Fallblatt 18: Jemperli, Opzelura (Terminologie)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

| Feld | Inhalt |
|---|---|
| Präparat(e) | Jemperli, Opzelura |
| Limitierung(en), Kennung in der Publikation | `JEMPERLI.01---Endometriumkarzinom-Mono`, `JEMPERLI.02---Endometriumkarzinom-Kombi`, `OPZELURA.01---Vitiligo-Erwachsene-und-Jugendliche-ab-12-Jahren` |
| Art der Prüfung | Terminologie (von BAG anderswo korrigierter Begriff) |
| Betroffene Sprachfassung(en) | FR |
| Abweichung | Terminologie, FR: steht «limitation doit être communiqué à l’assureur-maladie», von BAG anderswo ersetzt durch «limitation doit être transmis à l'assureur-maladie» |
| Weicht von den beiden anderen ab | FR |
| Erstmals festgestellt | erstmals am 01.08.2026, nicht vorhanden am 01.07.2026; vorhanden in 4 von 4 geprüften Ständen ab diesem Datum |
| Blinde Einstufung | geringfügig: Form fehlerhaft, Bedeutung erhalten (T09: minor; T10: minor; T11: minor) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit); keine Einstufung durch das BAG |
| Hinweis | – |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Jemperli» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund T09

- **DE:** …Der Indikationscode dieser Limitierung ist an den Krankenversicherer zu übermitteln.
- **FR:** …t de l'administration. Le code d’indication relatif à cette **limitation doit être communiqué à l’assureur-maladie**.
- **IT:** …Il codice di indicazione relativo a questa limitazione deve essere trasmesso alla cassa malati.

Einstufung: von beiden blinden Claude-Annotatoren als geringfügig bestätigt: die Form ist fehlerhaft, die Bedeutung erhalten.

### Befund T10

- **DE:** …Der Indikationscode dieser Limitierung ist an den Krankenversicherer zu übermitteln.
- **FR:** …t de l’administration. Le code d’indication relatif à cette **limitation doit être communiqué à l’assureur-maladie**.
- **IT:** …Il codice di indicazione relativo a questa limitazione deve essere trasmesso alla cassa malati.

Einstufung: von beiden blinden Claude-Annotatoren als geringfügig bestätigt: die Form ist fehlerhaft, die Bedeutung erhalten.

### Befund T11

- **DE:** …Der Indikationscode dieser Limitierung ist an den Krankenversicherer zu übermitteln.
- **FR:** …e est remboursé. Le code d’indication correspondant à cette **limitation doit être communiqué à l’assureur-maladie**.
- **IT:** …Il codice di indicazione corrispondente a tale limitazione deve essere comunicato all’assicuratore malattia.

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

Quelle: `data/audit/audit_20261006.json`, Befunde T09, T10, T11; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
