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
Several records, one output id: BAG can merge old limitations into one new CUD id (Sept -> Oct 2026: SKYRIZI.01Pe and
SKYRIZI.01 became one id). The ePL has exactly one CUD per id, so the drafts of one language that map to the same id are
merged deterministically into ONE CUD: identical drafts -> that text, verdict flagged if any of them is flagged; different
drafts -> the first draft in (ready before flagged, then item key) order, verdict always flagged ("drafts differ"), and
the other drafts stay readable in their own Provenance. Every item keeps its own Provenance (target = the shared CUD,
revision = its own old limitation code, extension merged = the keys of the other items).
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


DISPLAY = {"ready": "Guards passed: ready for translator review", "flagged": "Flagged by the guards: needs translator work",
           "merged": "Several previous limitations merged into this id and their drafts differ: needs translator work"}


def cud(v, status=None, display=None):
    """The draft CUD: the ePL shape plus status, verdict tag, profile and language."""
    status = status or v["status"]
    return {"resourceType": "ClinicalUseDefinition", "id": v["cud_id"],
            "meta": {"profile": [CUD_PROFILE],
                     "tag": [{"system": VERDICT_CS, "code": status, "display": display or DISPLAY[status]}]},
            "language": LANGS[v["lang"]],
            "text": {"status": "generated", "div": XHTML.format(html.escape(v["draft"], quote=False))},
            "type": "indication",
            "status": {"coding": [{"system": "http://hl7.org/fhir/publication-status", "code": "draft", "display": "Draft"}]},
            "indication": {"diseaseSymptomProcedure": {"concept": {"text": v["draft"]}}}}


def devices(meta):
    """The two agents: the model that drafted the wording and the pipeline that placed numbers and ran the guards."""
    model = {"resourceType": "Device", "id": _uuid("device", meta["model"]), "status": "active",
             "displayName": f"Apertus ({meta['model']})" if meta.get("model_known", True) else "Drafting model (not named in the records)",
             "manufacturer": "Swiss AI Initiative",
             "name": [{"value": meta["model"], "type": "user-friendly-name"}],
             "version": [{"type": {"text": "model"}, "value": meta["model"]}]}
    pipe = {"resourceType": "Device", "id": _uuid("device", meta["pipeline"]), "status": "active",
            "displayName": "Gleichlaut guarded drafting pipeline",
            "name": [{"value": "Gleichlaut", "type": "user-friendly-name"}],
            "version": [{"type": {"text": "pipeline"}, "value": meta["pipeline"]},
                        {"type": {"text": "recorded run"}, "value": f"{meta['run']} (outputs sha256:{meta['run_sha256']})"}]}
    return model, pipe


def provenance(v, meta, model, pipe, merged=()):
    ext = [{"url": "verdict", "valueCode": v["status"]}, {"url": "item", "valueString": v["key"]}]
    if merged:
        ext.append({"url": "merged", "valueString": "same output id as " + ", ".join(merged)})
        ext.append({"url": "draft", "valueString": v["draft"]})
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
                       {"role": "revision", "what": {"identifier": {"system": EPL + "ClinicalUseDefinition", "value": v.get("old_id") or v["cud_id"]},
                                                     "display": f"previous limitation text ({L}), SL snapshot {v['snap_old']}"}}]}


def by_output_id(V):
    """-> [(cud_id, [views])] in order of first appearance (several records can map to one new CUD id)."""
    G = {}
    for v in V: G.setdefault(v["cud_id"], []).append(v)
    return list(G.items())


def merged_cud(vs):
    """One CUD for every draft that maps to the same output id (see the module docstring)."""
    if len(vs) == 1: return cud(vs[0])
    order = sorted(vs, key=lambda v: (v["status"] != "ready", v["key"]))
    if len({v["draft"] for v in vs}) == 1:
        return cud(order[0], "flagged" if any(v["status"] == "flagged" for v in vs) else "ready")
    return cud(order[0], "flagged", DISPLAY["merged"])


def bundle(views, meta, lang):
    """One collection Bundle per target language, like the per-language ePL files."""
    V = [v for v in views if v["lang"] == lang]
    model, pipe = devices(meta)
    entries = []
    for cid, vs in by_output_id(V):
        entries.append({"fullUrl": EPL + "ClinicalUseDefinition/" + cid, "resource": merged_cud(vs)})
        for v in vs:
            p = provenance(v, meta, model, pipe, [w["key"] for w in vs if w is not v])
            entries.append({"fullUrl": "urn:uuid:" + p["id"], "resource": p})
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
