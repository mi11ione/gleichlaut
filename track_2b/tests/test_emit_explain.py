"""Plain-language guard findings (emit/explain.py) and the pre-existing-divergence rendering: one sentence per finding
in the draft's language, no raw token dumps or G-numbers in the sentence, the verdict untouched; the Nemluvio IT draft
that fixes 'ogni quattro -> otto' is presented as a correction to check, not only as lost words.
Runs under pytest or as `python3 tests/test_emit_explain.py`."""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import core, score
from gleichlaut.emit import explain, load

_C = {}
def _views():
    if not _C: _C["V"] = {v["key"]: v for v in load("fresh166")[1]}
    return _C["V"]


def test_one_sentence_per_finding_in_the_drafts_language():
    def starts(lang):          # each sentence starts like one of the language's templates (explain.T)
        return tuple({(explain._fr(T[lang]) if lang == "fr" else T[lang]).split("{")[0][:12] for T in explain.T.values()} - {""})
    S = {L: starts(L) for L in ("fr", "it")}
    for v in _views().values():
        for f in v["findings"]:
            t = f["text"]
            assert t and "\n" not in t and len(t) < 420, (v["key"], t)
            assert not re.search(r"\bG\d\b|G3[ac]|->|«»", t), (v["key"], t)          # no G-ids, no raw token arrows
            assert t.startswith(S[v["lang"]]), (v["key"], t)
            if f["gid"] != "corr": assert f["detail"] and f["name"], v["key"]


def test_verdict_is_untouched():
    for v in _views().values():
        guard = [f for f in v["findings"] if f["gid"] != "corr"]
        assert bool(guard) == (v["status"] == "flagged"), v["key"]
        failed = {g for g, _, st, _ in v["lights"] if st == "fail"} - {"reask"}
        assert {("slot" if f["gid"] == "unknown" else f["gid"]) for f in guard} <= failed, v["key"]


def test_readable_phrases_instead_of_token_bags():
    V = _views()
    g2 = [f["text"] for f in V["wb001-fr"]["findings"] if f["gid"] == "g2"][0]
    assert "nicht-kleinzelligem Lungenkarzinom" in g2 and "( »" not in g2
    g3 = [f["text"] for f in V["wb001-it"]["findings"] if f["gid"] == "g3"][0]
    assert "carcinoma polmonare non a piccole cellule" in g3           # the phrase of the old text, not the lemma bag
    g4 = [f["text"] for f in V["wb003-fr"]["findings"] if f["gid"] == "g4"][0]
    assert g4.count("grandes cellules") == 1                           # overlapping 6-grams merged into one phrase


def test_nemluvio_it_correction_is_named():
    v = _views()["wb004-it"]
    c = [f for f in v["findings"] if f["gid"] == "corr"]
    assert c and "«ogni quattro settimane» → «ogni otto settimane»" in c[0]["text"] and "acht" in c[0]["text"]
    lost = [f for f in v["findings"] if f["gid"] in ("g3", "lock") and "quattro" in f["text"]]
    assert lost and all(f["corrects"] for f in lost)
    assert v["status"] == "flagged"                                    # still flagged: a translator decides
    assert "corregge" in explain.corr_note("it") and "corrige" in explain.corr_note("fr")


def test_divergence_banner_when_audit_is_available():
    v = _views()["wb004-it"]
    if explain._audit_item is None:
        assert v["banner"] is None; return
    assert v["banner"].startswith("Il vecchio testo italiano diverge già dal tedesco") and "acht" in v["banner"]


def test_divergence_adapter_accepts_other_shapes():
    x = dict(key="k-fr", lang="fr", de_old="a", de_new="a", tgt_old="b")
    old = explain._audit_item
    try:
        explain._audit_item = lambda x: [dict(side="de", value="8", unit="Wochen", context=["…alle [acht] Wochen, zur…"])]
        d = explain.divergence(x); assert d and "alle acht Wochen" in d[0]["text"] and d[0]["text"].startswith("l'allemand dit")
        explain._audit_item = lambda x: {"divergences": [("8", "4")]}
        assert "allemand" in explain.divergence(x)[0]["text"]
        explain._audit_item = lambda x: []
        assert explain.divergence(x) == [] and explain.banner(x, []) is None
        explain._audit_item = lambda x: 1 / 0
        assert explain.divergence(x) == []
    finally:
        explain._audit_item = old


def test_decimal_separator_hint():
    v = _views().get("wb038-it")
    if not v: return
    t = [f["text"] for f in v["findings"] if "20,20" in f["text"]]
    assert t and "separatore decimale" in t[0]


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
