# Notiz an die Sektionsleitung: Sprachfassungen der SL-Limitierungen, Prüfung vom 6. Oktober 2026

Stand 11.10.2026. Entwurf; Adressat und Absender «durch BAG zu ergänzen». Der Antrag steht auf einer Seite in der
[Entscheidvorlage](Entscheidvorlage_Phase1.md).

## Worum es geht

Ein Programm hat alle 1688 Limitierungen der SL-Publikation vom 6. Oktober 2026 in DE, FR und IT verglichen: Zahlen,
Sprache des Feldes, Tippfehler und Begriffe, die das BAG anderswo bereits korrigiert hat. Es liest nur die öffentliche
Publikation und ruft kein Sprachmodell auf. Ergebnis: **38 Befunde** auf 27 Limitierungen, zusammengefasst in
18 Sachverhalten. Die Einstufung stammt von **blinden Claude-Annotatoren** (zwei, ein dritter bei Uneinigkeit), nicht
vom BAG: **16 real** (die Bedeutung weicht ab), **12 geringfügig** (Form fehlerhaft, Bedeutung erhalten),
**10 nicht bestätigt** (`eval/results/audit_relabel.json`).

Die Zahlen auf einen Blick (`eval/results/audit_grouping.json`, Abschnitt `reconciliation`; bestätigt = von der
Mehrheit der blinden Annotatoren als real oder geringfügig eingestuft):

| | Anzahl | bestätigt | real (Bedingung weicht ab) | geringfügig | nicht bestätigt |
|---|---|---|---|---|---|
| Befunde (Zahl, Einheit, Sprache, Tippfehler) | 27 | 17 | 12 | 5 | 10 |
| Terminologie-Hinweise | 11 | 11 | 4 | 7 | 0 |
| **Total im Register** | **38** | **28** | **16** | **12** | **10** |
| Experimentelle Prüfung (aus, separat geführt) | 31 | 6 | 3 | 3 | 25 |

Im Register ergeben die 38 Befunde und Hinweise 18 Sachverhalte (Fälle), gruppiert nach der Einstufung der
Annotatoren; die 4 Fälle, die sie nicht bestätigt haben (darunter die 3 vermutlich gleichwertigen Formulierungen), sind
eingeklappt. Die Befunde der experimentellen Prüfung gehören nicht zu den 18 Fällen und werden im
Register separat gezählt.

## Abweichungen in der Bedeutung (real)

- **Nemluvio** (IT): Erhaltungsdosis DE alle acht Wochen, IT alle vier Wochen («ogni quattro settimane»).
- **Diaphin** (IT): preisbezogener Zuschlag DE 6 %, IT 12 %.
- **Cresemba** (FR): DE verlangt ein Körpergewicht von mindestens 16 kg; FR nennt keines.
- **Dupixent** (FR, 4 Limitierungen): DE 15 bis < 60 kg, FR 30 bis < 60 kg; in zwei weiteren fehlt in FR die
  Gewichtsklasse 15 bis < 30 kg. Zwei der vier Abweichungen erscheinen erstmals im Stand vom 1. Juni 2026.
- **Etanercept** (Benepali, Erelzi, Nepexto; FR): FR schränkt die juvenile Arthritis auf Patientinnen und Patienten
  ab 62,5 kg ein; DE nicht.
- Weitere: **Keytruda** (KN045): das IT-Feld enthält den französischen Text, seit dem Stand vom 1. August 2026.
  **Perindopril-Kombinationen** (4 Limitierungen, FR): «inhibiteur de l'enzyme de conversion» (ACE-Hemmer), wo eine
  andere Wirkstoffklasse gemeint ist (Angiotensin-II-Antagonist); das BAG hat die Wendung in anderen Limitierungen
  bereits ersetzt. **Forsteo** (IT): «almeno se mesi» statt «sei mesi».

## Experimentelle Prüfung (standardmässig aus)

Eine zusätzliche Prüfung von Vergleichsoperatoren, Verneinungen und Zahlwörtern hat ihr vorab festgelegtes
Präzisionsziel verfehlt und ist ausgeschaltet. Von ihren 31 Befunden haben die Annotatoren 6 bestätigt, davon 3 real
(`eval/results/audit_r15.json`):

- **Amvuttra** (FR): Abbruchkriterium DE «NIS-Zunahme > 10 Punkte», FR «≤ 10 points».
- **Beyonttra** und **Vyndaqel** (IT): «on deve essere combinato» statt «non deve»: aus dem Kombinationsverbot wird
  dem Wortlaut nach eine Pflicht.

## Was Phase 1 kostet

Keine Beschaffung, keine Lizenz, kein Modell. Die 24 Fallblätter liegen vor ([Übersicht](fallblaetter/00_Uebersicht.md)).
Aufwand gemäss [adoption.md](../adoption.md) §4, Minutenwerte als *Annahme*: Prüfung der 38 Befunde rund 3–6 h einmalig;
danach rund 1 neuer Befund pro Monat, unter 0,5 h; ein eigener Lauf im BAG rund 0,5 h.

## Risiken

- Die Prüfung findet nicht alles; sie liefert eine Arbeitsliste, keine Bestätigung der Gleichwertigkeit.
- Die Einstufung ist nicht die des BAG; 10 der 38 Befunde haben die Annotatoren verworfen.
- Massgebende Sprachfassung und Korrekturweg einer publizierten Limitierung sind aus öffentlichen Quellen nicht
  bestimmbar; jedes Fallblatt verlangt sie aus dem Dossier.

## Beantragter Entscheid

Freigabe von Phase 1 ([Projektauftrag](Projektauftrag_Phase1.md)): Bezeichnung der Fachverantwortung und der
Prüfenden, Prüfung und Visum der Fallblätter, Weiterleitung der [Schutzbedarfsanalyse](Schutzbedarfsanalyse_Phase1.md)
an die Informationssicherheit.
