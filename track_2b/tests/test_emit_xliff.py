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
    low-priority notes in one note category gleichlaut:note, priority 8; the remaining reasons in plain words in one note
    category gleichlaut:checks, priority 10; the raw guard output with its codes only in one note category
    gleichlaut:debug, priority 10)."""
    meta, views = load("fresh166"); d = tempfile.mkdtemp(prefix="gl-xlf-all-"); V = {v["key"]: v for v in views}
    code = explain.CODE
    n_notes = []
    for p in xliff.write(views, meta, d):
        for u in ET.parse(p).getroot().iter(X + "unit"):
            v = V[u.get("id")]; N = list(u.find(X + "notes"))
            tb = [n for n in N if n.get("category") == "gleichlaut:termbase"]      # termbase advisory: its own note
            hs = [n for n in N if n.get("category") == "gleichlaut:house"]           # house-sentence advisory: its own note
            assert len(tb) <= 1 and all(n.get("priority") == "9" for n in tb + hs) and len(hs) <= 1
            n_notes.append(len(N) - len(tb) - len(hs) - sum(n.get("category") == "gleichlaut:debug" for n in N))
            reasons = [n for n in N if n.get("category") in ("gleichlaut:finding", "gleichlaut:divergence", "gleichlaut:model-numbers",
                                                             "gleichlaut:summary")]
            checks = [n for n in N if n.get("category") == "gleichlaut:checks"]
            debug = [n for n in N if n.get("category") == "gleichlaut:debug"]
            low = [n for n in N if n.get("category") == "gleichlaut:note"]
            assert len(reasons) <= 3 and len(debug) == (1 if any(f.get("detail") for f in v["findings"]) else 0)
            assert len(checks) == (1 if [x for x in xliff.rest(xliff.reasons(v)) if not x.get("dup")] else 0)
            assert all(not code.search(n.text) for n in N if n.get("category") != "gleichlaut:debug"), u.get("id")
            R = xliff.reasons(v)
            assert len([x for x in R if x["kind"] == "finding"]) == len(v["findings"])          # reworded, never dropped
            assert [n.text for n in reasons] == [x["text"] for x in xliff.top(R)]
            assert len(low) <= 1 and all(n.get("priority") == "8" and x["text"] in n.text for n in low for x in xliff.notes(R))
            assert bool(low) == bool(xliff.notes(R))
            if checks:
                assert checks[0].get("priority") == "10" and all(x["text"] in checks[0].text for x in xliff.rest(R) if not x.get("dup"))
            if debug:
                assert debug[0].get("priority") == "10" and all(explain.clip(f["detail"], 220)[:60] in debug[0].text for f in v["findings"] if f.get("detail"))
            assert [n.get("priority") for n in reasons] == ["3" if x["low"] else "1" for x in xliff.top(R)]
            assert not any(x.get("tally") and x["rule"] for x in xliff.top(R))      # a probably-fine count never takes a slot
            if v["status"] == "flagged": assert reasons, u.get("id")              # a flagged draft always says why
    assert max(n_notes) <= 9 and len(n_notes) == len(views)


def test_deletion_matching_the_german_is_a_low_priority_note():
    V = {v["key"]: v for v in load("fresh166")[1]}
    for k, de in (("wb004-fr", "Nach 52 Wochen"), ("wb008-fr", "Dosierungsschema"), ("wb076-fr", "In Kombination mit Insulin")):
        v = V[k]; R = xliff.reasons(v)                     # the German drops a sentence; the draft drops its French, one to one
        G = [r for r in R if r["gid"] == "g3"]
        assert G and all(r["tier"] != "reason" and r["low"] for r in G), k
        x = next(r for r in G if r["tier"] == "note")
        assert x["whole"] and x["text"].startswith("Suppression conforme à l'allemand\u00a0: l'allemand retire la phrase") and de in x["text"], (k, x["text"])
        assert "le brouillon retire la phrase correspondante" in x["text"] and "?" not in x["text"]
        assert not any(r["gid"] == "g3" for r in xliff.top(R)) and x in xliff.notes(R)
        assert v["status"] == "flagged"                                                # the verdict is untouched
    E = xliff.explanation(V["wb008-fr"])                   # wb008: every finding is a note or a detail: 0 to check
    assert E["counts"] == [0, 5] and E["top"] and E["top"][0][1]
    v = V["wb001-it"]                                      # a phrase the German shortens: still a question
    x = next(r for r in xliff.reasons(v) if r["gid"] == "g3" and r["tier"] == "note")
    assert not x["whole"] and x["text"].startswith("Soppressione conforme al tedesco? Da verificare")
    v = V["wb067-fr"]                         # lost words outside what the German removes: still a reason to check
    assert any(r["gid"] == "g3" and r["tier"] == "reason" and r["text"].startswith("Le brouillon supprime davantage") for r in xliff.reasons(v))
    E = xliff.explanation(V["wb004-fr"])
    assert "Suppression conforme" in E["note"] and "plus ( sans modèle de" in E["note"] and "le brouillon écrit «\u00a0caisse maladie\u00a0»" in E["note"]


def test_header_counts_what_the_reasons_list_shows():
    V = load("fresh166")[1]
    for v in V:
        if v["status"] != "flagged": continue
        R = xliff.reasons(v, old=False); c = xliff.counts(R)
        shown = [x for x in R if x["kind"] in ("finding", "model-numbers") and x["tier"] == "reason"]
        assert c[0] == sum(1 for x in shown if not x["low"] or x["gid"] == "record"), v["key"]
        assert c[0] + c[1] <= len([x for x in R if x["kind"] in ("finding", "model-numbers")]), v["key"]
        if c[0] == 0: assert all(x["low"] for x in xliff.top(R)), v["key"]          # nothing to check is shown as one


def test_house_sentence_note_and_debug_note_in_both_xliff_versions():
    from gleichlaut.emit import xliff12
    V = {v["key"]: v for v in load("fresh166")[1]}
    v = V["wb013-fr"]                               # 'communiqué' where BAG writes 'transmis' (111 limitations)
    h = xliff.house_note(v).replace("\u00a0", " ")
    assert h.startswith("Phrase maison pour « Folgender Indikationscode ist an den Krankenversicherer zu übermitteln: »")
    assert "(111 limitations)" in h and "le brouillon écrit « Le code d'indication suivant doit être communiqué" in h
    N = xliff.unit_notes(v); ids = [n[0] for n in N]
    assert ids.index("house") < ids.index("checks") if "checks" in ids else True
    assert [n[1:4] for n in N if n[0] == "house"] == [["gleichlaut:house", "target", "9"]]
    assert [n[1:4] for n in N if n[0] == "debug"] == [["gleichlaut:debug", None, "10"]]
    d = tempfile.mkdtemp(prefix="gl-xlf-house-"); meta = load("fresh166")[0]
    for p in xliff.write([v], meta, d): assert validate.validate_xliff(p) == [], p
    for p in xliff12.write([v], meta, d):
        assert validate.validate_xliff12(p) == [], p
        src = open(p, encoding="utf-8").read()
        assert 'from="gleichlaut-debug"' in src and "Phrase maison" in src


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


def test_review_decisions_sent_back_has_no_target_and_accepted_drops_the_flagged_verdict():
    """A sent-back unit never carries the rejected draft as pre-translation (XLIFF 2.1: no target, the draft in a note;
    XLIFF 1.2: an empty target with state needs-translation, the draft in alt-trans rejected); an accepted unit's verdict
    note is the reviewed note, not 'flagged … to correct'; the reviewer's reason is in the file's language."""
    from gleichlaut.emit import xliff12
    meta, views = load("q8_0"); d = tempfile.mkdtemp(prefix="gl-xlf-rev-")
    fl = [v for v in views if v["status"] == "flagged" and v["lang"] == "it"][:2]
    D = {fl[0]["key"]: dict(decision="send-back", reason="Content lost", note="", at="2026-10-11T10:00:00Z"),
         fl[1]["key"]: dict(decision="accept", reason="Wording", note="", at="2026-10-11T10:01:00Z")}
    V = [v for v in views if v["key"] in D]
    for p in xliff.write(V, meta, d, D) + xliff12.write(V, meta, d, D):
        assert (validate.validate_xliff12(p) if p.endswith(".xliff12.xlf") else validate.validate_xliff(p)) == [], p
    r = ET.parse(os.path.join(d, "gleichlaut-q8_0-de-CH_it-CH-reviewed.xlf")).getroot()
    U = {u.get("id"): u for u in r.iter(X + "unit")}
    sb, ac = U[fl[0]["key"]], U[fl[1]["key"]]
    assert all(s.find(X + "target") is None and s.get("subState") == "gleichlaut:sent-back" for s in sb.findall(X + "segment"))
    N = {n.get("id"): n.text for n in sb.find(X + "notes")}
    assert N["verdict"].startswith("Rinviata in revisione") and fl[0]["draft"] in N["rejected"] and "contenuto perso" in N["review"]
    A = {n.get("id"): n.text for n in ac.find(X + "notes")}
    assert A["verdict"].startswith("Rivista e accettata") and "segnalata" in A["verdict"] and "formulazione" in A["review"]
    assert not any("Il testo d'arrivo è la bozza, da correggere" in (n.text or "") for n in ac.find(X + "notes"))
    x = open(os.path.join(d, "gleichlaut-q8_0-de-CH_it-CH-reviewed.xliff12.xlf"), encoding="utf-8").read()
    N12 = "{urn:oasis:names:tc:xliff:document:1.2}"
    T = {t.get("id"): t for t in ET.fromstring(x.encode()).iter(N12 + "trans-unit")}
    t0 = T[fl[0]["key"]].find(N12 + "target")
    assert t0.get("state") == "needs-translation" and not "".join(t0.itertext())
    rj = [a for a in T[fl[0]["key"]].findall(N12 + "alt-trans") if a.get("alttranstype") == "rejected"]
    assert len(rj) == 1 and "".join(rj[0].find(N12 + "target").itertext()) == fl[0]["draft"]
    assert T[fl[1]["key"]].get("approved") == "yes" and T[fl[1]["key"]].find(N12 + "target").get("state") == "signed-off"


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
    S = lambda t: [t[a:b].strip() for a, b in segment.sentences(t)]                 # an abbreviation's full stop ends nothing
    assert S("Mit einem Calciumantagonisten des I.T. 02.06 und/oder einem ACE-Hemmer. Neu.") == \
        ["Mit einem Calciumantagonisten des I.T. 02.06 und/oder einem ACE-Hemmer.", "Neu."]
    for t in ("Bei Ansprechen (z.B. TTR-Stabilisatoren) weiter.", "Nach ca. 6 Zyklen weiter.", "Dr. med. Fadi Haidar, Genf.",
              "Von Fr. 40.-- zuzüglich MWST.", "Patienten (u.a. Kinder) resp. Erwachsene.", "En association (p. ex. AINS) seulement.",
              "Selon l'art. 52 al. 3 LAMal.", "In der Kombination (z. B. Methotrexat) weiter.", "1 bzw. 2 Durchstf. zurück."):
        assert S(t) == [t], t
    assert S("Bis zum Ende etc. Danach nicht.") == ["Bis zum Ende etc.", "Danach nicht."] and S("Typ A. Die Dosis.") == ["Typ A.", "Die Dosis."]


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
