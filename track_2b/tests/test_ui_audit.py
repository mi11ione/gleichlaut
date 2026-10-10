"""Review page, Register audit tab and old-text notices (gleichlaut.ui.audit_view, build.data): one row per audit
finding, the known divergences first, odd one out and snippets from the file (or derived), headline figures from
eval/results/audit.json; a language problem of the old text is a display notice that never changes a verdict.
Runs under pytest or as `python3 tests/test_ui_audit.py`."""
import json, os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import score
from gleichlaut.emit import explain
from gleichlaut.ui import audit_view, build

_C = {}
def _audit():
    if "A" not in _C: _C["A"] = audit_view.data(hist=None)
    return _C["A"]


def test_one_row_per_finding_known_first():
    A = _audit(); F = json.load(open(audit_view.AUDIT, encoding="utf-8"))["findings"]
    assert len(A["rows"]) == len(F) and len({r["rid"] for r in A["rows"]}) == len(F)
    k = [r["known"] for r in A["rows"]]; assert k == sorted(k, reverse=True)
    assert A["meta"]["known_rows"] == sum(1 for f in F if f.get("known")) >= 10
    assert A["meta"]["known_found"] == 10 and A["meta"]["known_of"] == 10
    R = json.load(open(audit_view.RESULTS, encoding="utf-8"))
    assert A["meta"]["precision"] == R["precision_pct"] and A["meta"]["ci"] == R["precision_wilson95"]


def test_snippets_highlight_conflicting_values():
    r = next(r for r in _audit()["rows"] if r["lim"] == "DIAPHIN.6-")
    assert r["odd"] == "it"
    hot = {L: [t for t, k in r["snip"][L] if k == 2] for L in r["snip"]}
    assert any("6" in t for t in hot["de"]) and any("12" in t for t in hot["it"])
    assert "".join(t for t, _ in r["snip"]["de"]).count("[") == 0


def test_works_with_the_round_two_shape():
    F = [dict(id="X.01", product=["Xprod"], lang="fr", kind="numeric", known=True, rank=1, description="DE has 8 (Wochen), FR does not",
              de_only=[dict(value="8", unit="Wochen", context=["…alle [acht] Wochen…"])], tgt_only=[]),
         dict(id="X.01", product=["Xprod"], lang="it", kind="numeric", rank=2, description="DE has 8 (Wochen), IT does not",
              de_only=[dict(value="8", unit="Wochen", context=["…alle [acht] Wochen…"])], tgt_only=[]),
         dict(id="Y.02", product="Y", lang="it", kind="numeric", rank=3, description="IT has 12 (%)",
              de_only=[], tgt_only=[dict(value="12", unit="%", context=["…di [12]% più…"])])]
    R = {r["lim"] + r["lang"]: r for r in audit_view.rows(F)}
    assert R["X.01fr"]["odd"] == "de" and R["X.01it"]["odd"] == "de" and R["Y.02it"]["odd"] == "it"
    assert R["X.01fr"]["kind"] == "number" and R["X.01fr"]["snip"]["de"][1] == ["acht Wochen", 2]


def test_page_has_both_tabs_audit_first():
    p = os.path.join(tempfile.mkdtemp(prefix="gl-ui-a-"), "index.html"); _, D = build.build(out=p)
    s = open(p, encoding="utf-8").read()
    assert s.index('id="t-audit"') < s.index('id="t-drafts"') and 'location.hash.slice(1)' in s and 'h==="audit"' in s
    assert 'var TAB=AU?"audit":"drafts"' in s and 'h==="drafts"' in s
    m = D["audit"]["meta"]                                 # the README's headline: 27 findings + 11 terminology notices
    R = {k: json.load(open(os.path.join(audit_view.core.ROOT, "eval", "results", f"{k}.json"), encoding="utf-8")) for k in ("audit", "audit_more")}
    assert (m["main"], m["term"]) == (27, 11) and m["main"] + m["term"] == len(D["audit"]["rows"])
    assert (m["main_real"], m["term_real"]) == (R["audit"]["v2"]["real_all_kinds"], R["audit_more"]["terminology"]["real"])   # R14 majority labels
    assert D["meta"]["lane"] == "8b" and "Model calls" not in s.split("var TX3=")[1]          # the drafts open on the 8B (default)
    for k in ('<option value="de">DE</option>', 'return "de"}', "Ready means checked by code, not by a person.",
              "Bereit heisst: vom Code geprüft, nicht von einer Person.", 'id="imp-file"', "data-copy", "gleichlaut:changed"):
        assert k in s, k
    for r in ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"): assert s.count('rd' + r + ':"') == 4    # every rule in the legend, 4 languages
    assert "family cb735e3b" not in s


