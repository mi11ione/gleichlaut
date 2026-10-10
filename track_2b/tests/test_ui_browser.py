"""The review page in a real browser (headless Chrome; skipped when no Chrome/Chromium is installed): the page script
runs without error, the page lands on the Register audit tab, #drafts opens the Drafts tab on the default lane (Apertus
8B Q8_0 on CPU, its figures in the context line) and the lane select / a hash prefix (#70b/wb013) opens the 70B "fewer
edits" lane under the same numbers, "Save, next" waits for a decision (drafts and audit), the legend tells the two
flagged marks apart, the storage note sits by the counter, no horizontal page overflow at 390 and 320 px (in an iframe of
that width: headless Chrome on macOS lays a --window-size below 500 px out at 500 px and crops the screenshot), #audit
opens the Register audit tab, a hash naming a draft opens it under the same number, the interface defaults to the browser language (else German), decisions import, the family action
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
    I = C["D"]["audit"]["issues"]; eq = [i for i in I if i["eq"]]          # one row per issue (grouped findings)
    assert len(re.findall(r'<tr data-iss="[0-9a-f]{10}"', s)) == len(I) - len(eq) and "Registerprüfung" in s and 'lang="de"' in s
    if eq: assert f"Wahrscheinlich gleichwertige Formulierung ({len(eq)})" in s     # collapsed, counted, never dropped
    assert sum(len(i["rows"]) for i in I) == len(C["D"]["audit"]["rows"])            # every finding is in exactly one issue
    assert "Von Amtes wegen" in s and "Sprachdienst" in s and ">GÄL<" not in s
    assert re.search(r'id="ex-tg" aria-expanded="true">\[−\] Experimentelle Prüfungen \(standardmässig aus\) · 6 von 31 bestätigt</button>', s)
    assert len(re.findall(r'<tr class="exp" data-exp="[OGW]\d\d"', s)) == 6 and 'data-exp="O01"' in s and 'data-exp="G03"' in s and 'data-exp="G17"' in s


def test_landing_is_the_audit_tab_and_drafts_by_hash():
    C = _page()
    s = _dom(C["p"], "", "it-CH")                    # the audit runs today with no model: it is the landing view, first in the bar
    assert re.search(r'id="t-audit"[^>]*aria-selected="true"', s) and "Verifica del registro" in s
    assert re.search(r'id="t-audit"[^>]*>[^<]*<span class="c"[^>]*>18</span>', s)          # the audit's issue count in the bar
    assert s.index('id="t-audit"') < s.index('id="t-drafts"')
    s = _dom(C["p"], "#drafts", "fr-CH,fr")
    assert re.search(r'id="t-drafts"[^>]*aria-selected="true"', s) and "Brouillons" in s and "Exporter les décisions (JSON)" in s
    ctx = re.search(r'<p class="ctx" id="ctxline"[^>]*>(.*?)</p>', s, re.S).group(1); txt = html.unescape(re.sub(r"<select.*?</select>", "", ctx, flags=re.S))
    assert '<option value="8b" selected="">Apertus 8B Q8_0 · CPU (par défaut)</option>' in ctx and '<option value="70b">Apertus 70B · point d\'accès (moins de corrections)</option>' in html.unescape(ctx)
    assert "166 brouillons d'Apertus 8B Q8_0." in txt and "62 prêts (37.3%) · 104 signalés · 17.5% identiques" in txt and "La voie par défaut" in txt
    assert "moins de corrections" not in txt and "70B" not in txt                       # the default lane claims no fewer edits
    s = _dom(C["p"], "#70b/wb013", "fr-CH,fr")                                         # the optional lane, same numbering
    ctx = html.unescape(re.sub(r"<select.*?</select>", "", re.search(r'<p class="ctx" id="ctxline"[^>]*>(.*?)</p>', s, re.S).group(1), flags=re.S))
    assert "166 brouillons d'Apertus 70B." in ctx and "66 prêts (39.8%) · 100 signalés · 17.5% identiques" in ctx and "La voie 70B optionnelle" in ctx
    assert '<option value="70b" selected="">' in s and re.search(r'<tr class="cnt" data-pair="wb013" aria-selected="true">', s)
    s = _dom(C["p"], "#wb013", "en")                 # one numbering: the address is the number
    assert re.search(r'<tr class="cnt" data-pair="wb013" aria-selected="true"><td class="m">.*?</td><td class="m">.*?</td><td class="prd"[^>]*>[^<]*<span class="pc">[^<]*· wb013</span>', s) and "No. wb013" in s
    assert "explanation (FR)" in s and "Check detail: all" in s


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


def test_lane_select_switches_and_hash_keeps_the_lane():
    C = _page()
    probe = ERR + ("setTimeout(function(){var e=document.createElement('pre');e.id='out';e.textContent=JSON.stringify({h:location.hash,err:window.__err});"
                   "document.body.appendChild(e);if(location.hash.indexOf('#70b')<0){var s=document.getElementById('lane-s');s.value='70b';s.onchange()}},300);")
    s = _dom(C["p"], "#drafts", "en", probe)                     # select -> #70b/drafts -> reload into the 70B lane
    o = json.loads(html.unescape(re.findall(r'<pre id="out">(.*?)</pre>', s, re.S)[-1]))
    assert not o["err"] and o["h"].startswith("#70b/") and "166 drafts by Apertus 70B." in html.unescape(s)
    s = _dom(C["p"], "#aug2026", "de")                           # a live month of the default 8B
    assert "Live-Monat 08.2026 (SL 01.08.2026 → 01.09.2026), 38 Entwürfe von Apertus 8B Q8_0." in html.unescape(s)
    assert "4 bereit · 18 markiert · 16 an die Übersetzung · 1 von 22 identisch" in html.unescape(s)


def test_save_next_waits_for_a_decision_legend_and_storage_note():
    C = _page()
    probe = ERR + ("setTimeout(function(){var b=document.getElementById('savenext'),d0=b.disabled,w0=document.getElementById('sn-why').textContent;"
                   "document.querySelector('.dec button[data-d=\"accept\"]').click();var d1=document.getElementById('savenext').disabled;"
                   "var e=document.createElement('pre');e.id='out';e.textContent=JSON.stringify({d0:d0,w0:w0,d1:d1,label:b.textContent,"
                   "key:document.getElementById('reg-key').textContent,prog:document.getElementById('progress').textContent,err:window.__err});document.body.appendChild(e)},300);")
    o = json.loads(html.unescape(re.search(r'<pre id="out">(.*?)</pre>', _dom(C["p"], "#drafts", "en", probe), re.S).group(1)))
    assert not o["err"] and o["d0"] is True and o["d1"] is False and o["label"] == "Save, next change" and o["w0"].startswith("Decide first"), o
    assert "~ flagged, probably fine" in o["key"] and "▲ flagged, to check" in o["key"]
    assert o["prog"] == "1/166 decided · saved in this browser only · export to keep"
    probe = ERR + ("setTimeout(function(){var b=document.getElementById('a-next'),d0=b.disabled,h=document.querySelector('#acase .sl .sub').textContent;"
                   "document.querySelector('#acase button[data-a=\"right\"]').click();var st=document.getElementById('a-stt');"
                   "var e=document.createElement('pre');e.id='out';e.textContent=JSON.stringify({d0:d0,h:h,d1:document.getElementById('a-next').disabled,"
                   "st:st.textContent,done:st.className,label:b.textContent,err:window.__err});document.body.appendChild(e)},300);")
    o = json.loads(html.unescape(re.search(r'<pre id="out">(.*?)</pre>', _dom(C["p"], "#audit", "en", probe), re.S).group(1)))
    assert not o["err"] and o["d0"] is True and o["d1"] is False and o["label"] == "Save, next issue"
    assert o["h"].startswith("Counts as decided once an answer below") and "done" in o["done"]


def test_no_horizontal_overflow_at_phone_width():
    C = _page(); ch = _chrome()
    probe = ("setTimeout(function(){parent.postMessage(JSON.stringify({w:document.documentElement.clientWidth,"
             "sw:document.documentElement.scrollWidth}),'*')},800);")
    s = open(C["p"], encoding="utf-8").read().replace("</body>", "<script>" + probe + "</script></body>")
    q = os.path.join(C["d"], "phone.html"); open(q, "w", encoding="utf-8").write(s)
    for w in (390, 320):
        for h in ("", "#drafts", "#wb004", "#70b/wb004"):
            wr = os.path.join(C["d"], "wrap.html")
            open(wr, "w", encoding="utf-8").write(f'<!doctype html><body style="margin:0"><iframe src="file://{q}{h}" style="border:0;width:{w}px;height:844px"></iframe>'
                                                 '<pre id="res"></pre><script>addEventListener("message",function(e){document.getElementById("res").textContent=e.data})</script></body>')
            prof = tempfile.mkdtemp(prefix="gl-prof-")
            try:
                r = subprocess.run([ch, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}", "--window-size=600,1000",
                                    "--virtual-time-budget=5000", "--dump-dom", "file://" + wr], capture_output=True, text=True, timeout=120)
            finally:
                shutil.rmtree(prof, ignore_errors=True)
            o = json.loads(html.unescape(re.search(r'<pre id="res">(.*?)</pre>', r.stdout, re.S).group(1)))
            assert o["sw"] <= o["w"] and w - 20 <= o["w"] <= w, (w, h, o)   # no horizontal overflow; a classic scrollbar (Linux) may take up to 20 px


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
