# Fallblatt 14: Keytruda (Sprache des Feldes)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

| Feld | Inhalt |
|---|---|
| Präparat(e) | Keytruda |
| Limitierung(en), Kennung in der Publikation | `KEYTRUDA.07---Inj-L-s---Urothelkarzinom--Monotherapie--KN045` |
| Art der Prüfung | Sprache des Feldes |
| Betroffene Sprachfassung(en) | IT |
| Abweichung | Sprache, IT: das IT-Feld ist in FR verfasst |
| Erstmals festgestellt | erstmals am 01.08.2026, nicht vorhanden am 01.07.2026; vorhanden in 4 von 4 geprüften Ständen ab diesem Datum |
| Blinde Einstufung | real: Bedeutung weicht ab (L01: real) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit, PREREG R14); keine Einstufung durch das BAG |
| Hinweis | – |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Keytruda» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund L01

- **DE:** Urothelkarzinom (Monotherapie) KN045 (mit Preismodell) Als Monotherapie zur Behandlung des lokal fortgeschrittenen…
- **FR:** Carcinome urothélial (monothérapie) KN045 (avec modèle de prix) Monothérapie du carcinome urothélial localement…
- **IT:** Carcinome urothélial (monothérapie) KN045 (avec modèle de prix) Monothérapie du carcinome urothélial localement avancé ou métastatique chez les adultes ayant ét…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *Italian field contains the French text verbatim.*

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Entscheid | ☐ Abweichung bestätigt, Bedeutung betroffen ☐ Abweichung bestätigt, nur Form ☐ keine Abweichung ☐ weitere Abklärung |
| Massnahme | ☐ Korrektur im ordentlichen Verfahren (Weg durch BAG festzulegen) ☐ Korrektur bei nächster Änderung oder Überprüfung ☐ keine |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befund L01; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
