# Fallblatt X3: Deca (Verneinung, Zusatzmodul)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

> **Operator- und Negationsmodul, zuschaltbar.** Dieser Befund stammt aus einer Prüfart, die ihr vorab festgelegtes Präzisionsziel nicht erreicht hat; sie ist im Standardlauf ausgeschaltet. Der Befund wurde von beiden blinden Annotatoren bestätigt und wird deshalb zur Prüfung vorgelegt.

| Feld | Inhalt |
|---|---|
| Präparat(e) | Deca |
| Limitierung(en), Kennung in der Publikation | `DECADURABOL2` |
| Art der Prüfung | Verneinung: Operator- und Negationsmodul, zuschaltbar |
| Betroffene Sprachfassung(en) | IT |
| Abweichung | Verneinung, IT: IT verneint («inefficaci»), DE nicht |
| Weicht von den beiden anderen ab | unklar (die dritte Sprache entscheidet es nicht) |
| Erstmals festgestellt | nicht datiert (das Operator- und Negationsmodul wird nicht über frühere Stände datiert) |
| Blinde Einstufung | geringfügig: Form fehlerhaft, Bedeutung erhalten (G04: minor) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, übereinstimmend; keine Einstufung durch das BAG |
| Hinweis | Operator- und Negationsmodul (zuschaltbar); 31 Befunde im Register, davon 6 bestätigt (eval/results/audit_r15.json) |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Deca» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund G04

- **DE:** Vergütung ausschliesslich bei schwerer postmenopausaler Osteoporose, wenn andere Therapieoptionen ausgeschöpft wurden.
- **FR:** Prise en charge exclusivement pour le traitement de l’ostéoporose postménopausique sévère, lorsque d’autres options thérapeutiques ont été épuisées.
- **IT:** Rimborso esclusivamente per il trattamento dell’osteoporosi post-menopausale grave, nel caso in cui altre opzioni terapeutiche si siano rivelate **inefficaci**.

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

Quelle: `data/audit/audit_20261006.json`, Befund G04; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
