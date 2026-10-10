"""PREREG R18: the Apertus 8B log-probability filter on the round-5 audit findings. Items reproduced from the snapshot when
present (tools/r18_filter.py --check); the pairs, split and prompts as frozen; the committed result recomputed from the
recorded run; the AUROC and the decision rule on small cases."""
import hashlib, importlib.util, json, os, unittest
from gleichlaut import score

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
spec = importlib.util.spec_from_file_location("r18_filter", os.path.join(ROOT, "tools", "r18_filter.py"))
T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
D = json.load(open(T.OUT, encoding="utf-8"))
RES = os.path.join(ROOT, "eval", "results", "audit_apertus_filter.json")


def test_items_reproduced_from_snapshot():
    if not os.path.exists(os.path.join(T.HIST, "20261006-de.json")): raise unittest.SkipTest("SL snapshot 20261006 not present")
    assert json.loads(json.dumps(T.build(T.HIST), ensure_ascii=False)) == D


def test_items_frozen_shape():
    I = D["items"]; reg = [x for x in I if x["set"] == "register"]
    assert len(reg) == 31 and sum(x["confirmed"] for x in reg) == 6
    assert {x["cud"] for x in reg if x["final"] == "real"} == set(score.R18_NAMED)
    P = {x["uid"][3:]: x for x in I if x["set"] == "planted"}; C = {x["uid"][3:]: x for x in I if x["set"] == "control"}
    assert len(P) == len(C) == 800 and set(P) == set(C)
    pairs = {p["pk"]: p for p in D["pairs"]}
    assert len(pairs) == len(D["pairs"]) == 1366 and all(x["pk"] in pairs for x in I)
    for k, p in P.items():
        c = C[k]; a, b = pairs[p["pk"]], pairs[c["pk"]]
        assert a["de"] == b["de"] and a["tgt"] != b["tgt"] and p["split"] == c["split"] == T.split(p["cud"])
        assert p["split"] == ("fit" if int(hashlib.md5(f"r18:{p['cud']}".encode()).hexdigest(), 16) % 2 == 0 else "test")
    for x in D["pairs"]: assert x["pk"] == T.pkey(x["lang"], x["de"], x["tgt"])
    assert [p["register"] for p in D["pairs"]] == sorted((p["register"] for p in D["pairs"]), reverse=True)   # register pairs first


def test_prompt_frozen():
    assert D["question"] == T.Q and (D["yes"], D["no"], D["max_tokens"]) == ("Ja", "Nein", 8)
    P = T.prompts("it", "Der Satz.", "La frase.")
    assert P["ab"].index("[DE] Der Satz.") < P["ab"].index("[IT] La frase.") and P["ab"].endswith("Antworte nur mit Ja oder Nein.")
    assert P["ba"].index("[IT] La frase.") < P["ba"].index("[DE] Der Satz.") and P["ba"].endswith("Antworte nur mit Nein oder Ja.")


def test_auroc():
    assert score._auroc([0.9, 0.8], [0.1, 0.2]) == 1.0 and score._auroc([0.1], [0.9]) == 0.0
    assert score._auroc([0.5, 0.5], [0.5]) == 0.5 and score._auroc([], [1]) is None


def test_result_recomputed():
    r = score.audit_apertus_filter()
    if r is None: raise unittest.SkipTest("R18 run not recorded yet")
    assert json.loads(json.dumps(r)) == json.load(open(RES, encoding="utf-8"))
    assert r["pairs"]["missing"] == 0 and r["shards"]["certificate_verified"] == r["shards"]["n"] > 0
    a = r["register"]["all"]; d = r["decision"]
    assert d["pass"] == (a["kept"] > 0 and a["precision_after_pct"] >= 50 and a["kept_confirmed"] >= 4)
    assert a["findings"] == 31 and a["confirmed"] == 6 and a["precision_before_pct"] == 19.4