def test_one_sided_number_shows_the_value_written_there():
    """'DE has 8 (Wochen), IT does not': the list shows what IT writes at that place (ogni quattro settimane -> 4), and keeps
    '—' where the other language has no number with that unit there."""
    W = {(tuple(I["products"]), w[1]): w for I in _audit()["issues"] for w in I["what"] if w[0] == "number"}
    assert W[(("Nemluvio",), "it")][2:] == ["8", "4"] and W[(("Leqvio",), "fr")][2:] == ["4", "1.4"]
    assert W[(("Cerdelga",), "fr")][2:] == ["18", "—"] and W[(("Emgality",), "fr")][2:] == ["120", "—"]
    r = dict(snip={"de": [["…alle ", 0], ["acht Wochen", 2]], "it": [["30 mg", 1], ["…ogni ", 0], ["quattro settimane", 1]]})
    assert audit_view.counterpart(r, "it", "de") == "4" and audit_view.counterpart(dict(snip={"de": r["snip"]["de"], "it": [["30 mg", 1]]}), "it", "de") is None
    F = json.load(open(audit_view.AUDIT, encoding="utf-8"))["findings"]           # the audit's own counterpart field agrees
    R = [x for x in audit_view.rows(F) if x["kind"] == "number" and x["cp"] is not None]
    assert R and all(x["cp"].get(x["lang"], []) == ([audit_view.counterpart(x, x["lang"], "de")] if audit_view.counterpart(x, x["lang"], "de") else [])
                     for x in R if x["vals"].get("de") and not x["vals"].get(x["lang"]))


def test_experimental_round5_findings_confirmed_only_and_outside_the_headline():
    A = _audit(); E = A["exp"]; m = A["meta"]
    lab = {l.split("\t")[1]: l.split("\t") for l in open(os.path.join(audit_view.core.ROOT, "eval", "labels", "audit_r15_20261006.tsv"), encoding="utf-8").read().splitlines()[1:]}
    assert E["n"] == 31 and E["confirmed"] == len(E["rows"]) == sum(r[9] in ("real", "minor") for r in lab.values()) == 6
    assert not any(E["on"].values())                                          # every round-5 kind ships off
    assert all(lab[r["fid"]][6] == lab[r["fid"]][7] == r["label"] for r in E["rows"])      # both blind annotators agree
    X = {(r["lim"], r["lang"]): r for r in E["rows"]}
    assert X[("AMVUTTRA.01a", "fr")]["what"] == ["operator", "fr", "> 10", "≤ 10"] and X[("AMVUTTRA.01a", "fr")]["label"] == "real"
    for k in (("BEYONTTRA", "it"), ("VYNDAQEL.01b", "it")):
        assert X[k]["what"] == ["negation", "it", "nicht", "—"] and X[k]["label"] == "real" and "on deve" in X[k]["snip"]["it"][0][0]
    assert (m["issues"], m["main"], m["term"]) == (18, 27, 11) and len(A["issues"]) == 18     # the headline is unchanged


def test_old_text_language_problem_is_a_display_notice():
    old = explain._audit_item
    try:
        explain._audit_item = lambda x: ([dict(kind="language", lang="it", detected="fr", odd_one_out="it",
                                               detail="The old Italian text is written in French.")] if x["key"] == "wb079-it" else [])
        D = build.data(audit=None)
    finally:
        explain._audit_item = old
    it = next(g["items"]["it"] for g in D["groups"] if g["items"].get("it", {}).get("key") == "wb079-it")
    assert it["status"] == "ready" and it["old"] == [dict(k="language", t="Il vecchio testo italiano è in francese.", f="fr")]
    assert it["banner"] == "Il vecchio testo italiano è in francese."
    assert D["counts"]["ready"] == score.score_run("fresh166")["summary"]["all"]["unflagged"]     # no verdict or metric moves


