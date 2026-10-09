"""XLIFF emit: 10 recorded fresh-166 drafts -> one XLIFF 2.1 file per target language, valid against the vendored OASIS
core XSD (lxml); verdicts map to state/subState; the target is the draft with numbers marked. The XSD must reject broken
files, so a silent no-op validator fails this test. Runs under pytest or as `python3 tests/test_emit_xliff.py`."""
import os, re, sys, tempfile
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import score
from gleichlaut.emit import load, select, validate, xliff

X = "{urn:oasis:names:tc:xliff:document:2.0}"
_C = {}
def _setup():
    if not _C:
        meta, views = load("fresh166"); V = select(views, 10); d = tempfile.mkdtemp(prefix="gl-xlf-")
        _C.update(V=V, d=d, paths=xliff.write(V, meta, d))
    return _C


def test_lxml_and_xsd_present():
    import lxml.etree  # noqa: F401  (required: without it the XSD check cannot run)
    assert os.path.exists(validate.XSD)


def test_files_validate_against_the_xliff_21_xsd():
    P = _setup()["paths"]
    assert [os.path.basename(p) for p in P] == ["gleichlaut-fresh166-de-CH_fr-CH.xlf", "gleichlaut-fresh166-de-CH_it-CH.xlf"]
    for p in P: assert validate.validate_xliff(p) == [], p


def test_units_carry_verdict_draft_and_context():
    C = _setup(); V = {v["key"]: v for v in C["V"]}; seen = 0
    for p in C["paths"]:
        r = ET.parse(p).getroot(); L = "fr" if r.get("trgLang") == "fr-CH" else "it"
        assert r.get("version") == "2.1" and r.get("srcLang") == "de-CH" and r.get("trgLang") in ("fr-CH", "it-CH")
        for u in r.iter(X + "unit"):
            v = V[u.get("id")]; seen += 1; S = u.findall(X + "segment")
            assert all((s.get("state"), s.get("subState")) == xliff.STATE[v["status"]] for s in S)
            assert all(s.get("state") == "translated" for s in S)              # never "initial" for a draft
            assert "".join("".join(s.find(X + "source").itertext()) for s in S) == v["de_new"]
            assert "".join("".join(s.find(X + "target").itertext()) for s in S) == v["draft"]
            notes = {n.get("id"): n for n in u.find(X + "notes")}
            assert notes["verdict"].text == xliff.nt(L, v["status"])
            assert notes["de-old"].text == xliff.nt(L, "prev_de", t=v["de_old"]) and notes["tgt-old"].text == xliff.nt(L, "prev_tgt", t=v["tgt_old"])
            assert "complaint" not in notes and not any(n.get("category") == "gleichlaut:guard" for n in notes.values())
            assert not re.search(r"\b(?:model|run|ready|flagged|Previous)\b", notes["verdict"].text + notes["product"].text)
            marks = [m for s in S for m in s.find(X + "target").iter(X + "mrk")]
            assert [m.text for m in marks] == [t for _, _, t, _, _ in v["numbers"]]
            assert all(m.get("translate") == "no" for m in marks if m.get("type") == "gleichlaut:code-number")
    assert seen == 10


def test_sentence_segments_and_changed_marks():
    C = _setup(); V = {v["key"]: v for v in C["V"]}; multi = 0
    from gleichlaut.emit import segment
    for p in C["paths"]:
        for u in ET.parse(p).getroot().iter(X + "unit"):
            v = V[u.get("id")]; S = u.findall(X + "segment")
            multi += len(S) > 1
            assert [s.get("id") for s in S] == [f"s{i}" for i in range(1, len(S) + 1)]
            ch = [m for s in S for m in s.find(X + "source").iter(X + "mrk")]
            assert all(m.get("type") == "gleichlaut:changed" and m.get("id").startswith("c") for m in ch)
            want = [v["de_new"][a:b] for a, b in segment.changed(v["de_old"], v["de_new"])]
            assert "".join(m.text for m in ch) == "".join(want) and want
    assert multi >= 5
    B = segment.align("Erster Satz mit 5 mg. Zweiter Satz. Dritter Satz hier.", "Première phrase avec 5 mg. Deuxième. Troisième phrase ici.")
    assert len(B) == 3


def test_header_notes_in_the_target_language():
    for p in _setup()["paths"]:
        r = ET.parse(p).getroot(); f = r.find(X + "file")
        txt = " ".join(n.text for n in f.find(X + "notes"))
        assert "model model" not in txt and "Hack Apertus" not in txt and "+-" not in txt
        assert ("Modèle swiss-ai" in txt) if r.get("trgLang") == "fr-CH" else ("Modello swiss-ai" in txt)


def test_never_contains_official_target_text():
    I = {x["key"]: x for x in score.load_items(score.RUNS["fresh166"]["items"])}
    texts = {p: "".join(ET.parse(p).getroot().itertext()) for p in _setup()["paths"]}
    for v in _setup()["V"]:
        off = I[v["key"]]["tgt_new"]
        if off != v["draft"]: assert all(off not in t for t in texts.values()), v["key"]


def test_xsd_rejects_broken_files():
    C = _setup(); src = open(C["paths"][0], encoding="utf-8").read()
    bad = {"state": src.replace('state="translated"', 'state="needs-review"', 1),
           "element": src.replace("<notes>", "<notes><comment>x</comment>", 1),
           "version": src.replace(' version="2.1"', "", 1),
           "unit-id": re.sub(r'<unit id="[^"]+"', '<unit id="a b"', src, count=1)}
    for name, s in bad.items():
        assert s != src, name
        p = os.path.join(C["d"], f"bad-{name}.xlf"); open(p, "w", encoding="utf-8").write(s)
        errs = validate.validate_xliff(p)
        assert errs and errs[0].startswith("XSD"), (name, errs)


def test_core_constraints_beyond_the_xsd():
    C = _setup(); src = open(C["paths"][0], encoding="utf-8").read()
    p = os.path.join(C["d"], "bad-trglang.xlf"); open(p, "w", encoding="utf-8").write(re.sub(r' trgLang="[^"]+"', "", src, count=1))
    assert "trgLang missing although targets exist" in validate.validate_xliff(p)


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
