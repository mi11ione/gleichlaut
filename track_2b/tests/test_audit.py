"""Pre-existing congruence audit (gleichlaut.audit): rules on synthetic texts, the UI hook on the fresh items, and the full
6 Oct 2026 snapshot (skipped when the snapshot dir is absent)."""
import json, os, unittest
from gleichlaut import audit as A, score

H = os.environ.get("GLEICHLAUT_HIST") or os.path.expanduser("~/Desktop/hackapertus/spikes/gleichlaut/data/hist")


def vals(r, side): return sorted(x["value"] for x in r["de_only" if side == "de" else "tgt_only"])


def test_canon_separators_and_decimals():
    assert A.canon("62,5") == A.canon("62.5") == ("62.5", None)
    assert A.canon("1'000")[0] == A.canon("1 000")[0] == "1000"
    assert A.canon("2.50") == ("2.5", None) and A.canon("1.000") == ("1", "1000")
    assert A.canon("832.112.31") == ("832.112.31", None)


def test_values_bind_units_ranges_and_number_words():
    v = {(x["v"], x["unit"]) for x in A.values("15 - < 60 kg, 6% alle acht Wochen, zweimal täglich, Code 21390.03", "de")}
    assert {("15", "kg"), ("60", "kg"), ("6", "%"), ("8", "Wochen"), ("2", "täglich"), ("21390.03", None)} <= v
    assert {(x["v"], x["unit"]) for x in A.values("à 2, 4 et 6 semaines", "fr")} == {("2", "semaines"), ("4", "semaines"), ("6", "semaines")}
    assert not A.values("FEV1 und HER2", "de")                       # digits glued to letters are names


def test_swap_is_reported_with_context():
    r = A.compare("Danach alle acht Wochen 30 mg. Zuschlag von 6%.", "Poi ogni quattro settimane 30 mg. Supplemento di 12%.", "it")
    assert vals(r, "de") == ["6", "8"] and vals(r, "it") == ["12", "4"]
    assert "[acht]" in r["de_only"][0]["context"][0] or "[acht]" in r["de_only"][1]["context"][0]
    assert A.rank(r) > A.rank(A.compare("16 kg", "", "fr"))


def test_one_sided_weight_condition():
    r = A.compare("ab 6 Jahren und mit einem Körpergewicht von mindestens 16 kg", "à partir de 6 ans", "fr")
    assert vals(r, "de") == ["16"] and not r["tgt_only"]


def test_suppression_rules():
    same = lambda de, t, L: not (A.compare(de, t, L)["de_only"] or A.compare(de, t, L)["tgt_only"])
    assert same("1) Daten 2) Dosis 30 mg", "Données; dose 30 mg", "fr")                  # R1 list numbering
    assert same("ab dem 12. Lebensjahr", "à partir de 11 ans révolus", "fr")             # R4d Lebensjahr
    assert same("Behandlung während 14 Tagen", "traitement pendant 2 semaines", "fr")     # R4c unit conversion
    assert same("Gabe alle 2 Monate", "somministrazione bimestrale", "it")                # R4f period word
    assert same("Thrombozyten ≥ 150.000/μL", "plaquettes ≥ 150 000/μL", "fr")            # R4a thousands
    assert same("1 Tablette täglich", "une tablette par jour", "fr")                      # R3 value 1
    assert same("ab der 2. Linie 5 mg", "dès la deuxième ligne 5 mg", "fr")               # R4e ordinal word
    assert same("Indikationscode 21390.03 und SR 832.112.31", "code 21390.03", "fr")     # R2 unbound: counted, not reported
    assert not same("mindestens 16 kg", "au moins 61 kg", "fr")


def test_audit_item_on_the_fresh_items():
    """the old Italian Nemluvio text (wb004-it) is the one fresh item whose old target already disagrees with the German."""
    X = score.load_items("items/items_fresh.json")
    hits = {x["key"]: A.audit_item(x) for x in X if A.audit_item(x)}
    assert list(hits) == ["wb004-it"]
    assert [(f["side"], f["value"], f["unit"]) for f in hits["wb004-it"]] == [("de", "8", "Wochen")]


def test_snapshot_recall_and_counts_match_the_committed_summary():
    if not os.path.exists(os.path.join(H, "20261006-de.json")): raise unittest.SkipTest("no 20261006 snapshot in " + H)
    F, S = A.run(H, "20261006"); R = A.recall(F)
    assert all(r["all"] for r in R.values()) and len(R) == 10
    assert not any(f["id"] == A.KNOWN_BONUS for f in F)
    ref = json.load(open(os.path.join(A.DEST, "audit_20261006_summary.json"), encoding="utf-8"))
    assert len(F) == ref["findings"] and S["count_only_differences"] == ref["count_only_differences"]
