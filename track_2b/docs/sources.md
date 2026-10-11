# Sources and verified facts (Gleichlaut, Track 2B)

Accessed 2026-10-09. Fetches used the User-Agent `hackapertus-research/0.1`. Every item gives a URL and the exact figure or quote. **UNVERIFIED** means a claim that no primary source confirmed. **Not public** (used for the SL process points re-checked on 2026-10-11, see [sl-process.md](sl-process.md)) means no public source settles the point, and the entry states what the public record shows. Notes marked "(own computation)" are numbers we derived from the primary files; they were not published by the source.

---

## 1. Population by main language; persons with mandatory health insurance

### 1.1 Main languages (BFS Strukturerhebung, latest year 2024)

- Table: "Die häufigsten Hauptsprachen der ständigen Wohnbevölkerung". BFS order no. **su-d-01.08.01.01**, DAM asset **36399478**, period 2010–2024, embargo date 2026-03-05.
  - Page: https://www.bfs.admin.ch/asset/de/36399478
  - File (xlsx): https://dam-api.bfs.admin.ch/hub/api/dam/assets/36399478/master
  - Sheet "Die häufigsten Hauptsprachen, 2024". Base "Ständige Wohnbevölkerung" = 8,836,430.
    - "Französisch (oder Patois Romand)": 1,994,713 persons, **22.57 %** (CI ±0.08 percentage points)
    - "Italienisch (oder Tessiner / bündneritalienischer Dialekt)": 688,670 persons, **7.79 %** (CI ±0.06 pp)
    - "Deutsch (oder Schweizerdeutsch)": 5,400,082 persons, 61.11 %
    - "Rätoromanisch": 38,009 persons, 0.43 %
  - Notes in the table: "Die Befragten konnten mehrere Hauptsprachen nennen. Bis zu drei Hauptsprachen je Person wurden berücksichtigt." and "Diese Tabelle umfasst alle Personen der ständigen Wohnbevölkerung, die in Privathaushalten leben." Because people could name several languages, the shares add up to more than 100 %.
  - Terms of use (DAM API metadata): "OPEN-BY", "Freie Nutzung - Quellenangabe ist Pflicht".

### 1.2 Persons insured under mandatory health insurance (OKP / LAMal)

- BAG, "Statistik der obligatorischen Krankenversicherung 2025", table **T 7.01 "Durchschnittlicher Versichertenbestand ab 2009"** (file KV701N_KVSTAT2025.xlsx in the ZIP).
  - ZIP: https://www.bag.admin.ch/dam/de/sd-web/rzVuBHgHn1Nw/KVSTAT2025_V20260929.zip
  - Landing page: https://www.bag.admin.ch/de/statistik-der-obligatorischen-krankenversicherung
  - Total **2025: 9,076,526**. Total 2024: 9,005,998. "Datenstand: 30.5.2026".
  - Footnotes: since 2017 the average is calculated from insured days (Art. 29 KVV). The figure includes "Personen mit Wohnsitz oder Aufenthalt im Ausland gemäss Art. 4 und 5 KVV".

---

## 2. Spezialitätenliste (SL): legal basis, publication, reuse, translation

### 2.1 Legal basis (Fedlex, consolidated versions current on 2026-10-09)

- **KVV (SR 832.102), Art. 71 Abs. 1 lit. a**: "Das BAG veröffentlicht: a. die Spezialitätenliste (Art. 52 Abs. 1 Bst. b KVG)". Version of 2026-08-01:
  https://fedlex.data.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/1995/3867_3867_3867/20260801/de/html/fedlex-data-admin-ch-eli-cc-1995-3867_3867_3867-20260801-de-html.html (portal: https://www.fedlex.admin.ch/eli/cc/1995/3867_3867_3867/de)
