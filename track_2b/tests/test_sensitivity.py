"""Annotator sensitivity (PREREG R11, tools/plant_sensitivity.py): the committed worklists and key are reproduced byte for
byte from the seed, the worklists are blind (protocol fields only, no item twice, a draft's planted and untouched copies
in different worklists, (b) without the reference), every planted copy differs from its draft by one edit, and the
committed result is what score.annotator_sensitivity computes from the committed labels."""
import importlib.util, json, os
from gleichlaut import score

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
L = os.path.join(ROOT, "eval", "labels")
_spec = importlib.util.spec_from_file_location("plant_sensitivity", os.path.join(ROOT, "tools", "plant_sensitivity.py"))
P = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(P)


def test_worklists_and_key_are_reproduced_from_the_seed():
    assert P.main(["--check"]) == 0


def test_worklists_are_blind_and_planted_copies_are_apart():
    K = json.load(open(os.path.join(L, "sensitivity_key.json"), encoding="utf-8"))
    fields = {"a": ["id", "lang", "de_old", "de_new", "tgt_old", "draft", "official_new"],
              "b": ["id", "lang", "de_old", "de_new", "tgt_old", "draft"]}
    for pr in "ab":
        seen = {}
        for st in (1, 2):
            W = json.load(open(os.path.join(L, f"sensitivity_{pr}_set{st}_worklist.json"), encoding="utf-8"))
            assert all(list(r) == fields[pr] for r in W)
            keys = [K["items"][K["ids"][pr][r["id"]]]["key"] for r in W]
            assert len(keys) == len(set(keys))                         # no item twice in one worklist
            for r in W: seen[K["ids"][pr][r["id"]]] = st
        assert set(seen) == set(K["items"])
        for u, it in K["items"].items():
            if it["kind"] == "planted": assert seen[u] != seen[it["key"] + "|untouched"]
    n = K["counts"]
    assert n["planted"] == n["untouched"] == sum(n["by_type_lang"].values())


def test_each_planted_copy_carries_one_edit_of_its_type():
    import difflib
    _, bases, _ = P.pool()
    W = {}
    for st in (1, 2):
        for r in json.load(open(os.path.join(L, f"sensitivity_a_set{st}_worklist.json"), encoding="utf-8")): W[r["id"]] = r
    K = json.load(open(os.path.join(L, "sensitivity_key.json"), encoding="utf-8"))
    for i, u in K["ids"]["a"].items():
        it = K["items"][u]
        if it["kind"] == "real": continue
        base = bases[it["key"]]["text"]; d = W[i]["draft"]
        if it["kind"] == "untouched": assert d == base; continue
        ops = [o for o in difflib.SequenceMatcher(None, base, d, autojunk=False).get_opcodes() if o[0] != "equal"]
        assert d != base and ops and it["after"] in d, u
        assert ops[-1][1] - ops[0][1] <= len(base) // 2 + 10, u                # one local edit, not a rewrite


def test_committed_result_matches_the_labels():
    p = os.path.join(ROOT, "eval", "results", "annotator_sensitivity.json")
    R = json.load(open(p, encoding="utf-8"))
    assert json.loads(json.dumps(score.annotator_sensitivity())) == R
    for name, d in R["protocols"].items():
        pl = d["planted"]
        assert pl["n"] == R["counts"]["planted"] and d["untouched"]["n"] == R["counts"]["untouched"]
        assert sum(v["n"] for v in d["planted_by_type"].values()) == pl["n"]
        for m in ("needs_fix", "severe"):
            b = pl[m]
            assert b["both"]["k"] <= min(b["A"]["k"], b["B"]["k"]) <= max(b["A"]["k"], b["B"]["k"]) <= b["either"]["k"]
        assert len(d["missed_planted"]) == pl["n"] - pl["severe"]["either"]["k"]
