# Adoption: a phased pilot for a federal office

This note is for an office that wants to try Gleichlaut without a large project. It proposes three phases. Each phase
can stop on its own and still leave something useful. **Phase 1, the audit, can start now.** It reads only public data,
calls no model, and needs no new tool. Drafting comes later. It first runs in shadow mode on the public feed (phase 2)
and then inside the office on unpublished German (phase 3).

Facts about BAG's process come from [sl-process.md](sl-process.md) and keep its labels: **VERIFIED** means we fetched
the source, **UNVERIFIED** means we found no public source. Every number comes from a file in this repository, and the
file is named next to the number. Numbers marked *assumption* were not measured. They are there to be replaced by the
office's own figures.

## 1. Three phases

| | Phase 1: audit | Phase 2: drafting in shadow mode | Phase 3: drafting in the office |
|---|---|---|---|
| Input | the public SL feed (FHIR NDJSON, DE/FR/IT) | the same feed: German changes between two published dates | the section's unpublished German changes, exported from ePL as an item file ([item-schema.json](item-schema.json)) |
| Model | none | local Apertus 8B on CPU, certified build | 8B air-gapped by default. The 70B is used only on an endpoint the office controls |
| Data | official publication | official publication | not public until BAG publishes it ([operations.md](operations.md) §8) |
| Infrastructure | any server with Python ≥ 3.9 or Docker. Outbound GET to `epl.bag.admin.ch`, or copy the snapshots in | 4 CPU cores, 16 GiB RAM, about 12 GB disk for the default Q8_0 build; 8 GiB RAM and about 8 GB disk with Q4_K_M ([dependencies.md](dependencies.md)) | the same box inside the office network. The month run uses `--network none` |
| Run | `make audit`, monthly or quarterly. It takes about 1 minute, or about 3 minutes with dating ([README](../README.md), [audit.md](audit.md)) | `make month`, monthly. About 3.2 h of CPU for about 57 FR/IT items ([operations.md](operations.md) §1) | `make month ITEMS=…` with the same timing. Then XLIFF goes to the translators |
| Output | `audit_<date>_summary.json`, the findings with DE/FR/IT excerpts, and the audit tab of the register | `summary.json`, which grades the drafts against the French and Italian BAG published: exact, ready and flag rates, and every ready draft that differs | XLIFF 2.1 and 1.2 for Transit. Ready drafts arrive as segments to accept. Flagged drafts carry the check's complaint as a note |
| Received by | the business owner and the staff responsible for each product | the business owner and the language side, as evidence | the translators, in their own CAT tool |

**Phase 1 ends** when the business owner has gone through the first full run and decided whether the audit becomes a
standing step, for example before each triennial review. The first run on the 6 Oct 2026 register has 38 findings: 27
number, language and editorial findings, and 11 terminology findings (`data/audit/audit_20261006_summary.json`). Two blind
Claude annotators (a third on disagreements) confirmed 17 of the 27 and 11 of the 11 ([technical_report.md](../technical_report.md) §5). These are the
measurable checks:

- (a) every finding has been confirmed or explained by BAG staff;
- (b) BAG's own confirmation rate has been compared with the annotators' rate of 28 of 38;
- (c) the confirmed divergences, such as Nemluvio "8" against "4" weeks, have been corrected through BAG's normal process.

**Phase 2 ends** after about three consecutive shadow months. That is about 170 FR/IT items, which is the size of the
held-out set of 166. Phase 3 starts if three conditions hold:

- (a) The pre-registered pass rule holds on the pooled months, judged by a BAG or language-service reader instead of
  Claude annotators. The rule is: unflagged real errors ≤ 1%, unflagged stale and untranslated ≤ 2%, exact match ≥ the
  rules-only start + 5 points, and flagged ≤ 70% ([technical_report.md](../technical_report.md) §5).
- (b) A timed study shows that translators finish sooner from the draft than from the no-model start (the old text
  with its numbers updated by code). The repository measures token edits only: 33.1% fewer for the 8B Q8_0 (the default) and
  20.9% fewer for Q4_K_M ([README](../README.md)).
- (c) The XLIFF files have passed a round trip through the language service's Transit setup.

The shadow workflow (`.github/workflows/shadow.yml`) and `make month` both need no access to internal data.

**Phase 3 ends**, and the tool becomes routine, under four conditions:

- the Schutzbedarfsanalyse is approved (section 3);
- ePL can produce the item file without retyping, or a documented manual step replaces the export;
- no accepted ready draft has carried a meaning error over an agreed period;
- the business owner and the language service decide to keep it.

