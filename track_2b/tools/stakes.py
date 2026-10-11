"""What the confirmed audit divergences put at stake, in Swiss francs, per patient: illustrative figures computed only from
the published 6 Oct 2026 SL feed (texts and pack prices), with every assumption stated and every formula shown.
Deterministic, stdlib only, no model, no network.

  python3 tools/stakes.py                       write eval/results/stakes.json from the committed inputs
  python3 tools/stakes.py --check               recompute and compare with eval/results/stakes.json (exit 1 if different)
  python3 tools/stakes.py --extract FEED.ndjson re-extract data/audit/prices_20261006.json from the public DE feed file
                                                (https://epl.bag.admin.ch/static/sl/publication/fhir/
                                                 foph-sl-publication-20261006-de.ndjson; its sha256 is recorded)

Inputs (all committed): data/audit/prices_20261006.json (every reimbursed pack whose SL entry carries one of the limitations
below: GTIN, description, public price = the feed's 'Retail price', ex-factory price, price-model flag), the three texts
of each limitation (data/audit/audit_texts_20261006.json), the blind confirmations (eval/labels/audit_relabel.tsv,
majority 'real'; eval/labels/audit_r15_20261006.tsv for the experimental Amvuttra operator finding).

What this is not: no patient counts are known from any public source in the repository, so no figure is multiplied by a
population; nothing here is a national cost. Published prices are list prices: where the SL entry carries a price model
(confidential refund), the net price is lower and not public, and the entry says so. A year is 52 weeks."""
import csv, hashlib, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DATE = "20261006"
FEED = f"https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-{DATE}-de.ndjson"
PRICES = os.path.join(ROOT, "data", "audit", f"prices_{DATE}.json")
TEXTS = os.path.join(ROOT, "data", "audit", f"audit_texts_{DATE}.json")
LABELS = os.path.join(ROOT, "eval", "labels")
OUT = os.path.join(ROOT, "eval", "results", "stakes.json")
WEEKS = 52
KEYS = ("NEMLUVIO.01", "DIAPHIN.6-", "CRESE.Kps.IM", "BENEPALI4", "ERELZI2", "NEPEXTO", "DUPIXENT.02", "DUPIXENT.02P",
        "DUPIXENT.05a", "DUPIXENT.05P", "AMVUTTRA.01a")


# ------------------------------------------------------------------ price extraction from the public feed (one-off)
def extract(feed):
    """-> the prices file content: every pack whose 'Reimbursement SL' authorisation references one of KEYS."""
    h = hashlib.sha256(); packs = []
    with open(feed, "rb") as f:
        for raw in f:
            h.update(raw)
            if not raw.strip() or not any(k.encode() in raw for k in KEYS): continue
            b = json.loads(raw); E = [e["resource"] for e in b.get("entry", [])]
            ppd = {r["id"]: r for r in E if r["resourceType"] == "PackagedProductDefinition"}
            for r in E:
                if r["resourceType"] != "RegulatedAuthorization": continue
                if not any(c.get("display") == "Reimbursement SL" for c in r.get("type", {}).get("coding", [])): continue
                lims = [s["valueReference"]["reference"].split("/", 1)[1]
                        for ind in r.get("indication", []) or [] for ex in ind.get("extension", [])
                        for s in ex.get("extension", []) if s.get("url") == "limitationIndication"]
                if not set(lims) & set(KEYS): continue
                p = ppd[r["subject"][0]["reference"].split("/", 1)[1]]
                rec = dict(description=p.get("description"), gtin=next((i["value"] for i in (p.get("packaging") or {}).get("identifier", [])), None),
                           limitations=sorted(set(lims)), public_price=None, ex_factory_price=None, price_model=False)
                for x in r.get("extension", [{}])[0].get("extension", []):
                    if x["url"] == "priceModel": rec["price_model"] = bool(x["valueBoolean"])
                    if x["url"] == "FOPHDossierNumber": rec["dossier"] = x["valueIdentifier"]["value"]
                    if x["url"].endswith("/productPrice"):
                        d = {y["url"]: y for y in x["extension"]}
                        t = d["type"]["valueCodeableConcept"]["coding"][0]["display"]
                        v = d["value"]["valueMoney"]["value"]
                        if t == "Retail price": rec["public_price"] = v
                        elif t == "Ex-factory price": rec["ex_factory_price"] = v
                packs.append(rec)
    packs.sort(key=lambda r: (r["description"] or "", r["gtin"] or ""))
    return dict(note="Pack prices of the SL entries carrying the audited limitations, extracted from the public 6 Oct 2026 SL feed "
                     "(DE file; prices are language-independent) by tools/stakes.py --extract. public_price = the feed's 'Retail price' "
                     "(Publikumspreis), ex_factory_price = 'Ex-factory price' (Fabrikabgabepreis), CHF incl. VAT for the public price. "
                     "price_model true = the SL entry has a price model (confidential refund; the net price is not public).",
                date=DATE, source=FEED, source_sha256=h.hexdigest(), keys=list(KEYS), packs=packs)


