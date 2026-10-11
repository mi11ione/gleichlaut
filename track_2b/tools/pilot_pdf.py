"""Pilot Phase 1 als PDF: jedes Fallblatt (docs/pilot/fallblaetter/*.md), die Management-Notiz und die Entscheidvorlage
als A4-PDF nach docs/pilot/pdf/ (python-markdown und Headless-Chrome-Druck, wie tools/report_pdf.py; nüchternes
Druck-CSS). Keine Modellaufrufe, kein Netz.

  python3 tools/pilot_pdf.py            rendert alle PDFs und schreibt docs/pilot/pdf/SOURCES.sha256
                                        (braucht python-markdown und Chrome/Chromium; CHROME=Pfad wählt den Browser)
  python3 tools/pilot_pdf.py --check    prüft ohne Browser und ohne python-markdown, dass die PDFs aktuell sind:
                                        jede Quelle hat ein PDF, der Hash von Quelle + Druck-CSS entspricht dem beim
                                        Rendern festgehaltenen, und jedes PDF ist das damals erzeugte (exit 1 sonst)

SOURCES.sha256, eine Zeile je PDF: sha256(Quelle + CSS + Renderer-Version), sha256(PDF), PDF-Name, Quelle. Chrome schreibt
Erstellungsdaten ins PDF, deshalb prüft --check die Quelle (nicht ein Byte-Vergleich eines neuen Drucks)."""
import glob, hashlib, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PILOT = os.path.join(ROOT, "docs", "pilot")
OUT = os.path.join(PILOT, "pdf")
MANIFEST = "SOURCES.sha256"
VERSION = "pilot_pdf 1"                         # change when the rendering changes in a way the CSS does not show
ONE_PAGE = ("Entscheidvorlage_Phase1.md",)      # must fit on one A4 page
CSS = """
@page { size: A4; margin: 16mm 16mm 16mm 18mm; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9pt; line-height: 1.36; color: #111; }
h1 { font-size: 13.5pt; font-weight: 600; margin: 0 0 6pt; padding-bottom: 4pt; border-bottom: 1pt solid #111; }
h2 { font-size: 10.5pt; font-weight: 600; margin: 10pt 0 3pt; } h3 { font-size: 9.4pt; font-weight: 600; margin: 8pt 0 2pt; }
p, ul, ol { margin: 2pt 0 5pt; } li { margin: 0 0 1.5pt; } ul, ol { padding-left: 14pt; }
table { border-collapse: collapse; width: 100%; margin: 3pt 0 7pt; font-size: 8.2pt; }
tr { page-break-inside: avoid; }
th, td { border-top: 0.4pt solid #999; border-bottom: 0.4pt solid #999; padding: 2pt 4pt 2pt 0; vertical-align: top; text-align: left; }
th { font-weight: 600; border-top: 0.8pt solid #111; } td:first-child { padding-right: 8pt; }
code { font-family: Menlo, Consolas, "DejaVu Sans Mono", monospace; font-size: 7.8pt; overflow-wrap: anywhere; }
blockquote { margin: 4pt 0 6pt; padding: 3pt 0 3pt 8pt; border-left: 2pt solid #111; }
a { color: #111; text-decoration: none; } strong { font-weight: 600; }
"""


def sources():
    """[(Quelle relativ zu ROOT, PDF-Name)]: Entscheidvorlage, Management-Notiz, dann die Fallblätter."""
    S = [os.path.join(PILOT, "Entscheidvorlage_Phase1.md"), os.path.join(PILOT, "Management_Notiz.md")]
    S += sorted(glob.glob(os.path.join(PILOT, "fallblaetter", "*.md")))
    return [(os.path.relpath(p, ROOT), os.path.splitext(os.path.basename(p))[0] + ".pdf") for p in S]


def src_hash(rel):
    h = hashlib.sha256(open(os.path.join(ROOT, rel), "rb").read())
    h.update(b"\0" + CSS.encode() + b"\0" + VERSION.encode())
    return h.hexdigest()