- **KVV Art. 73 "Limitierungen"**: "Die Aufnahme in eine Liste kann unter der Bedingung einer Limitierung erfolgen. Die Limitierung kann sich insbesondere auf die Menge oder die medizinischen Indikationen beziehen."
- **KLV (SR 832.112.31) Art. 30 ff.** set the conditions for listing in the SL. https://www.fedlex.admin.ch/eli/cc/1995/4964_4964_4964/de
- **PublG (SR 170.512) Art. 14 Abs. 1**: "Die Veröffentlichung erfolgt gleichzeitig in den Amtssprachen Deutsch, Französisch und Italienisch. Bei Erlassen sind die drei Fassungen in gleicher Weise verbindlich." Version of 2023-09-01:
  https://fedlex.data.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/2004/745/20230901/de/html/fedlex-data-admin-ch-eli-cc-2004-745-20230901-de-html-9.html
  - Art. 14 Abs. 2 lets the Federal Council exempt texts published by reference (Art. 13a Abs. 1 lit. a) from trilingual publication, under the conditions in letters a and b.
  - **PublG Art. 15 Abs. 1**: "Für Erlasse des Bundes [...] ist die in der AS veröffentlichte Fassung massgebend. Wird ein Text durch Verweis veröffentlicht, so ist die Fassung massgebend, auf die verwiesen wird."
  - **PublG Art. 10 Abs. 1**: the Federal Chancellery corrects "sinnverändernde Fehler" in the AS. **PublV (SR 170.512.1) Art. 8 Abs. 2 lit. c** lists among these: "Übersetzungsfehler oder terminologische Unstimmigkeiten". https://www.fedlex.admin.ch/eli/cc/2015/670/de
- **SpG (Sprachengesetz, SR 441.1) Art. 10 Abs. 1–2**: "Die Erlasse des Bundes und andere Texte, die nach dem Publikationsgesetz [...] in der Amtlichen und der Systematischen Sammlung des Bundesrechts oder im Bundesblatt zu veröffentlichen sind, werden in Deutsch, Französisch und Italienisch veröffentlicht, soweit das Gesetz nichts anderes vorsieht." / "Die Veröffentlichung erfolgt gleichzeitig in Deutsch, Französisch und Italienisch." Version of 2026-01-01:
  https://fedlex.data.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/2009/821/20260101/de/html/fedlex-data-admin-ch-eli-cc-2009-821-20260101-de-html-6.html
- **UNVERIFIED: that a statute declares the DE/FR/IT versions of SL limitation texts equally binding.** PublG Art. 14 and SpG Art. 10 cover texts published in the AS, SR or BBl. The SL is published by the BAG under KVV Art. 71, and we found no provision that publishes it in the AS or SR. The SL Handbuch (2.3) does not state an equal-authenticity rule either. In practice the SL is published in all three languages (per-language FHIR files, 2.2). The BAG's own review checklist asks whether the translations are "kongruent" (2.4).
- **Copyright (URG, SR 231.1) Art. 5**: not protected are "a. Gesetze, Verordnungen, völkerrechtliche Verträge und andere amtliche Erlasse; [...] c. Entscheidungen, Protokolle und Berichte von Behörden und öffentlichen Verwaltungen". Abs. 2: "Ebenfalls nicht geschützt sind amtliche oder gesetzlich geforderte Sammlungen und Übersetzungen der Werke nach Absatz 1." https://www.fedlex.admin.ch/eli/cc/1993/1798_1798_1798/de
  - Whether the SL counts as an "amtlicher Erlass" or a "Sammlung" under Art. 5: **UNVERIFIED** (this is a legal interpretation, not a published statement).

### 2.2 How the SL is published (ePL)

- BAG ePL page: https://www.bag.admin.ch/de/elektronische-plattform-leistungen-epl
  - "Die monatlichen Excel- und FHIR-Dateien werden wie gewohnt jeweils am ersten eines Monats auf der Spezialitätenliste publiziert ( https://www.sl.bag.admin.ch/resources/current-and-archived-data )."
  - "Die neue Spezialitätenliste ist seit dem 05. Januar 2026 unter folgender Adresse erreichbar: https://sl.bag.admin.ch/sl . Analog zur bisherigen Spezialitätenliste ist der Zugriff ohne Login möglich."
  - "Die neue und die alte Spezialitätenliste wurden bis 01. Juni 2026 parallel betrieben. Seit dem 01. Juni 2026 erfolgt die automatische Umleitung von der alten auf die neue Spezialitätenliste."
  - The page says an API is planned: "Weitere Informationen folgen." No production API URL is given.
