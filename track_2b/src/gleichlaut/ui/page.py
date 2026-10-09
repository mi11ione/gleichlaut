"""The review page template (HEAD = title + style, BODY = content + data + script), filled in by build.py.
No external request: fonts are inlined by build.fonts_css(), data by build.build()."""

HEAD = r"""<title>Gleichlaut Review</title>
<style>
__FONTS__
/* LAYOUT. One ruled sheet (max-width 1320px, centred; side gutter via padding-inline, padding-block only), 5px Swiss-red
   rule on top. 1 header: title + mono subtitle, two text tabs (Register audit | Drafts; the active one underlined on the
   rule), then a two-column key-value block for the active tab between two black rules.
   Register audit tab: lead sentence, filters, one ruled table row per audit finding (DE | FR | IT excerpts side by side,
   conflicting values boxed in red, the odd-one-out language with a red bar, two decision columns + note), export row.
   Below 900px each audit row becomes a labelled block.
   2 work area: register (left, 5fr: filters, sticky-head table of German changes, export row) | case (right, 7fr:
   1 German change, 2 Drafts FR|IT, 3 Checks ledger, 4 Decision). Below 900px the register sits above the case and every
   table scrolls inside its own overflow-x container. 3 footer: provenance + legend of the marks. Print: A4, register
   hidden, one case per page. Colour: ink on paper; red only for the top rule, failures, flags, pre-existing divergences
   and the keyboard focus outline. No fills, no radii, no shadows. */
:root{--paper:#ffffff;--ink:#0a0a0a;--ink2:#5f5f5b;--hair:#cfcfca;--rule:var(--ink);--red:#e1001a;--sel:var(--ink);--sel-ink:var(--paper);
--sans:"Source Sans 3","Frutiger","Avenir Next",Arial,sans-serif;--mono:"IBM Plex Mono",Menlo,Consolas,monospace;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0d0d0c;--ink:#ececea;--ink2:#9d9d97;--hair:#34342f;--red:#ff3b4e;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#0d0d0c;--ink:#ececea;--ink2:#9d9d97;--hair:#34342f;--red:#ff3b4e;color-scheme:dark}
*{box-sizing:border-box;border-radius:0}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:400 13px/1.5 var(--mono);font-variant-numeric:tabular-nums;border-top:5px solid var(--red)}
button,select,input,textarea{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--red);outline-offset:2px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important;scroll-behavior:auto!important}}
.sheet{max-width:1320px;margin:0 auto;padding-inline:max(16px,2.4vw);padding-block:0 28px}
.sans{font-family:var(--sans)}
/* header */
.hd{padding-block:22px 0}
.hrow{display:flex;flex-wrap:wrap;gap:6px 24px;align-items:flex-end;justify-content:space-between}
h1{font:400 34px/1.1 var(--sans);margin:0;letter-spacing:-.01em}
.sub{margin:6px 0 0;color:var(--ink2)}
.tools{display:flex;flex-wrap:wrap;gap:4px 16px;align-items:center;color:var(--ink2)}
.tools b{color:var(--ink);font-weight:500}
.tabs{display:flex;flex-wrap:wrap;gap:0 28px;margin-top:14px}
.tab{background:none;border:0;border-bottom:3px solid transparent;padding:6px 0 5px;font:500 12px/1.3 var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--ink2);cursor:pointer}
.tab:hover{color:var(--ink)}
.tab[aria-selected=true]{color:var(--ink);border-bottom-color:var(--ink)}
.tab .c{color:var(--ink2);font-weight:400;margin-left:6px}.tab .c.r{color:var(--red)}
.kv{display:grid;grid-template-columns:1fr 1fr;gap:0 32px;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);margin-top:0;padding-block:8px}
.kv .big{font-weight:500;color:var(--red)}
.kv dl{margin:0;display:grid;grid-template-columns:minmax(120px,max-content) 1fr;gap:2px 16px;align-content:start}
.kv dt{color:var(--ink2)}.kv dd{margin:0;overflow-wrap:anywhere}
.kv .pass{font-weight:500}.kv .fail{color:var(--red);font-weight:500}
/* text buttons */
.tb{background:none;border:0;padding:2px 0;cursor:pointer;text-decoration:none;border-bottom:2px solid transparent}
.tb:hover{border-bottom-color:var(--hair)}
.tb[aria-pressed=true]{border-bottom-color:var(--ink)}
.box{background:none;border:1px solid var(--ink);padding:3px 9px;cursor:pointer;white-space:nowrap}
.box[aria-pressed=true],.box.primary{background:var(--ink);color:var(--paper)}
.box:disabled{opacity:.45;cursor:default}
/* work area */
.work{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:0 28px;margin-top:0}
.register{border-right:1px solid var(--hair);padding-right:20px;padding-block:12px 0;min-width:0;position:sticky;top:0;align-self:start;max-height:100vh;display:flex;flex-direction:column}
.filters{display:flex;flex-direction:column;gap:6px;padding-bottom:10px;border-bottom:1px solid var(--rule)}
.fl{display:flex;flex-wrap:wrap;gap:2px 12px;align-items:baseline}
.fl .k{color:var(--ink2);min-width:72px}
.fl select,.fl input{background:var(--paper);border:0;border-bottom:1px solid var(--hair);padding:3px 0;min-width:0}
.fl input{flex:1 1 140px}.fl select{flex:0 1 auto;max-width:100%}
.tbl{overflow-x:auto;min-width:0}
.reg-wrap{overflow:auto;flex:1 1 auto;min-height:120px}
table{border-collapse:collapse;width:100%}
th{font:500 11px/1.4 var(--mono);text-transform:uppercase;letter-spacing:.06em;text-align:left;color:var(--ink2);padding:6px 8px;border-bottom:1px solid var(--rule);vertical-align:bottom}
td{padding:5px 8px;border-bottom:1px solid var(--hair);vertical-align:top}
#reg{table-layout:fixed;min-width:420px}
#reg thead th{position:sticky;top:0;background:var(--paper);z-index:1}
#reg col.c-mark{width:84px}#reg col.c-no{width:46px}#reg col.c-prod{width:34%}
#reg td{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;cursor:pointer}
#reg td.chg{font:400 14px/1.45 var(--sans)}
#reg td.prd .pc{display:block;font-size:11px;color:var(--ink2);overflow:hidden;text-overflow:ellipsis}
#reg tr[aria-selected=true] td.prd .pc{color:var(--sel-ink)}
#reg tr:hover td{background:color-mix(in srgb,var(--ink) 5%,transparent)}
#reg tr[aria-selected=true] td{background:var(--sel);color:var(--sel-ink)}
#reg tr[aria-selected=true] .mk.r{color:var(--sel-ink);text-decoration:underline}
.mk{letter-spacing:-.02em}.mk.r{color:var(--red);font-weight:500}.mk.o{color:var(--ink2)}
.count{color:var(--ink2);padding:6px 0}
.export{display:flex;flex-wrap:wrap;gap:8px;padding:10px 0 12px;border-top:1px solid var(--rule)}
.export .msg{color:var(--ink2);flex-basis:100%}
.export .where{color:var(--ink2);flex-basis:100%;font-size:12px}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
#copybox{width:100%;height:90px;font:12px/1.4 var(--mono);border:1px solid var(--hair);background:var(--paper)}
/* case */
.case{min-width:0;padding-block:14px 0}
.case:focus{outline:none}
h2{font:400 22px/1.25 var(--sans);margin:0}
.ref{color:var(--ink2);margin:4px 0 0;overflow-wrap:anywhere}
.sec{border-top:1px solid var(--rule);margin-top:16px;padding-top:8px}
.sl{display:flex;flex-wrap:wrap;gap:4px 14px;align-items:baseline;color:var(--ink2);margin-bottom:8px}
.sl .no{color:var(--ink);font-weight:500}
.sl .t{color:var(--ink);font-weight:500;text-transform:uppercase;letter-spacing:.06em;font-size:11px}
.sl .sp{margin-left:auto}
.txt{font:400 17px/1.55 var(--sans);white-space:pre-wrap;overflow-wrap:anywhere}
.de{border-left:1px solid var(--rule);padding-left:14px}
ins{text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:3px;text-decoration-color:var(--ink)}
del{color:var(--ink2);text-decoration:line-through;text-decoration-thickness:1px}
del{margin-right:.2em}
.gap{color:var(--ink2);font-family:var(--mono);font-size:13px;padding:0 4px}
.n{font:400 .8em/1 var(--mono);border:1px solid var(--hair);padding:1px 3px;white-space:nowrap}
.n sup{font-size:.7em;color:var(--ink2);margin-left:1px;vertical-align:.45em}
.n.m{border-color:var(--red)}
.drafts{display:grid;grid-template-columns:1fr 1fr;gap:0}
.drafts.one{grid-template-columns:1fr}
.dr{min-width:0;padding-right:16px}
.dr+.dr{border-left:1px solid var(--hair);padding:0 0 0 16px}
.dl{display:flex;flex-wrap:wrap;gap:2px 10px;align-items:baseline;margin-bottom:6px}
.dl .ln{font-weight:500}.dl .st{font-weight:500}.dl .st.r{color:var(--red)}.dl .key{color:var(--ink2);margin-left:auto}
.dl .cap{color:var(--ink2);font-size:12px;flex-basis:100%}
.dl .tri{color:var(--ink2)}.dl .tri b{color:var(--red);font-weight:500}
.ids{color:var(--ink2);margin-top:2px;font-size:12px}.ids summary{cursor:pointer;display:inline}
.notice.lang{font-size:17px}.notice.lang p:first-child{font-weight:600}
.notice{border-left:3px solid var(--red);padding:4px 0 4px 10px;margin:0 0 10px;font:400 15px/1.45 var(--sans)}
.notice .mk{font-family:var(--mono);font-size:13px;color:var(--red);font-weight:500;margin-right:6px}
.notice p{margin:0}.notice p+p{margin-top:4px}
.ed{outline:1px solid transparent;padding:2px 4px;margin:0 -4px}
.ed:hover{outline-color:var(--hair)}
.ed:focus{outline:1px solid var(--ink)}
.edmeta{color:var(--ink2);margin-top:6px;display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline}
.edmeta .tb{color:var(--ink)}
.human{font:400 15px/1.45 var(--sans);margin:0 0 8px}
.ledger{table-layout:auto;min-width:480px;margin-bottom:12px}
.ledger caption{text-align:left;font-weight:500;padding:2px 0 4px}
.ledger td{font-size:13px}
.ledger td.res{white-space:nowrap}
.ledger td.chk{width:34%}
.ledger .FAIL{color:var(--red);font-weight:500}.ledger .na{color:var(--ink2)}
.ledger .fd{font:400 15px/1.4 var(--sans)}
.ledger .fd p{margin:0}.ledger .fd p+p{margin-top:3px}
.ledger .cn{display:block;font:500 12px/1.4 var(--mono);color:var(--red);margin-top:2px}
.ledger details{margin-top:3px;color:var(--ink2);font-size:12px}
.ledger summary{cursor:pointer}
.ledger details div{overflow-wrap:anywhere;white-space:pre-wrap}
.ledger details.pf{color:var(--ink);font-size:inherit;margin-top:4px;border-top:1px dotted var(--hair);padding-top:3px}
.ledger details.pf summary{font:400 12px/1.4 var(--mono);color:var(--ink2)}
.ledger details.pf p{color:var(--ink2)}
.ledger caption .tri{font-weight:400;color:var(--ink2);margin-left:8px}.ledger caption .tri b{color:var(--red);font-weight:500}
.decs{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}
.decs.one{grid-template-columns:1fr}
.dec{min-width:0;border-left:3px solid transparent;padding:4px 0 6px 10px}
.dec.focus{border-left-color:var(--ink)}
.btns{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}
.dec label{display:block;color:var(--ink2);margin-top:6px}
.dec select{display:block;width:100%;margin-top:2px;background:var(--paper);border:1px solid var(--hair);padding:3px 4px}
.dec textarea{display:block;width:100%;margin-top:2px;min-height:52px;resize:vertical;background:var(--paper);border:1px solid var(--hair);padding:4px 6px;font:400 15px/1.4 var(--sans)}
.dec .stt{color:var(--ink2);margin-top:4px}
.save{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;margin-top:10px;padding-top:10px;border-top:1px solid var(--hair)}
.save .hint{color:var(--ink2)}
.empty{color:var(--ink2);padding:24px 0}
/* register audit */
.audit{padding-block:12px 0}
.lead{font:400 16px/1.45 var(--sans);margin:0 0 10px;max-width:90ch}
.afl{display:flex;flex-direction:column;gap:6px;padding-bottom:10px;border-bottom:1px solid var(--rule)}
#aud{table-layout:fixed;min-width:1080px}
#aud col.a-no{width:58px}#aud col.a-lim{width:13%}#aud col.a-kind{width:92px}#aud col.a-dec{width:118px}#aud col.a-act{width:15%}
#aud thead th{position:sticky;top:0;background:var(--paper);z-index:1}
#aud td{font-size:13px}
#aud tr.grp td{font:500 11px/1.4 var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--ink);padding:16px 8px 6px;border-bottom:1px solid var(--rule)}
#aud tr.grp .mk{margin-right:8px}
#aud .lim b{font:400 15px/1.3 var(--sans);display:block}
#aud .lim .code{color:var(--ink2);overflow-wrap:anywhere}
#aud .sub2{display:block;color:var(--ink2);font-size:12px;margin-top:3px}
.snip{font:400 14px/1.45 var(--sans);overflow-wrap:anywhere}
.snip .v2{border:1px solid var(--red);padding:0 2px;font-weight:600;white-space:nowrap}
.snip .v1{border-bottom:1px solid var(--ink2)}
.snip.src-s{color:color-mix(in srgb,var(--ink) 82%,var(--paper))}
.snip .sx{display:block;font:400 11px/1.3 var(--mono);color:var(--ink2);margin-top:3px}
td.odd{box-shadow:inset 3px 0 0 var(--red);padding-left:12px}
.oddl{display:block;font:500 11px/1.3 var(--mono);color:var(--red);text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px}
#aud select{width:100%;background:var(--paper);border:1px solid var(--hair);padding:3px 4px}
#aud textarea{display:block;width:100%;margin-top:4px;min-height:44px;resize:vertical;background:var(--paper);border:1px solid var(--hair);padding:3px 5px;font:400 14px/1.35 var(--sans)}
#aud .sug{color:var(--ink2);font-size:12px;margin-top:3px}
#aud .stt{color:var(--ink2);font-size:12px;margin-top:3px}
#aud .na{color:var(--ink2);font-style:italic}
footer{border-top:1px solid var(--rule);margin-top:28px;padding-top:8px;color:var(--ink2)}
footer p{margin:2px 0;overflow-wrap:anywhere}
#print{display:none}
[hidden]{display:none!important}
@media (max-width:900px){
 #aud{min-width:0;table-layout:auto}#aud colgroup,#aud thead{display:none}
 #aud tbody,#aud tr,#aud td{display:block;width:auto}
 #aud tr{border-bottom:1px solid var(--rule);padding:8px 0 10px}#aud tr.grp{padding:0;border:0}
 #aud td{border:0;padding:3px 0}#aud td.odd{padding-left:10px}#aud td.odd>.oddl{display:none}
 .kv dl{grid-template-columns:minmax(96px,44%) minmax(0,1fr)}
 #aud td[data-l]::before{content:attr(data-l);display:block;font:500 11px/1.4 var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--ink2)}
 .work{grid-template-columns:minmax(0,1fr)}
 .register{position:static;max-height:none;border-right:0;padding-right:0;border-bottom:1px solid var(--rule)}
 .reg-wrap{max-height:46vh}
 #reg{min-width:0}#reg col.c-mark{width:70px}#reg col.c-no{width:46px}
 .kv{grid-template-columns:1fr}
 .drafts,.decs{grid-template-columns:1fr}
 .dr{padding-right:0}.dr+.dr{border-left:0;border-top:1px solid var(--hair);padding:12px 0 0;margin-top:12px}
 h1{font-size:30px}
}
@media print{
 @page{size:A4;margin:14mm}
 body{border-top:0;font-size:10pt;background:#fff;color:#000}
 .register,.tools,.tabs,.save,.export,.edmeta,.btns,.dec select,.dec textarea,#case{display:none!important}
 #aud select,#aud textarea{border:0;padding:0}
 .work{display:block}
 #print{display:block}
 .pcase{break-after:page;page-break-after:always}
 .txt{font-size:11pt}
}
</style>
"""

