"""The review page template (HEAD = title + style, BODY = content + data + script), filled in by build.py.
No external request: fonts are inlined by build.fonts_css(), data by build.build()."""

HEAD = r"""<title>Gleichlaut Review</title>
<style>
__FONTS__
/* LAYOUT. A working tool, not a poster: one bar (name, the two views with their counts, progress, export, language),
   one line of context, then the work. Both views are the same two panes: a dense list on the left (filters on one line,
   marks explained once at the foot of the list) and the selected case on the right (numbered sections: 1 what changed or
   what differs, 2 the texts, 3 why, 4 the decision). Statistics, provenance and the full legend live in the footer.
   Type: Public Sans for texts and interface, Archivo condensed only for names (product, wordmark), Fragment Mono for codes,
   numbers and small labels. Colour: ink on white paper with hairline rules; ONE signal colour, international orange, only
   where something needs a person (flags, divergences, conflicting values, focus). No frames, cards, radii, shadows,
   gradients or decorative rulers. Below 900px the list sits above the case; no horizontal page scroll from 320px up. */
:root{--paper:#fbfbf9;--ink:#141513;--ink2:#62665f;--hair:#d9dbd4;--rule:#141513;--sig:#ff4f00;--sig-ink:#141513;--wash:#f0f1ec;
--sel:#141513;--sel-ink:#fbfbf9;--sheet:var(--paper);
--sans:"Public Sans","Helvetica Neue",Arial,sans-serif;--disp:"Archivo","Archivo Narrow","Helvetica Neue Condensed","Arial Narrow",sans-serif;
--mono:"Fragment Mono","Helvetica Mono",Menlo,Consolas,monospace;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#121412;--ink:#e6e8e2;--ink2:#9a9f96;--hair:#2f332f;--rule:#e6e8e2;--sig:#ff6a26;--sig-ink:#121412;--wash:#1a1d1a;--sel:#e6e8e2;--sel-ink:#121412;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#121412;--ink:#e6e8e2;--ink2:#9a9f96;--hair:#2f332f;--rule:#e6e8e2;--sig:#ff6a26;--sig-ink:#121412;--wash:#1a1d1a;--sel:#e6e8e2;--sel-ink:#121412;color-scheme:dark}
*{box-sizing:border-box;border-radius:0}
html{-webkit-text-size-adjust:100%;font-synthesis:none}
body{margin:0;background:var(--paper);color:var(--ink);font:400 14px/1.5 var(--sans);font-variant-numeric:tabular-nums;overflow-wrap:break-word}
button,select,input,textarea{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--sig);outline-offset:2px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important;scroll-behavior:auto!important}}
.app{max-width:1480px;margin:0 auto;padding-inline:24px}
.mono,.code{font-family:var(--mono)}
/* bar */
.bar{position:sticky;top:0;z-index:5;background:var(--paper);display:flex;flex-wrap:wrap;align-items:center;gap:6px 28px;min-height:56px;border-bottom:1px solid var(--rule);padding-block:6px}
.wm{font:600 24px/1 var(--disp);font-stretch:75%;letter-spacing:-.01em;margin-right:8px}
.views{display:flex;gap:22px;align-self:stretch}
.view{display:flex;align-items:center;gap:8px;background:none;border:0;border-bottom:2px solid transparent;margin-bottom:-7px;padding:0 0 1px;cursor:pointer;color:var(--ink2);font:500 15px/1 var(--sans)}
.view:hover{color:var(--ink)}
.view[aria-selected=true]{color:var(--ink);border-bottom-color:var(--ink)}
.view .c{font:400 12px/1 var(--mono);color:var(--ink2)}
.tools{margin-left:auto;display:flex;flex-wrap:wrap;align-items:center;gap:6px 16px;color:var(--ink2);font:400 12px/1.4 var(--mono)}
.tools b{color:var(--ink);font-weight:400}
.tools select{background:none;border:0;border-bottom:1px solid var(--hair);padding:1px 0}
.ctx{margin:0;padding:9px 0 10px;color:var(--ink2);font:400 13px/1.45 var(--sans);border-bottom:1px solid var(--hair);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;max-width:150ch}
.ctx b{color:var(--ink);font-weight:500}
.ctx .qh{background:none;border:1px solid var(--ink2);border-radius:50%;width:17px;height:17px;padding:0;margin:0 6px 0 0;font:500 11px/15px var(--sans);color:var(--ink);cursor:pointer;vertical-align:1px}
.ctx .qh[aria-expanded="true"]{background:var(--sel);color:var(--sel-ink)}
.lanehelp{margin:0;padding:6px 0 9px;color:var(--ink2);font:400 12.5px/1.45 var(--sans);border-bottom:1px solid var(--hair);max-width:150ch}
/* buttons */
.tb{background:none;border:0;padding:1px 0;cursor:pointer;color:var(--ink2);border-bottom:1px solid transparent}
.tb:hover{color:var(--ink);border-bottom-color:var(--hair)}
.tb[aria-pressed=true]{color:var(--ink);border-bottom-color:var(--ink)}
.box{background:none;border:1px solid var(--ink);padding:4px 10px;cursor:pointer;white-space:nowrap;font:400 12px/1.3 var(--mono)}
.box:hover{background:var(--wash)}
.box[aria-pressed=true],.box.primary{background:var(--ink);color:var(--paper)}
.box:disabled{opacity:.45;cursor:default}
/* two panes */
.work{display:grid;grid-template-columns:minmax(320px,440px) minmax(0,1fr);gap:0 36px}
.register{border-right:1px solid var(--hair);padding:10px 20px 0 0;min-width:0;position:sticky;top:56px;align-self:start;height:calc(100vh - 56px);display:flex;flex-direction:column}
.filters{display:flex;flex-wrap:wrap;gap:6px 14px;padding-bottom:9px;font:400 12px/1.4 var(--mono);align-items:baseline}
.fl{display:flex;flex-wrap:wrap;gap:2px 6px;align-items:baseline}
.fl .k{color:var(--ink2)}
.fl:has(input){flex:1 1 100%}
.fl select,.fl input{background:none;border:0;border-bottom:1px solid var(--hair);padding:3px 0;min-width:0;font:400 13px/1.3 var(--sans)}
.fl input{flex:1 1 140px}.fl select{flex:0 1 auto;max-width:100%;min-width:0}
#f-fam{flex:1 1 100%;width:100%;max-width:100%;text-overflow:ellipsis}.register .filters{min-width:0;max-width:100%}
.tbl{overflow-x:auto;min-width:0}
.reg-wrap{overflow:auto;flex:1 1 auto;min-height:120px;border-top:1px solid var(--rule)}
table{border-collapse:collapse;width:100%}
th{font:400 11px/1.4 var(--mono);text-align:left;color:var(--ink2);padding:6px 8px;border-bottom:1px solid var(--hair);vertical-align:bottom}
td{padding:6px 8px;border-bottom:1px solid var(--hair);vertical-align:top}
#reg,#aud{table-layout:fixed}
#reg thead th,#aud thead th{position:sticky;top:0;background:var(--paper);z-index:1}
#reg col.c-fr,#reg col.c-it{width:30px}#reg col.c-prod{width:46%}
#reg td.m{text-overflow:clip;padding-inline:4px;text-align:center}#reg th.m{text-align:center;padding-inline:4px}
#reg td,#aud td{cursor:pointer}
#reg td{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#reg td.no{font:400 11px/1.6 var(--mono);color:var(--ink2)}
#reg td.prd{font-weight:500}
#reg td.prd .pc{display:block;font:400 11px/1.4 var(--mono);color:var(--ink2);overflow:hidden;text-overflow:ellipsis;font-weight:400}
#reg td.chg{color:var(--ink2);white-space:normal}#reg td.chg .cl{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;line-height:1.35}
#reg tr:hover td,#aud tr.cnt:hover td{background:var(--wash)}
#reg tr[aria-selected=true] td,#aud tr[aria-selected=true] td,#reg tr[aria-selected=true]:hover td,#aud tr[aria-selected=true]:hover td{background:var(--sel);color:var(--sel-ink)}
#reg tr[aria-selected=true] td *,#aud tr[aria-selected=true] td *{color:var(--sel-ink)!important}
.mk{display:inline-block;min-width:1.3em;text-align:center;font:400 13px/1 var(--mono)}.mk.r{color:var(--sig)}.mk.o,.mk.f{color:var(--ink2)}
.lt{font:400 11px/1.4 var(--mono);letter-spacing:.04em;color:var(--ink2)}
.lt.s{color:var(--sig)}
.count{color:var(--ink2);padding:6px 0 10px;font:400 11px/1.6 var(--mono);border-top:1px solid var(--hair)}
.count .key{display:inline;padding:0;margin-left:10px}.count .key>span{margin-right:8px}
.export{display:flex;flex-wrap:wrap;gap:8px;padding:8px 0 12px;border-top:1px solid var(--hair)}
.export .msg{color:var(--ink2);flex-basis:100%;font:400 12px/1.4 var(--mono)}
.key{margin:0;padding:6px 0 0;color:var(--ink2);font:400 11px/1.7 var(--mono);overflow-wrap:anywhere}
.key>span{margin-right:12px;white-space:nowrap}
.key .v2{border:1px solid var(--sig);padding:0 2px;color:var(--ink)}.key .v1{border-bottom:1px solid var(--ink2);color:var(--ink)}
.key .obar{display:inline-block;width:2px;height:1em;background:var(--sig);vertical-align:-2px;margin-right:4px}
.xl{font:400 11px/1.3 var(--mono);color:var(--ink2)}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
#copybox{width:100%;height:90px;font:12px/1.4 var(--mono);border:1px solid var(--hair);background:var(--paper)}
/* case */
.case{min-width:0;padding:22px 0 40px;max-width:1040px;scroll-margin-top:64px}
html{scroll-padding-top:64px}.case h2{scroll-margin-top:72px}
.dec .why2{display:block;color:var(--ink2);font:400 12px/1.4 var(--mono);margin-top:2px}
.case:focus{outline:none}
h2{font:600 32px/1.05 var(--disp);font-stretch:75%;margin:0;letter-spacing:-.005em}
.ref{color:var(--ink2);margin:6px 0 0;font:400 12px/1.5 var(--mono);overflow-wrap:anywhere}
.sec{border-top:1px solid var(--hair);margin-top:22px;padding-top:10px;position:relative}
.sl{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline;margin-bottom:12px;font:600 14px/1.3 var(--sans);color:var(--ink)}
.sl .no{position:absolute;left:-28px;font:400 12px/1.6 var(--mono);color:var(--ink2)}.sl .no b{display:none}
.sl .sp{margin-left:auto;font:400 12px/1.4 var(--mono)}
.back{display:none;margin-bottom:12px}
.txt{font:400 17px/1.6 var(--sans);white-space:pre-wrap;overflow-wrap:anywhere;max-width:70ch}
.de{border-left:2px solid var(--hair);padding-left:14px}
ins{text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:3px;text-decoration-color:var(--ink)}
del{color:var(--ink2);text-decoration:line-through;text-decoration-thickness:1px;margin-right:.2em}
.gap{color:var(--ink2);font-family:var(--mono);font-size:13px;padding:0 4px}
.n{font:inherit;border-bottom:1px dotted var(--ink2);white-space:nowrap}
.n sup{display:none;font:400 .6em/1 var(--mono);color:var(--ink2);margin-left:1px;vertical-align:.5em}
.case.slots .n sup{display:inline}
.n.m{border:1px solid var(--sig);padding:0 2px}
.drafts{display:grid;grid-template-columns:1fr 1fr;grid-template-rows:repeat(4,auto);column-gap:36px}
.drafts.one{grid-template-columns:minmax(0,1fr)}
.lang{display:grid;grid-row:span 4;grid-template-rows:subgrid;min-width:0;row-gap:0}
.lang>*{min-width:0}
.lh1{display:flex;flex-wrap:wrap;gap:2px 10px;align-items:baseline;padding-bottom:8px;font:400 12px/1.5 var(--mono);color:var(--ink2)}
.lh1 .ln{font:600 15px/1.3 var(--sans);color:var(--ink)}
.lh1 .st{color:var(--ink)}.lh1 .st.r{color:var(--sig)}.lh1 .st .tq{border-bottom:1px solid var(--sig)}.lh1 .key{margin-left:auto;padding:0}
.lang .body{padding-bottom:4px}
.lang .why{border-top:1px solid var(--hair);margin-top:14px;padding-top:10px}
.lang .why .wh{display:flex;flex-wrap:wrap;gap:2px 10px;font:400 12px/1.5 var(--mono);color:var(--ink2);margin-bottom:4px}
.lang .why .tri b{color:var(--ink);font-weight:400}
.lang .dec{border-top:1px solid var(--hair);margin-top:12px;padding:10px 0 4px 0;border-left:0}
.lang .dec.focus .btns .box{border-color:var(--ink)}
.dec .btns .box{padding:7px 14px;font-size:13px}
.dl{display:flex;flex-wrap:wrap;gap:2px 10px;align-items:baseline;margin-bottom:8px;font:400 12px/1.5 var(--mono);color:var(--ink2)}
.dl .ln{color:var(--ink)}
.dl .st{color:var(--ink)}.dl .st.r{color:var(--sig)}
.dl .key{margin-left:auto;padding:0}
.dl .cap{flex-basis:100%;font:400 12px/1.4 var(--sans)}
.dl .tri b{color:var(--ink);font-weight:400}
.famline{color:var(--ink2);margin:2px 0 0;font:400 12px/1.5 var(--mono);overflow-wrap:anywhere}.famline .tb{color:var(--ink)}
.ids{color:var(--ink2);margin-top:2px;font:400 11px/1.5 var(--mono)}.ids summary{cursor:pointer;display:inline}
.notice{border-left:2px solid var(--sig);padding:2px 0 2px 12px;margin:0 0 12px;font:400 15px/1.45 var(--sans)}
.notice .mk{color:var(--sig);margin-right:6px;min-width:0}
.notice p{margin:0}.notice p+p{margin-top:4px}
.notice.lang p:first-child{font-weight:500}
.ed{outline:1px solid transparent;padding:2px 4px;margin:0 -4px}
.ed:hover{outline-color:var(--hair)}
.ed:focus{outline:1px solid var(--ink)}
.edmeta{color:var(--ink2);margin-top:6px;display:flex;flex-wrap:wrap;gap:4px 14px;align-items:baseline;font:400 12px/1.4 var(--mono)}
.human{font:400 15px/1.45 var(--sans);margin:0 0 8px}
.why{margin-bottom:14px}.why+.why{border-top:1px solid var(--hair);padding-top:10px}
.reasons{margin:4px 0 6px;padding-left:1.4em;font:400 15px/1.45 var(--sans);max-width:75ch}
.reasons li+li{margin-top:4px}.reasons li.low{color:var(--ink2)}
.reasons li::marker{font:400 12px var(--mono);color:var(--ink2)}
.why p.tb{margin:2px 0 6px;color:var(--ink2);font:400 13px/1.45 var(--sans);border:0}
.why .ok{font:400 15px/1.45 var(--sans);margin:4px 0 6px}
.why .more{color:var(--ink2);margin:0 0 4px;font:400 12px/1.4 var(--mono)}
details>summary{cursor:pointer;color:var(--ink2);font:400 12px/1.4 var(--mono);padding:3px 0}
details[open]>summary{margin-bottom:6px}
.ledger{table-layout:auto;min-width:480px;margin-bottom:12px}
.ledger td{font-size:13px}.ledger td.res{white-space:nowrap;font-family:var(--mono);font-size:12px}.ledger td.chk{width:34%}
.ledger .FAIL{color:var(--sig)}.ledger .FAILf{color:var(--ink)}.ledger .na{color:var(--ink2)}
.ledger .fd{font:400 14px/1.4 var(--sans)}.ledger .fd p{margin:0}.ledger .fd p+p{margin-top:3px}
.ledger .cn{display:block;font:400 12px/1.4 var(--mono);margin-top:2px}
.ledger details{margin-top:3px}.ledger details div{overflow-wrap:anywhere;white-space:pre-wrap;color:var(--ink2);font-size:12px}
.ledger details.pf{border-top:1px dotted var(--hair);padding-top:3px}
.decs{display:grid;grid-template-columns:1fr 1fr;gap:0 18px}
.decs.one{grid-template-columns:1fr}
.dec{min-width:0;border-left:2px solid transparent;padding:4px 0 6px 12px}
.dec.focus{border-left-color:var(--ink)}
.btns{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}
.dec label{display:block;color:var(--ink2);margin-top:8px;font:400 12px/1.4 var(--mono)}
.dec select,.dec textarea{display:block;width:100%;margin-top:3px;background:var(--paper);border:1px solid var(--hair);padding:4px 6px;font:400 14px/1.4 var(--sans);color:var(--ink)}
.dec textarea{min-height:52px;resize:vertical}
.dec .stt,.stt{color:var(--ink2);margin-top:4px;font:400 12px/1.4 var(--mono)}.stt.done{color:var(--ink)}
.sl .sub{flex-basis:100%;font:400 12px/1.4 var(--mono);color:var(--ink2)}
.lsn{color:var(--ink2)}
.ctx .lsel select{background:none;border:0;border-bottom:1px solid var(--ink);padding:0 2px 0 0;margin-right:4px;font:500 13px/1.3 var(--sans);color:var(--ink);max-width:min(100%,46ch);text-overflow:ellipsis}
.save{position:sticky;bottom:0;z-index:2;background:var(--paper);display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;margin-top:16px;padding:10px 0;border-top:1px solid var(--rule)}
.save .hint{color:var(--ink2);font:400 12px/1.4 var(--mono)}
.empty{color:var(--ink2);padding:24px 0}
.fambar{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:baseline;padding-top:4px}
.fambar .q{flex-basis:100%;font:400 14px/1.4 var(--sans)}.fambar .msg{color:var(--ink2);flex-basis:100%}
/* audit list */
#aud col.a-mk{width:36px}#aud col.a-what{width:44%}
#aud td{font-size:13px}
#aud td.ap b{display:block;font-weight:500}
#aud td.ap .code{display:block;font-size:11px;color:var(--ink2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#aud td.aw{font:400 12px/1.45 var(--mono);color:var(--ink)}
#aud td.aw .kd{display:block;color:var(--ink2)}
#aud tr.grp td{cursor:default;font:600 12px/1.4 var(--sans);color:var(--ink);padding:14px 8px 5px;border-bottom:1px solid var(--rule);background:none!important}
#aud tr.eqh td{cursor:default;padding:12px 8px 5px;border-bottom:1px solid var(--rule)}
#aud tr.eqh button{background:none;border:0;padding:0;cursor:pointer;font:600 12px/1.4 var(--sans);color:var(--ink2)}
#aud tr.eq td{color:var(--ink2)}
#aud tr.exp td,#aud tr.expd td,#aud tr.expn td{cursor:default}#aud tr.exp td{border-bottom:0}#aud tr.expd td{padding-top:0}
#aud tr.expn td{color:var(--ink2);font:400 12px/1.45 var(--sans)}#aud .expd .snip{font-size:13px;line-height:1.45;margin-top:3px}
/* audit case */
.snip{font:400 15px/1.55 var(--sans);overflow-wrap:anywhere}
.snip .v2{border:1px solid var(--sig);padding:0 2px;white-space:nowrap}
.snip .v2.w{white-space:normal;-webkit-box-decoration-break:clone;box-decoration-break:clone}
.snip .v1{border-bottom:1px solid var(--ink2)}
.snip.src-s{color:var(--ink2)}
.na{color:var(--ink2)}
.ftg{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0 18px;margin:4px 0 10px}
.ftc{min-width:0}.ftc+.ftc{border-left:1px solid var(--hair);padding-left:18px}
.ftc.odd{box-shadow:inset 2px 0 0 var(--sig);padding-left:14px}
.ftc .lh{display:flex;gap:8px;align-items:baseline;font:400 12px/1.4 var(--mono);color:var(--ink2);margin-bottom:4px}
.ftc .lh .oddl{color:var(--sig)}
.oddl{font:400 11px/1.3 var(--mono);color:var(--sig)}
.snip.ftx{font:400 15px/1.6 var(--sans)}
.ftl{margin:14px 0 2px;color:var(--ink2);font:400 12px/1.4 var(--mono)}.ftl b{color:var(--ink);font:500 15px/1.3 var(--sans);margin-right:6px}
.facts{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:3px 18px;margin:0;font:400 14px/1.45 var(--sans)}
.facts dt{color:var(--ink2);font:400 12px/1.8 var(--mono)}.facts dd{margin:0}
.facts a{color:var(--ink)}.facts .term,.facts .sub2{display:block}.facts .sub2{color:var(--ink2);font-size:13px;margin-top:3px}
.term s{color:var(--sig);text-decoration-thickness:1px}.term u{text-decoration-thickness:2px;text-underline-offset:3px}
table.mem{width:100%;table-layout:auto;margin:4px 0 6px}
table.mem td{font-size:13px;padding:6px 10px 6px 0;cursor:default}
table.mem td.mf{width:44px;white-space:nowrap;color:var(--ink2);font-family:var(--mono)}table.mem td.mc{width:40%}
table.mem .code{color:var(--ink2);font-size:12px}table.mem .sub2{display:block;color:var(--ink2);font-size:12px}
.adec{display:grid;grid-template-columns:minmax(0,1fr);gap:14px 0}
.adec .btns .box{padding:7px 14px;font-size:13px}.adec .grp2{display:flex;flex-wrap:wrap;gap:6px;align-items:baseline;margin-top:6px}
.adec .grp2 .lbl{font:400 12px/1.4 var(--mono);color:var(--ink2);min-width:9em}
.adec .q{display:block;font:400 12px/1.4 var(--mono);color:var(--ink2);margin-bottom:4px}
.adec select,.adec textarea{width:100%;background:var(--paper);border:1px solid var(--hair);padding:4px 6px;font:400 14px/1.4 var(--sans);color:var(--ink)}
.adec textarea{display:block;margin-top:8px;min-height:60px;resize:vertical}
.acts{display:flex;flex-direction:column;gap:4px;font:400 14px/1.35 var(--sans)}
.acts .fixl{color:var(--ink)}.acts .fixg{display:inline-flex;gap:14px;margin:0 0 4px 22px}
.acts .ck{display:inline-flex;gap:8px;align-items:baseline;cursor:pointer}
.acts input{accent-color:var(--ink);margin:0;transform:translateY(1px)}
.sug{color:var(--ink2);font:400 12px/1.4 var(--mono);margin-top:6px}
.adec .sub2{display:block;color:var(--ink2);font:400 12px/1.4 var(--sans);margin-bottom:2px}
.oddb{font-size:11px}.box[aria-pressed=false] .oddb{color:var(--sig)}
.arem{display:flex;flex-direction:column;align-items:flex-start;gap:6px;margin:6px 0}.arem .box{white-space:normal;text-align:left;padding:7px 14px;font-size:13px;max-width:100%}
.arem .box:disabled,.arem .box[aria-disabled="true"],.save .box[aria-disabled="true"]{opacity:.45;cursor:not-allowed}.arem .hint{color:var(--ink2);font:400 12px/1.4 var(--mono)}
.hint.warn{color:var(--ink);border-left:2px solid var(--sig);padding-left:6px}.box.pend{outline:1px dashed var(--sig);outline-offset:2px}
.aconf{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:baseline;margin:6px 0 2px;padding:8px 10px;border:1px solid var(--ink);background:var(--wash)}.aconf .q{flex-basis:100%;font:400 14px/1.4 var(--sans);color:var(--ink)}
.who.ask input{border-bottom:2px solid var(--sig)}.who input#a-rev{width:min(100%,40ch)}.who+.adec{margin-top:16px}.aname{margin:6px 0 0;font:400 13px/1.4 var(--sans);color:var(--ink)}
/* footer: what the register is, its numbers, provenance, the full legend */
footer{border-top:1px solid var(--hair);margin-top:32px;padding:10px 0 32px;color:var(--ink2);font:400 11px/1.6 var(--mono)}
.menu{position:relative}.menu>summary{list-style:none;cursor:pointer}.menu>summary::-webkit-details-marker{display:none}
.menu>summary::after{content:" ▾"}
.menu .mm{position:absolute;right:0;top:calc(100% + 6px);z-index:10;background:var(--paper);border:1px solid var(--ink);padding:8px 12px;display:flex;flex-direction:column;align-items:flex-start;gap:6px;min-width:240px;font:400 13px/1.4 var(--sans)}
.menu .mm .tb{color:var(--ink)}.menu .mm .msg{color:var(--ink2);font:400 11px/1.4 var(--mono)}
.who{margin-top:10px;font:400 12px/1.4 var(--mono);color:var(--ink2)}.who input{background:none;border:0;border-bottom:1px solid var(--hair);padding:2px 0;font:400 14px/1.4 var(--sans);color:var(--ink);min-width:220px}
footer h3{font:500 13px/1.4 var(--sans);color:var(--ink);margin:0 0 8px}
footer p{margin:6px 0 0;overflow-wrap:anywhere;max-width:150ch}
.kv{display:grid;grid-template-columns:1fr 1fr;gap:0 40px}
.kv dl{margin:0;display:grid;grid-template-columns:minmax(140px,max-content) 1fr;gap:2px 16px;align-content:start}
.kv dt{color:var(--ink2)}.kv dd{margin:0;color:var(--ink);overflow-wrap:anywhere}
.kv .pass{color:var(--ink)}.kv .fail{color:var(--sig)}.kv .big{color:var(--ink)}
#print{display:none}
[hidden]{display:none!important}
@media (max-width:900px){
 .app{padding-inline:16px}
 .work.case-open .register{display:none}.back{display:inline-block}.sl .no{position:static}
 .lang{display:block;grid-row:auto}.drafts{grid-template-rows:none}.lang+.lang{border-top:1px solid var(--rule);margin-top:18px;padding-top:12px}
 .register .key{display:none}.ctx{white-space:normal;display:block;-webkit-line-clamp:none;overflow:visible}.ctx .lsel{display:block;margin-bottom:4px}
 .key>span{white-space:normal}.tools{gap:6px 12px}.wm{font-size:22px}.views{gap:16px}.box{white-space:normal}
 .bar{position:static}.views{align-self:auto}.view{margin-bottom:0;padding-bottom:4px}.tools{margin-left:0}
 .work{grid-template-columns:minmax(0,1fr)}
 .register{position:static;height:auto;border-right:0;padding-right:0;border-bottom:1px solid var(--rule)}
 .reg-wrap{max-height:46vh}
 .drafts,.decs,.adec,.kv{grid-template-columns:1fr}
 .dr{padding-right:0}.dr+.dr{border-left:0;border-top:1px solid var(--hair);padding:12px 0 0;margin-top:12px}
 .ftg{grid-template-columns:minmax(0,1fr)}.ftc+.ftc{border-left:0;padding-left:0;border-top:1px solid var(--hair);margin-top:8px;padding-top:8px}
 .ftc.odd{padding-left:12px}
 .adec>div+div{margin-top:12px}
}
@media print{
 @page{size:A4;margin:14mm}
 body{font-size:10pt;background:#fff;color:#000}
 .bar,.register,.save,.export,.edmeta,.btns,.dec select,.dec textarea,#case,#acase{display:none!important}
 .why details{display:none}
 .work{display:block}
 #print{display:block}
 .pcase{break-after:page;page-break-after:always}
 .txt{font-size:11pt}
}
</style>
"""

