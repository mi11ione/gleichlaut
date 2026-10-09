"""The review page template (HEAD = title + style, BODY = content + data + script), filled in by build.py.
No external request: fonts are inlined by build.fonts_css(), data by build.build()."""

HEAD = r"""<title>Gleichlaut Review</title>
<style>
__FONTS__
/* LAYOUT. One ruled sheet (max-width 1320px, centred; side gutter via padding-inline, padding-block only), 5px Swiss-red
   rule on top. 1 header: title + mono subtitle, then a two-column key-value block between two black rules.
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
.kv{display:grid;grid-template-columns:1fr 1fr;gap:0 32px;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);margin-top:16px;padding-block:8px}
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
#reg tr:hover td{background:color-mix(in srgb,var(--ink) 5%,transparent)}
#reg tr[aria-selected=true] td{background:var(--sel);color:var(--sel-ink)}
#reg tr[aria-selected=true] .mk.r{color:var(--sel-ink);text-decoration:underline}
.mk{letter-spacing:-.02em}.mk.r{color:var(--red);font-weight:500}.mk.o{color:var(--ink2)}
.count{color:var(--ink2);padding:6px 0}
.export{display:flex;flex-wrap:wrap;gap:8px;padding:10px 0 12px;border-top:1px solid var(--rule)}
.export .msg{color:var(--ink2);flex-basis:100%}
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
footer{border-top:1px solid var(--rule);margin-top:28px;padding-top:8px;color:var(--ink2)}
footer p{margin:2px 0;overflow-wrap:anywhere}
#print{display:none}
[hidden]{display:none!important}
@media (max-width:900px){
 .work{grid-template-columns:minmax(0,1fr)}
 .register{position:static;max-height:none;border-right:0;padding-right:0;border-bottom:1px solid var(--rule)}
 .reg-wrap{max-height:46vh}
 #reg{min-width:0}#reg col.c-mark{width:70px}#reg col.c-no{width:38px}
 .kv{grid-template-columns:1fr}
 .drafts,.decs{grid-template-columns:1fr}
 .dr{padding-right:0}.dr+.dr{border-left:0;border-top:1px solid var(--hair);padding:12px 0 0;margin-top:12px}
 h1{font-size:30px}
}
@media print{
 @page{size:A4;margin:14mm}
 body{border-top:0;font-size:10pt;background:#fff;color:#000}
 .register,.tools,.save,.export,.edmeta,.btns,.dec select,.dec textarea,#case{display:none!important}
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
   <label><span id="l-ui"></span> <select id="ui-lang" aria-label="Interface language"><option value="en">EN</option><option value="fr">FR</option><option value="it">IT</option></select></label></div>
 </div>
 <div class="kv"><dl id="kv-l"></dl><dl id="kv-r"></dl></div>
</header>
<div class="work">
 <section class="register" id="register" aria-label="Register">
  <div class="filters">
   <div class="fl" id="f-status"></div>
   <div class="fl" id="f-lang"></div>
   <div class="fl"><select id="f-fam" aria-label="Family"></select><input type="search" id="f-q" aria-label="Search product or limitation code"></div>
  </div>
  <div class="tbl reg-wrap" id="reg-wrap"><table id="reg"><colgroup><col class="c-mark"><col class="c-no"><col class="c-prod"><col></colgroup>
   <thead><tr><th id="h-mark"></th><th id="h-no"></th><th id="h-prod"></th><th id="h-chg"></th></tr></thead><tbody></tbody></table></div>
  <div class="count" id="shown"></div>
  <div class="export"><button class="box" id="x-xlf" type="button"></button><button class="box" id="x-json" type="button"></button><button class="box" id="x-copy" type="button"></button>
   <span class="msg" id="x-msg" aria-live="polite"></span><textarea id="copybox" hidden readonly aria-label="Decisions JSON"></textarea></div>
 </section>
 <section class="case" id="case" tabindex="-1" aria-label="Case"></section>
</div>
<footer><p id="prov"></p><p id="legend"></p></footer>
</div>
<div id="print" class="sheet"></div>
<script type="application/json" id="data">__DATA__</script>
<script>
(function(){
"use strict";
var D=JSON.parse(document.getElementById("data").textContent),M=D.meta,A=D.all,G=D.groups;
var LK="gleichlaut:"+M.run+":"+M.run_sha256.slice(0,12);
function lsGet(k,d){try{var v=localStorage.getItem(k);return v==null?d:JSON.parse(v)}catch(e){return d}}
function lsSet(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}
var S=lsGet(LK+":state",null)||{dec:{},edits:{}};S.dec=S.dec||{};S.edits=S.edits||{};
var P=lsGet("gleichlaut:prefs",{})||{};
function save(){lsSet(LK+":state",S)}
function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}
function $(id){return document.getElementById(id)}
// ------------------------------------------------------------------ interface strings (EN / FR / IT)
var TX={
en:{ui:"UI",sub:"Review register",drafts:"drafts",model:"Model",run:"Run",guards:"Guards",items:"Items",changes:"Changes",ready:"Ready",flagged:"Flagged",
 exact:"Exact vs rules-only",rule:"Pre-registered rule",human:"Routed to a translator",divergent:"Previous text diverges",decided:"decided",
 status:"Status",language:"Language",open:"Open",all:"All",decidedF:"Decided",divF:"Divergent",allFam:"All families",search:"Product or code",
 mark:"Mark",no:"No.",product:"Product",change:"Change",shown:"changes shown",xlf:"Export XLIFF 2.1",json:"Export JSON",copy:"Copy decisions",
 copied:"Decisions copied to the clipboard.",selcopy:"Clipboard blocked: the JSON is selected below, copy it with Ctrl/Cmd+C.",dl:"Downloaded",
 s1:"German change",s2:"Drafts",s3:"Checks",s4:"Decision",ctxA:"Context: around changes",ctxF:"Context: full text",fr:"French",it:"Italian",
 lready:"ready",lflagged:"flagged",lhuman:"routed to a translator",edited:"edited",reset:"Reset to draft",editHint:"Click the text to edit it in place.",
 check:"Check",result:"Result",finding:"Finding",pass:"pass",fail:"FAIL",na:"n/a",raw:"technical detail",noChecks:"No checks: no machine draft.",
 accept:"Accept",acceptEd:"Accept edited",sendBack:"Send back",reason:"Reason",note:"Note (why)",saveNext:"Save, next",keys:"keys 1/2/3 decide · f/i language · Ctrl/Cmd+Enter save, next",
 savedAt:"saved",openSt:"open",noEdit:"Edit the draft text first (click into it).",
 humanTxt:"Routed to a translator: the German was rewritten by more than 60%",humanShort:"Routed to a translator, no machine draft",humanPrev:"Previous text (edit it in place to write the new version):",
 none:"No change matches these filters.",provenance:"Provenance",
 legend:"Marks: [x] ready · [!] flagged · [≠] previous text already diverges from the German · [h] routed to a translator · [a] accepted · [e] accepted edited · [r] sent back · keys j/k or ↑/↓ move, Enter opens, f/i language, 1/2/3 decide, Ctrl/Cmd+Enter save and next",
 theme:"Theme",auto:"auto",light:"light",dark:"dark",
 reasons:["","Number wrong","German change not applied","Content lost","German left / untranslated","Terminology","Wording","Other"]},
fr:{ui:"Interface",sub:"Registre de révision",drafts:"brouillons",model:"Modèle",run:"Série",guards:"Contrôles",items:"Éléments",changes:"Changements",ready:"Prêts",flagged:"Signalés",
 exact:"Exact vs règles seules",rule:"Règle préenregistrée",human:"Confiés à un traducteur",divergent:"Ancien texte divergent",decided:"décidés",
 status:"Statut",language:"Langue",open:"Ouverts",all:"Tous",decidedF:"Décidés",divF:"Divergents",allFam:"Toutes les familles",search:"Produit ou code",
 mark:"Marque",no:"N°",product:"Produit",change:"Changement",shown:"changements affichés",xlf:"Exporter XLIFF 2.1",json:"Exporter JSON",copy:"Copier les décisions",
 copied:"Décisions copiées dans le presse-papiers.",selcopy:"Presse-papiers bloqué : le JSON est sélectionné ci-dessous, copiez-le avec Ctrl/Cmd+C.",dl:"Téléchargé",
 s1:"Changement allemand",s2:"Brouillons",s3:"Contrôles",s4:"Décision",ctxA:"Contexte : autour des changements",ctxF:"Contexte : texte entier",fr:"Français",it:"Italien",
 lready:"prêt",lflagged:"signalé",lhuman:"confié à un traducteur",edited:"modifié",reset:"Rétablir le brouillon",editHint:"Cliquez dans le texte pour le modifier sur place.",
 check:"Contrôle",result:"Résultat",finding:"Constat",pass:"ok",fail:"ÉCHEC",na:"s.o.",raw:"détail technique",noChecks:"Pas de contrôle : pas de brouillon machine.",
 accept:"Accepter tel quel",acceptEd:"Accepter modifié",sendBack:"Renvoyer",reason:"Motif",note:"Remarque (pourquoi)",saveNext:"Enregistrer, suivant",keys:"touches 1/2/3 décider · f/i langue · Ctrl/Cmd+Entrée enregistrer, suivant",
 savedAt:"enregistré",openSt:"ouvert",noEdit:"Modifiez d'abord le texte du brouillon (cliquez dedans).",
 humanTxt:"Confié à un traducteur : l'allemand a été réécrit à plus de 60 %",humanShort:"Confié à un traducteur, pas de brouillon machine",humanPrev:"Ancien texte (modifiez-le sur place pour écrire la nouvelle version) :",
 none:"Aucun changement ne correspond à ces filtres.",provenance:"Provenance",
 legend:"Marques : [x] prêt · [!] signalé · [≠] l'ancien texte diverge déjà de l'allemand · [h] confié à un traducteur · [a] accepté · [e] accepté modifié · [r] renvoyé · touches j/k ou ↑/↓ naviguer, Entrée ouvrir, f/i langue, 1/2/3 décider, Ctrl/Cmd+Entrée enregistrer et suivant",
 theme:"Thème",auto:"auto",light:"clair",dark:"sombre",
 reasons:["","Nombre erroné","Changement allemand non appliqué","Contenu perdu","Allemand resté / non traduit","Terminologie","Formulation","Autre"]},
it:{ui:"Interfaccia",sub:"Registro di revisione",drafts:"bozze",model:"Modello",run:"Serie",guards:"Controlli",items:"Elementi",changes:"Modifiche",ready:"Pronte",flagged:"Segnalate",
 exact:"Esatte vs solo regole",rule:"Regola preregistrata",human:"Affidate a un traduttore",divergent:"Vecchio testo divergente",decided:"decise",
 status:"Stato",language:"Lingua",open:"Aperte",all:"Tutte",decidedF:"Decise",divF:"Divergenti",allFam:"Tutte le famiglie",search:"Prodotto o codice",
 mark:"Segno",no:"N.",product:"Prodotto",change:"Modifica",shown:"modifiche mostrate",xlf:"Esporta XLIFF 2.1",json:"Esporta JSON",copy:"Copia decisioni",
 copied:"Decisioni copiate negli appunti.",selcopy:"Appunti bloccati: il JSON è selezionato qui sotto, copiarlo con Ctrl/Cmd+C.",dl:"Scaricato",
 s1:"Modifica tedesca",s2:"Bozze",s3:"Controlli",s4:"Decisione",ctxA:"Contesto: attorno alle modifiche",ctxF:"Contesto: testo intero",fr:"Francese",it:"Italiano",
 lready:"pronta",lflagged:"segnalata",lhuman:"affidata a un traduttore",edited:"modificata",reset:"Ripristina la bozza",editHint:"Cliccare nel testo per modificarlo sul posto.",
 check:"Controllo",result:"Esito",finding:"Rilievo",pass:"ok",fail:"ERRORE",na:"n.a.",raw:"dettaglio tecnico",noChecks:"Nessun controllo: nessuna bozza automatica.",
 accept:"Accetta così",acceptEd:"Accetta modificata",sendBack:"Rinvia",reason:"Motivo",note:"Nota (perché)",saveNext:"Salva, avanti",keys:"tasti 1/2/3 decidere · f/i lingua · Ctrl/Cmd+Invio salva, avanti",
 savedAt:"salvato",openSt:"aperta",noEdit:"Modificare prima il testo della bozza (cliccarci dentro).",
 humanTxt:"Affidata a un traduttore: il tedesco è stato riscritto per oltre il 60%",humanShort:"Affidata a un traduttore, nessuna bozza automatica",humanPrev:"Vecchio testo (modificarlo sul posto per scrivere la nuova versione):",
 none:"Nessuna modifica corrisponde a questi filtri.",provenance:"Provenienza",
 legend:"Segni: [x] pronta · [!] segnalata · [≠] il vecchio testo diverge già dal tedesco · [h] affidata a un traduttore · [a] accettata · [e] accettata modificata · [r] rinviata · tasti j/k o ↑/↓ spostarsi, Invio aprire, f/i lingua, 1/2/3 decidere, Ctrl/Cmd+Invio salva e avanti",
 theme:"Tema",auto:"auto",light:"chiaro",dark:"scuro",
 reasons:["","Numero errato","Modifica tedesca non applicata","Contenuto perso","Tedesco rimasto / non tradotto","Terminologia","Formulazione","Altro"]}};
var UL=TX[P.ui]?P.ui:"en";function t(k){return (TX[UL][k]!=null?TX[UL][k]:TX.en[k])}
// ------------------------------------------------------------------ theme
var themes=["auto","light","dark"],TH=themes.indexOf(P.theme)>=0?P.theme:(document.documentElement.getAttribute("data-theme")||"auto");
function applyTheme(){if(TH==="auto")document.documentElement.removeAttribute("data-theme");else document.documentElement.setAttribute("data-theme",TH);
 $("theme").textContent=t("theme")+": "+t(TH)}
$("theme").onclick=function(){TH=themes[(themes.indexOf(TH)+1)%3];P.theme=TH;lsSet("gleichlaut:prefs",P);applyTheme()};
$("ui-lang").value=UL;$("ui-lang").onchange=function(){UL=this.value;P.ui=UL;lsSet("gleichlaut:prefs",P);chrome();renderReg();renderCase()};
// ------------------------------------------------------------------ helpers over the data
function pct(x){return (Math.round(x*10)/10).toFixed(1)+"%"}
function plain(S,old){return S.filter(function(s){return old?s[0]!=="i":s[0]!=="d"}).map(function(s){return s[1]}).join("")}
G.forEach(function(g,i){g.no=("00"+(i+1)).slice(-3);g.deNew=plain(g.de,false);["fr","it"].forEach(function(L){var it=g.items[L];if(it){it.draft=it.status==="human"?"":plain(it.segs,false);it.g=g}})});
var ITEMS=[];G.forEach(function(g){["fr","it"].forEach(function(L){if(g.items[L])ITEMS.push(g.items[L])})});
function dec(it){return S.dec[it.key]}
function mark(it){if(!it)return ['<span class="mk o">[ ]</span>',""];var d=dec(it);
 if(d)return ['<span class="mk">['+(d.decision==="accept"?"a":d.decision==="accept-edited"?"e":"r")+']</span>',d.decision];
 if(it.banner||it.corr)return ['<span class="mk r">[≠]</span>',"divergent"];
 if(it.status==="human")return ['<span class="mk">[h]</span>',"human"];
 return it.status==="ready"?['<span class="mk">[x]</span>',"ready"]:['<span class="mk r">[!]</span>',"flagged"]}
// ------------------------------------------------------------------ header and chrome
function kv(id,rows){$(id).innerHTML=rows.map(function(r){return "<dt>"+esc(r[0])+"</dt><dd"+(r[2]?' class="'+r[2]+'"':"")+">"+esc(r[1])+"</dd>"}).join("")}
function chrome(){
 document.documentElement.lang=UL;$("l-ui").textContent=t("ui");applyTheme();
 $("sub").textContent=t("sub")+" · "+M.label+" · "+D.counts.items+" "+t("drafts");
 var fz=(M.pipeline.match(/freeze sha256:([0-9a-f]+)/)||[])[1]||"";
 kv("kv-l",[[t("model"),M.model],[t("run"),M.run],[t("guards"),(M.stack==="g3"?"guards3 (frozen)":"guards v2 (frozen)")+(fz?" · freeze "+fz.slice(0,12):"")],
  [t("items"),String(D.counts.items)],[t("changes"),String(D.counts.changes)]]);
 var C=D.counts,r=[];
 if(A){r.push([t("ready"),A.unflagged+" · "+pct(A.ready_rate)]);r.push([t("flagged"),A.flagged+" · "+pct(A.flag_rate)]);
  var ex=A.exact;r.push([t("exact"),pct(ex.model)+" vs "+pct(ex.rules)+" ("+(ex.delta>=0?"+":"")+ex.delta+" pts, 95% CI "+ex.ci95[0]+" to "+ex.ci95[1]+")"]);
  if(A.pass!=null)r.push([t("rule"),A.pass?"PASS":"FAIL",A.pass?"pass":"fail"])}
 else{r.push([t("ready"),String(C.ready)]);r.push([t("flagged"),String(C.flagged)]);if(C.human)r.push([t("human"),String(C.human)]);
  if(C.exact!=null)r.push([t("exact").split(" vs")[0],String(C.exact)])}
 if(C.divergent)r.push([t("divergent"),String(C.divergent)]);
 kv("kv-r",r);
 seg("f-status",t("status"),[["open",t("open")],["ready",t("ready")],["flagged",t("flagged")],["divergent",t("divF")],["decided",t("decidedF")],["all",t("all")]],F.status,function(v){F.status=v;renderReg()});
 seg("f-lang",t("language"),[["all","FR+IT"],["fr","FR"],["it","IT"]],F.lang,function(v){F.lang=v;if(v!=="all")focusL=v;renderReg();renderCase()});
 var fs=$("f-fam");fs.innerHTML="";fs.appendChild(new Option(t("allFam")+" ("+D.families.length+")",""));
 D.families.forEach(function(f){fs.appendChild(new Option(f[0]+" · "+f[1],f[0]))});fs.value=F.fam;$("f-q").placeholder=t("search");
 $("h-mark").textContent=t("mark");$("h-no").textContent=t("no");$("h-prod").textContent=t("product");$("h-chg").textContent=t("change");
 $("x-xlf").textContent=t("xlf");$("x-json").textContent=t("json");$("x-copy").textContent=t("copy");
 $("prov").textContent=t("provenance")+": "+M.pipeline+" · outputs sha256:"+M.run_sha256.slice(0,16)+"… · items sha256:"+M.items_sha256.slice(0,16)+"…";
 $("legend").textContent=t("legend");progress()}
function seg(id,label,opts,cur,fn){var s=$(id);s.innerHTML='<span class="k">'+esc(label)+"</span>";
 opts.forEach(function(o){var b=document.createElement("button");b.type="button";b.className="tb";b.textContent=o[1];b.setAttribute("aria-pressed",o[0]===cur);
  b.onclick=function(){s.querySelectorAll("button").forEach(function(x){x.setAttribute("aria-pressed",x===b)});fn(o[0])};s.appendChild(b)})}
function progress(){var n=ITEMS.filter(function(it){return dec(it)}).length;$("progress").innerHTML="<b>"+n+"/"+ITEMS.length+"</b> "+esc(t("decided"))}
// ------------------------------------------------------------------ register
var F={status:"open",lang:"all",fam:"",q:""},sel=null,focusL="fr",VIS=[];
function langs(g){return ["fr","it"].filter(function(L){return g.items[L]&&(F.lang==="all"||F.lang===L)})}
function okItem(it){var d=dec(it);switch(F.status){case "open":return !d;case "ready":return it.status==="ready";case "flagged":return it.status==="flagged";
 case "divergent":return !!(it.banner||it.corr);case "decided":return !!d;default:return true}}
function renderReg(){var tb=document.querySelector("#reg tbody"),h="";VIS=[];
 G.forEach(function(g){var Ls=langs(g);if(!Ls.length)return;if(F.fam&&g.family!==F.fam)return;
  if(F.q&&(g.product+" "+g.code+" "+g.pair+" "+g.no).toLowerCase().indexOf(F.q)<0)return;
  if(!Ls.some(function(L){return okItem(g.items[L])}))return;VIS.push(g);
  var mk=(F.lang==="all"?["fr","it"]:[F.lang]).map(function(L){return mark(g.items[L])[0]}).join("");
  h+='<tr data-pair="'+esc(g.pair)+'" aria-selected="'+(sel===g)+'"><td>'+mk+'</td><td>'+g.no+'</td><td title="'+esc(g.product)+'">'+esc(g.product)+
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
function stLabel(it){return it.status==="ready"?t("lready"):it.status==="flagged"?t("lflagged"):t("lhuman")}
function notice(it){var p=[];if(it.banner)p.push("<p><span class=\"mk\">[≠]</span>"+esc(it.banner)+"</p>");
 if(it.corr)p.push("<p>"+(it.banner?"":"<span class=\"mk\">[≠]</span>")+esc(it.corr)+"</p>");return p.length?'<div class="notice" role="note">'+p.join("")+"</div>":""}
function caseHTML(g,live){var Ls=langs(g),one=Ls.length<2?" one":"",h="";
 h+="<h2>"+esc(g.product)+'</h2><p class="ref">'+esc(g.code)+" · SL "+esc(g.snap_old)+" → "+esc(g.snap_new)+" · family "+esc(g.family)+" · "+esc(g.pair)+" · "+g.no+"</p>";
 h+='<section class="sec"><div class="sl"><span class="no">1</span><span class="t">'+esc(t("s1"))+"</span>"+(live?'<button class="tb sp" type="button" id="ctx">'+esc(ctxMode?t("ctxA"):t("ctxF"))+"</button>":"")+
  '</div><div class="txt de" lang="de">'+segs(g.de,live&&ctxMode,false)+"</div></section>";
 h+='<section class="sec"><div class="sl"><span class="no">2</span><span class="t">'+esc(t("s2"))+'</span></div><div class="drafts'+one+'">';
 Ls.forEach(function(L){var it=g.items[L],ed=S.edits[it.key];
  h+='<div class="dr" data-lang="'+L+'"><div class="dl"><span class="ln">'+esc(LN(L))+'</span>·<span class="st'+(it.status==="flagged"?" r":"")+'">'+esc(stLabel(it))+'</span><span class="key">'+esc(it.key)+(it.rule_only?" · rules":"")+"</span></div>"+notice(it);
  if(it.status==="human")h+='<p class="human">'+esc(it.reason&&!/rewritten|60/.test(it.reason)?t("humanShort"):t("humanTxt"))+(it.ratio!=null?" ("+it.ratio+"%)":"")+".</p>"+(it.reason?'<p class="ref">'+esc(it.reason)+"</p>":"")+"<p class=\"human\" style=\"color:var(--ink2)\">"+esc(t("humanPrev"))+"</p>";
  var body=ed!=null?esc(ed):segs(it.segs,false,live);
  h+='<div class="txt'+(live?" ed":"")+'" lang="'+L+'"'+(live?' contenteditable="true" spellcheck="true" role="textbox" aria-multiline="true" aria-label="'+esc(LN(L))+'" data-key="'+esc(it.key)+'"':"")+">"+body+"</div>";
  if(live)h+='<div class="edmeta" data-meta="'+esc(it.key)+'">'+(ed!=null?"<span>"+esc(t("edited"))+'</span><button class="tb" type="button" data-reset="'+esc(it.key)+'">'+esc(t("reset"))+"</button>":"<span>"+esc(t("editHint"))+"</span>")+"</div>";
  h+="</div>"});
 h+="</div></section>";
 h+='<section class="sec"><div class="sl"><span class="no">3</span><span class="t">'+esc(t("s3"))+"</span></div>";
 Ls.forEach(function(L){var it=g.items[L];h+='<div class="tbl"><table class="ledger"><caption>'+esc(LN(L))+"</caption>";
  if(!it.ledger.length){h+='<tbody><tr><td class="na">'+esc(t("noChecks"))+"</td></tr></tbody></table></div>";return}
  h+="<thead><tr><th>"+esc(t("check"))+"</th><th>"+esc(t("result"))+"</th><th>"+esc(t("finding"))+"</th></tr></thead><tbody>";
  it.ledger.forEach(function(r){var st=r[2],res=st==="pass"?t("pass"):st==="fail"?t("fail"):t("na"),cls=st==="fail"?"FAIL":st==="pass"?"":"na";
   var fd=r[3].map(function(f){return "<p>"+esc(f.t)+(f.c&&it.corr_note?'<span class="cn">[≠] '+esc(it.corr_note)+"</span>":"")+"</p>"}).join("");
   if(!fd&&st!=="fail")fd='<span class="na">—</span>';
   if(r[4])fd+="<details><summary>"+esc(t("raw"))+" · "+esc(r[5])+"</summary><div>"+esc(r[4])+"</div></details>";
   h+='<tr><td class="chk" title="'+esc(r[5])+'">'+esc(r[1])+'</td><td class="res '+cls+'">'+esc(res)+'</td><td class="fd" lang="'+L+'">'+fd+"</td></tr>"});
  h+="</tbody></table></div>"});
 h+="</section>";
 if(live){h+='<section class="sec"><div class="sl"><span class="no">4</span><span class="t">'+esc(t("s4"))+'</span></div><div class="decs'+one+'">';
  Ls.forEach(function(L){var it=g.items[L],d=dec(it)||{};
   h+='<div class="dec'+(L===focusL||Ls.length<2?" focus":"")+'" data-lang="'+L+'" data-key="'+esc(it.key)+'"><div class="dl"><span class="ln">'+esc(LN(L))+'</span><span class="key">'+esc(it.key)+'</span></div><div class="btns">'+
    [["accept","(1) "+t("accept")],["accept-edited","(2) "+t("acceptEd")],["send-back","(3) "+t("sendBack")]].map(function(b){
     return '<button class="box" type="button" data-d="'+b[0]+'" aria-pressed="'+(d.decision===b[0])+'">'+esc(b[1])+"</button>"}).join("")+"</div>"+
    "<label>"+esc(t("reason"))+'<select data-f="reason">'+t("reasons").map(function(r,i){var v=TX.en.reasons[i];return '<option value="'+esc(v)+'"'+(d.reason===v?" selected":"")+">"+esc(r||"—")+"</option>"}).join("")+"</select></label>"+
    "<label>"+esc(t("note"))+'<textarea data-f="note" lang="'+L+'">'+esc(d.note||"")+"</textarea></label>"+
    '<div class="stt">'+esc(d.decision?t("savedAt")+" · "+d.at.slice(0,16).replace("T"," "):t("openSt"))+"</div></div>"});
  h+='</div><div class="save"><button class="box primary" type="button" id="savenext">'+esc(t("saveNext"))+'</button><span class="hint">'+esc(t("keys"))+"</span></div></section>"}
 return h}
function renderCase(){var c=$("case");if(!sel){c.innerHTML='<p class="empty">'+esc(t("none"))+"</p>";return}
 try{if(location.hash.slice(1)!==sel.pair)history.replaceState(null,"","#"+sel.pair)}catch(e){}
 var Ls=langs(sel);if(Ls.indexOf(focusL)<0)focusL=Ls[0];c.innerHTML=caseHTML(sel,true);wire(c)}
function wire(c){
 var b=$("ctx");if(b)b.onclick=function(){ctxMode=!ctxMode;renderCase()};
 c.querySelectorAll(".ed").forEach(function(el){var key=el.dataset.key,it=byKey[key];
  el.addEventListener("keydown",function(e){if(e.key==="Enter"&&!(e.metaKey||e.ctrlKey))e.preventDefault()});
  el.addEventListener("paste",function(e){e.preventDefault();var tx=(e.clipboardData||window.clipboardData).getData("text").replace(/\s*\n\s*/g," ");document.execCommand("insertText",false,tx)});
  el.addEventListener("focus",function(){setFocus(it.lang)});
  el.addEventListener("input",function(){var v=readEd(el);if(v===it.draft||(it.status==="human"&&v===plain(it.segs,false)))delete S.edits[key];else S.edits[key]=v;save();
   var m=c.querySelector('[data-meta="'+key+'"]');if(m)m.innerHTML=S.edits[key]!=null?"<span>"+esc(t("edited"))+'</span><button class="tb" type="button" data-reset="'+esc(key)+'">'+esc(t("reset"))+"</button>":"<span>"+esc(t("editHint"))+"</span>"})});
 c.addEventListener("click",function(e){var r=e.target.closest("[data-reset]");if(r){delete S.edits[r.dataset.reset];var d=S.dec[r.dataset.reset];if(d&&d.decision==="accept-edited"){delete S.dec[r.dataset.reset]};save();renderCase();refreshRow(sel);progress();return}
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
// ------------------------------------------------------------------ keyboard
document.addEventListener("keydown",function(e){var tg=e.target,typing=tg.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(tg.tagName);
 if(e.key==="Enter"&&(e.metaKey||e.ctrlKey)){e.preventDefault();saveNext();return}
 if(e.key==="Escape"&&typing){tg.blur();return}
 if(typing||e.altKey||e.metaKey||e.ctrlKey)return;
 var k=e.key;
 if(k==="j"||k==="ArrowDown"){e.preventDefault();move(1)}else if(k==="k"||k==="ArrowUp"){e.preventDefault();move(-1)}
 else if(k==="Enter"&&tg.closest&&!tg.closest("button,a")){e.preventDefault();$("case").focus();$("case").scrollIntoView({block:"start"})}
 else if(k==="f"||k==="i"){setFocus(k==="f"?"fr":"it")}
 else if(k==="1"||k==="2"||k==="3"){if(sel){var L=langs(sel).indexOf(focusL)>=0?focusL:langs(sel)[0];decide(L,["accept","accept-edited","send-back"][+k-1])}}});
// ------------------------------------------------------------------ export
function payload(){return {run:M.run,model:M.model,pipeline:M.pipeline,run_sha256:M.run_sha256,items_sha256:M.items_sha256,exported_at:new Date().toISOString(),decisions:S.dec,edits:S.edits}}
function download(name,text,type){var u=URL.createObjectURL(new Blob([text],{type:type})),a=document.createElement("a");a.href=u;a.download=name;document.body.appendChild(a);a.click();
 setTimeout(function(){URL.revokeObjectURL(u);a.remove()},500)}
function x(s){return esc(s).replace(/'/g,"&apos;")}
function xliff(L){var trg=L==="fr"?"fr-CH":"it-CH",u=[],n=0;
 ITEMS.forEach(function(it){if(it.lang!==L)return;var g=it.g,d=dec(it)||null,st=it.status==="ready"?["translated","gleichlaut:ready"]:["initial","gleichlaut:"+it.status],tgt=null,marks=true;
  if(d&&(d.decision==="accept"||d.decision==="accept-edited")&&(it.status!=="human"||d.text)){st=["reviewed",d.decision==="accept-edited"?"gleichlaut:accepted-edited":"gleichlaut:accepted"];
   if(d.decision==="accept-edited"){tgt=d.text;marks=false}}
  else if(d&&d.decision==="send-back")st=["initial","gleichlaut:sent-back"];
  var notes='<note id="verdict" category="gleichlaut:verdict" appliesTo="target" priority="1">'+x(it.status)+"</note>";
  if(it.banner)notes+='<note id="divergence" category="gleichlaut:divergence" appliesTo="target" priority="1">'+x(it.banner)+"</note>";
  var F_=it.findings.map(function(f){return (f[0]?"["+f[0]+"] ":"")+f[1]+(f[2]&&it.corr_note?" ("+it.corr_note+")":"")});if(it.corr)F_.unshift(it.corr);
  F_.forEach(function(f,i){notes+='<note id="finding-'+(i+1)+'" category="gleichlaut:finding" appliesTo="target" priority="1">'+x(f)+"</note>"});
  if(d)notes+='<note id="review" category="gleichlaut:review" appliesTo="target" priority="1">'+x("reviewer: "+d.decision+" ("+d.at+")"+((d.reason||d.note)?": "+[d.reason,d.note].filter(Boolean).join("; "):""))+"</note>";
  var T="";if(tgt!=null)T="<target>"+x(tgt)+"</target>";
  else if(it.status!=="human"){var m=0;T="<target>"+it.segs.filter(function(s){return s[0]!=="d"}).map(function(s){
    if(s.length===4&&marks){m++;var code=s[2]!=="model";return '<mrk id="t'+m+'"'+(code?' translate="no"':"")+' type="gleichlaut:'+(code?"code":"model")+'-number"'+(s[3]?' value="'+x(s[3])+'"':"")+">"+x(s[1])+"</mrk>"}
    return x(s[1])}).join("")+"</target>"}
  u.push('<unit id="'+x(it.key)+'" name="'+x(it.cud)+'"><notes>'+notes+'</notes><segment id="s1" state="'+st[0]+'" subState="'+st[1]+'"><source>'+x(g.deNew)+"</source>"+T+"</segment></unit>")});
 return '<?xml version="1.0" encoding="UTF-8"?>\n<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" version="2.1" srcLang="de-CH" trgLang="'+trg+'"><file id="f1" original="gleichlaut:'+x(M.run)+'">'+
  '<notes><note id="about" category="gleichlaut:about">Reviewed in the Gleichlaut review page ('+x(new Date().toISOString())+'). Source = new German text; target = accepted text (state=reviewed), or the machine draft (translated / initial).</note>'+
  '<note id="provenance" category="gleichlaut:provenance">model '+x(M.model)+"; "+x(M.pipeline)+"; run "+x(M.run)+"</note></notes>"+u.join("")+"</file></xliff>\n"}
function msg(s){$("x-msg").textContent=s}
$("x-xlf").onclick=function(){var Ls=F.lang==="all"?["fr","it"]:[F.lang];Ls=Ls.filter(function(L){return ITEMS.some(function(it){return it.lang===L})});
 Ls.forEach(function(L,i){setTimeout(function(){download("gleichlaut-"+M.run+"-de-CH_"+(L==="fr"?"fr-CH":"it-CH")+"-reviewed.xlf",xliff(L),"application/xliff+xml")},i*400)});
 msg(t("dl")+": "+Ls.map(function(L){return "XLIFF 2.1 "+L.toUpperCase()}).join(", "))};
$("x-json").onclick=function(){download("gleichlaut-decisions-"+M.run+".json",JSON.stringify(payload(),null,1),"application/json");msg(t("dl")+": JSON")};
$("x-copy").onclick=function(){var s=JSON.stringify(payload(),null,1),box=$("copybox");
 function fallback(){box.hidden=false;box.value=s;box.focus();box.select();msg(t("selcopy"))}
 try{if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(s).then(function(){box.hidden=true;msg(t("copied"))},fallback)}else fallback()}catch(e){fallback()}};
// ------------------------------------------------------------------ print: one case per page
window.addEventListener("beforeprint",function(){$("print").innerHTML=VIS.map(function(g){return '<article class="pcase">'+caseHTML(g,false)+"</article>"}).join("")});
window.addEventListener("afterprint",function(){$("print").innerHTML=""});
function fromHash(){var h=decodeURIComponent(location.hash.slice(1)),g=G.filter(function(g){return g.pair===h||g.no===h})[0];
 if(g){if(!G.some(function(){return true})||!(langs(g).some(function(L){return okItem(g.items[L])})))F.status="all";sel=g;return true}return false}
fromHash();chrome();renderReg();if(sel){markSel(true);renderCase()}
window.GleichlautReview={xliff:xliff,payload:payload};
window.addEventListener("hashchange",function(){if(fromHash()){chrome();renderReg();markSel(true);renderCase()}});
})();
</script>
"""
