# Projektauftrag (Entwurf): Prüfung der Sprachfassungen der SL-Limitierungen, Phase 1

Entwurf vom 10.10.2026 zur Prüfung durch das BAG. Gliederung in Anlehnung an das HERMES-Ergebnis «Projektauftrag».
Felder mit «durch BAG zu ergänzen» sind bewusst offen; es werden keine Personen oder Zuständigkeiten vorweggenommen.

| | |
|---|---|
| Vorhaben | Gleichlaut, Phase 1: regelbasierte Prüfung der publizierten Limitierungstexte DE/FR/IT, ohne Sprachmodell |
| Auftraggeber/in | «durch BAG zu ergänzen» |
| Fachverantwortung | «durch BAG zu ergänzen» (naheliegend: Sektion Arzneimittelaufnahmen; nicht bestätigt) |
| Projektleitung | «durch BAG zu ergänzen» |
| Prüfende je Präparat | «durch BAG zu ergänzen» (naheliegend: die zugeteilten wissenschaftlichen Mitarbeitenden; nicht bestätigt) |
| Technischer Betrieb (nur Variante B) | «durch BAG zu ergänzen» |
| Informationssicherheit | «durch BAG zu ergänzen» (Informationssicherheitsbeauftragte/r des Amtes) |
| Termine | «durch BAG zu ergänzen» |

## Ausgangslage

Das BAG entscheidet über die Limitierungen der Spezialitätenliste (KVV Art. 73) und publiziert sie in drei
Sprachfassungen auf sl.bag.admin.ch. Die Übereinstimmung der Übersetzungen fragt das BAG heute in der Überprüfung alle
drei Jahre ab, und zwar nicht nur die Kriterien Wirksamkeit, Zweckmässigkeit und Wirtschaftlichkeit (WZW) allgemein: Im
Kapitel Zweckmässigkeit des ePL-Formulars der dreijährlichen Überprüfung beantwortet die Zulassungsinhaberin wörtlich die
Frage «Falls eine Limitierung vorhanden ist, ist diese wissenschaftlich eindeutig und klar verständlich formuliert und
die Übersetzungen sind kongruent?» (Feld `sl.request.expediency.changes.formulationLimitation`, öffentlich in
https://sl.bag.admin.ch/assets/i18n/de.json; Hilfetext: «Ist gegebenenfalls eine Übersetzung missverständlich
formuliert?»). Es ist eine Selbstauskunft der Zulassungsinhaberin; eine Prüfung durch das BAG selbst ist nicht
dokumentiert ([sl-process.md](../sl-process.md) §5). Ein Programm vergleicht Zahlen,
Sprache des Feldes, Tippfehler und vom BAG bereits korrigierte Begriffe aller 1688 Limitierungen der Publikation vom
6. Oktober 2026. Es liest nur die öffentliche Publikation und ruft kein Sprachmodell auf. Ergebnis: 38 Befunde, von
blinden Claude-Annotatoren 16 als real (Bedeutung weicht ab) und 12 als geringfügig eingestuft
([Management_Notiz.md](Management_Notiz.md)). Die Befunde liegen als Fallblätter vor ([fallblaetter/](fallblaetter/00_Uebersicht.md)).

## Ziel

1. Jedes Fallblatt ist von einer zuständigen Person des BAG geprüft, entschieden und visiert.
2. Die Bestätigungsrate des BAG ist der Rate der Annotatoren (28 von 38) gegenübergestellt.
3. Bestätigte Abweichungen sind auf dem ordentlichen Weg des BAG berichtigt oder terminiert.
4. Die Fachverantwortung entscheidet, ob die Prüfung als fester Schritt weitergeführt wird (z. B. nach jeder
   Monatspublikation oder vor der Überprüfung alle drei Jahre).

## Nicht-Ziele

