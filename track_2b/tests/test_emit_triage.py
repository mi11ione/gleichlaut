"""Flag triage (emit/triage.py): eight fixed rules sort a flagged draft's findings into "check" and "probably fine"; the
verdict, the findings and their count never change. Runs under pytest or as `python3 tests/test_emit_triage.py`."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut.emit import load, triage, xliff

_C = {}
def _views():
    if not _C: _C["V"] = {v["key"]: v for v in load("fresh166")[1]}
    return _C["V"]


def test_display_only_verdicts_and_findings_untouched():
    for v in _views().values():
        T = triage.triage(v)
        assert len(T) == len(v["findings"])
        if v["status"] != "flagged": assert not any(T)
        assert all(t in (None,) + triage.RULES for t in T)
        assert all(t is None for f, t in zip(v["findings"], T) if f["gid"] in ("corr", "record", "g3", "g4", "g6"))
        assert all(t in (None, "T5", "T8") for f, t in zip(v["findings"], T) if f["gid"] == "lock")
        assert all(t in (None, "T6", "T8") for f, t in zip(v["findings"], T) if f["gid"] == "g2")
        assert len(xliff.ordered_findings(v)) == len(v["findings"])             # reordered, never dropped


def test_each_rule_on_a_known_case():
    V = _views()
    rule = lambda k, gid: [t for f, t in zip(V[k]["findings"], triage.triage(V[k])) if f["gid"] == gid]
    assert rule("wb042-fr", "g7") == ["T1"]                                  # ophtalmochirurgiens: well-formed French
    assert "T2" in rule("wb033-fr", "slot")                                  # 'ist … zu übermitteln' -> 'doit être transmis'
    assert "T3" in rule("wb038-it", "slot")                                  # 20.20 / 20,20
    assert rule("wb010-fr", "g5") == ["T4"]                                  # ESCC
    assert rule("wb064-fr", "g7") == [None]                                  # hormonsensible ~ hormonsensitivem: check
    assert rule("wb050-fr", "lock") == ["T5"] and rule("wb051-it", "lock") == ["T5"]   # Ocrevus 944.61 -> 731.07 (German price change)
    assert rule("wb013-fr", "lock") == [None]                                # quatre -> 4: the German does not change 4
    assert rule("wb062-fr", "g2") == ["T6"]                                  # bedürfen -> bedarf
    assert rule("wb068-fr", "g2") == ["T6", "T6", "T6"]                      # erste -> erst, Zeit-punkt, Rückerstattung(en)
    assert "T6" not in rule("wb069-fr", "g2")[3:]                            # Retinsäure -> Retinoinsäure: a word change
    assert rule("wb001-fr", "g2") == [None] and rule("wb001-fr", "slot") == ["T7"]   # nicht-kleinzelligem; the removal itself: check
    assert rule("wb008-fr", "slot")[0] == "T7" and rule("wb067-fr", "slot")[0] is None    # ne … pas once; a dropped negation stays
    assert "T8" in rule("wb057-fr", "slot") and "T8" in rule("wb058-fr", "slot")      # Kyprolis 20481 ×2 vs ×1


def test_three_level_status_counts():
    V = _views().values()
    L = [triage.level(v) for v in V]
    assert L.count("ready") == sum(v["status"] == "ready" for v in V) and L.count("fine") + L.count("check") == 100
    assert L.count("fine") == 40 and L.count("check") == 60
    assert triage.level(_views()["wb050-fr"]) == "fine" and triage.level(_views()["wb067-fr"]) == "check"


def test_rule_helpers():
    assert triage.acronym("ESCC") and triage.acronym("IX") and triage.acronym("rrPMBCL") and not triage.acronym("EoÖ")
    assert not triage.acronym("Colitis")
    assert triage.well_formed("ophtalmochirurgiens", "fr", "Ophthalmochirurgen") and not triage.well_formed("Packung", "it", "")
    assert not triage.well_formed("allergie", "fr", "bei Allergie")
    O = lambda a, b: triage._orthographic(f"G2 (add): «{a}» -> «{b}»")
    assert O("Zeitpunkt", "Zeit - punkt") and O("bedürfen", "bedarf") and O("erste", "erst") and O("Strasse", "Straße") and O("A.", "a")
    assert not O("Retinsäurerezeptor", "Retinoinsäurerezeptor") and not O("vier", "acht") and not O("maximal", "minimal") and not O("", "nicht")
    assert triage._neg("bei nicht-kleinzelligem Karzinom, nicht vergütet", "de") == 1
    assert triage._neg("la personne assurée ne peut pas être remboursée", "fr") == 1


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
