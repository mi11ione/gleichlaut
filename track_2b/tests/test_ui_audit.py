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
    p = os.path.join(tempfile.mkdtemp(prefix="gl-ui-a-"), "index.html"); build.build(out=p)
    s = open(p, encoding="utf-8").read()
    assert s.index('id="t-audit"') < s.index('id="t-drafts"') and 'location.hash.slice(1)' in s and 'h==="audit"' in s
    for k in ('<option value="de">DE</option>', 'return "de"}', "Ready means checked by code, not by a person.",
              "Bereit heisst: vom Code geprüft, nicht von einer Person.", 'id="imp-file"', "data-copy", "gleichlaut:changed"):
        assert k in s, k
    for r in ("T1", "T2", "T3", "T4"): assert s.count('rd' + r + ':"') == 4                 # every rule in the legend, 4 languages
    assert "family cb735e3b" not in s


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


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
