# Fallblatt 01: Diaphin (Zahl)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

| Feld | Inhalt |
|---|---|
| Präparat(e) | Diaphin |
| Limitierung(en), Kennung in der Publikation | `DIAPHIN.6-` |
| Art der Prüfung | Zahl (Wert mit Einheit) |
| Betroffene Sprachfassung(en) | IT |
| Abweichung | Zahl, IT: DE 6 · IT 12 |
| Erstmals festgestellt | bereits im frühesten geprüften Stand 2026 vorhanden (19.02.2026); vorhanden in 9 von 9 geprüften Ständen ab diesem Datum |
| Blinde Einstufung | real: Bedeutung weicht ab (N01: real) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit, PREREG R14); keine Einstufung durch das BAG |
| Hinweis | Fall war vor Entwicklung der Prüfregel bekannt (kein unabhängiger Treffer) |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Diaphin» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund N01

- **DE:** …brikabgabepreises zuzüglich dem preisbezogenen Zuschlag von **6%** zuzüglich MWST. Aufgrund spezieller Vertriebsverhältnisse …
- **FR:** …Diaphin sur la base du prix de fabrique, plus la prime relative au prix de **6%**, TVA en sus. En raison de la situation particulière de distribution…
- **IT:** …ezzo di fabbrica, più il supplemento attinente al prezzo di **12%** più la IVA. A causa della situazione particolare della dis…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *Supplement 6% in DE vs 12% in IT.*

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Entscheid | ☐ Abweichung bestätigt, Bedeutung betroffen ☐ Abweichung bestätigt, nur Form ☐ keine Abweichung ☐ weitere Abklärung |
| Massnahme | ☐ Korrektur im ordentlichen Verfahren (Weg durch BAG festzulegen) ☐ Korrektur bei nächster Änderung oder Überprüfung ☐ keine |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befund N01; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
