"""The review page in a real browser (headless Chrome; skipped when no Chrome/Chromium is installed): the page script
runs without error, the page lands on the Register audit tab, #drafts opens the Drafts tab on the default lane (Apertus
8B Q8_0 on CPU, its figures in the context line) and the lane select / a hash prefix (#70b/wb013) opens the 70B "fewer
edits" lane under the same numbers, "Save, next" waits for a decision (drafts and audit), the legend tells the two
flagged marks apart, the storage note sits by the counter, no horizontal page overflow at 390 and 320 px (in an iframe of
that width: headless Chrome on macOS lays a --window-size below 500 px out at 500 px and crops the screenshot), #audit
opens the Register audit tab, a hash naming a draft opens it under the same number, the interface defaults to the browser language (else German), decisions import, the family action
accepts after an in-page confirmation, "start from the old text" replaces the editable draft, and the page's own XLIFF
2.1 and 1.2 exports (with an accepted-edited and a sent-back decision) validate against the 2.1 core XSD + constraints
and the 1.2 strict XSD. The audit decision asks one question first ("Which text is wrong?", the odd one first and
labelled, nothing preselected), then the remedy; it needs the reviewer's name, confirms inline when a version that agrees
with another is marked wrong, still imports decision files of the earlier page, and exports labels in the interface
language with machine codes alongside.
Runs under pytest or as `python3 tests/test_ui_browser.py`."""
import html, json, os, re, shutil, subprocess, sys, tempfile, unittest
import xml.etree.ElementTree as ET
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
NAME = ("function name(v){var n=document.getElementById('a-rev');n.value=v;n.dispatchEvent(new Event('input',{bubbles:true}))}"
        "function q(s){return document.querySelector('#acase '+s)}function bw(L){return q('.aw button[data-a=\"wrong\"][data-v=\"'+L+'\"]')}"
        "function br(v){return q('button[data-a=\"rem\"][data-v=\"'+v+'\"]')}function out(o){var e=document.createElement('pre');e.id='out';e.textContent=JSON.stringify(o);document.body.appendChild(e)}"
        "function rows(){return window.GleichlautReview.payload().audit_rows}")


def _out(s):
    return json.loads(html.unescape(re.search(r'<pre id="out">(.*?)</pre>', s, re.S).group(1)))


def test_audit_tab_opens_with_hash_and_german_default():
    C = _page(); s = _dom(C["p"], "#audit", "de-CH,de")
    assert re.search(r'id="t-audit"[^>]*aria-selected="true"', s) and re.search(r'id="p-audit"[^>]*role="tabpanel"(?![^>]*hidden)', s)
    I = C["D"]["audit"]["issues"]; nc = [i for i in I if i["blind"] == "not"]   # one row per issue (grouped findings)
    assert len(re.findall(r'<tr data-iss="[0-9a-f]{10}"', s)) == len(I) - len(nc) and "Registerprüfung" in s and 'lang="de"' in s
    assert f"Von den Annotatoren nicht bestätigt ({len(nc)})" in s and len(nc) == 4     # collapsed, counted, never dropped
    G = [html.unescape(x) for x in re.findall(r'<tr class="grp"><td colspan="3">([^<]*)</td>', s) if "esc(" not in x]
    assert G == ["Ändert eine Bedingung · 8", "Tippfehler und Redaktion · 3", "Terminologie · 3"], G     # by the blind majority label
    assert "Zwei blinde Claude-Annotatoren: ändert eine Bedingung" in html.unescape(s)                  # on the issue shown
    assert sum(len(i["rows"]) for i in I) == len(C["D"]["audit"]["rows"])            # every finding is in exactly one issue
    assert "Von Amtes wegen" in s and "Sprachdienst" in s and ">GÄL<" not in s
    assert re.search(r'id="ex-tg" aria-expanded="false">\[\+\] Experimentelle Prüfungen \(ausgeschaltet\) · 6 von 31 Befunden von zwei blinden Annotatoren bestätigt · 0 entschieden</button>', s)
    assert "27 Befunde + 11 Terminologie-Hinweise = 38, zusammengefasst in 18 Fällen; 4 davon von den blinden Annotatoren nicht bestätigt (eingeklappt)." in html.unescape(s)
    assert "14 Fälle in der Liste + 4 eingeklappt (nicht bestätigt) = 18 von 18 Fällen · 38 von 38 Befunden und Hinweisen" in html.unescape(s)


