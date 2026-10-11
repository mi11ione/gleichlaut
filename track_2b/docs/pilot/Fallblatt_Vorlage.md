# Fallblatt [Nr.]: [Präparat] ([Art der Prüfung])

Vorlage. Die ausgefüllten Fallblätter des Laufs vom 06.10.2026 erzeugt `python3 tools/pilot_sheets.py` in
[fallblaetter/](fallblaetter/00_Uebersicht.md): eines je Sachverhalt (Befunde, die dieselbe Abweichung in derselben oder
einer verwandten Limitierung nennen, wie im Register gruppiert) und eines je bestätigtem Befund der experimentellen
Prüfung. Für einen neuen Lauf wird der Generator erneut ausgeführt; die Vorlage dient der manuellen Erfassung.

> Nur bei Befunden der Runde 5: **Operator- und Negationsmodul, zuschaltbar.** Das Modul liefert mehr Kandidaten als die Hauptprüfung
> und ist deshalb zuschaltbar; dieser Befund wurde von beiden blinden Annotatoren bestätigt.

| Feld | Inhalt |
|---|---|
| Präparat(e) | Name wie in der SL |
| Limitierung(en), Kennung in der Publikation | Kennung der Limitierung in der FHIR-Publikation (`ClinicalUseDefinition.id`), z. B. `NEMLUVIO.01` |
| Art der Prüfung | Zahl (Wert mit Einheit) · Einheit · Sprache des Feldes · redaktionell (Tippfehler) · Terminologie · experimentell: Vergleichsoperator, Verneinung, Zahlwort |
| Betroffene Sprachfassung(en) | DE, FR, IT |
| Abweichung | die abweichenden Werte, z. B. «Zahl, IT: DE 8 · IT 4» |
| Weicht von den beiden anderen ab | DE, FR oder IT; «unklar», wenn die dritte Sprache es nicht entscheidet |
| Erstmals festgestellt | erster geprüfter Stand mit dem Befund und der Stand davor ohne ihn; oder «bereits im frühesten geprüften Stand 2026 vorhanden» |
| Blinde Einstufung | real: Bedeutung weicht ab · geringfügig: Form fehlerhaft, Bedeutung erhalten · nicht bestätigt: gleiche Bedeutung |
| Herkunft der Einstufung | blinde Claude-Annotatoren; keine Einstufung durch das BAG |
| Hinweis | z. B. vorbekannter Fall; von der Prüfung als «vermutlich gleichwertig» markiert |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: FHIR-Publikation des Datums auf epl.bag.admin.ch |

## Auszüge

Wörtlich aus der Publikation; die abweichenden Werte **fett**. In jeder Sprache der Satz, den die Satzzuordnung der
Prüfung einander zuordnet (dieselbe Stelle in DE, FR und IT).

### Befund [Kennung]

- **DE:** …
- **FR:** …
- **IT:** …

Einstufung: in einem Satz, z. B. «von beiden blinden Claude-Annotatoren als real bestätigt: die Bedeutung weicht ab».

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Welcher Text ist falsch? | ☐ DE ☐ FR ☐ IT (mehrere möglich; gemessen am Entscheid des BAG) |
| Was ist zu tun? | ☐ Von Amtes wegen berichtigen ☐ Mit der Zulassungsinhaberin in der dreijährlichen Überprüfung aufnehmen ☐ An den Sprachdienst ☐ Keine Massnahme (gleichwertige Formulierung) ☐ Noch unklar – Entscheiddossier prüfen |
| Bemerkung | |
| Visum (Name, Datum) | |
