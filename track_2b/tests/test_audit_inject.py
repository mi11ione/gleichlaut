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
