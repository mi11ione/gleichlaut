"""PREREG R13, the fully blind relabel of the headline 70B fresh-166 run (tools/blind_relabel_70b.py): the worklist and key
are reproduced byte for byte, the worklists are blind (protocol fields only, neutral ids, no verdicts), the items are the
49 ready non-exact drafts plus the R1-seeded 20 flagged ones, the tie-break set follows PROTOCOL.md step 3, and the
committed result is what score.blind_relabel_70b computes from the committed labels."""
import importlib.util, json, os
from gleichlaut import score

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
L = os.path.join(ROOT, "eval", "labels")
FIELDS = ["id", "lang", "de_old", "de_new", "tgt_old", "draft", "official_new"]
_spec = importlib.util.spec_from_file_location("blind_relabel_70b", os.path.join(ROOT, "tools", "blind_relabel_70b.py"))
T = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(T)


def j(name): return json.load(open(os.path.join(L, name), encoding="utf-8"))


def test_worklist_and_key_are_reproduced():
    assert T.main(["--check"]) == 0


def test_items_and_blindness():
    K = j("fresh166_blind_key.json"); W = j("fresh166_blind_worklist.json")
    assert len(K["ready"]) == 49 and len(K["flagged_sample"]) == 20 and len(W) == 69
    assert set(K["ready"]) == set(score.load_labels("fresh166_unflagged.tsv"))           # the research-labelled ready drafts
    assert set(K["flagged_sample"]) == set(score.load_labels("fresh166_flagged20.tsv"))  # the R1 seed gives the same 20
    assert all(list(r) == FIELDS for r in W) and [r["id"] for r in W] == [f"H{i:02d}" for i in range(69)]
    assert sorted(K["ids"].values()) == sorted(K["ready"] + K["flagged_sample"])
    TW = j("fresh166_blind_tiebreak_worklist.json"); TK = j("fresh166_blind_tiebreak_key.json")
    assert all(list(r) == FIELDS for r in TW) and [r["id"] for r in TW] == sorted(TK["ids"])


def test_tiebreak_set_follows_the_protocol():
    K = j("fresh166_blind_key.json"); TK = j("fresh166_blind_tiebreak_key.json")
    ann = lambda n: {c[0]: (c[1], c[2]) for c in (l.split("\t") for l in open(os.path.join(L, n), encoding="utf-8").read().splitlines()[1:])}
    A, B = ann("fresh166_blind_A.tsv"), ann("fresh166_blind_B.tsv"); ready = set(K["ready"])
    want = {k for i, k in K["ids"].items() if score.blind_needs_tiebreak(A[i], B[i], k in ready)}
    assert set(TK["ids"].values()) == want


def test_committed_result_is_recomputed():
    got = json.loads(json.dumps(score.blind_relabel_70b()))
    assert got == json.load(open(os.path.join(ROOT, "eval", "results", "fresh166_blind.json"), encoding="utf-8"))
    assert got["items"] == 69 and got["vs_research"]["n"] == 69
