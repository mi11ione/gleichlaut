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
    """old Italian Nemluvio (wb004-it) disagrees on a number; old 'Italian' Myoview (wb079-it) is French. No other fresh
    item has a number, unit or language finding in its old texts."""
    X = score.load_items("items/items_fresh.json")
    hits = {x["key"]: A.audit_item(x) for x in X if A.audit_item(x)}
    div = {k: v for k, v in hits.items() if any(f["kind"] in ("number", "unit", "language") for f in v)}
    assert sorted(div) == ["wb004-it", "wb079-it"]
    assert [(f["side"], f["value"], f["unit"]) for f in hits["wb004-it"] if f["kind"] == "number"] == [("de", "8", "Wochen")]
    lg = [f for f in hits["wb079-it"] if f["kind"] == "language"]
    assert len(lg) == 1 and lg[0]["detected"] == "fr" and lg[0]["odd_one_out"] == "it" and "French" in lg[0]["detail"]


def test_audit_item_shape_is_backwards_compatible():
    """round-2 keys (side, value, unit, context) stay on number findings; every finding has kind, lang and an English detail."""
    x = dict(key="k-fr", lang="fr", de_old="Danach alle acht Wochen. Senkung um 1 .4 mmol/l nach 3 Wochen.",
             tgt_old="Ensuite toutes les quatre semaines. Réduction de 1,4 mmol/l après 3 mois.")
    r = A.audit_item(x)
    assert [f["kind"] for f in r] == ["number", "unit", "editorial"]   # FR 'quatre' = the '4' of DE '1 .4': no number finding
    for f in r: assert f["kind"] in ("number", "unit", "language", "editorial") and f["lang"] and f["detail"].endswith(".")
    n = r[0]; assert {"side", "value", "unit", "context", "values"} <= set(n)
    u = r[1]; assert u["side"] == "fr" and u["values"] == ["3"] and "weeks" in u["detail"] and "months" in u["detail"]
    e = r[2]; assert e["lang"] == "de" and e["surface"] == "1 .4" and e["suggestion"] == "1.4"
    assert A.audit_item(x, kinds=("number",)) == r[:1]


def test_language_check():
    st = A.load_stats()
    if st is None: raise unittest.SkipTest("no shipped register statistics " + A.STATS)
    fr = ("Monothérapie du carcinome urothélial localement avancé ou métastatique chez les adultes ayant été prétraités "
          "par chimiothérapie à base de platine au cours des 24 derniers mois.")
    it = ("Monoterapia del carcinoma uroteliale localmente avanzato o metastatico negli adulti che sono stati pretrattati "
          "con chemioterapia a base di platino entro gli ultimi 24 mesi.")
    assert A.lang_check(fr, "it", st=st)["detected"] == "fr"
    assert A.lang_check(it, "it", st=st)["detected"] == "it" and A.lang_check(fr, "fr", st=st)["detected"] == "fr"
    assert A.lang_check(it, "fr", st=st)["detected"] == "it"
    assert not A.lang_check("Keytruda KN045 200 mg", "it", st=st)["judged"]             # short: names and codes only
    assert A.lang_check(fr, "it", st=None)["detected"] == "it"                          # no profile: B cannot confirm
    assert not (A.FW["fr"] & A.FW["it"]) and "la" not in A.FW["fr"] and "la" not in A.FW["it"]


def test_unit_check():
    assert [(u["value"], u["de"], u["tgt"]) for u in A.unit_diff("nach 4 Wochen", "après 4 mois", "fr")] == [("4", "w", "m")]
    assert [(u["value"], u["de"], u["tgt"]) for u in A.unit_diff("ab 15 kg", "da 15 mg", "it")] == [("15", "kg", "mg")]
    assert not A.unit_diff("nach 4 Wochen", "après 4 semaines", "fr")
    assert not A.unit_diff("4 Wochen und 4 Monate", "4 semaines et 4 mois", "fr")
    assert not A.unit_diff("6 Monate und 6 Wochen", "6 mois", "fr")                     # one direction only: not a finding
    assert A.unit_one_sided("6 Monate und 6 Wochen", "6 mois", "fr")
    assert not A.unit_diff("ab dem 12. Lebensjahr, 12 Monate", "dès 12 ans, 12 mois", "fr")
    assert not A.unit_diff("15 kg", "15 %", "fr")                                       # different dimensions


def test_editorial_rules():
    ed = lambda t, L, st=None: [(e["rule"], e["surface"], e["suggestion"]) for e in A.editorial(t, L, st)]
    assert ed("LDL-C kleiner 1 .4 mmol/l", "de") == [("E1", "1 .4", "1.4")]
    assert ed("patients pesant moins de15 kg", "fr") == [("E2", "de15", "de 15")]
    assert ed("nach 4Wochen", "de") == [("E3", "4Wochen", "4 Wochen")]
    assert not ed("1.4 mmol/l, 15 kg, FEV1 80 %, HER2, Code 21390.03, Punkte 1 ,2 und 3", "de")
    st = dict(utri={"it": {"almeno sei mesi": 6, "almeno se mesi": 1}}, after={"it": {"mesi": 40, "settimane": 30}},
              _vocab={"it": {"almeno", "mesi", "mese"}})
    assert ed("terapia di almeno se mesi", "it", st) == [("E4", "se mesi", "sei mesi")]
    assert ed("dopo 6 mese", "it", st) == [] and ed("dopo 6 mesu", "it", st) == [("E5", "6 mesu", "6 mesi")]
    st["utri"]["it"]["almeno sei mesi"] = 4                                                # under the a-priori 5: silent
    assert ed("terapia di almeno se mesi", "it", st) == []


def test_lev1():
    assert A.lev1("se", "sei") and A.lev1("monte", "monate") and A.lev1("dei", "sei")
    assert not A.lev1("ab", "ba") and not A.lev1("sei", "sei") and not A.lev1("des", "deux")


def test_snapshot_recall_and_counts_match_the_committed_summary():
    if not os.path.exists(os.path.join(H, "20261006-de.json")): raise unittest.SkipTest("no 20261006 snapshot in " + H)
    F, S, X = A.run_all(H, "20261006")
    N = [f for f in F if f["kind"] == "number"]; R = A.recall(N)
    assert all(r["all"] for r in R.values()) and len(R) == 10
    ref = json.load(open(os.path.join(A.DEST, "audit_20261006_summary.json"), encoding="utf-8"))
    assert len(N) == ref["findings"] and S["count_only_differences"] == ref["count_only_differences"]
    assert {k: sum(f["kind"] == k for f in F) for k in ref["by_kind"]} == ref["by_kind"]
    kt = [f for f in F if f["id"] == A.KNOWN_BONUS]
    assert [(f["kind"], f["lang"], f["detected"], f["identical_to"]) for f in kt] == [("language", "it", "fr", ["fr"])]
    com = json.load(open(os.path.join(A.DEST, "audit_20261006.json"), encoding="utf-8"))["findings"]
    assert [(f["id"], f["lang"], f["rank"]) for f in N] == [(f["id"], f["lang"], f["rank"]) for f in com if f["kind"] == "number"]
    for f in F: assert f["suggested_action"] is None and f["context"] and f["fid"]
