"""Excerpts shown to the reader (register and Fallblatt) stand where the finding is: for every finding, each language's
excerpt contains the flagged value (with the flagged operator, or the flagged negation) in its own place, and the excerpts
of the other languages are the sentences the audit's sentence alignment pairs with it, not the first occurrence of the
value somewhere else in the text (the juror's Amvuttra case: the French 12-month rule shown for the 24-month stop rule)."""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from gleichlaut import audit as au
from gleichlaut.ui import audit_view as av

_D = {}


def _data():
    if not _D:
        _D["A"] = json.load(open(av.AUDIT, encoding="utf-8")); _D["D"] = av.data(hist=None)
    return _D["A"], _D["D"]


def _T(lim): return {k: au.nrm(v) for k, v in av._hist_texts(None, "20261006", lim).items()}


def _hot(segs): return [t for t, k in segs if k == 2]


def _text(segs): return "".join(t for t, _ in segs)


def _at(T, L, segs):
    """offset in T[L] of an excerpt (its text without the '…' ends), or None."""
    s = re.sub(r"\s+", " ", _text(segs)).strip().strip("…").strip()
    for n in (len(s), 60, 30):
        i = T[L].find(s[:n])
        if i >= 0: return i
    return None


def _same_place(T, ref, a, k, b):
    """offset b of language k lies in the sentence(s) aligned with the sentence of ref at offset a."""
    g = au.aligned_span(T, ref, a, k)
    return g is not None and g[0] <= b < g[1]


def test_operator_excerpts_are_the_aligned_pair():
    A, _ = _data(); n = 0
    for f in A["findings_r5"]:
        if f["kind"] != "operator": continue
        T = _T(f["id"]); o = au.operator_display(f, T); L = f["lang"]; n += 1
        assert o, f["fid"]
        for side, op in (("de", f["de_op"]), (L, f["tgt_op"])):
            m = re.search(r"\[([^\]]*)\]", o[side])
            assert m and op in m.group(1) and f["value"] in m.group(1), (f["fid"], side, o[side])
        if o["how"] == "aligned":
            a, b = T["de"].find(o["de"].strip("…").replace("[", "").replace("]", "")[:50]), T[L].find(o[L].strip("…").replace("[", "").replace("]", "")[:50])
            assert a >= 0 and b >= 0 and _same_place(T, "de", a + 60, L, b + 60), f["fid"]
    assert n == 4


def test_amvuttra_shows_the_stop_rule_in_all_three_languages():
    A, D = _data()
    f = next(f for f in A["findings_r5"] if f["id"] == "AMVUTTRA.01a" and f["kind"] == "operator")
    o = au.operator_display(f, _T(f["id"]))
    assert o["how"] == "aligned" and o["dirs"] == {"de": "min", "fr": "max", "it": "min"} and o["odd"] == "fr", o
    assert "12 mois: • augmentation du score NIS [≤ 10]" in o["fr"] and "pas d’augmentation" not in o["fr"], o["fr"]
    assert "[> 10]" in o["it"] and "NIS-Zunahme [> 10]" in o["de"]
    r = next(r for r in D["exp"]["rows"] if r["lim"] == "AMVUTTRA.01a")
    assert r["odd"] == "fr" and sorted(r["snip"]) == ["de", "fr", "it"]
    assert _hot(r["snip"]["fr"]) == ["≤ 10 points"] and _hot(r["snip"]["it"]) == ["> 10 punti"] and _hot(r["snip"]["de"]) == ["> 10 Punkte"]


def test_every_experimental_row_has_three_languages_and_its_flag():
    A, D = _data(); F5 = {f["fid"]: f for f in A["findings_r5"]}
    for r in D["exp"]["rows"]:
        f = F5[r["fid"]]; L = r["lang"]
        assert sorted(r["snip"]) == ["de", "fr", "it"], (r["fid"], sorted(r["snip"]))
        if r["xkind"] == "operator":
            assert any(f["de_op"] in h and f["value"] in h for h in _hot(r["snip"]["de"])), r["fid"]
            assert any(f["tgt_op"] in h and f["value"] in h for h in _hot(r["snip"][L])), r["fid"]
        elif r["xkind"] == "negation":
            side = f["side"]; assert any(w in _hot(r["snip"][side]) for w in f["negations"]), (r["fid"], r["snip"][side])
        else:
            for x in f.get("tgt_only") or []: assert x["value"] in [v for t in _hot(r["snip"][L]) for _, v in av._values_in(t, L)], r["fid"]
            for x in f.get("de_only") or []: assert x["value"] in [v for t in _hot(r["snip"]["de"]) for _, v in av._values_in(t, "de")], r["fid"]
    assert {r["lim"]: r["odd"] for r in D["exp"]["rows"]}["BEYONTTRA"] == "it"