BODY = r"""<div class="app">
<header class="bar">
 <span class="wm">Gleichlaut</span>
 <nav class="views" role="tablist" aria-label="Views" data-aria="views"><button class="view" role="tab" type="button" id="t-audit" aria-controls="p-audit"></button><button class="view" role="tab" type="button" id="t-drafts" aria-controls="p-drafts"></button></nav>
 <div class="tools"><span id="progress"></span>
  <details class="menu" id="xmenu"><summary class="box" id="x-sum"></summary><div class="mm">
   <button class="tb" id="x-dec" type="button"></button><button class="tb" id="x-xlf" type="button"></button><button class="tb" id="x-xlf12" type="button"></button>
   <button class="tb" id="x-copy" type="button"></button><button class="tb" id="x-imp" type="button"></button>
   <button class="tb" id="a-csv-i" type="button"></button><button class="tb" id="a-csv" type="button"></button><button class="tb" id="a-imp" type="button"></button>
   <span class="msg" id="x-msg" aria-live="polite"></span><span class="msg" id="a-msg" aria-live="polite"></span><span class="msg" id="where"></span>
   <textarea id="copybox" hidden readonly aria-label="Decisions JSON" data-aria="json"></textarea></div></details>
  <label><span id="l-ui" class="vh"></span><select id="ui-lang" aria-label="Interface language" data-aria="uil"><option value="de">DE</option><option value="en">EN</option><option value="fr">FR</option><option value="it">IT</option></select></label><button class="tb" id="theme" type="button"></button></div>
</header>
<p class="ctx" id="ctxline"></p>
<p class="lanehelp" id="lanehelp" hidden></p>
<div class="work" id="p-audit" role="tabpanel" aria-labelledby="t-audit" hidden>
 <section class="register" aria-label="Issues" data-aria="issues">
  <div class="filters"><div class="fl" id="a-show"></div><div class="fl" id="a-lang"></div><div class="fl" id="a-kind"></div><div class="fl" id="a-since" hidden></div>
</div>
  <div class="tbl reg-wrap" id="aud-wrap"><table id="aud"><colgroup><col class="a-mk"><col><col class="a-what"></colgroup>
   <thead><tr><th id="ah-no"></th><th id="ah-lim"></th><th id="ah-kind"></th></tr></thead><tbody></tbody></table></div>
  <div class="count" id="a-shown"></div>
 </section>
 <section class="case" id="acase" tabindex="-1" aria-label="Issue" data-aria="issue"></section>
</div>
<div class="work" id="p-drafts" role="tabpanel" aria-labelledby="t-drafts">
 <section class="register" id="register" aria-label="Register" data-aria="register">
  <div class="filters">
   <div class="fl" id="f-status"></div>
   <div class="fl" id="f-lang"></div>
   <div class="fl"><select id="f-fam" aria-label="Family" data-aria="family"></select><input type="search" id="f-q" aria-label="Search product or limitation code" data-aria="search"></div>
   <div class="fambar" id="fam-bulk" hidden></div>
  </div>
  <div class="tbl reg-wrap" id="reg-wrap"><table id="reg"><colgroup><col class="c-fr"><col class="c-it"><col class="c-prod"><col></colgroup>
   <thead><tr><th class="m">FR</th><th class="m">IT</th><th id="h-prod"></th><th id="h-chg"></th></tr></thead><tbody></tbody></table></div>
  <div class="count"><span id="shown"></span> <span class="key" id="reg-key"></span></div>
 </section>
 <section class="case" id="case" tabindex="-1" aria-label="Case" data-aria="case"></section>
</div>
<input type="file" id="imp-file" accept="application/json,.json" multiple class="vh" tabindex="-1" aria-hidden="true">
<textarea id="clipbox" class="vh" tabindex="-1" aria-hidden="true" readonly></textarea>
<footer><p id="prov"></p></footer>
</div>
<div id="print"></div>
<script type="application/json" id="data">__DATA__</script>
__LANES__<script>
(function(){
"use strict";
// lanes: the page carries the drafts of each lane (build.LANES) and parses only the one it shows. The first is the default
// (Apertus 8B Q8_0 on CPU); another is named by the hash prefix (#70b, #70b/wb013, #aug2026/drafts) and survives a reload.
var D0=JSON.parse(document.getElementById("data").textContent),LANES=D0.lanes||[],DEF=LANES.length?LANES[0].id:"";
function laneOf(h){var m=/^([a-z0-9]+)(?:\/|$)/.exec(h||""),ok=function(id){return LANES.some(function(l){return l.id===id})};return m&&ok(m[1])?m[1]:DEF}
function hashRest(h){var m=/^([a-z0-9]+)(?:\/|$)/.exec(h||"");return m&&laneOf(h)===m[1]&&LANES.length?(h.slice(m[0].length)||"drafts"):h}
var LANE=laneOf(decodeURIComponent(location.hash.slice(1))),HP=LANE&&LANE!==DEF?LANE+"/":"",DL=HP&&document.getElementById("data-"+LANE);
var D=DL?JSON.parse(DL.textContent):D0;if(D!==D0){D.audit=D0.audit;D.lanes=LANES}D0=null;
var M=D.meta,A=D.all,G=D.groups,AU=D.audit;
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
// record time stamps: Europe/Zurich local time with its offset (2026-10-11T01:45:12+02:00); older UTC stamps are converted
function zts(x){var d=x instanceof Date?x:new Date(x==null?Date.now():x);if(isNaN(d.getTime()))return x==null?"":String(x);
 try{var p={};new Intl.DateTimeFormat("en-GB",{timeZone:"Europe/Zurich",hourCycle:"h23",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",second:"2-digit"}).formatToParts(d).forEach(function(q){p[q.type]=q.value});
  var off=Math.round((Date.UTC(+p.year,+p.month-1,+p.day,+p.hour,+p.minute,+p.second)-Math.floor(d.getTime()/1000)*1000)/60000),a=Math.abs(off);
  return p.year+"-"+p.month+"-"+p.day+"T"+p.hour+":"+p.minute+":"+p.second+(off<0?"-":"+")+("0"+Math.floor(a/60)).slice(-2)+":"+("0"+a%60).slice(-2)}catch(e){return d.toISOString()}}
function tms(x){var n=Date.parse(x||"");return isNaN(n)?0:n}
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
 rdT1:"T1 Vokabular: ein «unbekanntes Wort», das ein wohlgeformtes Wort der Zielsprache ist (nur Buchstaben der Zielsprache, mind. 4, keine deutschen Lautfolgen wie sch/ck/tz/-ung/-keit/-lich, kein Wort des deutschen Textes, nicht mit dessen ersten 8 Buchstaben und, grossgeschrieben, nicht mit den ersten 4 Buchstaben eines deutschen Wortes des Textes, ausser es steht schon im bisherigen Text).",
 rdT2:"T2 Modalverb: das zusätzliche «doit/deve» entspricht einer deutschen Konstruktion «ist/sind … zu + Verb», die die Prüfung nicht als Modalverb zählt, und der Text sagt «doit être / deve essere».",
 rdT3:"T3 Zahlen: der Entwurf ändert genau dieselben Zahlenwerte wie das Deutsche (Zahlwörter 2–12 als Zahlen, Dezimalkomma als Dezimalpunkt).",
 rdT4:"T4 Abkürzung: als «Deutsch» gemeldete Wörter sind alle römische Zahlen oder Abkürzungen (mind. 2 Grossbuchstaben, mind. die Hälfte der Buchstaben, kein Umlaut).",
 triHead:"Sortierung der Markierungen (ordnet und klappt nur ein; der Status bleibt, kein Befund wird verborgen):",
 limitation:"Limitierung",ids:"interne Kennungen",family:"Familie",pair:"Paar",itemsL:"Elemente",
 copyTxt:"Text kopieren",copiedTxt:"Text kopiert (reiner Text für das ePL-Feld).",copySel:"Zwischenablage gesperrt: Der Text ist markiert, mit Ctrl/Cmd+C kopieren.",
 imp:"Entscheide importieren",imported:"Importiert: {d} Entscheide zu Entwürfen, {a} Entscheide zur Registerprüfung.",impBad:"Keine Gleichlaut-Entscheiddatei.",
 impRun:"Die Entscheide zu Entwürfen stammen aus einem anderen Lauf und wurden nicht importiert.",
 where:"Entscheide werden nur in diesem Browser gespeichert (lokaler Speicher dieser Seite, pro Browserprofil). Mit «JSON exportieren» sichern oder weitergeben, mit «Entscheide importieren» wiederherstellen.",
 oldLang:"Der bisherige {A} Text ist auf {F}.",adj:{fr:"französische",it:"italienische"},lname:{de:"Deutsch",fr:"Französisch",it:"Italienisch",en:"Englisch",rm:"Rätoromanisch"},
 aLead:"Widersprüche, die schon heute zwischen dem deutschen, französischen und italienischen Text der geltenden SL bestehen (Stand {d}), vom Code gefunden, bevor ein Entwurf entsteht. Die bekannten, im Text belegten Abweichungen sind der Beleg für das Problem.",
 aKnownHead:"Bekannte Abweichungen, im Text belegt: {k} von {n} gefunden",aOtherHead:"Weitere Befunde der Prüfung",
 aLim:"Limitierung",aKind:"Art",aOdd:"Weicht ab",aRight:"Welche Sprache stimmt?",aAction:"Massnahme · Notiz",aNote:"Notiz",aSug:"Vorschlag der Prüfung",
 aNoSnip:"kein Auszug in der Prüfdatei",aSnapSrc:"Auszug aus dem SL-Stand: der zugeordnete Satz, darin die Stelle mit den gemeinsamen Zahlen",
 kinds:{number:"Zahl",unit:"Einheit",language:"Sprache",editorial:"Redaktionell"},aUnclear:"unklar",acts:{"Berichtigung":"Berichtigung","GÄL":"GÄL","none":"keine","unclear":"unklar"},
 aShow:"Anzeigen",aKnownF:"Bekannt",aAllF:"Alle",aOpenF:"Offen",aDecF:"Entschieden",aKindF:"Art",aShown:"Befunde angezeigt",
 aSnap:"SL-Stand",aChecked:"Geprüfte Limitierungen",aFindings:"Befunde",aOnLims:"in {n} Limitierungen",aKnown:"Bekannte Abweichungen gefunden",aReal:"Echt bei Blindprüfung (Zahlen)",
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
 rdT1:"T1 vocabulary: an 'unknown word' that is a well-formed target-language word (target alphabet only, at least 4 letters, no German letter sequence such as sch/ck/tz/-ung/-keit/-lich, not a word of the German text, not sharing its first 8 letters with one, and, when capitalised, not starting with the first 4 letters of a German word of the text unless the old text already has it).",
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
fr:{ui:"Interface",sub:"Registre de révision",drafts:"brouillons",model:"Modèle",run:"Série",guards:"Contrôles",items:"Éléments",changes:"Modifications",ready:"Prêts",flagged:"Signalés",
 exact:"Exact vs règles seules",rule:"Règle préenregistrée",human:"Confiés à un traducteur",divergent:"Ancien texte divergent",decided:"décidés",
 status:"Statut",language:"Langue",open:"Ouverts",all:"Tous",decidedF:"Décidés",divF:"Divergents",allFam:"Toutes les familles",search:"Produit ou code",
 mark:"Marque",no:"N°",product:"Produit",change:"Modification",shown:"modifications affichées",xlf:"Exporter XLIFF 2.1",json:"Exporter JSON",copy:"Copier les décisions",
 copied:"Décisions copiées dans le presse-papiers.",selcopy:"Presse-papiers bloqué : le JSON est sélectionné ci-dessous, copiez-le avec Ctrl/Cmd+C.",dl:"Téléchargé",
 s1:"Modification du texte allemand",s2:"Brouillons",s3:"Contrôles",s4:"Décision",ctxA:"Contexte : autour des modifications",ctxF:"Contexte : texte entier",de:"Allemand",fr:"Français",it:"Italien",
 lready:"prêt",lflagged:"signalé",lhuman:"confié à un traducteur",readyAttn:"prêt (ancien texte à vérifier)",edited:"modifié",reset:"Rétablir le brouillon",editHint:"Cliquez dans le texte pour le modifier sur place.",
 check:"Contrôle",result:"Résultat",finding:"Constat",pass:"ok",fail:"ÉCHEC",na:"s.o.",raw:"détail technique",noChecks:"Pas de contrôle : pas de brouillon machine.",
 accept:"Accepter tel quel",acceptEd:"Accepter modifié",sendBack:"Renvoyer",reason:"Motif",note:"Remarque (pourquoi)",saveNext:"Enregistrer, suivant",keys:"touches 1/2/3 décider · f/i langue · Ctrl/Cmd+Entrée enregistrer, suivant",
 savedAt:"enregistré",openSt:"ouvert",noEdit:"Modifiez d'abord le texte du brouillon (cliquez dedans).",
 humanTxt:"Confié à un traducteur : l'allemand a été réécrit à plus de 60 %",humanShort:"Confié à un traducteur, pas de brouillon machine",humanPrev:"Ancien texte (modifiez-le sur place pour écrire la nouvelle version) :",
 none:"Aucune modification ne correspond à ces filtres.",provenance:"Provenance",
 legend:"Marques : ✓ prêt · ▲ signalé · ≠ l'ancien texte a déjà un problème (diverge de l'allemand ou est dans une autre langue) · h confié à un traducteur · A accepté · E accepté modifié · R renvoyé · touches j/k ou ↑/↓ naviguer, Entrée ouvrir, f/i langue, 1/2/3 décider, Ctrl/Cmd+Entrée enregistrer et suivant",
 theme:"Thème",auto:"auto",light:"clair",dark:"sombre",
 reasons:["","Nombre erroné","Modification du texte allemand non appliquée","Contenu perdu","Allemand non traduit","Terminologie","Formulation","Autre"],
 tabAudit:"Audit du registre",tabDrafts:"Brouillons",codeOnly:"Prêt signifie : vérifié par le code, pas par une personne.",
 triage:"Constats",chk1:"1 point à vérifier",chkN:"{n} points à vérifier",fine:"{n} probablement sans problème",pf:"probablement sans problème",
 rT1:"T1 vocabulaire",rT2:"T2 verbe modal",rT3:"T3 nombres",rT4:"T4 sigle",
 rdT1:"T1 vocabulaire : un « mot inconnu » qui est un mot bien formé de la langue cible (lettres de la langue cible seulement, au moins 4, pas de suite de lettres allemande comme sch/ck/tz/-ung/-keit/-lich, ni mot du texte allemand, ni mêmes 8 premières lettres, ni, avec majuscule, mêmes 4 premières lettres qu'un mot allemand du texte, sauf s'il figure déjà dans l'ancien texte).",
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
 aLead:"Contradictions qui existent déjà entre les textes allemand, français et italien de la LS en vigueur (version du {d}), trouvées par le code avant tout brouillon. Les divergences connues, attestées dans les textes, sont la preuve du problème.",
 aKnownHead:"Divergences connues, attestées dans les textes : {k} sur {n} trouvées",aOtherHead:"Autres constats de l'audit",
 aLim:"Limitation",aKind:"Type",aOdd:"Diverge",aRight:"Quelle langue a raison ?",aAction:"Mesure · remarque",aNote:"Remarque",aSug:"proposition de l'audit",
 aNoSnip:"pas d'extrait dans le fichier d'audit",aSnapSrc:"extrait de la version de la LS, repéré par position et nombres communs",
 kinds:{number:"nombre",unit:"unité",language:"langue",editorial:"rédactionnel"},aUnclear:"pas clair",acts:{"Berichtigung":"Berichtigung (rectification)","GÄL":"GÄL","none":"aucune","unclear":"pas clair"},
 aShow:"Afficher",aKnownF:"Connues",aAllF:"Tous",aOpenF:"Ouverts",aDecF:"Décidés",aKindF:"Type",aShown:"constats affichés",
 aSnap:"Version de la LS",aChecked:"Limitations contrôlées",aFindings:"Constats",aOnLims:"sur {n} limitations",aKnown:"Divergences connues trouvées",aReal:"Réels au contrôle à l'aveugle (nombres)",
 aHeld:"Moitié réservée à l'évaluation",aCalls:"Appels au modèle",aCsv:"Exporter CSV",aNone:"Aucun constat ne correspond à ces filtres.",aNoFile:"Pas de fichier d'audit dans cette version.",
 aLegend:"Marques : K divergence connue, attestée dans les textes · D décidé · cadre rouge = valeur contradictoire · souligné = autre nombre · barre rouge = la langue qui diffère des deux autres (pas forcément la fausse). Décisions : quelle langue dit la bonne condition, et la mesure (Berichtigung, GÄL, aucune).",
 aExpl:"expliqué par {x}",aFix:"coquille probable : « {a} » → « {b} »",aSince:"dans la LS depuis le {d} ({n} versions)",aFoundL:"texte en {F}",oddLbl:"diverge",real:"réels",of:"sur"},
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
 rdT1:"T1 vocabolario: una «parola sconosciuta» che è una parola ben formata della lingua d'arrivo (solo lettere della lingua d'arrivo, almeno 4, nessuna sequenza tedesca come sch/ck/tz/-ung/-keit/-lich, né parola del testo tedesco, né stesse prime 8 lettere, né, se maiuscola, stesse prime 4 lettere di una parola tedesca del testo, salvo che sia già nel vecchio testo).",
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
 aLead:"Contraddizioni già presenti tra i testi tedesco, francese e italiano dell'ES in vigore (versione del {d}), trovate dal codice prima di qualsiasi bozza. Le divergenze note, confermate nei testi, sono la prova del problema.",
 aKnownHead:"Divergenze note, confermate nei testi: {k} su {n} trovate",aOtherHead:"Altri rilievi della verifica",
 aLim:"Limitazione",aKind:"Tipo",aOdd:"Diverge",aRight:"Quale lingua è giusta?",aAction:"Misura · nota",aNote:"Nota",aSug:"proposta della verifica",
 aNoSnip:"nessun estratto nel file di verifica",aSnapSrc:"estratto dalla versione dell'ES, individuato per posizione e numeri comuni",
 kinds:{number:"numero",unit:"unità",language:"lingua",editorial:"redazionale"},aUnclear:"non chiaro",acts:{"Berichtigung":"Berichtigung (rettifica)","GÄL":"GÄL","none":"nessuna","unclear":"non chiaro"},
 aShow:"Mostra",aKnownF:"Note",aAllF:"Tutte",aOpenF:"Aperte",aDecF:"Decise",aKindF:"Tipo",aShown:"rilievi mostrati",
 aSnap:"Versione dell'ES",aChecked:"Limitazioni controllate",aFindings:"Rilievi",aOnLims:"su {n} limitazioni",aKnown:"Divergenze note trovate",aReal:"Reali al controllo alla cieca (numeri)",
 aHeld:"Metà tenuta da parte",aCalls:"Chiamate al modello",aCsv:"Esporta CSV",aNone:"Nessun rilievo corrisponde a questi filtri.",aNoFile:"Nessun file di verifica in questa versione.",
 aLegend:"Segni: K divergenza nota, confermata nei testi · D decisa · riquadro rosso = valore in contraddizione · sottolineato = altro numero · barra rossa = la lingua che differisce dalle altre due (non per forza quella sbagliata). Decisioni: quale lingua indica la condizione giusta, e la misura (Berichtigung, GÄL, nessuna).",
 aExpl:"spiegato da {x}",aFix:"refuso probabile: «{a}» → «{b}»",aSince:"nell'ES dal {d} ({n} versioni)",aFoundL:"testo in {F}",oddLbl:"diverge",real:"reali",of:"su"}};
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
 startOld:"Vom bisherigen Text ausgehen",startOldT:"Ersetzt den bearbeitbaren Entwurf durch den bisherigen Text mit den vom Code angewendeten Zahländerungen ({n}). «Entwurf wiederherstellen» macht es rückgängig.",startOldDone:"Bisheriger Text mit {n} Zahländerungen des Codes – jetzt bearbeiten.",startOldDone1:"Bisheriger Text mit 1 Zahländerung des Codes – jetzt bearbeiten.",
 xlf12:"XLIFF 1.2 exportieren",
 acts:{exofficio:"Von Amtes wegen in der nächsten Publikation berichtigen",holder:"Mit der Zulassungsinhaberin in der dreijährlichen Überprüfung aufnehmen",langsvc:"An den Sprachdienst",none:"Keine Massnahme (gleichwertige Formulierung)",unclear:"Unklar"},
 rev:"Prüfende Person",revPh:"Name (wird mit jedem Entscheid gespeichert)",decOn:"entschieden am {d} von {n}",decOnAnon:"entschieden am {d}",earlier:"in einer früheren Prüfung (Stand {s})",
 eqHead:"Wahrscheinlich gleichwertige Formulierung ({n})",eqWhy:"Grund",eqShow:"anzeigen",eqHide:"einklappen",
 kinds:{number:"Zahl",unit:"Einheit",language:"Sprache",editorial:"Redaktionell",terminology:"Terminologie"},termOld:"bisher",termNew:"vom BAG korrigiert zu",termWhere:"bereits korrigiert in: {x}",
 aLegend:"Zeichen: K bekannte Abweichung, im Text belegt · D entschieden · rot umrahmt = widersprüchlicher Wert · unterstrichen = weitere Zahl · roter Balken = die Sprache, die von den beiden anderen abweicht (nicht unbedingt die falsche). Entscheide: welche Sprache die richtige Bedingung nennt, und die Massnahme (von Amtes wegen berichtigen, in der dreijährlichen Überprüfung mit der Zulassungsinhaberin aufnehmen, Sprachdienst, keine, unklar). Ein Gesuch um Änderung der Limitierung (GÄL) stellt die Zulassungsinhaberin, nicht das BAG. Entscheide gelten pro Befund (Limitierung, Art, Sprache, Werte) und bleiben in der nächsten Prüfung erhalten."},
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
 startOld:"Start from the old text",startOldT:"Replaces the editable draft with the old text plus the number changes code applied ({n}). “Reset to draft” undoes it.",startOldDone:"Old text with {n} number changes applied by code – edit it now.",startOldDone1:"Old text with 1 number change applied by code – edit it now.",
 xlf12:"Export XLIFF 1.2",
 acts:{exofficio:"Correct ex officio in the next publication",holder:"Raise with the holder in the triennial review",langsvc:"Send to the language service",none:"No action (equivalent wording)",unclear:"Unclear"},
 rev:"Reviewer",revPh:"Name (stored with each decision)",decOn:"decided on {d} by {n}",decOnAnon:"decided on {d}",earlier:"in an earlier audit (snapshot {s})",
 eqHead:"Probably equivalent wording ({n})",eqWhy:"Reason",eqShow:"show",eqHide:"collapse",
 kinds:{number:"number",unit:"unit",language:"language",editorial:"editorial",terminology:"terminology"},termOld:"old",termNew:"corrected by BAG to",termWhere:"already corrected in: {x}",
 aLegend:"Marks: K known divergence, confirmed in the texts · D decided · red box = conflicting value · underlined = other number · red bar = the language that differs from the other two (not necessarily the wrong one). Decisions: which language states the right condition, and the action (correct ex officio, raise with the holder in the triennial review, language service, none, unclear). An application to change a limitation (GÄL) is filed by the holder, not by BAG. Decisions belong to a finding (limitation, kind, language, values) and carry over to the next audit."},
fr:{tb:{project:"Projet",drawing:"Dessin",sheet:"Feuille",rev:"Rév.",date:"Date (version LS)",freeze:"Gel",model:"Modèle",run:"Série",checked:"Contrôlé par",checkedV:"contrôles gelés"},lfine:"signalé – tous les constats probablement sans problème",lcheck:"signalé – à vérifier",fCheck:"À vérifier",fFine:"Probablement sans problème",
 triSplit:"Tri des signalés (affichage seulement)",triSplitV:"{c} à vérifier · {f} dont tous les constats sont probablement sans problème",
 rT5:"T5 nombres hors du passage",rT6:"T6 orthographe",rT7:"T7 négation",rT8:"T8 mêmes valeurs",
 rdT5:"T5 nombres hors du passage modifié : hors du passage modifié, le brouillon ne change que des nombres, exactement les valeurs que la modification du texte allemand remplace (Ocrevus 944.61 → 731.07).",
 rdT6:"T6 orthographe : la modification du texte allemand non reprise n'est qu'orthographique (umlaut/ß, trait d'union comme Zeitpunkt → Zeit-punkt, majuscules, ponctuation) ou une terminaison flexionnelle (bedürfen → bedarf, erste → erst).",
 rdT7:"T7 négation : comptée comme un lecteur la compte (« nicht- » préfixe comme dans nicht-kleinzellig ne compte pas, « ne … pas » compte une fois, « personne » nom ne compte pas), le brouillon change le nombre de négations exactement comme l'allemand.",
 rdT8:"T8 mêmes valeurs : les deux côtés ajoutent et retirent les mêmes valeurs, seul le nombre d'occurrences diffère (Kyprolis : 20481 deux fois en allemand, une fois dans le brouillon).",
 legend:"Marques : ✓ prêt · ~ signalé, tous les constats probablement sans problème · ▲ signalé, à vérifier · ≠ l'ancien texte a déjà un problème (diverge de l'allemand, est dans une autre langue ou emploie un terme que l'OFSP a corrigé ailleurs) · h confié à un traducteur · A accepté · E accepté modifié · R renvoyé · touches j/k ou ↑/↓ naviguer, Entrée ouvrir, f/i langue, 1/2/3 décider, Ctrl/Cmd+Entrée enregistrer et suivant",
 famAll:"Accepter tous les brouillons prêts de cette famille ({n})",famAsk:"Accepter tels quels {n} brouillons prêts encore ouverts ({fr} FR, {it} IT) de la famille « {f} » ? Ceux déjà décidés, modifiés ou avec un avis sur l'ancien texte restent ouverts.",
 famYes:"Confirmer l'acceptation",famNo:"Annuler",famDone:"{n} brouillons prêts acceptés.",famNone:"Aucun brouillon prêt ouvert dans cette famille.",famOf:"Famille",famFilter:"afficher seulement cette famille",famChanges:"{n} modifications",
 startOld:"Partir de l'ancien texte",startOldT:"Remplace le brouillon modifiable par l'ancien texte avec les changements de nombres appliqués par le code ({n}). « Rétablir le brouillon » annule.",startOldDone:"Ancien texte avec {n} changements de nombres faits par le code : à modifier maintenant.",startOldDone1:"Ancien texte avec 1 changement de nombre fait par le code : à modifier maintenant.",
 xlf12:"Exporter XLIFF 1.2",
 acts:{exofficio:"Corriger d'office dans la prochaine publication",holder:"Aborder avec le titulaire lors du réexamen triennal",langsvc:"Transmettre au service linguistique",none:"Aucune mesure (formulation équivalente)",unclear:"Pas clair"},
 rev:"Réviseur ou réviseuse",revPh:"Nom (enregistré avec chaque décision)",decOn:"décidé le {d} par {n}",decOnAnon:"décidé le {d}",earlier:"lors d'un audit antérieur (version du {s})",
 eqHead:"Formulation probablement équivalente ({n})",eqWhy:"Motif",eqShow:"afficher",eqHide:"replier",
 kinds:{number:"nombre",unit:"unité",language:"langue",editorial:"rédactionnel",terminology:"terminologie"},termOld:"ancien",termNew:"corrigé par l'OFSP en",termWhere:"déjà corrigé dans : {x}",
 aLegend:"Marques : K divergence connue, attestée dans les textes · D décidé · cadre rouge = valeur contradictoire · souligné = autre nombre · barre rouge = la langue qui diffère des deux autres (pas forcément la fausse). Décisions : quelle langue dit la bonne condition, et la mesure (corriger d'office, aborder avec le titulaire lors du réexamen triennal, service linguistique, aucune, pas clair). La demande de modification de la limitation (GÄL) est déposée par le titulaire, pas par l'OFSP. Les décisions valent par constat (limitation, type, langue, valeurs) et sont reprises au prochain audit."},
it:{tb:{project:"Progetto",drawing:"Disegno",sheet:"Foglio",rev:"Rev.",date:"Data (versione ES)",freeze:"Congelamento",model:"Modello",run:"Serie",checked:"Controllato da",checkedV:"controlli congelati"},lfine:"segnalata – tutti i rilievi probabilmente in ordine",lcheck:"segnalata – da verificare",fCheck:"Da verificare",fFine:"Probabilmente in ordine",
 triSplit:"Smistamento delle segnalate (solo visualizzazione)",triSplitV:"{c} da verificare · {f} con tutti i rilievi probabilmente in ordine",
 rT5:"T5 numeri fuori dal passo",rT6:"T6 ortografia",rT7:"T7 negazione",rT8:"T8 stessi valori",
 rdT5:"T5 numeri fuori dal passo modificato: fuori dal passo modificato la bozza cambia solo numeri, esattamente i valori che la modifica tedesca sostituisce (Ocrevus 944.61 → 731.07).",
 rdT6:"T6 ortografia: la modifica tedesca non ripresa è solo ortografica (umlaut/ß, trattino come Zeitpunkt → Zeit-punkt, maiuscole, punteggiatura) o una desinenza flessiva (bedürfen → bedarf, erste → erst).",
 rdT7:"T7 negazione: contata come la conta un lettore («nicht-» prefisso come in nicht-kleinzellig non conta, il francese «ne … pas» conta una volta, «personne» sostantivo non conta), la bozza cambia il numero di negazioni esattamente come il tedesco.",
 rdT8:"T8 stessi valori: entrambe le parti aggiungono e tolgono gli stessi valori, cambia solo quante volte un valore compare (Kyprolis: 20481 due volte nel tedesco, una volta nella bozza).",
 legend:"Segni: ✓ pronta · ~ segnalata, tutti i rilievi probabilmente in ordine · ▲ segnalata, da verificare · ≠ il vecchio testo ha già un problema (diverge dal tedesco, è in un'altra lingua o usa un termine che l'UFSP ha corretto altrove) · h affidata a un traduttore · A accettata · E accettata modificata · R rinviata · tasti j/k o ↑/↓ spostarsi, Invio aprire, f/i lingua, 1/2/3 decidere, Ctrl/Cmd+Invio salva e avanti",
 famAll:"Accetta tutte le bozze pronte di questa famiglia ({n})",famAsk:"Accettare così come sono {n} bozze pronte ancora aperte ({fr} FR, {it} IT) della famiglia «{f}»? Quelle già decise, modificate o con un avviso sul vecchio testo restano aperte.",
 famYes:"Conferma accettazione",famNo:"Annulla",famDone:"{n} bozze pronte accettate.",famNone:"Nessuna bozza pronta aperta in questa famiglia.",famOf:"Famiglia",famFilter:"mostra solo questa famiglia",famChanges:"{n} modifiche",
 startOld:"Parti dal vecchio testo",startOldT:"Sostituisce la bozza modificabile con il vecchio testo e le modifiche dei numeri applicate dal codice ({n}). «Ripristina la bozza» annulla.",startOldDone:"Vecchio testo con {n} modifiche dei numeri fatte dal codice: ora da modificare.",startOldDone1:"Vecchio testo con 1 modifica dei numeri fatta dal codice: ora da modificare.",
 xlf12:"Esporta XLIFF 1.2",
 acts:{exofficio:"Correggere d'ufficio nella prossima pubblicazione",holder:"Discutere con il titolare nel riesame triennale",langsvc:"Inviare al servizio linguistico",none:"Nessuna misura (formulazione equivalente)",unclear:"Non chiaro"},
 rev:"Revisore o revisora",revPh:"Nome (salvato con ogni decisione)",decOn:"deciso il {d} da {n}",decOnAnon:"deciso il {d}",earlier:"in una verifica precedente (versione {s})",
 eqHead:"Formulazione probabilmente equivalente ({n})",eqWhy:"Motivo",eqShow:"mostra",eqHide:"richiudi",
 kinds:{number:"numero",unit:"unità",language:"lingua",editorial:"redazionale",terminology:"terminologia"},termOld:"vecchio",termNew:"corretto dall'UFSP in",termWhere:"già corretto in: {x}",
 aLegend:"Segni: K divergenza nota, confermata nei testi · D decisa · riquadro rosso = valore in contraddizione · sottolineato = altro numero · barra rossa = la lingua che differisce dalle altre due (non per forza quella sbagliata). Decisioni: quale lingua indica la condizione giusta, e la misura (correggere d'ufficio, discutere con il titolare nel riesame triennale, servizio linguistico, nessuna, non chiaro). La domanda di modifica della limitazione (GÄL) è presentata dal titolare, non dall'UFSP. Le decisioni valgono per rilievo (limitazione, tipo, lingua, valori) e restano alla verifica successiva."}};
Object.keys(TX2).forEach(function(L){Object.keys(TX2[L]).forEach(function(k){TX[L][k]=TX2[L][k]})});
// round-4 strings: the two views as one system, lane, explanation language, legends, one decisions export, 27 + 11
var TX3={
de:{sub:"Prüfregister · Apertus entwirft, Code prüft",divergent:"Entwürfe, deren bisheriger Text schon ein Problem hat",
 tb:{project:"Projekt",drawing:"Zeichnung",sheet:"Blatt",rev:"Rev.",date:"Datum (SL-Stand)",lane:"Spur",model:"Modell",run:"Lauf",checked:"Geprüft von",checkedV:"eingefrorene Prüfungen"},
 lane70:"weniger Korrekturen: Apertus 70B, wie von Public AI bereitgestellt (optionale Spur; Identität nicht überprüft)",lane8:"Standard: 8B auf CPU, ohne Netz",laneDef:"Standardspur: 8B auf CPU, ohne Netz",drawingBy:"{l}, {n} Entwürfe von Apertus {m}",
 t1h:"Entwürfe",t1s:"Apertus entwirft, Code prüft",t1f:"{n} Entwürfe · {r} bereit · {f} markiert",
 t1t:"Apertus {m} schreibt für {c} deutsche Änderungen nur die Formulierung des französischen und italienischen Texts um; jede Zahl setzt der Code ein. Eingefrorene Prüfungen kennzeichnen jeden Entwurf als «bereit» oder «markiert» und sagen warum, in der Sprache der prüfenden Person.",
 t2h:"Registerprüfung",t2s:"nur Code, kein Modell",t2f:"{a} Befunde + {t} Terminologie-Hinweise",
 t2t:"Der Code liest alle {n} Limitierungen auf DE/FR/IT (Stand {d}) und sucht Stellen, an denen die Sprachen schon heute auseinandergehen: {k} von {o} bekannten Abweichungen gefunden.",go:"öffnen →",
 aFindingsV:"{a} ({b}) + {t} Terminologie-Hinweise",aConf:"Bei Blindprüfung bestätigt",aConfV:"{r} von {a} Befunden ({k} bekannte + {x} neue) · {tr} von {t} Hinweisen",
 aTermHead:"Terminologie-Hinweise: vom BAG anderswo korrigierter Begriff ({n})",aAllN:"Alle ({a} + {t})",progA:"{x}/{a} + {y}/{t} entschieden",
 expl:"Erläuterung",allPass:"Alle Prüfungen bestanden.",moreN:"+ {n} weitere im Prüfdetail",chkDetail:"Prüfdetail: alle {n} Prüfungen, Rohausgabe mit internen Codes",
 exportDec:"Entscheide exportieren (JSON)",where:"Entscheide bleiben in diesem Browser, bis Sie sie exportieren. Massgeblich sind das ePL und der XLIFF-Rücklauf, nicht diese Seite.",
 keyReg:[["✓","bereit"],["~","markiert, alle Befunde wahrscheinlich in Ordnung"],["▲","markiert, zu prüfen"],["≠","bisheriger Text hat schon ein Problem"],["h","an Übersetzung übergeben"],["AER","übernommen / bearbeitet / zurückgewiesen"]],
 keyNum:["vom Code aus dem Deutschen gesetzte Zahl (Platzhalter A)","orange umrahmt: Zahl vom Modell geschrieben, prüfen","neu","entfernt"],
 keyAud:[["✓","entschieden"],["v2","widersprüchlicher Wert"],["v1","weitere Zahl"],["bar","Sprache, die von den beiden anderen abweicht"]]},
en:{sub:"Review register · Apertus drafts, code checks",divergent:"Drafts whose old text already has a problem",
 tb:{project:"Project",drawing:"Drawing",sheet:"Sheet",rev:"Rev",date:"Date (SL snapshot)",lane:"Lane",model:"Model",run:"Run",checked:"Checked by",checkedV:"frozen checks"},
 lane70:"fewer edits: Apertus 70B as Public AI served it (optional lane; identity not verified)",lane8:"default: 8B on CPU, air-gapped",laneDef:"default lane: 8B on CPU, air-gapped",drawingBy:"{l}, {n} drafts by Apertus {m}",
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
 keyAud:[["✓","decided"],["v2","conflicting value"],["v1","other number"],["bar","language that differs from the other two"]]},
fr:{sub:"Registre de révision · Apertus rédige, le code contrôle",divergent:"Brouillons dont l'ancien texte a déjà un problème",
 tb:{project:"Projet",drawing:"Dessin",sheet:"Feuille",rev:"Rév.",date:"Date (version LS)",lane:"Variante",model:"Modèle",run:"Série",checked:"Contrôlé par",checkedV:"contrôles gelés"},
 lane70:"moins de corrections : Apertus 70B tel que servi par Public AI (variante optionnelle ; identité non vérifiée)",lane8:"par défaut : 8B sur CPU, hors réseau",laneDef:"variante par défaut : 8B sur CPU, hors réseau",drawingBy:"{l}, {n} brouillons d'Apertus {m}",
 t1h:"Brouillons",t1s:"Apertus rédige, le code contrôle",t1f:"{n} brouillons · {r} prêts · {f} signalés",
 t1t:"Pour {c} modifications du texte allemand, Apertus {m} ne réécrit que la formulation française et italienne ; le code écrit chaque nombre. Des contrôles gelés marquent chaque brouillon prêt ou signalé et disent pourquoi, dans la langue du réviseur.",
 t2h:"Audit du registre",t2s:"code seul, sans modèle",t2f:"{a} constats + {t} avis de terminologie",
 t2t:"Le code lit les {n} limitations en DE/FR/IT (version du {d}) et cherche les endroits où les langues divergent déjà : {k} des {o} divergences connues trouvées.",go:"ouvrir →",
 aFindingsV:"{a} ({b}) + {t} avis de terminologie",aConf:"Confirmés au contrôle à l'aveugle",aConfV:"{r} des {a} constats ({k} connus + {x} nouveaux) · {tr} des {t} avis",
 aTermHead:"Avis de terminologie : terme corrigé ailleurs par l'OFSP ({n})",aAllN:"Tous ({a} + {t})",progA:"{x}/{a} + {y}/{t} décidés",
 expl:"explication",allPass:"Tous les contrôles sont passés.",moreN:"+ {n} autres dans le détail des contrôles",moreN1:"+ 1 autre dans le détail des contrôles",chkDetail:"Détail des contrôles : les {n} contrôles, sortie brute avec codes internes",
 exportDec:"Exporter les décisions (JSON)",where:"Les décisions restent dans ce navigateur jusqu'à leur export. Le système de référence est l'ePL et l'aller-retour XLIFF, pas cette page.",
 keyReg:[["✓","prêt"],["~","signalé, tous les constats probablement sans problème"],["▲","signalé, à vérifier"],["≠","l'ancien texte a déjà un problème"],["h","confié à un traducteur"],["AER","accepté / modifié / renvoyé"]],
 keyNum:["nombre placé par le code à partir de l'allemand (emplacement A)","cadre orange : nombre écrit par le modèle, à vérifier","nouveau","supprimé"],
 keyAud:[["✓","décidé"],["v2","valeur contradictoire"],["v1","autre nombre"],["bar","langue qui diffère des deux autres"]]},
it:{sub:"Registro di revisione · Apertus redige, il codice controlla",divergent:"Bozze il cui vecchio testo ha già un problema",
 tb:{project:"Progetto",drawing:"Disegno",sheet:"Foglio",rev:"Rev.",date:"Data (versione ES)",lane:"Variante",model:"Modello",run:"Serie",checked:"Controllato da",checkedV:"controlli congelati"},
 lane70:"meno correzioni: Apertus 70B come servito da Public AI (variante opzionale; identità non verificata)",lane8:"predefinita: 8B su CPU, senza rete",laneDef:"variante predefinita: 8B su CPU, senza rete",drawingBy:"{l}, {n} bozze di Apertus {m}",
 t1h:"Bozze",t1s:"Apertus redige, il codice controlla",t1f:"{n} bozze · {r} pronte · {f} segnalate",
 t1t:"Per {c} modifiche tedesche, Apertus {m} riscrive solo la formulazione francese e italiana; ogni numero lo scrive il codice. Controlli congelati segnano ogni bozza come pronta o segnalata e dicono perché, nella lingua di chi rivede.",
 t2h:"Verifica del registro",t2s:"solo codice, nessun modello",t2f:"{a} rilievi + {t} avvisi di terminologia",
 t2t:"Il codice legge tutte le {n} limitazioni in DE/FR/IT (versione del {d}) e cerca i punti in cui le lingue già divergono: trovate {k} delle {o} divergenze note.",go:"apri →",
 aFindingsV:"{a} ({b}) + {t} avvisi di terminologia",aConf:"Confermati al controllo alla cieca",aConfV:"{r} di {a} rilievi ({k} noti + {x} nuovi) · {tr} di {t} avvisi",
 aTermHead:"Avvisi di terminologia: termine corretto altrove dall'UFSP ({n})",aAllN:"Tutti ({a} + {t})",progA:"{x}/{a} + {y}/{t} decisi",
 expl:"spiegazione",allPass:"Tutti i controlli superati.",moreN:"+ {n} altri nel dettaglio dei controlli",moreN1:"+ 1 altro nel dettaglio dei controlli",chkDetail:"Dettaglio dei controlli: tutti i {n} controlli, uscita grezza con codici interni",
 exportDec:"Esporta le decisioni (JSON)",where:"Le decisioni restano in questo browser finché non le esportate. Il sistema di riferimento è l'ePL con il ciclo XLIFF, non questa pagina.",
 keyReg:[["✓","pronta"],["~","segnalata, tutti i rilievi probabilmente in ordine"],["▲","segnalata, da verificare"],["≠","il vecchio testo ha già un problema"],["h","affidata a un traduttore"],["AER","accettata / modificata / rinviata"]],
 keyNum:["numero inserito dal codice a partire dal tedesco (segnaposto A)","riquadro arancione: numero scritto dal modello, da verificare","nuovo","tolto"],
 keyAud:[["✓","decisa"],["v2","valore in contraddizione"],["v1","altro numero"],["bar","lingua che differisce dalle altre due"]]}};
Object.keys(TX3).forEach(function(L){Object.keys(TX3[L]).forEach(function(k){TX[L][k]=TX3[L][k]})});
// round-5 strings: the register audit for the scientific officer (issues, dating, full texts, several actions, filing CSV)
// and the drafts banner (past changes used to test the tool; drafts are for translators)
var TX4={
de:{aLead:"Jede Zeile ist ein Fall: eine Stelle, an der der deutsche, französische und italienische Text einer Limitierung in der SL vom {d} Verschiedenes sagen, vom Code ohne Modell gefunden. Massgebend ist die Fassung, die dem Entscheid des BAG entspricht; welche das ist, weiss die Prüfung nicht – bitte mit dem Entscheiddossier abgleichen. {a} Befunde + {t} Terminologie-Hinweise in {n} Fällen; ein Entscheid zu einem Fall gilt für alle seine Befunde (jeder lässt sich auch einzeln entscheiden).",
 aKnownHead:"Vor dieser Prüfung von unserer früheren Erhebung erfasst: {k} von {n} gefunden",aOtherHead:"Weitere Befunde der Prüfung",
 aTermHead:"Terminologie-Hinweise: vom BAG anderswo korrigierter Begriff ({n} Fälle, {m} Hinweise)",eqHead:"Wahrscheinlich gleichwertige Formulierung ({n})",
 aKnown:"Vor dieser Prüfung erfasst (frühere Erhebung)",aConf:"Von blinden KI-Annotatoren (Claude) bestätigt",aConfV:"{r} von {a} Befunden ({k} früher erfasst + {x} neu) · {tr} von {t} Hinweisen",
 aFindingsV:"{a} ({b}) + {t} Terminologie-Hinweise, in {n} Fällen",t2f:"{a} Befunde + {t} Terminologie-Hinweise · {n} Fälle",
 t2t:"Der Code liest alle {n} Limitierungen auf DE/FR/IT (Stand {d}) und sucht Stellen, an denen die Sprachen schon heute auseinandergehen; er findet {k} der {o} Abweichungen, die unsere frühere Erhebung erfasst hatte.",
 dA:"in allen {n} Ständen seit {d} vorhanden, dem frühesten, den die Prüfung vergleicht (kann älter sein)",dB:"erstmals zwischen {p} und {d} aufgetreten; seither in allen {n} Ständen",dC:"erstmals am {d}; seither in {n} von {m} Ständen",
 newSince:"Neu seit",newAny:"jedem Stand",aRight:"Welche Fassung entspricht dem Entscheid?",rUnclear:"noch unklar",aAction:"Massnahmen · Notiz",
 acts:{fix:"Text berichtigen",langsvc:"An den Sprachdienst",decfile:"Entscheiddossier prüfen",pending:"Schon in einer hängigen Änderung",none:"Keine Massnahme (gleichwertige Formulierung)",falsealarm:"Fehlalarm",
  exofficio:"Von Amtes wegen in der nächsten Publikation berichtigen",holder:"Mit der Zulassungsinhaberin in der dreijährlichen Überprüfung aufnehmen",unclear:"Unklar"},
 ahNo:"Fall",aKind:"Art",aOdd:"Weicht ab",ft:"Volltexte DE · FR · IT",ftN:"{n} Limitierungen",ftNone:"Volltexte nicht in diesem Build",mem:"{n} Befunde in diesem Fall",
 memFollow:"folgt dem Entscheid zum Fall",memOwn:"einzeln entschieden",memSplit:"Einzeln entscheiden",memJoin:"Dem Entscheid zum Fall folgen",appliesAll:"gilt für alle {n} Befunde",someOwn:"{n} einzeln entschieden",
 csvIss:"Fälle exportieren (CSV, für GEVER)",aCsv:"Befunde exportieren (CSV)",yes:"ja",no2:"nein",
 csvHead:["Fall","Befunde","Produkt","Limitierung","Sprachen","Art","Werte","Datierung","Vor dieser Prüfung erfasst","Fassung gemäss Entscheid","Massnahmen","Notiz","Entschieden am","Entschieden von","Prüfung (SL-Stand)","Einzeln entschieden"],
 progA:"{i}/{n} Fälle entschieden ({x}/{a} + {y}/{t} Befunde)",aAllN:"Alle ({n} Fälle)",aKnownF:"Früher erfasst",aShownI:"{n} Fälle angezeigt ({m} Befunde)",aNone:"Kein Fall entspricht diesen Filtern.",
 keyAud:[["✓","entschieden"],["v2","widersprüchlicher Wert"],["v1","weitere Zahl"],["bar","Sprache, die von den beiden anderen abweicht"]],
 grouping:"Befunde bilden einen Fall, wenn sie dieselbe Abweichung (dieselben widersprüchlichen Werte, Einheit, Sprache, denselben Tippfehler oder dasselbe Begriffspaar) im selben Text nennen: in derselben Limitierung, einer Geschwisterlimitierung desselben Produkts oder derselben zitierten Passage; ein Tippfehler, der laut Prüfung eine Zahlabweichung erklärt, gehört zu ihr; ein Terminologie-Hinweis ist ein Fall pro Sprache und Begriffspaar.",
 aLegend:"Zeichen: K vor dieser Prüfung von unserer früheren Erhebung erfasst · D entschieden · rot umrahmt = widersprüchlicher Wert · unterstrichen = weitere Zahl · roter Balken = die Sprache, die von den beiden anderen abweicht (nicht unbedingt die falsche). Fälle: {g} Entscheide: welche Fassung dem Entscheid des BAG entspricht (das weiss die Prüfung nicht) und eine oder mehrere Massnahmen. Ein Entscheid zu einem Fall wird bei jedem seiner Befunde gespeichert (Limitierung, Art, Sprache, Werte) und bleibt in der nächsten Prüfung erhalten.",
 tbA:{rev:"Fälle",lane:"Methode",model:"Verglichen mit",run:"Geprüfte Limitierungen",checked:"Bestätigt durch"},revA:"{n} Fälle · {f} Befunde",laneA:"nur Code, kein Modell",modelA:"{n} SL-Stände, {a} – {b}",checkedA:"blinde KI-Annotatoren (Claude)",drawA:"Registerprüfung DE/FR/IT, SL-Stand {d}",
 dB1:"Diese {c} deutschen Änderungen sind vergangene SL-Änderungen{p}, mit denen Gleichlaut getestet wurde – keine offene Arbeit: Das BAG hat ihr Französisch und Italienisch bereits publiziert. ",
 dB2:"Die Entwürfe sind für die Übersetzung bestimmt (in STAR Transit, über XLIFF); ob ein Entwurf übernommen, bearbeitet oder zurückgewiesen wird, entscheidet die Übersetzerin oder der Übersetzer."},
en:{aLead:"Each row is one issue: a place where the German, French and Italian texts of a limitation say different things in the SL of {d}, found by code without a model. What counts is the version that matches BAG's decision, and the audit cannot tell which one that is: check the decision file. {a} findings + {t} terminology notices in {n} issues; a decision on an issue applies to all its findings (each can still be decided separately).",
 aKnownHead:"Listed before this audit by our earlier census: {k} of {n} found",aOtherHead:"Further findings of the audit",
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
 keyAud:[["✓","decided"],["v2","conflicting value"],["v1","other number"],["bar","language that differs from the other two"]],
 grouping:"findings are one issue when they name the same difference (the same conflicting values, unit, language, typo or term pair) on the same text: the same limitation, a sibling limitation of the same product, or the same quoted passage; a typo the audit says explains a number difference joins it; a terminology notice is one issue per language and term pair.",
 aLegend:"Marks: K listed before this audit by our earlier census · D decided · red box = conflicting value · underlined = other number · red bar = the language that differs from the other two (not necessarily the wrong one). Issues: {g} Decisions: which version matches BAG's decision (the audit cannot know), and one or more actions. A decision on an issue is stored with each of its findings (limitation, kind, language, values) and carries over to the next audit.",
 tbA:{rev:"Issues",lane:"Method",model:"Compared with",run:"Limitations checked",checked:"Confirmed by"},revA:"{n} issues · {f} findings",laneA:"code only, no model",modelA:"{n} SL snapshots, {a} – {b}",checkedA:"blind AI annotators (Claude)",drawA:"Register audit DE/FR/IT, SL of {d}",
 dB1:"These {c} German changes are past SL updates{p} used to test Gleichlaut, not pending work: BAG has already published their French and Italian. ",
 dB2:"The drafts are meant for translators (in STAR Transit, via XLIFF); accepting, editing or sending back a draft is the translator's decision."},
fr:{aLead:"Chaque ligne est un cas : un endroit où les textes allemand, français et italien d'une limitation disent des choses différentes dans la LS du {d}, trouvé par le code, sans modèle. Ce qui compte est la version conforme à la décision de l'OFSP, et l'audit ne peut pas savoir laquelle ; vérifiez-la dans le dossier de décision. {a} constats + {t} avis de terminologie en {n} cas ; une décision sur un cas vaut pour tous ses constats (chacun peut aussi être décidé séparément).",
 aKnownHead:"Recensés avant cet audit par notre inventaire antérieur (vérifiés à la main) : {k} sur {n} trouvés",aOtherHead:"Autres constats de l'audit",
 aTermHead:"Avis de terminologie : terme corrigé ailleurs par l'OFSP ({n} cas, {m} avis)",eqHead:"Formulation probablement équivalente ({n})",
 aKnown:"Recensés avant cet audit (inventaire antérieur)",aConf:"Confirmés par des annotateurs IA à l'aveugle (Claude)",aConfV:"{r} des {a} constats ({k} déjà recensés + {x} nouveaux) · {tr} des {t} avis",
 aFindingsV:"{a} ({b}) + {t} avis de terminologie, en {n} cas",t2f:"{a} constats + {t} avis de terminologie · {n} cas",
 t2t:"Le code lit les {n} limitations en DE/FR/IT (version du {d}) et cherche les endroits où les langues divergent déjà ; il trouve {k} des {o} divergences que notre inventaire antérieur avait recensées.",
 dA:"présent dans les {n} versions depuis le {d}, la plus ancienne que l'audit compare (il peut être plus ancien)",dB:"apparu entre le {p} et le {d} ; présent depuis dans les {n} versions",dC:"vu pour la première fois le {d} ; présent dans {n} des {m} versions depuis",
 newSince:"Nouveau depuis",newAny:"toute version",aRight:"Quelle version correspond à la décision ?",rUnclear:"pas encore clair",aAction:"Mesures · remarque",
 acts:{fix:"Corriger le texte",langsvc:"Transmettre au service linguistique",decfile:"Vérifier le dossier de décision",pending:"Déjà dans une modification en cours",none:"Aucune mesure (formulation équivalente)",falsealarm:"Fausse alerte",
  exofficio:"Corriger d'office dans la prochaine publication",holder:"Aborder avec le titulaire lors du réexamen triennal",unclear:"Pas clair"},
 ahNo:"Cas",aKind:"Type",aOdd:"Diverge",ft:"Textes complets DE · FR · IT",ftN:"{n} limitations",ftNone:"textes complets absents de cette version",mem:"{n} constats dans ce cas",
 memFollow:"suit la décision du cas",memOwn:"décidé séparément",memSplit:"Décider séparément",memJoin:"Suivre la décision du cas",appliesAll:"vaut pour les {n} constats",someOwn:"{n} décidés séparément",someOwn1:"1 décidé séparément",
 csvIss:"Exporter les cas (CSV, pour GEVER)",aCsv:"Exporter les constats (CSV)",yes:"oui",no2:"non",
 csvHead:["Cas","Constats","Produit","Limitation","Langues","Type","Valeurs","Datation","Recensé avant cet audit","Version conforme à la décision","Mesures","Remarque","Décidé le","Décidé par","Audit (version LS)","Décidé séparément"],
 progA:"{i}/{n} cas décidés ({x}/{a} + {y}/{t} constats)",aAllN:"Tous ({n} cas)",aKnownF:"Déjà recensés",aShownI:"{n} cas affichés ({m} constats)",aNone:"Aucun cas ne correspond à ces filtres.",
 keyAud:[["✓","décidé"],["v2","valeur contradictoire"],["v1","autre nombre"],["bar","langue qui diffère des deux autres"]],
 grouping:"des constats forment un cas quand ils nomment la même divergence (mêmes valeurs contradictoires, unité, langue, coquille ou paire de termes) dans le même texte : la même limitation, une limitation sœur du même produit ou le même passage cité ; une coquille qui, selon l'audit, explique une divergence de nombre la rejoint ; un avis de terminologie forme un cas par langue et paire de termes.",
 aLegend:"Marques : K recensé avant cet audit par notre inventaire antérieur · D décidé · cadre rouge = valeur contradictoire · souligné = autre nombre · barre rouge = la langue qui diffère des deux autres (pas forcément la fausse). Cas : {g} Décisions : quelle version correspond à la décision de l'OFSP (l'audit ne peut pas le savoir), et une ou plusieurs mesures. Une décision sur un cas est enregistrée avec chacun de ses constats (limitation, type, langue, valeurs) et reprise au prochain audit.",
 tbA:{rev:"Cas",lane:"Méthode",model:"Comparé à",run:"Limitations contrôlées",checked:"Confirmé par"},revA:"{n} cas · {f} constats",laneA:"code seul, sans modèle",modelA:"{n} versions de la LS, {a} – {b}",checkedA:"annotateurs IA à l'aveugle (Claude)",drawA:"Audit du registre DE/FR/IT, LS du {d}",
 dB1:"Ces {c} modifications du texte allemand sont tirées de l'historique de la LS{p} et servent à tester Gleichlaut ; ce n'est pas du travail en attente : l'OFSP en a déjà publié le français et l'italien. ",
 dB2:"Les brouillons sont destinés aux traducteurs (dans STAR Transit, via XLIFF) ; accepter, modifier ou renvoyer un brouillon est la décision du traducteur ou de la traductrice."},
it:{aLead:"Ogni riga è un caso: un punto in cui i testi tedesco, francese e italiano di una limitazione dicono cose diverse nell'ES del {d}, trovato dal codice, senza modello. Conta la versione conforme alla decisione dell'UFSP, e la verifica non può sapere quale sia; controllarla nel dossier della decisione. {a} rilievi + {t} avvisi di terminologia in {n} casi; una decisione su un caso vale per tutti i suoi rilievi (ognuno può anche essere deciso separatamente).",
 aKnownHead:"Già rilevate dal nostro censimento precedente: trovate {k} su {n}",aOtherHead:"Altri rilievi della verifica",
 aTermHead:"Avvisi di terminologia: termine corretto altrove dall'UFSP ({n} casi, {m} avvisi)",eqHead:"Formulazione probabilmente equivalente ({n})",
 aKnown:"Già rilevato dal nostro censimento precedente",aConf:"Confermati da annotatori IA alla cieca (Claude)",aConfV:"{r} di {a} rilievi ({k} già censiti + {x} nuovi) · {tr} di {t} avvisi",
 aFindingsV:"{a} ({b}) + {t} avvisi di terminologia, in {n} casi",t2f:"{a} rilievi + {t} avvisi di terminologia · {n} casi",
 t2t:"Il codice legge tutte le {n} limitazioni in DE/FR/IT (versione del {d}) e cerca i punti in cui le lingue già divergono; trova {k} delle {o} divergenze rilevate dal nostro censimento precedente.",
 dA:"presente in tutte le {n} versioni dal {d}, la più vecchia che la verifica confronta (può essere più vecchio)",dB:"comparso tra il {p} e il {d}; da allora presente in tutte le {n} versioni",dC:"visto per la prima volta il {d}; presente in {n} delle {m} versioni da allora",
 newSince:"Nuovo dal",newAny:"qualsiasi versione",aRight:"Quale versione corrisponde alla decisione?",rUnclear:"non ancora chiaro",aAction:"Misure · nota",
 acts:{fix:"Correggere il testo",langsvc:"Inviare al servizio linguistico",decfile:"Verificare il dossier della decisione",pending:"Già oggetto di una modifica in corso",none:"Nessuna misura (formulazione equivalente)",falsealarm:"Falso allarme",
  exofficio:"Correggere d'ufficio nella prossima pubblicazione",holder:"Discutere con il titolare nel riesame triennale",unclear:"Non chiaro"},
 ahNo:"Caso",aKind:"Tipo",aOdd:"Diverge",ft:"Testi completi DE · FR · IT",ftN:"{n} limitazioni",ftNone:"testi completi assenti in questa versione",mem:"{n} rilievi in questo caso",
 memFollow:"segue la decisione del caso",memOwn:"deciso separatamente",memSplit:"Decidere separatamente",memJoin:"Seguire la decisione del caso",appliesAll:"vale per tutti i {n} rilievi",someOwn:"{n} decisi separatamente",someOwn1:"1 deciso separatamente",
 csvIss:"Esporta i casi (CSV, per GEVER)",aCsv:"Esporta i rilievi (CSV)",yes:"sì",no2:"no",
 csvHead:["Caso","Rilievi","Prodotto","Limitazione","Lingue","Tipo","Valori","Datazione","Già rilevato in precedenza","Versione conforme alla decisione","Misure","Nota","Deciso il","Deciso da","Verifica (versione ES)","Deciso separatamente"],
 progA:"{i}/{n} casi decisi ({x}/{a} + {y}/{t} rilievi)",aAllN:"Tutti ({n} casi)",aKnownF:"Già rilevati",aShownI:"{n} casi mostrati ({m} rilievi)",aNone:"Nessun caso corrisponde a questi filtri.",
 keyAud:[["✓","deciso"],["v2","valore in contraddizione"],["v1","altro numero"],["bar","lingua che differisce dalle altre due"]],
 grouping:"i rilievi formano un caso quando indicano la stessa divergenza (stessi valori in contraddizione, unità, lingua, refuso o coppia di termini) nello stesso testo: la stessa limitazione, una limitazione sorella dello stesso prodotto o lo stesso passo citato; un refuso che secondo la verifica spiega una divergenza di numero vi si aggiunge; un avviso di terminologia è un caso per lingua e coppia di termini.",
 aLegend:"Segni: K già rilevato dal nostro censimento precedente · D deciso · riquadro rosso = valore in contraddizione · sottolineato = altro numero · barra rossa = la lingua che differisce dalle altre due (non per forza quella sbagliata). Casi: {g} Decisioni: quale versione corrisponde alla decisione dell'UFSP (la verifica non può saperlo), e una o più misure. Una decisione su un caso è salvata con ciascuno dei suoi rilievi (limitazione, tipo, lingua, valori) e resta alla verifica successiva.",
 tbA:{rev:"Casi",lane:"Metodo",model:"Confrontato con",run:"Limitazioni controllate",checked:"Confermato da"},revA:"{n} casi · {f} rilievi",laneA:"solo codice, nessun modello",modelA:"{n} versioni dell'ES, {a} – {b}",checkedA:"annotatori IA alla cieca (Claude)",drawA:"Verifica del registro DE/FR/IT, ES del {d}",
 dB1:"Queste {c} modifiche tedesche sono modifiche passate dell'ES{p}, usate per testare Gleichlaut, non lavoro in sospeso: l'UFSP ha già pubblicato il loro francese e italiano. ",
 dB2:"Le bozze sono destinate ai traduttori (in STAR Transit, tramite XLIFF); accettare, modificare o rinviare una bozza è decisione del traduttore o della traduttrice."}};
Object.keys(TX4).forEach(function(L){Object.keys(TX4[L]).forEach(function(k){TX[L][k]=TX4[L][k]})});
// redesign (10 Oct 2026): one bar, a context line, list + case in both views, statistics in the footer
var TX5={
de:{gCond:"Ändert eine Bedingung",gEdit:"Tippfehler und Redaktion",gTerm:"Terminologie",ctxAud:"Der Code vergleicht alle {n} Limitierungen auf DE/FR/IT, ohne Modell. Zu entscheiden ist pro Fall: welcher Text ist falsch, und was geschieht.",export:"Export",ctxD:"Die optionale 70B-Spur, wie von Public AI bereitgestellt (Identität nicht überprüft); die Standardspur (8B auf CPU) entwirft dieselben Änderungen. Markiert heisst: eine Person prüft – die Prüfungen sind darauf ausgelegt, nichts zu übersehen.",whereS:"Entscheide bleiben in diesem Browser, bis sie exportiert werden.",backList:"Liste",slotsT:"Platzhalter zeigen",famChange1:"1 Änderung",aThen:"Weiter",aOr:"Oder",aboutH:"Über dieses Register",aBind:"Massgebend ist die Fassung, die dem Entscheid des BAG entspricht; welche das ist, weiss die Prüfung nicht.",
 aKnownHeadS:"Von unserer früheren Erhebung erfasst · {k} von {n} gefunden",aTermHeadS:"Terminologie · {n}",aWhat:"Was abweicht",aDating:"Seit wann",aNote2:"Hinweis",aTermL:"Begriff",
 aTexts:"Die Texte",aActL:"Massnahmen und Notiz",saveNextI:"Nächster Fall",keysA:"j/k oder ↑/↓ wechseln · Ctrl/Cmd+Enter speichern und weiter",lane:"Spur",laneM:"Methode",comparedW:"Verglichen mit"},
en:{gCond:"Changes a condition",gEdit:"Typos and editorial",gTerm:"Terminology",ctxAud:"Code compares all {n} limitations in DE/FR/IT, no model. Each issue needs one decision: which text is wrong, and what happens next.",export:"Export",ctxD:"The optional 70B lane, as Public AI served it (identity not verified); the default 8B on CPU drafts the same changes. Flagged means a person checks it: the checks are tuned to miss nothing.",whereS:"Decisions stay in this browser until exported.",backList:"List",slotsT:"Show number slots",famChange1:"1 change",aThen:"Then",aOr:"Or",aboutH:"About this register",aBind:"What counts is the version that matches BAG's decision; which one that is, the audit cannot know.",
 aKnownHeadS:"Listed by our earlier census · {k} of {n} found",aTermHeadS:"Terminology · {n}",aWhat:"What differs",aDating:"Since when",aNote2:"Note",aTermL:"Term",
 aTexts:"The texts",aActL:"Actions and note",saveNextI:"Next issue",keysA:"j/k or ↑/↓ move · Ctrl/Cmd+Enter save and next",lane:"Lane",laneM:"Method",comparedW:"Compared with"},
fr:{gCond:"Modifie une condition",gEdit:"Coquilles et rédaction",gTerm:"Terminologie",ctxAud:"Le code compare les {n} limitations en DE/FR/IT, sans modèle. Chaque cas demande une décision : quel texte est erroné, et quelle suite lui donner.",export:"Exporter",ctxD:"La variante 70B optionnelle, telle que servie par Public AI (identité non vérifiée) ; la variante par défaut (8B sur CPU) rédige les mêmes modifications. Signalé veut dire : une personne vérifie, les contrôles sont réglés pour ne rien laisser passer.",whereS:"Les décisions restent dans ce navigateur jusqu'à leur exportation.",backList:"Liste",slotsT:"Afficher les emplacements",famChange1:"1 modification",aThen:"Ensuite",aOr:"Ou",aboutH:"À propos de ce registre",aBind:"Ce qui compte est la version conforme à la décision de l'OFSP ; laquelle, l'audit ne peut pas le savoir.",
 aKnownHeadS:"Recensés par notre inventaire antérieur · {k} sur {n} trouvés",aTermHeadS:"Terminologie · {n}",aWhat:"Ce qui diverge",aDating:"Depuis quand",aNote2:"Remarque",aTermL:"Terme",
 aTexts:"Les textes",aActL:"Mesures et remarque",saveNextI:"Cas suivant",keysA:"j/k ou ↑/↓ naviguer · Ctrl/Cmd+Entrée enregistrer et continuer",lane:"Variante",laneM:"Méthode",comparedW:"Comparé avec"},
it:{gCond:"Modifica una condizione",gEdit:"Refusi e redazione",gTerm:"Terminologia",ctxAud:"Il codice confronta tutte le {n} limitazioni in DE/FR/IT, senza modello. Ogni caso chiede una decisione: quale testo è sbagliato, e come procedere.",export:"Esporta",ctxD:"La variante 70B opzionale, come servita da Public AI (identità non verificata); la variante predefinita (8B su CPU) redige le stesse modifiche. Segnalata significa che una persona deve verificarla: i controlli sono tarati per non lasciarsi sfuggire nulla.",whereS:"Le decisioni restano in questo browser finché non vengono esportate.",backList:"Elenco",slotsT:"Mostra i segnaposto",famChange1:"1 modifica",aThen:"Poi",aOr:"Oppure",aboutH:"Informazioni su questo registro",aBind:"Conta la versione conforme alla decisione dell'UFSP; quale sia, la verifica non può saperlo.",
 aKnownHeadS:"Già rilevati dal nostro censimento precedente · trovati {k} su {n}",aTermHeadS:"Terminologia · {n}",aWhat:"Che cosa diverge",aDating:"Da quando",aNote2:"Nota",aTermL:"Termine",
 aTexts:"I testi",aActL:"Misure e nota",saveNextI:"Caso successivo",keysA:"j/k o ↑/↓ spostarsi · Ctrl/Cmd+Invio salva e continua",lane:"Variante",laneM:"Metodo",comparedW:"Confrontato con"}};
Object.keys(TX5).forEach(function(L){Object.keys(TX5[L]).forEach(function(k){TX[L][k]=TX5[L][k]})});
// lanes (8B Q8_0 on CPU the default, 70B fewer edits, live months), one save-and-next pattern, what counts as decided,
// where decisions live, distinct legend labels (10 Oct 2026, juror round)
var TX6={
de:{laneOpt8:"Testmenge (publiziert) · 8B Q8_0, CPU (Standard)",laneOpt70:"Testmenge (publiziert) · Apertus 70B, wie von Public AI bereitgestellt (optional; Identität nicht überprüft)",laneOptLive:"Schattenlauf {m} (nicht produktiv) · 8B Q8_0, CPU",
 ctxD8:"Die Standardspur: Apertus 8B auf CPU, ohne Netz. Markiert heisst: eine Person prüft – die Prüfungen sind darauf ausgelegt, nichts zu übersehen.",
 ctxDL:"Vom BAG im Monat {m} publizierte Änderungen, danach zur Messung mit der Standardspur (8B auf CPU) aus dem öffentlichen Feed entworfen; die französische und italienische Fassung des BAG hat das Modell nie gesehen. Lange oder umgeschriebene Texte gehen ohne Entwurf an die Übersetzung. Markiert heisst: eine Person prüft.",
 keyS:[["✓","bereit"],["~","markiert, wohl in Ordnung"],["▲","markiert, zu prüfen"],["≠","bisheriger Text mit Problem"]],
 saveNext:"Speichern, nächste Änderung",saveNextI:"Speichern, nächster Fall",
 keys:"j/k oder ↑/↓ wechseln · 1/2/3 entscheiden · f/i Sprache · Ctrl/Cmd+Enter speichern, weiter",keysA:"j/k oder ↑/↓ wechseln · 1–4 Fassung · Ctrl/Cmd+Enter speichern, weiter",
 needDec:"Zuerst entscheiden (1 übernehmen · 2 bearbeitet übernehmen · 3 zurückweisen); j oder ↓ überspringt ohne Entscheid.",
 needDecA:"Zuerst entscheiden: die richtige Fassung oder eine Massnahme; j oder ↓ überspringt ohne Entscheid.",
 aDecHint:"Gilt als entschieden, sobald eine Antwort unten (eine Fassung oder «noch unklar») oder eine Massnahme gewählt ist; eine Notiz allein lässt den Fall offen.",
 figsA:"{r} bereit ({rp}) · {f} markiert · {x} identisch mit dem publizierten Text des BAG",figsC:"{r} bereit · {f} markiert · {h} an die Übersetzung",figsX:"{x} von {n} identisch mit dem publizierten Text des BAG",
 lblHeld:"Testmenge: vergangene SL-Änderungen {p}, vom BAG bereits publiziert",lblLive:"Schattenlauf {m} (SL {a} → {b}), nicht für den produktiven Einsatz",
 expHead:"Experimentelle Prüfungen (standardmässig aus) · {c} von {n} bestätigt",expNote:"Die Prüfungen auf Operator, Verneinung und Zahlwort (Runde 5) sind ausgeschaltet: weniger als die Hälfte ihrer Befunde war echt. Hier stehen nur Befunde, die zwei blinde Annotatoren beide bestätigt haben; sie zählen nicht zu den Fällen oben, ein Entscheid wird nicht erfasst.",
 kindsX:{operator:"Operator",negation:"Verneinung",number_word:"Zahlwort"},labX:{real:"bestätigt: ändert die Bedeutung",minor:"bestätigt: geringfügig"},
 aNoteOnly:"offen · Notiz gespeichert, noch keine Fassung oder Massnahme gewählt",lsNote:"nur in diesem Browser gespeichert · zum Behalten exportieren"},
en:{laneOpt8:"Test set (published) · 8B Q8_0, CPU (default)",laneOpt70:"Test set (published) · Apertus 70B as Public AI served it (optional; identity not verified)",laneOptLive:"Shadow run {m} (not for production) · 8B Q8_0, CPU",
 ctxD8:"The default lane: Apertus 8B on CPU, air-gapped. Flagged means a person checks it: the checks are tuned to miss nothing.",
 ctxDL:"Changes BAG published in {m}, drafted afterwards from the public feed by the default lane (8B on CPU) to measure it; BAG's French and Italian were never shown to the model. Long or rewritten texts go to a translator without a draft. Flagged means a person checks it.",
 keyS:[["✓","ready"],["~","flagged, probably fine"],["▲","flagged, to check"],["≠","old text has a problem"]],
 saveNext:"Save, next change",saveNextI:"Save, next issue",
 keys:"j/k or ↑/↓ move · 1/2/3 decide · f/i language · Ctrl/Cmd+Enter save, next",keysA:"j/k or ↑/↓ move · 1–4 version · Ctrl/Cmd+Enter save, next",
 needDec:"Decide first (1 accept · 2 accept edited · 3 send back); j or ↓ skips without deciding.",
 needDecA:"Decide first: the right version or an action; j or ↓ skips without deciding.",
 aDecHint:"Counts as decided once an answer below (a version, or not clear yet) or an action is chosen; a note alone leaves the issue open.",
 figsA:"{r} ready ({rp}) · {f} flagged · {x} identical to BAG's published text",figsC:"{r} ready · {f} flagged · {h} to a translator",figsX:"{x} of {n} identical to BAG's published text",
 lblHeld:"test set: past SL changes {p} that BAG already published",lblLive:"shadow run {m} (SL {a} → {b}), not for production use",
 expHead:"Experimental checks (off by default) · {c} confirmed of {n}",expNote:"The operator, negation and number-word checks (round 5) ship off: fewer than half of their findings were real. Listed here only where two blind annotators both confirmed the finding; not counted in the issues above, no decision recorded.",
 kindsX:{operator:"operator",negation:"negation",number_word:"number word"},labX:{real:"confirmed: changes the meaning",minor:"confirmed: minor"},
 aNoteOnly:"open · note saved, no version or action chosen yet",lsNote:"saved in this browser only · export to keep"},
fr:{laneOpt8:"Jeu de test (publié) · 8B Q8_0, CPU (par défaut)",laneOpt70:"Jeu de test (publié) · Apertus 70B tel que servi par Public AI (optionnel ; identité non vérifiée)",laneOptLive:"Essai à blanc {m} (hors production) · 8B Q8_0, CPU",
 ctxD8:"La variante par défaut : Apertus 8B sur CPU, hors réseau. Signalé veut dire : une personne vérifie, les contrôles sont réglés pour ne rien laisser passer.",
 ctxDL:"Modifications publiées par l'OFSP au mois {m}, rédigées ensuite à partir du flux public par la variante par défaut (8B sur CPU) pour la mesurer ; le modèle n'a jamais vu le français ni l'italien de l'OFSP. Les textes longs ou réécrits vont au traducteur sans brouillon. Signalé veut dire : une personne vérifie.",
 keyS:[["✓","prêt"],["~","signalé, probablement sans problème"],["▲","signalé, à vérifier"],["≠","l'ancien texte a un problème"]],
 saveNext:"Enregistrer, modification suivante",saveNextI:"Enregistrer, cas suivant",
 keys:"j/k ou ↑/↓ naviguer · 1/2/3 décider · f/i langue · Ctrl/Cmd+Entrée enregistrer, suivant",keysA:"j/k ou ↑/↓ naviguer · 1–4 version · Ctrl/Cmd+Entrée enregistrer, suivant",
 needDec:"Décider d'abord (1 accepter · 2 accepter modifié · 3 renvoyer) ; j ou ↓ passe sans décider.",
 needDecA:"Décider d'abord : la bonne version ou une mesure ; j ou ↓ passe sans décider.",
 aDecHint:"Compte comme décidé dès qu'une réponse ci-dessous (une version, ou « pas encore clair ») ou une mesure est choisie ; une remarque seule laisse le cas ouvert.",
 figsA:"{r} prêts ({rp}) · {f} signalés · {x} identiques au texte publié par l'OFSP",figsC:"{r} prêts · {f} signalés · {h} confiés à un traducteur",figsX:"{x} sur {n} identiques au texte publié par l'OFSP",
 lblHeld:"jeu de test réservé à l'évaluation : modifications passées de la LS {p}, déjà publiées par l'OFSP",lblLive:"essai à blanc {m} (LS {a} → {b}), pas pour la production",
 expHead:"Contrôles expérimentaux (désactivés par défaut) · {c} confirmés sur {n}",expNote:"Les contrôles d'opérateur, de négation et de nombre en lettres (5e série) sont désactivés : moins de la moitié de leurs constats étaient réels. Ne figurent ici que les constats confirmés par deux annotateurs à l'aveugle ; ils ne comptent pas dans les cas ci-dessus et aucune décision n'est enregistrée.",
 kindsX:{operator:"opérateur",negation:"négation",number_word:"nombre en lettres"},labX:{real:"confirmé : change le sens",minor:"confirmé : mineur"},
 aNoteOnly:"ouvert · remarque enregistrée, ni version ni mesure choisie",lsNote:"enregistré dans ce navigateur seulement · exporter pour conserver"},
it:{laneOpt8:"Insieme di prova (pubblicato) · 8B Q8_0, CPU (predefinita)",laneOpt70:"Insieme di prova (pubblicato) · Apertus 70B come servito da Public AI (opzionale; identità non verificata)",laneOptLive:"Prova in parallelo {m} (non produttiva) · 8B Q8_0, CPU",
 ctxD8:"La variante predefinita: Apertus 8B su CPU, senza rete. Segnalata significa che una persona deve verificarla: i controlli sono tarati per non lasciarsi sfuggire nulla.",
 ctxDL:"Modifiche pubblicate dall'UFSP nel mese {m}, redatte in seguito dal flusso pubblico con la variante predefinita (8B su CPU) per misurarla; il modello non ha mai visto il francese né l'italiano dell'UFSP. I testi lunghi o riscritti vanno al traduttore senza bozza. Segnalata significa che una persona deve verificarla.",
 keyS:[["✓","pronta"],["~","segnalata, probabilmente in ordine"],["▲","segnalata, da verificare"],["≠","il vecchio testo ha un problema"]],
 saveNext:"Salva, modifica successiva",saveNextI:"Salva, caso successivo",
 keys:"j/k o ↑/↓ spostarsi · 1/2/3 decidere · f/i lingua · Ctrl/Cmd+Invio salva, avanti",keysA:"j/k o ↑/↓ spostarsi · 1–4 versione · Ctrl/Cmd+Invio salva, avanti",
 needDec:"Decidere prima (1 accetta · 2 accetta modificata · 3 rinvia); j o ↓ salta senza decidere.",
 needDecA:"Decidere prima: la versione giusta o una misura; j o ↓ salta senza decidere.",
 aDecHint:"Conta come deciso appena si sceglie una risposta qui sotto (una versione, o «non ancora chiaro») o una misura; una nota da sola lascia il caso aperto.",
 figsA:"{r} pronte ({rp}) · {f} segnalate · {x} identiche al testo pubblicato dall'UFSP",figsC:"{r} pronte · {f} segnalate · {h} affidate a un traduttore",figsX:"{x} su {n} identiche al testo pubblicato dall'UFSP",
 lblHeld:"insieme di prova tenuto da parte: modifiche passate dell'ES {p}, già pubblicate dall'UFSP",lblLive:"prova in parallelo {m} (ES {a} → {b}), non per l'uso produttivo",
 expHead:"Controlli sperimentali (disattivati per impostazione predefinita) · {c} confermati su {n}",expNote:"I controlli di operatore, negazione e numero in lettere (5ª serie) sono disattivati: meno della metà dei loro rilievi era reale. Qui figurano solo i rilievi confermati da entrambi gli annotatori alla cieca; non contano nei casi qui sopra e non si registra alcuna decisione.",
 kindsX:{operator:"operatore",negation:"negazione",number_word:"numero in lettere"},labX:{real:"confermato: cambia il senso",minor:"confermato: minore"},
 aNoteOnly:"aperto · nota salvata, nessuna versione o misura scelta",lsNote:"salvato solo in questo browser · esportare per conservare"}};
Object.keys(TX6).forEach(function(L){Object.keys(TX6[L]).forEach(function(k){TX[L][k]=TX6[L][k]})});
// round 11 (11 Oct 2026, public-sector juror, Italian federal translator, BAG officer): counts that explain themselves,
// experimental findings decidable, distinct family labels, test set vs shadow run, localised tooltips, terminology in
// the header of a ready draft, "accept edited" explained, decision files merged, the public SL entry
var TX7={
de:{rulesOnly:"nur Regeln",kindExp:"experimentelle Prüfung",
 cntA:"{a} Befunde + {t} Terminologie-Hinweise = {s}, zusammengefasst in {n} Fällen; {e} davon wahrscheinlich gleichwertig (eingeklappt).",
 shownL:"{l} Fälle in der Liste + {e} eingeklappt (wahrscheinlich gleichwertig) = {n} von {N} Fällen · {m} von {M} Befunden und Hinweisen",
 shownL0:"{n} von {N} Fällen in der Liste · {m} von {M} Befunden und Hinweisen",
 aDecHint:"Gilt als entschieden, sobald eine Fassung (oder «noch unklar») oder mindestens eine Massnahme gewählt ist – auch nur «An den Sprachdienst»; eine Notiz allein lässt den Fall offen.",
 expHead:"Experimentelle Prüfungen (ausgeschaltet) · {c} von {n} Befunden von zwei blinden Annotatoren bestätigt · {d} entschieden",
 expNote:"Die Prüfungen auf Operator, Verneinung und Zahlwort (Runde 5) sind ausgeschaltet: weniger als die Hälfte ihrer Befunde war echt. Hier stehen nur die Befunde, die zwei blinde Annotatoren beide bestätigt haben. Sie zählen nicht zu den {n} Fällen oben, lassen sich aber wie ein Fall entscheiden und werden als eigene Art «experimentelle Prüfung» exportiert.",
 labX:{real:"beide blinden Annotatoren: ändert die Bedeutung",minor:"beide blinden Annotatoren: geringfügig"},aBlind:"Blindprüfung",
 famOpt:"{f} · {w} · {n} Entwürfe",
 chipCode:"vom Code aus dem Deutschen gesetzte Zahl",chipModel:"vom Modell geschriebene Zahl: prüfen",slotS:"Platzhalter {s}",intCode:"interner Code {c}",
 termChk:"Begriff prüfen",termChkT:"Alle Prüfungen bestanden, aber ein Begriff weicht von der Hausübersetzung des BAG ab (Hinweis unter der Erläuterung).",
 rM:"Löschung wie im Deutschen",rdM:"Was der Entwurf mehr löscht als das Deutsche, steht in Sätzen, die das Deutsche selbst streicht (Hinweis unter der Erläuterung).",
 slAbbr:"SL",noEdit2:"«2 Bearbeitet übernehmen» geht erst nach einer Änderung am Entwurfstext (in den Text klicken).",
 impMerged:"{k} Dateien zusammengeführt: {d} Entscheide zu Entwürfen, {a} zur Registerprüfung (pro Element gilt der neueste Entscheid).",impConf:"Widersprüchlich, der neueste gilt: {x}.",
 whereM:"Entscheide von Kolleginnen und Kollegen zusammenführen: bei «Entscheide importieren» mehrere JSON-Dateien zugleich wählen; pro Element gilt der neueste Entscheid.",
 slLink:"Öffentliche SL",slLinkT:"sl.bag.admin.ch/sl öffnen und nach «{p}» suchen (einen stabilen Direktlink pro Produkt gibt es nicht)",
 decLang:"Sprache des Entscheids",decLangV:"nicht in den Daten der Prüfung",
 txtChange:"Textänderung {L} zwischen {p} und {d}: nicht im Repository (mitgeliefert sind nur die Texte vom {s})"},
en:{rulesOnly:"rules only",kindExp:"experimental check",
 cntA:"{a} findings + {t} terminology notices = {s}, grouped into {n} issues; {e} of them probably equivalent (collapsed).",
 shownL:"{l} issues listed + {e} collapsed (probably equivalent) = {n} of {N} issues · {m} of {M} findings and notices",
 shownL0:"{n} of {N} issues listed · {m} of {M} findings and notices",
 aDecHint:"Counts as decided once a version (or not clear yet) or at least one action is chosen, even only “Send to the language service”; a note alone leaves the issue open.",
 expHead:"Experimental checks (switched off) · {c} of {n} findings confirmed by two blind annotators · {d} decided",
 expNote:"The operator, negation and number-word checks (round 5) ship switched off: fewer than half of their findings were real. Listed here only where two blind annotators both confirmed the finding. They are not among the {n} issues above, but each can be decided like an issue and is exported as its own kind, “experimental check”.",
 labX:{real:"both blind annotators: changes the meaning",minor:"both blind annotators: minor"},aBlind:"Blind check",
 famOpt:"{f} · {w} · {n} drafts",
 chipCode:"number placed by code from the German",chipModel:"number written by the model: check it",slotS:"slot {s}",intCode:"internal code {c}",
 termChk:"term to check",termChkT:"Every check passed, but a term departs from BAG's house rendering (note under the explanation).",
 rM:"deletion as in the German",rdM:"What the draft removes beyond the German sits in sentences the German itself removes (note under the explanation).",
 slAbbr:"SL",noEdit2:"“2 Accept edited” becomes available once you edit the draft text (click into it).",
 impMerged:"Merged {k} files: {d} draft decisions, {a} audit decisions (per item the newest decision wins).",impConf:"Conflicting, newest kept: {x}.",
 whereM:"To merge colleagues' decisions, choose several JSON files at once in “Import decisions”; per item the newest decision wins.",
 slLink:"Public SL",slLinkT:"open sl.bag.admin.ch/sl and search for “{p}” (there is no stable per-product link)",
 decLang:"Language of the decision",decLangV:"not in the audit data",
 txtChange:"Text change {L} between {p} and {d}: not in the repo (only the texts of {s} ship with it)"},
fr:{rulesOnly:"règles seules",kindExp:"contrôle expérimental",
 cntA:"{a} constats + {t} avis de terminologie = {s}, regroupés en {n} cas ; {e} d'entre eux, formulation probablement équivalente (repliés).",
 shownL:"{l} cas listés + {e} repliés (formulation probablement équivalente) = {n} cas sur {N} · {m} constats et avis sur {M}",
 shownL0:"{n} cas listés sur {N} · {m} constats et avis sur {M}",
 aDecHint:"Compte comme décidé dès qu'une version (ou « pas encore clair ») ou au moins une mesure est choisie, même seulement « Transmettre au service linguistique » ; une remarque seule laisse le cas ouvert.",
 expHead:"Contrôles expérimentaux (désactivés) · {c} constats sur {n} confirmés par deux annotateurs à l'aveugle · {d} décidés",
 expNote:"Les contrôles d'opérateur, de négation et de nombre en lettres (5e série) sont livrés désactivés : moins de la moitié de leurs constats étaient réels. Ne figurent ici que les constats confirmés par deux annotateurs à l'aveugle. Ils ne font pas partie des {n} cas ci-dessus, mais chacun se décide comme un cas et s'exporte comme type à part, « contrôle expérimental ».",
 labX:{real:"les deux annotateurs à l'aveugle : change le sens",minor:"les deux annotateurs à l'aveugle : mineur"},aBlind:"Contrôle à l'aveugle",
 famOpt:"{f} · {w} · {n} brouillons",
 chipCode:"nombre placé par le code à partir de l'allemand",chipModel:"nombre écrit par le modèle : à vérifier",slotS:"emplacement {s}",intCode:"code interne {c}",
 termChk:"terme à vérifier",termChkT:"Tous les contrôles sont passés, mais un terme s'écarte de la traduction maison de l'OFSP (remarque sous l'explication).",
 rM:"suppression comme en allemand",rdM:"Ce que le brouillon supprime en plus de l'allemand se trouve dans des phrases que l'allemand supprime lui-même (remarque sous l'explication).",
 slAbbr:"LS",noEdit2:"« 2 Accepter modifié » devient disponible dès que vous modifiez le texte du brouillon (cliquez dedans).",
 impMerged:"{k} fichiers fusionnés : {d} décisions sur les brouillons, {a} décisions d'audit (pour chaque élément, la décision la plus récente l'emporte).",impConf:"Divergentes, la plus récente est gardée : {x}.",
 whereM:"Pour fusionner les décisions de collègues, choisissez plusieurs fichiers JSON à la fois dans « Importer des décisions » ; pour chaque élément, la décision la plus récente l'emporte.",
 slLink:"LS publique",slLinkT:"ouvrir sl.bag.admin.ch/sl et rechercher « {p} » (il n'existe pas de lien direct stable par produit)",
 decLang:"Langue de la décision",decLangV:"absente des données de l'audit",
 txtChange:"Modification du texte {L} entre le {p} et le {d} : pas dans le dépôt (seuls les textes du {s} sont livrés)"},
it:{rulesOnly:"solo regole",kindExp:"controllo sperimentale",
 cntA:"{a} rilievi + {t} avvisi di terminologia = {s}, raggruppati in {n} casi; {e} di questi con formulazione probabilmente equivalente (richiusi).",
 shownL:"{l} casi in elenco + {e} richiusi (formulazione probabilmente equivalente) = {n} casi su {N} · {m} rilievi e avvisi su {M}",
 shownL0:"{n} casi in elenco su {N} · {m} rilievi e avvisi su {M}",
 aDecHint:"Conta come deciso appena si sceglie una versione (o «non ancora chiaro») o almeno una misura, anche solo «Inviare al servizio linguistico»; una nota da sola lascia il caso aperto.",
 expHead:"Controlli sperimentali (disattivati) · {c} rilievi su {n} confermati da due annotatori alla cieca · {d} decisi",
 expNote:"I controlli di operatore, negazione e numero in lettere (5ª serie) sono forniti disattivati: meno della metà dei loro rilievi era reale. Qui figurano solo i rilievi confermati da entrambi gli annotatori alla cieca. Non fanno parte dei {n} casi qui sopra, ma ognuno si decide come un caso e si esporta come tipo a sé, «controllo sperimentale».",
 labX:{real:"entrambi gli annotatori alla cieca: cambia il senso",minor:"entrambi gli annotatori alla cieca: minore"},aBlind:"Controllo alla cieca",
 famOpt:"{f} · {w} · {n} bozze",
 chipCode:"numero inserito dal codice a partire dal tedesco",chipModel:"numero scritto dal modello: da verificare",slotS:"segnaposto {s}",intCode:"codice interno {c}",
 termChk:"termine da verificare",termChkT:"Tutti i controlli superati, ma un termine si scosta dalla traduzione in uso all'UFSP (nota sotto la spiegazione).",
 rM:"soppressione come nel tedesco",rdM:"Ciò che la bozza toglie oltre al tedesco sta in frasi che il tedesco stesso sopprime (nota sotto la spiegazione).",
 slAbbr:"ES",noEdit2:"«2 Accetta modificata» diventa disponibile dopo una modifica del testo della bozza (cliccarci dentro).",
 impMerged:"{k} file uniti: {d} decisioni sulle bozze, {a} decisioni della verifica (per ogni elemento vale la decisione più recente).",impConf:"In contrasto, tenuta la più recente: {x}.",
 whereM:"Per unire le decisioni di colleghe e colleghi, scegliere più file JSON insieme in «Importa decisioni»; per ogni elemento vale la decisione più recente.",
 slLink:"ES pubblico",slLinkT:"aprire sl.bag.admin.ch/sl e cercare «{p}» (non esiste un link diretto stabile per prodotto)",
 decLang:"Lingua della decisione",decLangV:"assente dai dati della verifica",
 txtChange:"Modifica del testo {L} tra il {p} e il {d}: non nel repository (sono inclusi solo i testi del {s})"}};
Object.keys(TX7).forEach(function(L){Object.keys(TX7[L]).forEach(function(k){TX[L][k]=TX7[L][k]});TX[L].kinds=Object.assign({},TX[L].kinds,{experimental:TX7[L].kindExp})});
// one question per issue (juror round, 10 Oct 2026): which text is wrong (the odd one first and labelled), then what to
// do; a majority version marked wrong is confirmed inline; the reviewer's name before the first decision; exports in
// the interface language with machine codes alongside
var TX8={
de:{aria:{views:"Ansichten",issues:"Fälle",issue:"Fall",register:"Register der Änderungen",family:"Familie",search:"Produkt oder Limitierungscode suchen",case:"Änderung",json:"Entscheide (JSON)",uil:"Sprache der Oberfläche"},undone:"Entscheid zurückgenommen (erneut klicken, um zu entscheiden)",frozenW:"eingefroren",descEn:"Befundtext der Prüfung (englisch, vom Code erzeugt, nicht übersetzt)",enCode:"englisch, vom Code erzeugt",impName:"Name der prüfenden Person aus der Datei übernommen: {n}.",progX:"{d}/{n} experimentell",aWrongQ:"Welcher Text ist falsch?",aWrongSub:"Gemessen am Entscheid des BAG, den die Prüfung nicht kennt. Mehrere Antworten möglich.",oddDiff:"weicht von den beiden anderen ab",
 aRemQ:"Was ist zu tun?",rem:{exofficio:"Von Amtes wegen berichtigen",holder:"Mit der Zulassungsinhaberin in der dreijährlichen Überprüfung aufnehmen",langsvc:"An den Sprachdienst",none:"Keine Massnahme (gleichwertige Formulierung)",unclear:"Noch unklar – Entscheiddossier prüfen"},
 remNeedW:"«Von Amtes wegen berichtigen» und «Mit der Zulassungsinhaberin aufnehmen» setzen voraus, dass oben der falsche Text gewählt ist.",
 aMajQ:"{L} stimmt hier mit {M} überein; abweichend ist {O}. {L} trotzdem als falsch markieren?",aMajYes:"Ja, {L} ist falsch",aMajNo:"Abbrechen",
 aNameAsk:"Zuerst Ihren Namen eingeben: Er wird mit jedem Entscheid und in den Exporten gespeichert. Ihre Wahl ist vorgemerkt und wird gespeichert, sobald der Name eingegeben ist.",revPh:"Name (nötig, wird mit jedem Entscheid gespeichert)",
 aDecHint:"Entschieden, sobald der falsche Text und die Massnahme gewählt sind. «An den Sprachdienst», «Keine Massnahme» und «Noch unklar» gelten auch ohne Angabe des falschen Texts; eine Notiz allein lässt den Fall offen.",
 needDecA:"Zuerst entscheiden: welcher Text falsch ist und was zu tun ist; j oder ↓ überspringt ohne Entscheid.",
 keysA:"j/k oder ↑/↓ wechseln · 1–3 falscher Text · Ctrl/Cmd+Enter speichern, weiter",
 aPartW:"offen · {w} als falsch markiert, noch keine Massnahme gewählt",aPartM:"offen · diese Massnahme setzt den falschen Text voraus",aWrongS:"{w} falsch",
 aLegacy:"Von einer früheren Version dieser Seite gespeichert: {x}",aRightS:"Fassung gemäss Entscheid {r}",
 csvHead:["Fall","Befunde","Produkt","Limitierung","Sprachen","Art","kind_code","Werte","Datierung","Vor dieser Prüfung erfasst","Falscher Text","Fassung gemäss Entscheid","Massnahme","action_code","Notiz","Entschieden am","Entschieden von","Prüfung (SL-Stand)","Einzeln entschieden","Code-Revision"]},
en:{aria:{views:"Views",issues:"Issues",issue:"Issue",register:"Register of changes",family:"Family",search:"Search product or limitation code",case:"Change",json:"Decisions (JSON)",uil:"Interface language"},undone:"decision undone (click again to decide)",frozenW:"frozen",descEn:"Finding text",enCode:"generated by the code",impName:"Reviewer name taken from the file: {n}.",progX:"{d}/{n} experimental",aWrongQ:"Which text is wrong?",aWrongSub:"Measured against BAG's decision, which the audit cannot see. More than one may be wrong.",oddDiff:"differs from the other two",
 aRemQ:"What should happen?",rem:{exofficio:"Correct ex officio",holder:"Raise with the holder in the triennial review",langsvc:"Send to the language service",none:"No action (equivalent wording)",unclear:"Not clear yet — check the decision file"},
 remNeedW:"“Correct ex officio” and “Raise with the holder” need the wrong text chosen above.",
 aMajQ:"{L} agrees with {M} here; {O} is the one that differs. Mark {L} as wrong anyway?",aMajYes:"Yes, {L} is wrong",aMajNo:"Cancel",
 aNameAsk:"Enter your name first: it is stored with each decision and in the exports. Your choice is kept and saved as soon as the name is entered.",revPh:"Name (required, stored with each decision)",
 aDecHint:"Decided once the wrong text and what to do are chosen. “Send to the language service”, “No action” and “Not clear yet” also count without naming the wrong text; a note alone leaves the issue open.",
 needDecA:"Decide first: which text is wrong and what to do; j or ↓ skips without deciding.",
 keysA:"j/k or ↑/↓ move · 1–3 wrong text · Ctrl/Cmd+Enter save, next",
 aPartW:"open · {w} marked wrong, no action chosen yet",aPartM:"open · this action needs the wrong text",aWrongS:"{w} wrong",
 aLegacy:"Stored by an earlier version of this page: {x}",aRightS:"version matching the decision {r}",
 csvHead:["Issue","Findings","Product","Limitation","Languages","Kind","kind_code","Values","Dating","Listed before this audit","Wrong text","Version matching the decision","Action","action_code","Note","Decided on","Decided by","Audit (SL of)","Decided separately","Code revision"]},
fr:{aria:{views:"Vues",issues:"Liste des cas",issue:"Cas",register:"Registre des modifications",family:"Famille",search:"Rechercher un produit ou un code de limitation",case:"Modification",json:"Décisions (JSON)",uil:"Langue de l'interface"},undone:"décision annulée (cliquez à nouveau pour décider)",frozenW:"gelés",descEn:"Texte du constat (en anglais, produit par le code, non traduit)",enCode:"en anglais, produit par le code",impName:"Nom du réviseur repris du fichier : {n}.",progX:"{d}/{n} expérimentaux",aWrongQ:"Quel texte est erroné ?",aWrongSub:"Par rapport à la décision de l'OFSP, que l'audit ne connaît pas. Plusieurs réponses possibles.",oddDiff:"diffère des deux autres",
 aRemQ:"Que faire ?",rem:{exofficio:"Corriger d'office",holder:"Aborder avec le titulaire lors du réexamen triennal",langsvc:"Transmettre au service linguistique",none:"Aucune mesure (formulation équivalente)",unclear:"Pas encore clair – vérifier le dossier de décision"},
 remNeedW:"« Corriger d'office » et « Aborder avec le titulaire » supposent que le texte erroné soit choisi ci-dessus.",
 aMajQ:"{L} concorde ici avec {M} ; c'est {O} qui diffère. Marquer quand même {L} comme erroné ?",aMajYes:"Oui, {L} est erroné",aMajNo:"Annuler",
 aNameAsk:"Saisissez d'abord votre nom : il est enregistré avec chaque décision et dans les exports. Votre choix est retenu et enregistré dès que le nom est saisi.",revPh:"Nom (requis, enregistré avec chaque décision)",
 aDecHint:"Décidé dès que le texte erroné et la mesure sont choisis. « Transmettre au service linguistique », « Aucune mesure » et « Pas encore clair » comptent aussi sans indiquer le texte erroné ; une remarque seule laisse le cas ouvert.",
 needDecA:"Décider d'abord : quel texte est erroné et que faire ; j ou ↓ passe sans décider.",
 keysA:"j/k ou ↑/↓ naviguer · 1–3 texte erroné · Ctrl/Cmd+Entrée enregistrer, suivant",
 aPartW:"ouvert · {w} marqué erroné, aucune mesure choisie",aPartM:"ouvert · cette mesure suppose le texte erroné",aWrongS:"{w} erroné",
 aLegacy:"Enregistré par une version antérieure de cette page : {x}",aRightS:"version conforme à la décision {r}",
 csvHead:["Cas","Constats","Produit","Limitation","Langues","Type","kind_code","Valeurs","Datation","Recensé avant cet audit","Texte erroné","Version conforme à la décision","Mesure","action_code","Remarque","Décidé le","Décidé par","Audit (version LS)","Décidé séparément","Révision du code"]},
it:{aria:{views:"Viste",issues:"Elenco dei casi",issue:"Caso",register:"Registro delle modifiche",family:"Famiglia",search:"Cercare un prodotto o un codice di limitazione",case:"Modifica",json:"Decisioni (JSON)",uil:"Lingua dell'interfaccia"},undone:"decisione annullata (cliccare di nuovo per decidere)",frozenW:"congelati",descEn:"Testo del rilievo (in inglese, generato dal codice, non tradotto)",enCode:"in inglese, generato dal codice",impName:"Nome del revisore ripreso dal file: {n}.",progX:"{d}/{n} sperimentali",aWrongQ:"Quale testo è errato?",aWrongSub:"Rispetto alla decisione dell'UFSP, che la verifica non conosce. Più risposte possibili.",oddDiff:"diverge dalle altre due",
 aRemQ:"Che cosa fare?",rem:{exofficio:"Correggere d'ufficio",holder:"Discutere con il titolare nel riesame triennale",langsvc:"Inviare al servizio linguistico",none:"Nessuna misura (formulazione equivalente)",unclear:"Non ancora chiaro – verificare il dossier della decisione"},
 remNeedW:"«Correggere d'ufficio» e «Discutere con il titolare» presuppongono che sopra sia scelto il testo errato.",
 aMajQ:"{L} concorda qui con {M}; a divergere è {O}. Segnare comunque {L} come errato?",aMajYes:"Sì, {L} è errato",aMajNo:"Annulla",
 aNameAsk:"Inserire prima il proprio nome: viene salvato con ogni decisione e negli export. La scelta è tenuta in sospeso e salvata appena il nome è inserito.",revPh:"Nome (obbligatorio, salvato con ogni decisione)",
 aDecHint:"Deciso appena si scelgono il testo errato e la misura. «Inviare al servizio linguistico», «Nessuna misura» e «Non ancora chiaro» valgono anche senza indicare il testo errato; una nota da sola lascia il caso aperto.",
 needDecA:"Decidere prima: quale testo è errato e che cosa fare; j o ↓ salta senza decidere.",
 keysA:"j/k o ↑/↓ spostarsi · 1–3 testo errato · Ctrl/Cmd+Invio salva, avanti",
 aPartW:"aperto · {w} segnato come errato, nessuna misura scelta",aPartM:"aperto · questa misura presuppone il testo errato",aWrongS:"{w} errato",
 aLegacy:"Salvato da una versione precedente di questa pagina: {x}",aRightS:"versione conforme alla decisione {r}",
 csvHead:["Caso","Rilievi","Prodotto","Limitazione","Lingue","Tipo","kind_code","Valori","Datazione","Già rilevato in precedenza","Testo errato","Versione conforme alla decisione","Misura","action_code","Nota","Deciso il","Deciso da","Verifica (versione ES)","Deciso separatamente","Revisione del codice"]}};
Object.keys(TX8).forEach(function(L){Object.keys(TX8[L]).forEach(function(k){TX[L][k]=TX8[L][k]})});
// federal and Apertus-team jurors (11 Oct 2026): the issues grouped by the blind annotators' majority label, the label on
// every issue, the GEVER CSV with the label and the excerpts, the audit decisions in a file of their own, the lanes and
// statuses explained under the lane select
var TX9={
de:{gNot:"Von den Annotatoren nicht bestätigt ({n})",blind2:"Zwei blinde Claude-Annotatoren: {x}",blind3:"Blinde Claude-Annotatoren (Mehrheit von drei): {x}",
 blindL:{real:"ändert eine Bedingung",minor:"geringfügig",not:"nicht bestätigt"},blindPer:"je Befund: {x}",
 cntB:"{a} Befunde + {t} Terminologie-Hinweise = {s}, zusammengefasst in {n} Fällen; {e} davon von den blinden Annotatoren nicht bestätigt (eingeklappt).",
 shownLB:"{l} Fälle in der Liste + {e} eingeklappt (nicht bestätigt) = {n} von {N} Fällen · {m} von {M} Befunden und Hinweisen",
 csvMore:["Blinde Einstufung","Auszug DE","Auszug FR","Auszug IT"],exportDecA:"Prüfungsentscheide exportieren (JSON)",
 laneQ:"Spuren und Status erklären",
 laneHelp:"Testmenge: 166 publizierte Änderungen, neu entworfen, um das Werkzeug zu messen; Standard ist Apertus 8B Q8_0 auf CPU (zertifizierter Build), optional Apertus 70B, wie von Public AI bereitgestellt (Identität nicht überprüft). Schattenlauf: ein Monat des Live-Feeds, nicht produktiv. Status: ✓ bereit (alle Prüfungen bestanden) · ~ wahrscheinlich in Ordnung (markiert, jeder Befund wahrscheinlich unbedenklich) · ▲ zu prüfen · ≠ abweichend (der alte Text weicht schon vom Deutschen ab) · h an Übersetzung übergeben."},
en:{gNot:"Not confirmed by the annotators ({n})",blind2:"Two blind Claude annotators: {x}",blind3:"Blind Claude annotators (majority of three): {x}",
 blindL:{real:"changes a condition",minor:"minor",not:"not confirmed"},blindPer:"per finding: {x}",
 cntB:"{a} findings + {t} terminology notices = {s}, grouped into {n} issues; {e} of them not confirmed by the blind annotators (collapsed).",
 shownLB:"{l} issues listed + {e} collapsed (not confirmed) = {n} of {N} issues · {m} of {M} findings and notices",
 csvMore:["Blind label","Excerpt DE","Excerpt FR","Excerpt IT"],exportDecA:"Export audit decisions (JSON)",
 laneQ:"Explain lanes and statuses",
 laneHelp:"Test set: 166 published changes re-drafted to measure the tool; the default is Apertus 8B Q8_0 on CPU (certified build), the option Apertus 70B as Public AI served it (identity not verified). Shadow run: one month of the live feed, not for production. Status: ✓ ready (all checks passed) · ~ probably fine (flagged, every finding probably harmless) · ▲ to check · ≠ divergent (the old text already differs from the German) · h routed to a translator."},
fr:{gNot:"Non confirmés par les annotateurs ({n})",blind2:"Deux annotateurs Claude à l'aveugle : {x}",blind3:"Annotateurs Claude à l'aveugle (majorité de trois) : {x}",
 blindL:{real:"modifie une condition",minor:"mineur",not:"non confirmé"},blindPer:"par constat : {x}",
 cntB:"{a} constats + {t} avis terminologiques = {s}, regroupés en {n} cas ; {e} d'entre eux non confirmés par les annotateurs à l'aveugle (repliés).",
 shownLB:"{l} cas listés + {e} repliés (non confirmés) = {n} cas sur {N} · {m} constats et avis sur {M}",
 csvMore:["Évaluation à l'aveugle","Extrait DE","Extrait FR","Extrait IT"],exportDecA:"Exporter les décisions de l'audit (JSON)",
 laneQ:"Expliquer les variantes et les statuts",
 laneHelp:"Jeu de test : 166 modifications publiées, rédigées à nouveau pour mesurer l'outil ; par défaut Apertus 8B Q8_0 sur CPU (build certifié), en option Apertus 70B tel que servi par Public AI (identité non vérifiée). Essai à blanc : un mois du flux réel, hors production. Statuts : ✓ prêt (tous les contrôles passés) · ~ probablement sans problème (signalé, chaque constat probablement anodin) · ▲ à vérifier · ≠ divergent (l'ancien texte diffère déjà de l'allemand) · h confié à un traducteur."},
it:{gNot:"Non confermati dagli annotatori ({n})",blind2:"Due annotatori Claude alla cieca: {x}",blind3:"Annotatori Claude alla cieca (maggioranza di tre): {x}",
 blindL:{real:"modifica una condizione",minor:"minore",not:"non confermato"},blindPer:"per rilievo: {x}",
 cntB:"{a} rilievi + {t} avvisi terminologici = {s}, raggruppati in {n} casi; {e} di essi non confermati dagli annotatori alla cieca (richiusi).",
 shownLB:"{l} casi in elenco + {e} richiusi (non confermati) = {n} casi su {N} · {m} rilievi e avvisi su {M}",
 csvMore:["Valutazione alla cieca","Estratto DE","Estratto FR","Estratto IT"],exportDecA:"Esporta le decisioni della verifica (JSON)",
 laneQ:"Spiegare varianti e stati",
 laneHelp:"Insieme di prova: 166 modifiche pubblicate, redatte di nuovo per misurare lo strumento; predefinita Apertus 8B Q8_0 su CPU (build certificato), opzionale Apertus 70B come servito da Public AI (identità non verificata). Prova in parallelo: un mese del flusso reale, non produttiva. Stati: ✓ pronta (tutti i controlli superati) · ~ probabilmente in ordine (segnalata, ogni rilievo probabilmente innocuo) · ▲ da verificare · ≠ divergente (il testo precedente diverge già dal tedesco) · h affidata a un traduttore."}};
Object.keys(TX9).forEach(function(L){Object.keys(TX9[L]).forEach(function(k){TX[L][k]=TX9[L][k]})});
function nT(k,n,o){o=o||{};o.n=n;return fmt(n===1&&TX[UL][k+"1"]!=null?t(k+"1"):t(k),o)}
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
// the numbers of a family's changes (first, and the last when there are more), so that two families of the same product differ
var FAMNO={};G.forEach(function(g){(FAMNO[g.family]=FAMNO[g.family]||[]).push(g.no)});
function famNos(f){var a=FAMNO[f]||[];return a.length?(a.length>1?a[0]+"–"+a[a.length-1]:a[0]):""}
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
var TAB=AU?"audit":"drafts",LHOPEN=false;   // landing view: the register audit (runs today, no model); #drafts or #wbNNN opens the drafts
function kv(id,rows){if(!$(id))return;$(id).innerHTML=rows.map(function(r){return "<dt"+(r[3]?' title="'+esc(r[3])+'"':"")+">"+esc(r[0])+"</dt><dd"+(r[2]?' class="'+r[2]+'"':"")+">"+esc(r[1])+"</dd>"}).join("")}
function ddate(s){return /^\d{8}$/.test(s||"")?s.slice(6,8)+"."+s.slice(4,6)+"."+s.slice(0,4):(s||"?")}
function grp(n){var s=String(n==null?"—":n);return /^\d{4,6}$/.test(s)?s.slice(0,-3)+(UL==="en"?",":"’")+s.slice(-3):s}
var MS=M.lane==="70b"?"70B":M.lane==="8b"?"8B"+(/q8_0/i.test(M.model||"")?" Q8_0":""):M.model;
function keyHTML(items){return items.map(function(k){var g=k[0],m;
  if(g==="AER")m='<span class="mk"><span class="lt">A</span></span><span class="mk"><span class="lt">E</span></span><span class="mk"><span class="lt">R</span></span>';
  else if(g==="K")m='<span class="lt s">K</span>';else if(g==="D")m='<span class="lt">D</span>';
  else if(g==="v2")m='<span class="v2">6%</span>';else if(g==="v1")m='<span class="v1">12</span>';else if(g==="bar")m='<span class="obar"></span>';
  else m='<span class="mk'+(g==="▲"||g==="≠"?" r":g==="~"?" f":"")+'">'+esc(g)+"</span>";
  return "<span>"+m+" "+esc(k[1])+"</span>"}).join("")}
function cap(x){x=String(x||"");return x.charAt(0).toUpperCase()+x.slice(1)}
function chrome(){
 document.documentElement.lang=UL;$("l-ui").textContent=t("ui");applyTheme();
 var C=D.counts;
 $("t-drafts").innerHTML=esc(t("tabDrafts"))+' <span class="c">'+C.items+"</span>";
 $("t-audit").hidden=!AU;if(AU)$("t-audit").innerHTML=esc(t("tabAudit"))+' <span class="c" title="'+esc(cntTxt())+'">'+AU.issues.length+"</span>";
 $("t-audit").setAttribute("aria-selected",TAB==="audit");$("t-drafts").setAttribute("aria-selected",TAB==="drafts");
 $("t-audit").tabIndex=TAB==="audit"?0:-1;$("t-drafts").tabIndex=TAB==="drafts"?0:-1;
 $("p-audit").hidden=TAB!=="audit";$("p-drafts").hidden=TAB!=="drafts";
 $("x-sum").textContent=t("export");$("x-dec").textContent=t(TAB==="audit"&&AU?"exportDecA":"exportDec");$("where").textContent=t("where")+" "+t("whereM");
 ["x-xlf","x-xlf12","x-copy","x-imp","x-msg"].forEach(function(i){$(i).hidden=TAB==="audit"});["a-csv-i","a-csv","a-imp","a-msg"].forEach(function(i){$(i).hidden=TAB!=="audit"});
 var fz1=(M.pipeline.match(/freeze sha256:([0-9a-f]+)/)||[])[1]||"";
 $("prov").textContent=M.pipeline.split(";")[0]+(fz1?" · freeze "+fz1.slice(0,12):"")+" · outputs "+M.run_sha256.slice(0,12)+(M.rev?" · rev "+M.rev:"")+" · "+t("whereS");
 $("prov").title=M.pipeline+" · outputs sha256:"+M.run_sha256+" · items sha256:"+M.items_sha256+(AU?" · audit "+AU.meta.file:"");
 $("lanehelp").hidden=TAB==="audit"||!LHOPEN;$("lanehelp").textContent=t("laneHelp");
 if(TAB==="audit"){chromeAudit();$("ctxline").title=$("ctxline").textContent;return}
 // one line of context: what these drafts are, whose decision they are
 // with lanes: a select of the lanes first (8B default, 70B fewer edits, the live months), then what the lane shown is
 var LB=M.live&&M.live_span?fmt(t("lblLive"),{m:M.live,a:M.live_span[0],b:M.live_span[1]}):M.period&&!M.custom&&/^held-out set \(/.test(M.label||"")?fmt(t("lblHeld"),{p:M.period}):M.label;
 // the lane's figures, from the run shown: its scored summary (recorded runs), else the counts of its records
 var FG=A?fmt(t("figsA"),{r:A.unflagged,rp:pct(A.ready_rate),f:A.flagged,x:pct(A.exact.model)}):fmt(t("figsC"),{r:C.ready,f:C.flagged,h:C.human});
 if(!A&&!C.human)FG=FG.split(" · ").slice(0,2).join(" · ");if(!A&&C.exact!=null)FG+=" · "+fmt(t("figsX"),{x:C.exact,n:C.exact_of});
 var ctx=(FG?FG+". ":"")+(M.live?fmt(t("ctxDL"),{m:M.live}):M.custom?t("dB2"):M.lane==="70b"?t("ctxD"):M.lane==="8b"?t("ctxD8"):t("dB2"));
 $("ctxline").innerHTML=(LANES.length>1?'<label class="lsel"><span class="vh">'+esc(t("lane"))+'</span><select id="lane-s">'+LANES.map(function(l){
   var o=l.live?fmt(t("laneOptLive"),{m:l.live}):l.lane==="70b"?t("laneOpt70"):t("laneOpt8");
   return '<option value="'+esc(l.id)+'"'+(l.id===(LANE||DEF)?" selected":"")+">"+esc(o)+"</option>"}).join("")+"</select></label> ":"")+
  '<button type="button" class="qh" id="lane-q" aria-expanded="'+LHOPEN+'" aria-controls="lanehelp" title="'+esc(t("laneQ"))+'" aria-label="'+esc(t("laneQ"))+'">?</button>'+
  "<b>"+esc(cap(fmt(t("drawingBy"),{l:LB,n:C.items,m:MS})))+".</b> "+esc(ctx);
 $("lane-q").onclick=function(){LHOPEN=!LHOPEN;this.setAttribute("aria-expanded",LHOPEN);$("lanehelp").hidden=!LHOPEN};
 if($("lane-s"))$("lane-s").onchange=function(){var v=this.value;location.hash="#"+(v===DEF?"":v+"/")+"drafts"};
 $("ctxline").title=cap(fmt(t("drawingBy"),{l:LB,n:C.items,m:MS}))+". "+ctx;
 var fz=(M.pipeline.match(/freeze sha256:([0-9a-f]+)/)||[])[1]||"";
 kv("kv-l",[[t("guards"),(M.stack==="g3"?"guards3":"guards v2")+" ("+t("frozenW")+")"+(fz?" · "+String((t("tb")||{}).freeze||"freeze").toLowerCase()+" "+fz.slice(0,12):"")],
  [t("items"),String(D.counts.items)],[t("changes"),String(D.counts.changes)],[t("model"),M.model],[t("run"),M.run],
  [t("lane"),M.lane==="70b"?t("lane70")+" · "+t("laneDef"):M.lane==="8b"?t("lane8"):"—"]]);
 var r=[];
 if(A){r.push([t("ready"),A.unflagged+" · "+pct(A.ready_rate),"",t("codeOnly")]);r.push([t("flagged"),A.flagged+" · "+pct(A.flag_rate)]);
  var ex=A.exact;r.push([t("exact"),pct(ex.model)+" vs "+pct(ex.rules)+" ("+sgn(ex.delta)+" pts, 95% CI "+ex.ci95[0]+" to "+ex.ci95[1]+")"]);
  if(A.pass!=null)r.push([t("rule"),A.pass?"PASS":"FAIL",A.pass?"pass":"fail"])}
 else{r.push([t("ready"),String(C.ready),"",t("codeOnly")]);r.push([t("flagged"),String(C.flagged)]);if(C.human)r.push([t("human"),String(C.human)]);
  if(C.exact!=null)r.push([t("exact").split(" vs")[0],String(C.exact)])}
 if(C.flagged)r.push([t("triSplit"),fmt(t("triSplitV"),{c:C.lvl_check,f:C.lvl_fine})]);
 if(C.flagged)r.push([t("triage"),triTxt(C.to_check,C.probably_fine)]);
 if(C.divergent)r.push([t("divergent"),String(C.divergent)]);
 kv("kv-r",r);
 selF("f-status",t("status"),[["open",t("open")],["ready",t("ready")],["check",t("fCheck")],["fine",t("fFine")],["flagged",t("flagged")],["divergent",t("divF")],["decided",t("decidedF")],["all",t("all")]],F.status,function(v){F.status=v;renderReg()});
 selF("f-lang",t("language"),[["all","FR+IT"],["fr","FR"],["it","IT"]],F.lang,function(v){F.lang=v;if(v!=="all")focusL=v;famBar();renderReg();renderCase()});
 var fs=$("f-fam");fs.innerHTML="";fs.appendChild(new Option(t("allFam")+" ("+D.families.length+")",""));
 D.families.forEach(function(f){var nm=String(f[2]).split(/,| \+\d/)[0],more=String(f[2]).indexOf(",")>=0||/\+\d/.test(f[2]);
  var o=new Option(fmt(t("famOpt"),{f:short(nm,32)+(more?" …":""),w:famNos(f[0]),n:f[1]}),f[0]);o.title=f[2]+" · "+famNos(f[0]);fs.appendChild(o)});fs.value=F.fam;$("f-q").placeholder=t("search");famBar();
 $("h-prod").textContent=t("product");$("h-chg").textContent=t("change");
 document.querySelectorAll("[data-aria]").forEach(function(e){var a=t("aria")[e.dataset.aria];if(a)e.setAttribute("aria-label",a)});
 $("x-xlf").textContent=t("xlf");$("x-xlf12").textContent=t("xlf12");$("x-copy").textContent=t("copy");$("x-imp").textContent=t("imp");
 $("reg-key").innerHTML=keyHTML(t("keyS"));
 $("reg-key").title=t("legend");progress()}
function selF(id,label,opts,cur,fn){var s=$(id);s.innerHTML='<label class="k" for="'+id+'-s">'+esc(label)+'</label><select id="'+id+'-s">'+opts.map(function(o){
  return '<option value="'+esc(o[0])+'"'+(o[0]===cur?" selected":"")+">"+esc(o[1])+"</option>"}).join("")+"</select>";$(id+"-s").onchange=function(){fn(this.value)}}
function seg(id,label,opts,cur,fn){var s=$(id);s.innerHTML='<span class="k">'+esc(label)+"</span>";
 opts.forEach(function(o){var b=document.createElement("button");b.type="button";b.className="tb";b.textContent=o[1];b.setAttribute("aria-pressed",o[0]===cur);
  b.onclick=function(){s.querySelectorAll("button").forEach(function(x){x.setAttribute("aria-pressed",x===b)});fn(o[0])};s.appendChild(b)})}
function progress(){if(TAB==="audit"&&AU){var tm=AU.rows.filter(function(r){return r.kind==="terminology"}),fm=AU.rows.filter(function(r){return r.kind!=="terminology"});
  var pa=fmt(t("progA"),{i:IS.filter(iDecided).length,n:IS.length,x:fm.filter(aDecided).length,a:fm.length,y:tm.filter(aDecided).length,t:tm.length});
  var px=XIS.length?fmt(t("progX"),{d:XIS.filter(iDecided).length,n:XIS.length}):"";   // experimental checks: counted apart
  $("progress").innerHTML="<b>"+esc(pa.split(" (")[0])+"</b>"+(px?" · <b>"+esc(px)+"</b>":"")+' · <span class="lsn">'+esc(t("lsNote"))+"</span>";$("progress").title=pa+(px?" · "+px:"")+" · "+t("where");return}
 var n=ITEMS.filter(function(it){return dec(it)}).length;$("progress").innerHTML="<b>"+n+"/"+ITEMS.length+"</b> "+esc(t("decided"))+' · <span class="lsn">'+esc(t("lsNote"))+"</span>";$("progress").title=t("where")}
// ------------------------------------------------------------------ tabs
function setTab(tb){if(tb==="audit"&&!AU)tb="drafts";TAB=tb;chrome();
 if(TAB==="audit"){renderAudit();try{if(location.hash!=="#"+HP+"audit")history.replaceState(null,"","#"+HP+"audit")}catch(e){}}
 else{renderReg();if(sel){markSel(true);renderCase()}}}
$("t-audit").onclick=function(){setTab("audit")};$("t-drafts").onclick=function(){setTab("drafts")};
document.querySelector(".views").addEventListener("keydown",function(e){if(e.key==="ArrowRight"||e.key==="ArrowLeft"){e.preventDefault();setTab(TAB==="audit"?"drafts":"audit");$(TAB==="audit"?"t-audit":"t-drafts").focus()}});
// ------------------------------------------------------------------ register audit
// One table row per issue (audit_view.issues: findings naming the same difference on the same text), its findings
// listed below it. Decisions are stored per finding signature (SA[sig] = {right, actions[], note, at, by, date} + own:true
// when a finding is decided apart from its issue): a decision on the issue is written to every finding of the issue
// that is not decided separately, so it carries over to the next audit run finding by finding.
var AF={show:"all",lang:"all",kind:"all",since:""},EQOPEN=false,NCOPEN=false,EXOPEN=false,OPEN={},
 LNG=["DE","FR","IT"],REM=["exofficio","holder","langsvc","none","unclear"],AWC=null,ANAME=false,PEND=null;
var IS=AU?AU.issues:[];
if(AU){IS.forEach(function(I){I.M=I.rows.map(function(i){return AU.rows[i]});I.M.forEach(function(r){r.I=I})})}
// experimental issues (round 5, checks off): one per finding, decided like an issue, outside the issue counts
var XIS=AU&&AU.exp&&AU.exp.issues?AU.exp.issues:[],XROWS=AU&&AU.exp?AU.exp.rows:[];
XIS.forEach(function(I){I.M=I.rows.map(function(i){return XROWS[i]});I.M.forEach(function(r){r.I=I})});
function allRows(){return AU?AU.rows.concat(XROWS):[]}
function aActs(d){return d?(d.actions||(d.action?[ACTMAP[d.action]||d.action]:[])):[]}
function aHas(d){return !!(d&&(d.right||aActs(d).length||d.note||(d.wrong||[]).length||d.remedy))}
// a decision has two answers: which text is wrong (wrong: ["IT"], several allowed) and what to do (remedy: one of REM).
// The stored fields of earlier page versions are derived from them (right: the versions not marked wrong, or "unclear";
// actions: fix_<lang> per wrong text for a correction plus the remedy, "decfile" for not clear yet), so older readers
// and exports keep working. A decision stored by an earlier page version (right + actions only) is read back into the
// two answers for display (aAns) and keeps its fields until it is changed.
function aAns(d){if(!d)return {w:[],m:""};if(d.remedy!=null||d.wrong)return {w:(d.wrong||[]).slice(),m:d.remedy||""};
 var A=aActs(d),w=A.filter(function(v){return /^fix_(de|fr|it)$/.test(v)}).map(function(v){return v.slice(4).toUpperCase()}),m="";
 [["exofficio","exofficio"],["holder","holder"],["langsvc","langsvc"],["none","none"],["falsealarm","none"],["decfile","unclear"],["unclear","unclear"]].some(function(p){if(A.indexOf(p[0])>=0){m=p[1];return true}return false});
 if(!m&&d.right==="unclear")m="unclear";return {w:w,m:m}}
function lsort(a,b){return LNG.indexOf(a)-LNG.indexOf(b)}
function fixRem(m){return m==="exofficio"||m==="holder"||m==="langsvc"}
function aDerive(d){var w=(d.wrong||[]).filter(function(x){return LNG.indexOf(x)>=0}).sort(lsort),m=REM.indexOf(d.remedy)>=0?d.remedy:"";d.wrong=w;d.remedy=m;
 d.right=w.length?LNG.filter(function(x){return w.indexOf(x)<0}).join("+"):(m==="unclear"?"unclear":"");
 var A=fixRem(m)?w.map(function(x){return "fix_"+x.toLowerCase()}):[];if(m)A.push(m==="unclear"?"decfile":m);d.actions=A;delete d.action;return d}
// decided: a remedy, and the wrong text unless the remedy is the language service, no action or not clear yet; a decision
// of an earlier page version counts as before (a version or an action)
function aDone(d){if(!d)return false;if(d.remedy!=null){var m=d.remedy;return !!m&&(!(m==="exofficio"||m==="holder")||(d.wrong||[]).length>0)}return !!(d.right||aActs(d).length)}
function aDecided(r){return aDone(SA[r.sig])}
function iDec(I){for(var i=0;i<I.M.length;i++){var d=SA[I.M[i].sig];if(d&&!d.own)return d}return null}
function iDecided(I){return I.M.every(aDecided)}
function iAny(I){return I.M.some(aDecided)}
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
function aMark(I){return iDecided(I)?'<span class="mk" title="'+esc(t("aDecF"))+'">✓</span>':""}
function aStatus(d){if(!d||!d.at)return t("openSt");
 if(!aDone(d)){var x=aAns(d);if(d.remedy!=null&&x.w.length&&!x.m)return fmt(t("aPartW"),{w:x.w.join(", ")});if(d.remedy!=null&&x.m)return t("aPartM");return t("aNoteOnly")}
 var day=ddate(zts(d.at).slice(0,10).replace(/-/g,""));
 var s=(d.remedy!=null?ansTxt(d)+" · ":"")+(d.by?fmt(t("decOn"),{d:day,n:d.by}):fmt(t("decOnAnon"),{d:day}));
 if(d.date&&AU&&d.date!==AU.meta.date)s+=" "+fmt(t("earlier"),{s:ddate(d.date)});return s}
function dating(x){if(!x)return "";if(x.earliest&&x.n===x.m)return fmt(t("dA"),{n:x.n,d:ddate(x.first)});
 if(x.prev&&x.n===x.m)return fmt(t("dB"),{p:ddate(x.prev),d:ddate(x.first),n:x.n});return fmt(t("dC"),{d:ddate(x.first),n:x.n,m:x.m==null?"?":x.m})}
function cntTxt(){var m=AU.meta,nc=IS.filter(function(I){return I.blind==="not"}).length,lab=IS.some(function(I){return I.blind});
 return fmt(t(lab?"cntB":"cntA"),{a:m.main,t:m.term,s:m.main+m.term,n:IS.length,e:lab?nc:IS.filter(function(I){return I.eq}).length})}
function chromeAudit(){var m=AU.meta,nf=AU.rows.length;
 $("ctxline").innerHTML="<b>"+esc(fmt(t("drawA"),{d:ddate(m.date)}))+".</b> "+esc(fmt(t("ctxAud"),{n:grp(m.n_limitations)}))+" "+esc(cntTxt());
 var bk=m.by_kind?Object.keys(m.by_kind).filter(function(k){return k!=="terminology"}).map(function(k){return m.by_kind[k]+" "+(t("kinds")[k]||k)}).join(", "):"";
 kv("kv-l",[[t("aSnap"),ddate(m.date)],[t("aChecked"),m.n_limitations!=null?grp(m.n_limitations):"—"],
  [t("aFindings"),fmt(t("aFindingsV"),{a:m.main,b:bk,t:m.term,n:IS.length}).replace(" ()","")],[t("laneM"),t("laneA")]]);
 var r=[[t("aKnown"),(m.known_found!=null?m.known_found:m.known_ids.length)+" / "+(m.known_of!=null?m.known_of:m.known_ids.length),"big"]];
 if(m.main_real!=null&&m.term_real!=null)r.push([t("aConf"),fmt(t("aConfV"),{r:m.main_real,a:m.main,k:m.main_real-(m.main_new_real||0),x:m.main_new_real||0,tr:m.term_real,t:m.term})]);
 var sn0=m.snapshots||[];if(sn0.length)r.push([t("comparedW"),fmt(t("modelA"),{n:sn0.length,a:ddate(sn0[0]),b:ddate(sn0[sn0.length-1])})]);
 kv("kv-r",r);
 selF("a-show",t("aShow"),[["all",fmt(t("aAllN"),{n:IS.length})],["known",t("aKnownF")+" ("+IS.filter(function(I){return I.known}).length+")"],["open",t("aOpenF")],["decided",t("aDecF")]],AF.show,function(v){AF.show=v;renderAudit()});
 selF("a-lang",t("language"),[["all","DE+FR+IT"],["de","DE"],["fr","FR"],["it","IT"]],AF.lang,function(v){AF.lang=v;renderAudit()});
 var ks=[["all",t("all")]];["number","unit","language","editorial","terminology"].forEach(function(k){var n=IS.filter(function(I){return I.kinds.indexOf(k)>=0}).length;if(n)ks.push([k,t("kinds")[k]+" ("+n+")"])});
 IS.forEach(function(I){I.kinds.forEach(function(k){if(!ks.some(function(x){return x[0]===k}))ks.push([k,k])})});
 if(XIS.length)ks.push(["experimental",t("kinds").experimental+" ("+XIS.length+")"]);
 selF("a-kind",t("aKindF"),ks,AF.kind,function(v){AF.kind=v;renderAudit()});
 // "new since": the snapshots the audit dates against (summary.snapshots_dated), each with the issues first seen after it
 var sn=(m.snapshots||[]).slice(0,-1),ss=$("a-since");
 if(sn.length&&IS.some(function(I){return I.dating})){var o='<label class="k" for="a-since-s">'+esc(t("newSince"))+'</label><select id="a-since-s"><option value="">'+esc(t("newAny"))+"</option>";
  sn.forEach(function(d){var n=IS.filter(function(I){return newAfter(I,d)}).length;o+='<option value="'+d+'"'+(AF.since===d?" selected":"")+">"+esc(ddate(d))+" ("+n+")</option>"});
  ss.innerHTML=o+"</select>";ss.hidden=false;$("a-since-s").onchange=function(){AF.since=this.value;renderAudit()}}else ss.hidden=true;
 $("ah-no").textContent="";$("ah-lim").textContent=t("aLim");$("ah-kind").textContent=t("aWhat");
 $("a-csv-i").textContent=t("csvIss");$("a-csv").textContent=t("aCsv");$("a-imp").textContent=t("imp");
 progress()}

function newAfter(I,d){return I.M.some(function(r){return r.dating&&r.dating.first>d})}
function aOk(I){if(AF.lang!=="all"&&I.langs.indexOf(AF.lang)<0)return false;if(AF.kind!=="all"&&I.kinds.indexOf(AF.kind)<0)return false;
 if(AF.since&&!newAfter(I,AF.since))return false;
 switch(AF.show){case "known":return I.known;case "open":return !iDecided(I);case "decided":return iDecided(I);default:return true}}
function segHTML(s){return s.map(function(x){return x[1]===2?'<span class="v2'+(x[0].length>16?" w":"")+'">'+esc(x[0])+"</span>":x[1]===1?'<span class="v1">'+esc(x[0])+"</span>":esc(x[0])}).join("")}
function trimSeg(s){if(!s||!s.length)return s;s=s.map(function(x){return x.slice()});
 if(/^…\S/.test(s[0][0])&&!s[0][1]){var k=s[0][0].search(/\s/);if(k>0)s[0][0]="…"+s[0][0].slice(k+1)}
 var z=s.length-1;if(/\S…$/.test(s[z][0])&&!s[z][1]){var q=s[z][0].slice(0,-1).search(/\s\S*$/);if(q>0)s[z][0]=s[z][0].slice(0,q)+" …"}return s}
function snipHTML(r,L){var s=trimSeg(r.snip[L]);if(!s||!s.length)return '<span class="na">'+esc(r.lang===L||L==="de"?t("aNoSnip"):"—")+"</span>";
 return '<div class="snip'+(r.src[L]==="snapshot"?" src-s":"")+'" lang="'+L+'"'+(r.src[L]==="snapshot"?' title="'+esc(t("aSnapSrc"))+'"':"")+">"+segHTML(s)+"</div>"}
function termHTML(r){var m=r.term;if(!m)return "";var h="";
 if(m.old||m["new"])h+='<span class="term" lang="'+esc(r.lang||"")+'">'+esc(t("termOld"))+" <s>"+esc(m.old||"?")+"</s> · "+esc(t("termNew"))+" <u>"+esc(m["new"]||"?")+"</u></span>";
 if(m.where&&m.where.length)h+='<span class="sub2" title="'+esc(m.where.join("; "))+'">'+esc(fmt(t("termWhere"),{x:m.where.slice(0,2).join("; ")+(m.where.length>2?" +"+(m.where.length-2):"")}))+"</span>";
 return h}
function uniqP(xs){var o=[];xs.forEach(function(x){if(x&&o.indexOf(x)<0)o.push(x)});return o}
// the decision controls, for an issue (scope "i") or one finding decided separately (scope "m")
function ansTxt(d){var x=aAns(d);return [x.w.length?fmt(t("aWrongS"),{w:x.w.join(", ")}):"",actLab(d)].filter(Boolean).join(" · ")}
// the action in the interface language (exports and status); a decision of an earlier page version by its stored actions
function actLab(d){if(!d)return "";var x=aAns(d);
 if(d.remedy!=null)return x.m?t("rem")[x.m]+(x.w.length&&fixRem(x.m)?" ("+x.w.join(", ")+")":""):"";
 var acts=t("acts");return aActs(d).map(function(v){return /^fix_/.test(v)?acts.fix+": "+v.slice(4).toUpperCase():(t("rem")[v]||acts[v]||v)}).join("; ")}
function kindLab(I){return I.exp?t("kinds").experimental:I.kinds.map(function(k){return t("kinds")[k]||k}).join(" + ")}
// the other version that agrees with v when odd is the one that differs ("" when v is the odd one or nothing differs)
function majPartner(odd,v){var O=String(odd||"").toUpperCase();if(LNG.indexOf(O)<0||v===O)return "";return LNG.filter(function(x){return x!==O&&x!==v})[0]}
// question 1, which text is wrong: nothing preselected; the version that differs from the other two first and labelled
function ctlWrong(d,odd,scope){var A=aAns(d),O=String(odd||"").toUpperCase(),L=LNG.indexOf(O)>=0?[O].concat(LNG.filter(function(x){return x!==O})):LNG;
 var h='<div class="btns aw" role="group" aria-label="'+esc(t("aWrongQ"))+'">'+L.map(function(v){
  var pd=isPend(scope,"wrong",v);return '<button type="button" class="box'+(pd?" pend":"")+'" data-a="wrong" data-v="'+v+'" aria-pressed="'+(A.w.indexOf(v)>=0||pd)+'">'+esc(v)+(v===O?'<span class="oddb"> · '+esc(t("oddDiff"))+"</span>":"")+"</button>"}).join("")+"</div>";
 if(AWC&&AWC.s===scope)h+='<div class="aconf" role="alert"><span class="q">'+esc(fmt(t("aMajQ"),{L:AWC.v,M:majPartner(O,AWC.v),O:O}))+'</span><button type="button" class="box primary" data-a="wrong" data-ok="1" data-v="'+AWC.v+'">'+
  esc(fmt(t("aMajYes"),{L:AWC.v}))+'</button><button type="button" class="box" data-a="wcancel">'+esc(t("aMajNo"))+"</button></div>";
 return h}
// question 2, what to do: one remedy; a correction or the holder needs the wrong text
// a correction or the holder needs the wrong text: until then the two buttons are aria-disabled (not disabled), so that a
// click on them shows why instead of doing nothing; a choice made before the reviewer's name is shown as pending
function remNeed(A,v,scope){var pw=PEND&&PEND.s===scope&&PEND.a==="wrong";return (v==="exofficio"||v==="holder")&&!A.w.length&&!pw&&A.m!==v}
function ctlRem(d,scope){var A=aAns(d),R=t("rem"),id="rn-"+scope.replace(/[^\w-]/g,"_"),W=A.w.concat(PEND&&PEND.s===scope&&PEND.a==="wrong"&&A.w.indexOf(PEND.v)<0?[PEND.v]:[]);
 return '<div class="arem" role="group" aria-label="'+esc(t("aRemQ"))+'">'+REM.map(function(v){var need=remNeed(A,v,scope),pd=isPend(scope,"rem",v);
  return '<button type="button" class="box'+(pd?" pend":"")+'" data-a="rem" data-v="'+v+'" aria-pressed="'+(A.m===v||pd)+'"'+(need?' aria-disabled="true" aria-describedby="'+id+'"':"")+">"+esc(R[v])+(W.length&&fixRem(v)?" · "+esc(W.join(", ")):"")+"</button>"}).join("")+
  '<span class="hint" id="'+id+'"'+(W.length?" hidden":"")+">"+esc(t("remNeedW"))+"</span></div>"}
function isPend(scope,a,v){return !!(PEND&&PEND.s===scope&&PEND.a===a&&PEND.v===v)}
// what an earlier page version stored, shown until the decision is changed
function ctlLegacy(d){if(!d||d.remedy!=null||!(d.right||aActs(d).length))return "";
 var x=[d.right?fmt(t("aRightS"),{r:d.right==="unclear"?t("rUnclear"):d.right}):"",actLab(d)].filter(Boolean).join(" · ");return '<div class="sug">'+esc(fmt(t("aLegacy"),{x:x}))+"</div>"}
function whoHTML(){var ask=ANAME&&!who();return '<div class="who'+(ask?" ask":"")+'"><label>'+esc(t("rev"))+' <input type="text" id="a-rev" data-rev="1" autocomplete="name" value="'+esc(P.reviewer||"")+'" placeholder="'+esc(t("revPh"))+'"'+
 (ask?' aria-invalid="true" aria-describedby="a-name-ask"':"")+"></label>"+(ask?'<p class="aname" id="a-name-ask" role="alert">'+esc(t("aNameAsk"))+"</p>":"")+"</div>"}
function ctlNote(d){return '<textarea data-a="note" aria-label="'+esc(t("aNote"))+'" placeholder="'+esc(t("aNote"))+'">'+esc(d.note||"")+"</textarea>"}
function iStatus(I){var d=iDec(I),o=iOwn(I),s=(iDecided(I)?"✓ ":"")+aStatus(d);if(I.M.length>1)s+=" · "+fmt(t("appliesAll"),{n:I.M.length-o});if(o)s+=" · "+nT("someOwn",o);return s}
function ftHTML(I){var h="";
 I.lims.forEach(function(lim){var T=AU.texts[lim],r=I.M.filter(function(x){return x.lim===lim})[0];
  if(I.lims.length>1)h+='<p class="ftl"><b>'+esc(r.product||lim)+"</b> "+esc(lim)+"</p>";
  if(!T){h+='<p class="na">'+esc(t("ftNone"))+"</p>";return}
  h+='<div class="ftg">'+["de","fr","it"].map(function(L){var odd=I.odd===L;return '<div class="ftc'+(odd?" odd":"")+'"><div class="lh"><span class="lt">'+L.toUpperCase()+"</span>"+(odd?'<span class="oddl">'+esc(t("oddLbl"))+"</span>":"")+"</div>"+
   '<div class="snip ftx" lang="'+L+'">'+(T[L]?segHTML(T[L]):"—")+"</div></div>"}).join("")+"</div>"});
 return h}
function memHTML(I){return '<table class="mem"><tbody>'+I.M.map(function(r){var d=SA[r.sig],own=!!(d&&d.own);
  return '<tr data-sig="'+esc(r.sig)+'"><td class="mf">'+esc(r.no||"")+"</td><td><b>"+esc(r.product||r.lim)+"</b> "+'<span class="code">'+esc(r.lim)+"</span>"+
   '<span class="sub2">'+esc((t("kinds")[r.kind]||r.kind)+" · "+(r.lang||"").toUpperCase())+(r.dating?" · "+esc(dating(r.dating)):"")+"</span></td>"+
   '<td class="mc">'+(own?ctlWrong(d,r.odd,r.sig)+ctlRem(d,r.sig)+ctlLegacy(d)+ctlNote(d)+'<div class="stt">'+esc(t("memOwn")+" · "+aStatus(d))+'</div><button type="button" class="tb" data-join="1">'+esc(t("memJoin"))+"</button>"
    :'<span class="stt">'+esc(t("memFollow"))+'</span> <button type="button" class="tb" data-split="1">'+esc(t("memSplit"))+"</button>")+"</td></tr>"}).join("")+"</tbody></table>"}
// the list: one row per issue (mark, product and codes, what differs); the selected issue opens on the right
var ASEL=null,AVIS=[];
function whatTxt(I){var W=I.what;if(I.exp)return W.map(function(w){return "DE "+w[2]+" · "+(w[1]||"").toUpperCase()+" "+w[3]+" ("+(t("kindsX")[w[4]]||w[4])+")"}).join("; ");if(sev(I)===1&&W.some(function(w){return w[0]==="editorial"}))W=W.filter(function(w){return w[0]==="editorial"});
 return W.map(function(w){var L=(w[1]||"").toUpperCase();
  if(w[0]==="number")return "DE "+w[2]+" · "+L+" "+w[3];
  if(w[0]==="language")return L+": "+fmt(t("aFoundL"),{F:t("lname")[w[2]]||w[2]});
  if(w[0]==="terminology")return L+" «"+w[2]+"» → «"+w[3]+"»";
  if(w[0]==="editorial")return L+" "+w[2]+(w[3]?" → "+w[3]:"");
  return L+" "+String(w[2]||"").slice(0,60)}).join("; ")}
function aRow(I){var codes=I.lims.length>2?I.lims.slice(0,2).join(" · ")+" +"+(I.lims.length-2):I.lims.join(" · ");
 return '<tr data-iss="'+esc(I.key)+'" class="cnt'+(I.eq?" eq":"")+'" aria-selected="'+(ASEL===I)+'"><td>'+aMark(I)+"</td>"+
  '<td class="ap"><b>'+esc(uniqP(I.products).join(", ")||I.lims[0])+'</b><span class="code" title="'+esc(I.lims.join("\n"))+'">'+esc(codes)+"</span></td>"+
  '<td class="aw"><span class="kd">'+esc(I.kinds.map(function(k){return t("kinds")[k]||k}).join(" + "))+"</span>"+esc(short(whatTxt(I),I.term?44:70))+"</td></tr>"}
function xOk(I){if(AF.lang!=="all"&&I.langs.indexOf(AF.lang)<0)return false;if(AF.kind!=="all"&&AF.kind!=="experimental")return false;if(AF.since)return false;
 switch(AF.show){case "known":return false;case "open":return !iDecided(I);case "decided":return iDecided(I);default:return true}}
function short(x,n){return x.length>n?x.slice(0,n).replace(/\s+\S*$/,"")+" …":x}
function sev(I){if(I.eq)return 3;if(I.term)return 2;var ed=I.M.some(function(r){return r.kind==="editorial"}),expl=I.M.some(function(r){return r.expl&&r.expl.length});
 if(I.kinds.every(function(k){return k==="editorial"})||(ed&&expl))return 1;return 0}
// the groups follow the blind annotators' majority label of each issue (its most serious finding): changes a condition,
// minor (typos and editorial), terminology apart, not confirmed (collapsed); an issue without labels falls back to the
// kinds of its findings (sev), with the audit's "probably equivalent" collapsed
function bucket(I){if(I.blind==="not")return 4;if(I.term)return 2;if(I.blind==="real")return 0;if(I.blind==="minor")return 1;return sev(I)}
function blindTxt(I){if(!I.blind)return "";var L=t("blindL"),s=fmt(t(I.blind_n>2?"blind3":"blind2"),{x:L[I.blind]||I.blind});
 if(I.M.length>1&&uniqP(I.M.map(function(r){return r.blind})).length>1)s+=" ("+fmt(t("blindPer"),{x:I.M.map(function(r){return (r.no||r.fid)+" "+(L[r.blind]||r.blind||"—")}).join(", ")})+")";
 return s}
function renderAudit(){if(!AU){$("p-audit").innerHTML='<p class="empty">'+esc(t("aNoFile"))+"</p>";return}
 var tb=document.querySelector("#aud tbody"),Is=AF.kind==="experimental"?[]:IS.filter(aOk),G=[[],[],[],[],[]],h="",Xs=XIS.filter(xOk);
 Is.forEach(function(I){G[bucket(I)].push(I)});
 var nf=function(L){return L.reduce(function(s,I){return s+I.M.length},0)};
 AVIS=G[0].concat(G[1],G[2],NCOPEN?G[4]:[],EQOPEN?G[3]:[],EXOPEN?Xs:[]);
 [["gCond",G[0]],["gEdit",G[1]],["gTerm",G[2]]].forEach(function(x){if(x[1].length)h+='<tr class="grp"><td colspan="3">'+esc(t(x[0]))+" · "+x[1].length+"</td></tr>"+x[1].map(aRow).join("")});
 if(G[4].length)h+='<tr class="eqh"><td colspan="3"><button type="button" id="nc-tg" aria-expanded="'+NCOPEN+'">['+(NCOPEN?"−":"+")+"] "+esc(fmt(t("gNot"),{n:G[4].length}))+"</button></td></tr>"+(NCOPEN?G[4].map(aRow).join(""):"");
 if(G[3].length)h+='<tr class="eqh"><td colspan="3"><button type="button" id="eq-tg" aria-expanded="'+EQOPEN+'">['+(EQOPEN?"−":"+")+"] "+esc(fmt(t("eqHead"),{n:G[3].length}))+"</button></td></tr>"+(EQOPEN?G[3].map(aRow).join(""):"");
 h+=expHTML(Xs);
 tb.innerHTML=h||'<tr><td colspan="3" class="empty">'+esc(t("aNone"))+"</td></tr>";
 var ng=$("nc-tg");if(ng)ng.onclick=function(){NCOPEN=!NCOPEN;renderAudit();var b=$("nc-tg");if(b)b.focus()};
 var tg=$("eq-tg");if(tg)tg.onclick=function(){EQOPEN=!EQOPEN;renderAudit();var b=$("eq-tg");if(b)b.focus()};
 var xg=$("ex-tg");if(xg)xg.onclick=function(){EXOPEN=!EXOPEN;renderAudit();var b=$("ex-tg");if(b)b.focus()};
 var nq=EQOPEN?0:G[3].length,nn=NCOPEN?0:G[4].length,ne=nq+nn;
 $("a-shown").textContent=fmt(t(!ne?"shownL0":nq?"shownL":"shownLB"),{l:Is.length-ne,e:ne,n:Is.length,N:IS.length,m:nf(Is),M:AU.rows.length});
 if(AVIS.indexOf(ASEL)<0)ASEL=AVIS[0]||null;
 renderACase();progress()}
// experimental checks (round 5, switched off): only the findings both blind annotators confirmed, below the issues and
// outside every count of the headline; collapsed at first; each one is decided like an issue (its own signature) and
// exported as the kind "experimental check"
function expHTML(Xs){var E=AU.exp;if(!E||!Xs.length)return "";
 var h='<tr class="eqh exh"><td colspan="3"><button type="button" id="ex-tg" aria-expanded="'+EXOPEN+'">['+(EXOPEN?"−":"+")+"] "+esc(fmt(t("expHead"),{c:E.confirmed,n:E.n,d:XIS.filter(iDecided).length}))+"</button></td></tr>";
 if(!EXOPEN)return h;return h+'<tr class="expn"><td colspan="3">'+esc(fmt(t("expNote"),{n:IS.length}))+"</td></tr>"+Xs.map(aRow).join("")}
function aMarkSel(scroll){document.querySelectorAll("#aud tbody tr[data-iss]").forEach(function(r){var on=!!ASEL&&r.dataset.iss===ASEL.key;r.setAttribute("aria-selected",on);
 if(on&&scroll){var w=$("aud-wrap"),top=r.offsetTop,hh=30;if(top-hh<w.scrollTop)w.scrollTop=top-hh;else if(top+r.offsetHeight>w.scrollTop+w.clientHeight)w.scrollTop=top+r.offsetHeight-w.clientHeight}})}
function aMove(d){if(!AVIS.length)return;var i=AVIS.indexOf(ASEL);i=Math.max(0,Math.min(AVIS.length-1,(i<0?0:i+d)));ASEL=AVIS[i];aMarkSel(true);renderACase()}
// the case: 1 what differs, 2 the texts (excerpts side by side, full texts below), 3 the findings of the issue, 4 the decision
function aCaseHTML(I){var r=I.M[0],d=iDec(I)||{},n=I.M.length,odd=I.odd==="unclear"?t("aUnclear"):String(I.odd||"—").toUpperCase(),sub=[];
 I.M.forEach(function(x){
  if(x.found)sub.push(fmt(t("aFoundL"),{F:t("lname")[x.found]||x.found}));
  if(x.fix)sub.push(fmt(t("aFix"),{a:x.fix[0],b:x.fix[1]}));
  if(x.eq!=null)sub.push(t("eqWhy")+(UL!=="en"?" ("+t("enCode")+")":"")+": "+(x.eq||"—"));
  if(x.expl&&x.expl.length)sub.push(fmt(t("aExpl"),{x:x.expl.join(", ")}))});
 var h='<button class="tb back" type="button" data-back="1">← '+esc(t("backList"))+"</button><h2>"+esc(uniqP(I.products).join(", ")||I.lims[0])+'</h2><p class="ref">'+esc(I.lims.join(" · "))+" · "+esc(t("ahNo"))+" "+esc(I.iid)+" · "+esc(I.fids.join(" "))+(I.known?" · "+esc(t("aKnown")):"")+"</p>";
 h+='<section class="sec"><div class="sl"><span class="no">1</span><span class="t">'+esc(t("aWhat"))+'</span></div><dl class="facts">'+
  "<dt>"+esc(t("aKind"))+"</dt><dd>"+esc(I.kinds.map(function(k){return t("kinds")[k]||k}).join(" + "))+" · "+esc(whatTxt(I))+"</dd>"+
  "<dt>"+esc(t("aOdd"))+"</dt><dd>"+esc(odd)+"</dd>"+
  (I.dating?"<dt>"+esc(t("aDating"))+"</dt><dd>"+esc(dating(I.dating))+"</dd>":"")+
  (uniqP(sub).length?"<dt>"+esc(t("aNote2"))+"</dt><dd>"+uniqP(sub).map(esc).join("<br>")+"</dd>":"")+
  (r.term?"<dt>"+esc(t("aTermL"))+"</dt><dd>"+termHTML(r)+"</dd>":"")+
  (I.blind?"<dt>"+esc(t("aBlind"))+"</dt><dd>"+esc(blindTxt(I))+(I.exp&&r.desc?'<span class="sub2"'+(UL!=="en"?' lang="en"':"")+">"+esc(UL!=="en"?t("descEn")+": ":"")+esc(r.desc)+"</span>":"")+"</dd>":"")+
  (I.dating&&I.dating.prev?"<dt></dt><dd><span class=\"sub2\">"+esc(fmt(t("txtChange"),{L:(I.odd&&I.odd!=="unclear"?I.odd:I.langs.filter(function(x){return x!=="de"})[0]||"").toUpperCase(),p:ddate(I.dating.prev),d:ddate(I.dating.first),s:ddate(AU.meta.date)}))+"</span></dd>":"")+
  "<dt>"+esc(t("decLang"))+"</dt><dd>"+esc(t("decLangV"))+"</dd>"+
  "<dt>"+esc(t("slLink"))+'</dt><dd><span class="mono">sl.bag.admin.ch/sl</span><span class="sub2">'+esc(fmt(t("slLinkT"),{p:uniqP(I.products).join(", ")||I.lims[0]}))+" · "+esc(I.lims.join(" · "))+"</span></dd></dl></section>";
 h+='<section class="sec"><div class="sl"><span class="no">2</span><span class="t">'+esc(t("aTexts"))+'</span></div><div class="ftg">'+
  ["de","fr","it"].map(function(L){var o=I.odd===L;return '<div class="ftc'+(o?" odd":"")+'"><div class="lh"><span class="lt">'+L.toUpperCase()+"</span>"+(o?'<span class="oddl">'+esc(t("oddLbl"))+"</span>":"")+"</div>"+snipHTML(r,L)+"</div>"}).join("")+"</div>"+
  '<details class="ft" data-k="ft"'+(OPEN["ft"+I.key]?" open":"")+"><summary>"+esc(t("ft"))+(I.lims.length>1?" · "+esc(fmt(t("ftN"),{n:I.lims.length})):"")+"</summary>"+(OPEN["ft"+I.key]?ftHTML(I):"")+"</details></section>";
 if(shortTexts(I))h=h.slice(0,h.lastIndexOf('<section class="sec"><div class="sl"><span class="no">2</span>'))+'<section class="sec"><div class="sl"><span class="no">2</span><span class="t">'+esc(t("aTexts"))+"</span></div>"+ftHTML(I)+"</section>";
 var no=3;
 if(n>1){h+='<section class="sec"><div class="sl"><span class="no">'+no+'</span><span class="t">'+esc(fmt(t("mem"),{n:n}))+"</span></div>"+memHTML(I)+"</section>";no++}
 h+='<section class="sec"><div class="sl"><span class="no">'+no+'</span><span class="t">'+esc(t("s4"))+'</span><span class="sub">'+esc(t("aDecHint"))+"</span></div>"+whoHTML()+
  '<div class="adec"><div><div class="q" id="aq-w">'+esc(t("aWrongQ"))+'</div><div class="sub2">'+esc(t("aWrongSub"))+"</div>"+ctlWrong(d,I.odd,"i:"+I.key)+"</div>"+
  '<div><div class="q">'+esc(t("aRemQ"))+"</div>"+ctlRem(d,"i:"+I.key)+(r.sug?'<div class="sug">'+esc(t("aSug"))+": "+esc(t("rem")[r.sug]||t("acts")[r.sug]||r.sug)+"</div>":"")+ctlLegacy(d)+ctlNote(d)+"</div></div>"+
  '<div class="stt'+(iAny(I)?" done":"")+'" id="a-stt">'+esc(iStatus(I))+'</div><div class="save"><button class="box primary" type="button" id="a-next"'+(iAny(I)?"":' aria-disabled="true"')+' aria-describedby="an-why">'+esc(t("saveNextI"))+'</button><span class="hint" id="an-why">'+esc(iAny(I)?t("keysA"):t("needDecA"))+"</span></div></section>";
 return h}
function shortTexts(I){return I.lims.every(function(lim){var T=AU.texts[lim];return T&&["de","fr","it"].every(function(L){return (T[L]||[]).reduce(function(n,x){return n+x[0].length},0)<=800})})}
function renderACase(){var c=$("acase");if(PEND&&(!ASEL||PEND.k!==ASEL.key))PEND=null;if(!ASEL){c.innerHTML='<p class="empty">'+esc(t("aNone"))+"</p>";return}c.innerHTML=aCaseHTML(ASEL)}
function issueOf(el){if(el.closest("#acase"))return ASEL;var tr=el.closest("tr[data-iss]");if(!tr)return null;var k=tr.dataset.iss;return IS.concat(XIS).filter(function(I){return I.key===k})[0]||null}
function rowOf(sig){return allRows().filter(function(x){return x.sig===sig})[0]}
function stamp(d){d.at=zts();d.by=who();d.date=AU.meta.date;return d}
function upd(d,f){var a=f.dataset.a,v=f.dataset.v;
 if(a==="wrong"||a==="rem"){var x=aAns(d);d.wrong=x.w;d.remedy=x.m;
  if(a==="wrong"){var on=d.wrong.indexOf(v)<0;d.wrong=d.wrong.filter(function(y){return y!==v});if(on)d.wrong.push(v)}
  else d.remedy=d.remedy===v?"":v;
  aDerive(d)}
 else d[a]=f.value;return d}
// before a choice is saved: the reviewer's name (asked for inline, once per browser), and an inline confirmation when the
// version marked wrong is one of the two that agree; returns false when nothing was saved
function aGate(f,I,mt){var a=f.dataset.a,sc=mt?mt.dataset.sig:"i:"+I.key;if(a==="wcancel"){AWC=null;return false}
 if(PEND&&who()){var again=isPend(sc,a,f.dataset.v);aPend(I);if(again)return false}if(a!=="wrong"&&a!=="rem")return true;
 if(!who()){ANAME=true;AWC=null;PEND=isPend(sc,a,f.dataset.v)?null:{s:sc,k:I.key,a:a,v:f.dataset.v};return false}ANAME=false;
 if(a==="wrong"&&!f.dataset.ok){var sg=mt?mt.dataset.sig:"",cur=aAns(mt?SA[sg]:iDec(I)),odd=mt?(rowOf(sg)||{}).odd:I.odd;
  if(cur.w.indexOf(f.dataset.v)<0&&majPartner(odd,f.dataset.v)){AWC={s:mt?sg:"i:"+I.key,v:f.dataset.v};return false}}
 AWC=null;return true}
function aRefresh(I){var tr=document.querySelector('#aud tr[data-iss="'+I.key+'"]');if(tr)tr.cells[0].innerHTML=aMark(I);var st=$("a-stt");if(st&&ASEL===I){st.textContent=iStatus(I);st.classList.toggle("done",iAny(I));
  var b=$("a-next"),w=$("an-why");if(b){if(iAny(I))b.removeAttribute("aria-disabled");else b.setAttribute("aria-disabled","true")}if(w){w.textContent=iAny(I)?t("keysA"):t("needDecA");if(iAny(I)){w.classList.remove("warn");w.removeAttribute("role")}}}
 var xg=$("ex-tg");if(xg&&I.exp&&AU.exp)xg.textContent="["+(EXOPEN?"−":"+")+"] "+fmt(t("expHead"),{c:AU.exp.confirmed,n:AU.exp.n,d:XIS.filter(iDecided).length});progress()}
// the choice made before the name was entered: applied once the name is in (its field changes, or the next choice or note)
function aPend(I){var p=PEND;PEND=null;if(!p||!who()||!I||p.k!==I.key)return;var c=$("acase");if(!c)return;
 var q='button[data-a="'+p.a+'"][data-v="'+p.v+'"]',b=p.s.indexOf("i:")===0?c.querySelector(".adec "+q):c.querySelector('.mem tr[data-sig="'+p.s.replace(/"/g,'\\"')+'"] '+q);
 if(!b)return;aSet(b);if(AWC||p.s.indexOf("i:")!==0){aAfter();return}aSync(I)}
// the decision controls of the open issue brought up to date in place (no re-render: a click under way is not lost)
function aSync(I){var c=$("acase");if(!c||ASEL!==I)return;var d=iDec(I)||{},A=aAns(d),sc="i:"+I.key;
 c.querySelectorAll('.adec .aw button[data-a="wrong"]:not([data-ok])').forEach(function(b){b.setAttribute("aria-pressed",A.w.indexOf(b.dataset.v)>=0||isPend(sc,"wrong",b.dataset.v));b.classList.toggle("pend",isPend(sc,"wrong",b.dataset.v))});
 c.querySelectorAll('.adec .arem button[data-a="rem"]').forEach(function(b){var v=b.dataset.v;b.setAttribute("aria-pressed",A.m===v||isPend(sc,"rem",v));b.classList.toggle("pend",isPend(sc,"rem",v));
  if(remNeed(A,v,sc))b.setAttribute("aria-disabled","true");else b.removeAttribute("aria-disabled");b.textContent=t("rem")[v]+(A.w.length&&fixRem(v)?" · "+A.w.join(", "):"")});
 var h=c.querySelector(".adec .arem .hint");if(h){h.hidden=!!A.w.length;if(A.w.length){h.classList.remove("warn");h.removeAttribute("role")}}aRefresh(I)}
// a click on a control that is not available yet: its reason, in one line, where the control says why
function aWhy(el){var id=el.getAttribute("aria-describedby"),h=id?document.getElementById(id):null;if(!h)return;h.hidden=false;h.classList.add("warn");h.setAttribute("role","alert");
 var x=h.textContent;h.textContent="";h.textContent=x}
function aSet(f){var I=issueOf(f);if(!I)return;var mt=f.closest(".mem tr[data-sig]");if(!aGate(f,I,mt))return;
 if(mt){var sg=mt.dataset.sig,d=upd(clone(SA[sg]),f);d.own=true;delete d.via;SA[sg]=stamp(d);saveA();var st=mt.querySelector(".stt");if(st)st.textContent=t("memOwn")+" · "+aStatus(SA[sg])}
 else{var base=upd(clone(iDec(I)),f);delete base.own;base.via=1;var keep=aHas(base);if(keep)stamp(base);
  I.M.forEach(function(r){var d=SA[r.sig];if(d&&d.own)return;if(keep)SA[r.sig]=clone(base);else delete SA[r.sig]});saveA()}
 aRefresh(I)}
function aAfter(){var y=window.scrollY;renderACase();window.scrollTo(0,y);var n=$("a-rev");if(ANAME&&n&&!who()){n.focus();return}
 var k=document.querySelector("#acase .aconf .primary");if(k)k.focus()}
function aNext(){if(ASEL&&!iAny(ASEL))return;var i=AVIS.indexOf(ASEL);renderAudit();var j=AVIS.indexOf(ASEL);ASEL=AVIS[(j>=0?j:i)+1]||ASEL;aMarkSel(true);renderACase();var c=$("acase");if(c.getBoundingClientRect().top<0)c.scrollIntoView()}
(function(){var tb=document.querySelector("#aud tbody"),c=$("acase");
 tb.addEventListener("click",function(e){var tr=e.target.closest("tr[data-iss]");if(!tr)return;ASEL=issueOf(tr);aMarkSel();renderACase();if(window.innerWidth<=900){$("p-audit").classList.add("case-open");window.scrollTo(0,0)}});
 c.addEventListener("change",function(e){if(e.target.dataset&&e.target.dataset.rev){if(who())aPend(ASEL);return}var f=e.target.closest("[data-a]");if(f)aSet(f)});
 c.addEventListener("input",function(e){if(e.target.dataset&&e.target.dataset.rev){P.reviewer=e.target.value;lsSet("gleichlaut:prefs",P);
   if(who()){ANAME=false;e.target.removeAttribute("aria-invalid");e.target.removeAttribute("aria-describedby");var q=$("a-name-ask");if(q)q.remove()}return}var f=e.target.closest("textarea[data-a]");if(f)aSet(f)});
 c.addEventListener("click",function(e){if(e.target.closest("#a-next")){if(ASEL&&!iAny(ASEL)){aWhy($("a-next"));return}aNext();return}
  if(e.target.closest("[data-back]")){$("p-audit").classList.remove("case-open");aMarkSel(true);return}
  var ab=e.target.closest("button[data-a]");if(ab){if(ab.getAttribute("aria-disabled")==="true"){aWhy(ab);return}aSet(ab);aAfter();return}
  var b=e.target.closest("button[data-split],button[data-join]");if(!b)return;var I=ASEL,sg=b.closest("tr[data-sig]").dataset.sig;
  if(b.dataset.split){var d=clone(SA[sg]||iDec(I));d.own=true;delete d.via;if(!aHas(d))d.at=null;SA[sg]=d}
  else{var base=iDec(I);if(base)SA[sg]=clone(base);else delete SA[sg]}
  saveA();renderACase();aRefresh(I)});
 // the full texts are put in when their block is opened (toggle does not bubble: listen in the capture phase)
 c.addEventListener("toggle",function(e){var dt=e.target;if(!dt.matches||!dt.matches("details[data-k]"))return;var I=ASEL;if(!I)return;
  OPEN[dt.dataset.k+I.key]=dt.open;if(dt.dataset.k==="ft"&&dt.open&&!dt.querySelector(".ftg,.na"))dt.insertAdjacentHTML("beforeend",ftHTML(I))},true);
 document.addEventListener("keydown",function(e){if(TAB!=="audit")return;var tg=e.target,typing=tg.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(tg.tagName);
  if(e.key==="Enter"&&(e.metaKey||e.ctrlKey)){e.preventDefault();aNext();return}
  if(typing||e.altKey||e.metaKey||e.ctrlKey)return;if(tg.closest&&tg.closest(".views"))return;
  if(e.key==="j"||e.key==="ArrowDown"){e.preventDefault();aMove(1)}else if(e.key==="k"||e.key==="ArrowUp"){e.preventDefault();aMove(-1)}
  else if(/^[1-3]$/.test(e.key)&&ASEL){var bt=c.querySelectorAll('.adec .aw button[data-a="wrong"]')[+e.key-1];if(bt){aSet(bt);aAfter()}}})})();
function iRow(I){var d=iDec(I)||{},x=aAns(d);
 var what=I.exp?whatTxt(I):I.what.map(function(w){var L=(w[1]||"").toUpperCase();
  if(w[0]==="number")return "DE "+w[2]+" / "+L+" "+w[3];
  if(w[0]==="language")return L+": "+fmt(t("aFoundL"),{F:t("lname")[w[2]]||w[2]});
  if(w[0]==="terminology")return L+": «"+w[2]+"» → «"+w[3]+"»";
  return L+": "+w[2]+(w[3]?" → "+w[3]:"")}).join("; ");
 var own=I.M.filter(function(r){var y=SA[r.sig];return y&&y.own}).map(function(r){var y=SA[r.sig];
  return r.no+" ("+[ansTxt(y)||y.right,y.note].filter(Boolean).join(" · ")+")"}).join("; ");
 return [I.iid,I.fids.join(" "),uniqP(I.products).join(", "),I.lims.join(" "),I.langs.map(function(L){return L.toUpperCase()}).join(" "),
  kindLab(I),I.exp?"experimental":I.kinds.join("+"),what,I.dating?dating(I.dating):"",I.known?t("yes"):t("no2"),
  x.w.join(", "),d.right==="unclear"?t("rUnclear"):(d.right||""),actLab(d),aActs(d).join(" "),d.note||"",d.at?zts(d.at):"",d.by||"",ddate(d.date||AU.meta.date),own,
  blindTxt(I),exText(I.M[0],"de"),exText(I.M[0],"fr"),exText(I.M[0],"it"),M.rev||""]}
// the excerpt of one language as the issue view shows it (the aligned passage, edges trimmed to whole words)
function exText(r,L){var s=trimSeg(r&&r.snip?r.snip[L]:null);return s&&s.length?s.map(function(x){return x[0]}).join(""):""}
// the issues with their decisions, one line each, for filing (GEVER): in the interface language, ';'-separated with a BOM so
// that Excel (de-CH) opens it in columns
function auditCsv(){var H=t("csvHead"),lines=[H.slice(0,-1).concat(t("csvMore"),H.slice(-1))].concat(IS.map(iRow),XIS.map(iRow));
 return "﻿"+lines.map(function(l){return l.map(csvCellS).join(";")}).join("\r\n")+"\r\n"}
function csvCellS(s){s=String(s==null?"":s);return /[";\n\r]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s}
// the JSON exports: codes (kind, wrong, remedy, right, actions) for machines, labels in the interface language at export
// time (kind_label, action_label, ui_lang) for the record
function rKindLab(r){return r.kind==="experimental"?t("kinds").experimental+(r.xkind?" ("+(t("kindsX")[r.xkind]||r.xkind)+")":""):(t("kinds")[r.kind]||r.kind)}
function auditExport(){if(!AU)return {};var o={};allRows().forEach(function(r){var d=SA[r.sig];if(d){var x=aAns(d);o[r.sig]={limitation:r.lim,product:r.product,lang:r.lang,kind:r.kind==="experimental"?"experimental check":r.kind,kind_label:rKindLab(r),check:r.xkind||undefined,odd_one_out:r.odd,known:r.known,
 issue:r.I?r.I.iid:"",issue_key:r.I?r.I.key:"",decided_separately:!!d.own,decided:aDone(d),wrong:x.w,remedy:x.m,right:d.right||"",actions:aActs(d),action_label:actLab(d),note:d.note||"",at:d.at?zts(d.at):null,by:d.by||"",audit_date:d.date||AU.meta.date,rev:M.rev||"",ui_lang:UL}}});return o}
function auditIssues(){return IS.concat(XIS).map(function(I){var d=iDec(I)||{},x=aAns(d);return {issue:I.iid,key:I.key,kind:I.exp?"experimental check":I.kinds.join(" + "),kind_label:kindLab(I),findings:I.M.map(function(r){return r.sig}),fids:I.fids,limitations:I.lims,blind_label:I.blind||null,
 wrong:x.w,remedy:x.m,right:d.right||"",actions:aActs(d),action_label:actLab(d),note:d.note||"",at:d.at?zts(d.at):null,by:d.by||"",decided:iDecided(I)}})}
function snipText(r,L){return (r.snip[L]||[]).map(function(x){return x[0]}).join("")}
$("a-csv-i").onclick=function(){download("gleichlaut-audit-"+AU.meta.date+"-issues.csv",auditCsv(),"text/csv");$("a-msg").textContent=t("dl")+": CSV"};
// the findings, one line each: machine column names, the kind and the action in the interface language with their codes;
// ';'-separated with a BOM like the issues file, every line with the SL snapshot and the code revision
function findingsCsv(){var head=["rank","issue","limitation","product","kind","kind_code","lang","odd_one_out","known","probably_equivalent","blind_label","de","fr","it","wrong","right","action","action_code","note","decided_at","decided_by","decided_in_audit","decided_separately","sl_snapshot","rev"];
 var lines=[head.join(";")].concat(allRows().map(function(r){var d=SA[r.sig]||{};return [r.rank,r.I?r.I.iid:"",r.lim,r.product,rKindLab(r),r.kind==="experimental"?"experimental:"+r.xkind:r.kind,r.lang,r.odd,r.known?"yes":"no",r.eq!=null?(r.eq||"yes"):"",r.blind||"",snipText(r,"de"),snipText(r,"fr"),snipText(r,"it"),aAns(d).w.join(" "),d.right||"",
  actLab(d),aActs(d).join(" "),d.note||"",d.at?zts(d.at):"",d.by||"",d.date||"",d.own?"yes":"",AU.meta.date,M.rev||""].map(csvCellS).join(";")}));
 return "\ufeff"+lines.join("\r\n")+"\r\n"}
$("a-csv").onclick=function(){
 download("gleichlaut-audit-"+AU.meta.date+"-findings.csv",findingsCsv(),"text/csv");$("a-msg").textContent=t("dl")+": CSV"};

// ------------------------------------------------------------------ register (drafts)
var F={status:"open",lang:"all",fam:"",q:""},sel=null,focusL="fr",VIS=[];
function langs(g){return ["fr","it"].filter(function(L){return g.items[L]&&(F.lang==="all"||F.lang===L)})}
function okItem(it){var d=dec(it);switch(F.status){case "open":return !d;case "ready":return it.status==="ready";case "flagged":return it.status==="flagged";case "check":return it.lvl==="check";case "fine":return it.lvl==="fine";
 case "divergent":return oldIssue(it);case "decided":return !!d;default:return true}}
function renderReg(){var tb=document.querySelector("#reg tbody"),h="";VIS=[];
 G.forEach(function(g){var Ls=langs(g);if(!Ls.length)return;if(F.fam&&g.family!==F.fam)return;
  if(F.q&&(g.product+" "+g.code+" "+g.pair+" "+g.no).toLowerCase().indexOf(F.q)<0)return;
  if(!Ls.some(function(L){return okItem(g.items[L])}))return;VIS.push(g);
  h+='<tr class="cnt" data-pair="'+esc(g.pair)+'" aria-selected="'+(sel===g)+'"><td class="m">'+mark(g.items.fr)[0]+'</td><td class="m">'+mark(g.items.it)[0]+'</td><td class="prd" title="'+esc(g.product+" · "+g.code+" · "+g.no)+'">'+esc(g.product)+'<span class="pc">'+esc(g.code)+" · "+esc(g.no)+"</span>"+
   '</td><td class="chg" title="'+esc(g.sum)+'"><div class="cl">'+esc(g.sum)+"</div></td></tr>"});
 tb.innerHTML=h||'<tr><td colspan="4" class="empty">'+esc(t("none"))+"</td></tr>";
 $("shown").textContent=VIS.length+" "+t("shown");
 if(VIS.indexOf(sel)<0){sel=VIS[0]||null;if(sel)markSel();renderCase()}}
function markSel(scroll){document.querySelectorAll("#reg tbody tr").forEach(function(r){var on=sel&&r.dataset.pair===sel.pair;r.setAttribute("aria-selected",on);
 if(on&&scroll){var w=$("reg-wrap"),top=r.offsetTop-w.offsetTop,hh=28;if(top-hh<w.scrollTop)w.scrollTop=top-hh;else if(top+r.offsetHeight>w.scrollTop+w.clientHeight)w.scrollTop=top+r.offsetHeight-w.clientHeight}})}
document.querySelector("#reg tbody").addEventListener("click",function(e){var r=e.target.closest("tr[data-pair]");if(!r)return;
 sel=G.filter(function(g){return g.pair===r.dataset.pair})[0];markSel();renderCase();if(window.innerWidth<=900){$("p-drafts").classList.add("case-open");window.scrollTo(0,0)}});
$("f-fam").onchange=function(){F.fam=this.value;famAsk=false;famMsg="";famBar();renderReg()};
// family bulk action: accept every open ready draft of the selected edit family, after an in-page confirmation
var famAsk=false,famMsg="",FAMN={};G.forEach(function(g){FAMN[g.family]=(FAMN[g.family]||0)+1});
function famSize(f){return FAMN[f]||0}
function famTargets(){if(!F.fam)return [];return ITEMS.filter(function(it){return it.g.family===F.fam&&it.status==="ready"&&!dec(it)&&S.edits[it.key]==null&&!oldIssue(it)&&(F.lang==="all"||it.lang===F.lang)})}
function famBar(){var b=$("fam-bulk");if(!F.fam){b.hidden=true;b.innerHTML="";famAsk=false;famMsg="";return}b.hidden=false;var T=famTargets(),h="";
 if(famAsk&&T.length){var fr=T.filter(function(it){return it.lang==="fr"}).length;
  h='<span class="q" role="alert">'+esc(fmt(t("famAsk"),{n:T.length,fr:fr,it:T.length-fr,f:FAML[F.fam]||F.fam}))+'</span><button class="box primary" type="button" id="fam-yes">'+esc(t("famYes"))+'</button><button class="box" type="button" id="fam-no">'+esc(t("famNo"))+"</button>"+
   (FPEND&&!who()?dWhoHTML("fam-rev"):"")}
 else h='<button class="box" type="button" id="fam-go"'+(T.length?"":" disabled")+">"+esc(fmt(t("famAll"),{n:T.length}))+"</button>";
 if(famMsg)h+='<span class="msg" aria-live="polite">'+esc(famMsg)+"</span>";else if(!T.length)h+='<span class="msg">'+esc(t("famNone"))+"</span>";
 b.innerHTML=h;var go=$("fam-go"),y=$("fam-yes"),n=$("fam-no");
 if(go)go.onclick=function(){famAsk=true;famMsg="";famBar();var yy=$("fam-yes");if(yy)yy.focus()};
 if(n)n.onclick=function(){famAsk=false;FPEND=false;famBar();var g2=$("fam-go");if(g2)g2.focus()};
 if(y)y.onclick=function(){if(!who()){FPEND=true;DNAME=true;famBar();var fi=$("fam-rev");if(fi)fi.focus();return}FPEND=false;var at=zts(),T2=famTargets();
  T2.forEach(function(it){S.dec[it.key]={decision:"accept",lang:it.lang,status:it.status,edited:false,text:it.draft,reason:"",note:"",bulk:"family "+F.fam,at:at,by:who()}});
  save();famAsk=false;famMsg=fmt(t("famDone"),{n:T2.length});famBar();renderReg();if(sel)renderCase();progress()}}
$("f-q").oninput=function(){F.q=this.value.trim().toLowerCase();renderReg()};
function move(d){if(!VIS.length)return;var i=VIS.indexOf(sel);i=Math.max(0,Math.min(VIS.length-1,(i<0?0:i+d)));sel=VIS[i];markSel(true);renderCase()}
function refreshRow(g){var r=document.querySelector('#reg tr[data-pair="'+g.pair+'"]');if(r){r.cells[0].innerHTML=mark(g.items.fr)[0];r.cells[1].innerHTML=mark(g.items.it)[0]}}
// ------------------------------------------------------------------ text rendering
function chip(s,edit){var slot=(s[3]||"").replace(/[⟨⟩]/g,""),m=s[2]==="model";
 var tip=t(m?"chipModel":"chipCode")+(slot?" ("+fmt(t("slotS"),{s:slot})+")":"");
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
function stHTML(it){return esc(stLabel(it))+(it.status==="ready"&&it.termq?' · <span class="tq" title="'+esc(t("termChkT"))+'">'+esc(t("termChk"))+"</span>":"")}
function stRed(it){return (it.status==="flagged"&&it.lvl!=="fine")||oldIssue(it)}
function langMsg(it,o){var a=t("adj")[it.lang]||LN(it.lang),f=t("lname")[o.f]||o.f;return fmt(t("oldLang"),{A:a,F:f})}
function notice(it){var p=[],lang=false;
 (it.old||[]).forEach(function(o){if(o.k==="language"){lang=true;var um=o.f?langMsg(it,o):o.t;p.push('<p><span class="mk">≠</span>'+esc(um)+"</p>"+(o.f&&o.t!==um?'<p lang="'+it.lang+'">'+esc(o.t)+"</p>":""))}});
 if(it.banner&&!(lang&&(it.old||[]).every(function(o){return o.k==="language"})))p.push("<p>"+(lang?"":"<span class=\"mk\">≠</span>")+esc(it.banner)+"</p>");
 if(it.corr)p.push("<p>"+(p.length?"":"<span class=\"mk\">≠</span>")+esc(it.corr)+"</p>");
 return p.length?'<div class="notice'+(lang?" lang":"")+'" role="note"><p class="xl">'+esc(t("expl")+" ("+it.lang.toUpperCase()+")")+"</p>"+p.join("")+"</div>":""}
function curText(it){var e=S.edits[it.key];return e!=null?e:it.draft}
// one column per language, rows aligned across the two (subgrid): status · text · why · decision. The decision sits
// under its own draft; the save bar stays in view at the bottom of the case.
var SLOTS=false;
function langHTML(g,L,live){var it=g.items[L],ed=S.edits[it.key],LL=L.toUpperCase();
 var a='<article class="lang" data-lang="'+L+'"><div class="lh1"><span class="ln" title="'+esc(it.key)+'">'+esc(LN(L))+'</span><span class="st'+(stRed(it)?" r":"")+'">'+stHTML(it)+"</span>"+(it.rule_only?'<span class="key">'+esc(t("rulesOnly"))+"</span>":"")+"</div>";
 a+='<div class="body">'+notice(it);
 if(it.status==="human")a+='<p class="human">'+esc(it.reason&&!/rewritten|60/.test(it.reason)?t("humanShort"):t("humanTxt"))+(it.ratio!=null?" ("+it.ratio+"%)":"")+".</p>"+(it.reason?'<p class="ref">'+esc(it.reason)+"</p>":"")+'<p class="human" style="color:var(--ink2)">'+esc(t("humanPrev"))+"</p>";
 var body=ed!=null?esc(ed):segs(it.segs,false,live);
 a+='<div class="txt'+(live?" ed":"")+'" lang="'+L+'"'+(live?' contenteditable="true" spellcheck="true" role="textbox" aria-multiline="true" title="'+esc(t("editHint"))+'" aria-label="'+esc(LN(L))+'" data-key="'+esc(it.key)+'"':"")+">"+body+"</div>";
 if(live)a+='<div class="edmeta" data-meta="'+esc(it.key)+'">'+edmeta(it.key)+"</div>";
 a+="</div>";
 // why: at most three reasons in plain wording in the reviewer's language (the same as the XLIFF notes); the termbase note
 // on its own line; the full checks ledger with its internal codes collapsed below
 a+='<div class="why"><div class="wh"><span class="xl">'+esc(t("expl")+" ("+LL+")")+"</span>"+(it.status==="flagged"?'<span class="tri">'+triHTML(it.tri[0],it.tri[1])+"</span>":"")+"</div>";
 if(!it.ledger.length)a+='<p class="ok">'+esc(t("noChecks"))+"</p>";
 else{var W=it.why||[[],0],sh=W[0];
  if(sh.length)a+='<ol class="reasons" lang="'+L+'">'+sh.map(function(x){return "<li"+(x[1]?' class="low"':"")+">"+esc(x[0])+"</li>"}).join("")+"</ol>";
  else a+='<p class="ok">'+esc(t("allPass"))+(it.status==="ready"?" "+esc(t("codeOnly")):"")+"</p>";
  if(W[1]>sh.length)a+='<p class="more">'+esc(nT("moreN",W[1]-sh.length))+"</p>";
  if(it.tb)a+='<p class="tb" lang="'+L+'">'+esc(it.tb)+"</p>";
  a+='<details class="chk"><summary>'+esc(fmt(t("chkDetail"),{n:it.ledger.length}))+'</summary><div class="tbl"><table class="ledger">';
  a+="<thead><tr><th>"+esc(t("check"))+" ("+LL+")</th><th>"+esc(t("result"))+"</th><th>"+esc(t("finding"))+" ("+LL+")</th></tr></thead><tbody>";
  it.ledger.forEach(function(r){var st=r[2],res=st==="pass"?t("pass"):st==="fail"?t("fail"):t("na"),cls=st==="fail"?"FAIL":st==="pass"?"":"na";
   if(st==="fail"&&r[3].length&&r[3].every(function(f){return f.r})){res="~ "+t("fail");cls="FAILf"}
   var fd=r[3].map(function(f){var p="<p>"+esc(f.t)+(f.c&&it.corr_note?'<span class="cn">[≠] '+esc(it.corr_note)+"</span>":"")+"</p>";
    return f.r?'<details class="pf" title="'+esc(t("rd"+f.r))+'"><summary>'+esc(t("pf"))+" · "+esc(t("r"+f.r))+"</summary>"+p+"</details>":p}).join("");
   if(!fd&&st!=="fail")fd='<span class="na">—</span>';
   if(r[4])fd+="<details><summary>"+esc(t("raw"))+" · "+esc(fmt(t("intCode"),{c:r[5]}))+"</summary><div>"+esc(r[4])+"</div></details>";
   a+='<tr><td class="chk">'+esc(r[1])+'</td><td class="res '+cls+'">'+esc(res)+'</td><td class="fd" lang="'+L+'">'+fd+"</td></tr>"});
  a+="</tbody></table></div></details>"}
 a+="</div>";
 if(live){var d=dec(it)||{};
  a+='<div class="dec'+(L===focusL||langs(g).length<2?" focus":"")+'" data-lang="'+L+'" data-key="'+esc(it.key)+'"><div class="btns">'+
   [["accept","1 "+t("accept")],["accept-edited","2 "+t("acceptEd")],["send-back","3 "+t("sendBack")]].map(function(b){var off=b[0]==="accept-edited"&&S.edits[it.key]==null&&d.decision!=="accept-edited";
    return '<button class="box" type="button" data-d="'+b[0]+'" aria-pressed="'+(d.decision===b[0])+'"'+(off?' disabled aria-describedby="ae-'+esc(it.key)+'"':"")+">"+esc(b[1])+"</button>"}).join("")+"</div>"+
   '<span class="why2" id="ae-'+esc(it.key)+'"'+(S.edits[it.key]==null?"":" hidden")+">"+esc(t("noEdit2"))+"</span>"+
   "<label>"+esc(t("reason"))+'<select data-f="reason">'+t("reasons").map(function(r,i){var v=TX.en.reasons[i];return '<option value="'+esc(v)+'"'+(d.reason===v?" selected":"")+">"+esc(r||"—")+"</option>"}).join("")+"</select></label>"+
   "<label>"+esc(t("note"))+'<textarea data-f="note" lang="'+L+'">'+esc(d.note||"")+"</textarea></label>"+
   '<div class="stt" aria-live="polite">'+esc(d.decision?t("savedAt")+" · "+zshow(d.at)+(d.by?" · "+d.by:""):t("openSt"))+"</div></div>"}
 else a+="<div></div>";
 return a+"</article>"}
function caseHTML(g,live){var Ls=langs(g),one=Ls.length<2?" one":"",h="",nf=famSize(g.family);
 var keys=["fr","it"].filter(function(L){return g.items[L]}).map(function(L){return g.items[L].key}).join(", ");
 if(live)h+='<button class="tb back" type="button" data-back="1">← '+esc(t("backList"))+"</button>";
 h+="<h2>"+esc(g.product)+'</h2><p class="ref">'+esc(t("limitation"))+" "+esc(g.code)+" · "+esc(t("slAbbr"))+" "+esc(g.snap_old)+" → "+esc(g.snap_new)+" · "+esc(t("no"))+" "+g.no+" · "+
  esc(t("famOf"))+" "+esc(FAML[g.family]||g.family)+" · "+esc(nf===1?t("famChange1"):fmt(t("famChanges"),{n:nf}))+
  (live&&F.fam!==g.family&&nf>1?' · <button class="tb" type="button" data-fam="'+esc(g.family)+'">'+esc(t("famFilter"))+"</button>":"")+"</p>";
 h+='<section class="sec"><div class="sl"><span class="no">1</span><span class="t">'+esc(t("s1"))+"</span>"+(live?'<button class="tb sp" type="button" id="ctx">'+esc(ctxMode?t("ctxA"):t("ctxF"))+"</button>":"")+
  '</div><div class="txt de" lang="de">'+segs(g.de,live&&ctxMode,false)+"</div></section>";
 h+='<section class="sec"><div class="sl"><span class="no">2</span><span class="t">'+esc(t("s2"))+"</span>"+(live?'<button class="tb sp" type="button" id="slots" aria-pressed="'+SLOTS+'" title="'+esc(t("keyNum")[0])+'">'+esc(t("slotsT"))+"</button>":"")+
  '</div><div class="drafts'+one+'">'+Ls.map(function(L){return langHTML(g,L,live)}).join("")+"</div></section>";
 if(live){var ok=caseDecided(g);h+=dWhoHTML("d-rev")+'<div class="save"><button class="box primary" type="button" id="savenext"'+(ok?"":" disabled")+' aria-describedby="sn-why">'+esc(t("saveNext"))+'</button><span class="hint" id="sn-why">'+esc(ok?t("keys"):t("needDec"))+"</span></div>"}
 h+='<details class="ids"><summary>'+esc(t("ids"))+"</summary> "+esc(t("family"))+" "+esc(g.family)+(FAML[g.family]?" ("+esc(FAML[g.family])+")":"")+" · "+esc(t("pair"))+" "+esc(g.pair)+" · "+esc(t("itemsL"))+" "+esc(keys)+"</details>";
 return h}
function edmeta(key){var it=byKey[key],e=S.edits[key]!=null;
 return (e?"<span>"+esc(t("edited"))+'</span><button class="tb" type="button" data-reset="'+esc(key)+'">'+esc(t("reset"))+"</button>":"")+
  ((it.status!=="human"||e)?'<button class="tb" type="button" data-copy="'+esc(key)+'">'+esc(t("copyTxt"))+'</button><span class="cpmsg" aria-live="polite"></span>':"")+
  (it.rt&&it.rt[0]!==it.draft&&S.edits[key]!==it.rt[0]?'<button class="tb" type="button" data-start="'+esc(key)+'" title="'+esc(fmt(t("startOldT"),{n:it.rt[1]}))+'">'+esc(t("startOld"))+"</button>":"")+
  (it.rt&&S.edits[key]===it.rt[0]?"<span>"+esc(nT("startOldDone",it.rt[1]))+"</span>":"")}
function renderCase(){var c=$("case");if(!sel){c.innerHTML='<p class="empty">'+esc(t("none"))+"</p>";return}
 try{if(TAB==="drafts"&&decodeURIComponent(location.hash.slice(1))!==HP+sel.pair)history.replaceState(null,"","#"+HP+sel.pair)}catch(e){}
 var Ls=langs(sel);if(Ls.indexOf(focusL)<0)focusL=Ls[0];c.classList.toggle("slots",SLOTS);c.innerHTML=caseHTML(sel,true);wire(c)}
function copyText(s,ok,fail){var box=$("clipbox");
 function fallback(){try{box.value=s;box.select();if(document.execCommand&&document.execCommand("copy")){ok();return}}catch(e){}fail()}
 try{if(navigator.clipboard&&navigator.clipboard.writeText&&window.isSecureContext!==false){navigator.clipboard.writeText(s).then(ok,fallback)}else fallback()}catch(e){fallback()}}
function wire(c){
 var b=$("ctx");if(b)b.onclick=function(){ctxMode=!ctxMode;renderCase()};
 var sb=$("slots");if(sb)sb.onclick=function(){SLOTS=!SLOTS;c.classList.toggle("slots",SLOTS);sb.setAttribute("aria-pressed",SLOTS)};
 c.querySelectorAll(".ed").forEach(function(el){var key=el.dataset.key,it=byKey[key];
  el.addEventListener("keydown",function(e){if(e.key==="Enter"&&!(e.metaKey||e.ctrlKey))e.preventDefault()});
  el.addEventListener("paste",function(e){e.preventDefault();var tx=(e.clipboardData||window.clipboardData).getData("text").replace(/\s*\n\s*/g," ");document.execCommand("insertText",false,tx)});
  el.addEventListener("focus",function(){setFocus(it.lang)});
  el.addEventListener("input",function(){var v=readEd(el);if(v===it.draft||(it.status==="human"&&v===plain(it.segs,false)))delete S.edits[key];else S.edits[key]=v;save();
   var m=c.querySelector('[data-meta="'+key+'"]');if(m)m.innerHTML=edmeta(key);aeState(key)})});
 // the case container outlives each render: its delegated click handler is attached once (attached on every render, a
 // decision button fired once per render and an even count toggled the decision straight back off)
 if(!c.dataset.wired)c.dataset.wired="1",c.addEventListener("click",function(e){if(e.target.closest("[data-back]")){$("p-drafts").classList.remove("case-open");markSel(true);return}
  var r=e.target.closest("[data-reset]");if(r){delete S.edits[r.dataset.reset];var d=S.dec[r.dataset.reset];if(d&&d.decision==="accept-edited"){delete S.dec[r.dataset.reset]};save();renderCase();refreshRow(sel);progress();snState();return}
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
document.addEventListener("input",function(e){var i=e.target;if(!i.dataset||!i.dataset.drev)return;P.reviewer=i.value;lsSet("gleichlaut:prefs",P);
 if(who()){i.removeAttribute("aria-invalid");i.removeAttribute("aria-describedby");var q=$(i.id+"-ask");if(q)q.remove();var w=i.closest(".dwho");if(w)w.classList.remove("ask")}});
document.addEventListener("change",function(e){var i=e.target;if(!i.dataset||!i.dataset.drev||!who())return;
 if(DPEND)dApplyPend();if(i.id==="fam-rev"&&FPEND){var y=$("fam-yes");if(y)y.click()}});
var pend={},byKey={};ITEMS.forEach(function(it){byKey[it.key]=it});
// the reviewer's name, required before the first draft decision as in the audit tab: a decision clicked without it is kept
// (DPEND) and saved once the name is entered; the family action waits the same way (FPEND)
var DNAME=false,DPEND=null,FPEND=false;
function dWhoHTML(id){var ask=DNAME&&!who();return '<div class="who dwho'+(ask?" ask":"")+'"><label>'+esc(t("rev"))+' <input type="text" id="'+id+'" data-drev="1" autocomplete="name" value="'+esc(P.reviewer||"")+'" placeholder="'+esc(t("revPh"))+'"'+
 (ask?' aria-invalid="true" aria-describedby="'+id+'-ask"':"")+"></label>"+(ask?'<p class="aname" id="'+id+'-ask" role="alert">'+esc(t("aNameAsk"))+"</p>":"")+"</div>"}
function dWhoRefresh(){document.querySelectorAll(".dwho").forEach(function(w){var i=w.querySelector("input");if(!i)return;var tmp=document.createElement("div");tmp.innerHTML=dWhoHTML(i.id);w.replaceWith(tmp.firstChild)})}
function dApplyPend(){var p=DPEND;DPEND=null;DNAME=false;dWhoRefresh();document.querySelectorAll(".dec button.pend").forEach(function(b){b.classList.remove("pend")});
 if(p&&who()&&sel&&sel.items[p.L]&&sel.items[p.L].key===p.k)decide(p.L,p.v)}
// a record time as the reviewer reads it: Europe/Zurich with its offset (2026-10-11 01:45 +02:00)
function zshow(x){var z=zts(x);return z.length>=25?z.slice(0,10)+" "+z.slice(11,16)+" "+z.slice(19):z}
// "2 Accept edited" waits for an edit of the draft text; its reason sits under the buttons
function aeState(key){var dv=document.querySelector('.dec[data-key="'+key+'"]');if(!dv)return;var b=dv.querySelector('button[data-d="accept-edited"]'),w=dv.querySelector(".why2"),ed=S.edits[key]!=null,d=dec(byKey[key]);
 if(b){b.disabled=!ed&&!(d&&d.decision==="accept-edited");if(b.disabled)b.setAttribute("aria-describedby","ae-"+key);else b.removeAttribute("aria-describedby")}if(w)w.hidden=ed}
function setFocus(L){if(!sel||!sel.items[L]||langs(sel).indexOf(L)<0)return;focusL=L;document.querySelectorAll(".dec").forEach(function(d){d.classList.toggle("focus",d.dataset.lang===L)})}
function decide(L,v){var it=sel&&sel.items[L];if(!it)return;var dv=document.querySelector('.dec[data-lang="'+L+'"]'),k=it.key;
 if(v==="accept-edited"&&S.edits[k]==null&&!(S.dec[k]&&S.dec[k].decision==="accept-edited")){var st=dv.querySelector(".stt");st.textContent=t("noEdit2");var ed=document.querySelector('.ed[data-key="'+k+'"]');if(ed)ed.focus();return}
 if(!who()){if(!DPEND)DPEND={k:k,L:L,v:v};DNAME=true;dWhoRefresh();var pb=dv.querySelector('button[data-d="'+DPEND.v+'"]');if(pb&&DPEND.k===k)pb.classList.add("pend");
  dv.querySelector(".stt").textContent=t("aNameAsk");var ni=$("d-rev");if(ni)ni.focus();return}
 if(DPEND){var p0=DPEND;DPEND=null;DNAME=false;dWhoRefresh();if(!(p0.k===k&&p0.v===v)&&sel.items[p0.L]&&sel.items[p0.L].key===p0.k)decide(p0.L,p0.v)}
 var cur=S.dec[k],undone=false;if(cur&&cur.decision===v){delete S.dec[k];undone=true}
 else{var reason=dv.querySelector('[data-f="reason"]').value,note=dv.querySelector('[data-f="note"]').value;
  S.dec[k]={decision:v,lang:L,status:it.status,edited:S.edits[k]!=null,text:v==="accept-edited"?S.edits[k]:(it.status==="human"?null:it.draft),reason:reason,note:note,at:zts(),by:who()}}
 delete pend[k];save();
 dv.querySelectorAll("button[data-d]").forEach(function(b){b.setAttribute("aria-pressed",!!S.dec[k]&&S.dec[k].decision===b.dataset.d)});
 dv.querySelectorAll("button.pend").forEach(function(b){b.classList.remove("pend")});
 dv.querySelector(".stt").textContent=S.dec[k]?t("savedAt")+" · "+zshow(S.dec[k].at)+(S.dec[k].by?" · "+S.dec[k].by:""):undone?t("undone"):t("openSt");refreshRow(sel);progress();snState();aeState(k)}
// "save, next" moves on once the change shown has a decision (in one of its languages); j / ↓ skip without deciding
function caseDecided(g){return !!g&&langs(g).some(function(L){return !!dec(g.items[L])})}
function snState(){var b=$("savenext"),w=$("sn-why");if(!b)return;var ok=caseDecided(sel);b.disabled=!ok;if(w)w.textContent=ok?t("keys"):t("needDec")}
function saveNext(){if(!caseDecided(sel)){snState();return}save();var old=sel,i=VIS.indexOf(old);renderReg();var j=VIS.indexOf(old);
 sel=j>=0?(VIS[j+1]||old):(VIS[Math.max(0,i)]||VIS[VIS.length-1]||null);markSel(true);renderCase();var c=$("case");if(c.getBoundingClientRect().top<0)c.scrollIntoView()}
// ------------------------------------------------------------------ keyboard (drafts tab)
document.addEventListener("keydown",function(e){if(TAB!=="drafts")return;var tg=e.target,typing=tg.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(tg.tagName);
 if(e.key==="Enter"&&(e.metaKey||e.ctrlKey)){e.preventDefault();saveNext();return}
 if(e.key==="Escape"&&typing){tg.blur();return}
 if(typing||e.altKey||e.metaKey||e.ctrlKey)return;
 if(tg.closest&&tg.closest(".views"))return;
 var k=e.key;
 if(k==="j"||k==="ArrowDown"){e.preventDefault();move(1)}else if(k==="k"||k==="ArrowUp"){e.preventDefault();move(-1)}
 else if(k==="Enter"&&tg.closest&&!tg.closest("button,a,summary")){e.preventDefault();$("case").focus();$("case").scrollIntoView({block:"start"})}
 else if(k==="f"||k==="i"){setFocus(k==="f"?"fr":"it")}
 else if(k==="1"||k==="2"||k==="3"){if(sel){var L=langs(sel).indexOf(focusL)>=0?focusL:langs(sel)[0];decide(L,["accept","accept-edited","send-back"][+k-1])}}});
// ------------------------------------------------------------------ export / import
function payload(){return {run:M.run,model:M.model,pipeline:M.pipeline,run_sha256:M.run_sha256,items_sha256:M.items_sha256,exported_at:zts(),
 reviewer:who(),ui_lang:UL,decisions:S.dec,edits:S.edits,audit_date:AU?AU.meta.date:null,audit:SA,audit_rows:auditExport(),audit_issues:AU?auditIssues():[]}}
function download(name,text,type){var u=URL.createObjectURL(new Blob([text],{type:type})),a=document.createElement("a");a.href=u;a.download=name;document.body.appendChild(a);a.click();
 setTimeout(function(){URL.revokeObjectURL(u);a.remove()},500)}
function x(s){return esc(s).replace(/'/g,"&apos;")}
function inl(s,a,b,spans,open){var out="",pos=a;(spans||[]).forEach(function(sp){var p=Math.max(sp[0],a),q=Math.min(sp[1],b);if(p>=q||p<pos)return;
  out+=x(s.slice(pos,p))+open(sp)+x(s.slice(p,q))+"</mrk>";pos=q});return out+x(s.slice(pos,b))}
function note(id,cat,ap,pr,text){return '<note id="'+id+'" category="'+cat+'"'+(ap?' appliesTo="'+ap+'"':"")+' priority="'+pr+'">'+x(text)+"</note>"}
// sentence segments of an edited target: emit/segment.py ported (sentences, align, merge_short; the same costs and
// tie-breaks, so an edited unit gets the segments the Python writers give it: tests/test_ui_browser.py compares them)
var SEG_END=/[.;:!?](\s+)(?=[A-ZÄÖÜÀÂÉÈÊÎÔÛÇ0-9(«"–-])/g,
 SEG_ABBR=/(?:(?<!\p{L})(?:\p{L}\.\s?){1,3}\p{L}\.|(?<![\p{L}\p{N}_.])(?:z\.\s?Bsp|p\.\s?ex|ad\s+es|bzw|resp|vgl|inkl|bspw|evtl|ggf|sog|med|Dr|Prof|St|od|cf|cfr|env|ecc|ev|Ev)\.)$/u,
 SEG_ABBR_NUM=/(?<![\p{L}\p{N}_.])(?:ca|Nr|nr|Art|art|Abs|al|cpv|Fr|max|mind|min|Ziff|ch|n°|No|no|Kap)\.$/u,
 SEG_BEADS=[[1,1,0],[1,2,1.2],[2,1,1.2],[2,2,1.8],[1,3,2.4],[3,1,2.4]];
function segAbbr(s,m){if(s[m.index]!==".")return false;var head=s.slice(0,m.index+1),tail=s.slice(m.index+m[0].length);
 if(/(?<!\p{L})\p{L}\.$/u.test(head)&&/^(?:\p{L}|Bsp|ex)\./u.test(tail))return true;
 return SEG_ABBR.test(head)||(SEG_ABBR_NUM.test(head)&&/^\d/.test(tail))}
function segSent(s){var out=[],a=0,m;SEG_END.lastIndex=0;while((m=SEG_END.exec(s))){if(segAbbr(s,m))continue;var e=m.index+m[0].length;out.push([a,e]);a=e}
 if(a<s.length||!out.length)out.push([a,s.length]);return out}
function segNums(s){var o={};(s.match(/\d+(?:[.,'’]\d+)*/g)||[]).forEach(function(x){o[x.replace(/[.,'’]/g,".")]=1});return o}
function segAlign(src,tgt){var S=segSent(src),T=segSent(tgt);if(!tgt.trim()||!src.trim())return [[0,src.length,0,tgt.length]];
 var r=Math.max(1,tgt.length)/Math.max(1,src.length),n=S.length,m=T.length,best=[],back=[],i,j;
 for(i=0;i<=n;i++){best.push([]);back.push([]);for(j=0;j<=m;j++){best[i].push(Infinity);back[i].push(null)}}best[0][0]=0;
 for(i=0;i<=n;i++)for(j=0;j<=m;j++){if(best[i][j]===Infinity)continue;
  SEG_BEADS.forEach(function(B){var di=B[0],dj=B[1];if(i+di>n||j+dj>m)return;var a0=S[i][0],a1=S[i+di-1][1],b0=T[j][0],b1=T[j+dj-1][1];
   var ls=src.slice(a0,a1).trim().length,lt=tgt.slice(b0,b1).trim().length,A=segNums(src.slice(a0,a1)),Bn=segNums(tgt.slice(b0,b1)),x=0,k;
   for(k in A)if(!Bn[k])x++;for(k in Bn)if(!A[k])x++;
   var cost=3*Math.abs(Math.log((lt+1)/(r*ls+1)))+B[2]+x;
   if(best[i][j]+cost<best[i+di][j+dj]){best[i+di][j+dj]=best[i][j]+cost;back[i+di][j+dj]=[i,j]}})}
 if(best[n][m]===Infinity)return [[0,src.length,0,tgt.length]];
 var out=[];i=n;j=m;while(i||j){var p=back[i][j];out.push([S[p[0]][0],S[i-1][1],T[p[1]][0],T[j-1][1]]);i=p[0];j=p[1]}return out.reverse()}
function segShort(t){t=t.trim();return t.length<20||!/\p{L}{2,}/u.test(t)}
function segBeads(src,tgt){var out=segAlign(src,tgt),k=0;
 while(out.length>1&&k<out.length){var b=out[k];
  if(segShort(src.slice(b[0],b[1]))||segShort(tgt.slice(b[2],b[3]))){if(k===0){var nx=out[1];out.splice(0,2,[b[0],nx[1],b[2],nx[3]])}else{var pv=out[k-1];out.splice(k-1,2,[pv[0],b[1],pv[2],b[3]]);k--}continue}
  k++}return out}
function xliff(L){var trg=L==="fr"?"fr-CH":"it-CH",u=[],X=D.xn[L],nd=0,colon=L==="fr"?" : ":": ";
 ITEMS.forEach(function(it){if(it.lang!==L)return;var g=it.g,d=dec(it)||null,st=it.status==="human"?["initial","gleichlaut:human"]:["translated","gleichlaut:"+it.status],text=it.status==="human"?null:it.draft,edited=false;
  var acc=d&&(d.decision==="accept"||d.decision==="accept-edited")&&(it.status!=="human"||d.text),back=d&&d.decision==="send-back";
  if(acc){st=["reviewed",d.decision==="accept-edited"?"gleichlaut:accepted-edited":"gleichlaut:accepted"];
   if(d.decision==="accept-edited"&&d.text){text=d.text;edited=true}}
  else if(back){st=["initial","gleichlaut:sent-back"];text=null}          // a sent-back draft is never a pre-translation
  if(d)nd++;
  // the unit notes of emit/xliff.py (verdict, at most three plain reasons, change), the old texts, then the one low-priority checks note
  var prev=note("de-old","context:previous-source","source",5,fmt(X.prev_de,{t:g.deOld}).replace(" : ",colon))+
   note("tgt-old","context:previous-target","target",5,fmt(X.prev_tgt,{t:plain(it.segs,true)}).replace(" : ",colon)),notes="";
  if(acc)notes+=note("verdict","gleichlaut:verdict","target",1,X.accepted[it.status]||X.accepted.flagged);
  if(back){notes+=note("verdict","gleichlaut:verdict",null,1,X.sent_back);if(it.draft)notes+=note("rejected","gleichlaut:rejected-draft",null,2,X.rejected.replace("{t}",it.draft))}
  // a signed-off unit keeps no note about the draft it replaced (emit/xliff.py SIGNED_KEEP): the German change and the old texts only
  it.xn.forEach(function(n){if((acc||back)&&n[0]==="verdict")return;if(acc&&n[0]!=="change")return;if(n[0]==="checks"||n[0]==="termbase"||n[0]==="notes"){notes+=prev;prev=""}notes+=note(n[0],n[1],n[2],n[3],n[4])});notes+=prev;
  if(d){var why=[X.reasons[d.reason]||d.reason,d.note].filter(Boolean).join("; ");notes+=note("review","gleichlaut:review","target",1,fmt(X.review,{d:X.dec[d.decision]||d.decision}).replace(" : ",colon)+" ("+zts(d.at)+")"+(why?colon+why:""))}
  var src=g.deNew,beads=text==null?it.bd.map(function(b){return [b[0],b[1],0,0]}):edited?segBeads(src,text):it.bd,nums=edited?[]:it.nm,c=0,n=0,sx="";
  beads.forEach(function(b,k){sx+='<segment id="s'+(k+1)+'" state="'+st[0]+'" subState="'+st[1]+'"><source>'+inl(src,b[0],b[1],g.ch,function(){c++;return '<mrk id="c'+c+'" type="gleichlaut:changed">'})+"</source>"+
   (text!=null?"<target>"+inl(text,b[2],b[3],nums,function(sp){n++;var code=sp[2]!=="model";return '<mrk id="t'+n+'"'+(code?' translate="no"':"")+' type="gleichlaut:'+(code?"code":"model")+'-number"'+(sp[3]?' value="'+x(sp[3])+'"':"")+">"})+"</target>":"")+"</segment>"});
  u.push('<unit id="'+x(it.key)+'" name="'+x(it.cud)+'"><notes>'+notes+"</notes>"+sx+"</unit>")});
 return '<?xml version="1.0" encoding="UTF-8"?>\n<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" version="2.1" srcLang="de-CH" trgLang="'+trg+'"><file id="f1" original="gleichlaut:'+x(M.run)+'">'+
  "<notes>"+note("about","gleichlaut:about",null,1,X.about).replace(' priority="1"',"")+note("states","gleichlaut:states",null,1,X.states).replace(' priority="1"',"")+
  note("provenance","gleichlaut:provenance",null,1,X.prov).replace(' priority="1"',"")+note("review","gleichlaut:review",null,1,fmt(nd===1?X.reviewed1:X.reviewed,{n:nd})+" · "+zts()).replace(' priority="1"',"")+
  "</notes>"+u.join("")+"</file></xliff>\n"}
function note12(ap,pr,text,frm){return '<note from="'+(frm||"gleichlaut")+'" annotates="'+(ap||"general")+'" priority="'+pr+'">'+x(text)+"</note>"}
// XLIFF 1.2 (strict) with the reviewer's decisions: the segments of the 2.1 export as <seg-source>/<target> <mrk mtype="seg">,
// accepted -> state signed-off approved=yes (edited text replaces the draft), sent back -> needs-translation (as emit/xliff12.py
// otherwise: ready translated, flagged needs-review-translation, no draft -> no target).
function xliff12(L){var trg=L==="fr"?"fr-CH":"it-CH",u=[],X=D.xn[L],nd=0,colon=L==="fr"?" : ":": ",ST={ready:"translated",flagged:"needs-review-translation"};
 var prot=function(){return '<mrk mtype="protected" comment="'+x(X.code_number)+'">'};
 ITEMS.forEach(function(it){if(it.lang!==L)return;var g=it.g,d=dec(it)||null,text=it.status==="human"?null:it.draft,edited=false,state=ST[it.status],appr="no";
  var acc=d&&(d.decision==="accept"||d.decision==="accept-edited")&&(it.status!=="human"||d.text),back=d&&d.decision==="send-back";
  if(acc){state="signed-off";appr="yes";if(d.decision==="accept-edited"&&d.text){text=d.text;edited=true}}
  else if(back)state="needs-translation";
  if(d)nd++;
  var src=g.deNew,beads=text==null?it.bd.map(function(b){return [b[0],b[1],0,0]}):edited?segBeads(src,text):it.bd,code=edited?[]:it.nm.filter(function(n){return n[2]!=="model"});
  var outer=g.ch.map(function(c){return [c[0],c[1],"c"]}).concat(g.sn.filter(function(n){return !g.ch.some(function(c){return c[0]<=n[0]&&n[1]<=c[1]})}).map(function(n){return [n[0],n[1],"n"]})).sort(function(p,q){return p[0]-q[0]});
  function sm(a,b){var out="",pos=a;outer.forEach(function(sp){var p=Math.max(sp[0],a),q=Math.min(sp[1],b);if(p>=q||p<pos)return;out+=x(src.slice(pos,p));
    out+=sp[2]==="n"?prot()+x(src.slice(p,q))+"</mrk>":'<mrk mtype="x-changed" comment="'+x(X.changed)+'">'+inl(src,p,q,g.sn,prot)+"</mrk>";pos=q});return out+x(src.slice(pos,b))}
  var h='<trans-unit id="'+x(it.key)+'" resname="'+x(it.cud)+'" approved="'+appr+'" xml:space="preserve"><source xml:lang="de-CH">'+sm(0,src.length)+"</source>"+
   '<seg-source xml:lang="de-CH">'+beads.map(function(b,k){return '<mrk mtype="seg" mid="'+(k+1)+'">'+sm(b[0],b[1])+"</mrk>"}).join("")+"</seg-source>";
  if(back)h+='<target state="needs-translation" xml:lang="'+trg+'"></target>';      // empty: the rejected draft is in alt-trans
  else if(text!=null)h+='<target state="'+state+'" xml:lang="'+trg+'">'+beads.map(function(b,k){return '<mrk mtype="seg" mid="'+(k+1)+'">'+inl(text,b[2],b[3],code,prot)+"</mrk>"}).join("")+"</target>";
  if(acc)h+=note12("target",1,X.accepted[it.status]||X.accepted.flagged);
  if(back)h+=note12("general",1,X.sent_back);
  var prev12=note12("source",5,fmt(X.prev_de,{t:g.deOld}).replace(" : ",colon))+note12("target",5,fmt(X.prev_tgt,{t:plain(it.segs,true)}).replace(" : ",colon));
  it.xn.forEach(function(n){if((acc||back)&&n[0]==="verdict")return;if(acc&&n[0]!=="change")return;if(n[0]==="checks"||n[0]==="termbase"||n[0]==="notes"){h+=prev12;prev12=""}h+=note12(n[2],n[3],n[4],n[0]==="checks"?"gleichlaut-checks":"gleichlaut")});h+=prev12;
  if(d){var why=[X.reasons[d.reason]||d.reason,d.note].filter(Boolean).join("; ");h+=note12("target",1,fmt(X.review,{d:X.dec[d.decision]||d.decision}).replace(" : ",colon)+" ("+zts(d.at)+(d.by?", "+d.by:"")+")"+(why?colon+why:""))}
  if(back&&it.draft)h+='<alt-trans alttranstype="rejected" origin="Gleichlaut draft, sent back on review" tool-id="gleichlaut"><target xml:lang="'+trg+'">'+x(it.draft)+"</target></alt-trans>";
  h+='<alt-trans alttranstype="previous-version" origin="SL previous version" tool-id="gleichlaut"><source xml:lang="de-CH">'+x(g.deOld)+'</source><target xml:lang="'+trg+'">'+x(plain(it.segs,true))+"</target></alt-trans></trans-unit>";
  u.push(h)});
 return '<?xml version="1.0" encoding="UTF-8"?>\n<xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2"><file original="gleichlaut:'+x(M.run)+'" source-language="de-CH" target-language="'+trg+'" datatype="plaintext" tool-id="gleichlaut">'+
  '<header><tool tool-id="gleichlaut" tool-name="Gleichlaut" tool-company="Gleichlaut"/><note from="gleichlaut">'+x(X.about12)+'</note><note from="gleichlaut">'+x(X.states12)+'</note><note from="gleichlaut">'+x(X.prov)+"</note>"+
  '<note from="gleichlaut">'+x(fmt(nd===1?X.reviewed1:X.reviewed,{n:nd})+" · "+zts())+"</note></header><"+"body>"+u.join("")+"</"+"body></file></xliff>\n"}
function msg(s){$("x-msg").textContent=s}
$("x-xlf").onclick=function(){var Ls=F.lang==="all"?["fr","it"]:[F.lang];Ls=Ls.filter(function(L){return ITEMS.some(function(it){return it.lang===L})});
 Ls.forEach(function(L,i){setTimeout(function(){download("gleichlaut-"+M.run+"-de-CH_"+(L==="fr"?"fr-CH":"it-CH")+"-reviewed.xlf",xliff(L),"application/xliff+xml")},i*400)});
 msg(t("dl")+": "+Ls.map(function(L){return "XLIFF 2.1 "+L.toUpperCase()}).join(", "))};
$("x-xlf12").onclick=function(){var Ls=F.lang==="all"?["fr","it"]:[F.lang];Ls=Ls.filter(function(L){return ITEMS.some(function(it){return it.lang===L})});
 Ls.forEach(function(L,i){setTimeout(function(){download("gleichlaut-"+M.run+"-de-CH_"+(L==="fr"?"fr-CH":"it-CH")+"-reviewed.xliff12.xlf",xliff12(L),"application/xliff+xml")},i*400)});
 msg(t("dl")+": "+Ls.map(function(L){return "XLIFF 1.2 "+L.toUpperCase()}).join(", "))};
// the one decisions export (draft and audit decisions, edits): the page keeps them only in this browser
// from the audit tab the audit decisions go to a file of their own, named by the SL snapshot audited; from the drafts tab
// the drafts' decisions and edits, named by the lane's run
function auditPayload(){return {audit_date:AU?AU.meta.date:null,exported_at:zts(),reviewer:who(),ui_lang:UL,rev:M.rev||"",audit:SA,audit_rows:auditExport(),audit_issues:AU?auditIssues():[]}}
function draftsPayload(){var p=payload();["audit_date","audit","audit_rows","audit_issues"].forEach(function(k){delete p[k]});return p}
function decFile(){return TAB==="audit"&&AU?["gleichlaut-audit-decisions-"+AU.meta.date+".json",auditPayload()]:["gleichlaut-decisions-"+M.run+".json",draftsPayload()]}
$("x-dec").onclick=function(){var f=decFile();download(f[0],JSON.stringify(f[1],null,1),"application/json");var b=$("x-dec");b.textContent=t("dl")+": "+f[0];
 setTimeout(function(){b.textContent=t(TAB==="audit"?"exportDecA":"exportDec")},2500)};
$("x-copy").onclick=function(){var s=JSON.stringify(draftsPayload(),null,1),box=$("copybox");
 function fallback(){box.hidden=false;box.value=s;box.focus();box.select();msg(t("selcopy"))}
 try{if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(s).then(function(){box.hidden=true;msg(t("copied"))},fallback)}else fallback()}catch(e){fallback()}};
// one file or several (colleagues' exports): merged with what this browser holds, the newest decision per item wins (by its
// time stamp); items whose files disagree are named
function importDecisions(o){var L=Array.isArray(o)?o:[o],nd={},na={},note="",conf=[],bad=0,dd={},ds={};
 function newer(a,b){return !b||tms(a&&a.at)>=tms(b.at)}
 function same(a,b){return JSON.stringify([a.decision||"",a.text||"",a.right||"",aActs(a).slice().sort()])===JSON.stringify([b.decision||"",b.text||"",b.right||"",aActs(b).slice().sort()])}
 var bySig={},byRid={};allRows().forEach(function(r){bySig[r.sig]=r;byRid[r.rid]=r.sig});
 L.forEach(function(o){if(!o||typeof o!=="object"||!(o.decisions||o.audit)){bad++;return}
  if(o.decisions){if(o.run_sha256&&o.run_sha256!==M.run_sha256)note=" "+t("impRun");
   else{Object.keys(o.decisions).forEach(function(k){if(!byKey[k])return;var d=o.decisions[k],c=dd[k];if(c&&!same(c,d)&&conf.indexOf(k)<0)conf.push(k);
     if(newer(d,c)){dd[k]=d;if(o.edits&&o.edits[k]!=null)S.edits[k]=o.edits[k]}});
    Object.keys(o.edits||{}).forEach(function(k){if(byKey[k]&&!dd[k])S.edits[k]=o.edits[k]})}}
  if(o.audit&&AU)Object.keys(o.audit).forEach(function(k){var sg=bySig[k]?k:(!o.audit_date||o.audit_date===AU.meta.date)?byRid[k]:null;if(!sg)return;var d=o.audit[k];
   if(d&&ACTMAP[d.action])d.action=ACTMAP[d.action];if(d&&(d.remedy!=null||d.wrong))aDerive(d);if(d&&!d.date)d.date=o.audit_date||AU.meta.date;var c=ds[sg],r=bySig[sg];
   if(c&&!same(c,d)){var lab=(r&&r.I?r.I.iid:"")+(r&&r.no?" "+r.no:"");if(conf.indexOf(lab)<0)conf.push(lab)}if(newer(d,c))ds[sg]=d})});
 if(bad===L.length)return t("impBad");
 Object.keys(dd).forEach(function(k){if(newer(dd[k],S.dec[k])){S.dec[k]=dd[k]}nd[k]=1});save();
 if(AU){Object.keys(ds).forEach(function(k){if(newer(ds[k],SA[k]))SA[k]=ds[k];na[k]=1});saveA();aMigrate()}
 // a fresh browser takes the reviewer's name from the file (its reviewer, else the newest decision's "by")
 var nm="";if(!who()){L.forEach(function(o){if(o&&typeof o.reviewer==="string"&&o.reviewer.trim())nm=o.reviewer.trim()});
  if(!nm){var bst=null;[ds,dd].forEach(function(D){Object.keys(D).forEach(function(k){var d=D[k];if(d&&d.by&&(!bst||tms(d.at)>=tms(bst.at)))bst=d})});if(bst)nm=String(bst.by).trim()}
  if(nm){P.reviewer=nm;lsSet("gleichlaut:prefs",P);ANAME=false}}
 var n1=Object.keys(nd).length,n2=Object.keys(na).length;
 return (L.length>1?fmt(t("impMerged"),{k:L.length,d:n1,a:n2}):fmt(t("imported"),{d:n1,a:n2}))+(conf.length?" "+fmt(t("impConf"),{x:conf.join(", ")}):"")+note+(nm?" "+fmt(t("impName"),{n:nm}):"")}
function pickImport(target){var f=$("imp-file");f.value="";f.onchange=function(){var fs=Array.prototype.slice.call(f.files||[]);if(!fs.length)return;var out=[],left=fs.length;
 function done(){var m;try{m=importDecisions(out.length===1?out[0]:out)}catch(e){m=t("impBad")}$(target).textContent=m;chrome();if(TAB==="audit")renderAudit();else{renderReg();renderCase()}}
 fs.forEach(function(file){var rd=new FileReader();rd.onload=function(){try{out.push(JSON.parse(rd.result))}catch(e){out.push(null)}if(--left===0)done()};rd.readAsText(file)})};f.click()}
$("x-imp").onclick=function(){pickImport("x-msg")};$("a-imp").onclick=function(){pickImport("a-msg")};
// ------------------------------------------------------------------ print: one case per page (drafts tab)
window.addEventListener("beforeprint",function(){if(TAB==="drafts")$("print").innerHTML=VIS.map(function(g){return '<article class="pcase">'+caseHTML(g,false)+"</article>"}).join("")});
window.addEventListener("afterprint",function(){$("print").innerHTML=""});
function fromHash(){var h=decodeURIComponent(location.hash.slice(1));if(laneOf(h)!==LANE){location.reload();return false}h=hashRest(h);if(h==="audit"&&AU){TAB="audit";return true}
 if(h==="drafts"){TAB="drafts";return true}
 var g=G.filter(function(g){return g.pair===h||g.no===h})[0];
 if(g){TAB="drafts";if(F.fam&&F.fam!==g.family){F.fam="";famAsk=false;famMsg=""}if(F.q){F.q="";$("f-q").value=""}if(!langs(g).length)F.lang="all";
  if(!(langs(g).some(function(L){return okItem(g.items[L])})))F.status="all";sel=g;return true}return false}
var fromLink=fromHash()&&TAB==="drafts"&&!!sel;chrome();if(TAB==="audit")renderAudit();else{renderReg();if(sel){markSel(true);renderCase()}}
if(fromLink)setTimeout(function(){var c=$("case");if(c&&c.getBoundingClientRect().top<64)c.scrollIntoView({block:"start"})},0);
window.GleichlautReview={xliff:xliff,xliff12:xliff12,segBeads:segBeads,payload:payload,auditPayload:auditPayload,draftsPayload:draftsPayload,decFile:decFile,importDecisions:importDecisions,setTab:setTab,auditCsv:auditCsv,findingsCsv:findingsCsv};
window.addEventListener("hashchange",function(){if(fromHash()){setTab(TAB);var c=$("case");if(TAB==="drafts"&&c&&c.getBoundingClientRect().top<64)c.scrollIntoView({block:"start"})}});
})();
</script>
"""
