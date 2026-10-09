"""The review page in a real browser (headless Chrome; skipped when no Chrome/Chromium is installed): the page script
runs without error, the page lands on the Register audit tab (also with #audit), #drafts or a hash naming a draft opens
the Drafts tab, the interface defaults to the browser language (else German), decisions import, the family action
accepts after an in-page confirmation, "start from the old text" replaces the editable draft, and the page's own XLIFF
2.1 and 1.2 exports (with an accepted-edited and a sent-back decision) validate against the 2.1 core XSD + constraints
and the 1.2 strict XSD.
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
    R = C["D"]["audit"]["rows"]; eq = [r for r in R if r["eq"] is not None and not r["known"]]
    assert len(re.findall(r'<tr data-sig="[A-Za-z0-9]', s)) == len(R) - len(eq) and "Registerprüfung" in s and 'lang="de"' in s
    if eq: assert f"Wahrscheinlich gleichwertige Formulierung ({len(eq)})" in s          # collapsed, counted, never dropped
    assert "Von Amtes wegen in der nächsten Publikation berichtigen" in s and ">GÄL<" not in s


def test_landing_is_the_audit_tab_unless_drafts_is_asked_for():
    C = _page()
    s = _dom(C["p"], "", "fr-CH,fr")
    assert re.search(r'id="t-audit"[^>]*aria-selected="true"', s) and "Audit du registre" in s
    s = _dom(C["p"], "#drafts", "it-CH")
    assert re.search(r'id="t-drafts"[^>]*aria-selected="true"', s) and "Bozze" in s and re.search(r'<tr data-pair="[^"]+" aria-selected="true"', s)


def test_three_levels_family_accept_and_start_from_old_text():
    C = _page(); D = C["D"]
    fam = next(f[0] for f in D["families"] if sum(1 for g in D["groups"] if g["family"] == f[0]
                                                   for it in g["items"].values() if it["status"] == "ready" and not it["old"]) >= 2)
    fl = next(it for g in D["groups"] for it in g["items"].values() if it.get("rt") and it["rt"][1] > 0)
    probe = ERR + ("setTimeout(function(){var R=window.GleichlautReview,f=document.getElementById('f-fam');f.value=" + json.dumps(fam) + ";f.onchange();"
                   "var q1=document.getElementById('fam-bulk').textContent;document.getElementById('fam-go').click();var q2=document.getElementById('fam-bulk').textContent;"
                   "document.getElementById('fam-yes').click();var n=Object.keys(R.payload().decisions).length;"
                   "location.hash='#" + fl["key"][:-3] + "';setTimeout(function(){var b=document.querySelector('[data-start=\"" + fl["key"] + "\"]');if(b)b.click();"
                   "var e=document.createElement('pre');e.id='out';e.textContent=JSON.stringify({q1:q1,q2:q2,n:n,ed:R.payload().edits[" + json.dumps(fl["key"]) + "]||null,"
                   "marks:document.querySelectorAll('#reg .mk.f').length,b:!!b,err:window.__err});document.body.appendChild(e)},300)},300);")
    s = _dom(C["p"], "#drafts", "en", probe)
    o = json.loads(html.unescape(re.search(r'<pre id="out">(.*?)</pre>', s, re.S).group(1)))
    assert not o["err"], o["err"]
    assert o["q1"].startswith("Accept all ready drafts of this edit family") and "Confirm accept" in o["q2"] and o["n"] >= 2
    assert o["ed"] and o["ed"] != next(it for g in D["groups"] for it in g["items"].values() if it["key"] == fl["key"]).get("draft")


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
                   "['fr','it'].forEach(function(L){var z=document.createElement('pre');z.id='out12-'+L;z.textContent=R.xliff12(L);document.body.appendChild(z)});"
                   "var e=document.createElement('pre');e.id='out-msg';e.textContent=m+' | '+window.__err.join(';');document.body.appendChild(e)},300);")
    s = _dom(C["p"], "", "en", probe)
    msg = html.unescape(re.search(r'<pre id="out-msg">(.*?)</pre>', s, re.S).group(1))
    assert msg.startswith("Imported 2 draft decisions") and msg.endswith("| "), msg
    for L in ("fr", "it"):
        x = html.unescape(re.search(rf'<pre id="out-{L}">(.*?)</pre>', s, re.S).group(1))
        p = os.path.join(C["d"], f"page-{L}.xlf"); open(p, "w", encoding="utf-8").write(x)
        assert validate.validate_xliff(p) == [], (L, validate.validate_xliff(p)[:5])
        x12 = html.unescape(re.search(rf'<pre id="out12-{L}">(.*?)</pre>', s, re.S).group(1))
        p12 = os.path.join(C["d"], f"page-{L}.xliff12.xlf"); open(p12, "w", encoding="utf-8").write(x12)
        assert validate.validate_xliff12(p12) == [], (L, validate.validate_xliff12(p12)[:5])
        assert '<seg-source xml:lang="de-CH"><mrk mtype="seg" mid="1">' in x12 and "LS ? → ?" not in x12
        if L == "fr": assert 'approved="yes"' in x12 and 'state="signed-off"' in x12 and "Texte révisé : 5 mg." in x12 and 'state="needs-translation"' in x12
        assert 'type="gleichlaut:changed"' in x and 'subState="gleichlaut:flagged"' not in x.replace('state="translated" subState="gleichlaut:flagged"', "")
        if L == "fr":
            assert 'state="reviewed" subState="gleichlaut:accepted-edited"' in x and "Texte révisé : 5 mg." in x
            assert 'state="initial" subState="gleichlaut:sent-back"' in x and "Révision : accepté modifié" in x


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
