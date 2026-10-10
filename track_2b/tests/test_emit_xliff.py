"""XLIFF emit: 10 recorded fresh-166 drafts -> one XLIFF 2.1 file per target language, valid against the vendored OASIS
core XSD (lxml); verdicts map to state/subState; the target is the draft with numbers marked. The XSD must reject broken
files, so a silent no-op validator fails this test. Runs under pytest or as `python3 tests/test_emit_xliff.py`."""
import os, re, sys, tempfile
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import score
from gleichlaut.emit import explain, load, select, validate, xliff

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
            assert not re.search(r"\b(?:model|run|ready|flagged|Previous)\b", notes["verdict"].text + notes["change"].text)
            assert v["cud_id"] in notes["change"].text
            marks = [m for s in S for m in s.find(X + "target").iter(X + "mrk")]
            assert [m.text for m in marks] == [t for _, _, t, _, _ in v["numbers"]]
            assert all(m.get("translate") == "no" for m in marks if m.get("type") == "gleichlaut:code-number")
    assert seen == 10


def test_at_most_three_plain_reasons_and_one_checks_note():
    """Translator-facing notes: at most three reasons without internal codes; every finding is still in the unit (the
    low-priority notes in one note category gleichlaut:note, priority 8; the rest, and the raw guard output with its
    codes, in one note category gleichlaut:checks, priority 10)."""
    meta, views = load("fresh166"); d = tempfile.mkdtemp(prefix="gl-xlf-all-"); V = {v["key"]: v for v in views}
    code = re.compile(r"\b(?:r[èe]gle|regola) T\d|\bT[1-8]\b|\bG\d[a-z]?\b|\b(?:Lock|Slots):")
    n_notes = []
    for p in xliff.write(views, meta, d):
        for u in ET.parse(p).getroot().iter(X + "unit"):
            v = V[u.get("id")]; N = list(u.find(X + "notes"))
            tb = [n for n in N if n.get("category") == "gleichlaut:termbase"]      # termbase advisory: its own note
            assert len(tb) <= 1 and all(n.get("priority") == "9" for n in tb); n_notes.append(len(N) - len(tb))
            reasons = [n for n in N if n.get("category") in ("gleichlaut:finding", "gleichlaut:divergence", "gleichlaut:model-numbers",
                                                             "gleichlaut:summary")]
            checks = [n for n in N if n.get("category") == "gleichlaut:checks"]
            low = [n for n in N if n.get("category") == "gleichlaut:note"]
            assert len(reasons) <= 3 and len(checks) == (1 if any(f.get("detail") for f in v["findings"]) else 0)
            assert all(not code.search(n.text) for n in N if n.get("category") != "gleichlaut:checks"), u.get("id")
            R = xliff.reasons(v)
            assert len([x for x in R if x["kind"] == "finding"]) == len(v["findings"])          # reworded, never dropped
            assert [n.text for n in reasons] == [x["text"] for x in xliff.top(R)]
            assert len(low) <= 1 and all(n.get("priority") == "8" and x["text"] in n.text for n in low for x in xliff.notes(R))
            assert bool(low) == bool(xliff.notes(R))
            if checks:
                assert checks[0].get("priority") == "10" and all(x["text"] in checks[0].text for x in xliff.rest(R))
                assert all(explain.clip(f["detail"], 220)[:60] in checks[0].text for f in v["findings"] if f.get("detail"))
            assert [n.get("priority") for n in reasons] == ["3" if x["low"] else "1" for x in xliff.top(R)]
            assert not any(x.get("tally") and x["rule"] for x in xliff.top(R))      # a probably-fine count never takes a slot
            if v["status"] == "flagged": assert reasons, u.get("id")              # a flagged draft always says why
    assert max(n_notes) <= 9 and len(n_notes) == len(views)


def test_deletion_matching_the_german_is_a_low_priority_question():
    V = {v["key"]: v for v in load("fresh166")[1]}
    for k, de in (("wb004-fr", "Nach 52 Wochen"), ("wb008-fr", "Dosierungsschema"), ("wb076-fr", "glykämische Kontrolle")):
        v = V[k]; R = xliff.reasons(v)                     # the German drops a sentence; the draft drops its French
        G = [r for r in R if r["gid"] == "g3"]
        assert G and all(r["tier"] != "reason" and r["low"] for r in G), k
        x = next(r for r in G if r["tier"] == "note")
        assert x["text"].startswith("Suppression conforme à l'allemand\u00a0? À vérifier") and de in x["text"], (k, x["text"])
        assert not any(r["gid"] == "g3" for r in xliff.top(R)) and x in xliff.notes(R)
        assert v["status"] == "flagged"                                                # the verdict is untouched
    v = V["wb067-fr"]                         # lost words outside what the German removes: still a reason to check
    assert any(r["gid"] == "g3" and r["tier"] == "reason" and r["text"].startswith("Le brouillon supprime davantage") for r in xliff.reasons(v))
    E = xliff.explanation(V["wb004-fr"])
    assert "Suppression conforme" in E["note"] and "plus ( sans modèle de" in E["note"] and "caisse maladie" in E["note"]


def test_mirror_is_decided_by_aligned_position_not_by_word_counts():
    de0 = "Die Therapie wird vergütet. Dosierungsschema und Dosierung sollen nach Angaben der Fachinformation erfolgen. Nur bis zur Progression."
    de1 = "Die Therapie wird vergütet. Nur bis zur Progression. Der Indikationscode ist zu übermitteln."
    fr0 = "Le traitement est remboursé. Le schéma posologique et la posologie doivent suivre l'information professionnelle. Seulement jusqu'à progression."
    x = dict(lang="fr", de_old=de0, de_new=de1, tgt_old=fr0)
    from gleichlaut import core
    ops = list(explain._de_ops(de0, de1))
    out = "Le traitement est remboursé. Seulement jusqu'à progression. Le code d'indication doit être transmis."
    bag = "schéma posologique posologie suivre information professionnelle"
    m = explain.mirror(x, out, ops, bag)
    assert m["mirrored"] == m["lost"] == 6 and m["de"].startswith("Dosierungsschema")       # same sentence: mirrored
    out2 = "Le schéma posologique et la posologie doivent suivre l'information professionnelle. Seulement jusqu'à progression. Le code d'indication doit être transmis."
    m2 = explain.mirror(x, out2, ops, "traitement remboursé")
    assert m2["mirrored"] == 0                          # the draft drops a sentence the German keeps: not mirrored
    assert core.lock.norm(out) != core.lock.norm(out2)


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
