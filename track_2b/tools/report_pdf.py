"""Render technical_report.md to TeamName_Report.pdf (A4, print CSS) with python-markdown and headless Chrome.
Development tool only.  usage: python tools/report_pdf.py [--team TeamName] [--chrome PATH]"""
import argparse, os, re, subprocess, sys, tempfile
import markdown

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CSS = """
@page { size: A4; margin: 15mm 14mm 15mm 14mm; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 8.6pt; line-height: 1.32; color: #111; }
h1 { font-size: 15pt; margin: 0 0 4pt; } h2 { font-size: 11pt; margin: 9pt 0 3pt; border-bottom: 0.5pt solid #999; }
h3 { font-size: 9.4pt; margin: 7pt 0 2pt; } p, ul { margin: 2pt 0 4pt; } li { margin: 0 0 1pt; }
table { border-collapse: collapse; width: 100%; margin: 3pt 0 6pt; font-size: 7.6pt; page-break-inside: avoid; }
th, td { border: 0.4pt solid #bbb; padding: 1.5pt 3pt; vertical-align: top; text-align: left; } th { background: #f0f0f0; }
code { font-family: Menlo, Consolas, monospace; font-size: 7.4pt; } pre { background: #f6f6f6; padding: 4pt; font-size: 6.9pt;
  line-height: 1.2; white-space: pre-wrap; page-break-inside: avoid; margin: 3pt 0 5pt; }
img { max-width: 100%; } a { color: #114; text-decoration: none; }
"""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--team", default="TeamName")
    ap.add_argument("--chrome", default="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    a = ap.parse_args()
    md = open(os.path.join(ROOT, "technical_report.md"), encoding="utf-8").read()
    html = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
    doc = f"<!doctype html><html><head><meta charset='utf-8'><title>Gleichlaut</title><style>{CSS}</style></head><body>{html}</body></html>"
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, dir=ROOT, encoding="utf-8") as f: f.write(doc); tmp = f.name
    out = os.path.join(ROOT, f"{a.team}_Report.pdf")
    try:
        subprocess.run([a.chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={out}", "file://" + tmp],
                       check=True, capture_output=True, timeout=120)
    finally:
        os.unlink(tmp)
    pages = len(re.findall(rb"/Type\s*/Page[^s]", open(out, "rb").read()))
    print(out, pages, "pages")
    if pages > 6: print("WARNING: more than 6 pages"); sys.exit(1)


if __name__ == "__main__":
    main()