The 70B lane is a separate decision. It needs an endpoint under the office's control and a contract, and it is worth it
only if the timed study shows that its edge counts in hours. On ready drafts that still need a fix, the 70B has 3 of 66
and the 8B Q8_0 has 25 of 62 ([README](../README.md)).

## 2. Owners

| Role | Proposed owner | Status |
|---|---|---|
| Business owner, all phases | BAG Sektion Arzneimittelaufnahmen | VERIFIED: BAG decides limitations (KVV Art. 73), and the section head signed the 2023 publication circular (sl-process §2). UNVERIFIED: whether the section would sponsor a pilot. We have no contact yet |
| Readers of audit findings (phase 1) | the scientific staff assigned to the product | VERIFIED: ePL assigns applications to scientific staff ("WiMi zuteilen", sl-process §2.5). Hypothesis: that they would own corrections |
| Language side (phases 2 and 3) | whoever writes FR/IT today: section staff, the BAG Sprachdienste, or external translators | UNVERIFIED (sl-process §6). Finding this out is the first question of the pilot |
| Technical operator | phases 1 and 2: anyone who may run Docker or Python, for example the ePL team (epl@bag.admin.ch). Phase 3: the office's IT service provider | the ePL team: VERIFIED. Which provider runs BAG's servers: UNVERIFIED |
| Information security | the office's information security officer (Informationssicherheitsbeauftragte, ISV Art. 37). Residual risks are accepted by the Informationssicherheitsverantwortliche, that is, the director or a delegated member of management (ISV Art. 27 para. 4, Art. 36) | the federal law is VERIFIED. The persons are not known to us |
| Language technology standard | Federal Chancellery (BK), Kompetenzzentrum Sprachtechnologien. Consulted in phase 3, not needed before | VERIFIED: in 2018 the Federal Council tasked the BK with standardising CAT, MT and terminology (sl-process §7) |

**No new tool for translators.** Transit is the CAT tool of all federal language services: "Vor ein paar Jahren wurde
für alle Sprachdienste der Bundesverwaltung das Übersetzungstool Transit eingeführt" (sl-process §7, VERIFIED). Transit
unpacks and packs XLIFF projects (VERIFIED). Gleichlaut writes XLIFF 2.1 and 1.2, both validated against the OASIS
schemas. Which XLIFF version the federal Transit setup accepts is UNVERIFIED, which is why the round trip is an exit
criterion. The federal setup also already provides for MT providers other than DeepL. The federal CAT tool "verfügt
über die Möglichkeit, DeepL Pro oder einen anderen MÜ-Dienstleister einzubinden" (KOSD DeepL report 2019, sl-process
§7). Gleichlaut does not need that plug-in slot, because its drafts arrive already filled into the XLIFF. Whether a
plug-in integration is worth building later is a question for the BK.

**Procurement.** Phases 1 to 3 on the 8B need no licence purchase. The code is Apache-2.0, the Apertus weights are
Apache-2.0 under the Apertus Acceptable Use Policy, and Transit and DeepL Pro licences already exist across the federal
administration (sl-process §7). The office's legal service should review the AUP's indemnification clause in favour of
ETH Zurich and EPFL before phase 2 ([target-architecture.md](target-architecture.md)). Only the 70B lane needs a
contract: own GPUs, or a Swiss-resident provider. The token cost is small, CHF 0.14 a month at today's volume
(`eval/results/economics.json`). The work is in the contract terms (see section 3).

## 3. Protection needs: a starting point for the Schutzbedarfsanalyse

**Framework** (checked on 2026-10-10):

- The Informationssicherheitsgesetz (ISG, SR 128) is fully in force since 1 January 2024, together with the
  Informationssicherheitsverordnung (ISV, SR 128.1).
- ISG Art. 6 names four protection goals: Vertraulichkeit, Verfügbarkeit, Integrität and Nachvollziehbarkeit.
- ISG Art. 13 sets the classification levels «intern», «vertraulich» and «geheim».
- ISG Art. 17 sets the security levels «Grundschutz», «hoher Schutz» and «sehr hoher Schutz».
- ISG Art. 16 and ISV Art. 27 set the Sicherheitsverfahren. Its directives are issued by the Fachstelle des Bundes für
  Informationssicherheit in the State Secretariat for Security Policy (SEPOS, VBS) (ISV Art. 27 para. 7, Art. 42). The
  Federal Office for Cybersecurity (BACS) advises on technical information security (ISV Art. 43), and its
  Sicherheitsverfahren page points to SEPOS.