def test_decisions_carry_over_by_signature_and_new_kinds():
    F = json.load(open(audit_view.AUDIT, encoding="utf-8"))["findings"]
    A = audit_view.rows(F); B = audit_view.rows([dict(f, rank=(f.get("rank") or 0) + 7, first_seen="20261101") for f in F], date="20261101")
    assert [r["sig"] for r in A] and {r["sig"] for r in A} == {r["sig"] for r in B} and len({r["sig"] for r in A}) == len(A)
    r = next(r for r in A if r["lim"] == "DIAPHIN.6-"); assert r["sig"] == "DIAPHIN.6-|number|it|12,6"
    T = [dict(id="X.9", product=["Xprod"], lang="fr", kind="terminology", old="inhibiteur de l'enzyme", new="antagoniste des récepteurs",
              corrected_in=[{"id": "OPDIVO.02---Melanom", "after": "20261001"}], context=["…d'un [inhibiteur de l'enzyme] de…"]),
         dict(id="Y.1", product="Y", lang="it", kind="number", likely_equivalent=True, equivalence="Q1 conversion: 14 Tagen = 2 settimane",
              de_only=[dict(value="14", unit="Tagen", context=["…von [14] Tagen…"])], tgt_only=[])]
    t, e = audit_view.rows(T)[0], audit_view.rows(T)[1]
    t, e = (t, e) if t["kind"] == "terminology" else (e, t)
    assert t["term"] == dict(old="inhibiteur de l'enzyme", new="antagoniste des récepteurs", where=["OPDIVO.02, 01.10.2026"]) and t["odd"] == "fr"
    assert e["eq"] == "Q1 conversion: 14 Tagen = 2 settimane" and t["eq"] is None
    assert audit_view.rows([dict(F[0], suggested_action="GÄL")])[0]["sug"] == "holder"


def test_terminology_notice_on_ready_drafts_comes_from_audit_item():
    old = explain._audit_item
    try:
        explain._audit_item = lambda x: ([dict(kind="terminology", lang="fr", old="AAA", new="BBB", corrected_in=["Z.1"])]
                                         if x["key"] == "wb000-fr" else [])
        D = build.data(audit=None)
    finally:
        explain._audit_item = old
    it = next(g["items"]["fr"] for g in D["groups"] if g["items"].get("fr", {}).get("key") == "wb000-fr")
    assert it["status"] == "ready" and it["old"][0]["k"] == "terminology" and "«\u00a0AAA\u00a0»" in it["old"][0]["t"] and "Z.1" in it["old"][0]["t"]
    assert it["banner"] == it["old"][0]["t"]


def test_audit_decision_strings_in_four_languages():
    """One question per issue, then the remedy: every string of the audit decision exists in DE/FR/IT/EN, the two old
    identical DE/FR/IT rows are gone, and the GEVER CSV header carries kind_code and action_code in every language."""
    from gleichlaut.ui import page
    s = page.BODY; tx8 = s[s.index("var TX8="):s.index("Object.keys(TX8)")]
    for k in ("aWrongQ", "oddDiff", "aRemQ", "rem", "remNeedW", "aMajQ", "aMajYes", "aMajNo", "aNameAsk", "aDecHint", "aLegacy", "csvHead"):
        assert tx8.count(k + ":") == 4, k
    assert tx8.count('"kind_code","Werte"') == 1 and tx8.count('"action_code"') == 4
    for k in ("ctlRight", "ctlActs", 'data-a="act"', 'data-a="right"'): assert k not in s, k
    assert "function aGate(" in s and "if(!who()){ANAME=true" in s and "function aDerive(" in s


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")


def test_findings_group_into_issues_deterministically():
    A = _audit(); R = A["rows"]; I = A["issues"]
    ix = sorted(i for g in I for i in g["rows"])
    assert ix == list(range(len(R)))                                         # a partition: every finding in exactly one issue
    assert len(I) < len(R) and I == audit_view.issues(list(R))               # grouping is a pure function of the findings
    for g in I:
        M = [R[i] for i in g["rows"]]
        assert len({tuple(r["gk"]) for r in M}) == 1 or any(r["expl"] for r in M)   # same conflict, or a typo explaining it
    dup = next(g for g in I if len(g["rows"]) > 1)                             # sibling products are one decision
    assert len(g["fids"]) == len(g["rows"]) and dup["iid"]
    for g in I:
        d = g["dating"]
        if d: assert d["first"] and (d["prev"] is None) == d["earliest"]      # "since the earliest snapshot" vs "first appeared between"
