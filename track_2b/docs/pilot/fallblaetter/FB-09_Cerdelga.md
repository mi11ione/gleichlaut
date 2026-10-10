# Fallblatt 09: Cerdelga (Zahl)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

| Feld | Inhalt |
|---|---|
| Präparat(e) | Cerdelga |
| Limitierung(en), Kennung in der Publikation | `CERDELGA` |
| Art der Prüfung | Zahl (Wert mit Einheit) |
| Betroffene Sprachfassung(en) | FR, IT |
| Abweichung | Zahl, FR: DE 18 · FR —<br>Zahl, IT: DE 18 · IT — |
| Erstmals festgestellt | bereits im frühesten geprüften Stand 2026 vorhanden (19.02.2026); vorhanden in 9 von 9 geprüften Ständen ab diesem Datum |
| Blinde Einstufung | nicht bestätigt: gleiche Bedeutung (N07: not; N08: not) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit, PREREG R14); keine Einstufung durch das BAG |
| Hinweis | Prüfung selbst markiert «vermutlich gleichwertige Formulierung» (nur Triage) |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Cerdelga» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund N07

- **DE:** Zur Monotherapie bei erwachsenen Patienten ab **18 Jahren** mit gesicherter Diagnose eines Morbus Gaucher Typ I,…
- **FR:** Pour la monothérapie chez les patients adultes atteints d’une maladie de Gaucher de type I diagnostiquée de manière avérée,…
- **IT:** Per la monoterapia di pazienti adulti con malattia di Gaucher di tipo I che sono metabolizzatori lenti (poor metabolizers,…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *"adultes" equals "ab 18 Jahren" (DE redundant); same condition.*

### Befund N08

- **DE:** Zur Monotherapie bei erwachsenen Patienten ab **18 Jahren** mit gesicherter Diagnose eines Morbus Gaucher Typ I,…
- **FR:** Pour la monothérapie chez les patients adultes atteints d’une maladie de Gaucher de type I diagnostiquée de manière avérée,…
- **IT:** Per la monoterapia di pazienti adulti con malattia di Gaucher di tipo I che sono metabolizzatori lenti (poor metabolizers,…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *"adulti" equals "ab 18 Jahren"; same condition.*

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Entscheid | ☐ Abweichung bestätigt, Bedeutung betroffen ☐ Abweichung bestätigt, nur Form ☐ keine Abweichung ☐ weitere Abklärung |
| Massnahme | ☐ Korrektur im ordentlichen Verfahren (Weg durch BAG festzulegen) ☐ Korrektur bei nächster Änderung oder Überprüfung ☐ keine |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befunde N07, N08; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