- The current SEPOS templates are the P041 Leitfaden Schutzbedarfsanalyse with the tool P041-Hi01 V5.1.1 (both 14 Oct
  2024), Si001 IT-Grundschutz V5.1, and P042 ISDS-Konzept.
- Directives that the NCSC issued before the ISV remain valid for at most three years after it came into force (ISV
  Art. 51 para. 1).
- HERMES makes a protection needs analysis mandatory for every IT project.
- A revision of the ISG is under way. Its consultation is planned for mid-2027 and may rename the classification
  levels.

The office's information security officer should confirm which templates apply at the time of the pilot.

| | Phase 1 | Phase 2 | Phase 3, 8B | Phase 3, 70B lane |
|---|---|---|---|---|
| Confidentiality | none: official publication | none | the draft German is not public until BAG publishes it. Whether it is classified «intern» is the classifying unit's decision. The applicant is heard on the draft ruling (sl-process §2.4) | as phase 3, and the text leaves the box. Per request this is one limitation, with numbers replaced by slot codes ([operations.md](operations.md) §9) |
| Integrity | low: a worklist for humans. The audit writes nowhere | low: drafts are graded and never used | medium: drafts feed legal texts. Mitigations: code writes every number, frozen checks run on every draft, a human accepts every draft, and the certified build is hashed before each run | as 8B, plus a certified endpoint and a monthly drift canary |
| Availability | low: a monthly or quarterly batch | low | low: the fallback is today's process. A missed run delays drafts, not rulings | low |
| Traceability | run summary | records, summary, metrics | records, call logs, certificates and gate overrides are logged ([operations.md](operations.md) §7, §8) | the same, plus endpoint call logs |
| Personal data | none ([dependencies.md](dependencies.md)) | none | none | none |
| Third parties | none at runtime | the GGUF is a third-party quantisation, pinned by sha256 ([dependencies.md](dependencies.md)) | the same | the endpoint provider: risk assessment of cooperation with third parties (ISV Art. 10). SEPOS model clauses for procurement contracts have applied since 1 January 2026 |
| Expected level, *to be confirmed by the information security officer* | Grundschutz | Grundschutz | Grundschutz likely. An ISDS-Konzept is needed only if the analysis finds a higher need | depends on the contract and the classification. If the protection need is higher: ISDS-Konzept with risk analysis (P042) |

## 4. Operating model and effort per month

**Assumptions.** About 57 FR/IT items a month (`eval/results/economics.json`). On the held-out set 60–64% of drafts are
flagged and 36–40% are ready ([technical_report.md](../technical_report.md) §5), but on the two live months the checks
flagged 81.8–92.7%, so plan with live rates: about 9 in 10 drafts go to a translator with the checks' complaint, and
drafting saves time only where a draft is a better start than the old text. That is what phase 2 must show before phase 3. About 3–4 larger German rewrites a month go to a
translator without a draft, as today (27 in 7.5 months, [backtest.md](backtest.md) §1). After the first audit, new
findings are rare: 32 of the 38 were already present in the earliest 2026 snapshot, and 6 appeared between June and
September (`first_seen` in `data/audit/audit_20261006.json`). Reading one finding or one draft takes 3–10 minutes:
*assumption*, not measured. No public figure exists on the hours BAG spends on these texts today (sl-process §8).

| Role | Phase 1 | Phase 2 | Phase 3 |
|---|---|---|---|
| Operator: start the job, read the summary, pass the output on | about 0.5 h per run (*assumption*) | about 0.5 h. The run itself is unattended: 200.5 s per item, about 3.2 h of CPU ([operations.md](operations.md) §1) | about 0.5 h. On the 70B lane add a monthly canary (about 70 requests, a few minutes) and a re-certification every 90 days (under an hour, about CHF 0.40, [operations.md](operations.md) §3b, §4) |
| Reviewer | the first run: 38 findings, about 3–6 h once. After that about 1 new finding a month, under 0.5 h | the drafts that differ from what BAG published: at live flag rates nearly every draft, about 50 a month, about 3–8 h (*assumption*: 3–10 minutes each). Plus a one-time timed study | the translator works the same 57 items as today, starting from drafts instead of old text. Ready drafts are accepted or edited. Flagged drafts come with the complaint as a note (13 of a sample of 20 flagged drafts needed no change, [technical_report.md](../technical_report.md) §5). The time saved is what the timed study measures |
| Business owner | decides on corrections, in the existing process | a go or no-go after about 3 months | no new step: the decision stays in ePL |