- Kein Entwurf und keine Übersetzung von Texten; kein Sprachmodell (Phasen 2 und 3 sind nicht Gegenstand).
- Kein Schreibzugriff auf ePL, keine Schnittstelle zu ePL, keine Verarbeitung unveröffentlichter Texte.
- Keine Änderung des Verfahrens zum Erlass von Verfügungen; der Entscheid über jede Korrektur bleibt beim BAG.
- Keine Beschaffung.

## Lieferobjekte

| Nr. | Lieferobjekt | Stand |
|---|---|---|
| L1 | Fallblätter: 18 Sachverhalte aus 38 Befunden, dazu 6 bestätigte Befunde einer experimentellen Prüfung | liegt vor |
| L2 | Entscheid und Visum je Fallblatt, abgelegt in GEVER | durch BAG |
| L3 | Schutzbedarfsanalyse Phase 1 ([Entwurf](Schutzbedarfsanalyse_Phase1.md)), geprüft durch die Informationssicherheit | Entwurf liegt vor |
| L4 | Kurzbericht: Bestätigungsrate BAG, umgesetzte Korrekturen, Antrag zur Weiterführung | durch BAG |

**Variante A:** nur L1, L2 und L4; das BAG übernimmt die vorliegenden Fallblätter als Dokumente, nichts wird
installiert. **Variante B:** zusätzlich ein eigener Lauf auf einer neuen Publikation im BAG (`make audit`, rund
1 Minute, mit Datierung rund 3 Minuten; Python ≥ 3.9 oder Docker; nur GET-Abrufe auf epl.bag.admin.ch).

## Aufwand

Aus [adoption.md](../adoption.md) §4. Die Minutenwerte sind *Annahmen*, nicht gemessen; es gibt keine öffentliche
Angabe zum heutigen Aufwand des BAG für diese Texte.

| Rolle | Aufwand |
|---|---|
| Prüfende | erster Lauf: 38 Befunde, rund 3–6 h einmalig (*Annahme*: 3–10 Minuten je Befund); danach rund 1 neuer Befund pro Monat, unter 0,5 h (6 der 38 Befunde erscheinen erstmals in den Ständen vom 1. Juni und 1. August 2026, die übrigen 32 bereits im frühesten geprüften Stand vom 19. Februar 2026) |
| Betrieb (nur Variante B) | rund 0,5 h je Lauf (*Annahme*) |
| Fachverantwortung | Entscheide im bestehenden Verfahren; kein zusätzlicher Schritt |
| Sachkosten | keine: Code unter Apache-2.0, kein Modell, keine Lizenz, kein externer Dienst |

Die 6 experimentellen Fallblätter sind in den 38 Befunden nicht enthalten; nach derselben *Annahme* kommen höchstens
rund 1 h hinzu.

## Risiken

| Risiko | Massnahme |
|---|---|
| Die Prüfung findet nicht alles (Operatoren, Verneinungen und Zahlwörter sind standardmässig aus) | Phase 1 bestätigt keine Gleichwertigkeit der Fassungen; sie liefert eine Arbeitsliste |
| Fehlalarme: 10 von 38 Befunden wurden von den Annotatoren nicht bestätigt | Entscheid je Fallblatt; Aufwand ist im Erstlauf eingerechnet |
| Die Einstufung stammt von Claude-Annotatoren, nicht vom BAG | Ziel 2 misst die Abweichung gegenüber dem BAG |
| Der Korrekturweg für eine publizierte Limitierung und die massgebende Sprachfassung sind nicht öffentlich dokumentiert | Feld «Sprache der Verfügung: aus dem Dossier» und «Massnahme» auf jedem Fallblatt; Weg durch BAG festzulegen |
| Keine Zusicherung für Wartung des Codes | Variante A hängt nicht davon ab; Variante B nur mit festgehaltener Code-Version |

## Entscheid

☐ Freigabe Phase 1, Variante A ☐ Freigabe Phase 1, Variante B ☐ Zurückstellung ☐ Ablehnung

Bemerkungen: «durch BAG zu ergänzen»

Ort, Datum, Unterschrift Auftraggeber/in: «durch BAG zu ergänzen»