def test_landing_is_the_audit_tab_and_drafts_by_hash():
    C = _page()
    s = _dom(C["p"], "", "it-CH")                    # the audit runs today with no model: it is the landing view, first in the bar
    assert re.search(r'id="t-audit"[^>]*aria-selected="true"', s) and "Verifica del registro" in s
    assert re.search(r'id="t-audit"[^>]*>[^<]*<span class="c"[^>]*>18</span>', s)          # the audit's issue count in the bar
    assert s.index('id="t-audit"') < s.index('id="t-drafts"')
    s = _dom(C["p"], "#drafts", "fr-CH,fr")
    assert re.search(r'id="t-drafts"[^>]*aria-selected="true"', s) and "Brouillons" in s and "Exporter les décisions (JSON)" in s
    for lab in ("Vues", "Liste des cas", "Registre des modifications", "Famille", "Modification", "Langue de l'interface"):   # round 13
        assert f'aria-label="{html.escape(lab, quote=False)}"' in s.replace("&#39;", "'"), lab
    assert not re.search(r'aria-label="(?:Views|Issues|Family|Register|Case|Interface language)"', s)
    ctx = re.search(r'<p class="ctx" id="ctxline"[^>]*>(.*?)</p>', s, re.S).group(1); txt = html.unescape(re.sub(r"<select.*?</select>", "", ctx, flags=re.S))
    assert '<option value="8b" selected="">Jeu de test (publié) · 8B Q8_0, CPU (par défaut)</option>' in ctx and '<option value="70b">Jeu de test (publié) · Apertus 70B tel que servi par Public AI (optionnel ; identité non vérifiée)</option>' in html.unescape(ctx)
    assert '<option value="aug2026">Essai à blanc 08.2026 (hors production) · 8B Q8_0, CPU</option>' in ctx
    assert "Jeu de test réservé à l'évaluation : modifications passées de la LS 06.2025–02.2026, déjà publiées par l'OFSP, 166 brouillons d'Apertus 8B Q8_0." in txt
    assert "62 prêts (37.3%) · 104 signalés · 17.5% identiques" in txt and "La variante par défaut" in txt
    assert "moins de corrections" not in txt and "70B" not in txt                       # the default lane claims no fewer edits
    s = _dom(C["p"], "#70b/wb013", "fr-CH,fr")                                         # the optional lane, same numbering
    ctx = html.unescape(re.sub(r"<select.*?</select>", "", re.search(r'<p class="ctx" id="ctxline"[^>]*>(.*?)</p>', s, re.S).group(1), flags=re.S))
    assert "166 brouillons d'Apertus 70B." in ctx and "66 prêts (39.8%) · 100 signalés · 17.5% identiques" in ctx and "La variante 70B optionnelle" in ctx
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
                   "document.getElementById('fam-yes').click();var n0=Object.keys(R.payload().decisions).length,fr=document.getElementById('fam-rev');"
                   "fr.value='R. Muster';fr.dispatchEvent(new Event('input',{bubbles:true}));fr.dispatchEvent(new Event('change',{bubbles:true}));"
                   "var D0=R.payload().decisions,n=Object.keys(D0).length,by=n?D0[Object.keys(D0)[0]].by:null;"
                   "location.hash='#" + fl["key"][:-3] + "';setTimeout(function(){var b=document.querySelector('[data-start=\"" + fl["key"] + "\"]');if(b)b.click();"
                   "var e=document.createElement('pre');e.id='out';e.textContent=JSON.stringify({q1:q1,q2:q2,n0:n0,n:n,by:by,ed:R.payload().edits[" + json.dumps(fl["key"]) + "]||null,"
                   "marks:document.querySelectorAll('#reg .mk.f').length,b:!!b,err:window.__err});document.body.appendChild(e)},300)},300);")
    s = _dom(C["p"], "#drafts", "en", probe)
    o = json.loads(html.unescape(re.search(r'<pre id="out">(.*?)</pre>', s, re.S).group(1)))
    assert not o["err"], o["err"]
    assert o["q1"].startswith("Accept all ready drafts of this edit family") and "Confirm accept" in o["q2"] and o["n"] >= 2
    assert o["n0"] == 0 and o["by"] == "R. Muster"            # the family action waits for the reviewer's name, then runs
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
    assert "Schattenlauf 08.2026 (SL 01.08.2026 → 01.09.2026), nicht für den produktiven Einsatz, 38 Entwürfe von Apertus 8B Q8_0." in html.unescape(s)
    assert "4 bereit · 18 markiert · 16 an die Übersetzung · 1 von 22 identisch" in html.unescape(s)


