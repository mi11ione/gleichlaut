# Schutzbedarfsanalyse (Entwurf): Gleichlaut, Phase 1

Entwurf vom 10.10.2026. Gegliedert nach dem Aufbau der Bundesvorlage P041 (Leitfaden Schutzbedarfsanalyse mit
Hilfsmittel P041-Hi01 V5.1.1, beide vom 14.10.2024, SEPOS), soweit öffentliche Angaben ihn ausfüllen. Die Übertragung in
das Hilfsmittel P041-Hi01 und der Abgleich der Feldbezeichnungen sind Sache der/des Informationssicherheitsbeauftragten
des Amtes (ISBO; ISV Art. 37). Offene Punkte für die ISBO sind mit **[O1]** usw. markiert und in Abschnitt 8 gesammelt.
Rahmen und Quellen: [adoption.md](../adoption.md) §3.

## 1. Angaben zum Schutzobjekt

| Feld | Eintrag |
|---|---|
| Bezeichnung | Gleichlaut, Phase 1: Prüfung der Sprachfassungen DE/FR/IT der SL-Limitierungen |
| Art | Werkzeug (Python-Programm, Apache-2.0), Batch-Lauf; keine Anwendung im Dauerbetrieb, keine Benutzeroberfläche mit Login |
| Geschäftsprozess | Qualitätssicherung der publizierten Limitierungstexte der Spezialitätenliste |
| Geschäftsprozessverantwortliche/r | «durch BAG zu ergänzen» |
| Verantwortliche/r Schutzobjekt | «durch BAG zu ergänzen» |
| ISBO | «durch BAG zu ergänzen» |
| Projektphase | Pilot, Phase 1 ([Projektauftrag](Projektauftrag_Phase1.md)) |
| Varianten | **A:** Das BAG übernimmt nur die bereits erstellten Fallblätter (Dokumente); im BAG wird nichts installiert. **B:** zusätzlich eigener Lauf auf einer neuen Publikation |

## 2. Beschreibung

- **Eingabe:** die öffentliche SL-Publikation als FHIR-NDJSON, eine Datei je Sprache, von `epl.bag.admin.ch`
  (nur GET-Abrufe, höchstens einer pro Sekunde) oder als kopierte Dateien ohne Netzzugriff
  ([operations.md](../operations.md) §9).
- **Verarbeitung:** deterministische Regeln, nur Python-Standardbibliothek; 0 Modellaufrufe; kein externer Dienst, keine
  Telemetrie.
- **Ausgabe:** Befundliste (`audit_<datum>.json`), Zusammenfassung, Textauszüge, Fallblätter (Markdown) zur Ablage in GEVER.
- **Schnittstellen:** keine zu ePL, kein schreibender Zugriff auf ein System des BAG.
- **Plattform (nur B):** ein Server oder Arbeitsplatz mit Python ≥ 3.9 oder Docker. **[O4]**
- **Benutzerkreis:** Prüfende und Fachverantwortung des BAG; Betrieb durch eine Person mit Recht, Python oder Docker
  auszuführen.

## 3. Datenschutz

| Frage | Antwort | Begründung |
|---|---|---|
| Werden Personendaten bearbeitet? | nein | Die Publikation enthält Präparate, Limitierungstexte und Preise. Genannte Firmen sind juristische Personen; das DSG (SR 235.1) erfasst nur Angaben über natürliche Personen (Art. 5 Bst. a). **[O2]** |
| Besonders schützenswerte Personendaten, Profiling? | nein | wie oben |
| Datenschutz-Folgenabschätzung nötig? | voraussichtlich nein | keine Bearbeitung von Personendaten durch das Werkzeug. **[O2]** |

Das Visum auf dem Fallblatt (Name, Datum) ist gewöhnliche Geschäftsverwaltung in GEVER und nicht Teil des Werkzeugs.

## 4. Informationsschutz (Klassifizierung, ISG Art. 13)

