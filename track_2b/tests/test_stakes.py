"""CHF at stake per patient (tools/stakes.py): the committed result re-derives from the committed prices and texts, the
formulas hold on the published prices, every figure rests on a blind-confirmed finding and on phrases the published texts
contain, and no population or national total appears. No snapshot or network needed."""
import importlib.util, json, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
spec = importlib.util.spec_from_file_location("stakes", os.path.join(ROOT, "tools", "stakes.py"))
S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
R = S.compute()
CASES = {c["id"]: c for c in R["cases"]}


def test_committed_result_rederives():
    assert json.loads(json.dumps(R, sort_keys=True)) == json.load(open(S.OUT, encoding="utf-8"))


def test_prices_file_names_the_public_feed():
    P = json.load(open(S.PRICES, encoding="utf-8"))
    assert P["source"].startswith("https://epl.bag.admin.ch/") and len(P["source_sha256"]) == 64
    assert all(p["public_price"] and p["ex_factory_price"] for p in P["packs"])


def test_formulas_on_published_prices():
    n = CASES["nemluvio"]
    assert n["extra_doses_per_year"] == 52 / 4 - 52 / 8 == 6.5
    assert abs(n["chf_per_patient_year"] - 6.5 * n["pack"]["public_price"]) < 0.01
    for r in CASES["diaphin"]["packs"]:
        assert abs(r["public_price"] - r["ex_factory_price"] * 1.06 * 1.026) < 0.06           # published price follows the 6 %
        assert abs(r["chf_difference_per_pack"] - r["public_price"] * 0.06 / 1.06) < 0.01
    a = CASES["amvuttra"]
    assert abs(a["chf_per_patient_year"] - 4 * a["chf_per_dose"]) < 0.01
    d = CASES["dupixent"]
    assert abs(d["atopic_dermatitis"]["chf_difference"] - (26 * d["chf_per_200mg"] - 13 * d["chf_per_300mg"])) < 0.05


def test_every_case_rests_on_a_confirmed_finding():
    for c in R["cases"]:
        conf = c.get("confirmed") or [p["confirmed"] for p in c.get("products", [])]
        for x in conf if isinstance(conf, list) else [conf]:
            assert x["label"] == "real", (c["id"], x)


def test_missing_phrase_raises():
    T = json.load(open(S.TEXTS, encoding="utf-8"))["texts"]
    try:
        S.quote(T, "NEMLUVIO.01", "it", "ogni otto settimane")
    except AssertionError:
        return
    raise AssertionError("quote() accepted a phrase the Italian text does not contain")


def test_per_patient_only():
    assert "per patient only" in R["scope"]
    s = json.dumps(R).lower()
    assert "patients per year" not in s and "national total" not in s.replace("no population or national total", "")
