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


def test_two_records_one_output_id_merge_into_one_cud():
    """Regression (real Sept -> Oct 2026 records): BAG merged SKYRIZI.01Pe and SKYRIZI.01 into one new CUD id; two items
    mapping to the same output id must give ONE CUD (no duplicate fullUrl) with one Provenance per item, and validate."""
    import contextlib, io
    from gleichlaut.emit.__main__ import main as emit_main
    I = {x["key"]: x for x in score.load_items(score.RUNS["fresh166"]["items"])}
    F = score.load_jsonl(score.RUNS["fresh166"]["final"])
    d = tempfile.mkdtemp(prefix="gl-fhir-merge-"); keys = ("wb000-fr", "wb001-fr")
    items = [dict(key=k, lang="fr", de_old=I[k]["de_old"], de_new=I[k]["de_new"], tgt_old=I[k]["tgt_old"], product="Skyrizi",
                  change_ratio=float(I[k]["de_ratio"]), code_old=old, cud_new="SKYRIZI.01")
             for k, old in zip(keys, ("SKYRIZI.01Pe", "SKYRIZI.01"))]
    ip, rp = os.path.join(d, "items.json"), os.path.join(d, "records.jsonl")
    json.dump(items, open(ip, "w", encoding="utf-8"), ensure_ascii=False)
    with open(rp, "w", encoding="utf-8") as fh:
        for k in keys: fh.write(json.dumps(F[k], ensure_ascii=False) + "\n")
    out = os.path.join(d, "emit")
    with contextlib.redirect_stdout(io.StringIO()) as so:
        assert emit_main(["--records", rp, "--items", ip, "--n", "0", "--out", out]) == 0, so.getvalue()
    b = json.load(open(os.path.join(out, "fhir", os.listdir(os.path.join(out, "fhir"))[0]), encoding="utf-8"))
    R = [e["resource"] for e in b["entry"]]
    cuds = [r for r in R if r["resourceType"] == "ClinicalUseDefinition"]
    provs = [r for r in R if r["resourceType"] == "Provenance"]
    assert [c["id"] for c in cuds] == ["SKYRIZI.01"] and len(provs) == 2
    assert {p["target"][0]["reference"] for p in provs} == {fhir.EPL + "ClinicalUseDefinition/SKYRIZI.01"}
    assert {p["entity"][1]["what"]["identifier"]["value"] for p in provs} == {"SKYRIZI.01Pe", "SKYRIZI.01"}
    assert cuds[0]["meta"]["tag"][0]["code"] == "flagged"                     # drafts differ -> a translator reconciles
    ext = [{e["url"]: e for e in p["extension"][0]["extension"]} for p in provs]
    assert all("merged" in e and "draft" in e for e in ext)
    C = _setup(); assert C["FV"].validate_bundle(b) == [] and validate.parity(b, C["shape"]) == []


def test_identical_drafts_on_one_id_keep_the_verdict():
    meta, views = load("fresh166"); v = next(v for v in views if v["status"] == "ready" and v["lang"] == "fr")
    w = dict(v, key=v["key"] + "-b")
    b = fhir.bundle([v, w], meta, "fr")
    cuds = [e["resource"] for e in b["entry"] if e["resource"]["resourceType"] == "ClinicalUseDefinition"]
    assert len(cuds) == 1 and cuds[0]["meta"]["tag"][0]["code"] == "ready"
    assert _setup()["FV"].validate_bundle(b) == []
    b2 = fhir.bundle([v, dict(w, status="flagged")], meta, "fr")
    assert [e["resource"]["meta"]["tag"][0]["code"] for e in b2["entry"] if e["resource"]["resourceType"] == "ClinicalUseDefinition"] == ["flagged"]


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