def test_negation_excerpts_are_aligned_sentences():
    A, _ = _data()
    for f in A["findings_r5"]:
        if f["kind"] != "negation": continue
        T = _T(f["id"]); L = f["lang"]; de, tg = [c.rstrip("…") for c in f["context"]]
        a, b = T["de"].find(de[:80]), f["tgt_span"][0]
        assert a >= 0 and T[L][b:b + 40] == tg[:40], f["fid"]
        assert _same_place(T, L, b, "de", a), f["fid"]
        assert all(re.search(re.escape(w), (de if f["side"] == "de" else tg), re.I) for w in f["negations"]), f["fid"]


def test_main_findings_show_the_flagged_value_at_its_place():
    _, D = _data(); n = 0
    for r in D["rows"]:
        if r["kind"] == "terminology": continue
        n += 1
        for L, V in r["vals"].items():
            if r["kind"] == "number" and L in r["snip"]:
                got = {v for t in _hot(r["snip"][L]) for _, v in av._values_in(t, L)}
                assert got & set(V), (r["fid"], L, V, _text(r["snip"][L]))
        T = _T(r["lim"]); ref = next((k for k in av.LANGS if r["src"].get(k) == "context"), None)
        assert ref, r["fid"]
        a = _at(T, ref, r["snip"][ref])
        for k in av.LANGS:
            if r["src"].get(k) != "snapshot": continue
            b = _at(T, k, r["snip"][k])
            assert a is not None and b is not None, (r["fid"], k)
            g = au.aligned_span(T, ref, a + len(_text(r["snip"][ref])) // 2, k)
            assert g is None or (g[0] <= b + 5 and b < g[1]), (r["fid"], k, g, b, _text(r["snip"][k]))
    assert n == 27


def test_fallblatt_quotes_the_register_excerpts():
    import pilot_sheets as ps
    _, D = _data(); files = ps.build()
    sheets = "\n".join(files.values())
    for r in D["rows"] + D["exp"]["rows"]:
        for L, segs in r["snip"].items():
            want = ps.render(ps.mark({L: segs}, [])[L]) if r["kind"] != "number" else None
            if want: assert f"- **{ps.LANG[L]}:** {want}" in sheets, (r["fid"], L)
    x1 = next(v for k, v in files.items() if k.startswith("FB-X1_"))
    assert "- **FR:** …être survenus dans les 12 mois: • augmentation du score NIS **≤ 10 points**" in x1
    assert "- **IT:** " in x1 and "**\\> 10 punti**" in x1 and "| Weicht von den beiden anderen ab | FR |" in x1
    assert "PREREG" not in sheets and "Annotator, englisch" not in sheets


def test_fallblatt_remedies_are_the_register_buttons():
    import pilot_sheets as ps
    from gleichlaut.ui import page
    de = re.search(r"var TX8=\{\s*de:\{(.*?)\n(?:en):\{", open(page.__file__, encoding="utf-8").read(), re.S).group(1)
    rem = re.search(r"rem:\{exofficio:\"([^\"]+)\",holder:\"([^\"]+)\",langsvc:\"([^\"]+)\",none:\"([^\"]+)\",unclear:\"([^\"]+)\"\}", de).groups()
    assert tuple(rem) == ps.REM, rem
    assert f'aWrongQ:"{ps.WRONG_Q}"' in de and f'aRemQ:"{ps.REM_Q}"' in de
    for s in ps.build().values():
        if s.startswith("# Fallblatt"): assert all(x in s for x in ps.REM)


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
