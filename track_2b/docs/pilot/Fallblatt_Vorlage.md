# Fallblatt [Nr.]: [Präparat] ([Art der Prüfung])

Vorlage. Die ausgefüllten Fallblätter des Laufs vom 06.10.2026 erzeugt `python3 tools/pilot_sheets.py` in
[fallblaetter/](fallblaetter/00_Uebersicht.md): eines je Sachverhalt (Befunde, die dieselbe Abweichung in derselben oder
einer verwandten Limitierung nennen, wie im Register gruppiert) und eines je bestätigtem Befund der experimentellen
Prüfung. Für einen neuen Lauf wird der Generator erneut ausgeführt; die Vorlage dient der manuellen Erfassung.

> Nur bei Befunden der Runde 5: **Experimentelle Prüfung, standardmässig aus.** Die Prüfart hat ihr vorab festgelegtes
> Präzisionsziel nicht erreicht; der Befund wurde von beiden blinden Annotatoren bestätigt.

| Feld | Inhalt |
|---|---|
| Präparat(e) | Name wie in der SL |
| Limitierung(en), Kennung in der Publikation | Kennung der Limitierung in der FHIR-Publikation (`ClinicalUseDefinition.id`), z. B. `NEMLUVIO.01` |
| Art der Prüfung | Zahl (Wert mit Einheit) · Einheit · Sprache des Feldes · redaktionell (Tippfehler) · Terminologie · experimentell: Vergleichsoperator, Verneinung, Zahlwort |
| Betroffene Sprachfassung(en) | DE, FR, IT |
| Abweichung | die abweichenden Werte, z. B. «Zahl, IT: DE 8 · IT 4» |
| Erstmals festgestellt | erster geprüfter Stand mit dem Befund und der Stand davor ohne ihn; oder «bereits im frühesten geprüften Stand 2026 vorhanden» |
| Blinde Einstufung | real: Bedeutung weicht ab · geringfügig: Form fehlerhaft, Bedeutung erhalten · nicht bestätigt: gleiche Bedeutung |
| Herkunft der Einstufung | blinde Claude-Annotatoren; keine Einstufung durch das BAG |
| Hinweis | z. B. vorbekannter Fall; von der Prüfung als «vermutlich gleichwertig» markiert |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: FHIR-Publikation des Datums auf epl.bag.admin.ch |

## Auszüge

Wörtlich aus der Publikation; die abweichenden Werte **fett**.

### Befund [Kennung]

- **DE:** …
- **FR:** …
- **IT:** …

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Entscheid | ☐ Abweichung bestätigt, Bedeutung betroffen ☐ Abweichung bestätigt, nur Form ☐ keine Abweichung ☐ weitere Abklärung |
| Massnahme | ☐ Korrektur im ordentlichen Verfahren (Weg durch BAG festzulegen) ☐ Korrektur bei nächster Änderung oder Überprüfung ☐ keine |
| Bemerkung | |
| Visum (Name, Datum) | |
