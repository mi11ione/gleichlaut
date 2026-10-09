"""FHIR R5 output in the shape of BAG's ePL feed: one collection Bundle per target language, one ClinicalUseDefinition
(CUD) per draft, plus who-made-it and what-the-guards-said as standard resources.

Shape, read off the ePL feed (5 Oct 2026, 5,010 CUD entries per language; validate.survey):
  fullUrl  http://fhir.epl.bag.admin.ch/ClinicalUseDefinition/<id>, id = limitation code (emit.cud_id)
  resource id, text{status: generated, div: <div xmlns=xhtml>escaped text</div>}, type: indication,
           indication.diseaseSymptomProcedure.concept.text = the limitation text (the feed carries nothing else).
The draft keeps exactly that and adds only standard R5 elements, so an ePL reader sees the same CUD:
  status    = publication-status 'draft' for every item: no draft is a published limitation, ready or not.
  meta.tag  = the guard verdict (ready | flagged); meta.tag is FHIR's slot for workflow labels and needs no profile.
  meta.profile = ch-idmp-clinicalusedefinition-indication (CH EPL IG 1.0.1), the profile the CUDs are validated against.
  language  = fr-CH / it-CH (the feed leaves it implicit in the per-language file; a single draft file needs it).
Why/by whom (Provenance, one per CUD): target = the CUD; agent author = the model (Device), assembler = the Gleichlaut
pipeline (Device, version = package + guard stack + freeze sha256); entity source = the new German text, revision = the
old FR/IT text (by limitation code and snapshot); one extension carries the per-guard results and the complaint.
The Bundle does not claim the ch-idmp-bundle profile: that profile requires the product's MedicinalProductDefinition,
PackagedProductDefinition and Ingredient entries, which a translation draft does not carry."""
import html, os, uuid
from . import dump_json

EPL = "http://fhir.epl.bag.admin.ch/"
CUD_PROFILE = "http://fhir.ch/ig/ch-epl/StructureDefinition/ch-idmp-clinicalusedefinition-indication"
CANON = "urn:gleichlaut:fhir"           # Gleichlaut's own code system / extension namespace (no domain of ours to claim)
VERDICT_CS = CANON + ":CodeSystem:guard-verdict"
VERDICT_EXT = CANON + ":StructureDefinition:guard-verdict"
LANGS = {"fr": "fr-CH", "it": "it-CH"}
XHTML = '<div xmlns="http://www.w3.org/1999/xhtml">{}</div>'


def _uuid(*parts): return str(uuid.uuid5(uuid.NAMESPACE_URL, CANON + ":" + ":".join(parts)))


def cud(v):
    """The draft CUD: the ePL shape plus status, verdict tag, profile and language."""
    return {"resourceType": "ClinicalUseDefinition", "id": v["cud_id"],
            "meta": {"profile": [CUD_PROFILE],
                     "tag": [{"system": VERDICT_CS, "code": v["status"],
                              "display": "Guards passed: ready for translator review" if v["status"] == "ready"
                              else "Flagged by the guards: needs translator work"}]},
            "language": LANGS[v["lang"]],
            "text": {"status": "generated", "div": XHTML.format(html.escape(v["draft"], quote=False))},
            "type": "indication",
            "status": {"coding": [{"system": "http://hl7.org/fhir/publication-status", "code": "draft", "display": "Draft"}]},
            "indication": {"diseaseSymptomProcedure": {"concept": {"text": v["draft"]}}}}


def devices(meta):
    """The two agents: the model that drafted the wording and the pipeline that placed numbers and ran the guards."""
    model = {"resourceType": "Device", "id": _uuid("device", meta["model"]), "status": "active",
             "displayName": f"Apertus ({meta['model']})", "manufacturer": "Swiss AI Initiative",
             "name": [{"value": meta["model"], "type": "user-friendly-name"}],
             "version": [{"type": {"text": "model"}, "value": meta["model"]}]}
    pipe = {"resourceType": "Device", "id": _uuid("device", meta["pipeline"]), "status": "active",
            "displayName": "Gleichlaut guarded drafting pipeline",
            "name": [{"value": "Gleichlaut", "type": "user-friendly-name"}],
            "version": [{"type": {"text": "pipeline"}, "value": meta["pipeline"]},
                        {"type": {"text": "recorded run"}, "value": f"{meta['run']} (outputs sha256:{meta['run_sha256']})"}]}
    return model, pipe


def provenance(v, meta, model, pipe):
    ext = [{"url": "verdict", "valueCode": v["status"]}, {"url": "item", "valueString": v["key"]}]
    for gid, lab, state, detail in v["lights"]:
        ext.append({"url": "guard", "extension": [{"url": "name", "valueCode": gid}, {"url": "result", "valueCode": state},
                                                  {"url": "detail", "valueString": detail}]})
    if v["complaint"]: ext.append({"url": "complaint", "valueString": v["complaint"]})
    nums = [f"{t}={'code' if who == 'code' else 'model'}" + (f" {s}" if s else "") for _, _, t, who, s in v["numbers"]]
    if nums: ext.append({"url": "numbers", "valueString": "; ".join(nums)})
    L = LANGS[v["lang"]]
    return {"resourceType": "Provenance", "id": _uuid("provenance", meta["run"], v["key"]),
            "extension": [{"url": VERDICT_EXT, "extension": ext}],
            "target": [{"reference": EPL + "ClinicalUseDefinition/" + v["cud_id"]}],
            "policy": [f"urn:sha256:{meta['pipeline'].rsplit(':', 1)[1]}"],
            "activity": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-DataOperation", "code": "CREATE", "display": "create"}],
                         "text": "machine draft of the amended limitation text"},
            "agent": [{"type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type", "code": "author", "display": "Author"}]},
                       "who": {"reference": "urn:uuid:" + model["id"], "display": model["displayName"]}},
                      {"type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type", "code": "assembler", "display": "Assembler"}]},
                       "who": {"reference": "urn:uuid:" + pipe["id"], "display": pipe["displayName"]}}],
            "entity": [{"role": "source", "what": {"identifier": {"system": EPL + "ClinicalUseDefinition", "value": v["cud_id"]},
                                                   "display": f"German limitation text (de-CH), SL snapshot {v['snap_new']}"}},
                       {"role": "revision", "what": {"identifier": {"system": EPL + "ClinicalUseDefinition", "value": v["cud_id"]},
                                                     "display": f"previous limitation text ({L}), SL snapshot {v['snap_old']}"}}]}


def bundle(views, meta, lang):
    """One collection Bundle per target language, like the per-language ePL files."""
    V = [v for v in views if v["lang"] == lang]
    model, pipe = devices(meta)
    entries = []
    for v in V:
        entries.append({"fullUrl": EPL + "ClinicalUseDefinition/" + v["cud_id"], "resource": cud(v)})
        p = provenance(v, meta, model, pipe); entries.append({"fullUrl": "urn:uuid:" + p["id"], "resource": p})
    entries += [{"fullUrl": "urn:uuid:" + d["id"], "resource": d} for d in (model, pipe)]
    return {"resourceType": "Bundle", "id": _uuid("bundle", meta["run"], lang, *[v["key"] for v in V]), "type": "collection",
            "entry": entries}


def write(views, meta, out_dir):
    """-> [paths]: out_dir/gleichlaut-<run>-<lang>.fhir.json per target language present."""
    paths = []
    for lang in LANGS:
        if not any(v["lang"] == lang for v in views): continue
        p = os.path.join(out_dir, f"gleichlaut-{meta['run']}-{LANGS[lang]}.fhir.json")
        dump_json(bundle(views, meta, lang), p); paths.append(p)
    return paths