def test_save_next_waits_for_a_decision_legend_and_storage_note():
    C = _page()
    probe = ERR + ("setTimeout(function(){var R=window.GleichlautReview,b=document.getElementById('savenext'),d0=b.disabled,w0=document.getElementById('sn-why').textContent;"
                   "function st(){return document.querySelector('.dec .stt').textContent}"
                   "document.querySelector('.dec button[data-d=\"accept\"]').click();var d1=document.getElementById('savenext').disabled,ask=!!document.getElementById('d-rev-ask'),st1=st(),"
                   "n1=Object.keys(R.payload().decisions).length,nm=document.getElementById('d-rev');"
                   "nm.value='M. Muster';nm.dispatchEvent(new Event('input',{bubbles:true}));nm.dispatchEvent(new Event('change',{bubbles:true}));"
                   "var d2=document.getElementById('savenext').disabled,st2=st(),D0=R.payload().decisions,by=D0[Object.keys(D0)[0]].by,at=D0[Object.keys(D0)[0]].at,prog=document.getElementById('progress').textContent;"
                   "document.querySelector('.dec button[data-d=\"accept\"]').click();var st3=st(),n3=Object.keys(R.payload().decisions).length;"
                   "var e=document.createElement('pre');e.id='out';e.textContent=JSON.stringify({d0:d0,w0:w0,d1:d1,ask:ask,st1:st1,n1:n1,d2:d2,st2:st2,by:by,at:at,st3:st3,n3:n3,label:b.textContent,"
                   "key:document.getElementById('reg-key').textContent,prog:prog,err:window.__err});document.body.appendChild(e)},300);")
    o = json.loads(html.unescape(re.search(r'<pre id="out">(.*?)</pre>', _dom(C["p"], "#drafts", "en", probe), re.S).group(1)))
    assert not o["err"] and o["d0"] is True and o["label"] == "Save, next change" and o["w0"].startswith("Decide first"), o
    # round 13: no decision without the reviewer's name (inline prompt, the first click kept and saved once the name is in)
    assert o["d1"] is True and o["ask"] and o["st1"].startswith("Enter your name first") and o["n1"] == 0, o
    assert o["d2"] is False and o["by"] == "M. Muster" and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d", o["at"]), o
    assert re.fullmatch(r"saved · \d{4}-\d\d-\d\d \d\d:\d\d [+-]\d\d:\d\d · M\. Muster", o["st2"]), o["st2"]     # Zurich time with offset
    assert o["st3"].startswith("decision undone") and o["n3"] == 0, o                                   # a second click says so
    assert "~ flagged, probably fine" in o["key"] and "▲ flagged, to check" in o["key"]
    assert o["prog"] == "1/166 decided · saved in this browser only · export to keep"
    probe = ERR + NAME + ("setTimeout(function(){var b=document.getElementById('a-next'),d0=b.getAttribute('aria-disabled')==='true',h=document.querySelector('#acase .sl .sub').textContent;name('A. Muster');"
                   "document.querySelector('#acase .aw button[data-a=\"wrong\"]').click();var dw=document.getElementById('a-next').getAttribute('aria-disabled')==='true';"
                   "document.querySelector('#acase button[data-a=\"rem\"][data-v=\"exofficio\"]').click();var st=document.getElementById('a-stt');"
                   "var e=document.createElement('pre');e.id='out';e.textContent=JSON.stringify({d0:d0,h:h,dw:dw,d1:document.getElementById('a-next').getAttribute('aria-disabled')==='true',"
                   "st:st.textContent,done:st.className,label:document.getElementById('a-next').textContent,err:window.__err});document.body.appendChild(e)},300);")
    o = json.loads(html.unescape(re.search(r'<pre id="out">(.*?)</pre>', _dom(C["p"], "#audit", "en", probe), re.S).group(1)))
    assert not o["err"] and o["d0"] is True and o["dw"] is True and o["d1"] is False and o["label"] == "Save, next issue", o   # the wrong text alone is not a decision
    assert o["h"].startswith("Decided once the wrong text and what to do are chosen. “Send to the language service”, “No action” and “Not clear yet” also count without naming the wrong text") and "done" in o["done"]
    assert o["st"].startswith("✓ IT wrong · Correct ex officio (IT) · decided on ") and " by A. Muster" in o["st"], o["st"]