def file_hash(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


def links(html, rel, pdfs):
    """Relative Links auf eine gerenderte Quelle zeigen auf deren PDF (alle PDFs liegen nebeneinander); andere relative
    Links werden zu Text (im PDF gäbe es das Ziel nicht); http(s)-Links bleiben."""
    base = os.path.dirname(rel)
    def fix(m):
        href, text = m.group(1), m.group(2)
        if re.match(r"https?://", href): return m.group(0)
        tgt = os.path.normpath(os.path.join(base, href.split("#")[0]))
        return f'<a href="{pdfs[tgt]}">{text}</a>' if tgt in pdfs else text
    return re.sub(r'<a href="([^"]+)">(.*?)</a>', fix, html, flags=re.S)


def chrome():
    for c in (os.environ.get("CHROME", ""), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        if c and (os.path.exists(c) or shutil.which(c)): return c if os.path.exists(c) else shutil.which(c)
    sys.exit("pilot_pdf: no Chrome / Chromium found (set CHROME=path)")


def pages(p): return len(re.findall(rb"/Type\s*/Page[^s]", open(p, "rb").read()))


def render():
    import markdown                                   # only for rendering; --check needs the standard library only
    ch = chrome(); S = sources(); pdfs = dict(S); os.makedirs(OUT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="gl-pilot-pdf-"); lines = []
    try:
        for rel, name in S:
            md = open(os.path.join(ROOT, rel), encoding="utf-8").read()
            title = (re.search(r"^# (.+)$", md, re.M) or [None, name[:-4]])[1]
            body = links(markdown.markdown(md, extensions=["tables", "sane_lists"]), rel, pdfs)
            doc = (f"<!doctype html><html lang='de-CH'><head><meta charset='utf-8'><title>{title}</title><style>{CSS}</style>"
                   f"</head><body>{body}</body></html>")
            h = os.path.join(tmp, name[:-4] + ".html"); open(h, "w", encoding="utf-8").write(doc)
            out = os.path.join(OUT, name)
            subprocess.run([ch, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={tmp}/prof",
                            f"--print-to-pdf={out}", "file://" + h], check=True, capture_output=True, timeout=120)
            n = pages(out)
            if os.path.basename(rel) in ONE_PAGE and n != 1: sys.exit(f"pilot_pdf: {rel} needs {n} pages, must fit on one")
            lines.append(f"{src_hash(rel)}  {file_hash(out)}  {name}  {rel}")
            print(f"{name}: {n} page{'s' if n != 1 else ''}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    keep = {n for _, n in S}
    for f in os.listdir(OUT):
        if f.endswith(".pdf") and f not in keep: os.remove(os.path.join(OUT, f))
    open(os.path.join(OUT, MANIFEST), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"{len(lines)} PDFs -> {os.path.relpath(OUT, ROOT)}")


def check():
    """-> [Abweichung] (leer: aktuell)."""
    p = os.path.join(OUT, MANIFEST)
    if not os.path.exists(p): return [f"{os.path.relpath(p, ROOT)} missing"]
    M = {}
    for l in open(p, encoding="utf-8").read().splitlines():
        if l.strip():
            sh, ph, name, rel = l.split("  ", 3); M[name] = (sh, ph, rel)
    bad = []
    S = sources()
    for rel, name in S:
        pdf = os.path.join(OUT, name)
        if name not in M or M[name][2] != rel: bad.append(f"{name}: not rendered from {rel}"); continue
        if M[name][0] != src_hash(rel): bad.append(f"{name}: {rel} changed since rendering")
        if not os.path.exists(pdf): bad.append(f"{name}: missing")
        elif file_hash(pdf) != M[name][1]: bad.append(f"{name}: PDF differs from the rendered one")
    extra = sorted(set(f for f in os.listdir(OUT) if f.endswith(".pdf")) - {n for _, n in S})
    bad += [f"{f}: no source" for f in extra] + [f"{n}: in {MANIFEST} but no source" for n in sorted(set(M) - {n for _, n in S})]
    return bad


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    if "--check" in a:
        bad = check()
        if bad: print("pilot PDFs not current (python3 tools/pilot_pdf.py re-renders them):\n  " + "\n  ".join(bad)); return 1
        print(f"ok: {len(sources())} PDFs current"); return 0
    render(); return 0


if __name__ == "__main__":
    sys.exit(main())
