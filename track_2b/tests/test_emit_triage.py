"""Flag triage (emit/triage.py): four fixed rules sort a flagged draft's findings into "check" and "probably fine"; the
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
        assert all(t is None for f, t in zip(v["findings"], T) if f["gid"] in ("corr", "record", "lock", "g2", "g3", "g4", "g6"))
        assert len(xliff.ordered_findings(v)) == len(v["findings"])             # reordered, never dropped


def test_each_rule_on_a_known_case():
    V = _views()
    rule = lambda k, gid: [t for f, t in zip(V[k]["findings"], triage.triage(V[k])) if f["gid"] == gid]
    assert rule("wb042-fr", "g7") == ["T1"]                                  # ophtalmochirurgiens: well-formed French
    assert "T2" in rule("wb033-fr", "slot")                                  # 'ist … zu übermitteln' -> 'doit être transmis'
    assert "T3" in rule("wb038-it", "slot")                                  # 20.20 / 20,20
    assert rule("wb010-fr", "g5") == ["T4"]                                  # ESCC
    assert rule("wb064-fr", "g7") == [None]                                  # hormonsensible ~ hormonsensitivem: check


def test_rule_helpers():
    assert triage.acronym("ESCC") and triage.acronym("IX") and triage.acronym("rrPMBCL") and not triage.acronym("EoÖ")
    assert not triage.acronym("Colitis")
    assert triage.well_formed("ophtalmochirurgiens", "fr", "Ophthalmochirurgen") and not triage.well_formed("Packung", "it", "")
    assert not triage.well_formed("allergie", "fr", "bei Allergie")


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