def test_experimental_findings_are_decidable_and_exported_as_their_own_kind():
    C = _page()
    probe = ERR + NAME + ("setTimeout(function(){document.getElementById('ex-tg').click();var rows=document.querySelectorAll('#aud tr[data-iss]').length;"
                   "var x=document.querySelector('#aud tr[data-iss]:last-child');x.querySelector('td').click();"
                   "var h=document.getElementById('acase').textContent;name('A. Muster');document.querySelector('#acase button[data-a=\"rem\"][data-v=\"langsvc\"]').click();"
                   "var R=window.GleichlautReview,p=R.payload(),csv=R.auditCsv(),xi=p.audit_issues.filter(function(i){return i.kind==='experimental check'});"
                   "var e=document.createElement('pre');e.id='out';e.textContent=JSON.stringify({rows:rows,h:h,xi:xi.length,dec:xi.filter(function(i){return i.decided}).length,"
                   "kinds:Object.keys(p.audit_rows).map(function(k){return p.audit_rows[k].kind}),csv:csv.indexOf('experimental check')>=0,"
                   "head:document.getElementById('ex-tg').textContent,prog:document.getElementById('progress').textContent,err:window.__err});document.body.appendChild(e)},300);")
    o = json.loads(html.unescape(re.search(r'<pre id="out">(.*?)</pre>', _dom(C["p"], "#audit", "en", probe), re.S).group(1)))
    assert not o["err"], o["err"]
    assert o["rows"] == 14 + 6 and "Two blind Claude annotators: " in o["h"]                 # the same label line as an issue
    assert o["xi"] == 6 and o["dec"] == 1 and o["kinds"] == ["experimental check"] and o["csv"]
    assert o["head"].endswith("· 1 decided") and o["prog"].startswith("0/18 issues decided")      # outside the 18 issues


def test_family_labels_distinct_in_every_lane():
    C = _page()
    probe = ERR + ("setTimeout(function(){var o=[].map.call(document.querySelectorAll('#f-fam option'),function(x){return x.textContent});"
                   "var e=document.createElement('pre');e.id='out';e.textContent=JSON.stringify({o:o,err:window.__err});document.body.appendChild(e)},300);")
    for h in ("#drafts", "#sep2026/drafts", "#aug2026/drafts", "#70b/drafts"):
        o = json.loads(html.unescape(re.search(r'<pre id="out">(.*?)</pre>', _dom(C["p"], h, "en", probe), re.S).group(1)))
        assert not o["err"] and len(o["o"]) > 2 and len(set(o["o"])) == len(o["o"]), (h, [x for x in o["o"] if o["o"].count(x) > 1])


def test_import_merges_several_files_and_accept_edited_says_why():
    C = _page(); D = C["D"]
    it = next(it for g in D["groups"] for it in g["items"].values() if it["status"] == "flagged" and it["lang"] == "fr")
    rd = next(it for g in D["groups"] for it in g["items"].values() if it["status"] == "ready" and it.get("termq")
              and not (it["old"] or it.get("banner") or it.get("corr")))
    a = {"run_sha256": D["meta"]["run_sha256"], "decisions": {it["key"]: {"decision": "accept", "at": "2026-10-09T10:00:00Z"}}}
    b = {"run_sha256": D["meta"]["run_sha256"], "decisions": {it["key"]: {"decision": "send-back", "at": "2026-10-10T10:00:00Z"},
                                                              rd["key"]: {"decision": "accept", "at": "2026-10-10T10:00:00Z"}}}
    probe = ERR + ("setTimeout(function(){var R=window.GleichlautReview,m=R.importDecisions(" + json.dumps([a, b]) + ");"
                   "location.hash='#" + rd["key"][:-3] + "';setTimeout(function(){var d=R.payload().decisions;"
                   "var b2=document.querySelector('.dec[data-key=\"" + rd["key"] + "\"] button[data-d=\"accept-edited\"]'),w=document.getElementById('ae-" + rd["key"] + "');"
                   "var st=document.querySelector('.lang[data-lang=\"" + rd["lang"] + "\"] .lh1 .st').textContent,tip=(document.querySelector('.lang .n')||{}).title||'';"
                   "var e=document.createElement('pre');e.id='out';e.textContent=JSON.stringify({m:m,d:d[" + json.dumps(it["key"]) + "].decision,n:Object.keys(d).length,"
                   "dis:b2.disabled,why:w.textContent,hid:w.hidden,st:st,tip:tip,where:document.getElementById('where').textContent,err:window.__err});document.body.appendChild(e)},300)},300);")
    o = json.loads(html.unescape(re.search(r'<pre id="out">(.*?)</pre>', _dom(C["p"], "#drafts", "it", probe), re.S).group(1)))
    assert not o["err"], o["err"]
    assert o["m"].startswith("2 file uniti: 2 decisioni sulle bozze") and "In contrasto, tenuta la più recente: " + it["key"] in o["m"], o["m"]
    assert o["d"] == "send-back" and o["n"] == 2                                     # the newest decision per item wins
    assert o["dis"] is True and not o["hid"] and o["why"].startswith("«2 Accetta modificata» diventa disponibile")
    assert o["st"] == "pronta · termine da verificare"
    assert o["tip"] == "" or o["tip"].startswith("numero inserito dal codice") or o["tip"].startswith("numero scritto dal modello")
    assert "più file JSON insieme" in o["where"]


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


