"""--records / --items: records written outside the recorded runs (gleichlaut month / draft) over an arbitrary items
file. A 3-item synthetic pair (one ready draft, one flagged draft, one item routed to a translator; no tgt_new, no
pair/cluster fields, one record without guard_flag) is re-guarded with the frozen guards3 stack, emitted to valid
FHIR / XLIFF 2.1 / XLIFF 1.2 and rendered by the review page with counts only. A recorded guard_flag that disagrees
with the recomputed one is refused. Runs under pytest or as `python3 tests/test_emit_records.py`."""
import contextlib, io, json, os, sys, tempfile
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import score
from gleichlaut.emit import load
from gleichlaut.emit.__main__ import main as emit_main
from gleichlaut.ui import build

X2, X12 = "{urn:oasis:names:tc:xliff:document:2.0}", "{urn:oasis:names:tc:xliff:document:1.2}"
KEYS = ("wb000-fr", "wb001-fr", "wb002-it")          # ready, flagged, -> routed to a translator
_C = {}


def _pair(d, flip=False):
    I = {x["key"]: x for x in score.load_items(score.RUNS["fresh166"]["items"])}
    F = score.load_jsonl(score.RUNS["fresh166"]["final"])
    items = [dict(key=k, lang=I[k]["lang"], de_old=I[k]["de_old"], de_new=I[k]["de_new"], tgt_old=I[k]["tgt_old"],
                  product=I[k]["product"], change_ratio=0.72 if k == KEYS[2] else float(I[k]["de_ratio"])) for k in KEYS]
    recs = [dict(F[KEYS[0]], model="swiss-ai/apertus-v1.5-70b"), dict(F[KEYS[1]]), {"key": KEYS[2], "status": "human"}]
    del recs[1]["guard_flag"]                                          # not required
    if flip: recs[0]["guard_flag"] = not recs[0]["guard_flag"]
    ip, rp = os.path.join(d, "items.json"), os.path.join(d, "month-2026-10.jsonl")
    json.dump(items, open(ip, "w", encoding="utf-8"), ensure_ascii=False)
    with open(rp, "w", encoding="utf-8") as fh:
        for r in recs: fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return rp, ip


def _setup():
    if not _C:
        d = tempfile.mkdtemp(prefix="gl-rec-"); rp, ip = _pair(d)
        _C.update(d=d, rp=rp, ip=ip, load=load(records=rp, items=ip))
    return _C


def test_reguarded_verdicts_and_human_item():
    meta, V = _setup()["load"]
    assert [v["status"] for v in V] == ["ready", "flagged", "human"]
    assert meta["custom"] and not meta["has_tgt_new"] and meta["run"] == "month-2026-10" and meta["model"] == "swiss-ai/apertus-v1.5-70b"
    h = V[2]; assert h["draft"] == "" and h["numbers"] == [] and h["findings"] == [] and h["pair"] == "wb002"
    assert V[1]["findings"] and V[1]["complaint"]


def test_recorded_flag_must_match():
    d = tempfile.mkdtemp(prefix="gl-rec-bad-"); rp, ip = _pair(d, flip=True)
    try: load(records=rp, items=ip)
    except AssertionError as e: assert "re-guarded flag" in str(e)
    else: raise AssertionError("a contradicting guard_flag was accepted")


def test_emit_cli_validates_and_routes_human_items():
    C = _setup(); out = os.path.join(C["d"], "emit")
    with contextlib.redirect_stdout(io.StringIO()) as so:
        rc = emit_main(["--records", C["rp"], "--items", C["ip"], "--n", "0", "--out", out])
    assert rc == 0, so.getvalue()
    rep = json.load(open(os.path.join(out, "validation.json"), encoding="utf-8"))
    assert rep["ok"] and rep["human"] == 1 and set(rep["xliff12"]) and rep["items"] == list(KEYS)
    it2 = ET.parse(os.path.join(out, "xliff", "gleichlaut-month-2026-10-de-CH_it-CH.xlf")).getroot()
    seg = it2.find(f".//{X2}segment")
    assert (seg.get("state"), seg.get("subState")) == ("initial", "gleichlaut:human") and seg.find(X2 + "target") is None
    it12 = ET.parse(os.path.join(out, "xliff", "gleichlaut-month-2026-10-de-CH_it-CH.xliff12.xlf")).getroot()
    assert it12.find(f".//{X12}trans-unit/{X12}target") is None
    fh = [json.load(open(os.path.join(out, "fhir", f), encoding="utf-8")) for f in os.listdir(os.path.join(out, "fhir"))]
    keys = [e["resource"].get("language") for b in fh for e in b["entry"] if e["resource"]["resourceType"] == "ClinicalUseDefinition"]
    assert keys == ["fr-CH", "fr-CH"]                                   # the human item has no draft CUD


def test_review_page_counts_only():
    C = _setup(); p = os.path.join(C["d"], "ui.html")
    _, D = build.build(out=p, records=C["rp"], items=C["ip"])
    assert D["all"] is None and D["counts"]["human"] == 1 and "exact" not in D["counts"]
    h = [g["items"]["it"] for g in D["groups"] if "it" in g["items"]][0]
    assert h["status"] == "human" and h["ratio"] == 72 and h["ledger"] == []
    page = open(p, encoding="utf-8").read()
    assert "German was rewritten by more than 60%" in page and "records month-2026-10" in page


