"""Pilot pack (docs/pilot): tools/pilot_sheets.py runs, writes one Fallblatt per register issue plus one per confirmed
experimental finding and an overview (the answers are the register's own: tests/test_excerpts.py), and the committed
sheets equal what it generates; the PDFs (tools/pilot_pdf.py) are current, the one-page Entscheidvorlage cites only bases
docs/sl-process.md states, and `make pilot-pack` (tools/pilot_pack.py) builds the same checksummed zip twice."""
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


def test_pdfs_are_current_and_the_memo_fits_one_page():
    """docs/pilot/pdf/: one PDF per Fallblatt plus the Entscheidvorlage and the Management-Notiz, rendered from the current
    sources (tools/pilot_pdf.py --check: source hash and PDF hash as recorded in SOURCES.sha256); the memo is one page."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import pilot_pdf
    assert pilot_pdf.check() == [], pilot_pdf.check()
    names = {n for _, n in pilot_pdf.sources()}
    assert {"Entscheidvorlage_Phase1.pdf", "Management_Notiz.pdf", "00_Uebersicht.pdf"} <= names and len(names) == 27
    assert pilot_pdf.pages(os.path.join(pilot_pdf.OUT, "Entscheidvorlage_Phase1.pdf")) == 1


def test_decision_memo_states_only_sourced_bases():
    """The Entscheidvorlage: phase 1 only, the three numbers from the results files, drafting only as an annex line, and
    every 'who signs' left to the legal service (no legal basis that docs/sl-process.md does not state)."""
    import json
    s = open(os.path.join(ROOT, "docs", "pilot", "Entscheidvorlage_Phase1.md"), encoding="utf-8").read()
    G = json.load(open(os.path.join(ROOT, "eval", "results", "audit_grouping.json"), encoding="utf-8"))["reconciliation"]
    assert f"**{G['issues']} Sachverhalte**" in s and f"aus {G['rows']} Befunden" in s
    assert f"**{G['register']['real']} bestätigte Befunde, die eine Bedingung ändern**" in s
    assert "keine Beschaffung" in s and "*Annahme*" in s and "3–6 h" in s
    rows = [l for l in s.splitlines() if l.startswith("| ") and "durch den Rechtsdienst zu bestätigen |" in l]
    assert len(rows) == 5 and all(l.split("|")[2].strip() == "durch den Rechtsdienst zu bestätigen" for l in rows)
    sl = open(os.path.join(ROOT, "docs", "sl-process.md"), encoding="utf-8").read()
    for art in re.findall(r"(?:KVV|KLV) Art\. \d+\w*", s) + re.findall(r"Art\. \d+\w* Abs\. \d+ (?:KVV|KLV)", s):
        assert art in sl, art                                         # every article cited is in sl-process.md
    assert s.count("Apertus") == 1 and "Anhang (nicht Gegenstand dieses Antrags)" in s


def test_pack_is_reproducible_and_checksummed():
    import hashlib, zipfile
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        for d in (a, b):
            r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "pilot_pack.py"), "--out", d], capture_output=True, text=True)
            assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
        za, zb = (sorted(f for f in os.listdir(d) if f.endswith(".zip")) for d in (a, b))
        assert za == zb == ["gleichlaut-pilot-phase1-20261006.zip"]
        A, B = (open(os.path.join(d, za[0]), "rb").read() for d in (a, b))
        assert A == B
        z = zipfile.ZipFile(os.path.join(a, za[0])); top = "gleichlaut-pilot-phase1-20261006/"
        sums = dict(l.split("  ")[::-1] for l in z.read(top + "SHA256SUMS").decode().splitlines())
        names = {n[len(top):] for n in z.namelist()} - {"SHA256SUMS"}
        assert names == set(sums) and all(hashlib.sha256(z.read(top + n)).hexdigest() == sums[n] for n in names)
        for need in ("Entscheidvorlage_Phase1.md", "pdf/Entscheidvorlage_Phase1.pdf", "Management_Notiz.md", "Projektauftrag_Phase1.md",
                     "Schutzbedarfsanalyse_Phase1.md", "fallblaetter/FB-01_Diaphin.md", "pdf/FB-01_Diaphin.pdf", "register/gleichlaut-register.html"):
            assert need in names, need
        assert open(os.path.join(a, za[0] + ".sha256")).read().split()[0] == hashlib.sha256(A).hexdigest()