def test_page_segments_an_edited_target_like_python_and_signed_off_units_keep_no_draft_notes():
    """Round 13: the page's sentence segmenter (segBeads) equals emit/segment.beads on every draft and old target of the
    page; an edited unit is exported in sentence segments (XLIFF 2.1 and 1.2), and a signed-off unit carries no note about
    the draft it replaced, nor raw check output."""
    from gleichlaut.emit import segment
    from gleichlaut.emit import load
    C = _page(); D = C["D"]
    views = load("q8_0")[1]
    pairs = [[v["de_new"], v["draft"]] for v in views if v.get("draft")] + [[v["de_new"], v["tgt_old"]] for v in views if v.get("tgt_old")]
    pairs += [["Die Therapie wird vergütet. Max. 4 Zyklen, z. B. bei Rezidiv. Nr. 3 gilt.", "Le traitement est remboursé. Max. 4 cycles, p. ex. en cas de récidive. Le n° 3 s'applique."]]
    fl = next(it for g in D["groups"] for it in g["items"].values() if it["status"] == "flagged" and it["lang"] == "fr" and len(it["bd"]) >= 3)
    draft = "".join(s_[1] for s_ in fl["segs"] if s_[0] != "d")
    ed = draft.rstrip() + " Phrase ajoutée à la révision."
    dec = {"run_sha256": D["meta"]["run_sha256"], "decisions": {fl["key"]: {"decision": "accept-edited", "text": ed, "reason": "Wording", "note": "", "at": "2026-10-11T10:00:00Z"}}}
    dp = os.path.join(C["d"], "segpairs.js"); open(dp, "w", encoding="utf-8").write("window.__P=" + json.dumps(pairs, ensure_ascii=False) + ";")
    probe = ERR + ("setTimeout(function(){var R=window.GleichlautReview;R.importDecisions(" + json.dumps(dec, ensure_ascii=False) + ");"
                   "var o={b:window.__P.map(function(p){return R.segBeads(p[0],p[1])}),x:R.xliff('fr'),x12:R.xliff12('fr'),err:window.__err};"
                   "var e=document.createElement('pre');e.id='out';e.textContent=JSON.stringify(o);document.body.appendChild(e)},300);")
    page = open(C["p"], encoding="utf-8").read().replace("</head>", '<script src="segpairs.js"></script></head>', 1)
    q = os.path.join(C["d"], "seg.html"); open(q, "w", encoding="utf-8").write(page)
    o = _out(_dom(q, "#drafts", "en", probe))
    assert not o["err"], o["err"]
    py = [[list(b) for b in segment.beads(a, t)] for a, t in pairs]
    bad = [i for i, (x, y) in enumerate(zip(o["b"], py)) if x != y]
    assert len(o["b"]) == len(py) > 100 and not bad, [(pairs[i][1][:80], o["b"][i], py[i]) for i in bad[:3]]
    want = segment.beads(next(v["de_new"] for v in views if v["key"] == fl["key"]), ed)
    X2 = "{urn:oasis:names:tc:xliff:document:2.0}"; X12 = "{urn:oasis:names:tc:xliff:document:1.2}"
    u = next(u for u in ET.fromstring(o["x"].encode()).iter(X2 + "unit") if u.get("id") == fl["key"])
    S = u.findall(X2 + "segment")
    assert len(S) == len(want) >= 3 and "".join("".join(s_.find(X2 + "target").itertext()) for s_ in S) == ed
    assert [n.get("id") for n in u.find(X2 + "notes")] == ["verdict", "change", "de-old", "tgt-old", "review"]
    t = next(t for t in ET.fromstring(o["x12"].encode()).iter(X12 + "trans-unit") if t.get("id") == fl["key"])
    M = [m for m in t.find(X12 + "target") if m.get("mtype") == "seg"]
    assert len(M) == len(want) and "".join("".join(m.itertext()) for m in M) == ed and len(t.findall(X12 + "note")) == 5
    assert "Slots:" not in o["x12"] and "gleichlaut-debug" not in o["x12"] and "Sortie brute" not in o["x12"] + o["x"]
    for x, val in ((o["x"], validate.validate_xliff), (o["x12"], validate.validate_xliff12)):
        p = os.path.join(C["d"], "seg-out" + (".xliff12.xlf" if val is validate.validate_xliff12 else ".xlf")); open(p, "w", encoding="utf-8").write(x)
        assert val(p) == [], val(p)[:3]


DIAPHIN = "DIAPHIN.6-|number|it|12,6"


