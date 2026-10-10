"""House sentences (gleichlaut.house): BAG's dominant FR/IT wording of frequent fixed German sentences, mined from the
register with the termbase's method, and the display-only advisory (its own low-priority note, never a reason, never a
verdict). The words the German and target registers share (termbase.shared_words) are checked here too. Runs under pytest
or as `python3 tests/test_house.py`."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import house as H, termbase as T


def _entries():
    return {(e["lang"], e["de"]): e for e in json.load(open(H.JSON, encoding="utf-8"))["entries"]}


CODE_FR = "Folgender Indikationscode ist an den Krankenversicherer zu übermitteln:"
CODE_OLD = "Folgender Code ist an den Krankenversicherer zu übermitteln:"
CODE_NEW = "Der Indikationscode dieser Limitierung ist an den Krankenversicherer zu übermitteln."


def test_shipped_house_sentences_follow_the_rules():
    E = _entries()
    e = E[("fr", CODE_FR)]
    assert e["house"] and e["text"] == "Le code d'indication suivant doit être transmis à l'assureur-maladie:"
    assert (e["support"], e["limitations"]) == (111, 167) and e["variants"][0]["limitations"] >= H.VAR_MIN
    old = E[("fr", CODE_OLD)]                     # the classic closing formula: BAG's French is split, no house wording
    assert not old["house"] and old["share"] <= H.MIN_SHARE and "no dominant rendering" in old["note"]
    assert {v["text"] for v in old["variants"]} >= {"Le code suivant doit être transmis à l'assureur-maladie:",
                                                    "Le code suivant doit être transmis à l'assurance-maladie:"}
    it = E[("it", CODE_NEW)]
    assert it["house"] and it["text"].startswith("Il codice di indicazione di questa limitazione deve essere trasmesso")
    for e in E.values():
        assert e["limitations"] >= H.MIN_SUPPORT and len(H.WORD.findall(e["de"])) >= H.MIN_WORDS and "#" not in e["text"]
        if e["house"]: assert e["support"] >= H.MIN_SUPPORT and e["share"] > H.MIN_SHARE
        assert all(v["limitations"] >= H.VAR_MIN and v["limitations"] <= e["support"] for v in e["variants"])
        assert len(e["variants"]) <= H.MAX_VARIANTS


def test_key_abstracts_numbers_spacing_and_apostrophes():
    assert H.key("Le code suivant doit être transmis à l’assureur-maladie :  21150.07") == \
        H.key("Le code suivant doit être transmis à l'assureur-maladie: 20481.02") == "Le code suivant doit être transmis à l'assureur-maladie: #"
    assert H.key("« Après 12 semaines »") == H.key("«Après 24 semaines»")
    assert H.display("après 12 semaines, code 21150.07") == "après … semaines, code …"


def _reg(n_house=8, n_var=4):
    """a synthetic aligned register: one fixed German sentence in n_house + n_var limitations, written two ways in French."""
    J = {L: {"lim": {}, "prod": {}} for L in ("de", "fr", "it")}
    for k in range(n_house + n_var):
        i = f"L{k:02d}"
        p = "PRODUKT" + chr(65 + k)                         # one product name per limitation (numbers would be abstracted)
        J["de"]["lim"][i] = f"Die Behandlung mit {p} wird vergütet. Folgender Indikationscode ist an den Krankenversicherer zu übermitteln: 2{k:04d}.01"
        t = "Le code d'indication suivant doit être transmis à l'assureur-maladie" if k < n_house else "Le code suivant doit être communiqué à l'assurance maladie"
        J["fr"]["lim"][i] = f"Le traitement par {p} est remboursé. {t}: 2{k:04d}.01"
        J["it"]["lim"][i] = f"Il trattamento con {p} è rimborsato. Il seguente codice di indicazione deve essere trasmesso: 2{k:04d}.01"
    return J


def test_mining_finds_the_dominant_wording_and_its_variant():
    d = H.mine(_reg(10, 4), "20990101")
    fr = next(e for e in d["entries"] if e["lang"] == "fr" and e["de"] == CODE_FR)
    assert fr["house"] and (fr["support"], fr["limitations"]) == (10, 14) and fr["share"] == round(10 / 14, 3)
    assert [(v["text"], v["limitations"]) for v in fr["variants"]] == [("Le code suivant doit être communiqué à l'assurance maladie:", 4)]
    assert not any(e["de"].startswith("Die Behandlung mit") for e in d["entries"])         # one per product: under MIN_SUPPORT
    fr = next(e for e in H.mine(_reg(7, 7), "20990101")["entries"] if e["lang"] == "fr" and e["de"] == CODE_FR)
    assert not fr["house"] and fr["share"] == 0.5                                             # no majority: not used
    fr = next(e for e in H.mine(_reg(9, 1), "20990101")["entries"] if e["lang"] == "fr" and e["de"] == CODE_FR)
    assert not fr["house"] and fr["support"] == 9                                             # under MIN_SUPPORT: not used


def _v(L, de_new, old, draft, status="flagged"):
    return dict(lang=L, de_new=de_new, tgt_old=old, draft=draft, status=status)


def test_advice_names_the_house_wording_only_in_sentences_the_draft_wrote():
    de = "Die Therapie wird vergütet. " + CODE_FR + " 21242.01"
    old = "Le traitement est remboursé."
    A = H.advice(_v("fr", de, old, "Le traitement est remboursé. Le code d'indication suivant doit être communiqué à l'assureur-maladie : 21242.01"))
    assert [(a["kind"], a["support"]) for a in A] == [("departs", 111)]
    t = H.advisory_text(A, "fr")
    assert t.startswith(f"Phrase maison pour « {CODE_FR} » : « Le code d'indication suivant doit être transmis à l'assureur-maladie: » (111 limitations)")
    assert t.endswith("le brouillon écrit « Le code d'indication suivant doit être communiqué à l'assureur-maladie : ».")
    ok = "Le traitement est remboursé. Le code d'indication suivant doit être transmis à l’assureur-maladie : 21242.01"
    assert H.advice(_v("fr", de, old, ok)) == []                                   # the house wording (spacing, apostrophe, code aside)
    assert H.advice(_v("fr", de, old, "Le traitement est remboursé.")) == []        # no counterpart: the checks' business
    kept = "Le traitement est remboursé. Le code d'indication suivant doit être communiqué à l'assureur-maladie: 21242.01"
    assert H.advice(_v("fr", de, kept, kept)) == []                                 # carried over unchanged: left alone
    assert [a["kind"] for a in H.advice(_v("fr", de, kept, kept), carried=True)] == ["kept"]
    assert H.advice(_v("fr", de, old, "", status="human")) == [] and H.advice(_v("rm", de, old, "x")) == []
    var = H.advice(_v("fr", de, old, "Le traitement est remboursé. Le code suivant doit être transmis à l'assureur-maladie: 21242.01"))
    assert var and var[0]["variant"] and "(variante publiée dans" in H.advisory_text(var, "fr")


def test_long_sentences_show_the_part_that_differs():
    a = "Réglementation exceptionnelle : les cliniques de formation A, B et C ont le droit de collaborer avec des ophtalmochirurgiens en cabinet pour assurer des soins qui soient proches du patient."
    b = "Réglementation exceptionnelle: les cliniques de formation A, B et C ont le droit de collaborer avec des ophtalmo-chirurgiens en cabinet pour assurer des soins qui soient proches du patient."
    assert H.gist(a, b) == ("… avec des ophtalmochirurgiens en cabinet …", "… avec des ophtalmo-chirurgiens en cabinet …")
    assert H.gist("court", "kurz") == ("court", "kurz")


def test_shared_words_are_target_words_too():
    fr, it = T.shared("fr"), T.shared("it")
    assert "allergie" in fr and "teclistamab" in fr and "code" in fr
    assert not {"die", "der", "nur", "colitis", "krankenversicherer", "in"} & (fr | it)


def test_house_note_is_its_own_note_and_never_a_reason():
    from gleichlaut.emit import xliff
    v = dict(_v("fr", "Die Therapie wird vergütet. " + CODE_FR + " 21242.01", "Le traitement est remboursé.",
                "Le traitement est remboursé. Le code d'indication suivant doit être communiqué à l'assureur-maladie : 21242.01", "ready"),
             key="x-fr", findings=[], numbers=[], termbase=[], de_old="Die Therapie wird vergütet.", product="P", cud_id="P.01")
    v["house"] = H.advice(v)
    N = xliff.unit_notes(v, prev=False)
    assert [n[:4] for n in N if n[0] == "house"] == [["house", "gleichlaut:house", "target", "9"]]
    assert not any(n[1] == "gleichlaut:finding" for n in N) and v["status"] == "ready"
    assert "Phrase maison" in xliff.explanation(v)["note"]


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
