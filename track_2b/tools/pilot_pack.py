"""Pilotpaket Phase 1, Variante A: eine ZIP-Datei mit Prüfsummen, reproduzierbar (gleicher Commit -> gleiche Bytes).

  python3 tools/pilot_pack.py              prüft Fallblätter und PDFs auf Aktualität, baut das Register offline und schreibt
                                           dist/gleichlaut-pilot-phase1-<SL-Stand>.zip und .zip.sha256 (dist/ ist
                                           gitignoriert; die ZIP-Datei wird nicht eingecheckt)
  python3 tools/pilot_pack.py --out DIR    schreibt nach DIR

Inhalt (Pfade wie in docs/pilot/, damit die Links der Dokumente gelten):
  Entscheidvorlage_Phase1.md, Management_Notiz.md, Projektauftrag_Phase1.md, Schutzbedarfsanalyse_Phase1.md
  fallblaetter/*.md                        die Fallblätter (tools/pilot_sheets.py) mit Übersicht
  pdf/*.pdf                                Entscheidvorlage, Management-Notiz und Fallblätter als PDF (tools/pilot_pdf.py)
  register/gleichlaut-register.html        das Register als eine Datei, offline lesbar (ohne Netz, ohne Server)
  SHA256SUMS                               sha256 jeder Datei im Paket (`shasum -a 256 -c SHA256SUMS` im entpackten Ordner)
Reproduzierbar: feste Reihenfolge, fester Zeitstempel (Commit-Zeit von HEAD, sonst 1980-01-01), feste Rechte, feste
Kompression. Keine Modellaufrufe, kein Netz."""
import glob, hashlib, io, os, subprocess, sys, zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
PILOT = os.path.join(ROOT, "docs", "pilot")
DOCS = ("Entscheidvorlage_Phase1.md", "Management_Notiz.md", "Projektauftrag_Phase1.md", "Schutzbedarfsanalyse_Phase1.md")


def stamp():
    """The zip entries' time: the commit time of HEAD (UTC), else 1980-01-01 (the earliest a zip can store)."""
    try:
        t = int(subprocess.run(["git", "log", "-1", "--format=%ct"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip())
        import time; return max(time.gmtime(t)[:6], (1980, 1, 1, 0, 0, 0))
    except Exception:
        return (1980, 1, 1, 0, 0, 0)


def files():
    """{path in the pack: bytes}"""
    import pilot_pdf, pilot_sheets
    from gleichlaut.ui import audit_view, build
    if pilot_sheets.main(["--check"]) != 0: sys.exit("pilot_pack: docs/pilot/fallblaetter/ is not current (python3 tools/pilot_sheets.py)")
    if pilot_pdf.main(["--check"]) != 0: sys.exit("pilot_pack: docs/pilot/pdf/ is not current (make pilot-pdf)")
    F = {}
    for d in DOCS: F[d] = open(os.path.join(PILOT, d), "rb").read()
    for p in sorted(glob.glob(os.path.join(PILOT, "fallblaetter", "*.md"))): F["fallblaetter/" + os.path.basename(p)] = open(p, "rb").read()
    for p in sorted(glob.glob(os.path.join(PILOT, "pdf", "*.pdf"))): F["pdf/" + os.path.basename(p)] = open(p, "rb").read()
    import tempfile
    with tempfile.TemporaryDirectory(prefix="gl-pack-") as t:
        out = os.path.join(t, "register.html")
        build.build(out=out, hist=None)                  # the bundled audit texts, as the published page: no snapshot files needed
        F["register/gleichlaut-register.html"] = open(out, "rb").read()
    F["SHA256SUMS"] = "".join(f"{hashlib.sha256(b).hexdigest()}  {k}\n" for k, b in sorted(F.items())).encode()
    return F


def pack(F, name):
    buf = io.BytesIO(); ts = stamp()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for k in ["SHA256SUMS"] + sorted(x for x in F if x != "SHA256SUMS"):
            zi = zipfile.ZipInfo(f"{name}/{k}", date_time=ts); zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16; zi.create_system = 3
            z.writestr(zi, F[k], compresslevel=9)
    return buf.getvalue()


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    out = a[a.index("--out") + 1] if "--out" in a else os.path.join(ROOT, "dist")
    from gleichlaut.ui import audit_view
    import json
    date = json.load(open(audit_view.AUDIT, encoding="utf-8")).get("summary", {}).get("date") or "audit"
    name = f"gleichlaut-pilot-phase1-{date}"
    F = files(); z = pack(F, name)
    os.makedirs(out, exist_ok=True); p = os.path.join(out, name + ".zip")
    open(p, "wb").write(z)
    h = hashlib.sha256(z).hexdigest()
    open(p + ".sha256", "w", encoding="utf-8").write(f"{h}  {name}.zip\n")
    print(f"{os.path.relpath(p, ROOT)}: {len(F)} files, {len(z) // 1024} KB, sha256 {h}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