def test_audit_asks_which_text_is_wrong_odd_first_majority_confirmed_name_required():
    """The juror's mis-click: on Diaphin (IT differs) one question 'Which text is wrong?' with IT first and labelled, nothing
    preselected; no save without the reviewer's name (inline prompt, focus on the field); DE (agrees with FR) asks for an
    inline confirmation and saves nothing until confirmed; IT + language service is stored as right DE+FR, fix_it."""
    C = _page()
    probe = ERR + NAME + ("setTimeout(function(){var o={};o.order=[].map.call(document.querySelectorAll('#acase .aw button'),function(b){return b.textContent});"
        "o.pressed0=document.querySelectorAll('#acase button[aria-pressed=\"true\"]').length;o.dis0=[].filter.call(document.querySelectorAll('#acase .arem button'),function(b){return b.getAttribute('aria-disabled')==='true'}).map(function(b){return b.dataset.v});"
        "bw('IT').click();o.n0=Object.keys(rows()).length;o.ask=!!document.getElementById('a-name-ask');o.focus=document.activeElement&&document.activeElement.id;"
        "o.pend=bw('IT').getAttribute('aria-pressed');name('R. Muster');document.getElementById('a-rev').dispatchEvent(new Event('change',{bubbles:true}));o.ask2=!!document.getElementById('a-name-ask');"
        "o.kept=(rows()[" + json.dumps(DIAPHIN) + "]||{}).wrong;o.keptBy=(rows()[" + json.dumps(DIAPHIN) + "]||{}).by;"
        "bw('DE').click();o.conf=(q('.aconf')||{}).textContent||'';o.n1=rows()[" + json.dumps(DIAPHIN) + "].wrong;q('button[data-a=\"wcancel\"]').click();o.conf2=!!q('.aconf');"
        "bw('FR').click();q('.aconf .primary').click();o.fr=rows()[" + json.dumps(DIAPHIN) + "].wrong;bw('FR').click();"
        "o.next1=document.getElementById('a-next').getAttribute('aria-disabled')==='true';br('langsvc').click();o.next2=document.getElementById('a-next').getAttribute('aria-disabled')==='true';"
        "o.r=rows()[" + json.dumps(DIAPHIN) + "];o.rev=window.GleichlautReview.payload().reviewer;o.st=document.getElementById('a-stt').textContent;"
        "o.lab=br('langsvc').textContent;o.err=window.__err;out(o)},300);")
    o = _out(_dom(C["p"], "#audit", "en", probe))
    assert not o["err"], o["err"]
    assert o["order"] == ["IT · differs from the other two", "DE", "FR"] and o["pressed0"] == 0 and o["dis0"] == ["exofficio", "holder"]
    assert o["n0"] == 0 and o["ask"] and o["focus"] == "a-rev" and not o["ask2"] and o["pend"] == "true"   # kept, not saved, without a name
    assert o["kept"] == ["IT"] and o["keptBy"] == "R. Muster"                                      # saved once the name is in
    assert o["conf"].startswith("DE agrees with FR here; IT is the one that differs. Mark DE as wrong anyway?") and o["n1"] == ["IT"] and not o["conf2"]
    assert o["fr"] == ["FR", "IT"]                                                                 # confirmed, then taken back
    assert o["next1"] is True and o["next2"] is False and o["lab"] == "Send to the language service · IT"
    r = o["r"]
    assert (r["wrong"], r["remedy"], r["right"], r["actions"], r["by"], r["decided"]) == (["IT"], "langsvc", "DE+FR", ["fix_it", "langsvc"], "R. Muster", True), r
    assert o["rev"] == "R. Muster" and o["st"].startswith("✓ IT wrong · Send to the language service (IT) · decided on ")