BODY = r"""<div class="sheet">
<header class="hd">
 <div class="hrow">
  <div><h1>Gleichlaut</h1><p class="sub" id="sub"></p></div>
  <div class="tools"><span id="progress"></span><button class="tb" id="theme" type="button"></button>
   <label><span id="l-ui"></span> <select id="ui-lang" aria-label="Interface language"><option value="de">DE</option><option value="en">EN</option><option value="fr">FR</option><option value="it">IT</option></select></label></div>
 </div>
 <nav class="tabs" role="tablist" aria-label="Views"><button class="tab" role="tab" type="button" id="t-audit" aria-controls="p-audit"></button><button class="tab" role="tab" type="button" id="t-drafts" aria-controls="p-drafts"></button></nav>
 <div class="kv"><dl id="kv-l"></dl><dl id="kv-r"></dl></div>
</header>
<section class="audit" id="p-audit" role="tabpanel" aria-labelledby="t-audit" hidden>
 <p class="lead" id="a-lead"></p>
 <div class="afl"><div class="fl" id="a-show"></div><div class="fl" id="a-lang"></div><div class="fl" id="a-kind"></div></div>
 <div class="tbl"><table id="aud"><colgroup><col class="a-no"><col class="a-lim"><col class="a-kind"><col><col><col><col class="a-dec"><col class="a-act"></colgroup>
  <thead><tr><th id="ah-no"></th><th id="ah-lim"></th><th id="ah-kind"></th><th>DE</th><th>FR</th><th>IT</th><th id="ah-right"></th><th id="ah-act"></th></tr></thead><tbody></tbody></table></div>
 <div class="count" id="a-shown"></div>
 <div class="export"><button class="box" id="a-json" type="button"></button><button class="box" id="a-csv" type="button"></button><button class="box" id="a-imp" type="button"></button>
  <span class="msg" id="a-msg" aria-live="polite"></span><span class="where" id="a-where"></span></div>
</section>
<div class="work" id="p-drafts" role="tabpanel" aria-labelledby="t-drafts">
 <section class="register" id="register" aria-label="Register">
  <div class="filters">
   <div class="fl" id="f-status"></div>
   <div class="fl" id="f-lang"></div>
   <div class="fl"><select id="f-fam" aria-label="Family"></select><input type="search" id="f-q" aria-label="Search product or limitation code"></div>
  </div>
  <div class="tbl reg-wrap" id="reg-wrap"><table id="reg"><colgroup><col class="c-mark"><col class="c-no"><col class="c-prod"><col></colgroup>
   <thead><tr><th id="h-mark"></th><th id="h-no"></th><th id="h-prod"></th><th id="h-chg"></th></tr></thead><tbody></tbody></table></div>
  <div class="count" id="shown"></div>
  <div class="export"><button class="box" id="x-xlf" type="button"></button><button class="box" id="x-json" type="button"></button><button class="box" id="x-copy" type="button"></button><button class="box" id="x-imp" type="button"></button>
   <span class="msg" id="x-msg" aria-live="polite"></span><span class="where" id="x-where"></span><textarea id="copybox" hidden readonly aria-label="Decisions JSON"></textarea></div>
 </section>
 <section class="case" id="case" tabindex="-1" aria-label="Case"></section>
</div>
<input type="file" id="imp-file" accept="application/json,.json" class="vh" tabindex="-1" aria-hidden="true">
<textarea id="clipbox" class="vh" tabindex="-1" aria-hidden="true" readonly></textarea>
<footer><p id="prov"></p><p id="legend"></p><p id="legend2"></p></footer>
</div>
<div id="print" class="sheet"></div>
<script type="application/json" id="data">__DATA__</script>
<script>
(function(){
"use strict";
var D=JSON.parse(document.getElementById("data").textContent),M=D.meta,A=D.all,G=D.groups,AU=D.audit;
var LK="gleichlaut:"+M.run+":"+M.run_sha256.slice(0,12),AK="gleichlaut:audit:"+(AU?AU.meta.date:"none");
function lsGet(k,d){try{var v=localStorage.getItem(k);return v==null?d:JSON.parse(v)}catch(e){return d}}
function lsSet(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}
var S=lsGet(LK+":state",null)||{dec:{},edits:{}};S.dec=S.dec||{};S.edits=S.edits||{};
var SA=lsGet(AK,null)||{};
var P=lsGet("gleichlaut:prefs",{})||{};
function save(){lsSet(LK+":state",S)}
function saveA(){lsSet(AK,SA)}
function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}
function $(id){return document.getElementById(id)}
function fmt(s,o){return String(s).replace(/\{(\w+)\}/g,function(_,k){return o[k]!=null?o[k]:""})}
// ------------------------------------------------------------------ interface strings (DE / EN / FR / IT)
var TX={
de:{ui:"Sprache",sub:"Prüfregister",drafts:"Entwürfe",model:"Modell",run:"Lauf",guards:"Prüfungen",items:"Elemente",changes:"Änderungen",ready:"Bereit",flagged:"Markiert",
 exact:"Exakt vs. nur Regeln",rule:"Vorregistrierte Regel",human:"An Übersetzung übergeben",divergent:"Bisheriger Text weicht ab",decided:"entschieden",
 status:"Status",language:"Sprache",open:"Offen",all:"Alle",decidedF:"Entschieden",divF:"Abweichend",allFam:"Alle Familien",search:"Produkt oder Code",
 mark:"Zeichen",no:"Nr.",product:"Produkt",change:"Änderung",shown:"Änderungen angezeigt",xlf:"XLIFF 2.1 exportieren",json:"JSON exportieren",copy:"Entscheide kopieren",
 copied:"Entscheide in die Zwischenablage kopiert.",selcopy:"Zwischenablage gesperrt: Das JSON ist unten markiert, mit Ctrl/Cmd+C kopieren.",dl:"Heruntergeladen",
 s1:"Deutsche Änderung",s2:"Entwürfe",s3:"Prüfungen",s4:"Entscheid",ctxA:"Kontext: um die Änderungen",ctxF:"Kontext: ganzer Text",de:"Deutsch",fr:"Französisch",it:"Italienisch",
 lready:"bereit",lflagged:"markiert",lhuman:"an Übersetzung übergeben",readyAttn:"bereit (bisheriger Text prüfen)",edited:"bearbeitet",reset:"Entwurf wiederherstellen",editHint:"In den Text klicken, um ihn direkt zu bearbeiten.",
 check:"Prüfung",result:"Ergebnis",finding:"Befund",pass:"ok",fail:"FEHLER",na:"n. a.",raw:"technisches Detail",noChecks:"Keine Prüfung: kein maschineller Entwurf.",
 accept:"Übernehmen",acceptEd:"Bearbeitet übernehmen",sendBack:"Zurückweisen",reason:"Grund",note:"Notiz (warum)",saveNext:"Speichern, weiter",keys:"Tasten 1/2/3 entscheiden · f/i Sprache · Ctrl/Cmd+Enter speichern, weiter",
 savedAt:"gespeichert",openSt:"offen",noEdit:"Zuerst den Entwurfstext bearbeiten (hineinklicken).",
 humanTxt:"An Übersetzung übergeben: Das Deutsche wurde zu mehr als 60 % neu geschrieben",humanShort:"An Übersetzung übergeben, kein maschineller Entwurf",humanPrev:"Bisheriger Text (direkt bearbeiten, um die neue Fassung zu schreiben):",
 none:"Keine Änderung entspricht diesen Filtern.",provenance:"Herkunft",
 legend:"Zeichen: [x] bereit · [!] markiert · [≠] der bisherige Text hat bereits ein Problem (weicht vom Deutschen ab oder ist in einer anderen Sprache) · [h] an Übersetzung übergeben · [a] übernommen · [e] bearbeitet übernommen · [r] zurückgewiesen · Tasten j/k oder ↑/↓ bewegen, Enter öffnet, f/i Sprache, 1/2/3 entscheiden, Ctrl/Cmd+Enter speichern und weiter",
 theme:"Darstellung",auto:"auto",light:"hell",dark:"dunkel",
 reasons:["","Zahl falsch","Deutsche Änderung nicht übernommen","Inhalt verloren","Deutsch stehen geblieben / nicht übersetzt","Terminologie","Formulierung","Anderes"],
 tabAudit:"Registerprüfung",tabDrafts:"Entwürfe",codeOnly:"Bereit heisst: vom Code geprüft, nicht von einer Person.",
 triage:"Markierungen",chk1:"1 Punkt zu prüfen",chkN:"{n} Punkte zu prüfen",fine:"{n} wahrscheinlich in Ordnung",pf:"wahrscheinlich in Ordnung",
 rT1:"T1 Vokabular",rT2:"T2 Modalverb",rT3:"T3 Zahlen",rT4:"T4 Abkürzung",
 rdT1:"T1 Vokabular: ein «unbekanntes Wort», das ein wohlgeformtes Wort der Zielsprache ist (nur Buchstaben der Zielsprache, mind. 4, keine deutschen Lautfolgen wie sch/ck/tz/-ung/-keit/-lich, kein Wort des deutschen Textes und nicht mit dessen ersten 8 Buchstaben).",
 rdT2:"T2 Modalverb: das zusätzliche «doit/deve» entspricht einer deutschen Konstruktion «ist/sind … zu + Verb», die die Prüfung nicht als Modalverb zählt, und der Text sagt «doit être / deve essere».",
 rdT3:"T3 Zahlen: der Entwurf ändert genau dieselben Zahlenwerte wie das Deutsche (Zahlwörter 2–12 als Zahlen, Dezimalkomma als Dezimalpunkt).",
 rdT4:"T4 Abkürzung: als «Deutsch» gemeldete Wörter sind alle römische Zahlen oder Abkürzungen (mind. 2 Grossbuchstaben, mind. die Hälfte der Buchstaben, kein Umlaut).",
 triHead:"Sortierung der Markierungen (ordnet und klappt nur ein; der Status bleibt, kein Befund wird verborgen):",
 limitation:"Limitation",ids:"interne Kennungen",family:"Familie",pair:"Paar",itemsL:"Elemente",
 copyTxt:"Text kopieren",copiedTxt:"Text kopiert (reiner Text für das ePL-Feld).",copySel:"Zwischenablage gesperrt: Der Text ist markiert, mit Ctrl/Cmd+C kopieren.",
 imp:"Entscheide importieren",imported:"Importiert: {d} Entscheide zu Entwürfen, {a} Entscheide zur Registerprüfung.",impBad:"Keine Gleichlaut-Entscheiddatei.",
 impRun:"Die Entscheide zu Entwürfen stammen aus einem anderen Lauf und wurden nicht importiert.",
 where:"Entscheide werden nur in diesem Browser gespeichert (lokaler Speicher dieser Seite, pro Browserprofil). Mit «JSON exportieren» sichern oder weitergeben, mit «Entscheide importieren» wiederherstellen.",
 oldLang:"Der bisherige {A} Text ist auf {F}.",adj:{fr:"französische",it:"italienische"},lname:{de:"Deutsch",fr:"Französisch",it:"Italienisch",en:"Englisch",rm:"Rätoromanisch"},
 aLead:"Widersprüche, die schon heute zwischen dem deutschen, französischen und italienischen Text der geltenden SL bestehen (Stand {d}), vom Code gefunden, bevor ein Entwurf entsteht. Die bekannten, im Text belegten Abweichungen sind der Beleg für das Problem.",
 aKnownHead:"Bekannte Abweichungen, im Text belegt: {k} von {n} gefunden",aOtherHead:"Weitere Befunde der Prüfung",
 aLim:"Limitation",aKind:"Art",aOdd:"Weicht ab",aRight:"Welche Sprache stimmt?",aAction:"Massnahme · Notiz",aNote:"Notiz",aSug:"Vorschlag der Prüfung",
 aNoSnip:"kein Auszug in der Prüfdatei",aSnapSrc:"Auszug aus dem SL-Stand, über Position und gemeinsame Zahlen gefunden",
 kinds:{number:"Zahl",unit:"Einheit",language:"Sprache",editorial:"Redaktionell"},aUnclear:"unklar",acts:{"Berichtigung":"Berichtigung","GÄL":"GÄL","none":"keine","unclear":"unklar"},
 aShow:"Anzeigen",aKnownF:"Bekannt",aAllF:"Alle",aOpenF:"Offen",aDecF:"Entschieden",aKindF:"Art",aShown:"Befunde angezeigt",
 aSnap:"SL-Stand",aChecked:"Geprüfte Limitationen",aFindings:"Befunde",aOnLims:"in {n} Limitationen",aKnown:"Bekannte Abweichungen gefunden",aReal:"Echt bei Blindprüfung (Zahlen)",
 aHeld:"Zurückgehaltene Hälfte",aCalls:"Modellaufrufe",aCsv:"CSV exportieren",aNone:"Kein Befund entspricht diesen Filtern.",aNoFile:"Keine Prüfdatei in diesem Build.",
 aLegend:"Zeichen: [k] bekannte Abweichung, im Text belegt · [d] entschieden · rot umrahmt = widersprüchlicher Wert · unterstrichen = weitere Zahl · roter Balken = die Sprache, die von den beiden anderen abweicht (nicht unbedingt die falsche). Entscheide: welche Sprache die richtige Bedingung nennt, und die Massnahme (Berichtigung, GÄL, keine).",
 aExpl:"erklärt durch {x}",aFix:"wahrscheinlicher Tippfehler: «{a}» → «{b}»",aSince:"in der SL seit {d} ({n} Stände)",aFoundL:"Text auf {F}",oddLbl:"weicht ab",real:"echt",of:"von"},
en:{ui:"UI",sub:"Review register",drafts:"drafts",model:"Model",run:"Run",guards:"Guards",items:"Items",changes:"Changes",ready:"Ready",flagged:"Flagged",
 exact:"Exact vs rules-only",rule:"Pre-registered rule",human:"Routed to a translator",divergent:"Previous text diverges",decided:"decided",
 status:"Status",language:"Language",open:"Open",all:"All",decidedF:"Decided",divF:"Divergent",allFam:"All families",search:"Product or code",
 mark:"Mark",no:"No.",product:"Product",change:"Change",shown:"changes shown",xlf:"Export XLIFF 2.1",json:"Export JSON",copy:"Copy decisions",
 copied:"Decisions copied to the clipboard.",selcopy:"Clipboard blocked: the JSON is selected below, copy it with Ctrl/Cmd+C.",dl:"Downloaded",
 s1:"German change",s2:"Drafts",s3:"Checks",s4:"Decision",ctxA:"Context: around changes",ctxF:"Context: full text",de:"German",fr:"French",it:"Italian",
 lready:"ready",lflagged:"flagged",lhuman:"routed to a translator",readyAttn:"ready (old text needs attention)",edited:"edited",reset:"Reset to draft",editHint:"Click the text to edit it in place.",
 check:"Check",result:"Result",finding:"Finding",pass:"pass",fail:"FAIL",na:"n/a",raw:"technical detail",noChecks:"No checks: no machine draft.",
 accept:"Accept",acceptEd:"Accept edited",sendBack:"Send back",reason:"Reason",note:"Note (why)",saveNext:"Save, next",keys:"keys 1/2/3 decide · f/i language · Ctrl/Cmd+Enter save, next",
 savedAt:"saved",openSt:"open",noEdit:"Edit the draft text first (click into it).",
 humanTxt:"Routed to a translator: the German was rewritten by more than 60%",humanShort:"Routed to a translator, no machine draft",humanPrev:"Previous text (edit it in place to write the new version):",
 none:"No change matches these filters.",provenance:"Provenance",
 legend:"Marks: [x] ready · [!] flagged · [≠] the previous text already has a problem (diverges from the German or is in another language) · [h] routed to a translator · [a] accepted · [e] accepted edited · [r] sent back · keys j/k or ↑/↓ move, Enter opens, f/i language, 1/2/3 decide, Ctrl/Cmd+Enter save and next",
 theme:"Theme",auto:"auto",light:"light",dark:"dark",
 reasons:["","Number wrong","German change not applied","Content lost","German left / untranslated","Terminology","Wording","Other"],
 tabAudit:"Register audit",tabDrafts:"Drafts",codeOnly:"Ready means checked by code, not by a person.",
 triage:"Flag findings",chk1:"1 issue to check",chkN:"{n} issues to check",fine:"{n} probably fine",pf:"probably fine",
 rT1:"T1 vocabulary",rT2:"T2 modal verb",rT3:"T3 numbers",rT4:"T4 acronym",
 rdT1:"T1 vocabulary: an 'unknown word' that is a well-formed target-language word (target alphabet only, at least 4 letters, no German letter sequence such as sch/ck/tz/-ung/-keit/-lich, not a word of the German text and not sharing its first 8 letters with one).",
 rdT2:"T2 modal verb: the extra 'doit/deve' matches a German 'ist/sind … zu + verb' construction, which the check does not count as a modal verb, and the text says 'doit être / deve essere'.",
 rdT3:"T3 numbers: the draft changes exactly the same number values as the German (number words 2–12 counted as numbers, decimal comma as decimal point).",
 rdT4:"T4 acronym: the words reported as German are all Roman numerals or acronyms (at least 2 capitals, at least half of the letters, no umlaut).",
 triHead:"Flag triage (orders and collapses only; the verdict stays and no finding is hidden):",
 limitation:"Limitation",ids:"internal ids",family:"family",pair:"pair",itemsL:"items",
 copyTxt:"Copy text",copiedTxt:"Text copied (plain text for the ePL field).",copySel:"Clipboard blocked: the text is selected, copy it with Ctrl/Cmd+C.",
 imp:"Import decisions",imported:"Imported {d} draft decisions and {a} audit decisions.",impBad:"Not a Gleichlaut decisions file.",
 impRun:"The draft decisions come from another run and were not imported.",
 where:"Decisions are kept in this browser only (this page's local storage, per browser profile). Export JSON to keep or share them; Import decisions restores them.",
 oldLang:"The previous {A} text is in {F}.",adj:{fr:"French",it:"Italian"},lname:{de:"German",fr:"French",it:"Italian",en:"English",rm:"Romansh"},
 aLead:"Contradictions that already exist between the German, French and Italian texts of the current SL (snapshot {d}), found by code before any draft is made. The known divergences, confirmed in the texts, are the evidence of the problem.",
 aKnownHead:"Known divergences, confirmed in the texts: {k} of {n} found",aOtherHead:"Further findings of the audit",
 aLim:"Limitation",aKind:"Kind",aOdd:"Odd one out",aRight:"Which language is right?",aAction:"Action · note",aNote:"Note",aSug:"audit suggests",
 aNoSnip:"no excerpt in the audit file",aSnapSrc:"excerpt from the SL snapshot, located by position and shared numbers",
 kinds:{number:"number",unit:"unit",language:"language",editorial:"editorial"},aUnclear:"unclear",acts:{"Berichtigung":"Berichtigung (correction)","GÄL":"GÄL","none":"none","unclear":"unclear"},
 aShow:"Show",aKnownF:"Known",aAllF:"All",aOpenF:"Open",aDecF:"Decided",aKindF:"Kind",aShown:"findings shown",
 aSnap:"SL snapshot",aChecked:"Limitations checked",aFindings:"Findings",aOnLims:"on {n} limitations",aKnown:"Known divergences found",aReal:"Real on blind check (numbers)",
 aHeld:"Held-out half",aCalls:"Model calls",aCsv:"Export CSV",aNone:"No finding matches these filters.",aNoFile:"No audit file in this build.",
 aLegend:"Marks: [k] known divergence, confirmed in the texts · [d] decided · red box = conflicting value · underlined = other number · red bar = the language that differs from the other two (not necessarily the wrong one). Decisions: which language states the right condition, and the action (Berichtigung, GÄL, none).",
 aExpl:"explained by {x}",aFix:"probable typo: “{a}” → “{b}”",aSince:"in the SL since {d} ({n} snapshots)",aFoundL:"text in {F}",oddLbl:"odd one out",real:"real",of:"of"},
fr:{ui:"Interface",sub:"Registre de révision",drafts:"brouillons",model:"Modèle",run:"Série",guards:"Contrôles",items:"Éléments",changes:"Changements",ready:"Prêts",flagged:"Signalés",
 exact:"Exact vs règles seules",rule:"Règle préenregistrée",human:"Confiés à un traducteur",divergent:"Ancien texte divergent",decided:"décidés",
 status:"Statut",language:"Langue",open:"Ouverts",all:"Tous",decidedF:"Décidés",divF:"Divergents",allFam:"Toutes les familles",search:"Produit ou code",
 mark:"Marque",no:"N°",product:"Produit",change:"Changement",shown:"changements affichés",xlf:"Exporter XLIFF 2.1",json:"Exporter JSON",copy:"Copier les décisions",
 copied:"Décisions copiées dans le presse-papiers.",selcopy:"Presse-papiers bloqué : le JSON est sélectionné ci-dessous, copiez-le avec Ctrl/Cmd+C.",dl:"Téléchargé",
 s1:"Changement allemand",s2:"Brouillons",s3:"Contrôles",s4:"Décision",ctxA:"Contexte : autour des changements",ctxF:"Contexte : texte entier",de:"Allemand",fr:"Français",it:"Italien",
 lready:"prêt",lflagged:"signalé",lhuman:"confié à un traducteur",readyAttn:"prêt (ancien texte à vérifier)",edited:"modifié",reset:"Rétablir le brouillon",editHint:"Cliquez dans le texte pour le modifier sur place.",
 check:"Contrôle",result:"Résultat",finding:"Constat",pass:"ok",fail:"ÉCHEC",na:"s.o.",raw:"détail technique",noChecks:"Pas de contrôle : pas de brouillon machine.",
 accept:"Accepter tel quel",acceptEd:"Accepter modifié",sendBack:"Renvoyer",reason:"Motif",note:"Remarque (pourquoi)",saveNext:"Enregistrer, suivant",keys:"touches 1/2/3 décider · f/i langue · Ctrl/Cmd+Entrée enregistrer, suivant",
 savedAt:"enregistré",openSt:"ouvert",noEdit:"Modifiez d'abord le texte du brouillon (cliquez dedans).",
 humanTxt:"Confié à un traducteur : l'allemand a été réécrit à plus de 60 %",humanShort:"Confié à un traducteur, pas de brouillon machine",humanPrev:"Ancien texte (modifiez-le sur place pour écrire la nouvelle version) :",
 none:"Aucun changement ne correspond à ces filtres.",provenance:"Provenance",
 legend:"Marques : [x] prêt · [!] signalé · [≠] l'ancien texte a déjà un problème (diverge de l'allemand ou est dans une autre langue) · [h] confié à un traducteur · [a] accepté · [e] accepté modifié · [r] renvoyé · touches j/k ou ↑/↓ naviguer, Entrée ouvrir, f/i langue, 1/2/3 décider, Ctrl/Cmd+Entrée enregistrer et suivant",
 theme:"Thème",auto:"auto",light:"clair",dark:"sombre",
 reasons:["","Nombre erroné","Changement allemand non appliqué","Contenu perdu","Allemand resté / non traduit","Terminologie","Formulation","Autre"],
 tabAudit:"Audit du registre",tabDrafts:"Brouillons",codeOnly:"Prêt signifie : vérifié par le code, pas par une personne.",
 triage:"Constats",chk1:"1 point à vérifier",chkN:"{n} points à vérifier",fine:"{n} probablement sans problème",pf:"probablement sans problème",
 rT1:"T1 vocabulaire",rT2:"T2 verbe modal",rT3:"T3 nombres",rT4:"T4 sigle",
 rdT1:"T1 vocabulaire : un « mot inconnu » qui est un mot bien formé de la langue cible (lettres de la langue cible seulement, au moins 4, pas de suite de lettres allemande comme sch/ck/tz/-ung/-keit/-lich, ni mot du texte allemand ni mêmes 8 premières lettres).",
 rdT2:"T2 verbe modal : le « doit/deve » en plus correspond à une construction allemande « ist/sind … zu + verbe », que le contrôle ne compte pas comme verbe modal, et le texte dit « doit être / deve essere ».",
 rdT3:"T3 nombres : le brouillon change exactement les mêmes valeurs que l'allemand (nombres écrits en lettres 2–12 comptés comme nombres, virgule décimale comme point).",
 rdT4:"T4 sigle : les mots signalés comme allemands sont tous des chiffres romains ou des sigles (au moins 2 majuscules, au moins la moitié des lettres, sans umlaut).",
 triHead:"Tri des signalements (ordonne et replie seulement ; le verdict reste, aucun constat n'est caché) :",
 limitation:"Limitation",ids:"identifiants internes",family:"famille",pair:"paire",itemsL:"éléments",
 copyTxt:"Copier le texte",copiedTxt:"Texte copié (texte brut pour le champ ePL).",copySel:"Presse-papiers bloqué : le texte est sélectionné, copiez-le avec Ctrl/Cmd+C.",
 imp:"Importer des décisions",imported:"Importé : {d} décisions sur les brouillons, {a} décisions d'audit.",impBad:"Ce n'est pas un fichier de décisions Gleichlaut.",
 impRun:"Les décisions sur les brouillons proviennent d'une autre série et n'ont pas été importées.",
 where:"Les décisions sont gardées dans ce navigateur seulement (stockage local de cette page, par profil de navigateur). « Exporter JSON » pour les conserver ou les partager ; « Importer des décisions » pour les restaurer.",
 oldLang:"L'ancien texte {A} est en {F}.",adj:{fr:"français",it:"italien"},lname:{de:"allemand",fr:"français",it:"italien",en:"anglais",rm:"romanche"},
 aLead:"Contradictions qui existent déjà entre les textes allemand, français et italien de la LS en vigueur (état {d}), trouvées par le code avant tout brouillon. Les divergences connues, attestées dans les textes, sont la preuve du problème.",
 aKnownHead:"Divergences connues, attestées dans les textes : {k} sur {n} trouvées",aOtherHead:"Autres constats de l'audit",
 aLim:"Limitation",aKind:"Type",aOdd:"Diverge",aRight:"Quelle langue a raison ?",aAction:"Mesure · remarque",aNote:"Remarque",aSug:"proposition de l'audit",
 aNoSnip:"pas d'extrait dans le fichier d'audit",aSnapSrc:"extrait de l'état de la LS, repéré par position et nombres communs",
 kinds:{number:"nombre",unit:"unité",language:"langue",editorial:"rédactionnel"},aUnclear:"pas clair",acts:{"Berichtigung":"Berichtigung (rectification)","GÄL":"GÄL","none":"aucune","unclear":"pas clair"},
 aShow:"Afficher",aKnownF:"Connues",aAllF:"Toutes",aOpenF:"Ouvertes",aDecF:"Décidées",aKindF:"Type",aShown:"constats affichés",
 aSnap:"État de la LS",aChecked:"Limitations contrôlées",aFindings:"Constats",aOnLims:"sur {n} limitations",aKnown:"Divergences connues trouvées",aReal:"Réels au contrôle à l'aveugle (nombres)",
 aHeld:"Moitié réservée",aCalls:"Appels au modèle",aCsv:"Exporter CSV",aNone:"Aucun constat ne correspond à ces filtres.",aNoFile:"Pas de fichier d'audit dans cette version.",
 aLegend:"Marques : [k] divergence connue, attestée dans les textes · [d] décidé · cadre rouge = valeur contradictoire · souligné = autre nombre · barre rouge = la langue qui diffère des deux autres (pas forcément la fausse). Décisions : quelle langue dit la bonne condition, et la mesure (Berichtigung, GÄL, aucune).",
 aExpl:"expliqué par {x}",aFix:"coquille probable : « {a} » → « {b} »",aSince:"dans la LS depuis le {d} ({n} états)",aFoundL:"texte en {F}",oddLbl:"diverge",real:"réels",of:"sur"},
it:{ui:"Interfaccia",sub:"Registro di revisione",drafts:"bozze",model:"Modello",run:"Serie",guards:"Controlli",items:"Elementi",changes:"Modifiche",ready:"Pronte",flagged:"Segnalate",
 exact:"Esatte vs solo regole",rule:"Regola preregistrata",human:"Affidate a un traduttore",divergent:"Vecchio testo divergente",decided:"decise",
 status:"Stato",language:"Lingua",open:"Aperte",all:"Tutte",decidedF:"Decise",divF:"Divergenti",allFam:"Tutte le famiglie",search:"Prodotto o codice",
 mark:"Segno",no:"N.",product:"Prodotto",change:"Modifica",shown:"modifiche mostrate",xlf:"Esporta XLIFF 2.1",json:"Esporta JSON",copy:"Copia decisioni",
 copied:"Decisioni copiate negli appunti.",selcopy:"Appunti bloccati: il JSON è selezionato qui sotto, copiarlo con Ctrl/Cmd+C.",dl:"Scaricato",
 s1:"Modifica tedesca",s2:"Bozze",s3:"Controlli",s4:"Decisione",ctxA:"Contesto: attorno alle modifiche",ctxF:"Contesto: testo intero",de:"Tedesco",fr:"Francese",it:"Italiano",
 lready:"pronta",lflagged:"segnalata",lhuman:"affidata a un traduttore",readyAttn:"pronta (vecchio testo da verificare)",edited:"modificata",reset:"Ripristina la bozza",editHint:"Cliccare nel testo per modificarlo sul posto.",
 check:"Controllo",result:"Esito",finding:"Rilievo",pass:"ok",fail:"ERRORE",na:"n.a.",raw:"dettaglio tecnico",noChecks:"Nessun controllo: nessuna bozza automatica.",
 accept:"Accetta così",acceptEd:"Accetta modificata",sendBack:"Rinvia",reason:"Motivo",note:"Nota (perché)",saveNext:"Salva, avanti",keys:"tasti 1/2/3 decidere · f/i lingua · Ctrl/Cmd+Invio salva, avanti",
 savedAt:"salvato",openSt:"aperta",noEdit:"Modificare prima il testo della bozza (cliccarci dentro).",
 humanTxt:"Affidata a un traduttore: il tedesco è stato riscritto per oltre il 60%",humanShort:"Affidata a un traduttore, nessuna bozza automatica",humanPrev:"Vecchio testo (modificarlo sul posto per scrivere la nuova versione):",
 none:"Nessuna modifica corrisponde a questi filtri.",provenance:"Provenienza",
 legend:"Segni: [x] pronta · [!] segnalata · [≠] il vecchio testo ha già un problema (diverge dal tedesco o è in un'altra lingua) · [h] affidata a un traduttore · [a] accettata · [e] accettata modificata · [r] rinviata · tasti j/k o ↑/↓ spostarsi, Invio aprire, f/i lingua, 1/2/3 decidere, Ctrl/Cmd+Invio salva e avanti",
 theme:"Tema",auto:"auto",light:"chiaro",dark:"scuro",
 reasons:["","Numero errato","Modifica tedesca non applicata","Contenuto perso","Tedesco rimasto / non tradotto","Terminologia","Formulazione","Altro"],
 tabAudit:"Verifica del registro",tabDrafts:"Bozze",codeOnly:"Pronta significa: verificata dal codice, non da una persona.",
 triage:"Rilievi",chk1:"1 punto da verificare",chkN:"{n} punti da verificare",fine:"{n} probabilmente in ordine",pf:"probabilmente in ordine",
 rT1:"T1 vocabolario",rT2:"T2 verbo modale",rT3:"T3 numeri",rT4:"T4 sigla",
 rdT1:"T1 vocabolario: una «parola sconosciuta» che è una parola ben formata della lingua di destinazione (solo lettere della lingua di destinazione, almeno 4, nessuna sequenza tedesca come sch/ck/tz/-ung/-keit/-lich, né parola del testo tedesco né stesse prime 8 lettere).",
 rdT2:"T2 verbo modale: il «doit/deve» in più corrisponde a una costruzione tedesca «ist/sind … zu + verbo», che il controllo non conta come verbo modale, e il testo dice «doit être / deve essere».",
 rdT3:"T3 numeri: la bozza cambia esattamente gli stessi valori del tedesco (numeri in lettere 2–12 contati come numeri, virgola decimale come punto).",
 rdT4:"T4 sigla: le parole segnalate come tedesche sono tutte numeri romani o sigle (almeno 2 maiuscole, almeno metà delle lettere, senza umlaut).",
 triHead:"Smistamento dei rilievi (ordina e richiude soltanto; il verdetto resta, nessun rilievo è nascosto):",
 limitation:"Limitazione",ids:"identificativi interni",family:"famiglia",pair:"coppia",itemsL:"elementi",
 copyTxt:"Copia il testo",copiedTxt:"Testo copiato (testo semplice per il campo ePL).",copySel:"Appunti bloccati: il testo è selezionato, copiarlo con Ctrl/Cmd+C.",
 imp:"Importa decisioni",imported:"Importate: {d} decisioni sulle bozze, {a} decisioni della verifica.",impBad:"Non è un file di decisioni Gleichlaut.",
 impRun:"Le decisioni sulle bozze provengono da un'altra serie e non sono state importate.",
 where:"Le decisioni restano solo in questo browser (memoria locale di questa pagina, per profilo del browser). «Esporta JSON» per conservarle o condividerle; «Importa decisioni» per ripristinarle.",
 oldLang:"Il vecchio testo {A} è in {F}.",adj:{fr:"francese",it:"italiano"},lname:{de:"tedesco",fr:"francese",it:"italiano",en:"inglese",rm:"romancio"},
 aLead:"Contraddizioni già presenti tra i testi tedesco, francese e italiano dell'ES in vigore (stato {d}), trovate dal codice prima di qualsiasi bozza. Le divergenze note, confermate nei testi, sono la prova del problema.",
 aKnownHead:"Divergenze note, confermate nei testi: {k} su {n} trovate",aOtherHead:"Altri rilievi della verifica",
 aLim:"Limitazione",aKind:"Tipo",aOdd:"Diverge",aRight:"Quale lingua è giusta?",aAction:"Misura · nota",aNote:"Nota",aSug:"proposta della verifica",
 aNoSnip:"nessun estratto nel file di verifica",aSnapSrc:"estratto dallo stato dell'ES, individuato per posizione e numeri comuni",
 kinds:{number:"numero",unit:"unità",language:"lingua",editorial:"redazionale"},aUnclear:"non chiaro",acts:{"Berichtigung":"Berichtigung (rettifica)","GÄL":"GÄL","none":"nessuna","unclear":"non chiaro"},
 aShow:"Mostra",aKnownF:"Note",aAllF:"Tutte",aOpenF:"Aperte",aDecF:"Decise",aKindF:"Tipo",aShown:"rilievi mostrati",
 aSnap:"Stato dell'ES",aChecked:"Limitazioni controllate",aFindings:"Rilievi",aOnLims:"su {n} limitazioni",aKnown:"Divergenze note trovate",aReal:"Reali al controllo alla cieca (numeri)",
 aHeld:"Metà riservata",aCalls:"Chiamate al modello",aCsv:"Esporta CSV",aNone:"Nessun rilievo corrisponde a questi filtri.",aNoFile:"Nessun file di verifica in questa versione.",
 aLegend:"Segni: [k] divergenza nota, confermata nei testi · [d] decisa · riquadro rosso = valore in contraddizione · sottolineato = altro numero · barra rossa = la lingua che differisce dalle altre due (non per forza quella sbagliata). Decisioni: quale lingua indica la condizione giusta, e la misura (Berichtigung, GÄL, nessuna).",
 aExpl:"spiegato da {x}",aFix:"refuso probabile: «{a}» → «{b}»",aSince:"nell'ES dal {d} ({n} stati)",aFoundL:"testo in {F}",oddLbl:"diverge",real:"reali",of:"su"}};
function pickUI(){if(TX[P.ui])return P.ui;var L=[];try{L=(navigator.languages&&navigator.languages.length)?navigator.languages:[navigator.language||""]}catch(e){}
 for(var i=0;i<L.length;i++){var c=String(L[i]||"").slice(0,2).toLowerCase();if(TX[c])return c}return "de"}
var UL=pickUI();function t(k){return (TX[UL][k]!=null?TX[UL][k]:TX.en[k])}
function triTxt(c,f){return (c===1?t("chk1"):fmt(t("chkN"),{n:c}))+(f?", "+fmt(t("fine"),{n:f}):"")}
function triHTML(c,f){var a=esc(c===1?t("chk1"):fmt(t("chkN"),{n:c}));return (c?"<b>"+a+"</b>":a)+(f?", "+esc(fmt(t("fine"),{n:f})):"")}
// ------------------------------------------------------------------ theme
var themes=["auto","light","dark"],TH=themes.indexOf(P.theme)>=0?P.theme:(document.documentElement.getAttribute("data-theme")||"auto");
function applyTheme(){if(TH==="auto")document.documentElement.removeAttribute("data-theme");else document.documentElement.setAttribute("data-theme",TH);
 $("theme").textContent=t("theme")+": "+t(TH)}
$("theme").onclick=function(){TH=themes[(themes.indexOf(TH)+1)%3];P.theme=TH;lsSet("gleichlaut:prefs",P);applyTheme()};
$("ui-lang").value=UL;$("ui-lang").onchange=function(){UL=this.value;P.ui=UL;lsSet("gleichlaut:prefs",P);chrome();if(TAB==="audit")renderAudit();else{renderReg();renderCase()}};
// ------------------------------------------------------------------ helpers over the data
function pct(x){return (Math.round(x*10)/10).toFixed(1)+"%"}
function sgn(x){x=+x;return (x>0?"+":x<0?"−":"")+Math.abs(x)}
function plain(S,old){return S.filter(function(s){return old?s[0]!=="i":s[0]!=="d"}).map(function(s){return s[1]}).join("")}
G.forEach(function(g,i){g.no=("00"+(i+1)).slice(-3);g.deNew=plain(g.de,false);g.deOld=plain(g.de,true);["fr","it"].forEach(function(L){var it=g.items[L];if(it){it.draft=it.status==="human"?"":plain(it.segs,false);it.g=g}})});
var ITEMS=[];G.forEach(function(g){["fr","it"].forEach(function(L){if(g.items[L])ITEMS.push(g.items[L])})});
var FAML={};D.families.forEach(function(f){FAML[f[0]]=f[2]});
function dec(it){return S.dec[it.key]}
function oldIssue(it){return !!(it.banner||it.corr||(it.old&&it.old.length))}
function mark(it){if(!it)return ['<span class="mk o">[ ]</span>',""];var d=dec(it);
 if(d)return ['<span class="mk">['+(d.decision==="accept"?"a":d.decision==="accept-edited"?"e":"r")+']</span>',d.decision];
 if(oldIssue(it))return ['<span class="mk r">[≠]</span>',"divergent"];
 if(it.status==="human")return ['<span class="mk">[h]</span>',"human"];
 return it.status==="ready"?['<span class="mk">[x]</span>',"ready"]:['<span class="mk r">[!]</span>',"flagged"]}
// ------------------------------------------------------------------ header and chrome
var TAB="drafts";
function kv(id,rows){$(id).innerHTML=rows.map(function(r){return "<dt"+(r[3]?' title="'+esc(r[3])+'"':"")+">"+esc(r[0])+"</dt><dd"+(r[2]?' class="'+r[2]+'"':"")+">"+esc(r[1])+"</dd>"}).join("")}
function ddate(s){return /^\d{8}$/.test(s||"")?s.slice(6,8)+"."+s.slice(4,6)+"."+s.slice(0,4):(s||"?")}
function chrome(){
 document.documentElement.lang=UL;$("l-ui").textContent=t("ui");applyTheme();
 $("sub").textContent=t("sub")+" · "+M.label+" · "+D.counts.items+" "+t("drafts");
 $("t-audit").hidden=!AU;
 $("t-audit").innerHTML=esc(t("tabAudit"))+(AU?'<span class="c r">'+AU.rows.length+"</span>":"");$("t-drafts").innerHTML=esc(t("tabDrafts"))+'<span class="c">'+D.counts.items+"</span>";
 $("t-audit").setAttribute("aria-selected",TAB==="audit");$("t-drafts").setAttribute("aria-selected",TAB==="drafts");
 $("t-audit").tabIndex=TAB==="audit"?0:-1;$("t-drafts").tabIndex=TAB==="drafts"?0:-1;
 $("p-audit").hidden=TAB!=="audit";$("p-drafts").hidden=TAB!=="drafts";
 $("prov").textContent=t("provenance")+": "+M.pipeline+" · outputs sha256:"+M.run_sha256.slice(0,16)+"… · items sha256:"+M.items_sha256.slice(0,16)+"…"+(AU?" · audit "+AU.meta.file+(AU.meta.results?" + "+AU.meta.results:""):"");
 if(TAB==="audit"){chromeAudit();return}
 var fz=(M.pipeline.match(/freeze sha256:([0-9a-f]+)/)||[])[1]||"";
 kv("kv-l",[[t("model"),M.model],[t("run"),M.run],[t("guards"),(M.stack==="g3"?"guards3 (frozen)":"guards v2 (frozen)")+(fz?" · freeze "+fz.slice(0,12):"")],
  [t("items"),String(D.counts.items)],[t("changes"),String(D.counts.changes)]]);
 var C=D.counts,r=[];
 if(A){r.push([t("ready"),A.unflagged+" · "+pct(A.ready_rate),"",t("codeOnly")]);r.push([t("flagged"),A.flagged+" · "+pct(A.flag_rate)]);
  var ex=A.exact;r.push([t("exact"),pct(ex.model)+" vs "+pct(ex.rules)+" ("+sgn(ex.delta)+" pts, 95% CI "+ex.ci95[0]+" to "+ex.ci95[1]+")"]);
  if(A.pass!=null)r.push([t("rule"),A.pass?"PASS":"FAIL",A.pass?"pass":"fail"])}
 else{r.push([t("ready"),String(C.ready),"",t("codeOnly")]);r.push([t("flagged"),String(C.flagged)]);if(C.human)r.push([t("human"),String(C.human)]);
  if(C.exact!=null)r.push([t("exact").split(" vs")[0],String(C.exact)])}
 if(C.flagged)r.push([t("triage"),triTxt(C.to_check,C.probably_fine)]);
 if(C.divergent)r.push([t("divergent"),String(C.divergent)]);
 kv("kv-r",r);
 seg("f-status",t("status"),[["open",t("open")],["ready",t("ready")],["flagged",t("flagged")],["divergent",t("divF")],["decided",t("decidedF")],["all",t("all")]],F.status,function(v){F.status=v;renderReg()});
 seg("f-lang",t("language"),[["all","FR+IT"],["fr","FR"],["it","IT"]],F.lang,function(v){F.lang=v;if(v!=="all")focusL=v;renderReg();renderCase()});
 var fs=$("f-fam");fs.innerHTML="";fs.appendChild(new Option(t("allFam")+" ("+D.families.length+")",""));
 D.families.forEach(function(f){var o=new Option(f[2]+" · "+f[1],f[0]);o.title=t("family")+" "+f[0];fs.appendChild(o)});fs.value=F.fam;$("f-q").placeholder=t("search");
 $("h-mark").textContent=t("mark");$("h-no").textContent=t("no");$("h-prod").textContent=t("product");$("h-chg").textContent=t("change");
 $("x-xlf").textContent=t("xlf");$("x-json").textContent=t("json");$("x-copy").textContent=t("copy");$("x-imp").textContent=t("imp");$("x-where").textContent=t("where");
 $("legend").textContent=t("legend");
 $("legend2").textContent=t("triHead")+" "+["T1","T2","T3","T4"].map(function(r){return t("rd"+r)}).join(" · ");progress()}
function seg(id,label,opts,cur,fn){var s=$(id);s.innerHTML='<span class="k">'+esc(label)+"</span>";
 opts.forEach(function(o){var b=document.createElement("button");b.type="button";b.className="tb";b.textContent=o[1];b.setAttribute("aria-pressed",o[0]===cur);
  b.onclick=function(){s.querySelectorAll("button").forEach(function(x){x.setAttribute("aria-pressed",x===b)});fn(o[0])};s.appendChild(b)})}
function progress(){var n,m;if(TAB==="audit"&&AU){n=AU.rows.filter(function(r){return aDecided(r)}).length;m=AU.rows.length}
 else{n=ITEMS.filter(function(it){return dec(it)}).length;m=ITEMS.length}$("progress").innerHTML="<b>"+n+"/"+m+"</b> "+esc(t("decided"))}
// ------------------------------------------------------------------ tabs
function setTab(tb){if(tb==="audit"&&!AU)tb="drafts";TAB=tb;chrome();
 if(TAB==="audit"){renderAudit();try{if(location.hash!=="#audit")history.replaceState(null,"","#audit")}catch(e){}}
 else{renderReg();if(sel){markSel(true);renderCase()}}}
$("t-audit").onclick=function(){setTab("audit")};$("t-drafts").onclick=function(){setTab("drafts")};
document.querySelector(".tabs").addEventListener("keydown",function(e){if(e.key==="ArrowRight"||e.key==="ArrowLeft"){e.preventDefault();setTab(TAB==="audit"?"drafts":"audit");$(TAB==="audit"?"t-audit":"t-drafts").focus()}});
// ------------------------------------------------------------------ register audit
var AF={show:"all",lang:"all",kind:"all"};
function aDec(r){return SA[r.rid]||{}}
function aDecided(r){var d=SA[r.rid];return !!(d&&(d.right||d.action))}
function chromeAudit(){var m=AU.meta;
 kv("kv-l",[[t("aSnap"),ddate(m.date)],[t("aChecked"),m.n_limitations!=null?String(m.n_limitations):"—"],
  [t("aFindings"),(m.total||m.findings)+(m.by_kind?" ("+Object.keys(m.by_kind).map(function(k){return m.by_kind[k]+" "+(t("kinds")[k]||k)}).join(", ")+")":"")],[t("aCalls"),String(m.model_calls||0)]]);
 var r=[[t("aKnown"),(m.known_found!=null?m.known_found:m.known_ids.length)+" / "+(m.known_of!=null?m.known_of:m.known_ids.length),"big"]];
 if(m.precision!=null)r.push([t("aReal"),(m.real!=null?m.real+" "+t("of")+" "+m.findings+" · ":"")+m.precision.toFixed(1)+"%"+(m.ci?" (95% CI "+m.ci[0]+"–"+m.ci[1]+")":"")]);
 if(m.held!=null)r.push([t("aHeld"),m.held_real+" "+t("of")+" "+m.held+" "+t("real")]);
 kv("kv-r",r);
 $("a-lead").textContent=fmt(t("aLead"),{d:ddate(m.date)});
 seg("a-show",t("aShow"),[["known",t("aKnownF")+" ("+m.known_rows+")"],["all",t("aAllF")+" ("+AU.rows.length+")"],["open",t("aOpenF")],["decided",t("aDecF")]],AF.show,function(v){AF.show=v;renderAudit()});
 seg("a-lang",t("language"),[["all","FR+IT"],["fr","FR"],["it","IT"]],AF.lang,function(v){AF.lang=v;renderAudit()});
 var ks=[["all",t("all")]];["number","unit","language","editorial"].forEach(function(k){var n=AU.rows.filter(function(r){return r.kind===k}).length;if(n)ks.push([k,t("kinds")[k]+" ("+n+")"])});
 AU.rows.forEach(function(r){if(!ks.some(function(k){return k[0]===r.kind}))ks.push([r.kind,r.kind])});
 seg("a-kind",t("aKindF"),ks,AF.kind,function(v){AF.kind=v;renderAudit()});
 $("ah-no").textContent=t("no");$("ah-lim").textContent=t("aLim");$("ah-kind").textContent=t("aKind")+" · "+t("aOdd");$("ah-right").textContent=t("aRight");$("ah-act").textContent=t("aAction");
 $("a-json").textContent=t("json");$("a-csv").textContent=t("aCsv");$("a-imp").textContent=t("imp");$("a-where").textContent=t("where");
 $("legend").textContent=t("aLegend");$("legend2").textContent="";progress()}
function aOk(r){if(AF.lang!=="all"&&r.lang!==AF.lang)return false;if(AF.kind!=="all"&&r.kind!==AF.kind)return false;
 switch(AF.show){case "known":return r.known;case "open":return !aDecided(r);case "decided":return aDecided(r);default:return true}}
function snipHTML(r,L){var s=r.snip[L];if(!s||!s.length)return '<span class="na">'+esc(r.lang===L||L==="de"?t("aNoSnip"):"—")+"</span>";
 var h=s.map(function(x){return x[1]===2?'<span class="v2">'+esc(x[0])+"</span>":x[1]===1?'<span class="v1">'+esc(x[0])+"</span>":esc(x[0])}).join("");
 return '<div class="snip'+(r.src[L]==="snapshot"?" src-s":"")+'" lang="'+L+'"'+(r.src[L]==="snapshot"?' title="'+esc(t("aSnapSrc"))+'"':"")+">"+h+"</div>"}
function aRow(r){var d=aDec(r),cell=function(L){var odd=r.odd===L;return '<td data-l="'+L.toUpperCase()+(odd?" · "+esc(t("oddLbl")):"")+'"'+(odd?' class="odd"':"")+">"+(odd?'<span class="oddl">'+esc(t("oddLbl"))+"</span>":"")+snipHTML(r,L)+"</td>"};
 var mk=(r.known?'<span class="mk r">[k]</span>':"")+(aDecided(r)?'<span class="mk">[d]</span>':"")||'<span class="mk o">[ ]</span>';
 var odd=r.odd==="unclear"?t("aUnclear"):String(r.odd||"—").toUpperCase();
 var h='<tr data-rid="'+esc(r.rid)+'"><td data-l="'+esc(t("no"))+'">'+mk+"<br>"+esc(r.no||"")+"</td>"+
  '<td class="lim" data-l="'+esc(t("aLim"))+'"><b>'+esc(r.product||r.lim)+'</b><span class="code" title="'+esc(r.desc)+'">'+esc(r.lim)+"</span>"+
   (r.since?'<span class="sub2">'+esc(fmt(t("aSince"),{d:ddate(r.since),n:r.seen||"?"}))+"</span>":"")+"</td>"+
  '<td data-l="'+esc(t("aKind"))+'">'+esc((t("kinds")[r.kind]||r.kind))+" · "+esc((r.lang||"").toUpperCase())+'<br><span class="oddl" style="display:inline">'+esc(t("aOdd"))+": "+esc(odd)+"</span>"+
   (r.found?'<span class="sub2">'+esc(fmt(t("aFoundL"),{F:t("lname")[r.found]||r.found}))+"</span>":"")+
   (r.fix?'<span class="sub2">'+esc(fmt(t("aFix"),{a:r.fix[0],b:r.fix[1]}))+"</span>":"")+
   (r.expl&&r.expl.length?'<span class="sub2">'+esc(fmt(t("aExpl"),{x:r.expl.join(", ")}))+"</span>":"")+"</td>"+
  cell("de")+cell("fr")+cell("it");
 h+='<td data-l="'+esc(t("aRight"))+'"><select data-a="right" aria-label="'+esc(t("aRight"))+'">'+[["",""],["DE","DE"],["FR","FR"],["IT","IT"],["unclear",t("aUnclear")]].map(function(o){
   return '<option value="'+o[0]+'"'+(d.right===o[0]?" selected":"")+">"+esc(o[1]||"—")+"</option>"}).join("")+"</select></td>";
 var acts=t("acts");
 h+='<td data-l="'+esc(t("aAction"))+'"><select data-a="action" aria-label="'+esc(t("aAction"))+'"><option value="">—</option>'+["Berichtigung","GÄL","none","unclear"].map(function(v){
   return '<option value="'+esc(v)+'"'+(d.action===v?" selected":"")+">"+esc(acts[v])+"</option>"}).join("")+"</select>"+
  (r.sug?'<div class="sug">'+esc(t("aSug"))+": "+esc(acts[r.sug]||r.sug)+"</div>":"")+
  '<textarea data-a="note" aria-label="'+esc(t("aNote"))+'" placeholder="'+esc(t("aNote"))+'">'+esc(d.note||"")+"</textarea>"+
  '<div class="stt">'+esc(d.at?t("savedAt")+" · "+d.at.slice(0,16).replace("T"," "):t("openSt"))+"</div></td></tr>";
 return h}
function renderAudit(){if(!AU){$("p-audit").innerHTML='<p class="empty">'+esc(t("aNoFile"))+"</p>";return}
 var tb=document.querySelector("#aud tbody"),rows=AU.rows.filter(aOk),kn=rows.filter(function(r){return r.known}),ot=rows.filter(function(r){return !r.known}),h="",m=AU.meta;
 if(kn.length)h+='<tr class="grp"><td colspan="8"><span class="mk r">[k]</span>'+esc(fmt(t("aKnownHead"),{k:m.known_found!=null?m.known_found:m.known_ids.length,n:m.known_of!=null?m.known_of:m.known_ids.length}))+"</td></tr>"+kn.map(aRow).join("");
 if(ot.length)h+='<tr class="grp"><td colspan="8">'+esc(t("aOtherHead"))+"</td></tr>"+ot.map(aRow).join("");
 tb.innerHTML=h||'<tr><td colspan="8" class="empty">'+esc(t("aNone"))+"</td></tr>";
 $("a-shown").textContent=rows.length+" "+t("aShown");progress()}
document.querySelector("#aud tbody").addEventListener("change",function(e){var f=e.target.closest("[data-a]");if(!f)return;aSet(f)});
document.querySelector("#aud tbody").addEventListener("input",function(e){var f=e.target.closest("textarea[data-a]");if(f)aSet(f)});
function aSet(f){var tr=f.closest("tr[data-rid]"),rid=tr.dataset.rid,d=SA[rid]||{};d[f.dataset.a]=f.value;
 if(!d.right&&!d.action&&!d.note){delete SA[rid]}else{d.at=new Date().toISOString();SA[rid]=d}saveA();
 tr.querySelector(".stt").textContent=SA[rid]?t("savedAt")+" · "+SA[rid].at.slice(0,16).replace("T"," "):t("openSt");
 var mk=tr.cells[0],r=AU.rows.filter(function(x){return x.rid===rid})[0];mk.innerHTML=((r.known?'<span class="mk r">[k]</span>':"")+(aDecided(r)?'<span class="mk">[d]</span>':"")||'<span class="mk o">[ ]</span>')+"<br>"+esc(r.no||"");progress()}
function auditExport(){if(!AU)return {};var o={};AU.rows.forEach(function(r){var d=SA[r.rid];if(d)o[r.rid]={limitation:r.lim,product:r.product,lang:r.lang,kind:r.kind,odd_one_out:r.odd,known:r.known,right:d.right||"",action:d.action||"",note:d.note||"",at:d.at}});return o}
function csvCell(s){s=String(s==null?"":s);return /[",\n;]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s}
function snipText(r,L){return (r.snip[L]||[]).map(function(x){return x[0]}).join("")}
$("a-csv").onclick=function(){var head=["rank","limitation","product","kind","lang","odd_one_out","known","de","fr","it","right","action","note","decided_at"];
 var lines=[head.join(",")].concat(AU.rows.map(function(r){var d=SA[r.rid]||{};return [r.rank,r.lim,r.product,r.kind,r.lang,r.odd,r.known?"yes":"no",snipText(r,"de"),snipText(r,"fr"),snipText(r,"it"),d.right||"",d.action||"",d.note||"",d.at||""].map(csvCell).join(",")}));
 download("gleichlaut-audit-"+AU.meta.date+"-decisions.csv","﻿"+lines.join("\r\n")+"\r\n","text/csv");$("a-msg").textContent=t("dl")+": CSV"};
$("a-json").onclick=function(){download("gleichlaut-decisions-"+M.run+".json",JSON.stringify(payload(),null,1),"application/json");$("a-msg").textContent=t("dl")+": JSON"};
// ------------------------------------------------------------------ register (drafts)
var F={status:"open",lang:"all",fam:"",q:""},sel=null,focusL="fr",VIS=[];
function langs(g){return ["fr","it"].filter(function(L){return g.items[L]&&(F.lang==="all"||F.lang===L)})}
function okItem(it){var d=dec(it);switch(F.status){case "open":return !d;case "ready":return it.status==="ready";case "flagged":return it.status==="flagged";
 case "divergent":return oldIssue(it);case "decided":return !!d;default:return true}}
function renderReg(){var tb=document.querySelector("#reg tbody"),h="";VIS=[];
 G.forEach(function(g){var Ls=langs(g);if(!Ls.length)return;if(F.fam&&g.family!==F.fam)return;
  if(F.q&&(g.product+" "+g.code+" "+g.pair+" "+g.no).toLowerCase().indexOf(F.q)<0)return;
  if(!Ls.some(function(L){return okItem(g.items[L])}))return;VIS.push(g);
  var mk=(F.lang==="all"?["fr","it"]:[F.lang]).map(function(L){return mark(g.items[L])[0]}).join("");
  h+='<tr data-pair="'+esc(g.pair)+'" aria-selected="'+(sel===g)+'"><td>'+mk+'</td><td>'+g.no+'</td><td class="prd" title="'+esc(g.product+" · "+g.code)+'">'+esc(g.product)+'<span class="pc">'+esc(g.code)+"</span>"+
   '</td><td class="chg" title="'+esc(g.sum)+'">'+esc(g.sum)+"</td></tr>"});
 tb.innerHTML=h||'<tr><td colspan="4" class="empty">'+esc(t("none"))+"</td></tr>";
 $("shown").textContent=VIS.length+" "+t("shown");
 if(VIS.indexOf(sel)<0){sel=VIS[0]||null;if(sel)markSel();renderCase()}}
function markSel(scroll){document.querySelectorAll("#reg tbody tr").forEach(function(r){var on=sel&&r.dataset.pair===sel.pair;r.setAttribute("aria-selected",on);
 if(on&&scroll){var w=$("reg-wrap"),top=r.offsetTop-w.offsetTop,hh=28;if(top-hh<w.scrollTop)w.scrollTop=top-hh;else if(top+r.offsetHeight>w.scrollTop+w.clientHeight)w.scrollTop=top+r.offsetHeight-w.clientHeight}})}
document.querySelector("#reg tbody").addEventListener("click",function(e){var r=e.target.closest("tr[data-pair]");if(!r)return;
 sel=G.filter(function(g){return g.pair===r.dataset.pair})[0];markSel();renderCase();if(window.innerWidth<=900)$("case").scrollIntoView()});
$("f-fam").onchange=function(){F.fam=this.value;renderReg()};
$("f-q").oninput=function(){F.q=this.value.trim().toLowerCase();renderReg()};
function move(d){if(!VIS.length)return;var i=VIS.indexOf(sel);i=Math.max(0,Math.min(VIS.length-1,(i<0?0:i+d)));sel=VIS[i];markSel(true);renderCase()}
function refreshRow(g){var r=document.querySelector('#reg tr[data-pair="'+g.pair+'"]');if(r)r.cells[0].innerHTML=(F.lang==="all"?["fr","it"]:[F.lang]).map(function(L){return mark(g.items[L])[0]}).join("")}
// ------------------------------------------------------------------ text rendering
function chip(s,edit){var slot=(s[3]||"").replace(/[⟨⟩]/g,""),m=s[2]==="model";
 var tip=(m?"number written by the model: check it":"number placed by code from the German")+(slot?" (slot "+slot+")":"");
 return '<span class="n'+(m?" m":"")+'" title="'+esc(tip)+'">'+esc(s[1])+(slot?"<sup"+(edit?' contenteditable="false"':"")+">"+esc(slot)+"</sup>":"")+"</span>"}
function segs(S,ctx,edit){var h="";S.forEach(function(s,i){var k=s[0],tx=s[1];
 if(s.length===4){var c=chip(s,edit);h+=k==="i"?"<ins>"+c+"</ins>":k==="d"?"<del>"+c+"</del>":c;return}
 if(k==="e"){if(ctx&&tx.length>260){var a=tx.slice(0,90).replace(/\s+\S*$/,""),b=tx.slice(-90).replace(/^\S*\s+/,"");
   h+=(i===0?"":esc(a))+'<span class="gap" contenteditable="false">…</span>'+(i===S.length-1?"":esc(b))}else h+=esc(tx);return}
 if(k==="i")h+="<ins>"+esc(tx)+"</ins>";
 else h+="<del"+(s[2]==="s"?' class="s"':"")+(edit?' contenteditable="false"':"")+">"+esc(tx)+"</del>"});return h}
function readEd(el){var c=el.cloneNode(true);c.querySelectorAll("del,sup,.gap").forEach(function(x){x.remove()});return c.textContent.replace(/ /g," ")}
// ------------------------------------------------------------------ case
var ctxMode=true;
function LN(L){return t(L)}
function stLabel(it){return it.status==="ready"?(oldIssue(it)?t("readyAttn"):t("lready")):it.status==="flagged"?t("lflagged"):t("lhuman")}
function langMsg(it,o){var a=t("adj")[it.lang]||LN(it.lang),f=t("lname")[o.f]||o.f;return fmt(t("oldLang"),{A:a,F:f})}
function notice(it){var p=[],lang=false;
 (it.old||[]).forEach(function(o){if(o.k==="language"){lang=true;var um=o.f?langMsg(it,o):o.t;p.push('<p><span class="mk">[≠]</span>'+esc(um)+"</p>"+(o.f&&o.t!==um?'<p lang="'+it.lang+'">'+esc(o.t)+"</p>":""))}});
 if(it.banner&&!(lang&&(it.old||[]).every(function(o){return o.k==="language"})))p.push("<p>"+(lang?"":"<span class=\"mk\">[≠]</span>")+esc(it.banner)+"</p>");
 if(it.corr)p.push("<p>"+(p.length?"":"<span class=\"mk\">[≠]</span>")+esc(it.corr)+"</p>");
 return p.length?'<div class="notice'+(lang?" lang":"")+'" role="note">'+p.join("")+"</div>":""}
function curText(it){var e=S.edits[it.key];return e!=null?e:it.draft}
function caseHTML(g,live){var Ls=langs(g),one=Ls.length<2?" one":"",h="";
 var keys=["fr","it"].filter(function(L){return g.items[L]}).map(function(L){return g.items[L].key}).join(", ");
 h+="<h2>"+esc(g.product)+'</h2><p class="ref">'+esc(t("limitation"))+" "+esc(g.code)+" · SL "+esc(g.snap_old)+" → "+esc(g.snap_new)+" · "+esc(t("no"))+" "+g.no+"</p>"+
  '<details class="ids"><summary>'+esc(t("ids"))+"</summary> "+esc(t("family"))+" "+esc(g.family)+(FAML[g.family]?" ("+esc(FAML[g.family])+")":"")+" · "+esc(t("pair"))+" "+esc(g.pair)+" · "+esc(t("itemsL"))+" "+esc(keys)+"</details>";
 h+='<section class="sec"><div class="sl"><span class="no">1</span><span class="t">'+esc(t("s1"))+"</span>"+(live?'<button class="tb sp" type="button" id="ctx">'+esc(ctxMode?t("ctxA"):t("ctxF"))+"</button>":"")+
  '</div><div class="txt de" lang="de">'+segs(g.de,live&&ctxMode,false)+"</div></section>";
 h+='<section class="sec"><div class="sl"><span class="no">2</span><span class="t">'+esc(t("s2"))+'</span></div><div class="drafts'+one+'">';
 Ls.forEach(function(L){var it=g.items[L],ed=S.edits[it.key];
  h+='<div class="dr" data-lang="'+L+'"><div class="dl"><span class="ln" title="'+esc(it.key)+'">'+esc(LN(L))+'</span>·<span class="st'+(it.status==="flagged"||oldIssue(it)?" r":"")+'">'+esc(stLabel(it))+"</span>"+
   (it.status==="flagged"?'<span class="tri">'+triHTML(it.tri[0],it.tri[1])+"</span>":"")+(it.rule_only?'<span class="key">rules</span>':"")+
   (it.status==="ready"?'<span class="cap">'+esc(t("codeOnly"))+"</span>":"")+"</div>"+notice(it);
  if(it.status==="human")h+='<p class="human">'+esc(it.reason&&!/rewritten|60/.test(it.reason)?t("humanShort"):t("humanTxt"))+(it.ratio!=null?" ("+it.ratio+"%)":"")+".</p>"+(it.reason?'<p class="ref">'+esc(it.reason)+"</p>":"")+"<p class=\"human\" style=\"color:var(--ink2)\">"+esc(t("humanPrev"))+"</p>";
  var body=ed!=null?esc(ed):segs(it.segs,false,live);
  h+='<div class="txt'+(live?" ed":"")+'" lang="'+L+'"'+(live?' contenteditable="true" spellcheck="true" role="textbox" aria-multiline="true" aria-label="'+esc(LN(L))+'" data-key="'+esc(it.key)+'"':"")+">"+body+"</div>";
  if(live)h+='<div class="edmeta" data-meta="'+esc(it.key)+'">'+edmeta(it.key)+"</div>";
  h+="</div>"});
 h+="</div></section>";
 h+='<section class="sec"><div class="sl"><span class="no">3</span><span class="t">'+esc(t("s3"))+"</span></div>";
 Ls.forEach(function(L){var it=g.items[L];h+='<div class="tbl"><table class="ledger"><caption>'+esc(LN(L))+(it.status==="flagged"?'<span class="tri">'+triHTML(it.tri[0],it.tri[1])+"</span>":"")+"</caption>";
  if(!it.ledger.length){h+='<tbody><tr><td class="na">'+esc(t("noChecks"))+"</td></tr></tbody></table></div>";return}
  h+="<thead><tr><th>"+esc(t("check"))+"</th><th>"+esc(t("result"))+"</th><th>"+esc(t("finding"))+"</th></tr></thead><tbody>";
  it.ledger.forEach(function(r){var st=r[2],res=st==="pass"?t("pass"):st==="fail"?t("fail"):t("na"),cls=st==="fail"?"FAIL":st==="pass"?"":"na";
   var fd=r[3].map(function(f){var p="<p>"+esc(f.t)+(f.c&&it.corr_note?'<span class="cn">[≠] '+esc(it.corr_note)+"</span>":"")+"</p>";
    return f.r?'<details class="pf" title="'+esc(t("rd"+f.r))+'"><summary>'+esc(t("pf"))+" · "+esc(t("r"+f.r))+"</summary>"+p+"</details>":p}).join("");
   if(!fd&&st!=="fail")fd='<span class="na">—</span>';
   if(r[4])fd+="<details><summary>"+esc(t("raw"))+" · "+esc(r[5])+"</summary><div>"+esc(r[4])+"</div></details>";
   h+='<tr><td class="chk" title="'+esc(r[5])+'">'+esc(r[1])+'</td><td class="res '+cls+'">'+esc(res)+'</td><td class="fd" lang="'+L+'">'+fd+"</td></tr>"});
  h+="</tbody></table></div>"});
 h+="</section>";
 if(live){h+='<section class="sec"><div class="sl"><span class="no">4</span><span class="t">'+esc(t("s4"))+'</span></div><div class="decs'+one+'">';
  Ls.forEach(function(L){var it=g.items[L],d=dec(it)||{};
   h+='<div class="dec'+(L===focusL||Ls.length<2?" focus":"")+'" data-lang="'+L+'" data-key="'+esc(it.key)+'"><div class="dl"><span class="ln">'+esc(LN(L))+'</span><span class="key">'+esc(stLabel(it))+'</span></div><div class="btns">'+
    [["accept","(1) "+t("accept")],["accept-edited","(2) "+t("acceptEd")],["send-back","(3) "+t("sendBack")]].map(function(b){
     return '<button class="box" type="button" data-d="'+b[0]+'" aria-pressed="'+(d.decision===b[0])+'">'+esc(b[1])+"</button>"}).join("")+"</div>"+
    "<label>"+esc(t("reason"))+'<select data-f="reason">'+t("reasons").map(function(r,i){var v=TX.en.reasons[i];return '<option value="'+esc(v)+'"'+(d.reason===v?" selected":"")+">"+esc(r||"—")+"</option>"}).join("")+"</select></label>"+
    "<label>"+esc(t("note"))+'<textarea data-f="note" lang="'+L+'">'+esc(d.note||"")+"</textarea></label>"+
    '<div class="stt">'+esc(d.decision?t("savedAt")+" · "+d.at.slice(0,16).replace("T"," "):t("openSt"))+"</div></div>"});
  h+='</div><div class="save"><button class="box primary" type="button" id="savenext">'+esc(t("saveNext"))+'</button><span class="hint">'+esc(t("keys"))+"</span></div></section>"}
 return h}
function edmeta(key){var it=byKey[key],e=S.edits[key]!=null;
 return (e?"<span>"+esc(t("edited"))+'</span><button class="tb" type="button" data-reset="'+esc(key)+'">'+esc(t("reset"))+"</button>":"<span>"+esc(t("editHint"))+"</span>")+
  ((it.status!=="human"||e)?'<button class="tb" type="button" data-copy="'+esc(key)+'">'+esc(t("copyTxt"))+'</button><span class="cpmsg" aria-live="polite"></span>':"")}
function renderCase(){var c=$("case");if(!sel){c.innerHTML='<p class="empty">'+esc(t("none"))+"</p>";return}
 try{if(TAB==="drafts"&&location.hash.slice(1)!==sel.pair)history.replaceState(null,"","#"+sel.pair)}catch(e){}
 var Ls=langs(sel);if(Ls.indexOf(focusL)<0)focusL=Ls[0];c.innerHTML=caseHTML(sel,true);wire(c)}
function copyText(s,ok,fail){var box=$("clipbox");
 function fallback(){try{box.value=s;box.select();if(document.execCommand&&document.execCommand("copy")){ok();return}}catch(e){}fail()}
 try{if(navigator.clipboard&&navigator.clipboard.writeText&&window.isSecureContext!==false){navigator.clipboard.writeText(s).then(ok,fallback)}else fallback()}catch(e){fallback()}}
function wire(c){
 var b=$("ctx");if(b)b.onclick=function(){ctxMode=!ctxMode;renderCase()};
 c.querySelectorAll(".ed").forEach(function(el){var key=el.dataset.key,it=byKey[key];
  el.addEventListener("keydown",function(e){if(e.key==="Enter"&&!(e.metaKey||e.ctrlKey))e.preventDefault()});
  el.addEventListener("paste",function(e){e.preventDefault();var tx=(e.clipboardData||window.clipboardData).getData("text").replace(/\s*\n\s*/g," ");document.execCommand("insertText",false,tx)});
  el.addEventListener("focus",function(){setFocus(it.lang)});
  el.addEventListener("input",function(){var v=readEd(el);if(v===it.draft||(it.status==="human"&&v===plain(it.segs,false)))delete S.edits[key];else S.edits[key]=v;save();
   var m=c.querySelector('[data-meta="'+key+'"]');if(m)m.innerHTML=edmeta(key)})});
 c.addEventListener("click",function(e){var r=e.target.closest("[data-reset]");if(r){delete S.edits[r.dataset.reset];var d=S.dec[r.dataset.reset];if(d&&d.decision==="accept-edited"){delete S.dec[r.dataset.reset]};save();renderCase();refreshRow(sel);progress();return}
  var cp=e.target.closest("[data-copy]");if(cp){var it=byKey[cp.dataset.copy],m=cp.parentNode.querySelector(".cpmsg"),tx=curText(it);
   copyText(tx,function(){m.textContent=t("copiedTxt")},function(){var el=c.querySelector('.ed[data-key="'+it.key+'"]');if(el){var rg=document.createRange();rg.selectNodeContents(el);var sl=window.getSelection();sl.removeAllRanges();sl.addRange(rg)}m.textContent=t("copySel")});return}
  var bt=e.target.closest(".dec button[data-d]");if(bt){var dv=bt.closest(".dec");setFocus(dv.dataset.lang);decide(dv.dataset.lang,bt.dataset.d)}});
 c.querySelectorAll(".dec").forEach(function(dv){dv.addEventListener("focusin",function(){setFocus(dv.dataset.lang)});
  dv.querySelectorAll("[data-f]").forEach(function(f){f.addEventListener(f.tagName==="SELECT"?"change":"input",function(){var k=dv.dataset.key,d=S.dec[k];
   if(d){d[f.dataset.f]=f.value;save()}else{pend[k]=pend[k]||{};pend[k][f.dataset.f]=f.value}})})});
 var sn=$("savenext");if(sn)sn.onclick=saveNext}
var pend={},byKey={};ITEMS.forEach(function(it){byKey[it.key]=it});
function setFocus(L){if(!sel||!sel.items[L]||langs(sel).indexOf(L)<0)return;focusL=L;document.querySelectorAll(".dec").forEach(function(d){d.classList.toggle("focus",d.dataset.lang===L)})}
function decide(L,v){var it=sel&&sel.items[L];if(!it)return;var dv=document.querySelector('.dec[data-lang="'+L+'"]'),k=it.key;
 if(v==="accept-edited"&&S.edits[k]==null){var st=dv.querySelector(".stt");st.textContent=t("noEdit");var ed=document.querySelector('.ed[data-key="'+k+'"]');if(ed)ed.focus();return}
 var cur=S.dec[k];if(cur&&cur.decision===v){delete S.dec[k]}
 else{var reason=dv.querySelector('[data-f="reason"]').value,note=dv.querySelector('[data-f="note"]').value;
  S.dec[k]={decision:v,lang:L,status:it.status,edited:S.edits[k]!=null,text:v==="accept-edited"?S.edits[k]:(it.status==="human"?null:it.draft),reason:reason,note:note,at:new Date().toISOString()}}
 delete pend[k];save();
 dv.querySelectorAll("button[data-d]").forEach(function(b){b.setAttribute("aria-pressed",!!S.dec[k]&&S.dec[k].decision===b.dataset.d)});
 dv.querySelector(".stt").textContent=S.dec[k]?t("savedAt")+" · "+S.dec[k].at.slice(0,16).replace("T"," "):t("openSt");refreshRow(sel);progress()}
function saveNext(){save();var old=sel,i=VIS.indexOf(old);renderReg();var j=VIS.indexOf(old);
 sel=j>=0?(VIS[j+1]||old):(VIS[Math.max(0,i)]||VIS[VIS.length-1]||null);markSel(true);renderCase();var c=$("case");if(c.getBoundingClientRect().top<0)c.scrollIntoView()}
// ------------------------------------------------------------------ keyboard (drafts tab)
document.addEventListener("keydown",function(e){if(TAB!=="drafts")return;var tg=e.target,typing=tg.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(tg.tagName);
 if(e.key==="Enter"&&(e.metaKey||e.ctrlKey)){e.preventDefault();saveNext();return}
 if(e.key==="Escape"&&typing){tg.blur();return}
 if(typing||e.altKey||e.metaKey||e.ctrlKey)return;
 if(tg.closest&&tg.closest(".tabs"))return;
 var k=e.key;
 if(k==="j"||k==="ArrowDown"){e.preventDefault();move(1)}else if(k==="k"||k==="ArrowUp"){e.preventDefault();move(-1)}
 else if(k==="Enter"&&tg.closest&&!tg.closest("button,a,summary")){e.preventDefault();$("case").focus();$("case").scrollIntoView({block:"start"})}
 else if(k==="f"||k==="i"){setFocus(k==="f"?"fr":"it")}
 else if(k==="1"||k==="2"||k==="3"){if(sel){var L=langs(sel).indexOf(focusL)>=0?focusL:langs(sel)[0];decide(L,["accept","accept-edited","send-back"][+k-1])}}});
// ------------------------------------------------------------------ export / import
function payload(){return {run:M.run,model:M.model,pipeline:M.pipeline,run_sha256:M.run_sha256,items_sha256:M.items_sha256,exported_at:new Date().toISOString(),
 decisions:S.dec,edits:S.edits,audit_date:AU?AU.meta.date:null,audit:SA,audit_rows:auditExport()}}
function download(name,text,type){var u=URL.createObjectURL(new Blob([text],{type:type})),a=document.createElement("a");a.href=u;a.download=name;document.body.appendChild(a);a.click();
 setTimeout(function(){URL.revokeObjectURL(u);a.remove()},500)}
function x(s){return esc(s).replace(/'/g,"&apos;")}
function inl(s,a,b,spans,open){var out="",pos=a;(spans||[]).forEach(function(sp){var p=Math.max(sp[0],a),q=Math.min(sp[1],b);if(p>=q||p<pos)return;
  out+=x(s.slice(pos,p))+open(sp)+x(s.slice(p,q))+"</mrk>";pos=q});return out+x(s.slice(pos,b))}
function note(id,cat,ap,pr,text){return '<note id="'+id+'" category="'+cat+'"'+(ap?' appliesTo="'+ap+'"':"")+' priority="'+pr+'">'+x(text)+"</note>"}
function xliff(L){var trg=L==="fr"?"fr-CH":"it-CH",u=[],X=D.xn[L],nd=0,colon=L==="fr"?" : ":": ";
 ITEMS.forEach(function(it){if(it.lang!==L)return;var g=it.g,d=dec(it)||null,st=it.status==="human"?["initial","gleichlaut:human"]:["translated","gleichlaut:"+it.status],text=it.status==="human"?null:it.draft,edited=false;
  if(d&&(d.decision==="accept"||d.decision==="accept-edited")&&(it.status!=="human"||d.text)){st=["reviewed",d.decision==="accept-edited"?"gleichlaut:accepted-edited":"gleichlaut:accepted"];
   if(d.decision==="accept-edited"&&d.text){text=d.text;edited=true}}
  else if(d&&d.decision==="send-back")st=["initial","gleichlaut:sent-back"];
  if(d)nd++;
  var notes=it.xn.map(function(n){return note(n[0],n[1],n[2],n[3],n[4])}).join("");
  notes+=note("de-old","context:previous-source","source",5,fmt(X.prev_de,{t:g.deOld}).replace(" : ",colon));
  notes+=note("tgt-old","context:previous-target","target",5,fmt(X.prev_tgt,{t:plain(it.segs,true)}).replace(" : ",colon));
  notes+=note("product","context:product",null,5,fmt(X.product,{product:g.product,code:it.cud,old:g.snap_old,"new":g.snap_new}).replace(/ ; /g," ; "));
  if(d){var why=[d.reason,d.note].filter(Boolean).join("; ");notes+=note("review","gleichlaut:review","target",1,fmt(X.review,{d:X.dec[d.decision]||d.decision}).replace(" : ",colon)+" ("+d.at+")"+(why?colon+why:""))}
  var src=g.deNew,beads=text==null?it.bd.map(function(b){return [b[0],b[1],0,0]}):edited?[[0,src.length,0,text.length]]:it.bd,nums=edited?[]:it.nm,c=0,n=0,sx="";
  beads.forEach(function(b,k){sx+='<segment id="s'+(k+1)+'" state="'+st[0]+'" subState="'+st[1]+'"><source>'+inl(src,b[0],b[1],g.ch,function(){c++;return '<mrk id="c'+c+'" type="gleichlaut:changed">'})+"</source>"+
   (text!=null?"<target>"+inl(text,b[2],b[3],nums,function(sp){n++;var code=sp[2]!=="model";return '<mrk id="t'+n+'"'+(code?' translate="no"':"")+' type="gleichlaut:'+(code?"code":"model")+'-number"'+(sp[3]?' value="'+x(sp[3])+'"':"")+">"})+"</target>":"")+"</segment>"});
  u.push('<unit id="'+x(it.key)+'" name="'+x(it.cud)+'"><notes>'+notes+"</notes>"+sx+"</unit>")});
 return '<?xml version="1.0" encoding="UTF-8"?>\n<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" version="2.1" srcLang="de-CH" trgLang="'+trg+'"><file id="f1" original="gleichlaut:'+x(M.run)+'">'+
  "<notes>"+note("about","gleichlaut:about",null,1,X.about).replace(' priority="1"',"")+note("states","gleichlaut:states",null,1,X.states).replace(' priority="1"',"")+
  note("provenance","gleichlaut:provenance",null,1,X.prov).replace(' priority="1"',"")+note("review","gleichlaut:review",null,1,fmt(X.reviewed,{n:nd})+" · "+new Date().toISOString()).replace(' priority="1"',"")+
  "</notes>"+u.join("")+"</file></xliff>\n"}
function msg(s){$("x-msg").textContent=s}
$("x-xlf").onclick=function(){var Ls=F.lang==="all"?["fr","it"]:[F.lang];Ls=Ls.filter(function(L){return ITEMS.some(function(it){return it.lang===L})});
 Ls.forEach(function(L,i){setTimeout(function(){download("gleichlaut-"+M.run+"-de-CH_"+(L==="fr"?"fr-CH":"it-CH")+"-reviewed.xlf",xliff(L),"application/xliff+xml")},i*400)});
 msg(t("dl")+": "+Ls.map(function(L){return "XLIFF 2.1 "+L.toUpperCase()}).join(", "))};
$("x-json").onclick=function(){download("gleichlaut-decisions-"+M.run+".json",JSON.stringify(payload(),null,1),"application/json");msg(t("dl")+": JSON")};
$("x-copy").onclick=function(){var s=JSON.stringify(payload(),null,1),box=$("copybox");
 function fallback(){box.hidden=false;box.value=s;box.focus();box.select();msg(t("selcopy"))}
 try{if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(s).then(function(){box.hidden=true;msg(t("copied"))},fallback)}else fallback()}catch(e){fallback()}};
function importDecisions(o){var nd=0,na=0,note="";
 if(!o||typeof o!=="object"||!(o.decisions||o.audit))return t("impBad");
 if(o.decisions){if(o.run_sha256&&o.run_sha256!==M.run_sha256)note=" "+t("impRun");
  else{Object.keys(o.decisions).forEach(function(k){if(byKey[k]){S.dec[k]=o.decisions[k];nd++}});Object.keys(o.edits||{}).forEach(function(k){if(byKey[k])S.edits[k]=o.edits[k]});save()}}
 if(o.audit&&AU&&(!o.audit_date||o.audit_date===AU.meta.date)){var ok={};AU.rows.forEach(function(r){ok[r.rid]=1});Object.keys(o.audit).forEach(function(k){if(ok[k]){SA[k]=o.audit[k];na++}});saveA()}
 return fmt(t("imported"),{d:nd,a:na})+note}
function pickImport(target){var f=$("imp-file");f.value="";f.onchange=function(){var file=f.files&&f.files[0];if(!file)return;var rd=new FileReader();
 rd.onload=function(){var m;try{m=importDecisions(JSON.parse(rd.result))}catch(e){m=t("impBad")}$(target).textContent=m;chrome();if(TAB==="audit")renderAudit();else{renderReg();renderCase()}};rd.readAsText(file)};f.click()}
$("x-imp").onclick=function(){pickImport("x-msg")};$("a-imp").onclick=function(){pickImport("a-msg")};
// ------------------------------------------------------------------ print: one case per page (drafts tab)
window.addEventListener("beforeprint",function(){if(TAB==="drafts")$("print").innerHTML=VIS.map(function(g){return '<article class="pcase">'+caseHTML(g,false)+"</article>"}).join("")});
window.addEventListener("afterprint",function(){$("print").innerHTML=""});
function fromHash(){var h=decodeURIComponent(location.hash.slice(1));if(h==="audit"&&AU){TAB="audit";return true}
 var g=G.filter(function(g){return g.pair===h||g.no===h})[0];
 if(g){TAB="drafts";if(!(langs(g).some(function(L){return okItem(g.items[L])})))F.status="all";sel=g;return true}return false}
fromHash();chrome();if(TAB==="audit")renderAudit();else{renderReg();if(sel){markSel(true);renderCase()}}
window.GleichlautReview={xliff:xliff,payload:payload,importDecisions:importDecisions,setTab:setTab};
window.addEventListener("hashchange",function(){if(fromHash()){setTab(TAB)}});
})();
</script>
"""
