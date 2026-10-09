"""FHIR emit: 10 recorded fresh-166 drafts -> ePL-shaped Bundles that pass the profile check and feed parity, carry the
draft status and guard verdict machine-readably, and never contain the official FR/IT text.
Runs under pytest or as `python3 tests/test_emit_fhir.py`."""
import copy, json, os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import core, score
from gleichlaut.emit import cud_id, fhir, load, select, validate

_C = {}
def _setup():
    if not _C:
        meta, views = load("fresh166"); V = select(views, 10); d = tempfile.mkdtemp(prefix="gl-fhir-")
        _C.update(meta=meta, V=V, paths=fhir.write(V, meta, d), FV=validate.FhirValidator(),
                  shape=json.load(open(validate.SHAPE, encoding="utf-8")))
    return _C


def _bundles(): return [json.load(open(p, encoding="utf-8")) for p in _setup()["paths"]]


def test_sample_has_both_verdicts_and_languages():
    V = _setup()["V"]
    assert len(V) == 10 and {v["status"] for v in V} == {"ready", "flagged"} and {v["lang"] for v in V} == {"fr", "it"}


def test_bundles_pass_profile_and_parity():
    C = _setup()
    for b in _bundles():
        assert C["FV"].validate_bundle(b) == []
        assert validate.parity(b, C["shape"]) == []


def test_status_verdict_and_provenance_are_machine_readable():
    C = _setup(); byid = {}
    for v in C["V"]: byid[(fhir.LANGS[v["lang"]], v["cud_id"])] = v
    for b in _bundles():
        R = [e["resource"] for e in b["entry"]]
        cuds = [r for r in R if r["resourceType"] == "ClinicalUseDefinition"]
        provs = {p["target"][0]["reference"]: p for p in R if p["resourceType"] == "Provenance"}
        devs = {d["id"]: d for d in R if d["resourceType"] == "Device"}
        assert any(d["name"][0]["value"] == core.M70 for d in devs.values())
        for c in cuds:
            v = byid[(c["language"], c["id"])]
            assert c["status"]["coding"][0]["code"] == "draft"
            assert c["meta"]["tag"][0] == dict(c["meta"]["tag"][0], system=fhir.VERDICT_CS, code=v["status"])
            assert c["indication"]["diseaseSymptomProcedure"]["concept"]["text"] == v["draft"]
            p = provs[fhir.EPL + "ClinicalUseDefinition/" + c["id"]]
            ext = {e["url"]: e for e in p["extension"][0]["extension"]}
            assert ext["verdict"]["valueCode"] == v["status"] and ext["item"]["valueString"] == v["key"]
            assert ("complaint" in ext) == (v["status"] == "flagged")
            assert {a["who"]["reference"][9:] for a in p["agent"]} <= set(devs)


def test_never_contains_official_target_text():
    I = {x["key"]: x for x in score.load_items(score.RUNS["fresh166"]["items"])}
    blob = "".join(open(p, encoding="utf-8").read() for p in _setup()["paths"])
    for v in _setup()["V"]:
        off = I[v["key"]]["tgt_new"]
        if off != v["draft"]: assert json.dumps(off, ensure_ascii=False)[1:-1] not in blob, v["key"]


def test_validator_rejects_broken_resources():
    """the check is not vacuous: each mutation of a valid Bundle must produce an error."""
    C = _setup(); b0 = _bundles()[0]
    cud = lambda b: b["entry"][0]["resource"]; prov = lambda b: b["entry"][1]["resource"]
    muts = [lambda b: cud(b).update(foo=1), lambda b: cud(b).update(type="warning"), lambda b: cud(b).pop("indication"),
            lambda b: cud(b).update(language="French"), lambda b: cud(b)["meta"].update(tag=cud(b)["meta"]["tag"][0]),
            lambda b: cud(b)["text"].update(div="<p>x</p>"), lambda b: prov(b).pop("agent"),
            lambda b: prov(b)["entity"][0].update(role="input"), lambda b: prov(b)["target"][0].update(reference="urn:uuid:x"),
            lambda b: prov(b)["extension"][0].update(valueString="x"), lambda b: b.update(type="bag"),
            lambda b: cud(b)["indication"]["diseaseSymptomProcedure"]["concept"].update(coding=[{"system": "https://www.meddra.org"}])]
    for i, m in enumerate(muts):
        b = copy.deepcopy(b0); m(b)
        assert C["FV"].validate_bundle(b) + validate.parity(b, C["shape"]), f"mutation {i} not caught"


def test_real_feed_cuds_pass_the_profile_check():
    C = _setup()
    for lang, e in C["shape"]["samples"].items():
        r = dict(copy.deepcopy(e["resource"]), meta={"profile": [fhir.CUD_PROFILE]})
        assert C["FV"].resource(r, f"feed-{lang}") == []


def test_cud_id_follows_the_feed_rule():
    assert cud_id(dict(code_old="X", code_new="NINLARO_01")) == "NINLARO-01"
    assert cud_id(dict(code_old="EXFORGE HCT", code_new="RA:d95dd545#2")) == "EXFORGE-HCT"
    assert len(cud_id(dict(code_old="A" * 80, code_new=""))) == 64


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
