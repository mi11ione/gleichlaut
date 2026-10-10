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



def test_change_applied_names_what_is_checked_not_unrelated_pairs():
    V = _views()
    g2 = [f["text"] for f in V["wb057-fr"]["findings"] if f["gid"] == "g2"]
    assert g2 and not any("Das Dosierungsschema" in t and "Kostengutsprache" in t for t in g2)
    assert any(t.startswith("L'allemand ajoute ici la phrase") and "Indikationscode (20481.XX) zu enthalten" in t
               and t.endswith("elle manque dans le brouillon.") for t in g2)          # nothing in the draft translates it
    g2 = [f["text"] for f in V["wb080-fr"]["findings"] if f["gid"] == "g2"]
    assert any("Neurogenic Detrusor Overactivity" in t for t in g2) and not any("Spina bifida" in t for t in g2)
    assert explain.related("Zeitpunkt", "Zeit-punkt") and explain.related("Monaten", "Monate") and explain.related("48 Wochen", "18 Monaten")
    assert not explain.related("Kombination", "Indikationen") and not explain.related("Das Dosierungsschema", "Eine Kostengutsprache")
    x = dict(lang="fr", de_old="Die Therapie wird vergütet.", de_new="Die Therapie wird vergütet. Folgender Code ist an den Krankenversicherer zu übermitteln: 21242.01")
    t = explain.g2_text("fr", "add", x, "", "Folgender Code ist an den Krankenversicherer zu übermitteln: 21242.01", None, (28, len(x["de_new"])))
    assert t.startswith("L'allemand ajoute ou réécrit ici la phrase") and "Krankenversicherer zu übermitteln" in t, t
    assert explain.g2_text("it", "remove", dict(x, de_old="a b"), "nicht adäquat", "", (0, 3), None).startswith("La soppressione tedesca di «nicht adäquat»")


def test_change_applied_states_missing_left_in_german_or_kept():
    """A sentence the German adds: 'missing' when the draft only carries over old sentences there, 'left in German' when
    the draft has its German words; a sentence the German removes and the draft carries over: named. Otherwise hedged."""
    de0 = "Die Therapie wird vergütet. Nur bis zur Progression der Krankheit."
    de1 = "Die Therapie wird vergütet. Eine Kostengutsprache hat den entsprechenden Indikationscode zu enthalten. Nur bis zur Progression der Krankheit."
    fr0 = "Le traitement est remboursé. Seulement jusqu'à progression de la maladie."
    x = dict(lang="fr", de_old=de0, de_new=de1, tgt_old=fr0)
    sb = (de1.index("Eine"), de1.index(" Nur"))
    t = lambda out: explain.g2_text("fr", "add", x, "", de1[sb[0]:sb[1]], None, sb, out).replace("\u00a0", " ")
    assert t(fr0).endswith("elle manque dans le brouillon.") and t(fr0).startswith("L'allemand ajoute ici la phrase « Eine Kostengutsprache")
    left = "Le traitement est remboursé. Eine Kostengutsprache hat den entsprechenden Indikationscode zu enthalten. Seulement jusqu'à progression de la maladie."
    assert "le brouillon la laisse en allemand" in t(left)
    done = "Le traitement est remboursé. Une garantie de prise en charge doit contenir le code d'indication. Seulement jusqu'à progression de la maladie."
    assert "vérifier qu'elle est traduite" in t(done)                    # something new is there: the check cannot tell
    assert "vérifier qu'elle est traduite" in t(None)                    # no draft: hedged as before
    sa = (de0.index("Nur"), len(de0)); xd = dict(x, de_new="Die Therapie wird vergütet.")
    k = explain.g2_text("fr", "remove", xd, de0[sa[0]:], "", sa, None, fr0).replace("\u00a0", " ")
    assert k.endswith(": le brouillon garde la phrase correspondante « Seulement jusqu'à progression de la maladie. ».") , k
    assert "vérifier que le brouillon la supprime" in explain.g2_text("fr", "remove", xd, de0[sa[0]:], "", sa, None, "Le traitement est remboursé.")


def test_german_looking_target_words_and_repetitions_the_german_has_too():
    from gleichlaut.emit import xliff
    V = _views()
    v = V["wb012-fr"]                                                   # 'allergie': French too (BAG's French register has it)
    f = next(f for f in v["findings"] if f["gid"] == "g5")
    assert explain.lexicon_fine(v, f) == (["allergie"], [])
    r = next(x for x in xliff.reasons(v) if x["gid"] == "g5")
    assert r["low"] and r["tier"] == "reason" and "probablement sans problème" in r["text"] and "limitations françaises" in r["text"]
    x = dict(lang="fr", tgt_old="Le teclistamab est remboursé.", findings=[])
    assert explain.lexicon_fine(x, dict(gid="g5", detail="G5: teclistamab, die, Krankenversicherer")) == (["teclistamab"], ["die", "Krankenversicherer"])
    v = V["wb044-fr"]                                                   # 'ou d'une perte de vision' x2: the German repeats it too
    f = next(f for f in v["findings"] if f["gid"] == "g4")
    assert explain.german_repeats(v, v["draft"], f["detail"])
    r = next(x for x in xliff.reasons(v) if x["gid"] == "g4")
    assert r["low"] and "l'allemand le répète aussi" in r["text"]
    y = dict(lang="fr", de_new="Die Therapie wird vergütet. Nur bei Erwachsenen.")
    assert not explain.german_repeats(y, "Le traitement est remboursé. Le traitement est remboursé chez les adultes.",
                                      "G4 repeated 6-grams: «le traitement est remboursé»")


def test_typography_the_draft_introduces_is_named_once():
    old = "Dermatite atopique – adultes et adolescents (sans modèle de prix) et/ou enfants."
    T = explain.typography(old, "Dermatite atopique – adultes et adolescents ( sans modèle de prix ) et / ou enfants , dès 12 ans. . Fin.")
    assert [k for k, _ in T] == ["open", "close", "comma", "slash", "double"] and "( sans modèle" in T[0][1]
    assert explain.typography(old, old) == [] and explain.typography("a ( b )", "a ( b ) c") == []      # already in the old text
    assert explain.typography("Prix 1.5 mg… voir p. 3", "Prix 1.5 mg… voir p. 3 ; « ici » : là ! oui ?") == []     # French spacing is correct


def test_counts_explained_by_sentences_both_remove():
    V = _views()
    v = V["wb004-fr"]                        # German drops 'Nemolizumab wird nicht …' and two more sentences, the draft too
    f = next(f for f in v["findings"] if f["detail"].startswith("Slots: neg"))
    assert explain.tally_mirrored(v, v["draft"], f["detail"])
    assert not explain.tally_mirrored(v, v["draft"], "Slots: nums DE +{} -{}, target +{} -{}")

if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
