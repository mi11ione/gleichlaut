"""The review page in a real browser (headless Chrome; skipped when no Chrome/Chromium is installed): the page script
runs without error, #audit opens the Register audit tab, a hash naming a draft opens the Drafts tab, the interface
defaults to the browser language (else German), decisions import, and the page's own XLIFF 2.1 export (with an
accepted-edited and a sent-back decision) validates against the XLIFF 2.1 core XSD + constraints.
Runs under pytest or as `python3 tests/test_ui_browser.py`."""
import html, json, os, re, shutil, subprocess, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut.emit import validate
from gleichlaut.ui import build

CANDIDATES = [os.environ.get("CHROME", ""), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
_C = {}


def _chrome():
    for c in CANDIDATES:
        if c and (os.path.exists(c) or shutil.which(c)): return c if os.path.exists(c) else shutil.which(c)
    raise unittest.SkipTest("no Chrome / Chromium for the browser test")


def _page():
    if "p" not in _C:
        d = tempfile.mkdtemp(prefix="gl-ui-br-"); p = os.path.join(d, "index.html"); _, D = build.build(out=p)
        _C.update(p=p, d=d, D=D)
    return _C


def _dom(path, hash_="", lang="en", probe=""):
    ch = _chrome(); prof = tempfile.mkdtemp(prefix="gl-prof-")
    if probe:
        s = open(path, encoding="utf-8").read()
        s = s.replace("</body>", "<script>" + probe + "</script></body>"); path = path[:-5] + "-probe.html"
        open(path, "w", encoding="utf-8").write(s)
    try:
        r = subprocess.run([ch, "--headless=new", "--disable-gpu", "--no-first-run"] + (["--no-sandbox"] if hasattr(os, "geteuid") and os.geteuid() == 0 else []) + [ f"--user-data-dir={prof}", f"--accept-lang={lang}",
                            "--virtual-time-budget=5000", "--dump-dom", "file://" + path + hash_], capture_output=True, text=True, timeout=120)
    finally:
        shutil.rmtree(prof, ignore_errors=True)
    return r.stdout


ERR = "window.__err=[];window.addEventListener('error',function(e){window.__err.push(String(e.message))});"


def test_audit_tab_opens_with_hash_and_german_default():
    C = _page(); s = _dom(C["p"], "#audit", "de-CH,de")
    assert re.search(r'id="t-audit"[^>]*aria-selected="true"', s) and re.search(r'id="p-audit"[^>]*role="tabpanel"(?![^>]*hidden)', s)
    assert len(re.findall(r'<tr data-rid="[0-9a-f]{10}"', s)) == len(C["D"]["audit"]["rows"]) and "Registerprüfung" in s and 'lang="de"' in s


def test_draft_hash_opens_drafts_and_unknown_language_falls_back_to_german():
    C = _page(); g = C["D"]["groups"][3]
    s = _dom(C["p"], "#" + g["pair"], "ja-JP")
    assert re.search(r'id="t-drafts"[^>]*aria-selected="true"', s) and 'id="p-audit"' in s
    assert "Entwürfe" in s and html.escape(g["product"], quote=False) in s and "Text kopieren" in s


def test_page_xliff_export_validates():
    C = _page(); D = C["D"]
    fl = next(it for g in D["groups"] for it in g["items"].values() if it["status"] == "flagged" and it["lang"] == "fr")
    rd = next(it for g in D["groups"] for it in g["items"].values() if it["status"] == "ready" and it["lang"] == "fr")
    dec = {"run_sha256": D["meta"]["run_sha256"], "decisions": {
        fl["key"]: {"decision": "accept-edited", "text": "Texte révisé : 5 mg.", "reason": "Wording", "note": "ok", "at": "2026-10-09T10:00:00Z"},
        rd["key"]: {"decision": "send-back", "reason": "Other", "note": "", "at": "2026-10-09T10:01:00Z"}}}
    probe = ERR + ("setTimeout(function(){var R=window.GleichlautReview,m=R.importDecisions(" + json.dumps(dec) + ");"
                   "var p=document.createElement('pre');p.id='out-fr';p.textContent=R.xliff('fr');document.body.appendChild(p);"
                   "var q=document.createElement('pre');q.id='out-it';q.textContent=R.xliff('it');document.body.appendChild(q);"
                   "var e=document.createElement('pre');e.id='out-msg';e.textContent=m+' | '+window.__err.join(';');document.body.appendChild(e)},300);")
    s = _dom(C["p"], "", "en", probe)
    msg = html.unescape(re.search(r'<pre id="out-msg">(.*?)</pre>', s, re.S).group(1))
    assert msg.startswith("Imported 2 draft decisions") and msg.endswith("| "), msg
    for L in ("fr", "it"):
        x = html.unescape(re.search(rf'<pre id="out-{L}">(.*?)</pre>', s, re.S).group(1))
        p = os.path.join(C["d"], f"page-{L}.xlf"); open(p, "w", encoding="utf-8").write(x)
        assert validate.validate_xliff(p) == [], (L, validate.validate_xliff(p)[:5])
        assert 'type="gleichlaut:changed"' in x and 'subState="gleichlaut:flagged"' not in x.replace('state="translated" subState="gleichlaut:flagged"', "")
        if L == "fr":
            assert 'state="reviewed" subState="gleichlaut:accepted-edited"' in x and "Texte révisé : 5 mg." in x
            assert 'state="initial" subState="gleichlaut:sent-back"' in x and "Révision : accepté modifié" in x


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