def test_juror_sequence_disabled_remedy_then_name_then_note():
    """The juror's sequence on Diaphin in a fresh profile (no stored name): "Correct ex officio" first (not available yet:
    a one-line reason, nothing saved), then IT (the name is asked for; IT stays chosen), the name, a note, "Save, next
    issue" (says why it waits), then the remedy, which now registers, and "Save, next issue" moves on. Time stamps are
    Europe/Zurich with offset; both CSVs are ';'-separated with a BOM and carry the SL snapshot and the code revision."""
    C = _page()
    probe = ERR + NAME + ("setTimeout(function(){var o={},h0=q('h2').textContent;"
        "br('exofficio').click();var why=document.getElementById(br('exofficio').getAttribute('aria-describedby'));"
        "o.why=why&&!why.hidden&&why.classList.contains('warn')?why.textContent:'';o.n0=Object.keys(rows()).length;"
        "bw('IT').click();o.ask=!!document.getElementById('a-name-ask');o.pend=bw('IT').getAttribute('aria-pressed');o.exDis=br('exofficio').getAttribute('aria-disabled');"
        "var n=document.getElementById('a-rev');n.focus();n.value='J. Juror';n.dispatchEvent(new Event('input',{bubbles:true}));"
        "var ta=q('textarea[data-a=\"note\"]');ta.focus();ta.value='checked against the dossier';ta.dispatchEvent(new Event('input',{bubbles:true}));"
        "var r=rows()[" + json.dumps(DIAPHIN) + "]||{};o.w=r.wrong;o.by=r.by;o.note=r.note;o.st=document.getElementById('a-stt').textContent;"
        "o.exDis2=br('exofficio').getAttribute('aria-disabled');"
        "document.getElementById('a-next').click();var aw=document.getElementById('an-why');o.nextWhy=aw.classList.contains('warn')?aw.textContent:'';o.stay=q('h2').textContent===h0;"
        "br('exofficio').click();r=rows()[" + json.dumps(DIAPHIN) + "];o.r=r;o.st2=document.getElementById('a-stt').textContent;"
        "o.prog=document.getElementById('progress').textContent;"
        "var R=window.GleichlautReview;o.csv=R.auditCsv();o.f=R.findingsCsv();o.at=R.payload().audit_rows[" + json.dumps(DIAPHIN) + "].at;"
        "document.getElementById('a-next').click();o.moved=q('h2').textContent!==h0;o.err=window.__err;out(o)},300);")
    o = _out(_dom(C["p"], "#audit", "en", probe))
    assert not o["err"], o["err"]
    assert o["why"] == "“Correct ex officio” and “Raise with the holder” need the wrong text chosen above." and o["n0"] == 0, o
    assert o["ask"] and o["pend"] == "true" and o["exDis"] is None                     # IT kept while the name is asked for
    assert o["w"] == ["IT"] and o["by"] == "J. Juror" and o["note"] == "checked against the dossier" and o["exDis2"] is None, o
    assert o["st"].startswith("open · IT marked wrong, no action chosen yet"), o["st"]
    assert o["nextWhy"].startswith("Decide first") and o["stay"]
    r = o["r"]
    assert (r["wrong"], r["remedy"], r["decided"], r["by"]) == (["IT"], "exofficio", True, "J. Juror") and o["st2"].startswith("✓ IT wrong · Correct ex officio (IT)")
    assert re.fullmatch(r"20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\+0[12]:00", r["at"]) and o["at"] == r["at"], r["at"]
    assert o["prog"].startswith("1/18 issues decided · 0/6 experimental"), o["prog"]
    head, row = o["csv"].split("\r\n")[:2]
    assert o["csv"].startswith("\ufeff") and head.split(";")[-1] == "Code revision" and r["at"] in row and ";06.10.2026;" in row
    fh, fr = o["f"].split("\r\n")[:2]
    assert o["f"].startswith("\ufeff") and fh.lstrip("\ufeff").split(";")[-2:] == ["sl_snapshot", "rev"] and fr.split(";")[-2] == "20261006"
    assert o["moved"]


def test_old_decision_files_still_import():
    """A decision file of the earlier page (right + actions; the oldest with a single 'action') imports, counts as decided,
    keeps its fields in the export and shows as the two answers plus what was stored."""
    C = _page(); R = C["D"]["audit"]["rows"]
    s2 = next(r["sig"] for r in R if r["lim"] == "NEMLUVIO.01")
    old = {"audit_date": C["D"]["audit"]["meta"]["date"], "audit": {
        DIAPHIN: {"right": "", "actions": ["fix_de", "langsvc"], "note": "", "at": "2026-10-09T10:00:00Z", "by": ""},
        s2: {"right": "IT", "action": "Berichtigung", "note": "alt", "at": "2026-10-08T10:00:00Z", "by": "X"}}}
    probe = ERR + NAME + ("setTimeout(function(){var R=window.GleichlautReview,m=R.importDecisions(" + json.dumps(old) + ");R.setTab('audit');var o={m:m};"
        "o.p=[].map.call(document.querySelectorAll('#acase button[aria-pressed=\"true\"]'),function(b){return b.dataset.v});"
        "o.legs=[].map.call(document.querySelectorAll('#acase .sug'),function(x){return x.textContent});o.st=document.getElementById('a-stt').textContent;"
        "var x=rows();o.a=x[" + json.dumps(DIAPHIN) + "];o.b=x[" + json.dumps(s2) + "];o.prog=document.getElementById('progress').textContent;o.err=window.__err;out(o)},300);")
    o = _out(_dom(C["p"], "#audit", "en", probe))
    assert not o["err"], o["err"]
    assert o["m"] == "Imported 0 draft decisions and 2 audit decisions. Reviewer name taken from the file: X.", o["m"]
    a, b = o["a"], o["b"]
    assert (a["right"], a["actions"], a["wrong"], a["remedy"], a["decided"]) == ("", ["fix_de", "langsvc"], ["DE"], "langsvc", True)
    assert (b["right"], b["actions"], b["remedy"], b["decided"], b["by"]) == ("IT", ["exofficio"], "exofficio", True, "X")
    assert sorted(o["p"]) == ["DE", "langsvc"] and any(x.startswith("Stored by an earlier version of this page: Correct the text: DE; Send to the language service") for x in o["legs"]), o
    assert o["prog"].startswith("2/18 issues decided")