def test_record_status_flagged_is_never_shown_ready():
    """Safety: guards passing is not enough. A record the pipeline flagged (air-gapped mode, statute lane, ...) or one
    with status flagged and no reason stays flagged everywhere: views, XLIFF 2.1 / 1.2 states and the review page."""
    d = tempfile.mkdtemp(prefix="gl-rec-ag-"); rp, ip = _pair(d)
    recs = [json.loads(l) for l in open(rp, encoding="utf-8")]
    assert recs[0]["guard_flag"] is False                               # wb000-fr: every guard passes
    recs[0].update(status="flagged", guard_status="ready", review_reason="air-gapped: every item is reviewed")
    recs[1].update(status="flagged")                                    # guard-flagged anyway, no reason
    with open(rp, "w", encoding="utf-8") as fh:
        for r in recs: fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    meta, V = load(records=rp, items=ip)
    v = V[0]
    assert v["status"] == "flagged" and v["findings"][0]["gid"] == "record"
    assert v["findings"][0]["text"].startswith("Mode hors ligne (air-gapped)")
    assert ("record", "Record", "fail") == v["lights"][0][:3] and "air-gapped" in v["complaint"].lower()
    assert V[1]["status"] == "flagged" and not any(f["gid"] == "record" for f in V[1]["findings"])
    out = os.path.join(d, "emit")
    with contextlib.redirect_stdout(io.StringIO()):
        assert emit_main(["--records", rp, "--items", ip, "--n", "0", "--out", out]) == 0
    fr2 = ET.parse(os.path.join(out, "xliff", "gleichlaut-month-2026-10-de-CH_fr-CH.xlf")).getroot()
    st = {u.get("id"): u.find(X2 + "segment").get("subState") for u in fr2.iter(X2 + "unit")}
    assert st["wb000-fr"] == "gleichlaut:flagged"
    fr12 = ET.parse(os.path.join(out, "xliff", "gleichlaut-month-2026-10-de-CH_fr-CH.xliff12.xlf")).getroot()
    st12 = {u.get("id"): u.find(X12 + "target").get("state") for u in fr12.iter(X12 + "trans-unit")}
    assert st12["wb000-fr"] == "needs-review-translation"
    _, D = build.build(out=os.path.join(d, "ui.html"), records=rp, items=ip)
    it = [g["items"]["fr"] for g in D["groups"] if g["items"].get("fr", {}).get("key") == "wb000-fr"][0]
    assert it["status"] == "flagged" and it["ledger"][0][0] == "record" and it["ledger"][0][2] == "fail"
    assert D["counts"]["ready"] == 0


def test_model_from_the_call_log_no_unknown_dates_and_stub_code_label():
    """Records that do not name the model: the call log next to them does (no 'modèle non indiqué'); items without
    snapshot dates get no 'LS ? → ?'; a stub record whose change code applied alone says so, not 'the draft is the old
    text'."""
    d = tempfile.mkdtemp(prefix="gl-rec-model-"); rp, ip = _pair(d)
    recs = [json.loads(l) for l in open(rp, encoding="utf-8")]; recs[0].pop("model", None)
    recs[0].update(status="flagged", rule_only=True, review_reason="stub backend (wiring test): the draft is the old text, not a translation")
    with open(rp, "w", encoding="utf-8") as fh:
        for r in recs: fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(d, "calls.jsonl"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"model": "swiss-ai/Apertus-70B-Instruct-2509", "model_served": "swiss-ai/Apertus-70B-Instruct-2509"}) + "\n")
    meta, V = load(records=rp, items=ip)
    assert meta["model"] == "swiss-ai/Apertus-70B-Instruct-2509" and meta["model_known"]
    assert V[0]["findings"][0]["text"] == "Backend de test\u00a0: changement appliqué par le code (aucun modèle nécessaire)."
    out = os.path.join(d, "emit")
    with contextlib.redirect_stdout(io.StringIO()):
        assert emit_main(["--records", rp, "--items", ip, "--n", "0", "--out", out]) == 0
    for fn in os.listdir(os.path.join(out, "xliff")):
        t = open(os.path.join(out, "xliff", fn), encoding="utf-8").read()
        assert "non indiqué" not in t and "non indicato" not in t and "Apertus-70B-Instruct-2509" in t, fn
        assert "? → ?" not in t and "LS ?" not in t and "ES ?" not in t, fn


def test_unknown_record_status_is_refused():
    d = tempfile.mkdtemp(prefix="gl-rec-st-"); rp, ip = _pair(d)
    recs = [json.loads(l) for l in open(rp, encoding="utf-8")]; recs[0]["status"] = "approved"
    with open(rp, "w", encoding="utf-8") as fh:
        for r in recs: fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    try: load(records=rp, items=ip)
    except AssertionError as e: assert "unknown record status" in str(e)
    else: raise AssertionError("an unknown record status was accepted")


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
