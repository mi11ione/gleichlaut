# Fallblatt X2: Beyonttra (Verneinung, experimentell)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

> **Experimentelle Prüfung, standardmässig aus.** Dieser Befund stammt aus einer Prüfart, die ihr vorab festgelegtes Präzisionsziel nicht erreicht hat; sie ist im Standardlauf ausgeschaltet. Der Befund wurde von beiden blinden Annotatoren bestätigt und wird deshalb zur Prüfung vorgelegt.

| Feld | Inhalt |
|---|---|
| Präparat(e) | Beyonttra |
| Limitierung(en), Kennung in der Publikation | `BEYONTTRA` |
| Art der Prüfung | Verneinung: experimentelle Prüfung, standardmässig aus |
| Betroffene Sprachfassung(en) | IT |
| Abweichung | Verneinung, IT: DE verneint («nicht»), IT nicht |
| Erstmals festgestellt | nicht datiert (die experimentelle Prüfung wird nicht über frühere Stände datiert) |
| Blinde Einstufung | real: Bedeutung weicht ab (G03: real) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, übereinstimmend (PREREG R15); keine Einstufung durch das BAG |
| Hinweis | experimentelle Prüfart; 31 Befunde im Register, davon 6 bestätigt (eval/results/audit_r15.json) |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Beyonttra» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund G03

- **DE:** BEYONTTRA darf **nicht** mit anderen spezifischen Arzneimitteln zur Behandlung der Transthyretin-Amyloidose (z.B. TTR-Stabilisatoren, TTR-Gen Silencer) kombiniert werden.
- **FR:** …filtration glomérulaire \< 25 ml/min/1,73 m2. BEYONTTRA ne doit pas être combiné avec d’autres médicaments spécifiques pour le traitement de l’amylose…
- **IT:** BEYONTTRA on deve essere combinato con altri medicamenti specifici per il trattamento dell’amiloidosi da transtiretina (ad esempio stabilizzatori del TTR, agenti silenziatori del gene TTR).

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *IT "BEYONTTRA on deve essere combinato" (typo for non) vs DE "darf nicht ... kombiniert werden"; prohibition literally lost.*

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Entscheid | ☐ Abweichung bestätigt, Bedeutung betroffen ☐ Abweichung bestätigt, nur Form ☐ keine Abweichung ☐ weitere Abklärung |
| Massnahme | ☐ Korrektur im ordentlichen Verfahren (Weg durch BAG festzulegen) ☐ Korrektur bei nächster Änderung oder Überprüfung ☐ keine |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befund G03; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