**The certification machinery, and the minimum an office needs.** A "ready" verdict is valid only for the exact model
build that passed the pre-registered rule. Certification is what binds the verdict to that build. Without a valid
certificate, nothing breaks: every draft simply goes to review.

| Phase | Minimum | Recurring work |
|---|---|---|
| 1 | nothing: the audit uses no model | none |
| 2, and 3 on the 8B | the build certificate shipped in the image. Without a signing key the gate accepts it as is ([deploy/README.md](deploy/README.md)) | none. A build certificate does not expire and needs no canary. Re-certify only after an upgrade of the GGUF, llama-cpp-python or the frozen code (`make certify`, seconds) |
| 3, 8B, optional | an HMAC key (`GLEICHLAUT_CERT_KEY`), if people other than the service account can write to `state/`. The information security officer decides | none |
| 3, 70B lane only | an endpoint certificate (once per endpoint and model), a monthly canary, and a 90-day validity (the default, configurable) | the operator, about 1 h a quarter plus minutes a month. This exists because a provider can change the model behind the same name |

## 5. System of record

**ePL stays the system of record.** The review register is a reviewing aid. It keeps a reviewer's decisions in the
browser (localStorage) until they are exported as XLIFF, JSON or CSV (`src/gleichlaut/ui/build.py`,
[operations.md](operations.md) §5c). In production, decisions travel by one route:

1. XLIFF goes to Transit, where the translator accepts or edits.
2. The final FR/IT text goes into the "Limitierungstext FR / IT" fields in ePL (VERIFIED, sl-process §4).
3. BAG publishes as today.

Gleichlaut's run records and summaries are process evidence, kept under the office's retention rule
([operations.md](operations.md) §8). They are not the decision record. Phase 1 findings belong in the office's own case
or ticket system.

## 6. What phase 1 settles

Everything above runs on what BAG already publishes, so phase 1 needs no access, no data transfer and no one's
permission. It also settles the points that only the office can confirm from the inside:

- **Owners.** Section 2 names the roles the public record points to (VERIFIED / UNVERIFIED as marked); the first audit
  hand-over confirms them.
- **The reviewer.** The labels so far come from blind annotators under a fixed protocol anyone can re-run
  ([PROTOCOL.md](../eval/labels/PROTOCOL.md)); a BAG translator reading the ready drafts uses the same worklists, and a
  timed comparison drops into the shadow month without any change to the pipeline.
- **The ePL hand-off.** Gleichlaut reads the public feed's own FHIR format (VERIFIED, sl-process §4); if the internal
  editor exports differently, `gleichlaut items` also takes the documented item file (`docs/item-schema.json`).
- **The Transit hand-off.** Gleichlaut writes both XLIFF 1.2 and 2.1, each validated against the OASIS schema, so
  whichever version the federal Transit setup expects is already there (sl-process §7).
- **The 70B lane.** It is defined by certificate, not by a vendor: any endpoint the office controls qualifies once it
  passes `make certify-endpoint`.
- **Protection needs.** Section 3 is a starting draft for the office's information security officer, written against
  the current ISG/ISV and the SEPOS templates.

## Sources for section 3 (retrieved 2026-10-10)

- ISG, SR 128, consolidated version of 1 Oct 2025, Art. 6, 13, 16, 17: https://www.fedlex.admin.ch/eli/cc/2022/232/de
- ISV, SR 128.1, version of 1 May 2025, Art. 10, 27, 36, 37, 42, 43, 51, 52: https://www.fedlex.admin.ch/eli/cc/2023/735/de
- SEPOS, Sicherheitsverfahren (templates P041, Si001, P042; page of 25 Aug 2026): https://www.sepos.admin.ch/de/sicherheitsverfahren
- BACS, Sicherheitsverfahren (refers to SEPOS): https://www.bacs.admin.ch/de/sicherheitsverfahren
- HERMES, "Analyze protection needs": https://www.hermes.admin.ch/en/project-management/tasks/analyze-protection-needs.html
- SEPOS model clauses for procurement contracts, effective 1 Jan 2026 (VBS, 13 Oct 2025): https://www.vbs.admin.ch/de/newnsb/3wFYzBM-h6ct9e1WtJQPl
- Federal Council starts the ISG revision (6 May 2026): https://www.admin.ch/de/newnsb/Dbs9cff6yxPdv-8jlLzpz
