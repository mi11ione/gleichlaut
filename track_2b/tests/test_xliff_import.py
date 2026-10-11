"""gleichlaut xliff-import: XLIFF 1.2 / 2.1 files returned through translate-toolkit 3.20.0 (fixtures written by
tools/xliff_tt_roundtrip.py from `gleichlaut emit --run q8_0 --n 10`, the default 8B lane) read back into the register's
decisions JSON: signed off -> accept / accept-edited, cleared -> send-back, edited but not signed off -> edits only;
segments joined, split or flattened read the same; the gettext bridge (xliff2po / po2xliff renumbers the units) is
matched by the German source; a unit without a draft left empty stays untranslated. The decisions then go through
`gleichlaut emit --decisions` into reviewed XLIFF that validates. Runs under pytest or as `python3 tests/test_xliff_import.py`."""
import contextlib, io, json, os, re, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import cli
from gleichlaut.emit import xliff_import as XI

FX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "xliff-roundtrip")
T12, T21, PO = (os.path.join(FX, f) for f in ("returned-tt-fr-CH.xliff12.xlf", "returned-tt-fr-CH.xlf", "returned-po2xliff-fr-CH.xliff12.xlf"))
WANT = {"wb000-fr": "accept-edited", "wb001-fr": "edited", "wb002-fr": "edited", "wb003-fr": "accept", "wb004-fr": "send-back"}


def _out(res): return {r["key"]: r["outcome"] for r in res["units"]}


def _draft(key):
    return XI.register("q8_0")[1][key]["draft"]


def test_xliff12_returned_by_translate_toolkit():
    res = XI.import_files([T12])
    assert res["run"] == "q8_0" and res["source"] == "xliff-import" and len(res["run_sha256"]) == 64
    assert _out(res) == WANT and all(r["matched_by"] == "id" for r in res["units"])
    D = res["decisions"]
    assert sorted(D) == ["wb000-fr", "wb003-fr", "wb004-fr"]
    # wb000: the <mrk mtype="seg"> segments were replaced by one plain target (segmentation changed), then signed off
    assert D["wb000-fr"]["decision"] == "accept-edited" and D["wb000-fr"]["edited"] is True
    assert XI.norm(D["wb000-fr"]["text"]) == XI.norm(_draft("wb000-fr").replace("l'assurance maladie: ", "l'assureur-maladie : "))
    assert D["wb003-fr"]["decision"] == "accept" and D["wb003-fr"]["text"] == _draft("wb003-fr")
    assert D["wb004-fr"]["decision"] == "send-back" and "needs-translation" in D["wb004-fr"]["note"]
    # edited but left needs-review-translation / translated: no decision, the edited text goes to edits for the page
    assert "à base de platine" in res["edits"]["wb001-fr"] and "par osimertinib" in res["edits"]["wb002-fr"]
    assert res["edits"]["wb000-fr"] == D["wb000-fr"]["text"]


def test_xliff21_returned_by_translate_toolkit_with_joined_and_split_segments():
    res = XI.import_files([T21])
    assert _out(res) == WANT
    st = {r["key"]: r["states"] for r in res["units"]}
    assert st["wb000-fr"] == ["reviewed"]                       # s1 + s2 joined into one segment
    assert st["wb002-fr"] == ["translated"] * 3                 # s2 split into s2 + s3
    assert st["wb003-fr"] == ["final", "final"] and st["wb004-fr"] == ["initial", "initial"]
    want2 = _draft("wb002-fr").replace("l'assurance maladie: ", "l'assureur-maladie : ")
    assert XI.norm(res["edits"]["wb002-fr"]) == XI.norm(want2)   # the split reads back as one text, nothing lost
    D = res["decisions"]
    assert D["wb000-fr"]["decision"] == "accept-edited" and "l'assureur-maladie : 21390.03" in D["wb000-fr"]["text"]
    assert D["wb003-fr"]["decision"] == "accept" and D["wb004-fr"]["decision"] == "send-back"


def test_gettext_bridge_is_matched_by_the_german_source():
    """xliff2po -> PO -> po2xliff: unit ids renumbered (1.1 namespace, no target language), fuzzy -> needs-translation
    with the text kept, not fuzzy -> approved=yes. Same outcomes as the direct round trip."""
    res = XI.import_files([PO], run="q8_0", lang="fr")
    assert _out(res) == WANT and all(r["matched_by"] == "source" and r["id"] != r["key"] for r in res["units"])
    assert all(r["xliff"] == "1.1" for r in res["units"]) and len(res["units"]) == 5          # the PO header unit skipped
    with contextlib.redirect_stderr(io.StringIO()):
        assert cli.main(["xliff-import", PO]) == 2                                         # neither run nor language named


