"""XLIFF 1.2 emit: 10 recorded fresh-166 drafts -> one XLIFF 1.2 file per target language, valid against the vendored
OASIS XLIFF 1.2 strict XSD (lxml, no network); verdicts map to valid 1.2 target states; numbers placed by code are
protected; notes carry the plain-language findings and the old texts. The XSD must reject broken files.
Runs under pytest or as `python3 tests/test_emit_xliff12.py`."""
import os, re, sys, tempfile
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import score
from gleichlaut.emit import load, select, validate, xliff, xliff12

X = "{urn:oasis:names:tc:xliff:document:1.2}"
_C = {}
def _setup():
    if not _C:
        meta, views = load("fresh166"); V = select(views, 10); d = tempfile.mkdtemp(prefix="gl-xlf12-")
        _C.update(meta=meta, V=V, d=d, paths=xliff12.write(V, meta, d))
    return _C


def test_schema_vendored_with_licence_note():
    assert os.path.exists(validate.XSD12) and os.path.exists(validate.XMLXSD)
    readme = open(os.path.join(validate.SCHEMAS, "README.md"), encoding="utf-8").read()
    assert "xliff-1.2/xliff-core-1.2-strict.xsd" in readme and "OASIS" in readme


def test_files_validate_against_the_xliff_12_strict_xsd():
    P = _setup()["paths"]
    assert [os.path.basename(p) for p in P] == ["gleichlaut-fresh166-de-CH_fr-CH.xliff12.xlf", "gleichlaut-fresh166-de-CH_it-CH.xliff12.xlf"]
    for p in P: assert validate.validate_xliff12(p) == [], p


def test_units_carry_state_draft_protected_numbers_and_notes():
    C = _setup(); V = {v["key"]: v for v in C["V"]}; seen = 0
    for p in C["paths"]:
        r = ET.parse(p).getroot(); f = r.find(X + "file")
        assert r.get("version") == "1.2" and f.get("source-language") == "de-CH" and f.get("target-language") in ("fr-CH", "it-CH")
        for tu in f.iter(X + "trans-unit"):
            v = V[tu.get("id")]; seen += 1
            t = tu.find(X + "target")
            assert t.get("state") == {"ready": "translated", "flagged": "needs-review-translation"}[v["status"]]
            assert "".join(t.itertext()) == v["draft"] and "".join(tu.find(X + "source").itertext()) == v["de_new"]
            prot = [m.text for m in t.iter(X + "mrk") if m.get("mtype") == "protected"]
            assert [m.text for m in tu.find(X + "source").iter(X + "mrk") if m.get("mtype") == "protected"] == \
                [m.group(0) for m in xliff12.core.gl2.NUMRX.finditer(v["de_new"])]
            assert prot == [n[2] for n in v["numbers"] if n[3] == "code"]
            notes = [n.text for n in tu.findall(X + "note")]; L = v["lang"]
            assert xliff.nt(L, "prev_de", t=v["de_old"]) in notes and xliff.nt(L, "prev_tgt", t=v["tgt_old"]) in notes
            assert xliff.nt(L, v["status"]) in notes and not any(n.startswith(("Previous", "Gleichlaut:")) for n in notes)
            chg = [m for m in tu.find(X + "source").iter(X + "mrk") if m.get("mtype") == "x-changed"]
            assert chg and all(m.get("comment") == xliff.nt(L, "changed") for m in chg)
            plain = [f["text"] for f in v["findings"]]
            assert all(any(s in n for n in notes) for s in plain)
            assert (v["status"] == "flagged") == bool([f for f in v["findings"] if f["gid"] != "corr"])
            alt = tu.find(X + "alt-trans")
            assert alt.get("alttranstype") == "previous-version" and alt.find(X + "target").text == v["tgt_old"]
    assert seen == 10


def test_segmented_like_xliff_21_without_lone_number_segments():
    C = _setup(); X2 = "{urn:oasis:names:tc:xliff:document:2.0}"
    seg21 = {}
    for p in xliff.write(C["V"], C["meta"], C["d"]):
        for u in ET.parse(p).getroot().iter(X2 + "unit"): seg21[u.get("id")] = len(u.findall(X2 + "segment"))
    for p in C["paths"]:
        for tu in ET.parse(p).getroot().iter(X + "trans-unit"):
            ss = [m for m in tu.find(X + "seg-source") if m.get("mtype") == "seg"]
            tg = [m for m in tu.find(X + "target") if m.get("mtype") == "seg"]
            assert len(ss) == len(tg) == seg21[tu.get("id")] and [m.get("mid") for m in ss] == [m.get("mid") for m in tg]
            assert "".join(tu.find(X + "seg-source").itertext()) == "".join(tu.find(X + "source").itertext())
            for m in ss + tg:
                t = "".join(m.itertext()).strip()
                assert len(t) >= 20 and re.search(r"[^\W\d_]{2}", t), (tu.get("id"), t)
    from gleichlaut.emit import segment
    src = "Folgender Code ist an den Krankenversicherer zu übermitteln: 21658.01"
    assert segment.beads(src) == [(0, len(src), 0, 0)]


def test_never_contains_official_target_text():
    I = {x["key"]: x for x in score.load_items(score.RUNS["fresh166"]["items"])}
    texts = ["".join(ET.parse(p).getroot().itertext()) for p in _setup()["paths"]]
    for v in _setup()["V"]:
        off = I[v["key"]]["tgt_new"]
        if off != v["draft"]: assert all(off not in t for t in texts), v["key"]


def test_xsd_rejects_broken_files():
    C = _setup(); src = open(C["paths"][0], encoding="utf-8").read()
    bad = {"state": src.replace('state="translated"', 'state="needs-review"', 1),
           "mtype": src.replace('mtype="protected"', 'mtype="locked"', 1),
           "element": src.replace("<body>", "<body><unit id=\"x\"/>", 1),
           "datatype": src.replace(' datatype="plaintext"', "", 1)}
    for name, s in bad.items():
        assert s != src, name
        p = os.path.join(C["d"], f"bad-{name}.xlf"); open(p, "w", encoding="utf-8").write(s)
        errs = validate.validate_xliff12(p)
        assert errs and errs[0].startswith("XSD"), (name, errs)



def test_header_tool_and_provenance():
    for p in _setup()["paths"]:
        r = ET.parse(p).getroot(); h = r.find(X + "file").find(X + "header")
        assert h.find(X + "tool").get("tool-company") == "Gleichlaut"
        txt = " ".join(n.text for n in h.findall(X + "note"))
        assert "model model" not in txt and "Hack Apertus" not in txt and "swiss-ai/apertus" in txt


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
