"""PREREG R17. (A) real errors BAG fixed without a German change (tools/r17_real_errors.py): worklists, key and frozen
Apertus prompts reproduced (byte for byte from the snapshots when they are present; the prompts always, from the committed
worklists), records blind and shaped as the protocol says, a change's error and control never in one worklist, the
committed merge and result recomputed. (B) Apertus 70B as a non-Claude annotator: fixed-format parsers, every recorded
response served by swiss-ai/apertus-v1.5-70b, committed result recomputed."""
import importlib.util, json, os, unittest
from gleichlaut import score

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
L = os.path.join(ROOT, "eval", "labels")
RES = os.path.join(ROOT, "eval", "results")
spec = importlib.util.spec_from_file_location("r17_real_errors", os.path.join(ROOT, "tools", "r17_real_errors.py"))
T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
j = lambda name: json.load(open(os.path.join(L, name), encoding="utf-8"))
NAMES = [f"r17_{p}_set{s}_worklist.json" for p in "ab" for s in (1, 2)]


def test_build_reproduced_from_snapshots():
    if not (os.path.isdir(T.HIST) and os.path.isdir(T.WB)): raise unittest.SkipTest("SL snapshot history not present")
    assert T.main(["build", "--check"]) == 0


def test_classify():
    assert T.classify("l’assureur-maladie", "l'assureur maladie", "fr")["type"] == "punctuation"
    assert T.classify("Vegzelma est", "VEGZELMA est", "fr")["type"] == "punctuation"
    assert T.classify("pendant 12 mois", "pendant 6 mois", "fr")["type"] == "number"
    assert T.classify("RESOLOR n’est destiné", "RESOLOR est destiné", "fr")["type"] == "negation_operator"
    c = T.classify("di prima linea di pazienti", "di pazienti", "it")
    assert c["type"] == "words" and c["subtype"] == "removed"


def test_records_blind_and_apart():
    K = j("r17_key.json"); seen = {}
    assert K["counts"]["content"] == 17 and K["counts"]["changes_mined"] == 29 and set(K["reversed"]) <= {c["uid"] for c in K["changes"]}
    for n in NAMES:
        p = n[4]; W = j(n); uids = []
        for r in W:
            assert set(r) == {"id", "lang", "de_old", "de_new", "tgt_old", "draft"} | ({"official_new"} if p == "a" else set())
            assert r["de_old"] == r["de_new"] and r["draft"] == r["tgt_old"]
            it = K["items"][K["ids"][r["id"]]]
            assert r["draft"] == (it["error_text"] if it["kind"] == "error" else it["correct_text"])
            if p == "a": assert r["official_new"] == it["correct_text"]
            uids.append(it["uid"]); seen.setdefault((p, it["uid"]), set()).add(it["kind"])
        assert len(uids) == len(set(uids))                       # never a change's error and control in one worklist
    assert all(v == {"error", "control"} for v in seen.values()) and len(seen) == 2 * 17


def test_prompts_frozen():
    W = {n: j(n) for n in NAMES}
    D = json.load(open(T.PROMPTS, encoding="utf-8"))
    assert D == json.loads(json.dumps(T.prompts(W))) and len(D["requests"]) == 49 + 2 * 34
    for r in D["requests"]:
        assert "official_new" not in r["prompt"].split("Record (JSON):")[1] or r["task"] == "a"


def test_parsers():
    assert score.r17_parse_record("needs_fix: no  \nclass: equivalent  \nnote: x") == ("no", "equivalent")
    assert score.r17_parse_record("**needs_fix:** yes\n**class:** real\nnote: x") == ("yes", "REAL")
    assert score.r17_parse_record("needs_fix: yes\nclass: wrong") is None
    assert score.r17_parse_audit("answer: minor\nnote: typo") == "minor" and score.r17_parse_audit("I think it is real") is None


def test_merge_and_result():
    K = j("r17_key.json")
    for p in "ab":
        rows = score._r17_rows(p)
        assert {r["key"] for r in rows} == set(K["items"]) and all(K["ids"][r["id"]] == r["key"] for r in rows)
    got = json.loads(json.dumps(score.annotator_real_errors()))
    assert got == json.load(open(os.path.join(RES, "annotator_real_errors.json"), encoding="utf-8"))


def test_crossfamily_result():
    got = json.loads(json.dumps(score.annotator_crossfamily()))
    assert got["served"] == {"swiss-ai/apertus-v1.5-70b": 117} and got["audit"]["n"] == 49
    assert got == json.load(open(os.path.join(RES, "annotator_crossfamily.json"), encoding="utf-8"))