def test_exports_in_the_interface_language_with_codes():
    """A German reviewer's GEVER CSV is German (kind, action), with kind_code and action_code alongside; the findings CSV
    and the JSON carry the same labels and codes."""
    C = _page()
    probe = ERR + NAME + ("setTimeout(function(){name('R. Muster');bw('IT').click();br('exofficio').click();var R=window.GleichlautReview;"
        "out({csv:R.auditCsv(),f:R.findingsCsv(),j:rows()[" + json.dumps(DIAPHIN) + "],i:R.payload().audit_issues[0],err:window.__err})},300);")
    o = _out(_dom(C["p"], "#audit", "de-CH,de", probe))
    assert not o["err"], o["err"]
    head, row = o["csv"].lstrip("\ufeff").split("\r\n")[:2]
    H = head.split(";"); V = dict(zip(H, row.split(";")))
    assert H[5:7] == ["Art", "kind_code"] and H[10:14] == ["Falscher Text", "Fassung gemäss Entscheid", "Massnahme", "action_code"], H
    assert (V["Art"], V["kind_code"], V["Falscher Text"], V["Fassung gemäss Entscheid"], V["Massnahme"], V["action_code"], V["Entschieden von"]) == \
        ("Zahl", "number", "IT", "DE+FR", "Von Amtes wegen berichtigen (IT)", "fix_it exofficio", "R. Muster"), V
    assert "Correct" not in o["csv"] and ";Zahl;number;" in o["f"] and ";Von Amtes wegen berichtigen (IT);fix_it exofficio;;" in o["f"]
    j, i = o["j"], o["i"]
    assert (j["kind"], j["kind_label"], j["action_label"], j["actions"], j["ui_lang"]) == ("number", "Zahl", "Von Amtes wegen berichtigen (IT)", ["fix_it", "exofficio"], "de")
    assert i["action_label"] == j["action_label"] and i["by"] == "R. Muster" and i["kind_label"] == "Zahl"


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")


def test_gever_csv_label_and_excerpts_export_names_and_lane_help():
    """The GEVER CSV of the issues carries the blind label and the DE/FR/IT excerpts the issue view shows; the audit
    decisions export as gleichlaut-audit-decisions-<SL date>.json (audit only), the drafts' as a lane-specific file; the
    drafts tab explains the lanes and statuses under a "?" next to the lane select."""
    C = _page()
    probe = ERR + NAME + ("setTimeout(function(){var R=window.GleichlautReview,o={},csv=R.auditCsv().replace(/^\\ufeff/,'').split('\\r\\n');"
        "o.h=csv[0].split(';');o.r=csv[1].split(';');o.ex=[].map.call(document.querySelectorAll('#acase .ftg .snip'),function(x){return x.textContent});"
        "var f=R.decFile();o.fa=f[0];o.ka=Object.keys(f[1]).sort();R.setTab('drafts');f=R.decFile();o.fd=f[0];o.kd=Object.keys(f[1]);"
        "var q=document.getElementById('lane-q'),hp=document.getElementById('lanehelp');o.h0=hp.hidden;q.click();o.h1=hp.hidden;o.ht=hp.textContent;o.qe=q.getAttribute('aria-expanded');"
        "o.err=window.__err;out(o)},300);")
    o = _out(_dom(C["p"], "#audit", "en", probe))
    assert not o["err"], o["err"]
    V = dict(zip(o["h"], o["r"]))
    assert o["h"][-5:] == ["Blind label", "Excerpt DE", "Excerpt FR", "Excerpt IT", "Code revision"], o["h"]
    assert V["Blind label"] == "Two blind Claude annotators: changes a condition" and V["Issue"] == "01"
    for k, full in zip(("Excerpt DE", "Excerpt FR", "Excerpt IT"), o["ex"][:3]):      # the aligned excerpt, taken from the text shown
        assert V[k].strip("…").strip() in full, (k, V[k])
    assert "6%" in V["Excerpt DE"] and "12%" in V["Excerpt IT"]
    assert o["fa"] == "gleichlaut-audit-decisions-20261006.json" and "audit" in o["ka"] and "decisions" not in o["ka"]
    assert o["fd"].startswith("gleichlaut-decisions-") and "audit" not in o["fd"] and "audit" not in o["kd"] and "decisions" in o["kd"]
    assert o["h0"] and not o["h1"] and o["qe"] == "true" and "probably fine" in o["ht"] and "divergent" in o["ht"] and "identity not verified" in o["ht"]
