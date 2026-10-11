# Fallblatt X2: Beyonttra (Verneinung, Zusatzmodul)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

> **Operator- und Negationsmodul, zuschaltbar.** Dieser Befund stammt aus einer Prüfart, die ihr vorab festgelegtes Präzisionsziel nicht erreicht hat; sie ist im Standardlauf ausgeschaltet. Der Befund wurde von beiden blinden Annotatoren bestätigt und wird deshalb zur Prüfung vorgelegt.

| Feld | Inhalt |
|---|---|
| Präparat(e) | Beyonttra |
| Limitierung(en), Kennung in der Publikation | `BEYONTTRA` |
| Art der Prüfung | Verneinung: Operator- und Negationsmodul, zuschaltbar |
| Betroffene Sprachfassung(en) | IT |
| Abweichung | Verneinung, IT: DE verneint («nicht»), IT nicht |
| Weicht von den beiden anderen ab | IT |
| Erstmals festgestellt | nicht datiert (das Operator- und Negationsmodul wird nicht über frühere Stände datiert) |
| Blinde Einstufung | real: Bedeutung weicht ab (G03: real) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, übereinstimmend; keine Einstufung durch das BAG |
| Hinweis | Operator- und Negationsmodul (zuschaltbar); 31 Befunde im Register, davon 6 bestätigt (eval/results/audit_r15.json) |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Beyonttra» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund G03

- **DE:** BEYONTTRA darf **nicht** mit anderen spezifischen Arzneimitteln zur Behandlung der Transthyretin-Amyloidose (z.B. TTR-Stabilisatoren, TTR-Gen Silencer) kombiniert werden.
- **FR:** BEYONTTRA **ne** doit pas être combiné avec d’autres médicaments spécifiques pour le traitement de l’amylose à transthyrétine (p. ex. stabilisateurs du TTR, agents silencieux du gène TTR).
- **IT:** BEYONTTRA on deve essere combinato con altri medicamenti specifici per il trattamento dell’amiloidosi da transtiretina (ad esempio stabilizzatori del TTR, agenti silenziatori del gene TTR).

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

Quelle: `data/audit/audit_20261006.json`, Befund G03; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
