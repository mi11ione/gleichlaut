"""PREREG R20 (predictions scored against BAG's own later corrections): the frozen prediction file carries the sha256
registered in PREREG R20 and the README, its counts, and the checker on the register's own texts (all unchanged, every
finding still reported) and on edited copies (a correction toward agreement, a change of the other side, an unrelated
edit, a removed and a renamed limitation). No snapshot or network needed: the 6 Oct 2026 texts are shipped."""
import hashlib, importlib.util, json, os, re, tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
spec = importlib.util.spec_from_file_location("check_predictions", os.path.join(ROOT, "tools", "check_predictions.py"))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
P = json.load(open(C.PRED, encoding="utf-8"))
TX = json.load(open(C.TEXTS, encoding="utf-8"))["texts"]


def _r20():
    t = open(os.path.join(ROOT, "eval", "prereg", "PREREG.md"), encoding="utf-8").read()
    a = t.index("\n## R20."); b = t.index("\n## ", a + 5)
    return t[a:b]


def test_prediction_file_hash_is_registered():
    h = hashlib.sha256(open(C.PRED, "rb").read()).hexdigest()
    reg = re.findall(r"sha256 `([0-9a-f]{64})`", _r20())
    assert reg and reg[0] == h, (reg, h)
    assert f"`{h[:12]}" in open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()


def test_prediction_counts():
    ps = P["predictions"]; c = P["counts"]
    assert len(ps) == c["predictions"] == 69 and len({p["pid"] for p in ps}) == 69
    assert (c["positive"]["n"], c["negative"]["n"]) == (34, 35)
    assert (c["positive"]["issues"], c["positive"]["experimental"]) == (28, 6)
    assert sum(p["set"] == "issues" for p in ps) == 38 and len({p["issue"] for p in ps if p["set"] == "issues"}) == 18
    assert sorted(p["pid"] for p in ps if p["set"] == "experimental" and p["confirmed"]) == ["G03", "G04", "G17", "G18", "O01", "W01"]
    assert all(p["confirmed"] == (p["blind_label"]["final"] in ("real", "minor")) for p in ps)
    assert len(P["limitation_ids_20261006"]) == 1688
    by = {p["pid"]: p for p in ps}
    assert by["O01"]["divergent"] == "fr" and "'> 10'" in by["O01"]["correction"]
    assert by["N18"]["divergent"] == "it" and by["N18"]["correction"].startswith("IT changes 4 to 8")
    for p in ps:
        assert set(p["texts_sha256"]) == set(C.LANGS) and p["texts_sha256"]["de"] == C.sha(C.nrm(TX[p["limitation"]]["de"]))


def _hist(td, date, edit=None, drop=(), rename=None):
    T = {i: dict(t) for i, t in TX.items()}
    for (i, L), f in (edit or {}).items(): T[i][L] = f(T[i][L])
    for i in drop: T.pop(i)
    if rename: T[rename[1]] = T.pop(rename[0])
    for L in C.LANGS:
        json.dump(dict(lim={i: t[L] for i, t in T.items()}, prod={}), open(os.path.join(td, f"{date}-{L}.json"), "w", encoding="utf-8"))
    return td


def _run(**kw):
    with tempfile.TemporaryDirectory() as td:
        R = C.check(_hist(td, "20261101", **kw), "20261101")
    return {r["pid"]: r for r in R["results"]}, R


def test_self_test_on_the_register_texts():
    with tempfile.TemporaryDirectory() as td:
        R = C.check(_hist(td, C.DATE), C.DATE)
    assert all(r["status"] == C.UNCHANGED and r["still_reported"] for r in R["results"]), \
        [r for r in R["results"] if r["status"] != C.UNCHANGED or not r["still_reported"]]
    assert R["role"].startswith("self-test") and R["summary"]["positive"]["unchanged"] == 34
    S = json.load(open(os.path.join(C.OUTD, "check_20261006.json"), encoding="utf-8"))      # the committed self-test
    assert S["predictions_sha256"] == hashlib.sha256(open(C.PRED, "rb").read()).hexdigest()
    assert [(r["pid"], r["status"], r["still_reported"]) for r in S["results"]] == [(r["pid"], r["status"], r["still_reported"]) for r in R["results"]]


def test_corrections_toward_agreement():
    def nth(old, new, k):          # replace the k-th occurrence (1-based)
        def f(t):
            parts = t.split(old); return old.join(parts[:k]) + new + old.join(parts[k:])
        return f
    E = {("AMVUTTRA.01a", "fr"): lambda t: nth("score NIS ≤ 10", "score NIS > 10", 3)(nth("score NIS ≤ 10", "score NIS > 10", 2)(t)),
         ("NEMLUVIO.01", "it"): nth("ogni quattro settimane", "ogni otto settimane", 2),
         ("BEYONTTRA", "it"): lambda t: t.replace("BEYONTTRA on deve", "BEYONTTRA non deve"),
         ("DIAPHIN.6-", "it"): lambda t: t.replace("prezzo di 12%", "prezzo di 6%"),
         ("JEMPERLI.01---Endometriumkarzinom-Mono", "fr"): lambda t: t.replace("doit être communiqué à", "doit être transmis à"),
         ("FORSTEO-2", "it"): lambda t: t.replace("se mesi", "sei mesi"),
         ("KEYTRUDA.07---Inj-L-s---Urothelkarzinom--Monotherapie--KN045", "it"): lambda t: TX["NEMLUVIO.01"]["it"]}
    by, R = _run(edit=E)
    for pid in ("O01", "N18", "G03", "N01", "T09", "E05", "N13", "L01"):
        assert by[pid]["status"] == C.CORRECTED, by[pid]
    assert by["T10"]["status"] == C.UNCHANGED and by["G17"]["status"] == C.UNCHANGED
    assert R["summary"]["positive"]["corrected toward agreement"] == 8


def test_other_changes_removed_and_renamed():
    E = {("DIAPHIN.6-", "de"): lambda t: t.replace("Zuschlag von 6%", "Zuschlag von 12%"),        # the wrong side moves
         ("NEMLUVIO.01", "de"): lambda t: t + " Ein neuer Satz.",                                     # an unrelated edit
         ("BEYONTTRA", "it"): lambda t: t.replace("BEYONTTRA on deve essere combinato", "BEYONTTRA deve essere combinato")}
    by, _ = _run(edit=E, drop=["CRESE.Kps.IM"], rename=("AMVUTTRA.01a", "AMVUTTRA.01b"))
    assert by["N01"]["status"] == C.OTHER and not by["N01"]["divergent_changed"]
    assert by["N18"]["status"] == C.OTHER and by["N18"]["still_reported"]
    assert by["G03"]["status"] == C.OTHER and by["G03"]["still_reported"]
    assert by["N09"]["status"] == C.REMOVED
    assert by["O01"]["status"] == C.UNCHANGED and by["O01"]["followed_to"] == "AMVUTTRA.01b"


def test_score_pending_and_fisher():
    S = C.score(files=[os.path.join(C.OUTD, "check_20261006.json")], today="20261011")
    assert S["scoring_snapshots"] == [] and all(h["outcome"].startswith("pending") for h in S["horizons"].values())
    assert abs(C.fisher_greater(10, 34, 1, 35) - 0.0021) < 0.001 and C.fisher_greater(0, 34, 0, 35) == 1.0
