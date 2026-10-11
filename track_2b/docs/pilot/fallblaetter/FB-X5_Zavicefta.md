# Fallblatt X5: Zavicefta (Verneinung, Zusatzmodul)

Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom 06.10.2026 (Phase 1, Pilot).

> **Operator- und Negationsmodul, zuschaltbar.** Dieser Befund stammt aus einer Prüfart, die ihr vorab festgelegtes Präzisionsziel nicht erreicht hat; sie ist im Standardlauf ausgeschaltet. Der Befund wurde von beiden blinden Annotatoren bestätigt und wird deshalb zur Prüfung vorgelegt.

| Feld | Inhalt |
|---|---|
| Präparat(e) | Zavicefta |
| Limitierung(en), Kennung in der Publikation | `ZAVICEFTA2` |
| Art der Prüfung | Verneinung: Operator- und Negationsmodul, zuschaltbar |
| Betroffene Sprachfassung(en) | FR |
| Abweichung | Verneinung, FR: FR verneint («n’»), DE nicht |
| Weicht von den beiden anderen ab | FR |
| Erstmals festgestellt | nicht datiert (das Operator- und Negationsmodul wird nicht über frühere Stände datiert) |
| Blinde Einstufung | geringfügig: Form fehlerhaft, Bedeutung erhalten (G18: minor) |
| Herkunft der Einstufung | zwei blinde Claude-Annotatoren, übereinstimmend; keine Einstufung durch das BAG |
| Hinweis | Operator- und Negationsmodul (zuschaltbar); 31 Befunde im Register, davon 6 bestätigt (eval/results/audit_r15.json) |
| Nachschlagen | https://sl.bag.admin.ch/sl, Präparat «Zavicefta» suchen, Limitierung in DE, FR und IT vergleichen; Rohdaten: https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (ebenso `-fr`, `-it`) |

## Auszüge

Wörtlich aus der Publikation vom 06.10.2026; die abweichenden Werte sind **fett**. «…» kürzt den Text.

### Befund G18

- **DE:** Die Pfizer AG vergütet dem Leistungserbringer, bei dem eine angebrochene Packung ZAVICEFTA verfällt, auf dessen erste Aufforderung hin den Anteil des Fabrikabgabepreises für die Anzahl der verfallenen Ampullen zurück.
- **FR:** À la première demande d’un prestataire de service **n’**ayant pas utilisé l’intégralité du contenu d’une boîte de ZAVICEFTA, la société Pfizer AG rembourse à celui-ci la part du prix de fabrique proportionnelle au nombre d’ampoules non utilisées.
- **IT:** Nel caso in cui scada un pacchetto aperto di ZAVICEFTA, Pfizer AG rimborsa al prestatore di servizi, alla sua prima richiesta, la quota del prezzo di fabbrica per la consegna corrispondente al numero di flaconcini scaduti.

Einstufung: von beiden blinden Claude-Annotatoren als geringfügig bestätigt: die Form ist fehlerhaft, die Bedeutung erhalten.

## Bearbeitung (durch BAG auszufüllen)

| Feld | Eintrag |
|---|---|
| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |
| Sprache der Verfügung | aus dem Dossier: ______ |
| Welcher Text ist falsch? | ☐ DE ☐ FR ☐ IT (mehrere möglich; gemessen am Entscheid des BAG) |
| Was ist zu tun? | ☐ Von Amtes wegen berichtigen ☐ Mit der Zulassungsinhaberin in der dreijährlichen Überprüfung aufnehmen ☐ An den Sprachdienst ☐ Keine Massnahme (gleichwertige Formulierung) ☐ Noch unklar – Entscheiddossier prüfen |
| Bemerkung | |
| Visum (Name, Datum) | |

Quelle: `data/audit/audit_20261006.json`, Befund G18; erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).
