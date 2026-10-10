"""Planted-divergence recall of the audit (tools/audit_inject.py): the injectors are deterministic and plant exactly the
declared fault, a planted fault of each kind is found by audit_item on a synthetic pair, and the committed result file is
internally consistent (no snapshot needed)."""
import importlib.util, json, os, random
from gleichlaut import audit as A

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
_spec = importlib.util.spec_from_file_location("audit_inject", os.path.join(ROOT, "tools", "audit_inject.py"))
I = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(I)
FR = "Traitement de 4 semaines à la dose de 150 mg. Contrôle après 12 mois chez les patients de plus de 18 ans."
DE = "Behandlung über 4 Wochen mit einer Dosis von 150 mg. Kontrolle nach 12 Monaten bei Patienten über 18 Jahren."


def test_injectors_are_deterministic_and_plant_the_declared_fault():
    for t in ("number", "unit", "deletion", "typo"):
        a, b = I.INJ[t](FR, "fr", random.Random(f"x:{t}")), I.INJ[t](FR, "fr", random.Random(f"x:{t}"))
        assert a == b and a["new"] != FR, t
    n = I.inj_number(FR, "fr", random.Random(1)); assert n["old_value"] != n["new_value"] and n["after"] in n["new"]
    u = I.inj_unit(FR, "fr", random.Random(1)); assert u["after"] in u["new"] and u["before"] not in u["new"].replace(u["after"], "")
    d = I.inj_deletion(FR, "fr", random.Random(1)); assert len(d["new"]) < len(FR) and d["values"]
    lg = I.inj_language(FR, "fr", random.Random(1), {"de": DE, "it": DE}); assert lg["new"] == DE and lg["source"] == "de"


def test_a_planted_fault_of_each_kind_is_found_on_a_synthetic_pair():
    kinds = lambda tgt: {f["kind"] for f in A.audit_item(dict(de_old=DE, tgt_old=tgt, lang="fr"), terms=[])}
    assert not kinds(FR) - {"terminology"}
    assert "number" in kinds(FR.replace("4 semaines", "8 semaines"))
    assert "unit" in kinds(FR.replace("12 mois", "12 semaines"))
    assert "number" in kinds(FR.replace(" Contrôle après 12 mois chez les patients de plus de 18 ans.", ""))
    assert "editorial" in kinds(FR.replace("de 150 mg", "de150 mg"))


def test_committed_result_is_consistent():
    p = os.path.join(ROOT, "eval", "results", "audit_injection.json")
    R = json.load(open(p, encoding="utf-8"))
    assert R["model_calls"] == 0 and set(R["types"]) == set(I.TYPES)
    for t, v in R["types"].items():
        assert v["n"] == sum(x["n"] for x in v["by_lang"].values()) and 0 <= v["detected"] <= v["any_finding"] <= v["n"]
        assert abs(v["recall"] - v["detected"] / v["n"]) < 1e-3 and v["wilson95"] == I.wilson(v["detected"], v["n"])
        assert sum(v["miss_reasons"].values()) == v["n"] - v["detected"]
    V = R["verification"]
    assert V["copies"] >= 1 and V["stats_identical"] == V["limitation_identical"] == V["copies"]
    assert V["findings_new_elsewhere"] == V["findings_lost_elsewhere"] == 0


# ------------------------------------------------------------------ protocol v2 (sites not chosen by the audit's own rule)
FR2 = ("Code d'indication: 19989.01. Antagoniste du calcium I.T. 02.06 (RS 832.112.31). 1) Patients à partir de 12 ans, "
       "au moins 40 kg; ont reçu au moins deux traitements antérieurs; la dose n'est pas dépassée avant le 01.01.2025, "
       "score EASI ≥ 21, dix-huit centres, prix CHF 2'843.98.")
IT2 = "Pazienti di almeno 40 kg, oltre i 65 anni, non superiore a 2 volte il limite, al massimo due cicli."


def test_v2_tokens_cover_all_numbers_and_exclude_only_declared_codes():
    T = I.ntoks(FR2, "fr"); ex = {x["surf"]: x["excluded"] for x in T}
    assert ex["19989.01"] == "indication code" and ex["02.06"] == "IT group code" and ex["832.112.31"] == "multi-separator reference"
    inc = {x["surf"]: x["cat"] for x in T if not x["excluded"]}
    assert inc["1"] == "list" and inc["12"] == "v1_site" and inc["40"] == "v1_site" and inc["01.01.2025"] == "date"
    assert inc["21"] == "digit" and inc["2'843.98"] == "digit" and inc["deux"] == "word"
    assert "dix" not in inc and "huit" not in inc                    # hyphen-joined number words are not sites
    assert I.fmt2(2 * 2843.98, "2'843.98") == "5'687.96" and I.fmt2(15.0, "7,5") == "15"


def test_v2_injectors_are_deterministic_and_plant_the_declared_fault():
    for t in I.TYPES2:
        for L, x in (("fr", FR2), ("it", IT2)):
            a, b = I.INJ2[t](x, L, random.Random(f"y:{t}")), I.INJ2[t](x, L, random.Random(f"y:{t}"))
            assert a == b and a["new"] != x, (t, L)
    for k in range(30):                                               # every draw avoids the excluded codes
        n = I.inj_number_any(FR2, "fr", random.Random(k))
        assert n["old_value"] != n["new_value"] and n["token"] not in ("19989.01", "02.06", "832.112.31")
        assert n["new"][:n["pos"]] == FR2[:n["pos"]] and n["new_token"] in n["new"]
    w = I.inj_number_word(IT2, "it", random.Random(1)); assert w["token"] == "due" and w["new_token"] in I.NUMWORD["it"]
    ops = {I.inj_operator(IT2, "it", random.Random(k))["sub"] for k in range(40)}
    assert {"almeno->al massimo", "oltre->sotto", "superior->inferior", "al massimo->almeno"} <= ops
    assert {I.inj_operator(FR2, "fr", random.Random(k))["sub"] for k in range(40)} >= {"au moins->au plus", "≥->≤"}
    assert "dose est dépassée" in I.inj_negation(FR2, "fr", random.Random(0))["new"]
    assert I.inj_negation(IT2, "it", random.Random(0))["new"] == IT2.replace("non superiore", "superiore")
    assert I.inj_operator("Le traitement dure au moins un an.", "fr", random.Random(0)) is None     # no number nearby
    assert I.inj_operator("sotto forma di 3 iniezioni", "it", random.Random(0)) is None             # 'sotto forma': no operator


def test_committed_v2_result_is_consistent():
    p = os.path.join(ROOT, "eval", "results", "audit_injection_v2.json")
    if not os.path.exists(p): raise __import__("unittest").SkipTest("no v2 result file")
    R = json.load(open(p, encoding="utf-8"))
    assert R["model_calls"] == 0 and R["seed"] == I.SEED2 and set(R["types"]) == set(I.TYPES2)
    for t, v in R["types"].items():
        assert v["n"] == sum(x["n"] for x in v["by_lang"].values()) and 0 <= v["detected"] <= v["any_finding"] <= v["n"]
        assert v["wilson95"] == I.wilson(v["detected"], v["n"]) and sum(v["miss_reasons"].values()) == v["n"] - v["detected"]
        if "by_category" in v: assert sum(c["n"] for c in v["by_category"].values()) == v["n"]
    V = R["verification"]
    assert V["stats_identical"] == V["limitation_identical"] == V["copies"] and V["findings_new_elsewhere"] == 0
