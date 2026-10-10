"""PREREG R14. (A) the audit relabel (tools/audit_relabel.py): the pooled worklist and key are reproduced byte for byte,
records keep their audit question and carry no first label, the tie-break set is every differing answer, the committed
merge and result are recomputed, and the audit headline numbers are the majority labels with the first labels kept.
(B) in-span sensitivity (tools/plant_inspan.py): worklists and key reproduced, worklists blind, planted and untouched
copies apart, every plant one edit inside the sentence the German change touched, committed result recomputed."""
import importlib.util, json, os
from gleichlaut import score

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
L = os.path.join(ROOT, "eval", "labels")
RES = os.path.join(ROOT, "eval", "results")


def _tool(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "tools", f"{name}.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


AR, PI = _tool("audit_relabel"), _tool("plant_inspan")
j = lambda name: json.load(open(os.path.join(L, name), encoding="utf-8"))


def test_audit_worklist_reproduced_and_blind():
    assert AR.main(["--check"]) == 0
    W, K = j("audit_relabel_worklist.json"), j("audit_relabel_key.json")
    assert len(W) == 49 and K["counts"] == {"register": 27, "terminology": 11, "lists": 11}
    F = AR.findings()
    for r in W:
        orig = F[K["ids"][r["id"]]][1]
        assert {k: v for k, v in r.items() if k != "id"} == {k: v for k, v in orig.items() if k != "id"}   # question unchanged
        assert not {"real", "note", "rank", "known", "half"} & set(r)
    assert set(K["ids"].values()) == set(score.audit_first_labels())


def test_audit_tiebreak_and_merge():
    K, TK = j("audit_relabel_key.json"), j("audit_relabel_tiebreak_key.json")
    ann = lambda n: {c[0]: c[1] for c in (l.split("\t") for l in open(os.path.join(L, n), encoding="utf-8").read().splitlines()[1:])}
    A, B = ann("audit_relabel_A.tsv"), ann("audit_relabel_B.tsv")
    assert set(TK["ids"].values()) == {u for i, u in K["ids"].items() if A[i] != B[i]}
    got = json.loads(json.dumps(score.audit_relabel()))
    assert got == json.load(open(os.path.join(RES, "audit_relabel.json"), encoding="utf-8"))
    assert got["findings"] == 49 and sum(b["n"] for b in got["sets"].values()) == 49


def test_audit_headline_uses_majority_and_keeps_first():
    R = score.audit_relabel(); M = score.audit_majority_labels(); first = score.audit_first_labels()
    a, m = score.audit_eval(), score.audit_more()
    assert a["v2"]["real_all_kinds"] == R["sets"]["register"]["confirmed_majority"]
    assert m["terminology"]["real"] == R["sets"]["terminology"]["confirmed_majority"]
    assert m["lists_real"] == R["sets"]["lists"]["confirmed_majority"]
    assert a["first_annotation"]["v2"]["real_all_kinds"] == R["sets"]["register"]["confirmed_first"] == \
        sum(first[u] == "yes" for u in first if u.split(":")[0] in score.AUDIT_RELABEL_SETS["register"])
    assert m["first_annotation"]["terminology_real"] == R["sets"]["terminology"]["confirmed_first"]
    assert set(M) == set(first)


def test_inspan_worklists_reproduced_and_blind():
    assert PI.main(["--check"]) == 0
    K = j("inspan_key.json"); seen = {}
    for st in (1, 2):
        W = j(f"inspan_set{st}_worklist.json")
        assert all(list(r) == ["id", "lang", "de_old", "de_new", "tgt_old", "draft", "official_new"] for r in W)
        keys = [K["items"][K["ids"][r["id"]]]["key"] for r in W]
        assert len(keys) == len(set(keys))
        for r in W: seen[K["ids"][r["id"]]] = st
    assert set(seen) == set(K["items"])
    for u, it in K["items"].items():
        if it["kind"] == "planted": assert seen[u] != seen[it["key"] + "|untouched"]


def test_each_plant_is_one_edit_inside_the_touched_sentence():
    I, bases, _ = PI.selection(); K = j("inspan_key.json")
    W = {r["id"]: r for st in (1, 2) for r in j(f"inspan_set{st}_worklist.json")}
    for i, u in K["ids"].items():
        it = K["items"][u]
        if it["kind"] == "real": continue
        base = bases[it["key"]]["text"]; d = W[i]["draft"]
        if it["kind"] == "untouched": assert d == base; continue
        assert d == base.replace(it["old"], it["new"]) and base.count(it["old"]) == 1
        s, e = PI.edit_span(base, d)
        assert any(a <= s and e <= b for a, b in PI.touched(I[it["key"]]["tgt_old"], base)), u


def test_inspan_result_recomputed():
    got = json.loads(json.dumps(score.annotator_sensitivity_inspan()))
    assert got == json.load(open(os.path.join(RES, "annotator_sensitivity_inspan.json"), encoding="utf-8"))
    p = got["planted"]
    assert p["n"] == got["counts"]["planted"] == 38 and got["untouched"]["n"] == 38
    assert sum(v["n"] for v in got["planted_by_type"].values()) == 38
    for m in ("needs_fix", "severe"):
        b = p[m]; assert b["both"]["k"] <= min(b["A"]["k"], b["B"]["k"]) <= max(b["A"]["k"], b["B"]["k"]) <= b["either"]["k"]
    assert len(got["missed_planted"]) == 38 - p["severe"]["both"]["k"]