# ------------------------------------------------------------------ inputs
def _load():
    P = json.load(open(PRICES, encoding="utf-8"))
    T = json.load(open(TEXTS, encoding="utf-8"))["texts"]
    return P, T


def _tsv(name): return list(csv.DictReader(open(os.path.join(LABELS, name), encoding="utf-8"), delimiter="\t"))


def confirmations(T):
    """{(limitation key, lang): (uid, final label)} for the register findings (audit_relabel.tsv, majority label), mapped
    to their limitation by the worklist record's DE and target texts; plus the round-5 operator finding (audit_r15)."""
    W = json.load(open(os.path.join(LABELS, f"audit_{DATE}_worklist.json"), encoding="utf-8"))
    by_text = {(v.get("de"), L, v.get(L)): k for k, v in T.items() for L in ("fr", "it")}
    lab = {r["uid"]: r["final"] for r in _tsv("audit_relabel.tsv")}
    out = {}
    for r in W:
        k = by_text.get((r["de"], r["lang"], r["target"])); uid = f"audit_{DATE}:{r['id']}"
        if k and uid in lab: out[(k, r["lang"])] = (uid, lab[uid])
    for r in _tsv(f"audit_r15_{DATE}.tsv"): out.setdefault((r["cud"], r["lang"]), (f"audit_r15_{DATE}:{r['fid']}", r["final"]))
    return out


def quote(T, key, lang, s):
    """the verbatim phrase s from the published text; raises if the text does not contain it (the figure would be unfounded)."""
    if s not in T[key][lang]: raise AssertionError(f"{key} [{lang}] does not contain {s!r}")
    return dict(limitation=key, lang=lang, text=s)


def pack(P, key, pred):
    """the single pack of the entries carrying `key` whose description satisfies pred."""
    c = [p for p in P["packs"] if key in p["limitations"] and pred(p["description"])]
    if len({(p["public_price"], p["ex_factory_price"]) for p in c}) != 1 or not c:
        raise AssertionError(f"{key}: expected one price among {[p['description'] for p in c]}")
    p = dict(c[0]); p["gtins"] = sorted(x["gtin"] for x in c); p.pop("gtin", None)
    return p


def r2(x): return round(x + 1e-9, 2)


def units(desc):
    """pens/syringes in a pack, from the published description ('Fertpen 4 Stk', '2 Fertspr 1 ml', 'Fertigspr 4 Fertspr 1 ml')."""
    m = re.findall(r"\b(\d+) (?:Stk|Fertspr|Fertpen)\b", desc)
    if len(set(m)) != 1: raise AssertionError(f"cannot read the pack size of {desc!r}")
    return int(m[0])


