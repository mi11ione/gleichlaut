"""python3 -m gleichlaut.ui.build [--run fresh166] [--out PATH]

One self-contained HTML review page over a recorded run (inline CSS/JS/data; no request at view time; works from
file://), grouped by German change with the FR and IT drafts side by side. Diffs, number provenance, guard lights and
complaints are computed here in Python from the same per-item views the emitters use (gleichlaut.emit.load); the
headline numbers come from score.score_run(run)["summary"]["all"]. Reviewer decisions stay in the browser
(localStorage) and leave it only through "Export decisions"."""
import argparse, difflib, html, json, os, re
from collections import Counter
from .. import core, score
from ..emit import load

OUT = os.path.join(core.ROOT, "out", "ui", "index.html")
TOK = re.compile(core.gl2.NUMRX.pattern + r"|\w+|\s+|[^\w\s]")        # numbers first: a number is one token


def _toks(s): return [(m.start(), m.group(0)) for m in TOK.finditer(s)]


def diff(old, new, nums=()):
    """-> [[kind, text, who?, slot?]]: kind e(qual) | i(nserted) | d(eleted), word-level; numbers of the new text whose
    span is in `nums` become their own segment carrying who placed them."""
    a, b = _toks(old), _toks(new); chip = {s: (who, slot) for s, e, t, who, slot in nums}
    segs = []
    def put(kind, start, text):
        c = chip.get(start) if kind != "d" else None
        if c: segs.append([kind, text, c[0], c[1]])
        elif segs and segs[-1][0] == kind and len(segs[-1]) == 2: segs[-1][1] += text
        else: segs.append([kind, text])
    sm = difflib.SequenceMatcher(None, [t for _, t in a], [t for _, t in b], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("delete", "replace"):
            for s, t in a[i1:i2]: put("d", s, t)
        if op in ("insert", "replace", "equal"):
            for s, t in b[j1:j2]: put("e" if op == "equal" else "i", s, t)
    return segs


def data(run):
    meta, views = load(run)
    summ = score.score_run(run)["summary"]
    groups = {}
    for v in views:
        g = groups.setdefault(v["pair"], dict(pair=v["pair"], product=v["product"], code=v["cud_id"], snap_old=v["snap_old"],
                                              snap_new=v["snap_new"], family=v["family"], de=diff(v["de_old"], v["de_new"]), items={}))
        g["items"][v["lang"]] = dict(key=v["key"], lang=v["lang"], status=v["status"], segs=diff(v["tgt_old"], v["draft"], v["numbers"]),
                                     lights=v["lights"], complaint=v["complaint"], rule_only=v["rule_only"],
                                     model_numbers=sum(n[3] == "model" for n in v["numbers"]), code_numbers=sum(n[3] == "code" for n in v["numbers"]))
    fam = Counter(v["family"] for v in views)
    return dict(meta=meta, all=summ["all"], fr=summ.get("fr"), it=summ.get("it"), groups=list(groups.values()),
                families=sorted(fam.items(), key=lambda kv: (-kv[1], kv[0])),
                counts=dict(items=len(views), ready=sum(v["status"] == "ready" for v in views),
                            code_numbers=sum(n[3] == "code" for v in views for n in v["numbers"]),
                            model_numbers=sum(n[3] == "model" for v in views for n in v["numbers"])))


def build(run="fresh166", out=OUT):
    D = data(run)
    blob = json.dumps(D, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = PAGE.replace("__TITLE__", html.escape(f"Gleichlaut review · {run}")).replace("__DATA__", blob)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f: f.write(page)
    return out, D


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#f6f7f9;--panel:#fff;--ink:#1c2128;--muted:#5d6672;--faint:#8a929c;--line:#e3e6ea;--line2:#d2d7dd;
--accent:#2f5bd3;--ins:#d9f2df;--ins-ink:#14532d;--del:#fbe1e1;--del-ink:#8a1c1c;--chip:#e6edff;--chip-ink:#1e3a8a;--chip-line:#b8c8f5;
--mchip:#fff1d6;--mchip-ink:#7a4a00;--ok:#1f8a4c;--bad:#c62f2f;--off:#b7bdc5;--ready-bg:#e3f4ea;--ready-ink:#14633a;
--flag-bg:#fdecd3;--flag-ink:#8a4b00;--acc-bg:#e3f4ea;--back-bg:#fbe4e4;--shadow:0 1px 2px rgba(16,24,40,.06)}
@media (prefers-color-scheme:dark){:root{--bg:#0f1216;--panel:#171b21;--ink:#e6e9ee;--muted:#a3abb6;--faint:#7c8591;--line:#262c34;--line2:#323a44;
--accent:#7aa2ff;--ins:#173a26;--ins-ink:#b7f0c9;--del:#43201f;--del-ink:#ffc2bd;--chip:#1d2a4d;--chip-ink:#c9d7ff;--chip-line:#34477a;
--mchip:#3d2c0c;--mchip-ink:#ffd58a;--ok:#42c27a;--bad:#ff6b6b;--off:#4a525d;--ready-bg:#16382a;--ready-ink:#9ce6bd;
--flag-bg:#3d2a10;--flag-ink:#ffcf8a;--acc-bg:#16382a;--back-bg:#43201f;--shadow:none}}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
header{background:var(--panel);border-bottom:1px solid var(--line);padding:20px 28px 16px}
h1{font-size:20px;margin:0;font-weight:650;letter-spacing:-.01em}
h1 small{font-weight:400;color:var(--muted);font-size:14px;margin-left:8px}
.what{color:var(--muted);font-size:13px;margin:4px 0 14px}
.tiles{display:flex;flex-wrap:wrap;gap:10px}
.tile{border:1px solid var(--line);border-radius:10px;padding:8px 14px;min-width:150px;background:var(--panel)}
.tile b{display:block;font-size:20px;font-variant-numeric:tabular-nums;font-weight:650}
.tile span{font-size:12px;color:var(--muted)}
.prov{font:12px/1.4 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:var(--faint);margin-top:12px;word-break:break-all}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 28px;display:flex;flex-wrap:wrap;gap:14px;align-items:center}
.seg{display:inline-flex;border:1px solid var(--line2);border-radius:8px;overflow:hidden;background:var(--panel)}
.seg button{border:0;background:none;color:var(--ink);padding:5px 11px;font:inherit;font-size:13px;cursor:pointer}
.seg button+button{border-left:1px solid var(--line2)}
.seg button[aria-pressed=true]{background:var(--accent);color:#fff}
select,input[type=search]{font:inherit;font-size:13px;padding:5px 8px;border:1px solid var(--line2);border-radius:8px;background:var(--panel);color:var(--ink)}
label.t{font-size:12px;color:var(--muted);margin-right:4px}
.btn{font:inherit;font-size:13px;padding:5px 11px;border-radius:8px;border:1px solid var(--line2);background:var(--panel);color:var(--ink);cursor:pointer}
.btn:hover{border-color:var(--accent)}
.count{font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums}
.legend{padding:8px 28px 0;font-size:12px;color:var(--muted);display:flex;flex-wrap:wrap;gap:16px;align-items:center}
main{padding:14px 28px 60px;max-width:1500px;margin:0 auto}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;margin:0 0 16px;box-shadow:var(--shadow)}
.card>.hd{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:baseline;padding:12px 18px;border-bottom:1px solid var(--line)}
.hd .prod{font-weight:600}
.hd .m{font-size:12px;color:var(--muted);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.de{padding:12px 18px;border-bottom:1px solid var(--line)}
.lab{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--faint);margin-bottom:4px;font-weight:600}
.txt{white-space:pre-wrap;overflow-wrap:anywhere}
.cols{display:grid;grid-template-columns:1fr 1fr}
.pane{padding:12px 18px 14px;min-width:0}
.pane+.pane{border-left:1px solid var(--line)}
.pane.none{color:var(--faint);font-size:13px;font-style:italic}
.pane.dec-accept{background:linear-gradient(var(--acc-bg),var(--acc-bg)) top/100% 3px no-repeat}
.pane.dec-back{background:linear-gradient(var(--back-bg),var(--back-bg)) top/100% 3px no-repeat}
.ph{display:flex;align-items:center;gap:8px;margin-bottom:6px}
.lang{font-weight:650;font-size:13px}
.pill{font-size:12px;font-weight:600;padding:1px 9px;border-radius:999px}
.pill.ready{background:var(--ready-bg);color:var(--ready-ink)}
.pill.flagged{background:var(--flag-bg);color:var(--flag-ink)}
.key{font:12px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:var(--faint);margin-left:auto}
ins{background:var(--ins);color:var(--ins-ink);text-decoration:none;border-radius:3px;padding:0 1px}
del{background:var(--del);color:var(--del-ink);border-radius:3px;padding:0 1px;text-decoration:line-through;text-decoration-thickness:1px}
.chip{display:inline-block;font-variant-numeric:tabular-nums;background:var(--chip);color:var(--chip-ink);border:1px solid var(--chip-line);
border-radius:6px;padding:0 5px;line-height:1.35;font-weight:600}
.chip.i{box-shadow:inset 0 -2px 0 var(--ok)}
.chip.m{background:var(--mchip);color:var(--mchip-ink);border-color:var(--mchip-ink)}
.gap{color:var(--faint);padding:0 3px}
.lights{display:flex;flex-wrap:wrap;gap:4px 10px;margin:10px 0 0;font-size:12px;color:var(--muted)}
.lt{display:inline-flex;align-items:center;gap:4px;cursor:help}
.dot{width:9px;height:9px;border-radius:50%;background:var(--off);display:inline-block}
.dot.pass{background:var(--ok)}.dot.fail{background:var(--bad)}
.lt.fail{color:var(--bad);font-weight:600}
.complaint{margin-top:10px;border-left:3px solid var(--flag-ink);background:var(--flag-bg);color:var(--ink);padding:6px 10px;border-radius:0 6px 6px 0;font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere}
.complaint .lab{color:var(--flag-ink)}
.acts{display:flex;gap:8px;margin-top:12px;align-items:center}
.acts .btn[aria-pressed=true].a{background:var(--ok);border-color:var(--ok);color:#fff}
.acts .btn[aria-pressed=true].b{background:var(--bad);border-color:var(--bad);color:#fff}
.acts .st{font-size:12px;color:var(--muted)}
.empty{padding:40px;text-align:center;color:var(--muted)}
[hidden]{display:none!important}
@media (max-width:900px){.cols{grid-template-columns:1fr}.pane+.pane{border-left:0;border-top:1px solid var(--line)}header,.bar,main,.legend{padding-left:16px;padding-right:16px}}
</style>
</head>
<body>
<header>
 <h1>Gleichlaut <small>translator review: guarded DE&rarr;FR/IT drafts of amended SL limitations</small></h1>
 <div class="what" id="what"></div>
 <div class="tiles" id="tiles"></div>
 <div class="prov" id="prov"></div>
</header>
<div class="bar">
 <span><label class="t">Status</label><span class="seg" id="f-status"><button data-v="all" aria-pressed="true">All</button><button data-v="ready" aria-pressed="false">Ready</button><button data-v="flagged" aria-pressed="false">Flagged</button></span></span>
 <span><label class="t">Language</label><span class="seg" id="f-lang"><button data-v="all" aria-pressed="true">FR + IT</button><button data-v="fr" aria-pressed="false">FR</button><button data-v="it" aria-pressed="false">IT</button></span></span>
 <span><label class="t" for="f-fam">Family</label><select id="f-fam"></select></span>
 <input type="search" id="f-q" placeholder="Product or code" aria-label="Search product or limitation code">
 <span class="seg" id="f-view"><button data-v="compact" aria-pressed="true">Compact</button><button data-v="full" aria-pressed="false">Full text</button></span>
 <span class="count" id="shown"></span>
 <span style="margin-left:auto" class="count" id="dec"></span>
 <button class="btn" id="export">Export decisions (JSON)</button>
</div>
<div class="legend">
 <span><span class="chip">20</span> number placed by code</span>
 <span><span class="chip m">2</span> number written by the model</span>
 <span><ins>inserted</ins> / <del>removed</del> vs the previous text</span>
 <span><span class="dot pass"></span> guard passed <span class="dot fail"></span> failed <span class="dot"></span> not applicable</span>
</div>
<main id="main"></main>
<script type="application/json" id="data">__DATA__</script>
<script>
(function(){
"use strict";
var D=JSON.parse(document.getElementById("data").textContent), M=D.meta, A=D.all;
var LK="gleichlaut:"+M.run+":"+M.run_sha256.slice(0,12)+":decisions";
var dec={};try{dec=JSON.parse(localStorage.getItem(LK)||"{}")||{}}catch(e){dec={}}
function save(){try{localStorage.setItem(LK,JSON.stringify(dec))}catch(e){}}
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}
function el(t,c,h){var e=document.createElement(t);if(c)e.className=c;if(h!=null)e.innerHTML=h;return e}
function pct(x){return x.toFixed(1)+"%"}
// ---------------------------------------------------------------- header (all numbers from score.score_run)
document.getElementById("what").textContent=M.what+" · run "+M.run;
var ex=A.exact, tiles=[
 [A.n+" items",A.pairs+" German changes · "+A.families+" families"],
 [pct(A.ready_rate),A.unflagged+" ready (all guards passed)"],
 [pct(A.flag_rate),A.flagged+" flagged for a translator"],
 [pct(ex.model)+" vs "+pct(ex.rules),"exact: model vs rules only ("+(ex.delta>=0?"+":"")+ex.delta+" pts, 95% CI "+ex.ci95[0]+" to "+ex.ci95[1]+")"]];
if(A.unflagged_REAL!=null)tiles.push([String(A.unflagged_REAL),"unflagged real errors (95% upper bound "+A.wilson95_unflagged_real[1]+"%)"]);
if(A.pass!=null)tiles.push([A.pass?"PASS":"FAIL","pre-registered pass rule"]);
tiles.push([String(D.counts.code_numbers),"numbers placed by code"+(D.counts.model_numbers?" ("+D.counts.model_numbers+" written by the model)":"")]);
var T=document.getElementById("tiles");tiles.forEach(function(t){T.appendChild(el("div","tile","<b>"+esc(t[0])+"</b><span>"+esc(t[1])+"</span>"))});
document.getElementById("prov").textContent="model "+M.model+" · "+M.pipeline+" · outputs sha256:"+M.run_sha256.slice(0,16)+"… · items sha256:"+M.items_sha256.slice(0,16)+"…";
// ---------------------------------------------------------------- text rendering
var compact=true;
function cut(t,first,last){if(!compact||t.length<260)return esc(t);
 var a=t.slice(0,90).replace(/\s+\S*$/,""),b=t.slice(-90).replace(/^\S*\s+/,"");
 return (first?"":esc(a))+'<span class="gap">…</span>'+(last?"":esc(b))}
function segs(S){var h="";S.forEach(function(s,i){var k=s[0],t=s[1];
 if(s.length>2){var m=s[2]==="model",tip=(m?"written by the model":"placed by code")+(s[3]?" (slot "+s[3]+")":"");
  var c='<span class="chip'+(m?" m":"")+(k==="i"?" i":"")+'" title="'+esc(t+": "+tip)+'" aria-label="'+esc(t+", "+tip)+'">'+esc(t)+"</span>";
  h+=k==="d"?"<del>"+c+"</del>":c;return}
 if(k==="e")h+=cut(t,i===0,i===S.length-1);else if(k==="i")h+="<ins>"+esc(t)+"</ins>";else h+="<del>"+esc(t)+"</del>"});return h}
// ---------------------------------------------------------------- cards
var main=document.getElementById("main"),cards=[],panes=[];
D.groups.forEach(function(g){
 var c=el("section","card");c.dataset.family=g.family;c.dataset.q=(g.product+" "+g.code+" "+g.pair).toLowerCase();
 var hd=el("div","hd");hd.appendChild(el("span","prod",esc(g.product)));
 hd.appendChild(el("span","m","limitation "+esc(g.code)+" · SL "+esc(g.snap_old)+" → "+esc(g.snap_new)+" · family "+esc(g.family)+" · "+esc(g.pair)));c.appendChild(hd);
 var de=el("div","de");de.appendChild(el("div","lab","German (source text): previous → amended"));var dt=el("div","txt");dt._s=g.de;de.appendChild(dt);c.appendChild(de);
 var cols=el("div","cols");
 ["fr","it"].forEach(function(L){var it=g.items[L],p;
  if(!it){p=el("div","pane none","No "+L.toUpperCase()+" item for this change (target text unchanged in the official update, or excluded).");p.dataset.lang=L;p.dataset.status="none";cols.appendChild(p);return}
  p=el("div","pane");p.dataset.lang=L;p.dataset.status=it.status;p.dataset.key=it.key;
  var ph=el("div","ph");ph.appendChild(el("span","lang",L==="fr"?"French draft":"Italian draft"));
  ph.appendChild(el("span","pill "+it.status,it.status==="ready"?"Ready":"Flagged"));ph.appendChild(el("span","key",esc(it.key)+(it.rule_only?" · rules only":"")));p.appendChild(ph);
  var tx=el("div","txt");tx._s=it.segs;p.appendChild(tx);
  var lt=el("div","lights");it.lights.forEach(function(l){var s=el("span","lt "+l[2],'<span class="dot '+l[2]+'"></span>'+esc(l[1]));
   s.title=l[1]+": "+(l[2]==="pass"?"passed":l[2]==="fail"?"FAILED":"n/a")+" — "+l[3];lt.appendChild(s)});p.appendChild(lt);
  if(it.complaint){var cp=el("div","complaint");cp.appendChild(el("div","lab","Guard complaint (⟨A⟩ = number slot)"));cp.appendChild(document.createTextNode(it.complaint));p.appendChild(cp)}
  var ac=el("div","acts"),a=el("button","btn a","Accept"),b=el("button","btn b","Send back"),st=el("span","st");
  function paint(){var d=dec[it.key]&&dec[it.key].decision;a.setAttribute("aria-pressed",d==="accept");b.setAttribute("aria-pressed",d==="send-back");
   p.classList.toggle("dec-accept",d==="accept");p.classList.toggle("dec-back",d==="send-back");st.textContent=d?(d==="accept"?"accepted":"sent back")+" · "+dec[it.key].at.slice(0,16).replace("T"," "):"open"}
  function set(v){if(dec[it.key]&&dec[it.key].decision===v)delete dec[it.key];else dec[it.key]={decision:v,status:it.status,lang:L,at:new Date().toISOString()};save();paint();counts()}
  a.onclick=function(){set("accept")};b.onclick=function(){set("send-back")};
  ac.appendChild(a);ac.appendChild(b);ac.appendChild(st);p.appendChild(ac);paint();cols.appendChild(p);panes.push(p)});
 c.appendChild(cols);main.appendChild(c);cards.push(c)});
var none=el("div","empty","No item matches these filters.");main.appendChild(none);
function render(){document.querySelectorAll(".txt").forEach(function(t){t.innerHTML=segs(t._s)})}
// ---------------------------------------------------------------- filters
var F={status:"all",lang:"all",fam:"",q:""};
var fs=document.getElementById("f-fam");fs.appendChild(new Option("All families ("+D.families.length+")",""));
D.families.forEach(function(f){fs.appendChild(new Option(f[0]+" · "+f[1]+" item"+(f[1]>1?"s":""),f[0]))});
function seg(id,fn){var s=document.getElementById(id);s.addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;
 s.querySelectorAll("button").forEach(function(x){x.setAttribute("aria-pressed",x===b)});fn(b.dataset.v)})}
seg("f-status",function(v){F.status=v;apply()});seg("f-lang",function(v){F.lang=v;apply()});
seg("f-view",function(v){compact=v==="compact";render()});
fs.onchange=function(){F.fam=fs.value;apply()};document.getElementById("f-q").oninput=function(e){F.q=e.target.value.trim().toLowerCase();apply()};
function apply(){var n=0,ni=0;cards.forEach(function(c){var vis=0;
 c.querySelectorAll(".pane").forEach(function(p){var okL=F.lang==="all"||p.dataset.lang===F.lang,
  okS=p.dataset.status!=="none"&&(F.status==="all"||p.dataset.status===F.status);p.hidden=!okL||(F.status!=="all"&&!okS);if(okL&&okS){vis++}});
 c.querySelector(".cols").style.gridTemplateColumns=F.lang==="all"?"":"1fr";
 var show=vis>0&&(!F.fam||c.dataset.family===F.fam)&&(!F.q||c.dataset.q.indexOf(F.q)>=0);c.hidden=!show;if(show){n++;ni+=vis}});
 none.hidden=n>0;document.getElementById("shown").textContent=n+" changes · "+ni+" drafts shown"}
function counts(){var a=0,b=0;Object.keys(dec).forEach(function(k){dec[k].decision==="accept"?a++:b++});
 document.getElementById("dec").textContent=a+" accepted · "+b+" sent back · "+(panes.length-a-b)+" open"}
document.getElementById("export").onclick=function(){
 var out={run:M.run,model:M.model,pipeline:M.pipeline,run_sha256:M.run_sha256,exported_at:new Date().toISOString(),decisions:dec};
 var blob=new Blob([JSON.stringify(out,null,1)],{type:"application/json"}),u=URL.createObjectURL(blob),l=document.createElement("a");
 l.href=u;l.download="gleichlaut-decisions-"+M.run+".json";document.body.appendChild(l);l.click();setTimeout(function(){URL.revokeObjectURL(u);l.remove()},0)};
render();apply();counts();
})();
</script>
</body>
</html>
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="build the static translator review page")
    ap.add_argument("--run", default="fresh166"); ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    p, D = build(a.run, a.out)
    print(f"ui: {D['counts']['items']} drafts in {len(D['groups'])} German changes ({D['counts']['ready']} ready) -> {p} "
          f"({os.path.getsize(p) // 1024} KB)")


if __name__ == "__main__":
    main()
