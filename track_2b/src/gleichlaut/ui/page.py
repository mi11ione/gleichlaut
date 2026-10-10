"""The review page template (HEAD = title + style, BODY = content + data + script), filled in by build.py.
No external request: fonts are inlined by build.fonts_css(), data by build.build()."""

HEAD = r"""<title>Gleichlaut Review</title>
<style>
__FONTS__
/* LAYOUT. An engineering drawing sheet / federal gazette hybrid. Page (paper) with one framed sheet (max-width 1320px,
   1px ink frame, registration marks at the four corners). 1 header = a title block: a ruled grid of small cells (mono
   9px labels: project, drawing, sheet, rev, date, lane, model, run, checked by) with "Gleichlaut" set large in Archivo
   condensed, the decisions export and its one-line note; the two views as one ruled two-cell band that is also the tab
   list (01 Drafts: Apertus drafts, code checks | 02 Register audit: code only), each with its headline figure; a
   two-column key-value block for the active view.
   Register audit tab: lead, filters, a compact legend of the marks, one ruled table row per audit finding (drawing-grid
   column letters A-H above the columns; the finding's own number N01/E01/L01/T01 in column A; DE | FR | IT excerpts side
   by side, conflicting values boxed in signal orange, the odd-one-out language with an orange bar, two decision columns +
   note), export row. Below 900px each audit row becomes a labelled block.
   2 work area: register (left, 5fr: filters, legend of the marks, sticky-head table with column letters, numbered by the
   change's address wbNNN, export row) | case (right, 7fr, a decorative tick ruler along its left edge: §1 German change,
   §2 Drafts FR|IT with a legend of the number marks, §3 Checks: at most three plain reasons per draft in the reviewer's
   language, labelled "explanation (FR/IT)", then the termbase advisory on its own low-priority line when there is one,
   the full checks ledger collapsed below, §4 Decision). Below 900px the
   register sits above the case and the band stacks; no horizontal page scroll from 320px up. 3 footer: provenance +
   legend of the marks and keys. Print: A4, register hidden, one case per page.
   Type: Public Sans (texts), Archivo condensed (headings, big figures), Fragment Mono (metadata, labels, tables,
   buttons). Colour: ink on a cool grey-green paper; ONE signal colour, international orange, for flags, failures,
   "to check", divergences and the keyboard focus; ready stays ink. Language tags are small inverted mono boxes.
   No radii, no shadows, no gradients, no fills except the inverted tags and the selected row. */
:root{--paper:#f4f5f1;--sheet:#fbfbf9;--ink:#111312;--ink2:#5a5f58;--hair:#c9ccc4;--rule:var(--ink);--sig:#ff4f00;--sig-ink:#111312;
--sel:var(--ink);--sel-ink:var(--sheet);
--sans:"Public Sans","Helvetica Neue",Arial,sans-serif;--disp:"Archivo","Archivo Narrow","Helvetica Neue Condensed","Arial Narrow",sans-serif;
--mono:"Fragment Mono","Helvetica Mono",Menlo,Consolas,monospace;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0f1110;--sheet:#151816;--ink:#e8eae4;--ink2:#9ba096;--hair:#353a36;--sig:#ff6a26;--sig-ink:#0f1110;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#0f1110;--sheet:#151816;--ink:#e8eae4;--ink2:#9ba096;--hair:#353a36;--sig:#ff6a26;--sig-ink:#0f1110;color-scheme:dark}
*{box-sizing:border-box;border-radius:0}
html{-webkit-text-size-adjust:100%;font-synthesis:none}
body{margin:0;background:var(--paper);color:var(--ink);font:400 13px/1.5 var(--mono);font-variant-numeric:tabular-nums;padding:28px 24px 40px;overflow-wrap:break-word}
button,select,input,textarea{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--sig);outline-offset:2px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important;scroll-behavior:auto!important}}
.sheet{max-width:1320px;margin:0 auto;padding-inline:max(16px,2vw);padding-block:0 24px;background:var(--sheet);border:1px solid var(--ink);position:relative}
/* registration marks: thin ink L-shapes just outside the four corners of the sheet */
.sheet::before,.sheet::after,.sheet>footer::before,.sheet>footer::after{content:"";position:absolute;width:12px;height:12px;border:0 solid var(--ink);pointer-events:none}
.sheet::before{top:-9px;left:-9px;border-top-width:1px;border-left-width:1px}
.sheet::after{top:-9px;right:-9px;border-top-width:1px;border-right-width:1px}
.sheet>footer::before{bottom:-9px;left:-9px;border-bottom-width:1px;border-left-width:1px}
.sheet>footer::after{bottom:-9px;right:-9px;border-bottom-width:1px;border-right-width:1px}
#print.sheet::before,#print.sheet::after{display:none}
.sans{font-family:var(--sans)}
/* header */
.hd{padding-block:16px 0}
/* title block: a ruled grid of cells, each a 9px mono label over its value */
.tblock{display:grid;grid-template-columns:minmax(220px,2.2fr) repeat(4,minmax(0,1fr));border:1px solid var(--ink);margin-bottom:0}
.tblock>div{border-right:1px solid var(--hair);border-bottom:1px solid var(--hair);padding:4px 8px 5px;min-width:0;word-break:break-word;overflow-wrap:anywhere}
.tblock>div:nth-child(5),.tblock>div:nth-child(9){border-right:0}
.tblock .lbl{display:block;font:400 9px/1.3 var(--mono);text-transform:uppercase;letter-spacing:.1em;color:var(--ink2)}
.tblock .val{display:block;font:400 12px/1.35 var(--mono)}
.tblock .val small{display:block;font-size:11px;color:var(--ink2)}
.tblock .tb-name{grid-row:span 3;display:flex;flex-direction:column;justify-content:space-between;border-right:1px solid var(--ink);border-bottom:0;padding:6px 10px 8px}
.tblock .tb-tools{grid-column:2/-1;display:flex;flex-wrap:wrap;gap:4px 16px;align-items:center;justify-content:flex-end;border-bottom:0;color:var(--ink2)}
.tblock .tb-tools .where{flex-basis:100%;text-align:right;font-size:11px;line-height:1.35}
.tblock .tb-tools .box{padding:1px 8px}
.hrow{display:flex;flex-wrap:wrap;gap:6px 24px;align-items:flex-end;justify-content:space-between}
h1{font:600 46px/0.95 var(--disp);font-stretch:75%;margin:2px 0 0;letter-spacing:-.015em}
.sub{margin:4px 0 0;color:var(--ink2);font-size:11px}
.tools{display:flex;flex-wrap:wrap;gap:4px 16px;align-items:center;color:var(--ink2)}
.tools b{color:var(--ink);font-weight:400}
/* the two views as one system: 01 Apertus drafts + code checks | 02 code audits the register; each cell is a tab */
.tabs{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);margin-top:10px;border:1px solid var(--ink)}
.tab{display:flex;flex-direction:column;gap:3px;min-width:0;text-align:left;background:none;border:0;border-top:3px solid transparent;padding:7px 12px 10px;color:var(--ink2);cursor:pointer}
.tab+.tab{border-left:1px solid var(--ink)}
.tab:hover .th{color:var(--ink)}
.tab[aria-selected=true]{border-top-color:var(--ink);color:var(--ink)}
.tab .th{font:400 11px/1.3 var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--ink2)}
.tab .th b{font-weight:400;color:var(--ink);margin-right:8px}
.tab[aria-selected=true] .th{color:var(--ink)}
.tab .tf{font:600 22px/1.05 var(--disp);font-stretch:75%;color:var(--ink);overflow-wrap:anywhere}
.tab .tt{font:400 13px/1.4 var(--sans);color:var(--ink2);max-width:62ch}
.tab .go{font:400 11px/1.3 var(--mono);color:var(--ink);text-transform:uppercase;letter-spacing:.06em;margin-top:2px}
.tab[aria-selected=true] .go{display:none}
.kv{display:grid;grid-template-columns:1fr 1fr;gap:0 32px;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);margin-top:0;padding-block:8px}
.kv .big{font:600 22px/1 var(--disp);font-stretch:75%;color:var(--ink)}
.kv dl{margin:0;display:grid;grid-template-columns:minmax(120px,max-content) 1fr;gap:2px 16px;align-content:start}
.kv dt{color:var(--ink2)}.kv dd{margin:0;overflow-wrap:anywhere}
.kv .pass{font:600 16px/1 var(--disp);font-stretch:75%}.kv .fail{color:var(--sig)}
/* text buttons */
.tb{background:none;border:0;padding:2px 0;cursor:pointer;text-decoration:none;border-bottom:2px solid transparent}
.tb:hover{border-bottom-color:var(--hair)}
.tb[aria-pressed=true]{border-bottom-color:var(--ink)}
.box{background:none;border:1px solid var(--ink);padding:3px 9px;cursor:pointer;white-space:nowrap}
.box[aria-pressed=true],.box.primary{background:var(--ink);color:var(--sheet)}
.box:disabled{opacity:.45;cursor:default}
/* work area */
.work{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:0 28px;margin-top:0}
.register{border-right:1px solid var(--hair);padding-right:20px;padding-block:12px 0;min-width:0;position:sticky;top:0;align-self:start;max-height:100vh;display:flex;flex-direction:column}
.filters{display:flex;flex-direction:column;gap:6px;padding-bottom:10px;border-bottom:1px solid var(--rule)}
.fl{display:flex;flex-wrap:wrap;gap:2px 12px;align-items:baseline}
.fl .k{color:var(--ink2);min-width:72px}
.fl select,.fl input{background:var(--sheet);border:0;border-bottom:1px solid var(--hair);padding:3px 0;min-width:0}
.fl input{flex:1 1 140px}.fl select{flex:0 1 auto;max-width:100%}
.tbl{overflow-x:auto;min-width:0}
.reg-wrap{overflow:auto;flex:1 1 auto;min-height:120px}
table{border-collapse:collapse;width:100%}
th{font:400 11px/1.4 var(--mono);text-transform:uppercase;letter-spacing:.06em;text-align:left;color:var(--ink2);padding:6px 8px;border-bottom:1px solid var(--rule);vertical-align:bottom}
td{padding:5px 8px;border-bottom:1px solid var(--hair);vertical-align:top}
#reg{table-layout:fixed;min-width:420px}
#reg thead th{position:sticky;top:0;background:var(--sheet);z-index:1}#reg thead tr.grid th{top:0}#reg thead tr+tr th{top:15px}
#reg col.c-mark{width:84px}#reg col.c-no{width:62px}#reg col.c-prod{width:34%}
#reg td{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;cursor:pointer}
#reg td.chg{font:400 14px/1.45 var(--sans)}
#reg td.prd .pc{display:block;font-size:11px;color:var(--ink2);overflow:hidden;text-overflow:ellipsis}
#reg tr[aria-selected=true] td.prd .pc{color:var(--sel-ink)}
#reg tr:hover td{background:color-mix(in srgb,var(--ink) 5%,transparent)}
#reg tr[aria-selected=true] td{background:var(--sel);color:var(--sel-ink)}
#reg tr[aria-selected=true] .mk.r{color:var(--sel-ink);text-decoration:underline}
.mk{display:inline-block;min-width:1.5em;text-align:center;letter-spacing:0}.mk.r{color:var(--sig)}.mk.o{color:var(--ink2)}.mk.f{color:var(--ink)}
/* language tags: small inverted mono boxes */
.lt{display:inline-block;font:400 10px/1.35 var(--mono);letter-spacing:.06em;background:var(--ink);color:var(--sheet);padding:0 4px;vertical-align:1px}
.lt.s{background:var(--sig);color:var(--sig-ink)}
/* drawing grid: column letters above the tables, row numbers in the margin */
tr.grid th{font:400 9px/1 var(--mono);color:var(--ink2);text-align:center;padding:3px 0 2px;border-bottom:1px solid var(--hair);letter-spacing:0;text-transform:none}
tr.grid th+th{border-left:1px solid var(--hair)}
.rnw{padding-left:26px}
.rn tbody{counter-reset:rn}
.rn tbody tr.cnt{counter-increment:rn}
.rn tbody tr.cnt>td:first-child{position:relative;overflow:visible}#reg tbody tr.cnt>td:first-child{overflow:visible}
.rn tbody tr.cnt>td:first-child::before{content:counter(rn,decimal-leading-zero);position:absolute;left:-26px;top:6px;width:20px;text-align:right;font:400 9px/1.2 var(--mono);color:var(--ink2)}
.count{color:var(--ink2);padding:6px 0}
.export{display:flex;flex-wrap:wrap;gap:8px;padding:10px 0 12px;border-top:1px solid var(--rule)}
.export .msg{color:var(--ink2);flex-basis:100%}
.export .where{color:var(--ink2);flex-basis:100%;font-size:12px}
/* compact legends of the marks, next to what they mark */
.key{margin:6px 0 4px;color:var(--ink2);font-size:12px;line-height:1.6;overflow-wrap:anywhere}
.key>span{margin-right:12px}.key>span>.mk,.key>span>.lt,.key>span>.n,.key>span>.v1,.key>span>.v2{white-space:nowrap}
.key .mk{min-width:1.2em}.key .n{font-size:11px}
.key .v2{border:1px solid var(--sig);padding:0 2px;font-weight:600;color:var(--ink)}.key .v1{border-bottom:1px solid var(--ink2);color:var(--ink)}
.key .bar{display:inline-block;width:3px;height:1em;background:var(--sig);vertical-align:-2px;margin-right:4px}
.xl{font:400 11px/1.3 var(--mono);color:var(--ink2);letter-spacing:.04em}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
#copybox{width:100%;height:90px;font:12px/1.4 var(--mono);border:1px solid var(--hair);background:var(--sheet)}
/* case */
.case{min-width:0;padding-block:14px 0;position:relative;padding-left:22px}
/* decorative tick ruler along the left edge of the case pane (a tick every 8px, a longer one every 40px) */
.case::before{content:"";position:absolute;left:0;top:0;bottom:0;width:11px;background:var(--ink2);opacity:.7;pointer-events:none;
-webkit-mask:url(data:image/svg+xml,%3Csvg%20xmlns=%27http://www.w3.org/2000/svg%27%20width=%2711%27%20height=%2740%27%3E%3Cpath%20d=%27M0%20.5H11M0%208.5H5M0%2016.5H5M0%2024.5H5M0%2032.5H5%27%20stroke=%27black%27%20stroke-width=%271%27/%3E%3C/svg%3E) 0 0/11px 40px repeat-y;
mask:url(data:image/svg+xml,%3Csvg%20xmlns=%27http://www.w3.org/2000/svg%27%20width=%2711%27%20height=%2740%27%3E%3Cpath%20d=%27M0%20.5H11M0%208.5H5M0%2016.5H5M0%2024.5H5M0%2032.5H5%27%20stroke=%27black%27%20stroke-width=%271%27/%3E%3C/svg%3E) 0 0/11px 40px repeat-y}
.case:focus{outline:none}
h2{font:600 30px/1.05 var(--disp);font-stretch:75%;margin:0;letter-spacing:-.005em}
.ref{color:var(--ink2);margin:4px 0 0;overflow-wrap:anywhere}
.sec{border-top:1px solid var(--rule);margin-top:16px;padding-top:8px}
.sl{display:flex;flex-wrap:wrap;gap:4px 14px;align-items:baseline;color:var(--ink2);margin-bottom:8px}
.sl .no{color:var(--ink);font:600 15px/1 var(--disp);font-stretch:75%}.sl .no b{color:var(--sig);font-weight:600;margin-right:1px}
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
.n.m{border-color:var(--sig)}
.drafts{display:grid;grid-template-columns:1fr 1fr;gap:0}
.drafts.one{grid-template-columns:1fr}
.dr{min-width:0;padding-right:16px}
.dr+.dr{border-left:1px solid var(--hair);padding:0 0 0 16px}
.dl{display:flex;flex-wrap:wrap;gap:2px 10px;align-items:baseline;margin-bottom:6px}
.dl .st.r{color:var(--ink)}.dl .st.r::before{content:"▲ ";color:var(--sig)}.dl .key{color:var(--ink2);margin-left:auto}
.dl .cap{color:var(--ink2);font-size:12px;flex-basis:100%}
.dl .tri{color:var(--ink2)}.dl .tri b{color:var(--ink);font-weight:400;box-shadow:inset 0 -2px 0 var(--sig)}
.ids{color:var(--ink2);margin-top:2px;font-size:12px}.ids summary{cursor:pointer;display:inline}
.notice.lang{font-size:17px}.notice.lang p:first-child{font-weight:600}
.notice{border-left:3px solid var(--sig);padding:4px 0 4px 10px;margin:0 0 10px;font:400 15px/1.45 var(--sans)}
.notice .mk{font-family:var(--mono);font-size:13px;color:var(--sig);margin-right:6px;min-width:0}
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
.ledger .FAIL{color:var(--ink)}.ledger .FAIL::before{content:"▲ ";color:var(--sig)}.ledger .FAILf{color:var(--ink)}.ledger .na{color:var(--ink2)}
.ledger .fd{font:400 15px/1.4 var(--sans)}
.ledger .fd p{margin:0}.ledger .fd p+p{margin-top:3px}
.ledger .cn{display:block;font:400 12px/1.4 var(--mono);color:var(--ink);margin-top:2px}
.ledger details{margin-top:3px;color:var(--ink2);font-size:12px}
.ledger summary{cursor:pointer}
.ledger details div{overflow-wrap:anywhere;white-space:pre-wrap}
.ledger details.pf{color:var(--ink);font-size:inherit;margin-top:4px;border-top:1px dotted var(--hair);padding-top:3px}
.ledger details.pf summary{font:400 12px/1.4 var(--mono);color:var(--ink2)}
.ledger details.pf p{color:var(--ink2)}
/* per-draft explanation: at most three reasons, plain wording; the full ledger collapsed below */
.why{margin-bottom:14px}.why+.why{border-top:1px solid var(--hair);padding-top:10px}
.reasons{margin:4px 0 6px;padding-left:1.6em;font:400 15px/1.45 var(--sans)}
.reasons li{padding-left:2px}.reasons li+li{margin-top:4px}
.reasons li.low{color:var(--ink2)}
.why p.tb{margin:2px 0 6px;color:var(--ink2);font:400 13px/1.45 var(--sans)}
.reasons li::marker{font:400 12px var(--mono);color:var(--ink2)}
.why .ok{font:400 15px/1.45 var(--sans);margin:4px 0 6px}
.why .more{color:var(--ink2);margin:0 0 4px;font-size:12px}
.why details.chk>summary{cursor:pointer;color:var(--ink2);font-size:12px;padding:3px 0}
.why details.chk[open]>summary{margin-bottom:6px}
.ledger caption .tri{font-weight:400;color:var(--ink2);margin-left:8px}.ledger caption .tri b{color:var(--ink);font-weight:400;box-shadow:inset 0 -2px 0 var(--sig)}
.decs{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}
.decs.one{grid-template-columns:1fr}
.dec{min-width:0;border-left:3px solid transparent;padding:4px 0 6px 10px}
.dec.focus{border-left-color:var(--ink)}
.btns{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}
.dec label{display:block;color:var(--ink2);margin-top:6px}
.dec select{display:block;width:100%;margin-top:2px;background:var(--sheet);border:1px solid var(--hair);padding:3px 4px}
.dec textarea{display:block;width:100%;margin-top:2px;min-height:52px;resize:vertical;background:var(--sheet);border:1px solid var(--hair);padding:4px 6px;font:400 15px/1.4 var(--sans)}
.dec .stt{color:var(--ink2);margin-top:4px}
.save{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;margin-top:10px;padding-top:10px;border-top:1px solid var(--hair)}
.save .hint{color:var(--ink2)}
.empty{color:var(--ink2);padding:24px 0}
/* register audit */
.audit{padding-block:12px 0}
.lead{font:400 16px/1.45 var(--sans);margin:0 0 10px;max-width:90ch}
.afl{display:flex;flex-direction:column;gap:6px;padding-bottom:10px;border-bottom:1px solid var(--rule)}
#aud{table-layout:fixed;min-width:1080px}
#aud col.a-no{width:58px}#aud col.a-lim{width:13%}#aud col.a-kind{width:150px}#aud col.a-dec{width:118px}#aud col.a-act{width:17%}
#aud td.kd{overflow-wrap:anywhere;word-break:normal}#aud td.kd .oddl{display:block;margin-top:2px}
#aud thead th{position:sticky;top:0;background:var(--sheet);z-index:1}
#aud td{font-size:13px}
#aud tr.grp td{font:400 11px/1.4 var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--ink);padding:16px 8px 6px;border-bottom:1px solid var(--rule)}
#aud tr.grp .mk{margin-right:8px}
#aud .lim b{font:400 15px/1.3 var(--sans);display:block}
#aud .lim .code{color:var(--ink2);overflow-wrap:anywhere}
#aud .sub2{display:block;color:var(--ink2);font-size:12px;margin-top:3px;overflow-wrap:anywhere}
#aud .term{display:block;font:400 14px/1.35 var(--sans);margin-top:4px;overflow-wrap:anywhere}
#aud .term s{color:var(--sig);text-decoration-thickness:1px}#aud .term u{text-decoration-thickness:2px;text-underline-offset:3px}
#aud tr.eqh td{padding:14px 8px 6px;border-bottom:1px solid var(--rule)}
#aud tr.eqh button{background:none;border:0;padding:0;cursor:pointer;font:400 11px/1.4 var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--ink)}
#aud tr.eqh button .mk{margin-right:8px}
#aud tr.eq td{color:color-mix(in srgb,var(--ink) 85%,var(--sheet))}
.afl .fl input{background:var(--sheet);border:0;border-bottom:1px solid var(--hair);padding:3px 0;min-width:0;flex:1 1 320px;max-width:440px}
.fambar{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:baseline;padding-top:4px}
.fambar .q{flex-basis:100%;font:400 14px/1.4 var(--sans)}.fambar .msg{color:var(--ink2);flex-basis:100%}
.famline{color:var(--ink2);margin:2px 0 0;overflow-wrap:anywhere}.famline .tb{color:var(--ink)}
.snip{font:400 14px/1.45 var(--sans);overflow-wrap:anywhere}
.snip .v2{border:1px solid var(--sig);padding:0 2px;font-weight:600;white-space:nowrap}
.snip .v1{border-bottom:1px solid var(--ink2)}
.snip.src-s{color:color-mix(in srgb,var(--ink) 82%,var(--sheet))}
.snip .sx{display:block;font:400 11px/1.3 var(--mono);color:var(--ink2);margin-top:3px}
td.odd{box-shadow:inset 3px 0 0 var(--sig);padding-left:12px}
.oddl{display:block;font:400 11px/1.3 var(--mono);color:var(--ink);text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px}
#aud select{width:100%;background:var(--sheet);border:1px solid var(--hair);padding:3px 4px}
#aud textarea{display:block;width:100%;margin-top:4px;min-height:44px;resize:vertical;background:var(--sheet);border:1px solid var(--hair);padding:3px 5px;font:400 14px/1.35 var(--sans)}
#aud .sug{color:var(--ink2);font-size:12px;margin-top:3px}
#aud .stt{color:var(--ink2);font-size:12px;margin-top:3px}
#aud .na{color:var(--ink2);font-style:italic}
.snip .v2.w{white-space:normal;-webkit-box-decoration-break:clone;box-decoration-break:clone}
/* register audit, round 5: one row per issue (number, findings), its full texts and findings in a row below it */
.band{border-left:3px solid var(--ink);padding:5px 0 5px 12px;margin:10px 0 0;font:400 15px/1.45 var(--sans);max-width:120ch}
#aud .iid{display:block;font:600 22px/1 var(--disp);font-stretch:75%;margin-top:2px}
#aud .fids{display:block;font-size:11px;line-height:1.3;color:var(--ink2);overflow-wrap:anywhere;margin-top:2px}
#aud .sub2.dt{color:var(--ink);font:400 12px/1.4 var(--sans);margin-top:5px}
#aud tr.iss>td{border-bottom:0}
#aud tr.det>td{padding:0 8px 10px;border-bottom:1px solid var(--hair)}
#aud details.ft,#aud details.mm{display:inline-block;vertical-align:top;margin-right:24px}
#aud details[open]{display:block;margin-right:0}
#aud details>summary{cursor:pointer;font:400 11px/1.4 var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--ink);padding:3px 0}
#aud details>summary::marker{color:var(--ink2)}
.acts{display:flex;flex-wrap:wrap;gap:1px 10px;align-items:baseline;font:400 12px/1.35 var(--sans);margin:0 0 2px}
.acts .fixl{color:var(--ink);flex-basis:100%}.acts .fixg{display:inline-flex;gap:12px;flex-basis:100%;margin-bottom:2px}
.acts .ck{display:inline-flex;gap:5px;align-items:baseline;cursor:pointer}
.acts .ck.row{flex-basis:100%}
.acts input{accent-color:var(--ink);margin:0;transform:translateY(1px)}
.ftl{margin:12px 0 2px;color:var(--ink2)}.ftl b{color:var(--ink);font:400 15px/1.3 var(--sans);margin-right:6px}
.ftg{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0 16px;margin:6px 0 10px}
.ftc{min-width:0}.ftc+.ftc{border-left:1px solid var(--hair);padding-left:16px}
.ftc.odd{box-shadow:inset 3px 0 0 var(--sig);padding-left:12px}.ftc .oddl{display:inline}
.snip.ftx{margin-top:4px;font:400 14px/1.55 var(--sans);max-width:75ch}
table.mem{width:100%;table-layout:auto;margin:4px 0 6px}
table.mem td{font-size:13px;border-bottom:1px dotted var(--hair);padding:5px 10px 5px 0;vertical-align:top}
table.mem td.mf{width:44px;white-space:nowrap;color:var(--ink2)}table.mem td.mc{width:36%}
table.mem .code{color:var(--ink2);overflow-wrap:anywhere}table.mem .tb{color:var(--ink);font-size:12px}
footer{border-top:1px solid var(--rule);margin-top:28px;padding-top:8px;color:var(--ink2)}
footer p{margin:2px 0;overflow-wrap:anywhere}
#print{display:none}
[hidden]{display:none!important}
@media (max-width:900px){
 #aud{min-width:0;table-layout:auto}#aud colgroup,#aud thead{display:none}
 #aud,#aud tbody,#aud tr,#aud td{display:block;width:auto;max-width:100%}
 #aud tr{border-bottom:1px solid var(--rule);padding:8px 0 10px}#aud tr.grp{padding:0;border:0}
 #aud td{border:0;padding:3px 0}#aud td.odd{padding-left:10px}#aud td.odd>.oddl{display:none}
 .kv dl{grid-template-columns:minmax(96px,44%) minmax(0,1fr)}
 #aud td[data-l]::before{content:attr(data-l);display:block;font:400 11px/1.4 var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--ink2)}
 .work{grid-template-columns:minmax(0,1fr)}
 .tabs{grid-template-columns:minmax(0,1fr)}.tab+.tab{border-left:0;border-top:1px solid var(--ink)}
 .tblock .tb-tools .where{text-align:left}
 .register{position:static;max-height:none;border-right:0;padding-right:0;border-bottom:1px solid var(--rule)}
 .reg-wrap{max-height:46vh}
 #reg{min-width:0}#reg col.c-mark{width:58px}#reg col.c-no{width:60px}#reg td,#reg th{padding-inline:6px}
 .kv{grid-template-columns:1fr}
 .drafts,.decs{grid-template-columns:1fr}
 .dr{padding-right:0}.dr+.dr{border-left:0;border-top:1px solid var(--hair);padding:12px 0 0;margin-top:12px}
 h1{font-size:40px}
 .tblock{grid-template-columns:repeat(2,minmax(0,1fr))}
 .tblock .tb-name{grid-column:1/-1;grid-row:auto;border-right:0;border-bottom:1px solid var(--ink)}
 .tblock>div:nth-child(5),.tblock>div:nth-child(9){border-right:1px solid var(--hair)}
 .tblock>div:nth-child(2n+1){border-right:0}
 .tblock .tb-tools{grid-column:1/-1;justify-content:flex-start}
 .rnw{padding-left:0}.rn tbody tr.cnt>td:first-child::before{display:none}
 #aud tr.grid{display:none}
 #aud tr.iss{border-bottom:0;padding-bottom:2px}#aud tr.det{padding-top:0}#aud tr.det>td{padding:0}
 #aud table.mem tr{border-bottom:1px dotted var(--hair);padding:6px 0}#aud table.mem td{padding:2px 0;width:auto}
 .ftg{grid-template-columns:minmax(0,1fr)}.ftc+.ftc{border-left:0;padding-left:0;border-top:1px solid var(--hair);margin-top:8px;padding-top:8px}
 .ftc.odd{padding-left:10px}
 .case{padding-left:16px}.case::before{width:8px}
}
@media (max-width:600px){
 .tab .tt{display:none}.tab .tf{font-size:19px}
}
@media (max-width:480px){
 body{padding:16px 10px 28px}
 .sheet{padding-inline:12px}
}
@media print{
 @page{size:A4;margin:14mm}
 body{border-top:0;font-size:10pt;background:#fff;color:#000}
 .register,.tools,.tabs,.save,.export,.edmeta,.btns,.dec select,.dec textarea,#case,.tb-tools .box,.tb-tools .where{display:none!important}
 .why details.chk{display:none}
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
 <div class="tblock" role="group" aria-label="Title block">
  <div class="tb-name"><span class="lbl" data-tb="project"></span><h1>Gleichlaut</h1><p class="sub" id="sub"></p></div>
  <div><span class="lbl" data-tb="drawing"></span><span class="val" id="tb-drawing"></span></div>
  <div><span class="lbl" data-tb="sheet"></span><span class="val" id="tb-sheet"></span></div>
  <div><span class="lbl" data-tb="rev"></span><span class="val" id="tb-rev"></span></div>
  <div><span class="lbl" data-tb="date"></span><span class="val" id="tb-date"></span></div>
  <div><span class="lbl" data-tb="lane"></span><span class="val" id="tb-lane"></span></div>
  <div><span class="lbl" data-tb="model"></span><span class="val" id="tb-model"></span></div>
  <div><span class="lbl" data-tb="run"></span><span class="val" id="tb-run"></span></div>
  <div><span class="lbl" data-tb="checked"></span><span class="val" id="tb-checked"></span></div>
  <div class="tb-tools"><span id="progress"></span><button class="box primary" id="x-dec" type="button"></button><button class="tb" id="theme" type="button"></button>
   <label><span id="l-ui"></span> <select id="ui-lang" aria-label="Interface language"><option value="de">DE</option><option value="en">EN</option><option value="fr">FR</option><option value="it">IT</option></select></label><span class="where" id="where"></span></div>
 </div>
 <nav class="tabs" role="tablist" aria-label="Views"><button class="tab" role="tab" type="button" id="t-drafts" aria-controls="p-drafts"></button><button class="tab" role="tab" type="button" id="t-audit" aria-controls="p-audit"></button></nav>
 <div class="kv"><dl id="kv-l"></dl><dl id="kv-r"></dl></div>
 <p class="band" id="d-band" hidden></p>
</header>
<section class="audit" id="p-audit" role="tabpanel" aria-labelledby="t-audit" hidden>
 <p class="lead" id="a-lead"></p>
 <div class="afl"><div class="fl" id="a-show"></div><div class="fl" id="a-lang"></div><div class="fl" id="a-kind"></div><div class="fl" id="a-since" hidden></div>
  <div class="fl"><label class="k" for="rev" id="l-rev"></label><input type="text" id="rev" autocomplete="name"></div></div>
 <p class="key" id="aud-key"></p>
 <div class="tbl"><table id="aud"><colgroup><col class="a-no"><col class="a-lim"><col class="a-kind"><col><col><col><col class="a-dec"><col class="a-act"></colgroup>
  <thead><tr class="grid" aria-hidden="true"><th>A</th><th>B</th><th>C</th><th>D</th><th>E</th><th>F</th><th>G</th><th>H</th></tr><tr><th id="ah-no"></th><th id="ah-lim"></th><th id="ah-kind"></th><th><span class="lt">DE</span></th><th><span class="lt">FR</span></th><th><span class="lt">IT</span></th><th id="ah-right"></th><th id="ah-act"></th></tr></thead><tbody></tbody></table></div>
 <div class="count" id="a-shown"></div>
 <div class="export"><button class="box" id="a-csv-i" type="button"></button><button class="box" id="a-csv" type="button"></button><button class="box" id="a-imp" type="button"></button>
  <span class="msg" id="a-msg" aria-live="polite"></span></div>
</section>
<div class="work" id="p-drafts" role="tabpanel" aria-labelledby="t-drafts">
 <section class="register" id="register" aria-label="Register">
  <div class="filters">
   <div class="fl" id="f-status"></div>
   <div class="fl" id="f-lang"></div>
   <div class="fl"><select id="f-fam" aria-label="Family"></select><input type="search" id="f-q" aria-label="Search product or limitation code"></div>
   <div class="fambar" id="fam-bulk" hidden></div>
  </div>
  <p class="key" id="reg-key"></p>
  <div class="tbl reg-wrap" id="reg-wrap"><table id="reg"><colgroup><col class="c-mark"><col class="c-no"><col class="c-prod"><col></colgroup>
   <thead><tr class="grid" aria-hidden="true"><th>A</th><th>B</th><th>C</th><th>D</th></tr><tr><th id="h-mark"></th><th id="h-no"></th><th id="h-prod"></th><th id="h-chg"></th></tr></thead><tbody></tbody></table></div>
  <div class="count" id="shown"></div>
  <div class="export"><button class="box" id="x-xlf" type="button"></button><button class="box" id="x-xlf12" type="button"></button><button class="box" id="x-copy" type="button"></button><button class="box" id="x-imp" type="button"></button>
   <span class="msg" id="x-msg" aria-live="polite"></span><textarea id="copybox" hidden readonly aria-label="Decisions JSON"></textarea></div>
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
var LK="gleichlaut:"+M.run+":"+M.run_sha256.slice(0,12),AK="gleichlaut:audit-decisions",AKOLD="gleichlaut:audit:"+(AU?AU.meta.date:"none");
function lsGet(k,d){try{var v=localStorage.getItem(k);return v==null?d:JSON.parse(v)}catch(e){return d}}
function lsSet(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}
var S=lsGet(LK+":state",null)||{dec:{},edits:{}};S.dec=S.dec||{};S.edits=S.edits||{};
var SA=lsGet(AK,null)||{};
var P=lsGet("gleichlaut:prefs",{})||{};
function save(){lsSet(LK+":state",S)}
function saveA(){lsSet(AK,SA)}
// audit decisions are keyed by the finding's signature (limitation | kind | language | values), not by the audit date, so
// they carry over to the next audit run; decisions stored by an earlier page version (per date, by row id) are moved over.
var ACTMAP={"Berichtigung":"exofficio","GÄL":"holder","GAEL":"holder"};
(function(){if(!AU)return;var old=lsGet(AKOLD,null),bySig={},ch=false;AU.rows.forEach(function(r){bySig[r.rid]=r.sig});
 if(old)Object.keys(old).forEach(function(k){var sg=bySig[k];if(sg&&!SA[sg]){var d=old[k];d.date=d.date||AU.meta.date;SA[sg]=d;ch=true}});
 Object.keys(SA).forEach(function(k){var d=SA[k];if(d&&ACTMAP[d.action]){d.action=ACTMAP[d.action];ch=true}});if(ch)saveA()})();
function who(){return String(P.reviewer||"").trim()}
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
 legend:"Zeichen: ✓ bereit · ▲ markiert · ≠ der bisherige Text hat bereits ein Problem (weicht vom Deutschen ab oder ist in einer anderen Sprache) · h an Übersetzung übergeben · A übernommen · E bearbeitet übernommen · R zurückgewiesen · Tasten j/k oder ↑/↓ bewegen, Enter öffnet, f/i Sprache, 1/2/3 entscheiden, Ctrl/Cmd+Enter speichern und weiter",
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
 aLegend:"Zeichen: K bekannte Abweichung, im Text belegt · D entschieden · rot umrahmt = widersprüchlicher Wert · unterstrichen = weitere Zahl · roter Balken = die Sprache, die von den beiden anderen abweicht (nicht unbedingt die falsche). Entscheide: welche Sprache die richtige Bedingung nennt, und die Massnahme (Berichtigung, GÄL, keine).",
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
 legend:"Marks: ✓ ready · ▲ flagged · ≠ the previous text already has a problem (diverges from the German or is in another language) · h routed to a translator · A accepted · E accepted edited · R sent back · keys j/k or ↑/↓ move, Enter opens, f/i language, 1/2/3 decide, Ctrl/Cmd+Enter save and next",
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
 aLegend:"Marks: K known divergence, confirmed in the texts · D decided · red box = conflicting value · underlined = other number · red bar = the language that differs from the other two (not necessarily the wrong one). Decisions: which language states the right condition, and the action (Berichtigung, GÄL, none).",
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
 legend:"Marques : ✓ prêt · ▲ signalé · ≠ l'ancien texte a déjà un problème (diverge de l'allemand ou est dans une autre langue) · h confié à un traducteur · A accepté · E accepté modifié · R renvoyé · touches j/k ou ↑/↓ naviguer, Entrée ouvrir, f/i langue, 1/2/3 décider, Ctrl/Cmd+Entrée enregistrer et suivant",
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
 aLegend:"Marques : K divergence connue, attestée dans les textes · D décidé · cadre rouge = valeur contradictoire · souligné = autre nombre · barre rouge = la langue qui diffère des deux autres (pas forcément la fausse). Décisions : quelle langue dit la bonne condition, et la mesure (Berichtigung, GÄL, aucune).",
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
 legend:"Segni: ✓ pronta · ▲ segnalata · ≠ il vecchio testo ha già un problema (diverge dal tedesco o è in un'altra lingua) · h affidata a un traduttore · A accettata · E accettata modificata · R rinviata · tasti j/k o ↑/↓ spostarsi, Invio aprire, f/i lingua, 1/2/3 decidere, Ctrl/Cmd+Invio salva e avanti",
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
 aLegend:"Segni: K divergenza nota, confermata nei testi · D decisa · riquadro rosso = valore in contraddizione · sottolineato = altro numero · barra rossa = la lingua che differisce dalle altre due (non per forza quella sbagliata). Decisioni: quale lingua indica la condizione giusta, e la misura (Berichtigung, GÄL, nessuna).",
 aExpl:"spiegato da {x}",aFix:"refuso probabile: «{a}» → «{b}»",aSince:"nell'ES dal {d} ({n} stati)",aFoundL:"testo in {F}",oddLbl:"diverge",real:"reali",of:"su"}};
// round-3 strings (three-level status, rules T5-T8, family action, old-text start, XLIFF 1.2, audit actions and reviewer)
var TX2={
de:{tb:{project:"Projekt",drawing:"Zeichnung",sheet:"Blatt",rev:"Rev.",date:"Datum (SL-Stand)",freeze:"Freeze",model:"Modell",run:"Lauf",checked:"Geprüft von",checkedV:"eingefrorene Prüfungen"},lfine:"markiert – alle Befunde wahrscheinlich in Ordnung",lcheck:"markiert – zu prüfen",fCheck:"Zu prüfen",fFine:"Wahrscheinlich in Ordnung",
 triSplit:"Sortierung der Markierten (nur Anzeige)",triSplitV:"{c} zu prüfen · {f} mit allen Befunden wahrscheinlich in Ordnung",
 rT5:"T5 Zahlen ausserhalb",rT6:"T6 Orthografie",rT7:"T7 Verneinung",rT8:"T8 gleiche Werte",
 rdT5:"T5 Zahlen ausserhalb der Änderung: ausserhalb des geänderten Abschnitts ändert der Entwurf nur Zahlen, und zwar genau die Werte, die die deutsche Änderung ersetzt (Ocrevus 944.61 → 731.07).",
 rdT6:"T6 Orthografie: die nicht übernommene deutsche Änderung ist nur orthografisch (Umlaut/ß, Bindestrich wie Zeitpunkt → Zeit-punkt, Gross-/Kleinschreibung, Satzzeichen) oder eine Flexionsendung (bedürfen → bedarf, erste → erst).",
 rdT7:"T7 Verneinung: so gezählt, wie ein Leser zählt («nicht-» als Wortvorsilbe wie nicht-kleinzellig zählt nicht, französisch «ne … pas» einmal, «personne» als Nomen nicht), ändert der Entwurf die Zahl der Verneinungen genau wie das Deutsche.",
 rdT8:"T8 gleiche Werte: beide Seiten fügen dieselben Werte hinzu und entfernen dieselben, nur wie oft ein Wert vorkommt, unterscheidet sich (Kyprolis: 20481 im Deutschen zweimal, im Entwurf einmal).",
 legend:"Zeichen: ✓ bereit · ~ markiert, alle Befunde wahrscheinlich in Ordnung · ▲ markiert, zu prüfen · ≠ der bisherige Text hat bereits ein Problem (weicht vom Deutschen ab, ist in einer anderen Sprache oder nutzt einen vom BAG anderswo korrigierten Begriff) · h an Übersetzung übergeben · A übernommen · E bearbeitet übernommen · R zurückgewiesen · Tasten j/k oder ↑/↓ bewegen, Enter öffnet, f/i Sprache, 1/2/3 entscheiden, Ctrl/Cmd+Enter speichern und weiter",
 famAll:"Alle bereiten Entwürfe dieser Familie übernehmen ({n})",famAsk:"{n} offene bereite Entwürfe ({fr} FR, {it} IT) der Familie «{f}» unverändert übernehmen? Bereits entschiedene, bearbeitete und solche mit Hinweis zum bisherigen Text bleiben offen.",
 famYes:"Übernehmen bestätigen",famNo:"Abbrechen",famDone:"{n} bereite Entwürfe übernommen.",famNone:"Keine offenen bereiten Entwürfe in dieser Familie.",famOf:"Familie",famFilter:"nur diese Familie zeigen",famChanges:"{n} Änderungen",
 startOld:"Vom bisherigen Text ausgehen",startOldT:"Ersetzt den bearbeitbaren Entwurf durch den bisherigen Text mit den vom Code angewendeten Zahländerungen ({n}). «Entwurf wiederherstellen» macht es rückgängig.",startOldDone:"Bisheriger Text mit {n} Zahländerung(en) des Codes – jetzt bearbeiten.",
 xlf12:"XLIFF 1.2 exportieren",
 acts:{exofficio:"Von Amtes wegen in der nächsten Publikation berichtigen",holder:"Mit der Zulassungsinhaberin in der dreijährlichen Überprüfung aufnehmen",langsvc:"An den Sprachdienst",none:"Keine Massnahme (gleichwertige Formulierung)",unclear:"Unklar"},
 rev:"Prüfende Person",revPh:"Name (wird mit jedem Entscheid gespeichert)",decOn:"entschieden am {d} von {n}",decOnAnon:"entschieden am {d}",earlier:"in einer früheren Prüfung (Stand {s})",
 eqHead:"Wahrscheinlich gleichwertige Formulierung ({n})",eqWhy:"Grund",eqShow:"anzeigen",eqHide:"einklappen",
 kinds:{number:"Zahl",unit:"Einheit",language:"Sprache",editorial:"Redaktionell",terminology:"Terminologie"},termOld:"bisher",termNew:"vom BAG korrigiert zu",termWhere:"bereits korrigiert in: {x}",
 aLegend:"Zeichen: K bekannte Abweichung, im Text belegt · D entschieden · rot umrahmt = widersprüchlicher Wert · unterstrichen = weitere Zahl · roter Balken = die Sprache, die von den beiden anderen abweicht (nicht unbedingt die falsche). Entscheide: welche Sprache die richtige Bedingung nennt, und die Massnahme (von Amtes wegen berichtigen, in der dreijährlichen Überprüfung mit der Zulassungsinhaberin aufnehmen, Sprachdienst, keine, unklar). Ein Gesuch um Änderung der Limitation (GÄL) stellt die Zulassungsinhaberin, nicht das BAG. Entscheide gelten pro Befund (Limitation, Art, Sprache, Werte) und bleiben in der nächsten Prüfung erhalten."},
en:{tb:{project:"Project",drawing:"Drawing",sheet:"Sheet",rev:"Rev",date:"Date (SL snapshot)",freeze:"Freeze",model:"Model",run:"Run",checked:"Checked by",checkedV:"frozen checks"},lfine:"flagged – all findings probably fine",lcheck:"flagged – to check",fCheck:"To check",fFine:"Probably fine",
 triSplit:"Triage of the flagged (display only)",triSplitV:"{c} to check · {f} with every finding probably fine",
 rT5:"T5 numbers outside",rT6:"T6 orthography",rT7:"T7 negation",rT8:"T8 same values",
 rdT5:"T5 numbers outside the change: outside the changed passage the draft changes numbers only, exactly the values the German change replaces (Ocrevus 944.61 → 731.07).",
 rdT6:"T6 orthography: the German change not carried over is orthographic only (umlaut/ß, hyphenation such as Zeitpunkt → Zeit-punkt, case, punctuation) or an inflectional ending (bedürfen → bedarf, erste → erst).",
 rdT7:"T7 negation: counted the way a reader counts ('nicht-' as a word prefix as in nicht-kleinzellig does not count, French 'ne … pas' counts once, 'personne' as a noun does not count), the draft changes the number of negations exactly as the German does.",
 rdT8:"T8 same values: both sides add and remove the same values; only how often a value occurs differs (Kyprolis: 20481 twice in the German, once in the draft).",
 legend:"Marks: ✓ ready · ~ flagged, all findings probably fine · ▲ flagged, to check · ≠ the previous text already has a problem (diverges from the German, is in another language or uses a term BAG corrected elsewhere) · h routed to a translator · A accepted · E accepted edited · R sent back · keys j/k or ↑/↓ move, Enter opens, f/i language, 1/2/3 decide, Ctrl/Cmd+Enter save and next",
 famAll:"Accept all ready drafts of this edit family ({n})",famAsk:"Accept {n} open ready drafts ({fr} FR, {it} IT) of the family “{f}” as they are? Drafts already decided, edited, or with an old-text notice stay open.",
 famYes:"Confirm accept",famNo:"Cancel",famDone:"{n} ready drafts accepted.",famNone:"No open ready drafts in this family.",famOf:"Family",famFilter:"show this family only",famChanges:"{n} changes",
 startOld:"Start from the old text",startOldT:"Replaces the editable draft with the old text plus the number changes code applied ({n}). “Reset to draft” undoes it.",startOldDone:"Old text with {n} number change(s) applied by code – edit it now.",
 xlf12:"Export XLIFF 1.2",
 acts:{exofficio:"Correct ex officio in the next publication",holder:"Raise with the holder in the triennial review",langsvc:"Send to the language service",none:"No action (equivalent wording)",unclear:"Unclear"},
 rev:"Reviewer",revPh:"Name (stored with each decision)",decOn:"decided on {d} by {n}",decOnAnon:"decided on {d}",earlier:"in an earlier audit (snapshot {s})",
 eqHead:"Probably equivalent wording ({n})",eqWhy:"Reason",eqShow:"show",eqHide:"collapse",
 kinds:{number:"number",unit:"unit",language:"language",editorial:"editorial",terminology:"terminology"},termOld:"old",termNew:"corrected by BAG to",termWhere:"already corrected in: {x}",
 aLegend:"Marks: K known divergence, confirmed in the texts · D decided · red box = conflicting value · underlined = other number · red bar = the language that differs from the other two (not necessarily the wrong one). Decisions: which language states the right condition, and the action (correct ex officio, raise with the holder in the triennial review, language service, none, unclear). An application to change a limitation (GÄL) is filed by the holder, not by BAG. Decisions belong to a finding (limitation, kind, language, values) and carry over to the next audit."},
fr:{tb:{project:"Projet",drawing:"Dessin",sheet:"Feuille",rev:"Rév.",date:"Date (état LS)",freeze:"Gel",model:"Modèle",run:"Série",checked:"Contrôlé par",checkedV:"contrôles gelés"},lfine:"signalé – tous les constats probablement sans problème",lcheck:"signalé – à vérifier",fCheck:"À vérifier",fFine:"Probablement sans problème",
 triSplit:"Tri des signalés (affichage seulement)",triSplitV:"{c} à vérifier · {f} dont tous les constats sont probablement sans problème",
 rT5:"T5 nombres hors du passage",rT6:"T6 orthographe",rT7:"T7 négation",rT8:"T8 mêmes valeurs",
 rdT5:"T5 nombres hors du passage modifié : hors du passage modifié, le brouillon ne change que des nombres, exactement les valeurs que le changement allemand remplace (Ocrevus 944.61 → 731.07).",
 rdT6:"T6 orthographe : le changement allemand non repris n'est qu'orthographique (umlaut/ß, trait d'union comme Zeitpunkt → Zeit-punkt, majuscules, ponctuation) ou une terminaison flexionnelle (bedürfen → bedarf, erste → erst).",
 rdT7:"T7 négation : comptée comme un lecteur la compte (« nicht- » préfixe comme dans nicht-kleinzellig ne compte pas, « ne … pas » compte une fois, « personne » nom ne compte pas), le brouillon change le nombre de négations exactement comme l'allemand.",
 rdT8:"T8 mêmes valeurs : les deux côtés ajoutent et retirent les mêmes valeurs, seul le nombre d'occurrences diffère (Kyprolis : 20481 deux fois en allemand, une fois dans le brouillon).",
 legend:"Marques : ✓ prêt · ~ signalé, tous les constats probablement sans problème · ▲ signalé, à vérifier · ≠ l'ancien texte a déjà un problème (diverge de l'allemand, est dans une autre langue ou emploie un terme que l'OFSP a corrigé ailleurs) · h confié à un traducteur · A accepté · E accepté modifié · R renvoyé · touches j/k ou ↑/↓ naviguer, Entrée ouvrir, f/i langue, 1/2/3 décider, Ctrl/Cmd+Entrée enregistrer et suivant",
 famAll:"Accepter tous les brouillons prêts de cette famille ({n})",famAsk:"Accepter tels quels {n} brouillons prêts encore ouverts ({fr} FR, {it} IT) de la famille « {f} » ? Ceux déjà décidés, modifiés ou avec un avis sur l'ancien texte restent ouverts.",
 famYes:"Confirmer l'acceptation",famNo:"Annuler",famDone:"{n} brouillons prêts acceptés.",famNone:"Aucun brouillon prêt ouvert dans cette famille.",famOf:"Famille",famFilter:"afficher seulement cette famille",famChanges:"{n} changements",
 startOld:"Partir de l'ancien texte",startOldT:"Remplace le brouillon modifiable par l'ancien texte avec les changements de nombres appliqués par le code ({n}). « Rétablir le brouillon » annule.",startOldDone:"Ancien texte avec {n} changement(s) de nombres du code – à modifier maintenant.",
 xlf12:"Exporter XLIFF 1.2",
 acts:{exofficio:"Corriger d'office dans la prochaine publication",holder:"Aborder avec le titulaire lors du réexamen triennal",langsvc:"Transmettre au service linguistique",none:"Aucune mesure (formulation équivalente)",unclear:"Pas clair"},
 rev:"Réviseur ou réviseuse",revPh:"Nom (enregistré avec chaque décision)",decOn:"décidé le {d} par {n}",decOnAnon:"décidé le {d}",earlier:"lors d'un audit antérieur (état {s})",
 eqHead:"Formulation probablement équivalente ({n})",eqWhy:"Motif",eqShow:"afficher",eqHide:"replier",
 kinds:{number:"nombre",unit:"unité",language:"langue",editorial:"rédactionnel",terminology:"terminologie"},termOld:"ancien",termNew:"corrigé par l'OFSP en",termWhere:"déjà corrigé dans : {x}",
 aLegend:"Marques : K divergence connue, attestée dans les textes · D décidé · cadre rouge = valeur contradictoire · souligné = autre nombre · barre rouge = la langue qui diffère des deux autres (pas forcément la fausse). Décisions : quelle langue dit la bonne condition, et la mesure (corriger d'office, aborder avec le titulaire lors du réexamen triennal, service linguistique, aucune, pas clair). La demande de modification de la limitation (GÄL) est déposée par le titulaire, pas par l'OFSP. Les décisions valent par constat (limitation, type, langue, valeurs) et sont reprises au prochain audit."},
it:{tb:{project:"Progetto",drawing:"Disegno",sheet:"Foglio",rev:"Rev.",date:"Data (stato ES)",freeze:"Congelamento",model:"Modello",run:"Serie",checked:"Controllato da",checkedV:"controlli congelati"},lfine:"segnalata – tutti i rilievi probabilmente in ordine",lcheck:"segnalata – da verificare",fCheck:"Da verificare",fFine:"Probabilmente in ordine",
 triSplit:"Smistamento delle segnalate (solo visualizzazione)",triSplitV:"{c} da verificare · {f} con tutti i rilievi probabilmente in ordine",
 rT5:"T5 numeri fuori dal passo",rT6:"T6 ortografia",rT7:"T7 negazione",rT8:"T8 stessi valori",
 rdT5:"T5 numeri fuori dal passo modificato: fuori dal passo modificato la bozza cambia solo numeri, esattamente i valori che la modifica tedesca sostituisce (Ocrevus 944.61 → 731.07).",
 rdT6:"T6 ortografia: la modifica tedesca non ripresa è solo ortografica (umlaut/ß, trattino come Zeitpunkt → Zeit-punkt, maiuscole, punteggiatura) o una desinenza flessiva (bedürfen → bedarf, erste → erst).",
 rdT7:"T7 negazione: contata come la conta un lettore («nicht-» prefisso come in nicht-kleinzellig non conta, il francese «ne … pas» conta una volta, «personne» sostantivo non conta), la bozza cambia il numero di negazioni esattamente come il tedesco.",
 rdT8:"T8 stessi valori: entrambe le parti aggiungono e tolgono gli stessi valori, cambia solo quante volte un valore compare (Kyprolis: 20481 due volte nel tedesco, una volta nella bozza).",
 legend:"Segni: ✓ pronta · ~ segnalata, tutti i rilievi probabilmente in ordine · ▲ segnalata, da verificare · ≠ il vecchio testo ha già un problema (diverge dal tedesco, è in un'altra lingua o usa un termine che l'UFSP ha corretto altrove) · h affidata a un traduttore · A accettata · E accettata modificata · R rinviata · tasti j/k o ↑/↓ spostarsi, Invio aprire, f/i lingua, 1/2/3 decidere, Ctrl/Cmd+Invio salva e avanti",
 famAll:"Accetta tutte le bozze pronte di questa famiglia ({n})",famAsk:"Accettare così come sono {n} bozze pronte ancora aperte ({fr} FR, {it} IT) della famiglia «{f}»? Quelle già decise, modificate o con un avviso sul vecchio testo restano aperte.",
 famYes:"Conferma accettazione",famNo:"Annulla",famDone:"{n} bozze pronte accettate.",famNone:"Nessuna bozza pronta aperta in questa famiglia.",famOf:"Famiglia",famFilter:"mostra solo questa famiglia",famChanges:"{n} modifiche",
 startOld:"Parti dal vecchio testo",startOldT:"Sostituisce la bozza modificabile con il vecchio testo e le modifiche dei numeri applicate dal codice ({n}). «Ripristina la bozza» annulla.",startOldDone:"Vecchio testo con {n} modifica/he dei numeri del codice – ora da modificare.",
 xlf12:"Esporta XLIFF 1.2",
 acts:{exofficio:"Correggere d'ufficio nella prossima pubblicazione",holder:"Sollevare con il titolare nel riesame triennale",langsvc:"Inviare al servizio linguistico",none:"Nessuna misura (formulazione equivalente)",unclear:"Non chiaro"},
 rev:"Revisore o revisora",revPh:"Nome (salvato con ogni decisione)",decOn:"deciso il {d} da {n}",decOnAnon:"deciso il {d}",earlier:"in una verifica precedente (stato {s})",
 eqHead:"Formulazione probabilmente equivalente ({n})",eqWhy:"Motivo",eqShow:"mostra",eqHide:"richiudi",
 kinds:{number:"numero",unit:"unità",language:"lingua",editorial:"redazionale",terminology:"terminologia"},termOld:"vecchio",termNew:"corretto dall'UFSP in",termWhere:"già corretto in: {x}",
 aLegend:"Segni: K divergenza nota, confermata nei testi · D decisa · riquadro rosso = valore in contraddizione · sottolineato = altro numero · barra rossa = la lingua che differisce dalle altre due (non per forza quella sbagliata). Decisioni: quale lingua indica la condizione giusta, e la misura (correggere d'ufficio, sollevare con il titolare nel riesame triennale, servizio linguistico, nessuna, non chiaro). La domanda di modifica della limitazione (GÄL) è presentata dal titolare, non dall'UFSP. Le decisioni valgono per rilievo (limitazione, tipo, lingua, valori) e restano alla verifica successiva."}};
Object.keys(TX2).forEach(function(L){Object.keys(TX2[L]).forEach(function(k){TX[L][k]=TX2[L][k]})});
// round-4 strings: the two views as one system, lane, explanation language, legends, one decisions export, 27 + 11
var TX3={
de:{sub:"Prüfregister · Apertus entwirft, Code prüft",divergent:"Entwürfe, deren bisheriger Text schon ein Problem hat",
 tb:{project:"Projekt",drawing:"Zeichnung",sheet:"Blatt",rev:"Rev.",date:"Datum (SL-Stand)",lane:"Spur",model:"Modell",run:"Lauf",checked:"Geprüft von",checkedV:"eingefrorene Prüfungen"},
 lane70:"weniger Korrekturen (optional): 70B, zertifizierter Endpunkt",lane8:"Standard: 8B auf CPU, ohne Netz",laneDef:"Standardspur: 8B auf CPU, ohne Netz",drawingBy:"{l}, {n} Entwürfe von Apertus {m}",
 t1h:"Entwürfe",t1s:"Apertus entwirft, Code prüft",t1f:"{n} Entwürfe · {r} bereit · {f} markiert",
 t1t:"Apertus {m} schreibt für {c} deutsche Änderungen nur die Formulierung des französischen und italienischen Texts um; jede Zahl setzt der Code ein. Eingefrorene Prüfungen markieren jeden Entwurf als bereit oder markiert und sagen warum, in der Sprache der prüfenden Person.",
 t2h:"Registerprüfung",t2s:"nur Code, kein Modell",t2f:"{a} Befunde + {t} Terminologie-Hinweise",
 t2t:"Der Code liest alle {n} Limitationen auf DE/FR/IT (Stand {d}) und sucht Stellen, an denen die Sprachen schon heute auseinandergehen: {k} von {o} bekannten Abweichungen gefunden.",go:"öffnen →",
 aFindingsV:"{a} ({b}) + {t} Terminologie-Hinweise",aConf:"Bei Blindprüfung bestätigt",aConfV:"{r} von {a} Befunden ({k} bekannte + {x} neue) · {tr} von {t} Hinweisen",
 aTermHead:"Terminologie-Hinweise: vom BAG anderswo korrigierter Begriff ({n})",aAllN:"Alle ({a} + {t})",progA:"{x}/{a} + {y}/{t} entschieden",
 expl:"Erläuterung",allPass:"Alle Prüfungen bestanden.",moreN:"+ {n} weitere im Prüfdetail",chkDetail:"Prüfdetail: alle {n} Prüfungen, Rohausgabe mit internen Codes",
 exportDec:"Entscheide exportieren (JSON)",where:"Entscheide bleiben in diesem Browser, bis Sie sie exportieren. Massgeblich sind das ePL und der XLIFF-Rücklauf, nicht diese Seite.",
 keyReg:[["✓","bereit"],["~","markiert, alle Befunde wahrscheinlich in Ordnung"],["▲","markiert, zu prüfen"],["≠","bisheriger Text hat schon ein Problem"],["h","an Übersetzung übergeben"],["AER","übernommen / bearbeitet / zurückgewiesen"]],
 keyNum:["vom Code aus dem Deutschen gesetzte Zahl (Platzhalter A)","orange umrahmt: Zahl vom Modell geschrieben, prüfen","neu","entfernt"],
 keyAud:[["K","bekannte Abweichung"],["D","entschieden"],["v2","widersprüchlicher Wert"],["v1","weitere Zahl"],["bar","Sprache, die von den beiden anderen abweicht"]]},
en:{sub:"Review register · Apertus drafts, code checks",divergent:"Drafts whose old text already has a problem",
 tb:{project:"Project",drawing:"Drawing",sheet:"Sheet",rev:"Rev",date:"Date (SL snapshot)",lane:"Lane",model:"Model",run:"Run",checked:"Checked by",checkedV:"frozen checks"},
 lane70:"fewer edits (optional): 70B, certified endpoint",lane8:"default: 8B on CPU, air-gapped",laneDef:"default lane: 8B on CPU, air-gapped",drawingBy:"{l}, {n} drafts by Apertus {m}",
 t1h:"Drafts",t1s:"Apertus drafts, code checks",t1f:"{n} drafts · {r} ready · {f} flagged",
 t1t:"For {c} German changes, Apertus {m} rewrites only the wording of the French and Italian; code writes every number. Frozen checks mark each draft ready or flagged and say why, in the reviewer's language.",
 t2h:"Register audit",t2s:"code only, no model",t2f:"{a} findings + {t} terminology notices",
 t2t:"Code reads all {n} limitations in DE/FR/IT (feed of {d}) for places where the languages already disagree: {k} of {o} known divergences found.",go:"open →",
 aFindingsV:"{a} ({b}) + {t} terminology notices",aConf:"Confirmed on blind check",aConfV:"{r} of {a} findings ({k} known + {x} new) · {tr} of {t} notices",
 aTermHead:"Terminology notices: a term BAG corrected elsewhere ({n})",aAllN:"All ({a} + {t})",progA:"{x}/{a} + {y}/{t} decided",
 expl:"explanation",allPass:"Every check passed.",moreN:"+ {n} more in the check detail",chkDetail:"Check detail: all {n} checks, raw output with internal codes",
 exportDec:"Export decisions (JSON)",where:"Decisions stay in this browser until you export them. The system of record is ePL and the XLIFF round trip, not this page.",
 keyReg:[["✓","ready"],["~","flagged, all findings probably fine"],["▲","flagged, to check"],["≠","old text already has a problem"],["h","routed to a translator"],["AER","accepted / edited / sent back"]],
 keyNum:["number placed by code from the German (slot A)","orange frame: number the model wrote, check it","new","removed"],
 keyAud:[["K","known divergence"],["D","decided"],["v2","conflicting value"],["v1","other number"],["bar","language that differs from the other two"]]},
fr:{sub:"Registre de révision · Apertus rédige, le code contrôle",divergent:"Brouillons dont l'ancien texte a déjà un problème",
 tb:{project:"Projet",drawing:"Dessin",sheet:"Feuille",rev:"Rév.",date:"Date (état LS)",lane:"Voie",model:"Modèle",run:"Série",checked:"Contrôlé par",checkedV:"contrôles gelés"},
 lane70:"moins de corrections (optionnelle) : 70B, point d'accès certifié",lane8:"par défaut : 8B sur CPU, hors réseau",laneDef:"voie par défaut : 8B sur CPU, hors réseau",drawingBy:"{l}, {n} brouillons d'Apertus {m}",
 t1h:"Brouillons",t1s:"Apertus rédige, le code contrôle",t1f:"{n} brouillons · {r} prêts · {f} signalés",
 t1t:"Pour {c} changements allemands, Apertus {m} ne réécrit que la formulation française et italienne ; le code écrit chaque nombre. Des contrôles gelés marquent chaque brouillon prêt ou signalé et disent pourquoi, dans la langue du réviseur.",
 t2h:"Audit du registre",t2s:"code seul, sans modèle",t2f:"{a} constats + {t} avis de terminologie",
 t2t:"Le code lit les {n} limitations en DE/FR/IT (état du {d}) et cherche les endroits où les langues divergent déjà : {k} des {o} divergences connues trouvées.",go:"ouvrir →",
 aFindingsV:"{a} ({b}) + {t} avis de terminologie",aConf:"Confirmés au contrôle à l'aveugle",aConfV:"{r} des {a} constats ({k} connus + {x} nouveaux) · {tr} des {t} avis",
 aTermHead:"Avis de terminologie : terme corrigé ailleurs par l'OFSP ({n})",aAllN:"Tous ({a} + {t})",progA:"{x}/{a} + {y}/{t} décidés",
 expl:"explication",allPass:"Tous les contrôles sont passés.",moreN:"+ {n} autre(s) dans le détail des contrôles",chkDetail:"Détail des contrôles : les {n} contrôles, sortie brute avec codes internes",
 exportDec:"Exporter les décisions (JSON)",where:"Les décisions restent dans ce navigateur jusqu'à leur export. Le système de référence est l'ePL et l'aller-retour XLIFF, pas cette page.",
 keyReg:[["✓","prêt"],["~","signalé, tous les constats probablement sans problème"],["▲","signalé, à vérifier"],["≠","l'ancien texte a déjà un problème"],["h","confié à un traducteur"],["AER","accepté / modifié / renvoyé"]],
 keyNum:["nombre placé par le code à partir de l'allemand (code A)","cadre orange : nombre écrit par le modèle, à vérifier","nouveau","supprimé"],
 keyAud:[["K","divergence connue"],["D","décidé"],["v2","valeur contradictoire"],["v1","autre nombre"],["bar","langue qui diffère des deux autres"]]},
it:{sub:"Registro di revisione · Apertus redige, il codice controlla",divergent:"Bozze il cui vecchio testo ha già un problema",
 tb:{project:"Progetto",drawing:"Disegno",sheet:"Foglio",rev:"Rev.",date:"Data (stato ES)",lane:"Corsia",model:"Modello",run:"Serie",checked:"Controllato da",checkedV:"controlli congelati"},
 lane70:"meno correzioni (opzionale): 70B, endpoint certificato",lane8:"predefinita: 8B su CPU, senza rete",laneDef:"corsia predefinita: 8B su CPU, senza rete",drawingBy:"{l}, {n} bozze di Apertus {m}",
 t1h:"Bozze",t1s:"Apertus redige, il codice controlla",t1f:"{n} bozze · {r} pronte · {f} segnalate",
 t1t:"Per {c} modifiche tedesche, Apertus {m} riscrive solo la formulazione francese e italiana; ogni numero lo scrive il codice. Controlli congelati segnano ogni bozza come pronta o segnalata e dicono perché, nella lingua di chi rivede.",
 t2h:"Verifica del registro",t2s:"solo codice, nessun modello",t2f:"{a} rilievi + {t} avvisi di terminologia",
 t2t:"Il codice legge tutte le {n} limitazioni in DE/FR/IT (stato del {d}) e cerca i punti in cui le lingue già divergono: trovate {k} delle {o} divergenze note.",go:"apri →",
 aFindingsV:"{a} ({b}) + {t} avvisi di terminologia",aConf:"Confermati al controllo alla cieca",aConfV:"{r} di {a} rilievi ({k} noti + {x} nuovi) · {tr} di {t} avvisi",
 aTermHead:"Avvisi di terminologia: termine corretto altrove dall'UFSP ({n})",aAllN:"Tutti ({a} + {t})",progA:"{x}/{a} + {y}/{t} decisi",
 expl:"spiegazione",allPass:"Tutti i controlli superati.",moreN:"+ {n} altro/i nel dettaglio dei controlli",chkDetail:"Dettaglio dei controlli: tutti i {n} controlli, uscita grezza con codici interni",
 exportDec:"Esporta le decisioni (JSON)",where:"Le decisioni restano in questo browser finché non le esportate. Il sistema di riferimento è l'ePL con il ciclo XLIFF, non questa pagina.",
 keyReg:[["✓","pronta"],["~","segnalata, tutti i rilievi probabilmente in ordine"],["▲","segnalata, da verificare"],["≠","il vecchio testo ha già un problema"],["h","affidata a un traduttore"],["AER","accettata / modificata / rinviata"]],
 keyNum:["numero inserito dal codice a partire dal tedesco (codice A)","riquadro arancione: numero scritto dal modello, da verificare","nuovo","tolto"],
 keyAud:[["K","divergenza nota"],["D","decisa"],["v2","valore in contraddizione"],["v1","altro numero"],["bar","lingua che differisce dalle altre due"]]}};
Object.keys(TX3).forEach(function(L){Object.keys(TX3[L]).forEach(function(k){TX[L][k]=TX3[L][k]})});
// round-5 strings: the register audit for the scientific officer (issues, dating, full texts, several actions, filing CSV)
// and the drafts banner (past changes used to test the tool; drafts are for translators)
var TX4={
de:{aLead:"Jede Zeile ist ein Fall: eine Stelle, an der der deutsche, französische und italienische Text einer Limitation in der SL vom {d} Verschiedenes sagen, vom Code ohne Modell gefunden. Alle drei Sprachfassungen sind gleichermassen verbindlich: Richtig ist die Fassung, die dem Entscheid des BAG entspricht, und welche das ist, weiss die Prüfung nicht – bitte mit dem Entscheiddossier abgleichen. {a} Befunde + {t} Terminologie-Hinweise in {n} Fällen; ein Entscheid zu einem Fall gilt für alle seine Befunde (jeder lässt sich auch einzeln entscheiden).",
 aKnownHead:"Vor dieser Prüfung von unserer früheren Erhebung erfasst (von Hand geprüft): {k} von {n} gefunden",aOtherHead:"Weitere Befunde der Prüfung",
 aTermHead:"Terminologie-Hinweise: vom BAG anderswo korrigierter Begriff ({n} Fälle, {m} Hinweise)",eqHead:"Wahrscheinlich gleichwertige Formulierung ({n})",
 aKnown:"Vor dieser Prüfung erfasst (frühere Erhebung)",aConf:"Von blinden KI-Annotatoren (Claude) bestätigt",aConfV:"{r} von {a} Befunden ({k} früher erfasst + {x} neu) · {tr} von {t} Hinweisen",
 aFindingsV:"{a} ({b}) + {t} Terminologie-Hinweise, in {n} Fällen",t2f:"{a} Befunde + {t} Terminologie-Hinweise · {n} Fälle",
 t2t:"Der Code liest alle {n} Limitationen auf DE/FR/IT (Stand {d}) und sucht Stellen, an denen die Sprachen schon heute auseinandergehen; er findet {k} der {o} Abweichungen, die unsere frühere Erhebung erfasst hatte.",
 dA:"in allen {n} Ständen seit {d} vorhanden, dem frühesten, den die Prüfung vergleicht (kann älter sein)",dB:"erstmals zwischen {p} und {d} aufgetreten; seither in allen {n} Ständen",dC:"erstmals am {d}; seither in {n} von {m} Ständen",
 newSince:"Neu seit",newAny:"jedem Stand",aRight:"Welche Fassung entspricht dem Entscheid?",rUnclear:"noch unklar",aAction:"Massnahmen · Notiz",
 acts:{fix:"Text berichtigen",langsvc:"An den Sprachdienst",decfile:"Entscheiddossier prüfen",pending:"Schon in einer hängigen Änderung",none:"Keine Massnahme (gleichwertige Formulierung)",falsealarm:"Fehlalarm",
  exofficio:"Von Amtes wegen in der nächsten Publikation berichtigen",holder:"Mit der Zulassungsinhaberin in der dreijährlichen Überprüfung aufnehmen",unclear:"Unklar"},
 ahNo:"Fall",aKind:"Art",aOdd:"Weicht ab",ft:"Volltexte DE · FR · IT",ftN:"{n} Limitationen",ftNone:"Volltexte nicht in diesem Build",mem:"{n} Befunde in diesem Fall",
 memFollow:"folgt dem Entscheid zum Fall",memOwn:"einzeln entschieden",memSplit:"Einzeln entscheiden",memJoin:"Dem Entscheid zum Fall folgen",appliesAll:"gilt für alle {n} Befunde",someOwn:"{n} einzeln entschieden",
 csvIss:"Fälle exportieren (CSV, für GEVER)",aCsv:"Befunde exportieren (CSV)",yes:"ja",no2:"nein",
 csvHead:["Fall","Befunde","Produkt","Limitation","Sprachen","Art","Werte","Datierung","Vor dieser Prüfung erfasst","Fassung gemäss Entscheid","Massnahmen","Notiz","Entschieden am","Entschieden von","Prüfung (SL-Stand)","Einzeln entschieden"],
 progA:"{i}/{n} Fälle entschieden ({x}/{a} + {y}/{t} Befunde)",aAllN:"Alle ({n} Fälle)",aKnownF:"Früher erfasst",aShownI:"{n} Fälle angezeigt ({m} Befunde)",aNone:"Kein Fall entspricht diesen Filtern.",
 keyAud:[["K","vor dieser Prüfung erfasst (frühere Erhebung)"],["D","entschieden"],["v2","widersprüchlicher Wert"],["v1","weitere Zahl"],["bar","Sprache, die von den beiden anderen abweicht"]],
 grouping:"Befunde bilden einen Fall, wenn sie dieselbe Abweichung (dieselben widersprüchlichen Werte, Einheit, Sprache, denselben Tippfehler oder dasselbe Begriffspaar) im selben Text nennen: in derselben Limitation, einer Geschwisterlimitation desselben Produkts oder derselben zitierten Passage; ein Tippfehler, der laut Prüfung eine Zahlabweichung erklärt, gehört zu ihr; ein Terminologie-Hinweis ist ein Fall pro Sprache und Begriffspaar.",
 aLegend:"Zeichen: K vor dieser Prüfung von unserer früheren Erhebung erfasst (von Hand geprüft) · D entschieden · rot umrahmt = widersprüchlicher Wert · unterstrichen = weitere Zahl · roter Balken = die Sprache, die von den beiden anderen abweicht (nicht unbedingt die falsche). Fälle: {g} Entscheide: welche Fassung dem Entscheid des BAG entspricht (das weiss die Prüfung nicht) und eine oder mehrere Massnahmen. Ein Entscheid zu einem Fall wird bei jedem seiner Befunde gespeichert (Limitation, Art, Sprache, Werte) und bleibt in der nächsten Prüfung erhalten.",
 tbA:{rev:"Fälle",lane:"Methode",model:"Verglichen mit",run:"Geprüfte Limitationen",checked:"Bestätigt durch"},revA:"{n} Fälle · {f} Befunde",laneA:"nur Code, kein Modell",modelA:"{n} SL-Stände, {a} – {b}",checkedA:"blinde KI-Annotatoren (Claude)",drawA:"Registerprüfung DE/FR/IT, SL-Stand {d}",
 dB1:"Diese {c} deutschen Änderungen sind vergangene SL-Änderungen{p}, mit denen Gleichlaut getestet wurde – keine offene Arbeit: Das BAG hat ihr Französisch und Italienisch bereits publiziert. ",
 dB2:"Die Entwürfe sind für die Übersetzung bestimmt (in STAR Transit, über XLIFF); ob ein Entwurf übernommen, bearbeitet oder zurückgewiesen wird, entscheidet die Übersetzerin oder der Übersetzer."},
en:{aLead:"Each row is one issue: a place where the German, French and Italian texts of a limitation say different things in the SL of {d}, found by code without a model. All three language versions are equally binding, so the right version is the one that matches BAG's decision, and the audit cannot tell which one that is: check the decision file. {a} findings + {t} terminology notices in {n} issues; a decision on an issue applies to all its findings (each can still be decided separately).",
 aKnownHead:"Listed before this audit by our earlier census (hand-checked): {k} of {n} found",aOtherHead:"Further findings of the audit",
 aTermHead:"Terminology notices: a term BAG corrected elsewhere ({n} issues, {m} notices)",eqHead:"Probably equivalent wording ({n})",
 aKnown:"Listed before this audit (our earlier census)",aConf:"Confirmed by blind AI annotators (Claude)",aConfV:"{r} of {a} findings ({k} listed earlier + {x} new) · {tr} of {t} notices",
 aFindingsV:"{a} ({b}) + {t} terminology notices, in {n} issues",t2f:"{a} findings + {t} terminology notices · {n} issues",
 t2t:"Code reads all {n} limitations in DE/FR/IT (feed of {d}) for places where the languages already disagree; it finds {k} of the {o} divergences our earlier census had listed.",
 dA:"present in all {n} snapshots since {d}, the earliest the audit compares (it may be older)",dB:"first appeared between {p} and {d}; present in all {n} snapshots since then",dC:"first seen on {d}; present in {n} of the {m} snapshots since then",
 newSince:"New since",newAny:"any snapshot",aRight:"Which version matches the decision?",rUnclear:"not clear yet",aAction:"Actions · note",
 acts:{fix:"Correct the text",langsvc:"Send to the language service",decfile:"Check the decision file",pending:"Already in a pending change",none:"No action (equivalent wording)",falsealarm:"False alarm",
  exofficio:"Correct ex officio in the next publication",holder:"Raise with the holder in the triennial review",unclear:"Unclear"},
 ahNo:"Issue",aKind:"Kind",aOdd:"Differs",ft:"Full texts DE · FR · IT",ftN:"{n} limitations",ftNone:"full texts not in this build",mem:"{n} findings in this issue",
 memFollow:"follows the issue decision",memOwn:"decided separately",memSplit:"Decide separately",memJoin:"Follow the issue decision",appliesAll:"applies to all {n} findings",someOwn:"{n} decided separately",
 csvIss:"Export issues (CSV, for GEVER)",aCsv:"Export findings (CSV)",yes:"yes",no2:"no",
 csvHead:["Issue","Findings","Product","Limitation","Languages","Kind","Values","Dating","Listed before this audit","Version matching the decision","Actions","Note","Decided on","Decided by","Audit (SL of)","Decided separately"],
 progA:"{i}/{n} issues decided ({x}/{a} + {y}/{t} findings)",aAllN:"All ({n} issues)",aKnownF:"Listed earlier",aShownI:"{n} issues shown ({m} findings)",aNone:"No issue matches these filters.",
 keyAud:[["K","listed before this audit (earlier census)"],["D","decided"],["v2","conflicting value"],["v1","other number"],["bar","language that differs from the other two"]],
 grouping:"findings are one issue when they name the same difference (the same conflicting values, unit, language, typo or term pair) on the same text: the same limitation, a sibling limitation of the same product, or the same quoted passage; a typo the audit says explains a number difference joins it; a terminology notice is one issue per language and term pair.",
 aLegend:"Marks: K listed before this audit by our earlier census (hand-checked) · D decided · red box = conflicting value · underlined = other number · red bar = the language that differs from the other two (not necessarily the wrong one). Issues: {g} Decisions: which version matches BAG's decision (the audit cannot know), and one or more actions. A decision on an issue is stored with each of its findings (limitation, kind, language, values) and carries over to the next audit.",
 tbA:{rev:"Issues",lane:"Method",model:"Compared with",run:"Limitations checked",checked:"Confirmed by"},revA:"{n} issues · {f} findings",laneA:"code only, no model",modelA:"{n} SL snapshots, {a} – {b}",checkedA:"blind AI annotators (Claude)",drawA:"Register audit DE/FR/IT, SL of {d}",
 dB1:"These {c} German changes are past SL updates{p} used to test Gleichlaut, not pending work: BAG has already published their French and Italian. ",
 dB2:"The drafts are meant for translators (in STAR Transit, via XLIFF); accepting, editing or sending back a draft is the translator's decision."},
fr:{aLead:"Chaque ligne est un cas : un endroit où les textes allemand, français et italien d'une limitation disent des choses différentes dans la LS du {d}, trouvé par le code, sans modèle. Les trois versions linguistiques font également foi : la bonne version est celle qui correspond à la décision de l'OFSP, et l'audit ne peut pas savoir laquelle ; vérifiez-la dans le dossier de décision. {a} constats + {t} avis de terminologie en {n} cas ; une décision sur un cas vaut pour tous ses constats (chacun peut aussi être décidé séparément).",
 aKnownHead:"Recensées avant cet audit par notre inventaire antérieur (vérifiées à la main) : {k} sur {n} trouvées",aOtherHead:"Autres constats de l'audit",
 aTermHead:"Avis de terminologie : terme corrigé ailleurs par l'OFSP ({n} cas, {m} avis)",eqHead:"Formulation probablement équivalente ({n})",
 aKnown:"Recensées avant cet audit (inventaire antérieur)",aConf:"Confirmés par des annotateurs IA à l'aveugle (Claude)",aConfV:"{r} des {a} constats ({k} déjà recensés + {x} nouveaux) · {tr} des {t} avis",
 aFindingsV:"{a} ({b}) + {t} avis de terminologie, en {n} cas",t2f:"{a} constats + {t} avis de terminologie · {n} cas",
 t2t:"Le code lit les {n} limitations en DE/FR/IT (état du {d}) et cherche les endroits où les langues divergent déjà ; il trouve {k} des {o} divergences que notre inventaire antérieur avait recensées.",
 dA:"présent dans les {n} états depuis le {d}, le plus ancien que l'audit compare (peut être plus ancien)",dB:"apparu entre le {p} et le {d} ; présent depuis dans les {n} états",dC:"vu pour la première fois le {d} ; présent dans {n} des {m} états depuis",
 newSince:"Nouveau depuis",newAny:"tout état",aRight:"Quelle version correspond à la décision ?",rUnclear:"pas encore clair",aAction:"Mesures · remarque",
 acts:{fix:"Corriger le texte",langsvc:"Transmettre au service linguistique",decfile:"Vérifier le dossier de décision",pending:"Déjà dans une modification en cours",none:"Aucune mesure (formulation équivalente)",falsealarm:"Fausse alerte",
  exofficio:"Corriger d'office dans la prochaine publication",holder:"Aborder avec le titulaire lors du réexamen triennal",unclear:"Pas clair"},
 ahNo:"Cas",aKind:"Type",aOdd:"Diverge",ft:"Textes complets DE · FR · IT",ftN:"{n} limitations",ftNone:"textes complets absents de cette version",mem:"{n} constats dans ce cas",
 memFollow:"suit la décision du cas",memOwn:"décidé séparément",memSplit:"Décider séparément",memJoin:"Suivre la décision du cas",appliesAll:"vaut pour les {n} constats",someOwn:"{n} décidé(s) séparément",
 csvIss:"Exporter les cas (CSV, pour GEVER)",aCsv:"Exporter les constats (CSV)",yes:"oui",no2:"non",
 csvHead:["Cas","Constats","Produit","Limitation","Langues","Type","Valeurs","Datation","Recensé avant cet audit","Version conforme à la décision","Mesures","Remarque","Décidé le","Décidé par","Audit (état LS)","Décidé séparément"],
 progA:"{i}/{n} cas décidés ({x}/{a} + {y}/{t} constats)",aAllN:"Tous ({n} cas)",aKnownF:"Déjà recensés",aShownI:"{n} cas affichés ({m} constats)",aNone:"Aucun cas ne correspond à ces filtres.",
 keyAud:[["K","recensé avant cet audit (inventaire antérieur)"],["D","décidé"],["v2","valeur contradictoire"],["v1","autre nombre"],["bar","langue qui diffère des deux autres"]],
 grouping:"des constats forment un cas quand ils nomment la même divergence (mêmes valeurs contradictoires, unité, langue, coquille ou paire de termes) dans le même texte : la même limitation, une limitation sœur du même produit ou le même passage cité ; une coquille qui, selon l'audit, explique une divergence de nombre la rejoint ; un avis de terminologie forme un cas par langue et paire de termes.",
 aLegend:"Marques : K recensé avant cet audit par notre inventaire antérieur (vérifié à la main) · D décidé · cadre rouge = valeur contradictoire · souligné = autre nombre · barre rouge = la langue qui diffère des deux autres (pas forcément la fausse). Cas : {g} Décisions : quelle version correspond à la décision de l'OFSP (l'audit ne peut pas le savoir), et une ou plusieurs mesures. Une décision sur un cas est enregistrée avec chacun de ses constats (limitation, type, langue, valeurs) et reprise au prochain audit.",
 tbA:{rev:"Cas",lane:"Méthode",model:"Comparé à",run:"Limitations contrôlées",checked:"Confirmé par"},revA:"{n} cas · {f} constats",laneA:"code seul, sans modèle",modelA:"{n} états de la LS, {a} – {b}",checkedA:"annotateurs IA à l'aveugle (Claude)",drawA:"Audit du registre DE/FR/IT, LS du {d}",
 dB1:"Ces {c} changements allemands sont des modifications passées de la LS{p}, utilisées pour tester Gleichlaut, pas du travail en attente : l'OFSP a déjà publié leur français et leur italien. ",
 dB2:"Les brouillons sont destinés aux traducteurs (dans STAR Transit, via XLIFF) ; accepter, modifier ou renvoyer un brouillon est la décision du traducteur ou de la traductrice."},
it:{aLead:"Ogni riga è un caso: un punto in cui i testi tedesco, francese e italiano di una limitazione dicono cose diverse nell'ES del {d}, trovato dal codice, senza modello. Le tre versioni linguistiche fanno ugualmente fede: quella giusta è la versione conforme alla decisione dell'UFSP, e la verifica non può sapere quale sia; controllarla nel dossier della decisione. {a} rilievi + {t} avvisi di terminologia in {n} casi; una decisione su un caso vale per tutti i suoi rilievi (ognuno può anche essere deciso separatamente).",
 aKnownHead:"Censite prima di questa verifica dal nostro censimento precedente (controllate a mano): {k} su {n} trovate",aOtherHead:"Altri rilievi della verifica",
 aTermHead:"Avvisi di terminologia: termine corretto altrove dall'UFSP ({n} casi, {m} avvisi)",eqHead:"Formulazione probabilmente equivalente ({n})",
 aKnown:"Censite prima di questa verifica (censimento precedente)",aConf:"Confermati da annotatori IA alla cieca (Claude)",aConfV:"{r} di {a} rilievi ({k} già censiti + {x} nuovi) · {tr} di {t} avvisi",
 aFindingsV:"{a} ({b}) + {t} avvisi di terminologia, in {n} casi",t2f:"{a} rilievi + {t} avvisi di terminologia · {n} casi",
 t2t:"Il codice legge tutte le {n} limitazioni in DE/FR/IT (stato del {d}) e cerca i punti in cui le lingue già divergono; ne trova {k} delle {o} divergenze censite dal nostro censimento precedente.",
 dA:"presente in tutti i {n} stati dal {d}, il più vecchio che la verifica confronta (può essere più vecchio)",dB:"comparso tra il {p} e il {d}; da allora presente in tutti i {n} stati",dC:"visto per la prima volta il {d}; presente in {n} dei {m} stati da allora",
 newSince:"Nuovo dal",newAny:"qualsiasi stato",aRight:"Quale versione corrisponde alla decisione?",rUnclear:"non ancora chiaro",aAction:"Misure · nota",
 acts:{fix:"Correggere il testo",langsvc:"Inviare al servizio linguistico",decfile:"Verificare il dossier della decisione",pending:"Già in una modifica pendente",none:"Nessuna misura (formulazione equivalente)",falsealarm:"Falso allarme",
  exofficio:"Correggere d'ufficio nella prossima pubblicazione",holder:"Sollevare con il titolare nel riesame triennale",unclear:"Non chiaro"},
 ahNo:"Caso",aKind:"Tipo",aOdd:"Diverge",ft:"Testi completi DE · FR · IT",ftN:"{n} limitazioni",ftNone:"testi completi assenti in questa versione",mem:"{n} rilievi in questo caso",
 memFollow:"segue la decisione del caso",memOwn:"deciso separatamente",memSplit:"Decidere separatamente",memJoin:"Seguire la decisione del caso",appliesAll:"vale per tutti i {n} rilievi",someOwn:"{n} deciso/i separatamente",
 csvIss:"Esporta i casi (CSV, per GEVER)",aCsv:"Esporta i rilievi (CSV)",yes:"sì",no2:"no",
 csvHead:["Caso","Rilievi","Prodotto","Limitazione","Lingue","Tipo","Valori","Datazione","Censito prima di questa verifica","Versione conforme alla decisione","Misure","Nota","Deciso il","Deciso da","Verifica (stato ES)","Deciso separatamente"],
 progA:"{i}/{n} casi decisi ({x}/{a} + {y}/{t} rilievi)",aAllN:"Tutti ({n} casi)",aKnownF:"Già censiti",aShownI:"{n} casi mostrati ({m} rilievi)",aNone:"Nessun caso corrisponde a questi filtri.",
 keyAud:[["K","censito prima di questa verifica (censimento precedente)"],["D","deciso"],["v2","valore in contraddizione"],["v1","altro numero"],["bar","lingua che differisce dalle altre due"]],
 grouping:"i rilievi formano un caso quando indicano la stessa divergenza (stessi valori in contraddizione, unità, lingua, refuso o coppia di termini) nello stesso testo: la stessa limitazione, una limitazione sorella dello stesso prodotto o lo stesso passo citato; un refuso che secondo la verifica spiega una divergenza di numero vi si aggiunge; un avviso di terminologia è un caso per lingua e coppia di termini.",
 aLegend:"Segni: K censito prima di questa verifica dal nostro censimento precedente (controllato a mano) · D deciso · riquadro rosso = valore in contraddizione · sottolineato = altro numero · barra rossa = la lingua che differisce dalle altre due (non per forza quella sbagliata). Casi: {g} Decisioni: quale versione corrisponde alla decisione dell'UFSP (la verifica non può saperlo), e una o più misure. Una decisione su un caso è salvata con ciascuno dei suoi rilievi (limitazione, tipo, lingua, valori) e resta alla verifica successiva.",
 tbA:{rev:"Casi",lane:"Metodo",model:"Confrontato con",run:"Limitazioni controllate",checked:"Confermato da"},revA:"{n} casi · {f} rilievi",laneA:"solo codice, nessun modello",modelA:"{n} stati dell'ES, {a} – {b}",checkedA:"annotatori IA alla cieca (Claude)",drawA:"Verifica del registro DE/FR/IT, ES del {d}",
 dB1:"Queste {c} modifiche tedesche sono modifiche passate dell'ES{p}, usate per testare Gleichlaut, non lavoro in sospeso: l'UFSP ha già pubblicato il loro francese e italiano. ",
 dB2:"Le bozze sono destinate ai traduttori (in STAR Transit, tramite XLIFF); accettare, modificare o rinviare una bozza è decisione del traduttore o della traduttrice."}};
Object.keys(TX4).forEach(function(L){Object.keys(TX4[L]).forEach(function(k){TX[L][k]=TX4[L][k]})});
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
// one numbering: a change is numbered by its address (#wb013 is No. wb013); index numbers only for records without one
G.forEach(function(g,i){g.no=/^wb\d+$/i.test(g.pair)?g.pair:("00"+(i+1)).slice(-3);g.deNew=plain(g.de,false);g.deOld=plain(g.de,true);["fr","it"].forEach(function(L){var it=g.items[L];if(it){it.draft=it.status==="human"?"":plain(it.segs,false);it.g=g}})});
var ITEMS=[];G.forEach(function(g){["fr","it"].forEach(function(L){if(g.items[L])ITEMS.push(g.items[L])})});
var FAML={};D.families.forEach(function(f){FAML[f[0]]=f[2]});
// "start from the old text": the old target with the rules lane's number changes, stored as edits [start, end, text] of the old target
ITEMS.forEach(function(it){if(!it.rt)return;var o=plain(it.segs,true),ops=it.rt[0].slice().sort(function(a,b){return b[0]-a[0]});
 ops.forEach(function(op){o=o.slice(0,op[0])+op[2]+o.slice(op[1])});it.rt=[o,it.rt[1]]});
function dec(it){return S.dec[it.key]}
function oldIssue(it){return !!(it.banner||it.corr||(it.old&&it.old.length))}
// marks: ✓ ready · ~ flagged, all findings probably fine · ▲ flagged, to check · ≠ old text diverges · h routed to a
// translator · decided: A accepted, E accepted edited, R sent back (inverted tags)
function mark(it){if(!it)return ['<span class="mk o">·</span>',""];var d=dec(it);
 if(d)return ['<span class="mk"><span class="lt">'+(d.decision==="accept"?"A":d.decision==="accept-edited"?"E":"R")+'</span></span>',d.decision];
 if(oldIssue(it))return ['<span class="mk r">≠</span>',"divergent"];
 if(it.status==="human")return ['<span class="mk">h</span>',"human"];
 return it.status==="ready"?['<span class="mk">✓</span>',"ready"]:it.lvl==="fine"?['<span class="mk f">~</span>',"fine"]:['<span class="mk r">▲</span>',"flagged"]}
// ------------------------------------------------------------------ header and chrome
var TAB="drafts";        // landing view: 01 Drafts (Apertus drafts, code checks); #audit opens 02 Register audit, #wbNNN a draft
function kv(id,rows){$(id).innerHTML=rows.map(function(r){return "<dt"+(r[3]?' title="'+esc(r[3])+'"':"")+">"+esc(r[0])+"</dt><dd"+(r[2]?' class="'+r[2]+'"':"")+">"+esc(r[1])+"</dd>"}).join("")}
function ddate(s){return /^\d{8}$/.test(s||"")?s.slice(6,8)+"."+s.slice(4,6)+"."+s.slice(0,4):(s||"?")}
function grp(n){var s=String(n==null?"—":n);return /^\d{4,6}$/.test(s)?s.slice(0,-3)+(UL==="en"?",":"’")+s.slice(-3):s}
var MS=M.lane==="70b"?"70B":M.lane==="8b"?"8B":M.model;
function keyHTML(items){return items.map(function(k){var g=k[0],m;
  if(g==="AER")m='<span class="mk"><span class="lt">A</span></span><span class="mk"><span class="lt">E</span></span><span class="mk"><span class="lt">R</span></span>';
  else if(g==="K")m='<span class="lt s">K</span>';else if(g==="D")m='<span class="lt">D</span>';
  else if(g==="v2")m='<span class="v2">6%</span>';else if(g==="v1")m='<span class="v1">12</span>';else if(g==="bar")m='<span class="bar"></span>';
  else m='<span class="mk'+(g==="▲"||g==="≠"?" r":g==="~"?" f":"")+'">'+esc(g)+"</span>";
  return "<span>"+m+" "+esc(k[1])+"</span>"}).join("")}
function chrome(){
 document.documentElement.lang=UL;$("l-ui").textContent=t("ui");applyTheme();
 $("sub").textContent=t("sub");
 var fz0=(M.pipeline.match(/freeze sha256:([0-9a-f]+)/)||[])[1]||"",TB=t("tb"),C=D.counts;
 var TBA=TAB==="audit"&&AU?t("tbA"):{};document.querySelectorAll("[data-tb]").forEach(function(e){e.textContent=TBA[e.dataset.tb]||TB[e.dataset.tb]});
 $("tb-drawing").textContent=fmt(t("drawingBy"),{l:M.label,n:C.items,m:MS});
 $("tb-sheet").textContent=AU?(TAB==="drafts"?"1 / 2 · "+t("tabDrafts"):"2 / 2 · "+t("tabAudit")):"1 / 1 · "+t("tabDrafts");
 $("tb-rev").textContent=M.rev||"—";$("tb-date").textContent=ddate(AU?AU.meta.date:D.snap);
 $("tb-lane").innerHTML=M.lane==="70b"?esc(t("lane70"))+"<small>"+esc(t("laneDef"))+"</small>":M.lane==="8b"?esc(t("lane8")):"—";
 $("tb-model").textContent=M.model;$("tb-run").textContent=M.run;
 $("tb-checked").textContent=TB.checkedV+" "+(M.stack||"g3")+(fz0?" · freeze "+fz0.slice(0,12):"");
 if(TAB==="audit"&&AU){var am0=AU.meta,sn0=am0.snapshots||[];$("tb-drawing").textContent=fmt(t("drawA"),{d:ddate(am0.date)});
  $("tb-rev").textContent=fmt(t("revA"),{n:AU.issues.length,f:AU.rows.length});$("tb-lane").textContent=t("laneA");
  $("tb-model").textContent=sn0.length?fmt(t("modelA"),{n:sn0.length,a:ddate(sn0[0]),b:ddate(sn0[sn0.length-1])}):"—";
  $("tb-run").textContent=am0.n_limitations!=null?grp(am0.n_limitations):"—";$("tb-checked").textContent=t("checkedA")}
 // drafts banner: what the drafts are (past changes used to test the tool, or the records of a run) and whose decision they are
 var bn=$("d-band");if(TAB==="drafts"){bn.hidden=false;bn.textContent=(M.custom?"":fmt(t("dB1"),{c:C.changes,p:M.period?" ("+M.period+")":""}))+t("dB2")}else bn.hidden=true;
 $("x-dec").textContent=t("exportDec");$("where").textContent=t("where");
 $("t-audit").hidden=!AU;
 $("t-drafts").innerHTML='<span class="th"><b>01</b>'+esc(t("t1h"))+" · "+esc(t("t1s"))+'</span><span class="tf">'+esc(fmt(t("t1f"),{n:C.items,r:C.ready,f:C.flagged}))+
  '</span><span class="tt">'+esc(fmt(t("t1t"),{c:C.changes,m:MS}))+'</span><span class="go">'+esc(t("go"))+"</span>";
 if(AU){var am=AU.meta;$("t-audit").innerHTML='<span class="th"><b>02</b>'+esc(t("t2h"))+" · "+esc(t("t2s"))+'</span><span class="tf">'+esc(fmt(t("t2f"),{a:am.main,t:am.term,n:AU.issues.length}))+
  '</span><span class="tt">'+esc(fmt(t("t2t"),{n:grp(am.n_limitations),d:ddate(am.date),k:am.known_found!=null?am.known_found:am.known_ids.length,o:am.known_of!=null?am.known_of:am.known_ids.length}))+
  '</span><span class="go">'+esc(t("go"))+"</span>"}
 $("t-audit").setAttribute("aria-selected",TAB==="audit");$("t-drafts").setAttribute("aria-selected",TAB==="drafts");
 $("t-audit").tabIndex=TAB==="audit"?0:-1;$("t-drafts").tabIndex=TAB==="drafts"?0:-1;
 $("p-audit").hidden=TAB!=="audit";$("p-drafts").hidden=TAB!=="drafts";
 $("prov").textContent=t("provenance")+": "+M.pipeline+" · outputs sha256:"+M.run_sha256.slice(0,16)+"… · items sha256:"+M.items_sha256.slice(0,16)+"…"+(AU?" · audit "+AU.meta.file+(AU.meta.results?" + "+AU.meta.results:"")+(AU.meta.more?" + "+AU.meta.more:""):"")+(M.rev?" · rev "+M.rev:"");
 if(TAB==="audit"){chromeAudit();return}
 var fz=(M.pipeline.match(/freeze sha256:([0-9a-f]+)/)||[])[1]||"";
 kv("kv-l",[[t("guards"),(M.stack==="g3"?"guards3 (frozen)":"guards v2 (frozen)")+(fz?" · freeze "+fz.slice(0,12):"")],
  [t("items"),String(D.counts.items)],[t("changes"),String(D.counts.changes)]]);
 var C=D.counts,r=[];
 if(A){r.push([t("ready"),A.unflagged+" · "+pct(A.ready_rate),"",t("codeOnly")]);r.push([t("flagged"),A.flagged+" · "+pct(A.flag_rate)]);
  var ex=A.exact;r.push([t("exact"),pct(ex.model)+" vs "+pct(ex.rules)+" ("+sgn(ex.delta)+" pts, 95% CI "+ex.ci95[0]+" to "+ex.ci95[1]+")"]);
  if(A.pass!=null)r.push([t("rule"),A.pass?"PASS":"FAIL",A.pass?"pass":"fail"])}
 else{r.push([t("ready"),String(C.ready),"",t("codeOnly")]);r.push([t("flagged"),String(C.flagged)]);if(C.human)r.push([t("human"),String(C.human)]);
  if(C.exact!=null)r.push([t("exact").split(" vs")[0],String(C.exact)])}
 if(C.flagged)r.push([t("triSplit"),fmt(t("triSplitV"),{c:C.lvl_check,f:C.lvl_fine})]);
 if(C.flagged)r.push([t("triage"),triTxt(C.to_check,C.probably_fine)]);
 if(C.divergent)r.push([t("divergent"),String(C.divergent)]);
 kv("kv-r",r);
 seg("f-status",t("status"),[["open",t("open")],["ready",t("ready")],["check",t("fCheck")],["fine",t("fFine")],["flagged",t("flagged")],["divergent",t("divF")],["decided",t("decidedF")],["all",t("all")]],F.status,function(v){F.status=v;renderReg()});
 seg("f-lang",t("language"),[["all","FR+IT"],["fr","FR"],["it","IT"]],F.lang,function(v){F.lang=v;if(v!=="all")focusL=v;famBar();renderReg();renderCase()});
 var fs=$("f-fam");fs.innerHTML="";fs.appendChild(new Option(t("allFam")+" ("+D.families.length+")",""));
 D.families.forEach(function(f){var o=new Option(f[2]+" · "+f[1],f[0]);o.title=t("family")+" "+f[0];fs.appendChild(o)});fs.value=F.fam;$("f-q").placeholder=t("search");famBar();
 $("h-mark").textContent=t("mark");$("h-no").textContent=t("no");$("h-prod").textContent=t("product");$("h-chg").textContent=t("change");
 $("x-xlf").textContent=t("xlf");$("x-xlf12").textContent=t("xlf12");$("x-copy").textContent=t("copy");$("x-imp").textContent=t("imp");
 $("reg-key").innerHTML=keyHTML(t("keyReg"));$("legend").textContent=t("legend");
 $("legend2").textContent=t("triHead")+" "+["T1","T2","T3","T4","T5","T6","T7","T8"].map(function(r){return t("rd"+r)}).join(" · ");progress()}
function seg(id,label,opts,cur,fn){var s=$(id);s.innerHTML='<span class="k">'+esc(label)+"</span>";
 opts.forEach(function(o){var b=document.createElement("button");b.type="button";b.className="tb";b.textContent=o[1];b.setAttribute("aria-pressed",o[0]===cur);
  b.onclick=function(){s.querySelectorAll("button").forEach(function(x){x.setAttribute("aria-pressed",x===b)});fn(o[0])};s.appendChild(b)})}
function progress(){if(TAB==="audit"&&AU){var tm=AU.rows.filter(function(r){return r.kind==="terminology"}),fm=AU.rows.filter(function(r){return r.kind!=="terminology"});
  $("progress").innerHTML="<b>"+esc(fmt(t("progA"),{i:IS.filter(iDecided).length,n:IS.length,x:fm.filter(aDecided).length,a:fm.length,y:tm.filter(aDecided).length,t:tm.length}))+"</b>";return}
 var n=ITEMS.filter(function(it){return dec(it)}).length;$("progress").innerHTML="<b>"+n+"/"+ITEMS.length+"</b> "+esc(t("decided"))}
// ------------------------------------------------------------------ tabs
function setTab(tb){if(tb==="audit"&&!AU)tb="drafts";TAB=tb;chrome();
 if(TAB==="audit"){renderAudit();try{if(location.hash!=="#audit")history.replaceState(null,"","#audit")}catch(e){}}
 else{renderReg();if(sel){markSel(true);renderCase()}}}
$("t-audit").onclick=function(){setTab("audit")};$("t-drafts").onclick=function(){setTab("drafts")};
document.querySelector(".tabs").addEventListener("keydown",function(e){if(e.key==="ArrowRight"||e.key==="ArrowLeft"){e.preventDefault();setTab(TAB==="audit"?"drafts":"audit");$(TAB==="audit"?"t-audit":"t-drafts").focus()}});
// ------------------------------------------------------------------ register audit
// One table row per issue (audit_view.issues: findings naming the same difference on the same text), its findings
// listed below it. Decisions are stored per finding signature (SA[sig] = {right, actions[], note, at, by, date} + own:true
// when a finding is decided apart from its issue): a decision on the issue is written to every finding of the issue
// that is not decided separately, so it carries over to the next audit run finding by finding.
var AF={show:"all",lang:"all",kind:"all",since:""},EQOPEN=false,OPEN={},
 ACTS=["fix_de","fix_fr","fix_it","langsvc","decfile","pending","none","falsealarm"],LEGACY=["exofficio","holder","unclear"];
var IS=AU?AU.issues:[];
if(AU){IS.forEach(function(I){I.M=I.rows.map(function(i){return AU.rows[i]});I.M.forEach(function(r){r.I=I})})}
function aActs(d){return d?(d.actions||(d.action?[ACTMAP[d.action]||d.action]:[])):[]}
function aHas(d){return !!(d&&(d.right||aActs(d).length||d.note))}
function aDecided(r){var d=SA[r.sig];return !!(d&&(d.right||aActs(d).length))}
function iDec(I){for(var i=0;i<I.M.length;i++){var d=SA[I.M[i].sig];if(d&&!d.own)return d}return null}
function iDecided(I){return I.M.every(aDecided)}
function iOwn(I){return I.M.filter(function(r){var d=SA[r.sig];return d&&d.own}).length}
function clone(d){var o={};Object.keys(d||{}).forEach(function(k){o[k]=Array.isArray(d[k])?d[k].slice():d[k]});return o}
// decisions from earlier page versions: one action -> a list; a finding decided on its own (before issues existed) is
// marked as decided separately unless every finding of its issue carries the same decision
function aMigrate(){if(!AU)return;var ch=false;
 Object.keys(SA).forEach(function(k){var d=SA[k];if(d&&d.action&&!d.actions){d.actions=[ACTMAP[d.action]||d.action];delete d.action;ch=true}});
 IS.forEach(function(I){var ds=I.M.map(function(r){return SA[r.sig]}),legacy=ds.filter(function(d){return d&&d.own==null&&d.via==null});if(!legacy.length)return;
  var sig=function(d){return d?JSON.stringify([d.right||"",aActs(d).slice().sort(),d.note||""]):"-"},same=ds.every(function(d){return d&&sig(d)===sig(ds[0])});
  legacy.forEach(function(d){if(same)d.via=1;else d.own=true});ch=true});
 if(ch)saveA()}
aMigrate();
function aMark(I){return ((I.known?'<span class="mk"><span class="lt s">K</span></span>':"")+(iDecided(I)?'<span class="mk"><span class="lt">D</span></span>':"")||'<span class="mk o">·</span>')+
 '<span class="iid">'+esc(I.iid)+'</span><span class="fids">'+esc(I.fids.join(" "))+"</span>"}
function aStatus(d){if(!d||!d.at)return t("openSt");var day=ddate(d.at.slice(0,10).replace(/-/g,""));
 var s=d.by?fmt(t("decOn"),{d:day,n:d.by}):fmt(t("decOnAnon"),{d:day});
 if(d.date&&AU&&d.date!==AU.meta.date)s+=" "+fmt(t("earlier"),{s:ddate(d.date)});return s}
function dating(x){if(!x)return "";if(x.earliest&&x.n===x.m)return fmt(t("dA"),{n:x.n,d:ddate(x.first)});
 if(x.prev&&x.n===x.m)return fmt(t("dB"),{p:ddate(x.prev),d:ddate(x.first),n:x.n});return fmt(t("dC"),{d:ddate(x.first),n:x.n,m:x.m==null?"?":x.m})}
function chromeAudit(){var m=AU.meta,nf=AU.rows.length;
 var bk=m.by_kind?Object.keys(m.by_kind).filter(function(k){return k!=="terminology"}).map(function(k){return m.by_kind[k]+" "+(t("kinds")[k]||k)}).join(", "):"";
 kv("kv-l",[[t("aSnap"),ddate(m.date)],[t("aChecked"),m.n_limitations!=null?grp(m.n_limitations):"—"],
  [t("aFindings"),fmt(t("aFindingsV"),{a:m.main,b:bk,t:m.term,n:IS.length}).replace(" ()","")]]);
 var r=[[t("aKnown"),(m.known_found!=null?m.known_found:m.known_ids.length)+" / "+(m.known_of!=null?m.known_of:m.known_ids.length),"big"]];
 if(m.main_real!=null&&m.term_real!=null)r.push([t("aConf"),fmt(t("aConfV"),{r:m.main_real,a:m.main,k:m.main_real-(m.main_new_real||0),x:m.main_new_real||0,tr:m.term_real,t:m.term})]);
 kv("kv-r",r);$("aud-key").innerHTML=keyHTML(t("keyAud"));
 $("a-lead").textContent=fmt(t("aLead"),{d:ddate(m.date),a:m.main,t:m.term,n:IS.length});
 seg("a-show",t("aShow"),[["known",t("aKnownF")+" ("+IS.filter(function(I){return I.known}).length+")"],["all",fmt(t("aAllN"),{n:IS.length})],["open",t("aOpenF")],["decided",t("aDecF")]],AF.show,function(v){AF.show=v;renderAudit()});
 seg("a-lang",t("language"),[["all","DE+FR+IT"],["de","DE"],["fr","FR"],["it","IT"]],AF.lang,function(v){AF.lang=v;renderAudit()});
 var ks=[["all",t("all")]];["number","unit","language","editorial","terminology"].forEach(function(k){var n=IS.filter(function(I){return I.kinds.indexOf(k)>=0}).length;if(n)ks.push([k,t("kinds")[k]+" ("+n+")"])});
 IS.forEach(function(I){I.kinds.forEach(function(k){if(!ks.some(function(x){return x[0]===k}))ks.push([k,k])})});
 seg("a-kind",t("aKindF"),ks,AF.kind,function(v){AF.kind=v;renderAudit()});
 // "new since": the snapshots the audit dates against (summary.snapshots_dated), each with the issues first seen after it
 var sn=(m.snapshots||[]).slice(0,-1),ss=$("a-since");
 if(sn.length&&IS.some(function(I){return I.dating})){var o='<label class="k" for="a-since-s">'+esc(t("newSince"))+'</label><select id="a-since-s"><option value="">'+esc(t("newAny"))+"</option>";
  sn.forEach(function(d){var n=IS.filter(function(I){return newAfter(I,d)}).length;o+='<option value="'+d+'"'+(AF.since===d?" selected":"")+">"+esc(ddate(d))+" ("+n+")</option>"});
  ss.innerHTML=o+"</select>";ss.hidden=false;$("a-since-s").onchange=function(){AF.since=this.value;renderAudit()}}else ss.hidden=true;
 $("l-rev").textContent=t("rev");$("rev").placeholder=t("revPh");$("rev").value=P.reviewer||"";
 $("ah-no").textContent=t("ahNo");$("ah-lim").textContent=t("aLim");$("ah-kind").textContent=t("aKind")+" · "+t("aOdd");$("ah-right").textContent=t("aRight");$("ah-act").textContent=t("aAction");
 $("a-csv-i").textContent=t("csvIss");$("a-csv").textContent=t("aCsv");$("a-imp").textContent=t("imp");
 $("legend").textContent=fmt(t("aLegend"),{g:t("grouping")});$("legend2").textContent="";progress()}
$("rev").addEventListener("input",function(){P.reviewer=this.value;lsSet("gleichlaut:prefs",P)});
function newAfter(I,d){return I.M.some(function(r){return r.dating&&r.dating.first>d})}
function aOk(I){if(AF.lang!=="all"&&I.langs.indexOf(AF.lang)<0)return false;if(AF.kind!=="all"&&I.kinds.indexOf(AF.kind)<0)return false;
 if(AF.since&&!newAfter(I,AF.since))return false;
 switch(AF.show){case "known":return I.known;case "open":return !iDecided(I);case "decided":return iDecided(I);default:return true}}
function segHTML(s){return s.map(function(x){return x[1]===2?'<span class="v2'+(x[0].length>16?" w":"")+'">'+esc(x[0])+"</span>":x[1]===1?'<span class="v1">'+esc(x[0])+"</span>":esc(x[0])}).join("")}
function snipHTML(r,L){var s=r.snip[L];if(!s||!s.length)return '<span class="na">'+esc(r.lang===L||L==="de"?t("aNoSnip"):"—")+"</span>";
 return '<div class="snip'+(r.src[L]==="snapshot"?" src-s":"")+'" lang="'+L+'"'+(r.src[L]==="snapshot"?' title="'+esc(t("aSnapSrc"))+'"':"")+">"+segHTML(s)+"</div>"}
function termHTML(r){var m=r.term;if(!m)return "";var h="";
 if(m.old||m["new"])h+='<span class="term" lang="'+esc(r.lang||"")+'">'+esc(t("termOld"))+" <s>"+esc(m.old||"?")+"</s> · "+esc(t("termNew"))+" <u>"+esc(m["new"]||"?")+"</u></span>";
 if(m.where&&m.where.length)h+='<span class="sub2" title="'+esc(m.where.join("; "))+'">'+esc(fmt(t("termWhere"),{x:m.where.slice(0,2).join("; ")+(m.where.length>2?" +"+(m.where.length-2):"")}))+"</span>";
 return h}
function uniqP(xs){var o=[];xs.forEach(function(x){if(x&&o.indexOf(x)<0)o.push(x)});return o}
// the decision controls, for an issue (scope "i") or one finding decided separately (scope "m")
function ctlRight(d){return '<select data-a="right" aria-label="'+esc(t("aRight"))+'">'+[["",""],["DE","DE"],["FR","FR"],["IT","IT"],["unclear",t("rUnclear")]].map(function(o){
  return '<option value="'+o[0]+'"'+(d.right===o[0]?" selected":"")+">"+esc(o[1]||"—")+"</option>"}).join("")+"</select>"}
function ctlActs(d){var A=aActs(d),acts=t("acts"),ck=function(v,lab,row){return '<label class="ck'+(row?" row":"")+'"><input type="checkbox" data-a="act" value="'+v+'"'+(A.indexOf(v)>=0?" checked":"")+"> "+esc(lab)+"</label>"};
 var h='<div class="acts" role="group" aria-label="'+esc(t("aAction"))+'"><span class="fixl">'+esc(acts.fix)+':</span><span class="fixg">'+ck("fix_de","DE")+ck("fix_fr","FR")+ck("fix_it","IT")+"</span>";
 ["langsvc","decfile","pending","none","falsealarm"].forEach(function(v){h+=ck(v,acts[v],1)});
 A.forEach(function(v){if(ACTS.indexOf(v)<0)h+=ck(v,acts[v]||v,1)});            // an action of an earlier page version stays visible
 return h+"</div>"}
function ctlNote(d){return '<textarea data-a="note" aria-label="'+esc(t("aNote"))+'" placeholder="'+esc(t("aNote"))+'">'+esc(d.note||"")+"</textarea>"}
function iStatus(I){var d=iDec(I),o=iOwn(I),s=aStatus(d);if(I.M.length>1)s+=" · "+fmt(t("appliesAll"),{n:I.M.length-o});if(o)s+=" · "+fmt(t("someOwn"),{n:o});return s}
function ftHTML(I){var h="";
 I.lims.forEach(function(lim){var T=AU.texts[lim],r=I.M.filter(function(x){return x.lim===lim})[0];
  if(I.lims.length>1)h+='<p class="ftl"><b>'+esc(r.product||lim)+"</b> "+esc(lim)+"</p>";
  if(!T){h+='<p class="na">'+esc(t("ftNone"))+"</p>";return}
  h+='<div class="ftg">'+["de","fr","it"].map(function(L){var odd=I.odd===L;return '<div class="ftc'+(odd?" odd":"")+'"><span class="lt">'+L.toUpperCase()+"</span>"+(odd?' <span class="oddl">'+esc(t("oddLbl"))+"</span>":"")+
   '<div class="snip ftx" lang="'+L+'">'+(T[L]?segHTML(T[L]):"—")+"</div></div>"}).join("")+"</div>"});
 return h}
function memHTML(I){return '<table class="mem"><tbody>'+I.M.map(function(r){var d=SA[r.sig],own=!!(d&&d.own);
  return '<tr data-sig="'+esc(r.sig)+'"><td class="mf">'+esc(r.no||"")+"</td><td><b>"+esc(r.product||r.lim)+"</b> "+'<span class="code">'+esc(r.lim)+"</span>"+
   '<span class="sub2">'+esc((t("kinds")[r.kind]||r.kind)+" · "+(r.lang||"").toUpperCase())+(r.dating?" · "+esc(dating(r.dating)):"")+"</span></td>"+
   '<td class="mc">'+(own?ctlRight(d)+ctlActs(d)+ctlNote(d)+'<div class="stt">'+esc(t("memOwn")+" · "+aStatus(d))+'</div><button type="button" class="tb" data-join="1">'+esc(t("memJoin"))+"</button>"
    :'<span class="stt">'+esc(t("memFollow"))+'</span> <button type="button" class="tb" data-split="1">'+esc(t("memSplit"))+"</button>")+"</td></tr>"}).join("")+"</tbody></table>"}
function aRow(I){var r=I.M[0],d=iDec(I)||{},cell=function(L){var odd=I.odd===L;return '<td data-l="'+L.toUpperCase()+(odd?" · "+esc(t("oddLbl")):"")+'"'+(odd?' class="odd"':"")+">"+(odd?'<span class="oddl">'+esc(t("oddLbl"))+"</span>":"")+snipHTML(r,L)+"</td>"};
 var odd=I.odd==="unclear"?t("aUnclear"):String(I.odd||"—").toUpperCase(),n=I.M.length,sub=[];
 I.M.forEach(function(x){
  if(x.found)sub.push(fmt(t("aFoundL"),{F:t("lname")[x.found]||x.found}));
  if(x.fix)sub.push(fmt(t("aFix"),{a:x.fix[0],b:x.fix[1]}));
  if(x.eq!=null)sub.push(t("eqWhy")+": "+(x.eq||"—"));
  if(x.expl&&x.expl.length)sub.push(fmt(t("aExpl"),{x:x.expl.join(", ")}))});
 var codes=I.lims.length>3?I.lims.slice(0,3).join(" · ")+" +"+(I.lims.length-3):I.lims.join(" · ");
 var h='<tr data-iss="'+esc(I.key)+'" class="cnt iss'+(I.eq?' eq':"")+'"><td data-l="'+esc(t("ahNo"))+'">'+aMark(I)+"</td>"+
  '<td class="lim" data-l="'+esc(t("aLim"))+'"><b>'+esc(uniqP(I.products).join(", ")||I.lims[0])+'</b><span class="code" title="'+esc(I.lims.join("\n"))+'">'+esc(codes)+"</span>"+
   (I.dating?'<span class="sub2 dt">'+esc(dating(I.dating))+"</span>":"")+"</td>"+
  '<td class="kd" data-l="'+esc(t("aKind"))+'">'+esc(I.kinds.map(function(k){return t("kinds")[k]||k}).join(" + "))+" · "+esc(I.langs.map(function(L){return L.toUpperCase()}).join(" "))+
   '<span class="oddl">'+esc(t("aOdd"))+": "+esc(odd)+"</span>"+uniqP(sub).map(function(s){return '<span class="sub2">'+esc(s)+"</span>"}).join("")+termHTML(r)+"</td>"+
  cell("de")+cell("fr")+cell("it");
 h+='<td data-l="'+esc(t("aRight"))+'">'+ctlRight(d)+"</td>";
 h+='<td data-l="'+esc(t("aAction"))+'">'+ctlActs(d)+(r.sug?'<div class="sug">'+esc(t("aSug"))+": "+esc(t("acts")[r.sug]||r.sug)+"</div>":"")+ctlNote(d)+
  '<div class="stt">'+esc(iStatus(I))+"</div></td></tr>";
 h+='<tr class="det" data-det="'+esc(I.key)+'"><td colspan="8"><details class="ft" data-k="ft"'+(OPEN["ft"+I.key]?" open":"")+"><summary>"+esc(t("ft"))+(I.lims.length>1?" · "+esc(fmt(t("ftN"),{n:I.lims.length})):"")+"</summary>"+
  (OPEN["ft"+I.key]?ftHTML(I):"")+"</details>"+
  (n>1?'<details class="mm" data-k="mm"'+(OPEN["mm"+I.key]?" open":"")+"><summary>"+esc(fmt(t("mem"),{n:n}))+" · "+esc(I.fids.join(", "))+"</summary>"+memHTML(I)+"</details>":"")+"</td></tr>";
 return h}
function renderAudit(){if(!AU){$("p-audit").innerHTML='<p class="empty">'+esc(t("aNoFile"))+"</p>";return}
 var tb=document.querySelector("#aud tbody"),Is=IS.filter(aOk),kn=Is.filter(function(I){return I.known}),
  ot=Is.filter(function(I){return !I.known&&!I.eq&&!I.term}),tm=Is.filter(function(I){return !I.known&&!I.eq&&I.term}),eq=Is.filter(function(I){return !I.known&&I.eq}),h="",m=AU.meta;
 var nf=function(L){return L.reduce(function(s,I){return s+I.M.length},0)};
 if(kn.length)h+='<tr class="grp"><td colspan="8"><span class="lt s">K</span> '+esc(fmt(t("aKnownHead"),{k:m.known_found!=null?m.known_found:m.known_ids.length,n:m.known_of!=null?m.known_of:m.known_ids.length}))+"</td></tr>"+kn.map(aRow).join("");
 if(ot.length)h+='<tr class="grp"><td colspan="8">'+esc(t("aOtherHead"))+"</td></tr>"+ot.map(aRow).join("");
 if(tm.length)h+='<tr class="grp"><td colspan="8">'+esc(fmt(t("aTermHead"),{n:tm.length,m:nf(tm)}))+"</td></tr>"+tm.map(aRow).join("");
 if(eq.length)h+='<tr class="eqh"><td colspan="8"><button type="button" id="eq-tg" aria-expanded="'+EQOPEN+'"><span class="mk">['+(EQOPEN?"−":"+")+"]</span>"+esc(fmt(t("eqHead"),{n:eq.length}))+" · "+esc(EQOPEN?t("eqHide"):t("eqShow"))+"</button></td></tr>"+(EQOPEN?eq.map(aRow).join(""):"");
 tb.innerHTML=h||'<tr><td colspan="8" class="empty">'+esc(t("aNone"))+"</td></tr>";
 var tg=$("eq-tg");if(tg)tg.onclick=function(){EQOPEN=!EQOPEN;renderAudit();var b=$("eq-tg");if(b)b.focus()};
 $("a-shown").textContent=fmt(t("aShownI"),{n:Is.length,m:nf(Is)});progress()}
function issueOf(el){var tr=el.closest("tr[data-iss],tr[data-det]");if(!tr)return null;var k=tr.dataset.iss||tr.dataset.det;return IS.filter(function(I){return I.key===k})[0]||null}
function rowOf(sig){return AU.rows.filter(function(x){return x.sig===sig})[0]}
function stamp(d){d.at=new Date().toISOString();d.by=who();d.date=AU.meta.date;return d}
function upd(d,f){if(f.dataset.a==="act"){var A=aActs(d).filter(function(v){return v!==f.value});if(f.checked)A.push(f.value);d.actions=A;delete d.action}else d[f.dataset.a]=f.value;return d}
function aSet(f){var I=issueOf(f);if(!I)return;var mt=f.closest(".mem tr[data-sig]");
 if(mt){var sg=mt.dataset.sig,d=upd(clone(SA[sg]),f);d.own=true;delete d.via;SA[sg]=stamp(d);saveA();var st=mt.querySelector(".stt");if(st)st.textContent=t("memOwn")+" · "+aStatus(SA[sg])}
 else{var base=upd(clone(iDec(I)),f);delete base.own;base.via=1;var keep=aHas(base);if(keep)stamp(base);
  I.M.forEach(function(r){var d=SA[r.sig];if(d&&d.own)return;if(keep)SA[r.sig]=clone(base);else delete SA[r.sig]});saveA();
  var tr=document.querySelector('#aud tr[data-iss="'+I.key+'"]');if(tr)tr.querySelector("td:last-child .stt").textContent=iStatus(I)}
 var tr2=document.querySelector('#aud tr[data-iss="'+I.key+'"]');if(tr2)tr2.cells[0].innerHTML=aMark(I);progress()}
function aRerow(I){var tr=document.querySelector('#aud tr[data-iss="'+I.key+'"]');if(!tr)return;var det=tr.nextElementSibling,tmp=document.createElement("tbody");
 tmp.innerHTML=aRow(I);var a=tmp.children[0],b=tmp.children[1];tr.replaceWith(a);if(det&&det.dataset.det===I.key)det.replaceWith(b)}
(function(){var tb=document.querySelector("#aud tbody");
 tb.addEventListener("change",function(e){var f=e.target.closest("[data-a]");if(f)aSet(f)});
 tb.addEventListener("input",function(e){var f=e.target.closest("textarea[data-a]");if(f)aSet(f)});
 tb.addEventListener("click",function(e){var b=e.target.closest("button[data-split],button[data-join]");if(!b)return;var I=issueOf(b),sg=b.closest("tr[data-sig]").dataset.sig;
  if(b.dataset.split){var d=clone(SA[sg]||iDec(I));d.own=true;delete d.via;if(!aHas(d))d.at=null;SA[sg]=d}
  else{var base=iDec(I);if(base)SA[sg]=clone(base);else delete SA[sg]}
  saveA();OPEN["mm"+I.key]=true;aRerow(I);progress()});
 // the full texts are put in when their block is opened (toggle does not bubble: listen in the capture phase)
 tb.addEventListener("toggle",function(e){var dt=e.target;if(!dt.matches||!dt.matches("details[data-k]"))return;var I=issueOf(dt);if(!I)return;
  OPEN[dt.dataset.k+I.key]=dt.open;if(dt.dataset.k==="ft"&&dt.open&&!dt.querySelector(".ftg,.na"))dt.insertAdjacentHTML("beforeend",ftHTML(I))},true)})();
function iRow(I){var d=iDec(I)||{},acts=TX[UL].acts,A=aActs(d);
 var what=I.what.map(function(w){var L=(w[1]||"").toUpperCase();
  if(w[0]==="number")return "DE "+w[2]+" / "+L+" "+w[3];
  if(w[0]==="language")return L+": "+fmt(t("aFoundL"),{F:t("lname")[w[2]]||w[2]});
  if(w[0]==="terminology")return L+": «"+w[2]+"» → «"+w[3]+"»";
  return L+": "+w[2]+(w[3]?" → "+w[3]:"")}).join("; ");
 var actL=A.map(function(v){return /^fix_/.test(v)?acts.fix+": "+v.slice(4).toUpperCase():acts[v]||v}).join("; ");
 var own=I.M.filter(function(r){var x=SA[r.sig];return x&&x.own}).map(function(r){var x=SA[r.sig];
  return r.no+" ("+[x.right,aActs(x).map(function(v){return /^fix_/.test(v)?acts.fix+": "+v.slice(4).toUpperCase():acts[v]||v}).join(", "),x.note].filter(Boolean).join(" · ")+")"}).join("; ");
 return [I.iid,I.fids.join(" "),uniqP(I.products).join(", "),I.lims.join(" "),I.langs.map(function(L){return L.toUpperCase()}).join(" "),
  I.kinds.map(function(k){return t("kinds")[k]||k}).join(" + "),what,I.dating?dating(I.dating):"",I.known?t("yes"):t("no2"),
  d.right==="unclear"?t("rUnclear"):(d.right||""),actL,d.note||"",d.at?d.at.slice(0,10):"",d.by||"",ddate(d.date||AU.meta.date),own]}
// the issues with their decisions, one line each, for filing (GEVER): in the interface language, ';'-separated with a BOM so
// that Excel (de-CH) opens it in columns
function auditCsv(){var lines=[t("csvHead")].concat(IS.map(iRow));
 return "﻿"+lines.map(function(l){return l.map(csvCellS).join(";")}).join("\r\n")+"\r\n"}
function csvCellS(s){s=String(s==null?"":s);return /[";\n\r]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s}
function auditExport(){if(!AU)return {};var o={};AU.rows.forEach(function(r){var d=SA[r.sig];if(d)o[r.sig]={limitation:r.lim,product:r.product,lang:r.lang,kind:r.kind,odd_one_out:r.odd,known:r.known,
 issue:r.I?r.I.iid:"",issue_key:r.I?r.I.key:"",decided_separately:!!d.own,right:d.right||"",actions:aActs(d),note:d.note||"",at:d.at,by:d.by||"",audit_date:d.date||AU.meta.date}});return o}
function auditIssues(){return IS.map(function(I){var d=iDec(I)||{};return {issue:I.iid,key:I.key,findings:I.M.map(function(r){return r.sig}),fids:I.fids,limitations:I.lims,
 right:d.right||"",actions:aActs(d),note:d.note||"",decided:iDecided(I)}})}
function csvCell(s){s=String(s==null?"":s);return /[",\n;]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s}
function snipText(r,L){return (r.snip[L]||[]).map(function(x){return x[0]}).join("")}
$("a-csv-i").onclick=function(){download("gleichlaut-audit-"+AU.meta.date+"-issues.csv",auditCsv(),"text/csv");$("a-msg").textContent=t("dl")+": CSV"};
$("a-csv").onclick=function(){var head=["rank","issue","limitation","product","kind","lang","odd_one_out","known","probably_equivalent","de","fr","it","right","actions","note","decided_at","decided_by","decided_in_audit","decided_separately"],acts=TX.en.acts;
 var lines=[head.join(",")].concat(AU.rows.map(function(r){var d=SA[r.sig]||{};return [r.rank,r.I?r.I.iid:"",r.lim,r.product,r.kind,r.lang,r.odd,r.known?"yes":"no",r.eq!=null?(r.eq||"yes"):"",snipText(r,"de"),snipText(r,"fr"),snipText(r,"it"),d.right||"",
  aActs(d).map(function(v){return /^fix_/.test(v)?"correct "+v.slice(4).toUpperCase():acts[v]||v}).join("; "),d.note||"",d.at||"",d.by||"",d.date||"",d.own?"yes":""].map(csvCell).join(",")}));
 download("gleichlaut-audit-"+AU.meta.date+"-findings.csv","﻿"+lines.join("\r\n")+"\r\n","text/csv");$("a-msg").textContent=t("dl")+": CSV"};

// ------------------------------------------------------------------ register (drafts)
var F={status:"open",lang:"all",fam:"",q:""},sel=null,focusL="fr",VIS=[];
function langs(g){return ["fr","it"].filter(function(L){return g.items[L]&&(F.lang==="all"||F.lang===L)})}
function okItem(it){var d=dec(it);switch(F.status){case "open":return !d;case "ready":return it.status==="ready";case "flagged":return it.status==="flagged";case "check":return it.lvl==="check";case "fine":return it.lvl==="fine";
 case "divergent":return oldIssue(it);case "decided":return !!d;default:return true}}
function renderReg(){var tb=document.querySelector("#reg tbody"),h="";VIS=[];
 G.forEach(function(g){var Ls=langs(g);if(!Ls.length)return;if(F.fam&&g.family!==F.fam)return;
  if(F.q&&(g.product+" "+g.code+" "+g.pair+" "+g.no).toLowerCase().indexOf(F.q)<0)return;
  if(!Ls.some(function(L){return okItem(g.items[L])}))return;VIS.push(g);
  var mk=(F.lang==="all"?["fr","it"]:[F.lang]).map(function(L){return mark(g.items[L])[0]}).join("");
  h+='<tr class="cnt" data-pair="'+esc(g.pair)+'" aria-selected="'+(sel===g)+'"><td>'+mk+'</td><td>'+g.no+'</td><td class="prd" title="'+esc(g.product+" · "+g.code)+'">'+esc(g.product)+'<span class="pc">'+esc(g.code)+"</span>"+
   '</td><td class="chg" title="'+esc(g.sum)+'">'+esc(g.sum)+"</td></tr>"});
 tb.innerHTML=h||'<tr><td colspan="4" class="empty">'+esc(t("none"))+"</td></tr>";
 $("shown").textContent=VIS.length+" "+t("shown");
 if(VIS.indexOf(sel)<0){sel=VIS[0]||null;if(sel)markSel();renderCase()}}
function markSel(scroll){document.querySelectorAll("#reg tbody tr").forEach(function(r){var on=sel&&r.dataset.pair===sel.pair;r.setAttribute("aria-selected",on);
 if(on&&scroll){var w=$("reg-wrap"),top=r.offsetTop-w.offsetTop,hh=28;if(top-hh<w.scrollTop)w.scrollTop=top-hh;else if(top+r.offsetHeight>w.scrollTop+w.clientHeight)w.scrollTop=top+r.offsetHeight-w.clientHeight}})}
document.querySelector("#reg tbody").addEventListener("click",function(e){var r=e.target.closest("tr[data-pair]");if(!r)return;
 sel=G.filter(function(g){return g.pair===r.dataset.pair})[0];markSel();renderCase();if(window.innerWidth<=900)$("case").scrollIntoView()});
$("f-fam").onchange=function(){F.fam=this.value;famAsk=false;famMsg="";famBar();renderReg()};
// family bulk action: accept every open ready draft of the selected edit family, after an in-page confirmation
var famAsk=false,famMsg="",FAMN={};G.forEach(function(g){FAMN[g.family]=(FAMN[g.family]||0)+1});
function famSize(f){return FAMN[f]||0}
function famTargets(){if(!F.fam)return [];return ITEMS.filter(function(it){return it.g.family===F.fam&&it.status==="ready"&&!dec(it)&&S.edits[it.key]==null&&!oldIssue(it)&&(F.lang==="all"||it.lang===F.lang)})}
function famBar(){var b=$("fam-bulk");if(!F.fam){b.hidden=true;b.innerHTML="";famAsk=false;famMsg="";return}b.hidden=false;var T=famTargets(),h="";
 if(famAsk&&T.length){var fr=T.filter(function(it){return it.lang==="fr"}).length;
  h='<span class="q" role="alert">'+esc(fmt(t("famAsk"),{n:T.length,fr:fr,it:T.length-fr,f:FAML[F.fam]||F.fam}))+'</span><button class="box primary" type="button" id="fam-yes">'+esc(t("famYes"))+'</button><button class="box" type="button" id="fam-no">'+esc(t("famNo"))+"</button>"}
 else h='<button class="box" type="button" id="fam-go"'+(T.length?"":" disabled")+">"+esc(fmt(t("famAll"),{n:T.length}))+"</button>";
 if(famMsg)h+='<span class="msg" aria-live="polite">'+esc(famMsg)+"</span>";else if(!T.length)h+='<span class="msg">'+esc(t("famNone"))+"</span>";
 b.innerHTML=h;var go=$("fam-go"),y=$("fam-yes"),n=$("fam-no");
 if(go)go.onclick=function(){famAsk=true;famMsg="";famBar();var yy=$("fam-yes");if(yy)yy.focus()};
 if(n)n.onclick=function(){famAsk=false;famBar();var g2=$("fam-go");if(g2)g2.focus()};
 if(y)y.onclick=function(){var at=new Date().toISOString(),T2=famTargets();
  T2.forEach(function(it){S.dec[it.key]={decision:"accept",lang:it.lang,status:it.status,edited:false,text:it.draft,reason:"",note:"",bulk:"family "+F.fam,at:at,by:who()}});
  save();famAsk=false;famMsg=fmt(t("famDone"),{n:T2.length});famBar();renderReg();if(sel)renderCase();progress()}}
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
function stLabel(it){return it.status==="ready"?(oldIssue(it)?t("readyAttn"):t("lready")):it.status==="flagged"?(it.lvl==="fine"?t("lfine"):t("lcheck")):t("lhuman")}
function stRed(it){return (it.status==="flagged"&&it.lvl!=="fine")||oldIssue(it)}
function langMsg(it,o){var a=t("adj")[it.lang]||LN(it.lang),f=t("lname")[o.f]||o.f;return fmt(t("oldLang"),{A:a,F:f})}
function notice(it){var p=[],lang=false;
 (it.old||[]).forEach(function(o){if(o.k==="language"){lang=true;var um=o.f?langMsg(it,o):o.t;p.push('<p><span class="mk">≠</span>'+esc(um)+"</p>"+(o.f&&o.t!==um?'<p lang="'+it.lang+'">'+esc(o.t)+"</p>":""))}});
 if(it.banner&&!(lang&&(it.old||[]).every(function(o){return o.k==="language"})))p.push("<p>"+(lang?"":"<span class=\"mk\">≠</span>")+esc(it.banner)+"</p>");
 if(it.corr)p.push("<p>"+(p.length?"":"<span class=\"mk\">≠</span>")+esc(it.corr)+"</p>");
 return p.length?'<div class="notice'+(lang?" lang":"")+'" role="note"><p class="xl">'+esc(t("expl")+" ("+it.lang.toUpperCase()+")")+"</p>"+p.join("")+"</div>":""}
function curText(it){var e=S.edits[it.key];return e!=null?e:it.draft}
function caseHTML(g,live){var Ls=langs(g),one=Ls.length<2?" one":"",h="";
 var keys=["fr","it"].filter(function(L){return g.items[L]}).map(function(L){return g.items[L].key}).join(", ");
 h+="<h2>"+esc(g.product)+'</h2><p class="ref">'+esc(t("limitation"))+" "+esc(g.code)+" · SL "+esc(g.snap_old)+" → "+esc(g.snap_new)+" · "+esc(t("no"))+" "+g.no+"</p>"+
  '<p class="famline">'+esc(t("famOf"))+": "+esc(FAML[g.family]||g.family)+" · "+esc(fmt(t("famChanges"),{n:famSize(g.family)}))+
   (live&&F.fam!==g.family&&famSize(g.family)>1?' · <button class="tb" type="button" data-fam="'+esc(g.family)+'">'+esc(t("famFilter"))+"</button>":"")+"</p>"+
  '<details class="ids"><summary>'+esc(t("ids"))+"</summary> "+esc(t("family"))+" "+esc(g.family)+(FAML[g.family]?" ("+esc(FAML[g.family])+")":"")+" · "+esc(t("pair"))+" "+esc(g.pair)+" · "+esc(t("itemsL"))+" "+esc(keys)+"</details>";
 h+='<section class="sec"><div class="sl"><span class="no"><b>§</b>1</span><span class="t">'+esc(t("s1"))+"</span>"+(live?'<button class="tb sp" type="button" id="ctx">'+esc(ctxMode?t("ctxA"):t("ctxF"))+"</button>":"")+
  '</div><div class="txt de" lang="de">'+segs(g.de,live&&ctxMode,false)+"</div></section>";
 h+='<section class="sec"><div class="sl"><span class="no"><b>§</b>2</span><span class="t">'+esc(t("s2"))+'</span></div><div class="drafts'+one+'">';
 Ls.forEach(function(L){var it=g.items[L],ed=S.edits[it.key];
  h+='<div class="dr" data-lang="'+L+'"><div class="dl"><span class="ln" title="'+esc(it.key)+'"><span class="lt">'+L.toUpperCase()+"</span> "+esc(LN(L))+'</span>·<span class="st'+(stRed(it)?" r":"")+'">'+esc(stLabel(it))+"</span>"+
   (it.status==="flagged"?'<span class="tri">'+triHTML(it.tri[0],it.tri[1])+"</span>":"")+(it.rule_only?'<span class="key">rules</span>':"")+
   (it.status==="ready"?'<span class="cap">'+esc(t("codeOnly"))+"</span>":"")+"</div>"+notice(it);
  if(it.status==="human")h+='<p class="human">'+esc(it.reason&&!/rewritten|60/.test(it.reason)?t("humanShort"):t("humanTxt"))+(it.ratio!=null?" ("+it.ratio+"%)":"")+".</p>"+(it.reason?'<p class="ref">'+esc(it.reason)+"</p>":"")+"<p class=\"human\" style=\"color:var(--ink2)\">"+esc(t("humanPrev"))+"</p>";
  var body=ed!=null?esc(ed):segs(it.segs,false,live);
  h+='<div class="txt'+(live?" ed":"")+'" lang="'+L+'"'+(live?' contenteditable="true" spellcheck="true" role="textbox" aria-multiline="true" aria-label="'+esc(LN(L))+'" data-key="'+esc(it.key)+'"':"")+">"+body+"</div>";
  if(live)h+='<div class="edmeta" data-meta="'+esc(it.key)+'">'+edmeta(it.key)+"</div>";
  h+="</div>"});
 h+="</div>";
 if(live){var kn=t("keyNum");h+='<p class="key"><span><span class="n">8<sup>A</sup></span> '+esc(kn[0])+'</span><span><span class="n m">8</span> '+esc(kn[1])+
  '</span><span><ins>ab</ins> '+esc(kn[2])+'</span><span><del>ab</del> '+esc(kn[3])+"</span></p>"}
 h+="</section>";
 // §3: per draft, at most three reasons in plain wording in the reviewer's language (the same as the XLIFF notes), the
 // full checks ledger with its internal codes collapsed below
 h+='<section class="sec"><div class="sl"><span class="no"><b>§</b>3</span><span class="t">'+esc(t("s3"))+"</span></div>";
 Ls.forEach(function(L){var it=g.items[L],LL=L.toUpperCase();
  h+='<div class="why"><div class="dl"><span class="ln"><span class="lt">'+LL+"</span> "+esc(LN(L))+'</span>·<span class="xl">'+esc(t("expl")+" ("+LL+")")+"</span>"+
   (it.status==="flagged"?'<span class="tri">'+triHTML(it.tri[0],it.tri[1])+"</span>":"")+"</div>";
  if(!it.ledger.length){h+='<p class="ok">'+esc(t("noChecks"))+"</p></div>";return}
  var W=it.why||[[],0],sh=W[0];
  if(sh.length)h+='<ol class="reasons" lang="'+L+'">'+sh.map(function(x){return "<li"+(x[1]?' class="low"':"")+">"+esc(x[0])+"</li>"}).join("")+"</ol>";
  else h+='<p class="ok">'+esc(t("allPass"))+(it.status==="ready"?" "+esc(t("codeOnly")):"")+"</p>";
  if(W[1]>sh.length)h+='<p class="more">'+esc(fmt(t("moreN"),{n:W[1]-sh.length}))+"</p>";
  if(it.tb)h+='<p class="tb" lang="'+L+'">'+esc(it.tb)+"</p>";   // termbase advisory: its own low-priority line, not one of the three
  h+='<details class="chk"><summary>'+esc(fmt(t("chkDetail"),{n:it.ledger.length}))+'</summary><div class="tbl"><table class="ledger">';
  h+="<thead><tr><th>"+esc(t("check"))+" ("+LL+")</th><th>"+esc(t("result"))+"</th><th>"+esc(t("finding"))+" ("+LL+")</th></tr></thead><tbody>";
  it.ledger.forEach(function(r){var st=r[2],res=st==="pass"?t("pass"):st==="fail"?t("fail"):t("na"),cls=st==="fail"?"FAIL":st==="pass"?"":"na";
   if(st==="fail"&&r[3].length&&r[3].every(function(f){return f.r})){res="~ "+t("fail");cls="FAILf"}
   var fd=r[3].map(function(f){var p="<p>"+esc(f.t)+(f.c&&it.corr_note?'<span class="cn">[≠] '+esc(it.corr_note)+"</span>":"")+"</p>";
    return f.r?'<details class="pf" title="'+esc(t("rd"+f.r))+'"><summary>'+esc(t("pf"))+" · "+esc(t("r"+f.r))+"</summary>"+p+"</details>":p}).join("");
   if(!fd&&st!=="fail")fd='<span class="na">—</span>';
   if(r[4])fd+="<details><summary>"+esc(t("raw"))+" · "+esc(r[5])+"</summary><div>"+esc(r[4])+"</div></details>";
   h+='<tr><td class="chk" title="'+esc(r[5])+'">'+esc(r[1])+'</td><td class="res '+cls+'">'+esc(res)+'</td><td class="fd" lang="'+L+'">'+fd+"</td></tr>"});
  h+="</tbody></table></div></details></div>"});
 h+="</section>";
 if(live){h+='<section class="sec"><div class="sl"><span class="no"><b>§</b>4</span><span class="t">'+esc(t("s4"))+'</span></div><div class="decs'+one+'">';
  Ls.forEach(function(L){var it=g.items[L],d=dec(it)||{};
   h+='<div class="dec'+(L===focusL||Ls.length<2?" focus":"")+'" data-lang="'+L+'" data-key="'+esc(it.key)+'"><div class="dl"><span class="ln"><span class="lt">'+L.toUpperCase()+"</span> "+esc(LN(L))+'</span><span class="key">'+esc(stLabel(it))+'</span></div><div class="btns">'+
    [["accept","(1) "+t("accept")],["accept-edited","(2) "+t("acceptEd")],["send-back","(3) "+t("sendBack")]].map(function(b){
     return '<button class="box" type="button" data-d="'+b[0]+'" aria-pressed="'+(d.decision===b[0])+'">'+esc(b[1])+"</button>"}).join("")+"</div>"+
    "<label>"+esc(t("reason"))+'<select data-f="reason">'+t("reasons").map(function(r,i){var v=TX.en.reasons[i];return '<option value="'+esc(v)+'"'+(d.reason===v?" selected":"")+">"+esc(r||"—")+"</option>"}).join("")+"</select></label>"+
    "<label>"+esc(t("note"))+'<textarea data-f="note" lang="'+L+'">'+esc(d.note||"")+"</textarea></label>"+
    '<div class="stt">'+esc(d.decision?t("savedAt")+" · "+d.at.slice(0,16).replace("T"," "):t("openSt"))+"</div></div>"});
  h+='</div><div class="save"><button class="box primary" type="button" id="savenext">'+esc(t("saveNext"))+'</button><span class="hint">'+esc(t("keys"))+"</span></div></section>"}
 return h}
function edmeta(key){var it=byKey[key],e=S.edits[key]!=null;
 return (e?"<span>"+esc(t("edited"))+'</span><button class="tb" type="button" data-reset="'+esc(key)+'">'+esc(t("reset"))+"</button>":"<span>"+esc(t("editHint"))+"</span>")+
  ((it.status!=="human"||e)?'<button class="tb" type="button" data-copy="'+esc(key)+'">'+esc(t("copyTxt"))+'</button><span class="cpmsg" aria-live="polite"></span>':"")+
  (it.rt&&it.rt[0]!==it.draft&&S.edits[key]!==it.rt[0]?'<button class="tb" type="button" data-start="'+esc(key)+'" title="'+esc(fmt(t("startOldT"),{n:it.rt[1]}))+'">'+esc(t("startOld"))+"</button>":"")+
  (it.rt&&S.edits[key]===it.rt[0]?"<span>"+esc(fmt(t("startOldDone"),{n:it.rt[1]}))+"</span>":"")}
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
  var so=e.target.closest("[data-start]");if(so){var k0=so.dataset.start;S.edits[k0]=byKey[k0].rt[0];save();renderCase();
   var ed0=c.querySelector('.ed[data-key="'+k0+'"]');if(ed0)ed0.focus();return}
  var fl=e.target.closest("[data-fam]");if(fl){F.fam=fl.dataset.fam;$("f-fam").value=F.fam;famBar();renderReg();return}
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
  S.dec[k]={decision:v,lang:L,status:it.status,edited:S.edits[k]!=null,text:v==="accept-edited"?S.edits[k]:(it.status==="human"?null:it.draft),reason:reason,note:note,at:new Date().toISOString(),by:who()}}
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
 decisions:S.dec,edits:S.edits,audit_date:AU?AU.meta.date:null,audit:SA,audit_rows:auditExport(),audit_issues:AU?auditIssues():[]}}
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
  // the unit notes of emit/xliff.py (verdict, at most three plain reasons, change), the old texts, then the one low-priority checks note
  var prev=note("de-old","context:previous-source","source",5,fmt(X.prev_de,{t:g.deOld}).replace(" : ",colon))+
   note("tgt-old","context:previous-target","target",5,fmt(X.prev_tgt,{t:plain(it.segs,true)}).replace(" : ",colon)),notes="";
  it.xn.forEach(function(n){if(n[0]==="checks"||n[0]==="termbase"){notes+=prev;prev=""}notes+=note(n[0],n[1],n[2],n[3],n[4])});notes+=prev;
  if(d){var why=[d.reason,d.note].filter(Boolean).join("; ");notes+=note("review","gleichlaut:review","target",1,fmt(X.review,{d:X.dec[d.decision]||d.decision}).replace(" : ",colon)+" ("+d.at+")"+(why?colon+why:""))}
  var src=g.deNew,beads=text==null?it.bd.map(function(b){return [b[0],b[1],0,0]}):edited?[[0,src.length,0,text.length]]:it.bd,nums=edited?[]:it.nm,c=0,n=0,sx="";
  beads.forEach(function(b,k){sx+='<segment id="s'+(k+1)+'" state="'+st[0]+'" subState="'+st[1]+'"><source>'+inl(src,b[0],b[1],g.ch,function(){c++;return '<mrk id="c'+c+'" type="gleichlaut:changed">'})+"</source>"+
   (text!=null?"<target>"+inl(text,b[2],b[3],nums,function(sp){n++;var code=sp[2]!=="model";return '<mrk id="t'+n+'"'+(code?' translate="no"':"")+' type="gleichlaut:'+(code?"code":"model")+'-number"'+(sp[3]?' value="'+x(sp[3])+'"':"")+">"})+"</target>":"")+"</segment>"});
  u.push('<unit id="'+x(it.key)+'" name="'+x(it.cud)+'"><notes>'+notes+"</notes>"+sx+"</unit>")});
 return '<?xml version="1.0" encoding="UTF-8"?>\n<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" version="2.1" srcLang="de-CH" trgLang="'+trg+'"><file id="f1" original="gleichlaut:'+x(M.run)+'">'+
  "<notes>"+note("about","gleichlaut:about",null,1,X.about).replace(' priority="1"',"")+note("states","gleichlaut:states",null,1,X.states).replace(' priority="1"',"")+
  note("provenance","gleichlaut:provenance",null,1,X.prov).replace(' priority="1"',"")+note("review","gleichlaut:review",null,1,fmt(X.reviewed,{n:nd})+" · "+new Date().toISOString()).replace(' priority="1"',"")+
  "</notes>"+u.join("")+"</file></xliff>\n"}
function note12(ap,pr,text,frm){return '<note from="'+(frm||"gleichlaut")+'" annotates="'+(ap||"general")+'" priority="'+pr+'">'+x(text)+"</note>"}
// XLIFF 1.2 (strict) with the reviewer's decisions: the segments of the 2.1 export as <seg-source>/<target> <mrk mtype="seg">,
// accepted -> state signed-off approved=yes (edited text replaces the draft), sent back -> needs-translation (as emit/xliff12.py
// otherwise: ready translated, flagged needs-review-translation, no draft -> no target).
function xliff12(L){var trg=L==="fr"?"fr-CH":"it-CH",u=[],X=D.xn[L],nd=0,colon=L==="fr"?" : ":": ",ST={ready:"translated",flagged:"needs-review-translation"};
 var prot=function(){return '<mrk mtype="protected" comment="'+x(X.code_number)+'">'};
 ITEMS.forEach(function(it){if(it.lang!==L)return;var g=it.g,d=dec(it)||null,text=it.status==="human"?null:it.draft,edited=false,state=ST[it.status],appr="no";
  if(d&&(d.decision==="accept"||d.decision==="accept-edited")&&(it.status!=="human"||d.text)){state="signed-off";appr="yes";if(d.decision==="accept-edited"&&d.text){text=d.text;edited=true}}
  else if(d&&d.decision==="send-back")state="needs-translation";
  if(d)nd++;
  var src=g.deNew,beads=text==null?it.bd.map(function(b){return [b[0],b[1],0,0]}):edited?[[0,src.length,0,text.length]]:it.bd,code=edited?[]:it.nm.filter(function(n){return n[2]!=="model"});
  var outer=g.ch.map(function(c){return [c[0],c[1],"c"]}).concat(g.sn.filter(function(n){return !g.ch.some(function(c){return c[0]<=n[0]&&n[1]<=c[1]})}).map(function(n){return [n[0],n[1],"n"]})).sort(function(p,q){return p[0]-q[0]});
  function sm(a,b){var out="",pos=a;outer.forEach(function(sp){var p=Math.max(sp[0],a),q=Math.min(sp[1],b);if(p>=q||p<pos)return;out+=x(src.slice(pos,p));
    out+=sp[2]==="n"?prot()+x(src.slice(p,q))+"</mrk>":'<mrk mtype="x-changed" comment="'+x(X.changed)+'">'+inl(src,p,q,g.sn,prot)+"</mrk>";pos=q});return out+x(src.slice(pos,b))}
  var h='<trans-unit id="'+x(it.key)+'" resname="'+x(it.cud)+'" approved="'+appr+'" xml:space="preserve"><source xml:lang="de-CH">'+sm(0,src.length)+"</source>"+
   '<seg-source xml:lang="de-CH">'+beads.map(function(b,k){return '<mrk mtype="seg" mid="'+(k+1)+'">'+sm(b[0],b[1])+"</mrk>"}).join("")+"</seg-source>";
  if(text!=null)h+='<target state="'+state+'" xml:lang="'+trg+'">'+beads.map(function(b,k){return '<mrk mtype="seg" mid="'+(k+1)+'">'+inl(text,b[2],b[3],code,prot)+"</mrk>"}).join("")+"</target>";
  var prev12=note12("source",5,fmt(X.prev_de,{t:g.deOld}).replace(" : ",colon))+note12("target",5,fmt(X.prev_tgt,{t:plain(it.segs,true)}).replace(" : ",colon));
  it.xn.forEach(function(n){if(n[0]==="checks"||n[0]==="termbase"){h+=prev12;prev12=""}h+=note12(n[2],n[3],n[4],n[0]==="checks"?"gleichlaut-checks":"gleichlaut")});h+=prev12;
  if(d){var why=[d.reason,d.note].filter(Boolean).join("; ");h+=note12("target",1,fmt(X.review,{d:X.dec[d.decision]||d.decision}).replace(" : ",colon)+" ("+d.at+(d.by?", "+d.by:"")+")"+(why?colon+why:""))}
  h+='<alt-trans alttranstype="previous-version" origin="SL previous version" tool-id="gleichlaut"><source xml:lang="de-CH">'+x(g.deOld)+'</source><target xml:lang="'+trg+'">'+x(plain(it.segs,true))+"</target></alt-trans></trans-unit>";
  u.push(h)});
 return '<?xml version="1.0" encoding="UTF-8"?>\n<xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2"><file original="gleichlaut:'+x(M.run)+'" source-language="de-CH" target-language="'+trg+'" datatype="plaintext" tool-id="gleichlaut">'+
  '<header><tool tool-id="gleichlaut" tool-name="Gleichlaut" tool-company="Gleichlaut"/><note from="gleichlaut">'+x(X.about12)+'</note><note from="gleichlaut">'+x(X.states12)+'</note><note from="gleichlaut">'+x(X.prov)+"</note>"+
  '<note from="gleichlaut">'+x(fmt(X.reviewed,{n:nd})+" · "+new Date().toISOString())+"</note></header><"+"body>"+u.join("")+"</"+"body></file></xliff>\n"}
function msg(s){$("x-msg").textContent=s}
$("x-xlf").onclick=function(){var Ls=F.lang==="all"?["fr","it"]:[F.lang];Ls=Ls.filter(function(L){return ITEMS.some(function(it){return it.lang===L})});
 Ls.forEach(function(L,i){setTimeout(function(){download("gleichlaut-"+M.run+"-de-CH_"+(L==="fr"?"fr-CH":"it-CH")+"-reviewed.xlf",xliff(L),"application/xliff+xml")},i*400)});
 msg(t("dl")+": "+Ls.map(function(L){return "XLIFF 2.1 "+L.toUpperCase()}).join(", "))};
$("x-xlf12").onclick=function(){var Ls=F.lang==="all"?["fr","it"]:[F.lang];Ls=Ls.filter(function(L){return ITEMS.some(function(it){return it.lang===L})});
 Ls.forEach(function(L,i){setTimeout(function(){download("gleichlaut-"+M.run+"-de-CH_"+(L==="fr"?"fr-CH":"it-CH")+"-reviewed.xliff12.xlf",xliff12(L),"application/xliff+xml")},i*400)});
 msg(t("dl")+": "+Ls.map(function(L){return "XLIFF 1.2 "+L.toUpperCase()}).join(", "))};
// the one decisions export (draft and audit decisions, edits): the page keeps them only in this browser
$("x-dec").onclick=function(){download("gleichlaut-decisions-"+M.run+".json",JSON.stringify(payload(),null,1),"application/json");var b=$("x-dec");b.textContent=t("dl")+": JSON";
 setTimeout(function(){b.textContent=t("exportDec")},2500)};
$("x-copy").onclick=function(){var s=JSON.stringify(payload(),null,1),box=$("copybox");
 function fallback(){box.hidden=false;box.value=s;box.focus();box.select();msg(t("selcopy"))}
 try{if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(s).then(function(){box.hidden=true;msg(t("copied"))},fallback)}else fallback()}catch(e){fallback()}};
function importDecisions(o){var nd=0,na=0,note="";
 if(!o||typeof o!=="object"||!(o.decisions||o.audit))return t("impBad");
 if(o.decisions){if(o.run_sha256&&o.run_sha256!==M.run_sha256)note=" "+t("impRun");
  else{Object.keys(o.decisions).forEach(function(k){if(byKey[k]){S.dec[k]=o.decisions[k];nd++}});Object.keys(o.edits||{}).forEach(function(k){if(byKey[k])S.edits[k]=o.edits[k]});save()}}
 if(o.audit&&AU){var bySig={},byRid={};AU.rows.forEach(function(r){bySig[r.sig]=1;byRid[r.rid]=r.sig});        // by signature; old files by row id
  Object.keys(o.audit).forEach(function(k){var sg=bySig[k]?k:(!o.audit_date||o.audit_date===AU.meta.date)?byRid[k]:null;if(!sg)return;var d=o.audit[k];
   if(d&&ACTMAP[d.action])d.action=ACTMAP[d.action];if(d&&!d.date)d.date=o.audit_date||AU.meta.date;SA[sg]=d;na++});saveA();aMigrate()}
 return fmt(t("imported"),{d:nd,a:na})+note}
function pickImport(target){var f=$("imp-file");f.value="";f.onchange=function(){var file=f.files&&f.files[0];if(!file)return;var rd=new FileReader();
 rd.onload=function(){var m;try{m=importDecisions(JSON.parse(rd.result))}catch(e){m=t("impBad")}$(target).textContent=m;chrome();if(TAB==="audit")renderAudit();else{renderReg();renderCase()}};rd.readAsText(file)};f.click()}
$("x-imp").onclick=function(){pickImport("x-msg")};$("a-imp").onclick=function(){pickImport("a-msg")};
// ------------------------------------------------------------------ print: one case per page (drafts tab)
window.addEventListener("beforeprint",function(){if(TAB==="drafts")$("print").innerHTML=VIS.map(function(g){return '<article class="pcase">'+caseHTML(g,false)+"</article>"}).join("")});
window.addEventListener("afterprint",function(){$("print").innerHTML=""});
function fromHash(){var h=decodeURIComponent(location.hash.slice(1));if(h==="audit"&&AU){TAB="audit";return true}
 if(h==="drafts"){TAB="drafts";return true}
 var g=G.filter(function(g){return g.pair===h||g.no===h})[0];
 if(g){TAB="drafts";if(F.fam&&F.fam!==g.family){F.fam="";famAsk=false;famMsg=""}if(F.q){F.q="";$("f-q").value=""}if(!langs(g).length)F.lang="all";
  if(!(langs(g).some(function(L){return okItem(g.items[L])})))F.status="all";sel=g;return true}return false}
fromHash();chrome();if(TAB==="audit")renderAudit();else{renderReg();if(sel){markSel(true);renderCase()}}
window.GleichlautReview={xliff:xliff,xliff12:xliff12,payload:payload,importDecisions:importDecisions,setTab:setTab,auditCsv:auditCsv};
window.addEventListener("hashchange",function(){if(fromHash()){setTab(TAB)}});
})();
</script>
"""