# ------------------------------------------------------------------ the cases
def compute():
    P, T = _load(); C = confirmations(T); cases = []

    def confirmed(key, lang):
        uid, lab = C[(key, lang)]
        if lab != "real": raise AssertionError(f"{key} {lang}: {uid} is {lab!r}, not confirmed real")
        return dict(uid=uid, label=lab)

    # 1 Nemluvio: maintenance every 8 weeks (DE, FR) vs every 4 weeks (IT); one 30 mg pen per dose
    k = "NEMLUVIO.01"; pk = pack(P, k, lambda d: "30 mg" in d and "1 Stk" in d)
    q8, q4 = WEEKS / 8, WEEKS / 4; extra = q4 - q8
    cases.append(dict(
        id="nemluvio", product="Nemluvio", limitation=k, kind="price", confirmed=confirmed(k, "it"),
        evidence=[quote(T, k, "de", "danach in einer Erhaltungsdosis von 30 mg als subkutane Injektion alle acht Wochen"),
                  quote(T, k, "fr", "puis d'une dose d'entretien de 30 mg par la suite, en injection sous-cutanée toutes les huit semaines"),
                  quote(T, k, "it", "successivamente in una dose di mantenimento di 30 mg come iniezione sottocutanea ogni quattro settimane"),
                  quote(T, k, "de", "(ohne Preismodell)")],
        pack=pk, doses_per_year_de_fr=q8, doses_per_year_it=q4, extra_doses_per_year=extra,
        chf_per_dose=pk["public_price"], chf_per_patient_year=r2(extra * pk["public_price"]),
        formula=f"({WEEKS}/4 - {WEEKS}/8) maintenance doses x CHF {pk['public_price']:.2f} per 30 mg pen = {extra} x {pk['public_price']:.2f}",
        assumptions=["maintenance phase (after week 16), a 52-week year", "one 30 mg pen per maintenance dose (the text: 'Erhaltungsdosis von 30 mg')",
                     "public price of the 1-pen pack; this indication is listed without a price model ('ohne Preismodell'), so the list price applies"],
        reading=("Read in Italian, an insurer would reimburse 6.5 more pens per patient per maintenance year than the German and "
                 "French texts allow; read in German or French, a patient whose prescriber follows the Italian text would be refused them.")))

    # 2 Diaphin: distribution surcharge 6 % (DE, FR) vs 12 % (IT) on the ex-factory price, VAT on top, no per-pack surcharge
    k = "DIAPHIN.6-"; rows = []
    for p in sorted((p for p in P["packs"] if k in p["limitations"]), key=lambda p: p["description"]):
        vat = p["public_price"] / (p["ex_factory_price"] * 1.06) - 1
        d = p["public_price"] * (1.12 - 1.06) / 1.06
        rows.append(dict(description=p["description"], gtin=p["gtin"], ex_factory_price=p["ex_factory_price"], public_price=p["public_price"],
                         implied_vat_pct=round(100 * vat, 2), public_price_at_12pct=r2(p["public_price"] * 1.12 / 1.06),
                         chf_difference_per_pack=r2(d)))
    if not all(abs(r["implied_vat_pct"] - 2.6) < 0.1 for r in rows): raise AssertionError(f"Diaphin: published prices do not follow 6 % + 2.6 % VAT: {rows}")
    cases.append(dict(
        id="diaphin", product="Diaphin", limitation=k, kind="price", confirmed=confirmed(k, "it"),
        evidence=[quote(T, k, "de", "zuzüglich dem preisbezogenen Zuschlag von 6% zuzüglich MWST"),
                  quote(T, k, "fr", "plus la prime relative au prix de 6%, TVA en sus"),
                  quote(T, k, "it", "più il supplemento attinente al prezzo di 12% più la IVA"),
                  quote(T, k, "de", "ohne Zuschlag je Packung")],
        packs=rows, pct_of_public_price=round(100 * (1.12 - 1.06) / 1.06, 2),
        chf_difference_per_pack_min=min(r["chf_difference_per_pack"] for r in rows),
        chf_difference_per_pack_max=max(r["chf_difference_per_pack"] for r in rows),
        formula="public price x (1.12 - 1.06) / 1.06 per pack (the published price is ex-factory x 1.06 x (1 + VAT); VAT cancels)",
        assumptions=["the published public price follows the German/French 6 % (checked: every pack's implied VAT is 2.6 %, the Swiss rate for medicines)",
                     "no per-pack surcharge in either reading (all three texts)",
                     "per pack only: the text gives no dose or pack frequency, so no annual figure"],
        reading=("Read in Italian, each pack would be priced (and reimbursed) higher by this amount; read in German or French, "
                 "the published price stands and a pharmacy applying the Italian text would charge above it.")))

    # 3 Cresemba: FR omits the minimum body weight of 16 kg (paediatric mucormycosis)
    k = "CRESE.Kps.IM"
    rows = [dict(description=p["description"], gtin=p["gtin"], public_price=p["public_price"], ex_factory_price=p["ex_factory_price"])
            for p in sorted((p for p in P["packs"] if k in p["limitations"] and "Kaps" in p["description"]), key=lambda p: p["description"])]
    cases.append(dict(
        id="cresemba", product="Cresemba", limitation=k, kind="eligibility", confirmed=confirmed(k, "fr"),
        evidence=[quote(T, k, "de", "ab dem Alter von 6 Jahren und mit einem Körpergewicht von mindestens 16 kg vergütet"),
                  quote(T, k, "fr", "chez les adultes et les patients pédiatriques à partir de 6 ans.")],
        packs=rows, chf_per_pack=rows[0]["public_price"] if len({r["public_price"] for r in rows}) == 1 else None,
        formula="public price per capsule pack (no annual figure)",
        assumptions=["per pack only: the limitation gives no dose or treatment duration"],
        reading=("Read in French, a child from 6 years weighing under 16 kg is eligible; read in German or Italian, that child's "
                 "treatment is not reimbursed.")))

    # 4 Etanercept biosimilars: FR adds 'patients weighing >= 62.5 kg' to juvenile arthritis
    rows = []
    for k, name in (("BENEPALI4", "Benepali"), ("ERELZI2", "Erelzi"), ("NEPEXTO", "Nepexto")):
        cf = confirmed(k, "fr")
        quote(T, k, "fr", "de l'arthrite chronique juvénile polyarticulaire active chez les patients pesant ≥ 62.5 kg")
        quote(T, k, "de", "der aktiven juvenilen chronischen Arthritis mit polyartikulärem Verlauf")
        quote(T, k, "de", "Standarddosierung pro Behandlungszyklus: 1 x 50 mg pro Woche")
        c = [dict(description=p["description"], gtin=p["gtin"], public_price=p["public_price"], units=units(p["description"]))
             for p in P["packs"] if k in p["limitations"] and "50 mg/ml" in p["description"]]
        per50 = min(x["public_price"] / x["units"] for x in c)
        rows.append(dict(product=name, limitation=k, confirmed=cf, packs=c, chf_per_50mg=r2(per50), chf_per_patient_year=r2(WEEKS * per50)))
    cases.append(dict(
        id="etanercept", product="Benepali, Erelzi, Nepexto (etanercept)", limitation="BENEPALI4, ERELZI2, NEPEXTO", kind="eligibility",
        evidence=[quote(T, "BENEPALI4", "fr", "chez les patients pesant ≥ 62.5 kg"),
                  quote(T, "BENEPALI4", "de", "Standarddosierung pro Behandlungszyklus: 1 x 50 mg pro Woche")],
        products=rows, chf_per_patient_year_min=min(r["chf_per_patient_year"] for r in rows),
        chf_per_patient_year_max=max(r["chf_per_patient_year"] for r in rows),
        formula=f"{WEEKS} weeks x (public price of a 50 mg/ml pack / number of 1 ml pens or syringes in it), cheapest pack per product",
        assumptions=["the only dose the limitation states (1 x 50 mg per week, given in its psoriasis paragraph) applied for a full year; "
                     "the juvenile arthritis paragraph states none, and a patient under 62.5 kg may need less, so this is an upper bound",
                     "the cheapest 50 mg pack of each product, per pen or syringe"],
        reading=("Read in French, a young patient under 62.5 kg with polyarticular juvenile arthritis is not reimbursed; read in German "
                 "or Italian, the patient is.")))

    # 5 Dupixent: the 15 to < 30 kg tier
    p200 = pack(P, "DUPIXENT.02", lambda d: "200 mg" in d and "2 " in d and "Fertspr" in d)
    p300 = pack(P, "DUPIXENT.02", lambda d: "300 mg" in d and "2 " in d and "Fertspr" in d)
    c200, c300 = p200["public_price"] / 2, p300["public_price"] / 2
    ad_de, ad_fr = (WEEKS / 4) * c300, (WEEKS / 2) * c200
    for k in ("DUPIXENT.02", "DUPIXENT.02P"):
        quote(T, k, "de", "bei Patienten mit einem Körpergewicht ab 15 kg bis unter 30 kg")
        quote(T, k, "de", "gefolgt von einer Dosis von 300 mg als subkutane Injektion alle vier Wochen")
        quote(T, k, "fr", "pour les patients pesant moins de 60 kg à une dose initiale de 400 mg")
        quote(T, k, "fr", "suivie d'une dose de 200 mg en injection sous- cutanée toutes les deux semaines")
    for k in ("DUPIXENT.05a", "DUPIXENT.05P"):
        quote(T, k, "de", "300 mg alle 4 Wochen bei einem Körpergewicht von 15 - < 60 kg")
        quote(T, k, "fr", "300 mg toutes les 4 semaines pour un poids corporel de 30 kg à moins de 60 kg")
    cases.append(dict(
        id="dupixent", product="Dupixent", limitation="DUPIXENT.02, .02P (atopic dermatitis 12-17); DUPIXENT.05a, .05P (asthma 6-11)",
        kind="eligibility", confirmed=[confirmed(k, "fr") for k in ("DUPIXENT.02", "DUPIXENT.02P", "DUPIXENT.05a", "DUPIXENT.05P")],
        packs=dict(mg200=p200, mg300=p300), chf_per_200mg=r2(c200), chf_per_300mg=r2(c300),
        asthma=dict(chf_per_patient_year=r2((WEEKS / 4) * c300), formula=f"{WEEKS}/4 doses x CHF {c300:.3f} per 300 mg syringe",
                    reading=("A child of 6 to 11 weighing 15 to under 30 kg: read in German or Italian, 300 mg every 4 weeks is "
                             "reimbursed; read in French, no regimen covers that weight.")),
        atopic_dermatitis=dict(chf_per_patient_year_de=r2(ad_de), chf_per_patient_year_fr=r2(ad_fr), chf_difference=r2(ad_fr - ad_de),
                               formula=f"FR {WEEKS}/2 x CHF {c200:.3f} (200 mg every 2 weeks) - DE {WEEKS}/4 x CHF {c300:.3f} (300 mg every 4 weeks)",
                               reading=("An adolescent of 12 to 17 weighing 15 to under 30 kg: the German text reimburses 300 mg every 4 weeks, "
                                        "the French text (one tier for everyone under 60 kg) 200 mg every 2 weeks.")),
        assumptions=["maintenance year only (loading doses excluded), a 52-week year",
                     "one prefilled syringe per dose; public price of the 2-syringe pack / 2 (pens are priced the same where listed)",
                     "Dupixent's SL entry carries a price model: the net price is lower and not public"],
        price_model=p300["price_model"]))

    # 6 Amvuttra (experimental operator check, confirmed): the French stop rule says NIS increase '<= 10' where DE/IT say '> 10'
    k = "AMVUTTRA.01a"; pk = pack(P, k, lambda d: "25 mg" in d)
    per_year = 4
    cases.append(dict(
        id="amvuttra", product="Amvuttra", limitation=k, kind="eligibility", experimental=True, confirmed=confirmed(k, "fr"),
        evidence=[quote(T, k, "de", "AMVUTTRA wird nicht mehr vergütet, wenn eine Progression unter Therapie auftritt"),
                  quote(T, k, "de", "• NIS-Zunahme > 10 Punkte und • Zunahme im PND-Score um > 1 Stufe"),
                  quote(T, k, "fr", "• augmentation du score NIS ≤ 10 points et • augmentation du score PND > 1 stade"),
                  quote(T, k, "it", "• aumento del NIS > 10 punti e • aumento del punteggio PND di > 1 livello"),
                  quote(T, k, "de", "für jede bezogene Packung AMVUTTRA einen festgelegten Betrag des Fabrikabgabepreises zurück")],
        pack=pk, chf_per_dose=pk["public_price"], doses_per_year=per_year, chf_per_patient_year=r2(per_year * pk["public_price"]),
        formula=f"{per_year} doses x CHF {pk['public_price']:.2f} per 25 mg syringe",
        assumptions=["one 25 mg syringe every 3 months: the authorised dosing interval of the product information, NOT stated in the "
                     "SL text (the only input here that is not in the feed); the per-dose figure needs no assumption",
                     "list price: the SL entry has a price model and the text says the manufacturer refunds an undisclosed fixed "
                     "amount per pack, so the net cost is lower"],
        reading=("A patient after 24 months whose NIS rose by 10 points or less with a PND increase of more than one stage: read in "
                 "French, reimbursement stops; read in German or Italian, it continues.")))

    head = dict(nemluvio_chf_per_patient_year=cases[0]["chf_per_patient_year"], nemluvio_extra_doses=cases[0]["extra_doses_per_year"],
                diaphin_pct=cases[1]["pct_of_public_price"], amvuttra_chf_per_dose=cases[5]["chf_per_dose"],
                amvuttra_chf_per_patient_year=cases[5]["chf_per_patient_year"],
                etanercept_chf_per_patient_year_max=cases[3]["chf_per_patient_year_max"],
                dupixent_asthma_chf_per_patient_year=cases[4]["asthma"]["chf_per_patient_year"])
    return dict(date=DATE, generated_by="python3 tools/stakes.py", model_calls=0, source=P["source"], source_sha256=P["source_sha256"],
                scope=("per patient only: no public source in the repository gives patient counts, so no population or national total "
                       "is estimated; list prices (public price incl. VAT) as published on 6 Oct 2026"),
                weeks_per_year=WEEKS, headline=head, cases=cases)


def dumps(o): return json.dumps(o, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main(argv):
    if "--extract" in argv:
        d = extract(argv[argv.index("--extract") + 1])
        open(PRICES, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
        print(PRICES, len(d["packs"]), "packs"); return 0
    s = dumps(compute())
    if "--check" in argv:
        same = json.load(open(OUT, encoding="utf-8")) == json.loads(s)
        print("stakes:", "OK" if same else "DIFFERS"); return 0 if same else 1
    open(OUT, "w", encoding="utf-8").write(s); print(OUT); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