- XML end-of-life (SL UI string, https://sl.bag.admin.ch/assets/i18n/de.json, key `resources.currentAndArchivedData.currentDataTab.xml.alert`): "Die aktuellen Daten im XML Format sind nur noch bis zum 30. Juni 2026 (Datenstamm 01. Juni 2026) verfügbar, danach werden diese nur noch im FHIR Format angeboten."
- Machine endpoint used by the SL web app (found in the app's JS bundle, not documented on a BAG page). It needs an `Accept-Language` header (de/fr/it); without one it returns nulls:
  - `GET https://epl.bag.admin.ch/api/sl/public/resources/current` with `Accept-Language: de`. Response on 2026-10-09: `"fhir":{"fileUrl":"sl/publication/fhir/foph-sl-publication-20261006-de.ndjson","lastUpdated":"2026-10-06"}`.
  - Files are served under `https://epl.bag.admin.ch/static/`, for example https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-de.ndjson (93,566,103 bytes). The `-fr` file is 94,156,235 bytes and the `-it` file 93,778,113 bytes.
  - There is **one NDJSON file per language**. Each line is a FHIR R5 `Bundle` (profile `http://fhir.ch/ig/ch-epl/StructureDefinition/ch-idmp-bundle`).
  - Archive endpoint: `https://epl.bag.admin.ch/api/sl/public/resources/archive`.
  - Observed: the current FHIR file is dated 2026-10-06, not the 1st of the month.
- SL Handbuch (valid from 1.1.2025), section A.6.1: "Das BAG setzt Änderungen (Aufnahmen, Streichungen usw.) der SL sowie der GG-SL auf den 1. eines Monats in Kraft [...]. Unter www.spezialitaetenliste.ch ist die geänderte SL sowie GG-SL in Form von Excel- und XML-Dateien bereits am 27. des Vormonats abrufbar. Änderungen bis zum letzten Tag des Vormonats sind noch möglich."
  https://www.bag.admin.ch/dam/it/sd-web/eWqYyGMBwYb0/handbuch-betreffend-die-spezialitaetenliste-gueltig-ab-1-1-2025.pdf
- (Own computation) In the DE file of 2026-10-06 we counted 6,749 bundles and 1,688 unique `ClinicalUseDefinition` ids. The limitation texts total 1,467,094 characters (178,382 whitespace-separated words).
- Limitation ids are identical across the DE, FR and IT files, so the three versions can be aligned by `ClinicalUseDefinition.id`. Examples:
  - `ABEVMY.01a---Kolorektalkarzinom` → DE "Kolorektalkarzinom Nach Kostengutsprache durch den Krankenversicherer…" / FR "Carcinome colorectal Après accord sur la prise en charge des frais…" / IT "Carcinoma del colon-retto Dopo la garanzia di rimborso dei costi…"
  - The id carries a German slug in every language file.

### 2.3 Reuse terms for SL/ePL data

- The BAG ePL page names no licence and no terms of use. The SL is not listed on opendata.swiss: a CKAN search for "Spezialitätenliste" returned `count 0` (https://ckan.opendata.swiss/api/3/action/package_search?q=Spezialitätenliste).
- The BAG data-use page (https://www.bag.admin.ch/de/ergaenzende-informationen-zur-datennutzung) covers privacy and embedded content only, not reuse.
- The admin.ch legal notice (https://www.admin.ch/gov/de/start/rechtliches.html) returned HTTP 403 to our fetch, so its content is **UNVERIFIED** here.
- The FHIR implementation guide (the specification, not the data) is CC0-1.0 (section 3).
- **UNVERIFIED: an explicit open-data licence for the SL/ePL data.**

### 2.4 Who translates SL texts

- **Not public.** No public source says who translates SL limitation texts (BAG language service, Federal Chancellery or the marketing authorisation holder). The public record gives the federal default: Sprachdiensteverordnung (SpDV, SR 172.081) Art. 10 Abs. 1, "Die Übersetzungen und die anderen Sprachdienstleistungen für die Bundesverwaltung werden in der Regel von den Sprachdiensten der Bundesverwaltung erbracht" (https://www.fedlex.admin.ch/eli/cc/2012/771/de). Details and the searches behind "not public": [sl-process.md](sl-process.md) §6.
- Related facts:
  - The SL Handbuch says application forms "in einer Amtssprache (deutsch, französisch, italienisch) auszufüllen" (multiple sections, e.g. Key Facts forms).
  - The SL triennial-review checklist in the SL app (https://sl.bag.admin.ch/assets/i18n/de.json, key `sl.request.expediency.changes.formulationLimitation`): "Falls eine Limitierung vorhanden ist, ist diese wissenschaftlich eindeutig und klar verständlich formuliert und die Übersetzungen sind kongruent?"
  - Companion key `...info.changes.formulationLimitation`: "Ist gegebenenfalls eine Übersetzung missverständlich formuliert? Inhaltliche Limitierungsanpassungen oder -erweiterungen müssen in Form eines Gesuches Änderung der Limitierung (GÄL) oder Gesuch um Erweiterung der Indikation (IND) eingereicht werden."

---

## 3. FHIR: Swiss ePL implementation guide

- **CH EPL (R5)**. Published at https://fhir.ch/ig/ch-epl/ (index: https://fhir.ch/ig/ch-epl/index.html).
  - Canonical: `http://fhir.ch/ig/ch-epl/ImplementationGuide/ch.fhir.ig.ch-epl`
  - "Version : 1.0.1", "Active as of 2026-03-06", "(v1.0.1: DSTU 1) based on FHIR [...] v5.0.0", status trial-use.
  - Package `ch.fhir.ig.ch-epl#1.0.1`, `"license" : "CC0-1.0"`, author "Federal Office of Public Health FOPH". Package download: https://fhir.ch/ig/ch-epl/package.tgz
  - Older versions: https://fhir.ch/ig/ch-epl/1.0.0/index.html and https://fhir.ch/ig/ch-epl/1.0.0-ballot/index.html.
  - Source: https://github.com/bag-epl/bag-epl-fhir (linked from the SL app).
  - The former CI build URL https://build.fhir.org/ig/bag-epl/bag-epl-fhir/ returned 404 on 2026-10-09.
- Resource profiles (artifacts page https://fhir.ch/ig/ch-epl/artifacts.html): AdministrableProductDefinition, Bundle, **ClinicalUseDefinition Indication**, DocumentReference, Ingredient, ManufacturedItemDefinition, MedicinalProductDefinition, Organization, PackagedProductDefinition, RegulatedAuthorization.
- **Limitation modelling:**
  - Extension **"CH EPL - Regulated Authorization Limitation"**, `http://fhir.ch/ig/ch-epl/StructureDefinition/regulatedAuthorization-limitation`. Description: "A limitation to an authorisation for reimbursement of a drug, for a certain indication." Status draft, version 1.0.1. https://fhir.ch/ig/ch-epl/StructureDefinition-regulatedAuthorization-limitation.html
    - Sub-extensions: `status` (CodeableConcept), `statusDate`, `period`, `reimbursementEndDate`, `firstLimitationDate`, `limitationIndication` (Reference), `indicationCode` (string), `priceModelSpecification`, `priceModel` (boolean), `relatedIndication` (Reference), `productPrice`.
  - The limitation **text** sits in the referenced `ClinicalUseDefinition` (profile `http://fhir.ch/ig/ch-epl/StructureDefinition/ch-idmp-clinicalusedefinition-indication`), in `indication.diseaseSymptomProcedure.concept.text`. This is confirmed in the IG example `ClinicalUseDefinition-LIM-64766004-ABRILADA` and in the live feed.
  - Related extension: `reimbursementSL`. Related code system: `ch-epl-foph-limitationstatus`.
- Language handling:
  - In the IG package, language designations (de/fr/it) appear only in `CodeSystem-ch-epl-foph-index-therapeuticus`. No `StructureDefinition/translation` extension is used.
  - The live feed carries one language per file (2.2), not FHIR translation extensions.

---

## 4. XLIFF

- **XLIFF Version 2.1, OASIS Standard, 13 February 2018**: http://docs.oasis-open.org/xliff/xliff-core/v2.1/os/xliff-core-v2.1-os.html
  - Core XSD: http://docs.oasis-open.org/xliff/xliff-core/v2.1/os/schemas/xliff_core_2.0.xsd. Namespace `urn:oasis:names:tc:xliff:document:2.0`; the file is named 2.0 but is part of the 2.1 work product.
  - The XSD imports `informativeCopiesOf3rdPartySchemas/w3c/xml.xsd`.
  - Schema directory: http://docs.oasis-open.org/xliff/xliff-core/v2.1/os/schemas/ ; XML catalog: .../schemas/catalog.xml
- Licence / IPR:
  - Spec: "This specification is provided under the RF on RAND Terms Mode of the OASIS IPR Policy".
  - Notices: "This document and translations of it may be copied and furnished to others, and derivative works that comment on or otherwise explain it or assist in its implementation may be prepared, copied, published, and distributed, in whole or in part, without restriction of any kind, provided that the above copyright notice and this section are included on all such copies and derivative works. However, this document itself may not be modified in any way, including by removing the copyright notice or references to OASIS [...]".
  - XSD header: "Copyright (c) OASIS Open 2018. All Rights Reserved." plus "TC IPR Statement: https://www.oasis-open.org/committees/xliff/ipr.php".
  - TC IPR page: "All participants in this TC have agreed to the terms of the RF on RAND Mode of the OASIS IPR Policy".
  - Practical reading: redistribute the XSD unmodified, with its header kept. Whether that header satisfies the "Notices" requirement for a schema file: **UNVERIFIED**.
- XLIFF 2.2 exists as a "Committee Specification 13 March 2025" (Part 1: Core), not an OASIS Standard: https://docs.oasis-open.org/xliff/xliff-core/v2.2/xliff-core-v2.2-part1.html
- CAT tools in Swiss federal translation services:
  - **ISB IKT-Vorgabe A734 "Übersetzungslösung BUND"**, version 1.0, in force 15 June 2020: "Im Einsatzgebiet Übersetzungen gilt eine Einproduktstrategie. [...] Es MUSS folgendes Standardprodukt eingesetzt werden: − CAT-Tool Star Transit der Firma Star AG". The WTO tender "Übersetzungslösung Bund (18012) 701" was awarded on 26 September 2019. Translation services named: "Die Sprachdienste der Departemente stellen Übersetzungen bzw. Revisionen ins Französische, Italienische, Deutsche und - teilweise - ins Englische sicher (die Schweizerische Bundeskanzlei BK zusätzlich ins Rätoromanische)." https://www.bk.admin.ch/dam/de/sd-web/eGerKT54ncdB/a734_1-0_genehmigt.pdf
    - Whether a later version has replaced A734 v1.0 is not public. On 2026-10-11 the bk.admin.ch link above still served v1.0 ("Diese Version: 1.0", "Status (diese Version): Genehmigt"). The document itself provides for a review "spätestens vier Jahre nach der Genehmigung".
  - **STAR Transit XLIFF version support: not public.** STAR's current documentation (User's Guide SP18 2025-08, Product Guide SP18 2026-01, Feature Guide SP18 2026-04, "Tips & Tricks for All File Formats" SP18 2026-01, release notes) names no XLIFF version. The file-format reference lists "File extensions: *.xliff *.zip" and "Standard function for Transit Freelance Pro and Professional" (https://www.star-group.net/-downloads-/document/2024/TransitNXT_Usage_TipsAndTricksForAllFileFormats_ENG.pdf). The Feature Guide marks "Pack project as XLIFF file" as "CLM" ("CLM = combined with STAR CLM"), while unpacking XLIFF and sending back the translation as XLIFF are standard (https://www.star-group.net/-downloads-/document/1927/TransitNXT_FeatureGuide_ENG.pdf, p. 8). Details: [sl-process.md](sl-process.md) §7.
  - Trados Studio / memoQ XLIFF 2.x support: **UNVERIFIED** (forum and Wikipedia only, e.g. https://proz.com/forum/cat_tools_technical_help/327422-support_for_xliff_20_and_later.html). Neither tool is shown to be in federal use.
  - Okapi Framework has an "XLIFF-2 Filter": https://okapiframework.org/wiki/index.php/XLIFF-2_Filter

---

## 5. Hosting Apertus; licence; self-hosting sizes

### 5.1 Providers

Primary overview: Apertus "Inference Ecosystem", 17 Sept 2026, https://www.apertus-ai.org/articles/2026-09-apertus-1-5-ga/. Its column "Location¹" is footnoted "Physical location of the datacenter where user data is processed." The table gives:

| Provider | Models | Location | Per-token |
|---|---|---|---|
| Swisscom | 70B | 🇨🇭 | ✅ |
| Infomaniak | 70B | 🇨🇭 | ✅ |
| PHOENIQS (kvant.cloud) | 70B | 🇨🇭 | ✅ |
| Safe Swiss Cloud | 70B | 🇨🇭 | ✅ |
| OnPrem.ai | 70B | 🇨🇭 | |
| stepping stone | 8B | 🇨🇭 | |
| Public AI | 8B, 70B | 🌍 | ✅ |
| Featherless | 70B | 🌍 | ✅ |

The same page lists Exoscale (8B, 70B, 🇨🇭) under self-deployment. "Information is current as of September 2026." Get-started page: https://apertus-ai.org/pages/get-started/ (Public AI listed as "Various regions").

- **Infomaniak**
  - Price page https://www.infomaniak.com/en/hosting/ai-tools/prices: "swiss-ai/Apertus-v1.5-70B Input token: CHF 0.70 / 1M tokens Output token: CHF 2.50 / 1M tokens".
  - Residency, as quoted by the provider on apertus-ai.org: "keeping your data securely hosted in Swiss data centers" and "a clear no‑logs policy".
- **Safe Swiss Cloud**
  - https://safeswisscloud.com/en/private-ai/private-ai-pricing/: apertus-v1.5-70b input "0.712", output "2.553" per million tokens; "All prices are in CHF / EUR."
  - "Programmatic access to Swiss-hosted private LLMs". A Swiss location specific to Apertus is not stated on that page.
- **Swisscom**: 70B, Switzerland according to apertus-ai.org.
  - "Swisscom is offering 1000 keys for Apertus during the Swiss {ai} Weeks hackathons." Docs: cloud.swisscom.ch.
  - **Pricing UNVERIFIED** (the product page https://digital.swisscom.com/products/swiss-ai-platform/info did not render content for our fetch).
- **PHOENIQS (Phoenix Technologies / kvant.cloud)**: 70B, "Swiss data center" according to apertus-ai.org. **Pricing UNVERIFIED.**
- **CSCS**
  - Named by Public AI as an inference partner: "6 inference partners across 5 countries including AWS, Exoscale, AI Singapore, Cudo, CSCS, Australia NCI, and Juelich SC" (https://publicai.substack.com/p/public-ai-is-here).
  - A public CSCS Apertus API offering: **UNVERIFIED**.
- **Public AI: routing outside Switzerland, yes as stated.**
  - https://publicai.co/utility: "These servers are deployed across clusters donated by national and industry partners. A global load-balancing layer ensures that requests are routed efficiently and transparently, regardless of which country's compute is serving the query."
  - The same text appears at https://huggingface.co/blog/inference-providers-publicai.

### 5.2 Licence and acceptable use

- Hugging Face metadata for `swiss-ai/Apertus-v1.5-70B` (https://huggingface.co/swiss-ai/Apertus-v1.5-70B): tag `license:apache-2.0`, `gated: auto`.
  - Gate text: "By clicking "Agree" I confirm I have read and agree to the Apache 2․0 license and the Acceptable Use Policy (AUP), available at: https://github.com/swiss-ai/apertus-legal/blob/main/apertus_1.5/USAGE_POLICY.pdf."
  - Accepting the gate shares the user's email and username with the repository authors.
- AUP v1.5 (July 14, 2026): https://github.com/swiss-ai/apertus-legal/blob/main/apertus_1.5/USAGE_POLICY.pdf
  - Indemnity: "You agree to indemnify, defend, and hold harmless ETH Zurich and EPFL against any third-party claims arising from or in connection with your use of Apertus LLM."
  - On redistribution, the redistributor must "(a) make available to your recipient of Apertus the AUP [...]; (b) condition the redistribution on the recipient accepting the AUP by an express act of assent; and (c) contractually require the recipient to pass on the obligations [...] (back-to-back)."
  - Personal data: "SNAI will regularly provide a file with hash values [...] which you can apply as an output filter [...] We strongly advise downloading and applying this output filter from SNAI every six months following the release of the model."
- Model card facts:
  - "Apertus 1.5 is a family of 8B and 70B parameter language models", "contexts of up to 262,144 tokens", multimodal input (image, audio, text).
  - Official vLLM example for 70B uses `--tensor-parallel-size 4 --gpu-memory-utilization 0.8 --max-model-len 262144`.
  - Upstream vLLM/transformers support is not yet merged: "use our modified version of vLLM and transformers" (Docker image `ghcr.io/swiss-ai/vllm_apertus_1.5_release:latest-amd64`).

### 5.3 Sizes (from the Hugging Face API file listings, `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`; GB = 10^9 bytes)

| Repo | Format | Size |
|---|---|---|
| swiss-ai/Apertus-v1.5-70B | safetensors (bf16, incl. vision/audio towers) | 144.6 GB |
| swiss-ai/Apertus-v1.5-8B | safetensors | 18.4 GB |
| onprem-ai/Apertus-v1.5-70B-FP8 | FP8 | 76.2 GB |
| onprem-ai/Apertus-v1.5-70B-NVFP4 | NVFP4 | 51.5 GB |
| **katya228/Apertus-v1.5-70B-text-GGUF** | GGUF Q4_K_M (`apertus-70b-Q4_K_M.gguf`) | **43.72 GB** |
| Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF | GGUF Q4_K_M | 5.06 GB |
| andreasmartin/apertus-v1.5-8b-text-Q8_0-GGUF | GGUF Q8_0 | 8.57 GB |
| bartowski/swiss-ai_Apertus-8B-Instruct-2509-GGUF | Q4_K_M / Q8_0 / bf16 | 5.06 / 8.57 / 16.12 GB |
| bartowski/swiss-ai_Apertus-70B-Instruct-2509-GGUF | Q4_K_M / Q8_0 | 43.72 / 75.02 GB |
| unsloth/Apertus-70B-Instruct-2509-GGUF | Q4_K_M / BF16 | 43.72 / 141.21 GB |

- **A 70B GGUF exists for v1.5, but only as an unofficial text-only test quant.**
  - The katya228 README: "These are TEST quants. [...] No imatrix, no perplexity measurements" and "This is text-only. The vision and audio towers of v1.5 were stripped".
  - It also says "Two launch flags are mandatory — `--override-kv tokenizer.ggml.eos_token_id=int:68` [...] and `-sp`".
  - It states that "the only Apertus GGUFs on the Hub are for the older `2509` (v1.0) release" at its upload time.
- No official swiss-ai GGUF repo exists. The swiss-ai org list on 2026-10-09 shows safetensors and MLX repos only.
- The v1.5 8B GGUFs above derive from a third-party text-only extraction (`andreasmartin/apertus-v1.5-8b-text`). No direct GGUF quant of `swiss-ai/Apertus-v1.5-8B` appears under the HF filter `base_model:quantized:swiss-ai/Apertus-v1.5-8B`.
- The "8B Q4_K_M ~4.9 GB" figure: the measured file size is 5.06 × 10^9 bytes (= 4.71 GiB).
- OnPrem.ai is quoted on apertus-ai.org with "99% of FP8 MMLU quality in a 48 GiB checkpoint". This is the vendor's claim and **UNVERIFIED**.

---

## 6. Other Swiss multilingual binding lists with the same "DE changed → update FR/IT" workflow

| List / corpus | URL | Update frequency | Languages | Notes |
|---|---|---|---|---|
| MiGeL (Mittel- und Gegenständeliste, KLV Anhang 2) | https://www.bag.admin.ch/de/mittel-und-gegenstaendeliste-migel | Versions "per 1. Januar 2026" and "per 1. Juli 2026" (observed half-yearly; no rule found) | Excel sheets "MiGeL D", "MiGeL F", "MiGeL I"; has a "Limitation" column | KLV Art. 20a Abs. 3: "Die Liste der Mittel und Gegenstände wird in der AS und in der SR nicht veröffentlicht. Die Änderungen und konsolidierte Fassungen der Liste werden auf der Website des BAG publiziert." ePL timeline: MiGeL to follow 2026–2027 |
| Analysenliste (AL, KLV Anhang 3) | https://www.bag.admin.ch/de/analysenliste-al | Versions per 1.1.2026 and 1.7.2026 observed. KVV Art. 60: "wird in der Regel jährlich herausgegeben" | Excel sheets "Deutsch", "Français", "Italiano"; has a "Limitationen" column | KLV Art. 28 Abs. 2: "Die Analysenliste wird in der AS und in der SR nicht veröffentlicht. Die Änderungen und konsolidierte Fassungen der Liste werden auf der Website des BAG publiziert." |
| GG-SL / GGML (Geburtsgebrechen-Spezialitätenliste) | published with the SL: https://www.sl.bag.admin.ch/resources/current-and-archived-data | monthly, same cycle as the SL (Handbuch A.6.1) | DE/FR/IT (same per-language files) | SL app label "Aktueller Datenstamm (SL/GGSL/GGML)" |
| Geburtsgebrechenliste (GgV-EDI, SR 831.232.211, Anhang) | https://www.fedlex.admin.ch/eli/cc/2021/708/de | Fedlex SPARQL lists one consolidation only, 2022-01-01 ("Stand am 1. Januar 2022") | DE/FR/IT (in SR, so PublG Art. 14 applies) | Art. 1: "Die Geburtsgebrechen [...] sind im Anhang aufgeführt." |
| Fedlex AS / SR (federal law) | https://www.fedlex.admin.ch ; SPARQL https://fedlex.data.admin.ch/sparqlendpoint | PublV Art. 34 Abs. 2: "Die AS und das BBl erscheinen in der Regel an jedem Arbeitstag." Abs. 3: "Die Online-Version der SR wird laufend nachgeführt." | DE/FR/IT equally binding for Erlasse (PublG Art. 14 Abs. 1); RM/EN translations under Art. 13a Abs. 1 lit. d | Machine-readable: per-language HTML/XML manifestations via the SPARQL endpoint (used for this document) |
| Graubünden (trilingual DE/RM/IT) | https://www.gr-lex.gr.ch | **UNVERIFIED** | DE, RM, IT | KV GR Art. 3 Abs. 1 (per search result, not fetched): "Deutsch, Rätoromanisch und Italienisch sind die gleichwertigen Landes- und Amtssprachen des Kantons." SpG GR (BR 492.100, Stand 1.1.2025) Art. 3 Abs. 1: "Die Amtssprachen des Kantons finden Anwendung in Rechtssetzung, Rechtsanwendung und Rechtsprechung." Art. 4 Abs. 3: texts for the Bündner Rechtsbuch "müssen für die Behandlung im Grossen Rat [...] in allen Amtssprachen vorliegen." (copy: https://gr.lexwork.naz.ch/de/dta/492.100.pdf). Explicit equal-authenticity clause: **UNVERIFIED** |
| Bern (DE/FR) | https://www.belex.sites.be.ch | PuG Art. 20 Abs. 3 (copy): BSG "wird jährlich mehrmals auf bestimmte Stichtage nachgeführt" | DE, FR | PuG (BSG 103.1, Stand 01.12.2021) **Art. 11** Abs. 1: "Die deutsche und die französische Fassung der in der Bernischen Amtlichen Gesetzessammlung veröffentlichten kantonalen Erlasse sind in gleicher Weise massgebend." (copy: https://be.lexwork.naz.ch/de/dta/103.1.pdf) |
| Fribourg (FR/DE) | https://bdlf.fr.ch | **UNVERIFIED** | FR, DE | LPAL (RSF 124.1, version in force 01.01.2024) Art. 20 Abs. 1: "Les deux versions linguistiques font foi de manière égale." (copy: https://fr.lexwork.naz.ch/fr/dta/124.1.pdf) |
| Valais (FR/DE) | https://lex.vs.ch | **UNVERIFIED** | FR, DE | Equal-authenticity provision: **UNVERIFIED** |

The lexwork.naz.ch links are third-party copies. Check the official cantonal portals before citing them.

---

## 7. Translation volume, cost, timeliness

- **Cost per translated page (EFD only)**: Staatsrechnung 2023, Band 2B, Generalsekretariat EFD, "Sprachdienste".
  - "Durchschnittliche Kosten pro übersetzter Seite (CHF)": **252** (R 2022), **260** (VA 2023), **267** (R 2023).
  - Comment: "Die durchschnittlichen Kosten pro übersetzte Seite werden auf Basis der Vollkosten berechnet. 2023 liegen sie sieben Franken über dem Sollwert."
  - https://www.efv.admin.ch/dam/de/sd-web/HovZzpOGQhzq/SR%20Staatsrechnung%20-%20Band%202B_DE.pdf
  - This is one department, not the Federal Chancellery.
- **Staffing (whole federal administration)**: LeGes 2020/3, "Maschinelle Übersetzung": "In den Sprachdiensten der Bundesverwaltung arbeiten circa 420 Sprachfachleute (zumeist Übersetzer/innen) auf circa 330 Vollzeitstellen. Von den ungefähr 36 000 Vollzeitstellen der Bundesverwaltung sind also etwas weniger als 1 Prozent Sprachdienststellen." https://leges.weblaw.ch/legesissues/2020/3/maschinelle-ubersetz_f92b5ffeea.html
- **Federal Council answer to Interpellation 22.4284** (2022): no figures. Quote: the Federal Council "ist bestrebt sicherzustellen, dass die Sprachdienste der Bundesverwaltung über genügend eigene Mitarbeiterinnen und Mitarbeiter, eine moderne Arbeitsplatzinfrastruktur und genügend finanzielle Ressourcen verfügen". Source: https://ws.parlament.ch/odata.svc/Business(ID=20224284,Language='DE')
- **Federal Chancellery central language services, pages per year or total cost: UNVERIFIED** (no current public figure found).
- **SL timeliness rule** (SL Handbuch A.6.1, see 2.2): changes take effect on the 1st of the month. Files are available on the 27th of the previous month, and changes remain possible until the last day of that month.
- **SL translation backlog: UNVERIFIED** (no public figure found).
