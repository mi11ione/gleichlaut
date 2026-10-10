"""PREREG R16, the memorisation probe (tools/r16_memo.py, score.memorisation): the three sets are as registered (sizes,
disjoint, T = the fresh-166 answers, every text cut at a word boundary), the per-text scorer behaves as the rule says,
every recorded 70B response was served by the 70B, and the committed result is what score.memorisation computes."""
import importlib.util, json, os, unittest
from gleichlaut import score
from gleichlaut.sl.ingest import nrm

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
D = json.load(open(os.path.join(ROOT, "data", "memo", "r16_items.json"), encoding="utf-8"))
_spec = importlib.util.spec_from_file_location("r16_memo", os.path.join(ROOT, "tools", "r16_memo.py"))
T = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(T)


def test_sets_as_registered():
    I = D["items"]
    assert D["sizes"] == {"T": 160, "P": 120, "N": 62} and D["max_tokens"] == 300
    texts = {s: {r["text"] for r in I if r["set"] == s} for s in "TPN"}
    assert all(len(texts[s]) == D["sizes"][s] for s in "TPN")
    assert not (texts["T"] & texts["P"] or texts["T"] & texts["N"] or texts["P"] & texts["N"])
    fresh = {nrm(x["tgt_new"]) for x in json.load(open(os.path.join(ROOT, "data", "items", "items_fresh.json"), encoding="utf-8"))}
    assert texts["T"] <= fresh
    for r in I:
        assert r["prefix"] + " " + r["truth"] == r["text"] and len(r["text"]) >= 200 and len(r["truth"].split(" ")) >= 10
        assert (r["prefix"], r["truth"]) == T.split(r["text"])
    assert all(r["src"]["valid_from"] < "2023-01-01" for r in I if r["set"] == "P")


def test_items_rebuild_byte_identical():
    if not (os.path.isdir(T.HIST) and os.path.isdir(T.WB)): raise unittest.SkipTest("snapshot files not present")
    s = json.dumps(T.build(), ensure_ascii=False, indent=1) + "\n"
    assert s == open(T.OUT, encoding="utf-8").read()


def test_per_text_scorer():
    r = dict(set="T", key="k", lang="fr", prefix="a b c", truth=" ".join(f"w{i}" for i in range(12)))
    d = score.memo_score_text(r, r["truth"])
    assert d["next10"] and d["lcp"] == 12 and abs(d["chrf"] - 100) < 1e-9 and not d["echo"]
    d = score.memo_score_text(r, "a b c " + r["truth"])                     # an echoed first half is removed
    assert d["echo"] and d["next10"] and d["lcp"] == 12
    d = score.memo_score_text(r, "… w0 w1 w2 x w4")                    # leading ellipsis dropped; stops at the first miss
    assert not d["next10"] and d["lcp"] == 3
    d = score.memo_score_text(dict(r, old_cont="z0 z1 z2"), "z0 z1 z2")
    assert d["closer"] == "old"


def test_recorded_responses_and_result():
    p = os.path.join(ROOT, "eval", "results", "memorisation.json")
    if not os.path.exists(p): raise unittest.SkipTest("no committed R16 result yet")
    res = score.memorisation()
    m = res["models"]["70b"]
    assert m["texts"] == 342 and m["requests"] == 333 and m["served"] == {"swiss-ai/apertus-v1.5-70b": 342}   # 9 texts share a first half
    assert json.loads(json.dumps(res)) == json.load(open(p, encoding="utf-8"))
