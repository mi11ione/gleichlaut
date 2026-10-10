# Fallblatt 11: Forsteo, Movymia, Sondelbay (Zahl, redaktionell)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

| Feld | Inhalt |
|---|---|
| Präparat(e) | Forsteo, Movymia, Sondelbay |
| Limitierung(en), Kennung in der Publikation | `FORSTEO-2` |
| Art der Prüfung | Zahl (Wert mit Einheit), redaktionell (Tippfehler) |
| Betroffene Sprachfassung(en) | IT |
| Abweichung | Zahl, IT: DE 6 · IT —<br>Tippfehler, IT: «se mesi», gemeint «sei mesi» |
| Erstmals festgestellt | bereits im frühesten geprüften Stand 2026 vorhanden (19.02.2026); vorhanden in 9 von 9 geprüften Ständen ab diesem Datum |
| Blinde Einstufung | real: Bedeutung weicht ab (N13: minor; E05: real) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit, PREREG R14); keine Einstufung durch das BAG |
| Hinweis | – |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Forsteo, Movymia, Sondelbay» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund N13

- **DE:** …ebedingten Wirbelkörperfrakturen, die nach einer mindestens **6-monatigen** Therapie mit Calcitonin, SERM (selektiver Oestrog…
- **FR:** …ostéoporotiques documentées radiologiquement, après une thérapie d'au minimum **6 mois** sous Calcitonine, SERM (modulateur sélectif des récepteurs oestrogéniques),…
- **IT:** …vertebrali osteoporotiche documentate radiologicamente, dopo una terapia di almeno se mesi con Calcitonina, SERM (modulatore selettivo del recettore…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *IT 'se mesi' typo; six months intended but number garbled.*

### Befund E05

- **DE:** …osteoporosebedingten Wirbelkörperfrakturen, die nach einer mindestens **6-monatigen** Therapie mit Calcitonin, SERM (selektiver Oestrogen-Rezeptor-Modulator),…
- **FR:** …ostéoporotiques documentées radiologiquement, après une thérapie d'au minimum **6 mois** sous Calcitonine, SERM (modulateur sélectif des récepteurs oestrogéniques),…
- **IT:** …tate radiologicamente, dopo una terapia di almeno **se mesi** con Calcitonina, SERM (modulatore selettivo del r…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *'se mesi' typo drops the six-month duration value.*

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Entscheid | ☐ Abweichung bestätigt, Bedeutung betroffen ☐ Abweichung bestätigt, nur Form ☐ keine Abweichung ☐ weitere Abklärung |
| Massnahme | ☐ Korrektur im ordentlichen Verfahren (Weg durch BAG festzulegen) ☐ Korrektur bei nächster Änderung oder Überprüfung ☐ keine |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befunde N13, E05; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
