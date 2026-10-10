# Fallblatt X1: Amvuttra (Vergleichsoperator, experimentell)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

> **Experimentelle Prüfung, standardmässig aus.** Dieser Befund stammt aus einer Prüfart, die ihr vorab festgelegtes Präzisionsziel nicht erreicht hat; sie ist im Standardlauf ausgeschaltet. Der Befund wurde von beiden blinden Annotatoren bestätigt und wird deshalb zur Prüfung vorgelegt.

| Feld | Inhalt |
|---|---|
| Präparat(e) | Amvuttra |
| Limitierung(en), Kennung in der Publikation | `AMVUTTRA.01a` |
| Art der Prüfung | Vergleichsoperator: experimentelle Prüfung, standardmässig aus |
| Betroffene Sprachfassung(en) | FR |
| Abweichung | Vergleichsoperator, FR: DE «\> 10» · FR «≤ 10» |
| Erstmals festgestellt | nicht datiert (die experimentelle Prüfung wird nicht über frühere Stände datiert) |
| Blinde Einstufung | real: Bedeutung weicht ab (O01: real) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, übereinstimmend (PREREG R15); keine Einstufung durch das BAG |
| Hinweis | experimentelle Prüfart; 31 Befunde im Register, davon 6 bestätigt (eval/results/audit_r15.json) |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Amvuttra» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund O01

- **DE:** …n folgende Kriterien eingetreten sein müssen: • NIS-Zunahme **\> 10 Punkte** und • Zunahme im PND-Score um \> 1 Stufe (PND IIIa zu…
- **FR:** …critères suivants sont remplis: - augmentation du score NIS **≤ 10 points**, et - pas d’augmentation du score PND. • après 24 mo…
- **IT:** …mesi devono essere subentrati i seguenti criteri: • aumento del NIS \> 10 punti e • aumento del punteggio PND di \> 1 livello (anche un PND da…

Begründung der blinden Einstufung (Annotator, englisch, unverändert): *Stop criteria: DE "NIS-Zunahme \> 10 Punkte" vs FR "augmentation du score NIS ≤ 10 points"; inverts discontinuation threshold.*

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Entscheid | ☐ Abweichung bestätigt, Bedeutung betroffen ☐ Abweichung bestätigt, nur Form ☐ keine Abweichung ☐ weitere Abklärung |
| Massnahme | ☐ Korrektur im ordentlichen Verfahren (Weg durch BAG festzulegen) ☐ Korrektur bei nächster Änderung oder Überprüfung ☐ keine |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befund O01; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
