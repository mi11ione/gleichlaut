"""Pilot pack (docs/pilot): tools/pilot_sheets.py runs, writes one Fallblatt per register issue plus one per confirmed
experimental finding and an overview (the answers are the register's own: tests/test_excerpts.py), and the committed
sheets equal what it generates."""
import os, re, subprocess, sys, tempfile
from gleichlaut.ui import audit_view as av

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TOOL = os.path.join(ROOT, "tools", "pilot_sheets.py")


def test_one_sheet_per_issue():
    D = av.data(hist=None)
    with tempfile.TemporaryDirectory() as t:
        r = subprocess.run([sys.executable, TOOL, "--out", t], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-2000:]
        got = sorted(f for f in os.listdir(t) if f.startswith("FB-"))
        reg = [f for f in got if re.match(r"FB-\d\d_", f)]; exp = [f for f in got if f.startswith("FB-X")]
        assert len(reg) == len(D["issues"]) and len(exp) == D["exp"]["confirmed"], (len(reg), len(exp))
        assert "00_Uebersicht.md" in os.listdir(t)
        for f in got:
            s = open(os.path.join(t, f), encoding="utf-8").read()
            for field in ("Sprache der Verfügung | aus dem Dossier", "| Welcher Text ist falsch? |", "| Was ist zu tun? |", "| Visum", "sl.bag.admin.ch/sl",
                          "| Weicht von den beiden anderen ab |"):
                assert field in s, (f, field)
            assert ("experimentelle Prüfung, standardmässig aus" in s) == f.startswith("FB-X"), f


def test_committed_sheets_are_current():
    r = subprocess.run([sys.executable, TOOL, "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