| Information | Vorschlag | Begründung |
|---|---|---|
| Eingabe: SL-Publikation | nicht klassifiziert | amtliche Veröffentlichung (KVV Art. 71) |
| Ausgabe: Befundliste, Fallblätter | nicht klassifiziert | vollständig aus öffentlichen Daten abgeleitet und von jedermann mit dem öffentlichen Code reproduzierbar |
| Entscheide und Massnahmen je Fallblatt | durch die klassifizierende Stelle zu bestimmen | interne Geschäftsunterlagen des BAG. **[O3]** |

## 5. Schutzbedarf je Schutzziel (ISG Art. 6)

| Schutzziel | Bedarf (Vorschlag) | Begründung |
|---|---|---|
| Vertraulichkeit | kein erhöhter Bedarf | Eingabe öffentlich; Ausgabe öffentlich reproduzierbar (Abschnitt 4) |
| Integrität | kein erhöhter Bedarf | Die Befunde sind eine Arbeitsliste für Menschen. Das Werkzeug schreibt nirgends hin. Ein falscher Befund wird bei der Prüfung am publizierten Text erkannt; ein verpasster Befund lässt den heutigen Zustand unverändert. Keine Korrektur ohne Entscheid des BAG |
| Verfügbarkeit | kein erhöhter Bedarf | monatlicher oder quartalsweiser Batch, Laufzeit rund 1 Minute (mit Datierung rund 3). Fällt er aus, gilt das heutige Verfahren; keine Verfügung hängt davon ab |
| Nachvollziehbarkeit | kein erhöhter Bedarf | Jeder Befund nennt Kennung, Sprachfassungen und Wortlaut; der Lauf ist deterministisch. Massnahmen: verwendete Code-Version und Publikationsdatum im Fallblatt bzw. Laufprotokoll festhalten; Entscheid und Visum in GEVER. **[O5]** |

## 6. Abhängigkeiten und Dritte

- Zur Laufzeit: keine Drittdienste. Netz nur für GET auf `epl.bag.admin.ch` (Variante B), über den Proxy des Amtes
  möglich (`HTTPS_PROXY`), Prüfung gegen die System-CA ([operations.md](../operations.md) §9). **[O4]**
- Beim Bau (nur Docker): Basis-Image per Digest festgelegt, PyPI-Pakete per Hash; beides auch aus internem Spiegel
  beziehbar ([dependencies.md](../dependencies.md)).
- Kein Vertrag mit Dritten, keine Risikobeurteilung nach ISV Art. 10 nötig, solange kein externer Dienst genutzt wird.

## 7. Ergebnis (Vorschlag)

**Sicherheitsstufe Grundschutz** (ISG Art. 17). Kein erhöhter Schutzbedarf, daher kein ISDS-Konzept (P042) nötig. Für
den Arbeitsplatz oder Server gelten die üblichen Grundschutzmassnahmen (Si001). In Variante A entsteht kein neues
Informatikschutzobjekt; es werden nur Dokumente abgelegt. **Zu bestätigen durch die ISBO.**

## 8. Offene Punkte für die ISBO

| Nr. | Punkt |
|---|---|
| O1 | Übertragung in P041-Hi01 V5.1.1; Bestätigung, dass P041, Si001 und P042 zum Zeitpunkt des Pilots gelten (ISV Art. 51 Abs. 1; Revision des ISG in Vorbereitung) |
| O2 | Bestätigung «keine Personendaten», gegebenenfalls mit der Datenschutzberatung des Amtes |
| O3 | Klassifizierung der Entscheide und Massnahmen vor der Berichtigung einer Publikation |
| O4 | Variante B: Zulässigkeit der Ausführung von Python oder Docker auf dem vorgesehenen Gerät; ausgehender GET auf `epl.bag.admin.ch` |
| O5 | Ablageort und Aufbewahrung der Fallblätter und Laufergebnisse in GEVER |
| O6 | Annahme des Restrisikos durch die Informationssicherheitsverantwortliche Person (Direktion oder delegiertes Mitglied der Geschäftsleitung; ISV Art. 27 Abs. 4, Art. 36) |

## 9. Unterschriften

| Rolle | Name, Datum, Unterschrift |
|---|---|
| Geschäftsprozessverantwortliche/r | «durch BAG zu ergänzen» |
| ISBO | «durch BAG zu ergänzen» |
| Informationssicherheitsverantwortliche Person (Restrisiko) | «durch BAG zu ergänzen» |