def test_untranslated_unit_without_draft_and_a_translator_filled_one():
    """A unit routed to a translator (no draft) left empty stays untranslated with no decision; one the translator wrote
    and signed off is accept-edited with status human."""
    meta, reg = XI.register("q8_0"); reg = {k: dict(v) for k, v in reg.items()}
    reg["wb004-fr"]["draft"] = None; reg["wb000-fr"]["draft"] = None
    orig = XI.register
    XI.register = lambda *a, **k: (meta, reg)
    try:
        for p in (T12, T21):
            res = XI.import_files([p])
            assert _out(res)["wb004-fr"] == "untranslated" and "wb004-fr" not in res["decisions"]
            d = res["decisions"]["wb000-fr"]
            assert d["decision"] == "accept-edited" and d["status"] == "human" and "assureur-maladie" in d["text"]
    finally:
        XI.register = orig


def test_reviewer_and_time_from_the_file():
    d = tempfile.mkdtemp(prefix="gl-xi-")
    s = open(T12, encoding="utf-8").read()
    s = s.replace("<header>", '<header><phase-group><phase phase-name="rev1" process-name="review" contact-name="A. Muster" '
                              'date="2026-10-11T10:00:00Z"/></phase-group>', 1)
    s = re.sub(r'(<trans-unit id="wb000-fr".*?<target )', r'\1phase-name="rev1" ', s, count=1, flags=re.S)
    p = os.path.join(d, "r.xliff12.xlf"); open(p, "w", encoding="utf-8").write(s)
    res = XI.import_files([p])
    assert res["reviewer"] == "A. Muster" and res["decisions"]["wb000-fr"]["by"] == "A. Muster"
    assert res["decisions"]["wb000-fr"]["at"] == "2026-10-11T10:00:00Z"
    s = open(T21, encoding="utf-8").read().replace('<file id="f1" original="gleichlaut:q8_0">',
        '<file id="f1" original="gleichlaut:q8_0"><mda:metadata xmlns:mda="urn:oasis:names:tc:xliff:metadata:2.0">'
        '<mda:metaGroup><mda:meta type="reviewer">B. Rossi</mda:meta></mda:metaGroup></mda:metadata>', 1)
    p = os.path.join(d, "r.xlf"); open(p, "w", encoding="utf-8").write(s)
    assert XI.import_files([p])["decisions"]["wb003-fr"]["by"] == "B. Rossi"
    assert XI.import_files([p], reviewer="C. Weber")["decisions"]["wb003-fr"]["by"] == "C. Weber"


def test_bad_input_exits_2():
    d = tempfile.mkdtemp(prefix="gl-xi-"); p = os.path.join(d, "x.xml"); open(p, "w").write("<html/>")
    with contextlib.redirect_stderr(io.StringIO()) as e:
        assert cli.main(["xliff-import", p]) == 2
        assert cli.main(["xliff-import", T12, "--run", "fresh166"]) == 2
    assert "not XLIFF" in e.getvalue() and "not fresh166" in e.getvalue()


def test_cli_writes_decisions_that_emit_turns_into_valid_reviewed_xliff():
    """The loop closes: exported XLIFF unchanged -> no decisions; returned files -> decisions JSON (the review page's
    format) -> `gleichlaut emit --decisions` -> reviewed XLIFF 2.1 / 1.2, validated against the OASIS XSDs."""
    try: import lxml  # noqa: F401
    except ImportError: raise unittest.SkipTest("lxml absent: emit cannot validate")
    d = tempfile.mkdtemp(prefix="gl-xi-"); out = os.path.join(d, "dec.json")
    with contextlib.redirect_stdout(io.StringIO()):
        assert cli.main(["emit", "--run", "q8_0", "--n", "10", "--out", os.path.join(d, "emit")]) == 0
    x = os.path.join(d, "emit", "xliff")
    with contextlib.redirect_stdout(io.StringIO()) as o, contextlib.redirect_stderr(io.StringIO()):
        assert cli.main(["xliff-import", os.path.join(x, "gleichlaut-q8_0-de-CH_fr-CH.xliff12.xlf"),
                         os.path.join(x, "gleichlaut-q8_0-de-CH_it-CH.xlf")]) == 0
    fresh = json.loads(o.getvalue())
    assert not fresh["decisions"] and not fresh["edits"] and {r["outcome"] for r in fresh["units"]} == {"unchanged"}
    with contextlib.redirect_stderr(io.StringIO()) as e:
        assert cli.main(["xliff-import", T21, "--out", out]) == 0
    assert "accept 1, accept-edited 1, send-back 1, edited 2" in e.getvalue()
    with contextlib.redirect_stdout(io.StringIO()) as o:
        assert cli.main(["emit", "--run", "q8_0", "--n", "10", "--decisions", out, "--out", os.path.join(d, "rev")]) == 0
    assert "validation PASSED" in o.getvalue()
    r = open(os.path.join(d, "rev", "xliff", "gleichlaut-q8_0-de-CH_fr-CH-reviewed.xlf"), encoding="utf-8").read()
    assert "l'assureur-maladie : " in r and 'subState="gleichlaut:accepted-edited"' in r and 'subState="gleichlaut:sent-back"' in r


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_"): f(); print("ok", n)
